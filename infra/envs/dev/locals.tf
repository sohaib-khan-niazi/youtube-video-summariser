locals {
  name_prefix   = "${var.project_prefix}-${var.env}"
  bucket_suffix = var.suffix != "" ? "-${var.suffix}" : ""

  raw_bucket         = "${local.name_prefix}-raw${local.bucket_suffix}"
  transcripts_bucket = "${local.name_prefix}-transcripts${local.bucket_suffix}"
  summaries_bucket   = "${local.name_prefix}-summaries${local.bucket_suffix}"

  common_tags = {
    Project   = var.project_prefix
    Env       = var.env
    ManagedBy = "terraform"
  }
}
