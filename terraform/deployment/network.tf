# ==============================================================================
# Network Configuration: Dedicated VPC, Subnet, Internet Gateway & Security Group
# ==============================================================================

# 1. Virtual Private Cloud (VPC)
resource "aws_vpc" "app_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# 2. Internet Gateway (IGW) for public internet traffic
resource "aws_internet_gateway" "app_igw" {
  vpc_id = aws_vpc.app_vpc.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# 3. Public Subnet in ap-south-1a
resource "aws_subnet" "app_public_subnet" {
  vpc_id                  = aws_vpc.app_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet-1a"
  }
}

# 4. Route Table routing outbound traffic to Internet Gateway
resource "aws_route_table" "app_public_rt" {
  vpc_id = aws_vpc.app_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.app_igw.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

# 5. Associate Public Subnet with Public Route Table
resource "aws_route_table_association" "app_public_rta" {
  subnet_id      = aws_subnet.app_public_subnet.id
  route_table_id = aws_route_table.app_public_rt.id
}

# 6. Security Group for EC2 Application Server
resource "aws_security_group" "app_sg" {
  name        = "${var.project_name}-ec2-sg"
  description = "Security group for US Visa application server"
  vpc_id      = aws_vpc.app_vpc.id

  # SSH Access
  ingress {
    description = "SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr]
  }

  # FastAPI Web Application Port (8080)
  ingress {
    description = "FastAPI web application port"
    from_port   = var.app_port
    to_port     = var.app_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP (Port 80)
  ingress {
    description = "Standard HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS (Port 443)
  ingress {
    description = "Standard HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound rules (allow all outbound traffic for docker pull, apt, etc.)
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg"
  }
}

# 7. Static Elastic IP (EIP) for CI/CD Deployment Target
# Guarantees a permanent static IP that never changes across instance reboots or stops
resource "aws_eip" "app_eip" {
  domain     = "vpc"
  instance   = aws_instance.app_server.id
  depends_on = [aws_internet_gateway.app_igw]

  tags = {
    Name = "${var.project_name}-static-eip"
  }
}

