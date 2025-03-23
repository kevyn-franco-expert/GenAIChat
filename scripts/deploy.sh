#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting deployment of CV Assistant...${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Terraform is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if terraform.tfvars exists
if [ ! -f "terraform/terraform.tfvars" ]; then
    echo -e "${YELLOW}terraform.tfvars not found. Creating from example...${NC}"
    cp terraform/terraform.tfvars.example terraform/terraform.tfvars
    echo -e "${RED}Please edit terraform/terraform.tfvars with your AWS configuration before continuing.${NC}"
    exit 1
fi

# Initialize Terraform
echo -e "${YELLOW}Initializing Terraform...${NC}"
cd terraform
terraform init

# Plan Terraform changes
echo -e "${YELLOW}Planning Terraform changes...${NC}"
terraform plan -out=tfplan

# Apply Terraform changes
echo -e "${YELLOW}Applying Terraform changes...${NC}"
terraform apply tfplan

# Get outputs
ECR_REPO=$(terraform output -raw ecr_repository_url)
S3_BUCKET=$(terraform output -raw s3_bucket_name)
API_ENDPOINT=$(terraform output -raw api_endpoint)

echo -e "${GREEN}Infrastructure provisioned successfully!${NC}"
echo -e "ECR Repository: ${ECR_REPO}"
echo -e "S3 Bucket: ${S3_BUCKET}"
echo -e "API Endpoint: ${API_ENDPOINT}"

# Build and push Docker image
cd ..
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t cv-assistant .

# Login to ECR
echo -e "${YELLOW}Logging in to ECR...${NC}"
aws ecr get-login-password --region $(grep aws_region terraform/terraform.tfvars | cut -d'"' -f2) | docker login --username AWS --password-stdin ${ECR_REPO%/*}

# Tag and push Docker image
echo -e "${YELLOW}Pushing Docker image to ECR...${NC}"
docker tag cv-assistant:latest ${ECR_REPO}:latest
docker push ${ECR_REPO}:latest

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "Your CV Assistant API is now accessible at: ${API_ENDPOINT}"
echo -e "API Documentation is available at: ${API_ENDPOINT}/docs"
