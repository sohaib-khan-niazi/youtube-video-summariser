output "lambda_function_name" {
  value       = aws_lambda_function.video_processor.function_name
  description = "Name of the Lambda function"
}

output "lambda_function_arn" {
  value       = aws_lambda_function.video_processor.arn
  description = "ARN of the Lambda function"
}

output "lambda_invoke_arn" {
  value       = aws_lambda_function.video_processor.invoke_arn
  description = "Invoke ARN of the Lambda function"
}

output "lambda_role_arn" {
  value       = aws_iam_role.lambda_role.arn
  description = "ARN of the Lambda execution role"
}
