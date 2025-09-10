# S3 buckets for video processing
module "s3" {
  source = "../../modules/s3"

  # Bucket names come from env locals
  raw_bucket_name         = local.raw_bucket
  transcripts_bucket_name = local.transcripts_bucket
  summaries_bucket_name   = local.summaries_bucket

  # Common tags from locals
  tags = local.common_tags

  # Lifecycle / safety
  raw_expiration_days = 1
  force_destroy       = true
  versioning_enabled  = true
}

# Lambda function for video processing
module "lambda" {
  source = "../../modules/lambda"

  function_name = "${local.name_prefix}-video-processor"

  # S3 bucket names from S3 module
  raw_bucket_name         = module.s3.raw_bucket_name
  transcripts_bucket_name = module.s3.transcripts_bucket_name
  summaries_bucket_name   = module.s3.summaries_bucket_name

  # Lambda deployment package (you'll need to create this)
  lambda_zip_path = "../../../backend/lambda_function.zip"

  # AI service configuration
  openai_api_key = var.openai_api_key
  bedrock_model  = var.bedrock_model

  tags = local.common_tags
}

# API Gateway for frontend
module "api_gateway" {
  source = "../../modules/api_gateway"

  api_name = "${local.name_prefix}-api"

  # Lambda integration
  lambda_function_name = module.lambda.lambda_function_name
  lambda_invoke_arn    = module.lambda.lambda_invoke_arn

  tags = local.common_tags
}

# S3 static website hosting
module "s3_site" {
  source = "../../modules/s3_site"

  bucket_name = "${local.name_prefix}-website${local.bucket_suffix}"

  # Update the index.html with the actual API Gateway URL
  index_html_content = replace(
    file("${path.module}/index.html"),
    "API_GATEWAY_URL",
    module.api_gateway.api_gateway_url
  )

  tags = local.common_tags
}
