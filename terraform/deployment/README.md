# US Visa Approval Prediction System - AWS Deployment (ap-south-1)

Terraform infrastructure-as-code configuration for deploying the containerized US Visa Approval Prediction System on **AWS (Asia Pacific - Mumbai / `ap-south-1`)**.

---

## Architecture Overview

```
                      Internet
                         │
                         ▼
             [Internet Gateway (IGW)]
                         │
                         ▼
     [VPC: 10.0.0.0/16] ──► [Public Subnet: 10.0.1.0/24 (ap-south-1a)]
                                   │
              ┌────────────────────┴────────────────────┐
              │                                         │
              ▼                                         ▼
   [Security Group]                           [AWS ECR Repository]
   - Port 22   (SSH)                          - us-visa-approval-app
   - Port 8080 (FastAPI App)                  - Scanned on push
   - Port 80   (HTTP)                         - Lifecycle policy (auto-expire)
   - Port 443  (HTTPS)                                  ▲
              │                                         │ (docker pull via
              ▼                                         │  Root / AWS credentials)
   [Elastic IP (Static)] ───────────────────────────────┘
              │
              ▼
   [EC2 Instance (t2.medium)]
   - OS: Ubuntu 22.04 LTS
   - Storage: 30 GB gp3 EBS (3000 IOPS)
   - User Data: Auto-installs Docker, AWS CLI v2, CI/CD runner tools
   - Deployment Helper: /home/ubuntu/run_app.sh <tag>
```

---

## File Structure

| File | Purpose |
| :--- | :--- |
| `provider.tf` | Configures Terraform version and AWS Provider for region `ap-south-1`. |
| `variables.tf` | Configurable input parameters (region, instance type, volume size, port, etc.). |
| `network.tf` | Provisions dedicated VPC, Internet Gateway, Public Subnet, Route Table, and Security Group. |
| `ecr.tf` | Elastic Container Registry (ECR) for hosting the project Docker image with retention lifecycle. |
| `ec2.tf` | Provisions the EC2 VM with 30 GB gp3 storage, latest Ubuntu 22.04 AMI, and Docker bootstrap. |
| `outputs.tf` | Prints ECR URL, EC2 Public IP, Application URL, and ready-to-run Docker push commands. |
| `terraform.tfvars.example` | Template for variable overrides. |

---

## Step-by-Step Deployment Instructions

### 1. Configure Variables (Optional)
If you wish to change settings (e.g. specify an existing SSH Key Pair or change instance type):
```bash
cp terraform.tfvars.example terraform.tfvars
```
Edit `terraform.tfvars` with your preferred values:
```hcl
aws_region    = "ap-south-1"
instance_type = "t2.medium"
key_name      = "your-aws-key-pair-name" # optional
```

### 2. Initialize and Review Plan
```bash
terraform init
terraform plan
```

### 3. Provision Infrastructure
```bash
terraform apply
```
After completion, Terraform will output the **ECR URL**, **EC2 Public IP**, and **Application URL**.

---

## Pushing Your Docker Image to ECR

From the root of the project directory (`US-Visa-Approval-Prediction-System`):

```bash
# 1. Login to AWS ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <ECR_REPOSITORY_URL>

# 2. Build the Docker image
docker build -t us-visa-approval-app:latest .

# 3. Tag the image for ECR
docker tag us-visa-approval-app:latest <ECR_REPOSITORY_URL>:latest

# 4. Push to ECR
docker push <ECR_REPOSITORY_URL>:latest
```

---

## Starting the Application on EC2

The EC2 instance is pre-configured with a deployment helper script (`/home/ubuntu/run_app.sh`).

### Option A: Via SSH
```bash
ssh -i <your-key.pem> ubuntu@<EC2_PUBLIC_IP>
./run_app.sh
```

### Option B: Via AWS Systems Manager (No SSH Key Needed)
1. Navigate to **AWS Console** > **EC2** > **Instances**.
2. Select `us-visa-approval-app-server` and click **Connect** > **Session Manager**.
3. In the terminal:
   ```bash
   sudo -u ubuntu /home/ubuntu/run_app.sh
   ```

---

## Accessing the Deployed Application

Once the container is started:
- **Web Interface**: `http://<EC2_PUBLIC_IP>:8080/`
- **Interactive Swagger API Docs**: `http://<EC2_PUBLIC_IP>:8080/docs`
- **Health Check**: `http://<EC2_PUBLIC_IP>:8080/health`

---

## CI/CD Pipeline Setup (For Later Configuration)

When you are ready to configure your CI/CD pipeline (e.g., GitHub Actions Secrets or GitLab CI Variables), configure the following repository secrets provided directly by `terraform output`:

| Secret Name | Value | Description |
| :--- | :--- | :--- |
| `AWS_ACCESS_KEY_ID` | `<Your AWS Access Key>` | Root/Admin AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | `<Your AWS Secret Key>` | Root/Admin AWS secret key |
| `AWS_REGION` | `ap-south-1` | AWS deployment region |
| `AWS_ECR_LOGIN_URI` | `<from terraform output>` | e.g. `123456789012.dkr.ecr.ap-south-1.amazonaws.com` |
| `ECR_REPOSITORY_NAME` | `us-visa-approval-app` | ECR repository name |
| `EC2_HOST` | `<Static Elastic IP>` | Permanent IP that never changes on reboots |
| `EC2_USERNAME` | `ubuntu` | Default EC2 user |

The EC2 user-data script already includes all CI/CD runner dependencies (`build-essential`, `libicu-dev`, `git`, `docker`, `unzip`, `jq`, `aws-cli`) and provides a parameterizable `/home/ubuntu/run_app.sh <tag>` script for deployments.

---

## Destroying Resources (Tear Down)
To avoid ongoing AWS charges when you are done testing:
```bash
terraform destroy
```
