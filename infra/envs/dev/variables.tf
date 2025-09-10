variable "env" {
  description = "Environment name"
  type        = string
}

variable "project_prefix" {
  description = "Short project prefix (e.g., yvs)"
  type        = string
}

variable "suffix" {
  description = "Optional short suffix for global-unique S3 names (e.g., your initials)"
  type        = string
  default     = ""
}

variable "openai_api_key" {
  description = "OpenAI API key for video summarization"
  type        = string
  sensitive   = true
  default     = ""
}

variable "bedrock_model" {
  description = "Bedrock model ID for video summarization"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}
