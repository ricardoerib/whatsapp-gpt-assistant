output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "dashboard_url" {
  description = "URL to the CloudWatch dashboard"
  value       = "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alarms"
  value       = aws_sns_topic.alarms.arn
}

output "alarm_names" {
  description = "Names of the CloudWatch alarms"
  value = [
    aws_cloudwatch_metric_alarm.lambda_errors.alarm_name,
    aws_cloudwatch_metric_alarm.api_gateway_5xx.alarm_name,
    aws_cloudwatch_metric_alarm.lambda_duration.alarm_name
  ]
}