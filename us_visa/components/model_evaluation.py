from dataclasses import dataclass
import sys
from typing import Optional
import pandas as pd
from sklearn.metrics import f1_score

from us_visa.constants import TARGET_COLUMN, CURRENT_YEAR
from us_visa.entity.artifact_entity import (
    DataIngestionArtifact,
    ModelTrainerArtifact,
    ModelEvaluationArtifact,
)
from us_visa.entity.config_entity import ModelEvaluationConfig
from us_visa.entity.estimator import TargetValueMapping
from us_visa.entity.s3_estimator import USvisaEstimator
from us_visa.exception import USvisaException
from us_visa.logger import logging
from us_visa.utils.main_utils import load_object


@dataclass
class EvaluateModelResponse:
    trained_model_f1_score: float
    best_model_f1_score: Optional[float]
    is_model_accepted: bool
    difference: float


class ModelEvaluation:
    def __init__(
        self,
        model_eval_config: ModelEvaluationConfig,
        data_ingestion_artifact: DataIngestionArtifact,
        model_trainer_artifact: ModelTrainerArtifact,
    ):
        """
        :param model_eval_config: Configuration for model evaluation
        :param data_ingestion_artifact: Output artifact from data ingestion
        :param model_trainer_artifact: Output artifact from model trainer
        """
        try:
            self.model_eval_config = model_eval_config
            self.data_ingestion_artifact = data_ingestion_artifact
            self.model_trainer_artifact = model_trainer_artifact
        except Exception as e:
            raise USvisaException(e, sys) from e

    def get_best_model(self) -> Optional[USvisaEstimator]:
        """
        Method Name :   get_best_model
        Description :   Fetches the production model from the S3 bucket provisioned via Terraform if available.
        
        Output      :   Returns USvisaEstimator if model is present, otherwise None
        On Failure  :   Logs info and returns None
        """
        try:
            bucket_name = self.model_eval_config.bucket_name
            model_path = self.model_eval_config.s3_model_key_path
            usvisa_estimator = USvisaEstimator(bucket_name=bucket_name, model_path=model_path)

            if usvisa_estimator.is_model_present(model_path=model_path):
                return usvisa_estimator
            return None
        except Exception as e:
            logging.info(f"No active model retrieved from Terraform S3 bucket: {e}")
            return None

    def evaluate_model(self) -> EvaluateModelResponse:
        """
        Method Name :   evaluate_model
        Description :   Evaluates the newly trained model against the S3 production model (if present)
                        on held-out test data.
        
        Output      :   Returns EvaluateModelResponse with metrics and acceptance decision
        On Failure  :   Logs error and raises USvisaException
        """
        try:
            test_df = pd.read_csv(self.data_ingestion_artifact.test_file_path)
            logging.info(f"Loaded test dataset from: {self.data_ingestion_artifact.test_file_path}")

            # Feature engineering: calculate company_age and drop unneeded columns
            test_df["company_age"] = CURRENT_YEAR - test_df["yr_of_estab"]
            drop_cols = [TARGET_COLUMN, "case_id", "yr_of_estab"]
            x = test_df.drop(columns=drop_cols, errors="ignore")
            y = test_df[TARGET_COLUMN].replace(TargetValueMapping()._asdict()).astype(int)

            # Evaluate newly trained candidate model
            trained_model = load_object(file_path=self.model_trainer_artifact.trained_model_file_path)
            trained_model_y_pred = trained_model.predict(x)
            trained_model_f1_score = f1_score(y, trained_model_y_pred)
            logging.info(f"Trained model F1 score on test data: {trained_model_f1_score}")

            # Evaluate existing production model in Terraform S3 bucket
            best_model_f1_score = None
            best_model = self.get_best_model()

            if best_model is not None:
                logging.info("Existing production model found in S3. Evaluating production model...")
                y_best_pred = best_model.predict(x)
                best_model_f1_score = f1_score(y, y_best_pred)
                logging.info(f"Production model F1 score on test data: {best_model_f1_score}")

            tmp_best_model_score = 0 if best_model_f1_score is None else best_model_f1_score
            difference = trained_model_f1_score - tmp_best_model_score
            is_model_accepted = difference > self.model_eval_config.changed_threshold_score

            response = EvaluateModelResponse(
                trained_model_f1_score=trained_model_f1_score,
                best_model_f1_score=best_model_f1_score,
                is_model_accepted=is_model_accepted,
                difference=difference,
            )
            logging.info(f"Model evaluation response: {response}")
            return response

        except Exception as e:
            raise USvisaException(e, sys) from e

    def initiate_model_evaluation(self) -> ModelEvaluationArtifact:
        """
        Method Name :   initiate_model_evaluation
        Description :   Initiates the evaluation process and constructs the ModelEvaluationArtifact.
        
        Output      :   Returns ModelEvaluationArtifact
        On Failure  :   Logs error and raises USvisaException
        """
        try:
            logging.info("Entered initiate_model_evaluation method of ModelEvaluation class")
            evaluate_model_response = self.evaluate_model()
            s3_model_path = self.model_eval_config.s3_model_key_path

            model_evaluation_artifact = ModelEvaluationArtifact(
                is_model_accepted=evaluate_model_response.is_model_accepted,
                changed_accuracy=evaluate_model_response.difference,
                s3_model_path=s3_model_path,
                trained_model_path=self.model_trainer_artifact.trained_model_file_path,
            )
            logging.info(f"Model evaluation artifact: {model_evaluation_artifact}")
            logging.info("Exited initiate_model_evaluation method of ModelEvaluation class")
            return model_evaluation_artifact

        except Exception as e:
            raise USvisaException(e, sys) from e
