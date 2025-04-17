terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "whatsapp-gpt-assistant-terraform-state"
    key            = "whatsapp-gpt-assistant/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-lock"
    encrypt        = true
  }

  required_version = ">= 1.0.0"
}
