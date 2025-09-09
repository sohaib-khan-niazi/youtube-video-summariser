output "api_gateway_id" {
  value       = aws_api_gateway_rest_api.main.id
  description = "ID of the API Gateway"
}

output "api_gateway_arn" {
  value       = aws_api_gateway_rest_api.main.arn
  description = "ARN of the API Gateway"
}

output "api_gateway_url" {
  value       = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${aws_api_gateway_stage.main.stage_name}"
  description = "URL of the API Gateway"
}

output "api_gateway_execution_arn" {
  value       = aws_api_gateway_rest_api.main.execution_arn
  description = "Execution ARN of the API Gateway"
}

data "aws_region" "current" {}
