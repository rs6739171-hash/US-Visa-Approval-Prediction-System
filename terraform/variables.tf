variable "region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for infrastructure deployment"
}

variable "bucket_prefix" {
  type        = string
  default     = "mlops-bucket-"
  description = "Prefix for the S3 bucket name (must be lowercase)"
}

variable "model_local_path" {
  type        = string
  default     = "../artifact/model.pkl"
  description = "Local file path to the trained model.pkl to upload"
}

variable "model_s3_key" {
  type        = string
  default     = "model.pkl"
  description = "Target key/path of the model artifact inside the S3 bucket"
}
