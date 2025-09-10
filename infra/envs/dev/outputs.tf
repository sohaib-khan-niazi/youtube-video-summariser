# S3 Bucket outputs
output "raw_bucket_name" {
  value       = module.s3.raw_bucket_name
  description = "Name of the raw audio S3 bucket"
}

output "transcripts_bucket_name" {
  value       = module.s3.transcripts_bucket_name
  description = "Name of the transcripts S3 bucket"
}

output "summaries_bucket_name" {
  value       = module.s3.summaries_bucket_name
  description = "Name of the summaries S3 bucket"
}

# Lambda outputs
output "lambda_function_name" {
  value       = module.lambda.lambda_function_name
  description = "Name of the Lambda function"
}

output "lambda_function_arn" {
  value       = module.lambda.lambda_function_arn
  description = "ARN of the Lambda function"
}

# API Gateway outputs
output "api_gateway_url" {
  value       = module.api_gateway.api_gateway_url
  description = "URL of the API Gateway"
}

output "api_gateway_id" {
  value       = module.api_gateway.api_gateway_id
  description = "ID of the API Gateway"
}

# Website outputs
output "website_url" {
  value       = "http://${module.s3_site.website_endpoint}"
  description = "URL of the static website"
}

output "website_bucket_name" {
  value       = module.s3_site.bucket_name
  description = "Name of the website S3 bucket"
}
