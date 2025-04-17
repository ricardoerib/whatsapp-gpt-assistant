resource "aws_dynamodb_table" "main" {
  name           = var.table_name
  billing_mode   = var.billing_mode
  read_capacity  = var.billing_mode == "PROVISIONED" ? var.read_capacity : null
  write_capacity = var.billing_mode == "PROVISIONED" ? var.write_capacity : null
  hash_key       = "profile_id"

  attribute {
    name = "profile_id"
    type = "S"
  }

  # Add GSI for phone_number lookups
  global_secondary_index {
    name               = "PhoneNumberIndex"
    hash_key           = "phone_number"
    projection_type    = "ALL"
    read_capacity      = var.billing_mode == "PROVISIONED" ? var.read_capacity : null
    write_capacity     = var.billing_mode == "PROVISIONED" ? var.write_capacity : null
  }

  # Add this attribute for the GSI
  attribute {
    name = "phone_number"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  # Enable server-side encryption
  server_side_encryption {
    enabled = true
  }

  # Add auto scaling if using provisioned capacity
  lifecycle {
    ignore_changes = [
      read_capacity,
      write_capacity
    ]
  }

  tags = {
    Name        = var.table_name
    Environment = var.environment
    Terraform   = "true"
  }
}

# Set up auto scaling for read capacity
resource "aws_appautoscaling_target" "read_target" {
  count              = var.billing_mode == "PROVISIONED" ? 1 : 0
  max_capacity       = var.autoscaling_max_read_capacity
  min_capacity       = var.read_capacity
  resource_id        = "table/${aws_dynamodb_table.main.name}"
  scalable_dimension = "dynamodb:table:ReadCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "read_policy" {
  count              = var.billing_mode == "PROVISIONED" ? 1 : 0
  name               = "DynamoDBReadCapacityUtilization:${aws_appautoscaling_target.read_target[0].resource_id}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.read_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.read_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.read_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "DynamoDBReadCapacityUtilization"
    }
    target_value = var.autoscaling_target_value
  }
}

# Set up auto scaling for write capacity
resource "aws_appautoscaling_target" "write_target" {
  count              = var.billing_mode == "PROVISIONED" ? 1 : 0
  max_capacity       = var.autoscaling_max_write_capacity
  min_capacity       = var.write_capacity
  resource_id        = "table/${aws_dynamodb_table.main.name}"
  scalable_dimension = "dynamodb:table:WriteCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "write_policy" {
  count              = var.billing_mode == "PROVISIONED" ? 1 : 0
  name               = "DynamoDBWriteCapacityUtilization:${aws_appautoscaling_target.write_target[0].resource_id}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.write_target[0].resource_id
  scalable_dimension = aws_appautoscaling_target.write_target[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.write_target[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "DynamoDBWriteCapacityUtilization"
    }
    target_value = var.autoscaling_target_value
  }
}