resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name        = "${var.app_name}-vpc-${var.environment}"
    Environment = var.environment
    Terraform   = "true"
  }
}

# Subnets
resource "aws_subnet" "public" {
  count                   = length(var.public_subnets)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.app_name}-public-subnet-${count.index}-${var.environment}"
    Environment = var.environment
    Terraform   = "true"
    Type        = "public"
  }
}

resource "aws_subnet" "private" {
  count                   = length(var.private_subnets)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.private_subnets[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = false

  tags = {
    Name        = "${var.app_name}-private-subnet-${count.index}-${var.environment}"
    Environment = var.environment
    Terraform   = "true"
    Type        = "private"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.app_name}-igw-${var.environment}"
    Environment = var.environment
    Terraform   = "true"
  }
}

# NAT Gateway and Elastic IP
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name        = "${var.app_name}-nat-eip-${var.environment}"
    Environment = var.environment
    Terraform   = "true"
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name        = "${var.app_name}-nat-gw-${var.environment}"
    Environment = var.environment
    Terraform   = "true"
  }

  depends_on = [aws_internet_gateway.main]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "${var.app_name}-public-rt-${var.environment}"
    Environment = var.environment
    Terraform   = "true"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name        = "${var.app_name}-private-rt-${var.environment}"
    Environment = var.environment
    Terraform   = "true"
  }
}

# Route Table Association
resource "aws_route_table_association" "public" {
  count          = length(var.public_subnets)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = length(var.private_subnets)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# Security Group for Lambda
resource "aws_security_group" "lambda" {
  name        = "${var.app_name}-lambda-sg-${var.environment}"
  description = "Security group for Lambda function"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.app_name}-lambda-sg-${var.environment}"
    Environment = var.environment
    Terraform   = "true"
  }
}

# Data sources
data "aws_availability_zones" "available" {}