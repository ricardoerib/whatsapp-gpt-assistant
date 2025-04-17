variable "app_name" {
  description = "Name of the application"
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod)"
  type        = string
}

variable "bucket_prefix" {
  description = "Prefix for the S3 bucket name"
  type        = string
}