resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.app_name}-dashboard-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", var.lambda_function_name],
            ["AWS/Lambda", "Errors", "FunctionName", var.lambda_function_name],
            ["AWS/Lambda", "Duration", "FunctionName", var.lambda_function_name]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Lambda - Invocations, Errors, Duration"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiName", var.api_gateway_name],
            ["AWS/ApiGateway", "4XXError", "ApiName", var.api_gateway_name],
            ["AWS/ApiGateway", "5XXError", "ApiName", var.api_gateway_name]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "API Gateway - Requests and Errors"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", var.lambda_function_name]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Lambda - Concurrent Executions"
          period  = 300
          yAxis = {
            left = {
              min = 0
            }
          }
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", var.dynamodb_table_name],
            ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", var.dynamodb_table_name]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "DynamoDB - Consumed Capacity Units"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 24
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", var.lambda_function_name, {"stat": "p50"}],
            ["AWS/Lambda", "Duration", "FunctionName", var.lambda_function_name, {"stat": "p90"}],
            ["AWS/Lambda", "Duration", "FunctionName", var.lambda_function_name, {"stat": "p99"}]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Lambda - Duration Percentiles (ms)"
          period  = 300
        }
      }
    ]
  })
}

# CloudWatch Alarms

# Lambda Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.app_name}-lambda-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "This metric monitors lambda function errors"
  treat_missing_data  = "notBreaching"
  
  dimensions = {
    FunctionName = var.lambda_function_name
  }
  
  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]
}

# API Gateway 5XX Error Alarm
resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx" {
  alarm_name          = "${var.app_name}-api-gateway-5xx-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "This metric monitors API Gateway 5XX errors"
  treat_missing_data  = "notBreaching"
  
  dimensions = {
    ApiName = var.api_gateway_name
  }
  
  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]
}

# Lambda Duration Alarm (p90 > 5000ms)
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.app_name}-lambda-duration-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  extended_statistic  = "p90"
  threshold           = 5000
  alarm_description   = "This metric monitors lambda function duration (p90)"
  treat_missing_data  = "notBreaching"
  
  dimensions = {
    FunctionName = var.lambda_function_name
  }
  
  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]
}

# SNS Topic for Alarms
resource "aws_sns_topic" "alarms" {
  name = "${var.app_name}-alarms-${var.environment}"
}

# Optional: Add email subscription to SNS topic
resource "aws_sns_topic_subscription" "email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# Data sources
data "aws_region" "current" {}