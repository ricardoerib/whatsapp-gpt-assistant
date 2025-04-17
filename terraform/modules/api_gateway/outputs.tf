output "api_id" {
  description = "ID of the API Gateway"
  value       = aws_api_gateway_rest_api.main.id
}

output "api_name" {
  description = "Name of the API Gateway"
  value       = aws_api_gateway_rest_api.main.name
}

output "api_endpoint" {
  description = "Base URL of the API Gateway"
  value       = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${aws_api_gateway_stage.main.stage_name}"
}

output "webhook_endpoint" {
  description = "Full URL of the webhook endpoint"
  value       = "${aws_api_gateway_stage.main.invoke_url}/webhook"
}

output "ask_endpoint" {
  description = "Full URL of the ask endpoint"
  value       = "${aws_api_gateway_stage.main.invoke_url}/ask"
}

output "healthcheck_endpoint" {
  description = "Full URL of the healthcheck endpoint"
  value       = "${aws_api_gateway_stage.main.invoke_url}/healthcheck"
}

# Uncomment if you want to use a custom domain name
# output "custom_domain_url" {
#   description = "Custom domain URL (if configured)"
#   value       = var.domain_name != "" ? "https://${var.domain_name}" : null
# }

# Get current AWS region
data "aws_region" "current" {}