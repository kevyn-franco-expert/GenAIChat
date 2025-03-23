output "ecr_repository_url" {
  description = "The URL of the ECR repository"
  value       = aws_ecr_repository.app_repository.repository_url
}

output "load_balancer_dns" {
  description = "The DNS name of the load balancer"
  value       = aws_lb.app_lb.dns_name
}

output "s3_bucket_name" {
  description = "The name of the S3 bucket"
  value       = aws_s3_bucket.cv_bucket.bucket
}

output "api_endpoint" {
  description = "The endpoint to access the API"
  value       = "http://${aws_lb.app_lb.dns_name}"
}

output "ai_service_used" {
  description = "Which AI service is being used (OpenAI or Bedrock)"
  value       = var.use_openai ? "OpenAI" : "Amazon Bedrock"
}