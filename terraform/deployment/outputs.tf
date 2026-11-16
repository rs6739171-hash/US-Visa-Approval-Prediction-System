# ==============================================================================
# Terraform Deployment Outputs
# ==============================================================================

output "aws_region" {
  description = "Target AWS Region"
  value       = var.aws_region
}

output "ecr_repository_url" {
  description = "The URL of the ECR repository to push the Docker image to"
  value       = aws_ecr_repository.app_ecr_repo.repository_url
}

output "ecr_registry_id" {
  description = "The registry ID where the repository was created"
  value       = aws_ecr_repository.app_ecr_repo.registry_id
}

output "ec2_public_ip" {
  description = "Static Elastic IP (EIP) address of the EC2 application host"
  value       = aws_eip.app_eip.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS hostname of the EC2 application host"
  value       = aws_instance.app_server.public_dns
}

output "application_url" {
  description = "Direct web browser URL for the deployed US Visa application"
  value       = "http://${aws_eip.app_eip.public_ip}:${var.app_port}"
}

output "swagger_docs_url" {
  description = "Interactive Swagger API documentation URL"
  value       = "http://${aws_eip.app_eip.public_ip}:${var.app_port}/docs"
}

output "docker_push_commands" {
  description = "Terminal commands to build, tag, and push Docker image to ECR"
  value       = <<-EOT
    # 1. Authenticate Docker with your ECR registry
    aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.app_ecr_repo.repository_url}

    # 2. Build your Docker image
    docker build -t ${var.ecr_repository_name}:latest .

    # 3. Tag image for ECR
    docker tag ${var.ecr_repository_name}:latest ${aws_ecr_repository.app_ecr_repo.repository_url}:latest

    # 4. Push image to ECR
    docker push ${aws_ecr_repository.app_ecr_repo.repository_url}:latest
  EOT
}

output "ssh_command" {
  description = "SSH connection string (requires key_name to be set)"
  value       = var.key_name != "" ? "ssh -i <path-to-${var.key_name}.pem> ubuntu@${aws_eip.app_eip.public_ip}" : "SSH key not specified. Use AWS Console Systems Manager (Session Manager) or configure key_name in terraform.tfvars."
}

# ==============================================================================
# CI/CD Pipeline Dedicated Configuration Outputs
# Copy these values into your CI/CD repository secrets (e.g. GitHub Secrets)
# ==============================================================================

output "ci_cd_aws_region" {
  description = "AWS_REGION secret for CI/CD"
  value       = var.aws_region
}

output "ci_cd_ecr_repo_name" {
  description = "ECR_REPOSITORY_NAME secret for CI/CD"
  value       = var.ecr_repository_name
}

output "ci_cd_ecr_login_uri" {
  description = "AWS_ECR_LOGIN_URI secret for CI/CD"
  value       = split("/", aws_ecr_repository.app_ecr_repo.repository_url)[0]
}

output "ci_cd_ec2_host" {
  description = "EC2_HOST secret for CI/CD (Static Elastic IP that will never change)"
  value       = aws_eip.app_eip.public_ip
}

output "ci_cd_secrets_guide" {
  description = "Summary of CI/CD secrets to configure in your Git repository"
  value       = <<-EOT
    ====================================================================
    CONFIGURING CI/CD SECRETS (e.g. GitHub Actions / GitLab CI):
    --------------------------------------------------------------------
    AWS_ACCESS_KEY_ID       : <Your AWS Root/Admin Access Key>
    AWS_SECRET_ACCESS_KEY   : <Your AWS Root/Admin Secret Key>
    AWS_REGION              : ${var.aws_region}
    AWS_ECR_LOGIN_URI       : ${split("/", aws_ecr_repository.app_ecr_repo.repository_url)[0]}
    ECR_REPOSITORY_NAME     : ${var.ecr_repository_name}
    EC2_HOST                : ${aws_eip.app_eip.public_ip}
    EC2_USERNAME            : ubuntu
    ====================================================================
  EOT
}
