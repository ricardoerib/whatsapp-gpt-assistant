output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.main.id
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.main.arn
}

output "bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = aws_s3_bucket.main.bucket_domain_name
}

output "audio_folder_path" {
  description = "Path to audio folder in S3"
  value       = "${aws_s3_bucket.main.id}/audio/"
}

output "csv_folder_path" {
  description = "Path to CSV folder in S3"
  value       = "${aws_s3_bucket.main.id}/csv/"
}

output "temp_folder_path" {
  description = "Path to temporary folder in S3"
  value       = "${aws_s3_bucket.main.id}/temp/"
}