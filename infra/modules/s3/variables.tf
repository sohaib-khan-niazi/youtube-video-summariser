variable "raw_bucket_name" {
  description = "Bucket name for downloaded audio"
  type        = string
}

variable "transcripts_bucket_name" {
  description = "Bucket name for Transcribe output"
  type        = string
}

variable "summaries_bucket_name" {
  description = "Bucket name for summary JSON"
  type        = string
}

variable "tags" {
  description = "Common tags to apply"
  type        = map(string)
  default     = {}
}

variable "raw_expiration_days" {
  description = "Auto-delete raw audio after N days"
  type        = number
  default     = 1
}

variable "force_destroy" {
  description = "Allow bucket delete even if non-empty"
  type        = bool
  default     = true
}

variable "sse_algorithm" {
  description = "SSE algorithm"
  type        = string
  default     = "AES256"
}

variable "versioning_enabled" {
  description = "Enable S3 versioning"
  type        = bool
  default     = true
}
