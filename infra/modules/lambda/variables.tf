variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "lambda_zip_path" {
  description = "Path to the Lambda deployment package"
  type        = string
  default     = "lambda_function.zip"
}

variable "raw_bucket_name" {
  description = "Name of the raw audio S3 bucket"
  type        = string
}

variable "transcripts_bucket_name" {
  description = "Name of the transcripts S3 bucket"
  type        = string
}

variable "summaries_bucket_name" {
  description = "Name of the summaries S3 bucket"
  type        = string
}

variable "openai_api_key" {
  description = "OpenAI API key for summarization"
  type        = string
  sensitive   = true
  default     = ""
}

variable "bedrock_model" {
  description = "Bedrock model ID for summarization"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}

variable "tags" {
  description = "Common tags to apply"
  type        = map(string)
  default     = {}
}
