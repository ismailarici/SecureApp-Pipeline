resource "aws_ecr_repository" "app" {
  name = "${var.project_name}-app"

  #checkov:skip=CKV_AWS_136: KMS CMK encryption adds cost and operational complexity inappropriate for a dev learning environment. AES256 with AWS-managed keys is acceptable here.
  #checkov:skip=CKV_AWS_51: Moved to IMMUTABLE after initial Checkov scan. This skip is no longer needed but retained for documentation purposes.
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name    = "${var.project_name}-app"
    Project = var.project_name
  }
}

resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}