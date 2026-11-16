variable "aws_region" {
  type        = string
  default     = "ap-south-1"
  description = "AWS region for infrastructure and container deployment"
}

variable "project_name" {
  type        = string
  default     = "us-visa-approval"
  description = "Name of the project used for naming resources and tagging"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Target deployment environment (e.g. production, staging, dev)"
}

variable "ecr_repository_name" {
  type        = string
  default     = "us-visa-approval-app"
  description = "Name of the AWS ECR repository to push Docker images"
}

variable "instance_type" {
  type        = string
  default     = "t2.medium"
  description = "EC2 instance size (t2.medium provides 2 vCPUs & 4GB RAM, ideal for ML container execution)"
}

variable "key_name" {
  type        = string
  default     = ""
  description = "Name of an existing AWS Key Pair for SSH access into the EC2 instance (optional)"
}

variable "ssh_allowed_cidr" {
  type        = string
  default     = "0.0.0.0/0"
  description = "CIDR block permitted to SSH into the EC2 instance (recommend locking down to your own IP)"
}

variable "app_port" {
  type        = number
  default     = 8080
  description = "Port on which the FastAPI application container listens"
}

variable "root_volume_size" {
  type        = number
  default     = 30
  description = "Size in GB of the root EBS gp3 volume for OS, Docker engine, and cached images"
}

variable "custom_ami_id" {
  type        = string
  default     = ""
  description = "Optional custom AMI ID. If empty, the latest official Ubuntu 22.04 LTS AMI is used"
}
