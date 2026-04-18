# SecureApp Pipeline

A production-grade DevSecOps pipeline built from scratch to demonstrate
end-to-end application security — from first commit to live deployment on
AWS ECS Fargate. Every layer of the stack is scanned, gated, and audited
automatically on every push.

---

## What This Project Demonstrates

This project is not a tutorial follow-along. Every architectural decision
was made deliberately and can be defended. It covers:

- Secrets scanning before code reaches the repository
- SAST across Python source code with two independent tools
- Software composition analysis and SBOM generation
- Container image scanning with CVE gating
- Infrastructure as code security scanning with documented suppressions
- OIDC-based deployment with zero static credentials
- DAST against a live running application on AWS ECS Fargate
- Centralised findings reporting via SARIF to GitHub Security tab

---

## Pipeline Architecture

┌─────────────────────────────────────────────────────────────┐
│ On Every Push │
└─────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────┐
│ Gitleaks │ Secrets scanning — blocks hardcoded credentials
└────────┬────────┘
│
▼
┌────────────────────────────────────┐
│ Bandit + Semgrep (parallel) │ SAST — insecure code patterns
└────────────────┬───────────────────┘
│
▼
┌────────────────────────────────────┐
│ pip-audit + Syft + Trivy │ SCA, SBOM, container CVE scanning
│ (parallel) │
└────────────────┬───────────────────┘
│
▼
┌─────────────────┐
│ Checkov │ IaC scanning — Terraform security misconfigurations
└────────┬────────┘
│
▼
┌─────────────────┐
│ Build + Push │ Docker image → Amazon ECR (immutable tags)
│ to ECR │
└────────┬────────┘
│
▼
┌─────────────────┐
│ Deploy to ECS │ OIDC → STS temporary credentials → ECS Fargate
│ Fargate │
└────────┬────────┘
│
▼
┌─────────────────┐
│ OWASP ZAP │ DAST — attacks the live running application
└─────────────────┘
│
▼
┌─────────────────────────────────────┐
│ GitHub Security Tab (SARIF) │ All findings, one audit trail
└─────────────────────────────────────┘

---

## Target Application

A deliberately vulnerable Python Flask application built with intentional
security flaws to provide realistic scan findings:

- SQL injection via string concatenation
- Hardcoded credentials
- Command injection via subprocess with shell=True
- Path traversal via unsanitised file reads
- Debug mode enabled in production
- Cross-site scripting

These vulnerabilities are intentional. They exist to generate real findings
across the scanning tools and demonstrate that the pipeline catches them.

---

## Security Tools

| Tool      | Category           | What It Catches                                                                 |
| --------- | ------------------ | ------------------------------------------------------------------------------- |
| Gitleaks  | Secrets Detection  | Hardcoded API keys, passwords, tokens in source and git history                 |
| Bandit    | SAST               | Python-specific insecure patterns: SQL injection, subprocess misuse, debug mode |
| Semgrep   | SAST               | Framework-aware injection flaws, taint analysis, Flask-specific rules           |
| pip-audit | SCA                | Known CVEs in Python dependencies via OSV database                              |
| Syft      | SBOM               | Full software bill of materials in CycloneDX format                             |
| Trivy     | Container Scanning | OS and library CVEs in the Docker image, with ignore-unfixed gating             |
| Checkov   | IaC Scanning       | Terraform misconfigurations across AWS VPC, ECS, ECR, IAM, CloudWatch           |
| OWASP ZAP | DAST               | Runtime vulnerabilities in the live application: missing headers, injection     |

---

## Infrastructure

All AWS infrastructure is provisioned with Terraform:

- VPC with public subnets across two availability zones
- Amazon ECR with scan-on-push and immutable tags
- ECS Fargate cluster and service
- CloudWatch log group with 365-day retention
- Two least-privilege IAM roles: task execution and task runtime
- GitHub OIDC provider for keyless deployment
- Security groups with explicit ingress rules

18 AWS resources managed as code. No resources created manually.

---

## Three Decisions That Show Security Reasoning

### 1. OIDC Instead of Static Credentials

The pipeline deploys to AWS without storing any AWS credentials in GitHub
Secrets. Instead, GitHub generates a signed JWT for each workflow run. AWS
validates the token claims — repository name, branch, workflow — and issues
temporary STS credentials scoped to the deployment role only.

This means there are no long-lived credentials to rotate, leak, or
compromise. If the OIDC trust relationship is misconfigured, deployment
fails rather than silently succeeding with overly broad access.

### 2. Documented Suppressions in Checkov

Checkov identified findings that were accepted as appropriate for a
development environment — VPC flow logging, KMS encryption for CloudWatch
logs, private subnets. Rather than silently skipping them, each suppression
is documented inline in the Terraform code with a business justification and
a note of what would be required in production.

This means every accepted risk is visible, attributable, and reviewable.
The suppressions are not hiding findings — they are making risk acceptance
explicit and auditable.

### 3. ignore-unfixed in Trivy

Trivy is configured with `ignore-unfixed: true`, which means it only fails
the pipeline on CVEs that have an available fix. CVEs with no upstream patch
are reported but do not block deployment.

This is a deliberate risk acceptance decision. Blocking on unfixable CVEs
creates alert fatigue without actionable remediation paths. The finding is
still recorded. The gate only triggers when a developer can actually do
something about it.

---

## SARIF Reporting

All five scanning tools output findings in SARIF format and upload to the
GitHub Security tab on every pipeline run. This means:

- Every finding is timestamped and attributed to a specific tool
- Fixed findings are automatically marked closed
- Reintroduced findings are automatically reopened
- Every dismissal is recorded with a reason
- The full history of findings across all tools is visible in one place

The Security tab is the audit trail. It answers the question a security
team will always ask: "when did this finding appear, who saw it, and what
was done about it?"

---

## What I Would Add in Production

**Slack alerting on HIGH and CRITICAL findings** — security findings are
useless if nobody sees them in real time. A pipeline report that sits in
GitHub Actions logs provides no operational visibility.

**Branch protection rules** — the pipeline gate only works if developers
cannot bypass it by pushing directly to main. Branch protection enforces
that every change goes through a pull request and passes all pipeline checks
before merging.

**Application Load Balancer** — the current setup assigns a public IP
directly to the ECS task, which changes on every deployment. An ALB provides
a stable DNS endpoint, enables HTTPS termination, and is a prerequisite for
any production traffic management.

**TruffleHog alongside Gitleaks** — TruffleHog's key differentiator is
credential verification. It calls live APIs to confirm whether a found
secret is still valid. A verified, active credential is a critical incident.
An expired one is informational. That distinction matters at scale.

**WAF in front of the application** — DAST with ZAP catches vulnerabilities
but does not block exploitation. A Web Application Firewall provides a
runtime defence layer that complements the pipeline scanning gates.

---

## Running the Pipeline

Push to main. The pipeline runs automatically. No manual steps required.

To run scans locally:

```bash
# Secrets
gitleaks detect --source . -v

# SAST
bandit -r app/app.py
semgrep scan --config=auto app/

# Dependencies
pip-audit -r app/requirements.txt

# Container
docker build -t secureapp app/
trivy image secureapp:latest

# IaC
cd terraform && checkov -d .
```

---

## Repository Structure

SecureApp-Pipeline/
├── app/ # Flask application and Dockerfile
├── terraform/ # AWS infrastructure as code
├── .github/workflows/ # GitHub Actions pipeline
├── .semgrep/ # Custom Semgrep rules
├── .zap/ # ZAP scan configuration
└── reports/ # Local scan outputs (gitignored)

---

_Built as a portfolio project to demonstrate practical DevSecOps skills
across the full pipeline lifecycle — from secure coding practices through
infrastructure provisioning to runtime security validation._
