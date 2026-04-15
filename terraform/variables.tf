variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS CLI profile to use for authentication"
  type        = string
  default     = "nordiq-dev"
}

variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "secureapp"
}

variable "container_port" {
  description = "Port the Flask app listens on"
  type        = number
  default     = 5000
}