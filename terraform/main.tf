terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.72.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6.0"
    }
  }
}

provider "aws" {
  region = var.region
}

resource "random_id" "rand_id" {
  byte_length = 8
}

# AWS S3 Bucket for MLOps Artifacts & Production Model Storage
resource "aws_s3_bucket" "MLOps_Bucket" {
  bucket = "${var.bucket_prefix}${lower(random_id.rand_id.hex)}"

  tags = {
    Name        = "MLOps-Model-Bucket"
    Environment = "Production"
    Project     = "US-Visa-Approval"
  }
}

# Public access block configuration for S3 bucket
resource "aws_s3_account_public_access_block" "public_access" {
  ignore_public_acls      = false
  block_public_acls       = false
  block_public_policy     = false
  restrict_public_buckets = false
}

# Upload trained model artifact to S3 bucket via Terraform
resource "aws_s3_object" "trained_model" {
  bucket = aws_s3_bucket.MLOps_Bucket.bucket
  key    = var.model_s3_key
  source = var.model_local_path

  etag = fileexists(var.model_local_path) ? filemd5(var.model_local_path) : null

  tags = {
    Type = "TrainedModelArtifact"
  }
}
