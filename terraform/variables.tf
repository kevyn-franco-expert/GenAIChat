variable "aws_region" {
  description = "The AWS region to deploy the infrastructure"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g. dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "cv_bucket_name" {
  description = "Name of the S3 bucket to store CVs"
  type        = string
  default     = "cv-assistant-bucket"
}

variable "ecr_repository_name" {
  description = "Name of the ECR repository"
  type        = string
  default     = "cv-assistant"
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
  default     = "cv-assistant-cluster"
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
}

variable "task_cpu" {
  description = "CPU units for the ECS task"
  type        = string
  default     = "1024" # 1 vCPU
}

variable "task_memory" {
  description = "Memory for the ECS task"
  type        = string
  default     = "2048" # 2 GB
}

variable "service_desired_count" {
  description = "Desired number of instances of the service"
  type        = number
  default     = 1
}

variable "bedrock_model_id" {
  description = "Bedrock model ID for LLM"
  type        = string
  default     = "anthropic.claude-3-sonnet-20240229-v1:0"
}

variable "bedrock_embedding_model" {
  description = "Bedrock model ID for embeddings"
  type        = string
  default     = "amazon.titan-embed-text-v1"
}

variable "use_openai" {
  description = "Whether to use OpenAI instead of Bedrock"
  type        = bool
  default     = false
}

variable "openai_api_key" {
  description = "OpenAI API Key (only required if use_openai is true)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "openai_model" {
  description = "OpenAI model to use"
  type        = string
  default     = "gpt-4"
}