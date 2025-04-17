resource "aws_s3_bucket" "main" {
  bucket = "${var.bucket_prefix}-data-${var.environment}"

  tags = {
    Name        = "${var.bucket_prefix}-data-${var.environment}"
    Environment = var.environment
    Terraform   = "true"
  }
}

# Server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "main" {
  bucket                  = aws_s3_bucket.main.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versioning
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Lifecycle rules
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    id     = "audio-files"
    status = "Enabled"

    filter {
      prefix = "audio/"
    }

    # Keep audio files for 7 days
    expiration {
      days = 7
    }
  }

  rule {
    id     = "temp-files"
    status = "Enabled"

    filter {
      prefix = "temp/"
    }

    # Keep temp files for 1 day
    expiration {
      days = 1
    }
  }

  # Keep non-current versions for 7 days
  rule {
    id     = "noncurrent-version-expiration"
    status = "Enabled"

    filter {
      prefix = "exp/"
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

# Initial folder structure
resource "aws_s3_object" "audio_folder" {
  bucket  = aws_s3_bucket.main.id
  key     = "audio/"
  content_type = "application/x-directory"
  source  = "/dev/null"  # Empty object

  # The etag forces the object to be updated
  etag    = md5("")
}

resource "aws_s3_object" "csv_folder" {
  bucket  = aws_s3_bucket.main.id
  key     = "csv/"
  content_type = "application/x-directory"
  source  = "/dev/null"  # Empty object

  # The etag forces the object to be updated
  etag    = md5("")
}

resource "aws_s3_object" "temp_folder" {
  bucket  = aws_s3_bucket.main.id
  key     = "temp/"
  content_type = "application/x-directory"
  source  = "/dev/null"  # Empty object

  # The etag forces the object to be updated
  etag    = md5("")
}