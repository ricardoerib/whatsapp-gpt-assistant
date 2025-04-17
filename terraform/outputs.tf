output "api_gateway_endpoint" {
  description = "The endpoint URL of the API Gateway"
  value       = module.api_gateway.api_endpoint
}

output "lambda_function_name" {
  description = "The name of the Lambda function"
  value       = module.lambda.function_name
}

output "lambda_function_arn" {
  description = "The ARN of the Lambda function"
  value       = module.lambda.function_arn
}

output "dynamodb_table_name" {
  description = "The name of the DynamoDB table"
  value       = module.dynamodb.table_name
}

output "dynamodb_table_arn" {
  description = "The ARN of the DynamoDB table"
  value       = module.dynamodb.table_arn
}

output "s3_bucket_name" {
  description = "The name of the S3 bucket"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "The ARN of the S3 bucket"
  value       = module.s3.bucket_arn
}

output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.network.vpc_id
}

output "private_subnet_ids" {
  description = "The IDs of the private subnets"
  value       = module.network.private_subnet_ids
}

output "public_subnet_ids" {
  description = "The IDs of the public subnets"
  value       = module.network.public_subnet_ids
}

output "cloudwatch_dashboard_url" {
  description = "URL to the CloudWatch dashboard"
  value       = module.monitoring.dashboard_url
}

output "webhook_url" {
  description = "URL to use for WhatsApp webhook configuration"
  value       = "${module.api_gateway.api_endpoint}/webhook"
}