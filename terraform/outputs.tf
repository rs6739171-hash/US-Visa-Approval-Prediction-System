output "s3_bucket_name" {
  value       = aws_s3_bucket.MLOps_Bucket.bucket
  description = "The name of the provisioned S3 bucket"
}

output "s3_model_uri" {
  value       = "s3://${aws_s3_bucket.MLOps_Bucket.bucket}/${aws_s3_object.trained_model.key}"
  description = "The full S3 URI of the model uploaded via Terraform"
}
