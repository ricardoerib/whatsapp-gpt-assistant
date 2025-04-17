output "function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.main.function_name
}

output "function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.main.arn
}

output "invoke_arn" {
  description = "Invocation ARN of the Lambda function"
  value       = aws_lambda_function.main.invoke_arn
}

output "role_arn" {
  description = "ARN of the IAM role used by the Lambda function"
  value       = aws_iam_role.lambda_role.arn
}

output "log_group_name" {
  description = "Name of the CloudWatch log group for the Lambda function"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}