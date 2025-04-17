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

variable "lambda_handler" {
  description = "Handler for the Lambda function"
  type        = string
}

variable "lambda_runtime" {
  description = "Runtime for the Lambda function"
  type        = string
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda function in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function in seconds"
  type        = number
  default     = 30
}

variable "lambda_log_retention" {
  description = "Number of days to retain Lambda logs"
  type        = number
  default     = 14
}

variable "lambda_concurrent_executions" {
  description = "Number of concurrent executions for the Lambda function"
  type        = number
  default     = 0  # 0 means no limit (use AWS account limit)
}

variable "subnet_ids" {
  description = "List of subnet IDs for the Lambda function VPC configuration"
  type        = list(string)
}

variable "security_group_ids" {
  description = "List of security group IDs for the Lambda function VPC configuration"
  type        = list(string)
}

variable "environment_variables" {
  description = "Environment variables for the Lambda function"
  type        = map(string)
  default     = {}
}