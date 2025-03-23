# Configure AWS provider
provider "aws" {
  region = var.aws_region
}

# Create S3 bucket for CV storage
resource "aws_s3_bucket" "cv_bucket" {
  bucket = var.cv_bucket_name
  
  tags = {
    Name        = "CV Storage Bucket"
    Environment = var.environment
    Project     = "CV Assistant"
  }
}

# Configure S3 bucket access
resource "aws_s3_bucket_ownership_controls" "cv_bucket_ownership" {
  bucket = aws_s3_bucket.cv_bucket.id
  
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "cv_bucket_acl" {
  depends_on = [aws_s3_bucket_ownership_controls.cv_bucket_ownership]
  
  bucket = aws_s3_bucket.cv_bucket.id
  acl    = "private"
}

# Create ECR repository for Docker image
resource "aws_ecr_repository" "app_repository" {
  name                 = var.ecr_repository_name
  image_tag_mutability = "MUTABLE"
  
  image_scanning_configuration {
    scan_on_push = true
  }
  
  tags = {
    Name        = "CV Assistant Repository"
    Environment = var.environment
    Project     = "CV Assistant"
  }
}

# Create ECS cluster
resource "aws_ecs_cluster" "app_cluster" {
  name = var.ecs_cluster_name
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = {
    Name        = "CV Assistant Cluster"
    Environment = var.environment
    Project     = "CV Assistant"
  }
}

# Define IAM role for ECS task execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "cv-assistant-ecs-task-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  
  tags = {
    Name        = "CV Assistant ECS Role"
    Environment = var.environment
    Project     = "CV Assistant"
  }
}

# Attach policies to ECS task execution role
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Create policy for Bedrock access
resource "aws_iam_policy" "bedrock_access_policy" {
  count       = var.use_openai ? 0 : 1
  name        = "cv-assistant-bedrock-access-policy"
  description = "Policy to allow Bedrock API access"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "bedrock:InvokeModel",
          "bedrock:ListFoundationModels"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# Attach Bedrock policy to role
resource "aws_iam_role_policy_attachment" "bedrock_policy_attachment" {
  count      = var.use_openai ? 0 : 1
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = aws_iam_policy.bedrock_access_policy[0].arn
}

# Create a secret for OpenAI API Key (only if using OpenAI)
resource "aws_secretsmanager_secret" "openai_api_key" {
  count       = var.use_openai ? 1 : 0
  name        = "cv-assistant/openai-api-key"
  description = "OpenAI API Key for CV Assistant"
  
  tags = {
    Name        = "CV Assistant OpenAI API Key"
    Environment = var.environment
    Project     = "CV Assistant"
  }
}

# Store the OpenAI API Key in the secret (only if using OpenAI)
resource "aws_secretsmanager_secret_version" "openai_api_key" {
  count         = var.use_openai ? 1 : 0
  secret_id     = aws_secretsmanager_secret.openai_api_key[0].id
  secret_string = var.openai_api_key
}

# Add permission to ECS task role to read the secret (only if using OpenAI)
resource "aws_iam_policy" "secrets_access_policy" {
  count       = var.use_openai ? 1 : 0
  name        = "cv-assistant-secrets-access-policy"
  description = "Policy to allow access to Secrets Manager"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Effect   = "Allow"
        Resource = aws_secretsmanager_secret.openai_api_key[0].arn
      }
    ]
  })
}

# Attach Secrets Manager policy to role (only if using OpenAI)
resource "aws_iam_role_policy_attachment" "secrets_policy_attachment" {
  count      = var.use_openai ? 1 : 0
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = aws_iam_policy.secrets_access_policy[0].arn
}

# Create policy for S3 access
resource "aws_iam_policy" "s3_access_policy" {
  name        = "cv-assistant-s3-access-policy"
  description = "Policy to allow S3 access"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Effect   = "Allow"
        Resource = [
          "${aws_s3_bucket.cv_bucket.arn}",
          "${aws_s3_bucket.cv_bucket.arn}/*"
        ]
      }
    ]
  })
}

# Attach S3 policy to role
resource "aws_iam_role_policy_attachment" "s3_policy_attachment" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = aws_iam_policy.s3_access_policy.arn
}

# Create EFS for persistent storage
resource "aws_efs_file_system" "app_efs" {
  creation_token = "cv-assistant-efs"
  
  lifecycle_policy {
    transition_to_ia = "AFTER_30_DAYS"
  }
  
  tags = {
    Name        = "CV Assistant EFS"
    Environment = var.environment
    Project     = "CV Assistant"
  }
}

# Create security group for EFS
resource "aws_security_group" "efs_sg" {
  name        = "cv-assistant-efs-sg"
  description = "Security group for CV Assistant EFS"
  vpc_id      = var.vpc_id
  
  ingress {
    description      = "NFS from VPC"
    from_port        = 2049
    to_port          = 2049
    protocol         = "tcp"
    cidr_blocks      = [data.aws_vpc.selected.cidr_block]
  }
  
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }
  
  tags = {
    Name        = "CV Assistant EFS SG"
    Environment = var.environment
    Project     = "CV Assistant"
  }
}

# Create EFS mount targets in all subnets
resource "aws_efs_mount_target" "app_efs_mount" {
  for_each = toset(var.subnet_ids)
  
  file_system_id  = aws_efs_file_system.app_efs.id
  subnet_id       = each.value
  security_groups = [aws_security_group.efs_sg.id]
}

# Data source for VPC
data "aws_vpc" "selected" {
  id = var.vpc_id
}

# Create security group for app
resource "aws_security_group" "app_sg" {
  name        = "cv-assistant-app-sg"
  description = "Security group for CV Assistant App"
  vpc_id      = var.vpc_id
  
  ingress {
    description      = "HTTP"
    from_port        = 8000
    to_port          = 8000
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
  }
  
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }
  
  tags = {
    Name        = "CV Assistant App SG"
    Environment = var.environment
    Project     = "CV Assistant"
  }
}

# Create CloudWatch log group
resource "aws_cloudwatch_log_group" "app_log_group" {
  name              = "/ecs/cv-assistant"
  retention_in_days = 30
  
  tags = {
    Name        = "CV Assistant Logs"
    Environment = var.environment
    Project     = "CV Assistant"
  }
}

# Create ECS task definition
resource "aws_ecs_task_definition" "app_task" {
  family                   = "cv-assistant"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_execution_role.arn
  
  container_definitions = jsonencode([
    {
      name      = "cv-assistant"
      image     = "${aws_ecr_repository.app_repository.repository_url}:latest"
      essential = true
      
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      
      environment = concat(
        [
          {
            name  = "AWS_REGION"
            value = var.aws_region
          },
          {
            name  = "S3_BUCKET_NAME"
            value = aws_s3_bucket.cv_bucket.bucket
          },
          {
            name  = "BEDROCK_MODEL_ID"
            value = var.bedrock_model_id
          },
          {
            name  = "BEDROCK_EMBEDDING_MODEL"
            value = var.bedrock_embedding_model
          },
          {
            name  = "VECTOR_DB_DIR"
            value = "/data/chroma_db"
          },
          {
            name  = "USE_OPENAI"
            value = tostring(var.use_openai)
          }
        ],
        var.use_openai ? [
          {
            name  = "OPENAI_MODEL"
            value = var.openai_model
          }
        ] : []
      )
      
      secrets = var.use_openai ? [
        {
          name      = "OPENAI_API_KEY"
          valueFrom = aws_secretsmanager_secret.openai_api_key[0].arn
        }
      ] : []
      
      mountPoints = [
        {
          sourceVolume  = "efs-data"
          containerPath = "/data"
          readOnly      = false
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app_log_group.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
  
  volume {
    name = "efs-data"
    
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.app_efs.id
      root_directory = "/"
      
      transit_encryption = "ENABLED"
      authorization_config {
        iam = "ENABLED"
      }
    }
  }
  
  tags = {
    Name        = "CV Assistant Task"
    Environment = var.environment
    Project     = "CV Assistant"
  }
}

# Create ALB for the service
resource "aws_lb" "app_lb" {
  name               = "cv-assistant-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.app_sg.id]
  subnets            = var.subnet_ids
  
  tags = {
    Name        = "CV Assistant LB"
    Environment = var.environment
    Project     = "CV Assistant"
  }
}

# Create target group
resource "aws_lb_target_group" "app_tg" {
  name        = "cv-assistant-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  
  health_check {
    enabled             = true
    interval            = 30
    path                = "/health"
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }
  
  tags = {
    Name        = "CV Assistant TG"
    Environment = var.environment
    Project     = "CV Assistant"
  }
}

# Create listener
resource "aws_lb_listener" "app_listener" {
  load_balancer_arn = aws_lb.app_lb.arn
  port              = 80
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app_tg.arn
  }
  
  tags = {
    Name        = "CV Assistant Listener"
    Environment = var.environment
    Project     = "CV Assistant"
  }
}

# Create ECS service
resource "aws_ecs_service" "app_service" {
  name            = "cv-assistant"
  cluster         = aws_ecs_cluster.app_cluster.id
  task_definition = aws_ecs_task_definition.app_task.arn
  launch_type     = "FARGATE"
  desired_count   = var.service_desired_count
  
  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.app_sg.id]
    assign_public_ip = true
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.app_tg.arn
    container_name   = "cv-assistant"
    container_port   = 8000
  }
  
  depends_on = [
    aws_lb_listener.app_listener,
    aws_iam_role_policy_attachment.ecs_task_execution_role_policy
  ]
  
  tags = {
    Name        = "CV Assistant Service"
    Environment = var.environment
    Project     = "CV Assistant"
  }
}

# Outputs
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