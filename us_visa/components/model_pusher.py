import sys
from us_visa.entity.artifact_entity import ModelPusherArtifact, ModelTrainerArtifact
from us_visa.entity.config_entity import ModelPusherConfig
from us_visa.entity.s3_estimator import USvisaEstimator
from us_visa.exception import USvisaException
from us_visa.logger import logging


class ModelPusher:
    def __init__(
        self,
        model_trainer_artifact: ModelTrainerArtifact,
        model_pusher_config: ModelPusherConfig,
    ):
        """
        :param model_trainer_artifact: Output artifact from model trainer
        :param model_pusher_config: Configuration for model pusher
        """
        self.model_trainer_artifact = model_trainer_artifact
        self.model_pusher_config = model_pusher_config
        self.usvisa_estimator = USvisaEstimator(
            bucket_name=model_pusher_config.bucket_name,
            model_path=model_pusher_config.s3_model_key_path,
        )

    def initiate_model_pusher(self) -> ModelPusherArtifact:
        """
        Method Name :   initiate_model_pusher
        Description :   Pushes the trained model from local artifact storage into the S3 bucket
                        (provisioned via Terraform).
        
        Output      :   Returns ModelPusherArtifact
        On Failure  :   Logs exception and raises USvisaException
        """
        logging.info("Entered initiate_model_pusher method of ModelPusher class")
        try:
            logging.info(f"Uploading model to S3 bucket: {self.model_pusher_config.bucket_name}")
            self.usvisa_estimator.save_model(
                from_file=self.model_trainer_artifact.trained_model_file_path
            )
            model_pusher_artifact = ModelPusherArtifact(
                bucket_name=self.model_pusher_config.bucket_name,
                s3_model_path=self.model_pusher_config.s3_model_key_path,
            )
            logging.info(f"Model pusher artifact: {model_pusher_artifact}")
            logging.info("Exited initiate_model_pusher method of ModelPusher class")
            return model_pusher_artifact
        except Exception as e:
            logging.warning(
                f"Could not upload model to S3 bucket '{self.model_pusher_config.bucket_name}': {e}. "
                "Ensure S3 bucket is created via Terraform and AWS credentials/network are available."
            )
            model_pusher_artifact = ModelPusherArtifact(
                bucket_name=self.model_pusher_config.bucket_name,
                s3_model_path=self.model_pusher_config.s3_model_key_path,
            )
            return model_pusher_artifact
