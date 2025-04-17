provider "aws" {
  region = var.aws_region
}

# Módulo para recursos de rede
module "network" {
  source = "./modules/network"

  app_name        = var.app_name
  environment     = var.environment
  vpc_cidr        = var.vpc_cidr
  public_subnets  = var.public_subnets
  private_subnets = var.private_subnets
}

# Módulo para o Lambda
module "lambda" {
  source = "./modules/lambda"

  app_name                = var.app_name
  environment             = var.environment
  lambda_function_name    = "${var.app_name}-${var.environment}"
  lambda_handler          = "lambda_handler.handler"
  lambda_runtime          = "python3.11"
  lambda_memory_size      = var.lambda_memory_size
  lambda_timeout          = var.lambda_timeout
  lambda_log_retention    = var.lambda_log_retention
  lambda_concurrent_executions = 0  # Temporariamente defina como 0
  subnet_ids              = module.network.private_subnet_ids
  security_group_ids      = [module.network.lambda_security_group_id]
  
  environment_variables = {
    APP_ENVIRONMENT    = var.environment
    LOG_LEVEL          = var.log_level
    DATABASE_ENABLED   = var.database_enabled
    DYNAMODB_TABLE     = module.dynamodb.table_name
    WHATSAPP_API_TOKEN = var.whatsapp_api_token
    WHATSAPP_API_URL   = var.whatsapp_api_url
    PHONE_NUMBER_ID    = var.phone_number_id
    OPENAI_API_KEY     = var.openai_api_key
    GPT_MODEL          = var.gpt_model
    JWT_SECRET_KEY     = var.jwt_secret_key
  }
}

# Módulo para API Gateway
module "api_gateway" {
  source = "./modules/api_gateway"

  app_name              = var.app_name
  environment           = var.environment
  lambda_function_name  = module.lambda.function_name
  lambda_function_arn   = module.lambda.function_arn
  lambda_invoke_arn     = module.lambda.invoke_arn
  whatsapp_verify_token = var.whatsapp_verify_token
}

# Módulo para DynamoDB
module "dynamodb" {
  source = "./modules/dynamodb"

  app_name    = var.app_name
  environment = var.environment
  table_name  = "${var.app_name}-users-${var.environment}"
  billing_mode = var.dynamodb_billing_mode
  read_capacity = var.dynamodb_read_capacity
  write_capacity = var.dynamodb_write_capacity
}

# Módulo para S3 (para armazenamento de áudio e CSV)
module "s3" {
  source = "./modules/s3"

  app_name      = var.app_name
  environment   = var.environment
  bucket_prefix = var.app_name
}

# Módulo para CloudWatch Dashboard
module "monitoring" {
  source = "./modules/monitoring"

  app_name             = var.app_name
  environment          = var.environment
  lambda_function_name = module.lambda.function_name
  api_gateway_name     = module.api_gateway.api_name
  dynamodb_table_name  = module.dynamodb.table_name
}