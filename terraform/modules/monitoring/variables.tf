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

variable "api_gateway_name" {
  description = "Name of the API Gateway"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "alarm_email" {
  description = "Email to send alarm notifications to (leave empty to disable email notifications)"
  type        = string
  default     = ""
}