resource "aws_ecr_repository" "lambda_repo" {
  name = "${var.app_name}-${var.environment}"
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "null_resource" "docker_build" {
  triggers = {
    # Forçar uma nova construção quando qualquer arquivo Python for alterado
    app_hash = sha256(join("", [for f in fileset("${path.module}/../../../app", "**/*.py") : filesha256("${path.module}/../../../app/${f}")]))
    handler_hash = filesha256("${path.module}/../../../lambda_handler.py")
    requirements_hash = filesha256("${path.module}/../../../requirements.txt")
    dockerfile_hash = filesha256("${path.module}/../../../Dockerfile")
  }

  provisioner "local-exec" {
    command = <<EOF
      aws ecr get-login-password --region ${data.aws_region.current.name} | docker login --username AWS --password-stdin ${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.name}.amazonaws.com
      docker build -t ${aws_ecr_repository.lambda_repo.repository_url}:latest ${path.module}/../../../
      docker push ${aws_ecr_repository.lambda_repo.repository_url}:latest
    EOF
  }
}

resource "aws_lambda_function" "main" {
  function_name = var.lambda_function_name
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda_repo.repository_url}:latest"
  role          = aws_iam_role.lambda_role.arn
  memory_size   = var.lambda_memory_size
  timeout       = var.lambda_timeout
  publish       = true

  # VPC configuration
  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = var.security_group_ids
  }

  # Environment variables
  environment {
    variables = var.environment_variables
  }

  depends_on = [null_resource.docker_build]

  tags = {
    Name        = var.lambda_function_name
    Environment = var.environment
    Terraform   = "true"
  }
}

# Criar um alias para a versão publicada
resource "aws_lambda_alias" "current" {
  name             = "current"
  function_name    = aws_lambda_function.main.function_name
  function_version = aws_lambda_function.main.version
  
  depends_on = [aws_lambda_function.main]
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = var.lambda_log_retention

  tags = {
    Name        = "${var.lambda_function_name}-logs"
    Environment = var.environment
    Terraform   = "true"
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.lambda_function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.lambda_function_name}-role"
    Environment = var.environment
    Terraform   = "true"
  }
}

# IAM Policies for Lambda Role
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Custom policy for DynamoDB access
resource "aws_iam_policy" "lambda_dynamodb_policy" {
  name        = "${var.lambda_function_name}-dynamodb-policy"
  description = "Allow Lambda to access DynamoDB tables"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:dynamodb:*:*:table/*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_dynamodb_policy.arn
}

# Custom policy for S3 access
resource "aws_iam_policy" "lambda_s3_policy" {
  name        = "${var.lambda_function_name}-s3-policy"
  description = "Allow Lambda to access S3 buckets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = [
          "arn:aws:s3:::${var.app_name}-*/*",
          "arn:aws:s3:::${var.app_name}-*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_s3" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_s3_policy.arn
}

# ECR access policy
resource "aws_iam_policy" "lambda_ecr_policy" {
  name        = "${var.lambda_function_name}-ecr-policy"
  description = "Allow Lambda to pull from ECR"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:GetRepositoryPolicy",
          "ecr:DescribeRepositories"
        ]
        Effect   = "Allow"
        Resource = [aws_ecr_repository.lambda_repo.arn]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_ecr" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_ecr_policy.arn
}

# # Lambda provisioned concurrency - aplicado ao alias
# resource "aws_lambda_provisioned_concurrency_config" "main" {
#   count                             = var.lambda_concurrent_executions > 0 ? 1 : 0
#   function_name                     = aws_lambda_function.main.function_name
#   provisioned_concurrent_executions = var.lambda_concurrent_executions
#   qualifier                         = aws_lambda_alias.current.name
  
#   depends_on = [aws_lambda_alias.current]
# }

# Dados para os comandos
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}