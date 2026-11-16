# ==============================================================================
# EC2 Virtual Machine Configuration for Running US Visa App Container
# ==============================================================================

# Data Source: Find latest official Ubuntu 22.04 LTS AMI in ap-south-1
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical official owner ID

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# EC2 Instance
resource "aws_instance" "app_server" {
  ami                    = var.custom_ami_id != "" ? var.custom_ami_id : data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.app_public_subnet.id
  vpc_security_group_ids = [aws_security_group.app_sg.id]

  key_name                    = var.key_name != "" ? var.key_name : null
  associate_public_ip_address = true

  # Storage Configuration: High-performance gp3 EBS volume for OS and Docker
  root_block_device {
    volume_size           = var.root_volume_size
    volume_type           = "gp3"
    iops                  = 3000
    throughput            = 125
    encrypted             = true
    delete_on_termination = true

    tags = {
      Name = "${var.project_name}-root-ebs"
    }
  }

  # Startup Script: Install Docker, AWS CLI v2, and set up CI/CD-ready deployment environment
  user_data = <<-EOF
              #!/bin/bash
              set -e

              # 1. Update OS and install prerequisites (including CI/CD runner dependencies)
              apt-get update -y
              apt-get install -y ca-certificates curl gnupg lsb-release unzip jq git tar wget \
                                 build-essential libssl-dev libffi-dev libicu-dev

              # 2. Install Docker & Compose plugin
              apt-get install -y docker.io docker-compose-v2
              systemctl enable docker
              systemctl start docker
              usermod -aG docker ubuntu

              # 3. Install AWS CLI v2
              curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
              unzip -q awscliv2.zip
              ./aws/install
              rm -rf aws awscliv2.zip

              # 4. Create directory for GitHub Actions Self-Hosted Runner (optional use)
              mkdir -p /home/ubuntu/actions-runner
              chown -R ubuntu:ubuntu /home/ubuntu/actions-runner

              # 5. Create automated CI/CD deployment script
              # Accepts an optional image tag (defaults to "latest") e.g.: ./run_app.sh v1.0.2
              cat << 'SCRIPT' > /home/ubuntu/run_app.sh
              #!/bin/bash
              set -e
              IMAGE_TAG="$${1:-latest}"
              REGION="${var.aws_region}"
              ECR_URL="${aws_ecr_repository.app_ecr_repo.repository_url}"

              echo "=== 1. Authenticating Docker with ECR in $REGION ==="
              aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URL

              echo "=== 2. Pulling Docker image: $ECR_URL:$IMAGE_TAG ==="
              docker pull $ECR_URL:$IMAGE_TAG

              echo "=== 3. Stopping and removing previous container ==="
              docker stop us-visa-app 2>/dev/null || true
              docker rm -f us-visa-app 2>/dev/null || true

              echo "=== 4. Launching US Visa Application on Port ${var.app_port} ==="
              docker run -d \
                --name us-visa-app \
                --restart always \
                -p ${var.app_port}:${var.app_port} \
                $ECR_URL:$IMAGE_TAG

              echo "=== 5. Cleaning up dangling images to preserve disk space ==="
              docker image prune -f --filter "until=48h" || true

              echo "=== Deployment Succeeded! Application running on port ${var.app_port} ==="
              SCRIPT

              chmod +x /home/ubuntu/run_app.sh
              chown ubuntu:ubuntu /home/ubuntu/run_app.sh

              echo "Cloud-init finished successfully" > /var/log/user_data_status.log
              EOF

  tags = {
    Name = "${var.project_name}-app-server"
  }
}
