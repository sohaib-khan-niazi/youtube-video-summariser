# Lambda function for YouTube video processing
resource "aws_lambda_function" "video_processor" {
  function_name = var.function_name
  role         = aws_iam_role.lambda_role.arn
  handler      = "index.handler"
  runtime      = "python3.11"
  timeout      = 900  # 15 minutes for video processing
  memory_size  = 1024

  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)

  environment {
    variables = {
      RAW_BUCKET         = var.raw_bucket_name
      TRANSCRIPTS_BUCKET = var.transcripts_bucket_name
      SUMMARIES_BUCKET   = var.summaries_bucket_name
      OPENAI_API_KEY     = var.openai_api_key
      BEDROCK_MODEL      = var.bedrock_model
    }
  }

  tags = var.tags
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# IAM policy for Lambda to access S3, Transcribe, and Bedrock
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.function_name}-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:aws:s3:::${var.raw_bucket_name}/*",
          "arn:aws:s3:::${var.transcripts_bucket_name}/*",
          "arn:aws:s3:::${var.summaries_bucket_name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "transcribe:StartTranscriptionJob",
          "transcribe:GetTranscriptionJob"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "*"
      }
    ]
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 14
  tags              = var.tags
}
