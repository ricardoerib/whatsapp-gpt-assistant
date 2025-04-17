variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Name of the application"
  type        = string
  default     = "whatsapp-chatbot"
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod)"
  type        = string
  default     = "dev"
}

# Network variables
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnets" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.3.0/24", "10.0.4.0/24"]
}

# Lambda variables
variable "lambda_memory_size" {
  description = "Memory size for Lambda function"
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
  description = "Limit concurrent executions of the Lambda function"
  type        = number
  default     = 10
}

# DynamoDB variables
variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "dynamodb_read_capacity" {
  description = "DynamoDB read capacity units (if using PROVISIONED billing mode)"
  type        = number
  default     = 5
}

variable "dynamodb_write_capacity" {
  description = "DynamoDB write capacity units (if using PROVISIONED billing mode)"
  type        = number
  default     = 5
}

# App configuration variables
variable "log_level" {
  description = "Log level for the application"
  type        = string
  default     = "INFO"
}

variable "database_enabled" {
  description = "Whether to enable database connection"
  type        = string
  default     = "true"
}

variable "whatsapp_api_token" {
  description = "WhatsApp API token"
  type        = string
  sensitive   = true
}

variable "whatsapp_api_url" {
  description = "WhatsApp API URL"
  type        = string
  default     = "https://graph.facebook.com/v17.0/"
}

variable "phone_number_id" {
  description = "WhatsApp phone number ID"
  type        = string
}

variable "whatsapp_verify_token" {
  description = "WhatsApp verify token for webhook validation"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "gpt_model" {
  description = "GPT model to use"
  type        = string
  default     = "gpt-4-turbo-preview"
}

variable "jwt_secret_key" {
  description = "Secret key for JWT token generation"
  type        = string
  sensitive   = true
}