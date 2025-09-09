output "bucket_name" {
  value       = aws_s3_bucket.website.bucket
  description = "Name of the S3 website bucket"
}

output "bucket_arn" {
  value       = aws_s3_bucket.website.arn
  description = "ARN of the S3 website bucket"
}

output "website_endpoint" {
  value       = aws_s3_bucket_website_configuration.website.website_endpoint
  description = "Website endpoint of the S3 bucket"
}

output "website_domain" {
  value       = aws_s3_bucket_website_configuration.website.website_domain
  description = "Website domain of the S3 bucket"
}
