resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.app_name}-api-${var.environment}"
  description = "API Gateway for ${var.app_name} in ${var.environment}"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name        = "${var.app_name}-api-${var.environment}"
    Environment = var.environment
    Terraform   = "true"
  }
}

# Resources (endpoints)
resource "aws_api_gateway_resource" "webhook" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "webhook"
}

resource "aws_api_gateway_resource" "ask" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "ask"
}

resource "aws_api_gateway_resource" "healthcheck" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "healthcheck"
}

# Methods
# Webhook - GET (for verification)
resource "aws_api_gateway_method" "webhook_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.webhook.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.querystring.hub.mode" = true
    "method.request.querystring.hub.verify_token" = true
    "method.request.querystring.hub.challenge" = true
  }
}

# Webhook - POST (for receiving messages)
resource "aws_api_gateway_method" "webhook_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.webhook.id
  http_method   = "POST"
  authorization = "NONE"
}

# Ask - POST
resource "aws_api_gateway_method" "ask_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.ask.id
  http_method   = "POST"
  authorization = "NONE"
}

# Healthcheck - GET
resource "aws_api_gateway_method" "healthcheck_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.healthcheck.id
  http_method   = "GET"
  authorization = "NONE"
}

# Integrations with Lambda
# Webhook - GET Integration
resource "aws_api_gateway_integration" "webhook_get_integration" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.webhook.id
  http_method             = aws_api_gateway_method.webhook_get.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:lambda:path/2015-03-31/functions/${var.lambda_function_arn}:current/invocations"
}

# Webhook - POST Integration
resource "aws_api_gateway_integration" "webhook_post_integration" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.webhook.id
  http_method             = aws_api_gateway_method.webhook_post.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = "${var.lambda_invoke_arn}:current"
}

# Ask - POST Integration
resource "aws_api_gateway_integration" "ask_post_integration" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.ask.id
  http_method             = aws_api_gateway_method.ask_post.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = "${var.lambda_invoke_arn}:current"
}

# Healthcheck - GET Integration
resource "aws_api_gateway_integration" "healthcheck_get_integration" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.healthcheck.id
  http_method             = aws_api_gateway_method.healthcheck_get.http_method
  type                    = "AWS_PROXY"
  integration_http_method = "POST"
  uri                     = "${var.lambda_invoke_arn}:current"
}

# Deployment and stage
resource "aws_api_gateway_deployment" "main" {
  depends_on = [
    aws_api_gateway_integration.webhook_get_integration,
    aws_api_gateway_integration.webhook_post_integration,
    aws_api_gateway_integration.ask_post_integration,
    aws_api_gateway_integration.healthcheck_get_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.main.id
  
  # Use a timestamp to force redeployment when needed
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.webhook.id,
      aws_api_gateway_resource.ask.id,
      aws_api_gateway_resource.healthcheck.id,
      aws_api_gateway_method.webhook_get.id,
      aws_api_gateway_method.webhook_post.id,
      aws_api_gateway_method.ask_post.id,
      aws_api_gateway_method.healthcheck_get.id,
      aws_api_gateway_integration.webhook_get_integration.id,
      aws_api_gateway_integration.webhook_post_integration.id,
      aws_api_gateway_integration.ask_post_integration.id,
      aws_api_gateway_integration.healthcheck_get_integration.id
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Adicione um novo recurso de stage
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment
  
  # Recomendado: habilitar logs para o stage
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format          = "$context.identity.sourceIp - - [$context.requestTime] \"$context.httpMethod $context.routeKey $context.protocol\" $context.status $context.responseLength $context.requestId $context.integrationErrorMessage"
  }
}

# Crie o grupo de logs para o API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.app_name}-${var.environment}"
  retention_in_days = 7
}

# Custom domain name (optional)
# Uncomment if you have a custom domain
# resource "aws_api_gateway_domain_name" "main" {
#   domain_name     = var.domain_name
#   certificate_arn = var.certificate_arn
#   
#   endpoint_configuration {
#     types = ["REGIONAL"]
#   }
# }
# 
# resource "aws_api_gateway_base_path_mapping" "main" {
#   api_id      = aws_api_gateway_rest_api.main.id
#   stage_name  = aws_api_gateway_stage.main.stage_name
#   domain_name = aws_api_gateway_domain_name.main.domain_name
# }

# Lambda permissions to allow API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  qualifier     = "current"  # Use o qualificador do alias
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}