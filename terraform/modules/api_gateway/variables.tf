variable "app_name" {
  description = "Name of the application"
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod)"
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "lambda_function_arn" {
  description = "ARN of the Lambda function"
  type        = string
}

variable "lambda_invoke_arn" {
  description = "Invocation ARN of the Lambda function"
  type        = string
}

variable "whatsapp_verify_token" {
  description = "WhatsApp verify token for webhook validation"
  type        = string
}

# Uncomment if you want to use a custom domain name
# variable "domain_name" {
#   description = "Custom domain name for the API Gateway"
#   type        = string
#   default     = ""
# }
# 
# variable "certificate_arn" {
#   description = "ARN of the ACM certificate for the custom domain"
#   type        = string
#   default     = ""
# }