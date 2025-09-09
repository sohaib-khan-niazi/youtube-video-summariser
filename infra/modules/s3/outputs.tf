output "raw_bucket_name" {
  value       = aws_s3_bucket.raw.bucket
  description = "Raw audio bucket"
}

output "transcripts_bucket_name" {
  value       = aws_s3_bucket.transcripts.bucket
  description = "Transcripts bucket"
}

output "summaries_bucket_name" {
  value       = aws_s3_bucket.summaries.bucket
  description = "Summaries bucket"
}
