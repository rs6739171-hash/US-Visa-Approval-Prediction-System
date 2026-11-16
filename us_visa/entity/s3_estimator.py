import os
import sys
import dill
import boto3
from botocore.exceptions import ClientError
from pandas import DataFrame

from us_visa.constants import (
    AWS_ACCESS_KEY_ID_ENV_KEY,
    AWS_SECRET_ACCESS_KEY_ENV_KEY,
    REGION_NAME,
)
from us_visa.entity.estimator import USvisaModel
from us_visa.exception import USvisaException
from us_visa.logger import logging


class USvisaEstimator:
    """
    Handles retrieving, checking, and persisting USvisaModel from/to
    the AWS S3 bucket provisioned via Terraform.
    """

    def __init__(self, bucket_name: str, model_path: str, region_name: str = REGION_NAME):
        """
        :param bucket_name: Name of the AWS S3 bucket created via Terraform
        :param model_path: S3 key/path of the model artifact (e.g. model.pkl)
        :param region_name: AWS region (defaults to us-east-1 as set in Terraform)
        """
        self.bucket_name = bucket_name
        self.model_path = model_path
        self.region_name = region_name
        self._s3_client = None
        self.loaded_model: USvisaModel = None

    @property
    def s3_client(self):
        """
        Initializes and returns boto3 S3 client using environment credentials.
        """
        if self._s3_client is None:
            access_key = os.getenv(AWS_ACCESS_KEY_ID_ENV_KEY) or os.getenv("AWS_ACCESS_KEY")
            secret_key = os.getenv(AWS_SECRET_ACCESS_KEY_ENV_KEY)
            region = os.getenv("AWS_DEFAULT_REGION", self.region_name)

            self._s3_client = boto3.client(
                "s3",
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
            )
        return self._s3_client

    def is_model_present(self, model_path: str = None) -> bool:
        """
        Checks whether the model exists in the Terraform S3 bucket.
        """
        key = model_path or self.model_path
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            logging.info(f"Model found in S3 bucket: s3://{self.bucket_name}/{key}")
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("404", "NoSuchKey", "NoSuchBucket"):
                logging.info(f"Model not present in S3 bucket (Error Code: {error_code})")
                return False
            logging.warning(f"S3 ClientError while verifying model presence: {e}")
            return False
        except Exception as e:
            logging.warning(f"Could not reach S3 bucket '{self.bucket_name}': {e}")
            return False

    def load_model(self) -> USvisaModel:
        """
        Downloads and deserializes the USvisaModel from S3.
        """
        try:
            logging.info(f"Downloading model from s3://{self.bucket_name}/{self.model_path}")
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=self.model_path)
            model_bytes = response["Body"].read()
            return dill.loads(model_bytes)
        except Exception as e:
            raise USvisaException(e, sys) from e

    def save_model(self, from_file: str, remove: bool = False) -> None:
        """
        Uploads the local model file to the Terraform S3 bucket.
        """
        try:
            logging.info(f"Uploading model {from_file} to s3://{self.bucket_name}/{self.model_path}")
            self.s3_client.upload_file(from_file, self.bucket_name, self.model_path)
            logging.info(f"Successfully uploaded model to s3://{self.bucket_name}/{self.model_path}")
            if remove and os.path.exists(from_file):
                os.remove(from_file)
        except Exception as e:
            raise USvisaException(e, sys) from e

    def predict(self, dataframe: DataFrame):
        """
        Runs inference using the S3-loaded model.
        """
        try:
            if self.loaded_model is None:
                self.loaded_model = self.load_model()
            return self.loaded_model.predict(dataframe=dataframe)
        except Exception as e:
            raise USvisaException(e, sys) from e
