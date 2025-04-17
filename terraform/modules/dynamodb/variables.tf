variable "app_name" {
  description = "Name of the application"
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod)"
  type        = string
}

variable "table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "billing_mode" {
  description = "DynamoDB billing mode (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "read_capacity" {
  description = "DynamoDB read capacity units (only used for PROVISIONED billing mode)"
  type        = number
  default     = 5
}

variable "write_capacity" {
  description = "DynamoDB write capacity units (only used for PROVISIONED billing mode)"
  type        = number
  default     = 5
}

variable "autoscaling_max_read_capacity" {
  description = "Maximum read capacity for auto scaling"
  type        = number
  default     = 100
}

variable "autoscaling_max_write_capacity" {
  description = "Maximum write capacity for auto scaling"
  type        = number
  default     = 100
}

variable "autoscaling_target_value" {
  description = "Target utilization percentage for auto scaling"
  type        = number
  default     = 70
}