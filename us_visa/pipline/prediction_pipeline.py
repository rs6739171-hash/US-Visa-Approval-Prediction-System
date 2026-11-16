import os
import sys
from typing import Optional
import numpy as np
import pandas as pd
from pandas import DataFrame

from us_visa.constants import CURRENT_YEAR
from us_visa.entity.config_entity import USvisaPredictorConfig
from us_visa.entity.estimator import TargetValueMapping
from us_visa.entity.s3_estimator import USvisaEstimator
from us_visa.exception import USvisaException
from us_visa.logger import logging
from us_visa.utils.main_utils import load_object


class USvisaData:
    """
    Class responsible for mapping single or batch user input data
    into a pandas DataFrame formatted for model prediction.
    """

    def __init__(
        self,
        continent: str,
        education_of_employee: str,
        has_job_experience: str,
        requires_job_training: str,
        no_of_employees: int,
        region_of_employment: str,
        prevailing_wage: float,
        unit_of_wage: str,
        full_time_position: str,
        yr_of_estab: Optional[int] = None,
        company_age: Optional[int] = None,
    ):
        """
        :param continent: Continent of employee
        :param education_of_employee: Education level
        :param has_job_experience: Y or N
        :param requires_job_training: Y or N
        :param no_of_employees: Number of employees in company
        :param region_of_employment: Employment region (e.g. West, South, etc.)
        :param prevailing_wage: Prevailing wage amount
        :param unit_of_wage: Hour, Year, Month, Week
        :param full_time_position: Y or N
        :param yr_of_estab: Year of establishment of company
        :param company_age: Age of company in years (optional, auto-derived from yr_of_estab if omitted)
        """
        try:
            self.continent = continent
            self.education_of_employee = education_of_employee
            self.has_job_experience = has_job_experience
            self.requires_job_training = requires_job_training
            self.no_of_employees = no_of_employees
            self.region_of_employment = region_of_employment
            self.prevailing_wage = prevailing_wage
            self.unit_of_wage = unit_of_wage
            self.full_time_position = full_time_position
            self.yr_of_estab = yr_of_estab
            self.company_age = company_age
        except Exception as e:
            raise USvisaException(e, sys) from e

    def get_usvisa_input_data_frame(self) -> DataFrame:
        """
        Converts input values to DataFrame with expected feature names.
        """
        try:
            input_dict = self.get_usvisa_data_as_dict()
            df = DataFrame(input_dict)

            # Auto-calculate company_age if not provided
            if "company_age" not in df.columns or df["company_age"].iloc[0] is None:
                if self.yr_of_estab is not None:
                    yr = int(self.yr_of_estab)
                    # If user enters a small value (<= 150), treat it directly as company age in years (e.g. 22 -> 22 yrs)
                    # Otherwise, if it's a calendar year (e.g. 1995, 2005), calculate CURRENT_YEAR - yr
                    if yr <= 150:
                        df["company_age"] = max(0, yr)
                    else:
                        df["company_age"] = max(0, CURRENT_YEAR - yr)
                else:
                    raise Exception("Either yr_of_estab or company_age must be provided.")

            # Drop yr_of_estab so input columns match preprocessor requirements
            if "yr_of_estab" in df.columns:
                df.drop(columns=["yr_of_estab"], inplace=True)

            return df
        except Exception as e:
            raise USvisaException(e, sys) from e

    def get_usvisa_data_as_dict(self) -> dict:
        """
        Returns input data formatted as dictionary of lists.
        """
        try:
            input_data = {
                "continent": [self.continent],
                "education_of_employee": [self.education_of_employee],
                "has_job_experience": [self.has_job_experience],
                "requires_job_training": [self.requires_job_training],
                "no_of_employees": [self.no_of_employees],
                "region_of_employment": [self.region_of_employment],
                "prevailing_wage": [self.prevailing_wage],
                "unit_of_wage": [self.unit_of_wage],
                "full_time_position": [self.full_time_position],
            }
            if self.company_age is not None:
                input_data["company_age"] = [self.company_age]
            elif self.yr_of_estab is not None:
                input_data["yr_of_estab"] = [self.yr_of_estab]

            return input_data
        except Exception as e:
            raise USvisaException(e, sys) from e


class USvisaClassifier:
    """
    Class responsible for loading the trained model (from AWS S3 bucket
    or local fallback) and generating prediction labels ('Certified' / 'Denied').
    """
    _cached_model = None

    def __init__(
        self,
        prediction_pipeline_config: USvisaPredictorConfig = USvisaPredictorConfig(),
    ):
        """
        :param prediction_pipeline_config: Configuration for prediction pipeline
        """
        try:
            self.prediction_pipeline_config = prediction_pipeline_config
        except Exception as e:
            raise USvisaException(e, sys) from e

    @classmethod
    def invalidate_cache(cls):
        """Invalidates in-memory cached model so freshly trained model is loaded."""
        cls._cached_model = None

    def get_model(self):
        """Loads model from local artifact storage or from AWS S3."""
        model = None
        # 1. Local artifact check
        local_model_path = os.path.join("artifact", "model.pkl")
        if not os.path.exists(local_model_path):
            import glob
            candidates = glob.glob(
                os.path.join("artifact", "*", "model_trainer", "trained_model", "model.pkl")
            )
            if candidates:
                local_model_path = candidates[-1]

        if os.path.exists(local_model_path):
            logging.info(f"Loading local model from {local_model_path}")
            return load_object(local_model_path)

        # 2. Attempt loading model from S3 using USvisaEstimator
        try:
            usvisa_estimator = USvisaEstimator(
                bucket_name=self.prediction_pipeline_config.model_bucket_name,
                model_path=self.prediction_pipeline_config.model_file_path,
            )
            if usvisa_estimator.is_model_present():
                logging.info("Production model successfully located in S3 bucket")
                return usvisa_estimator
        except Exception as e:
            logging.info(f"Could not load model from S3: {e}")

        raise Exception("Model not found in local artifact directory or AWS S3 bucket.")

    def predict(self, dataframe: DataFrame) -> np.ndarray:
        """
        Runs model prediction on the given DataFrame.
        
        :param dataframe: DataFrame containing input applicant features
        :return: np.ndarray of prediction strings e.g. ['Certified'] or ['Denied']
        """
        try:
            logging.info("Entered predict method of USvisaClassifier class")
            if USvisaClassifier._cached_model is None:
                USvisaClassifier._cached_model = self.get_model()

            model = USvisaClassifier._cached_model
            predictions = model.predict(dataframe)

            # Map predictions: 0 -> Certified, 1 -> Denied
            target_mapping = TargetValueMapping().reverse_mapping()
            result = [target_mapping.get(int(pred), str(pred)) for pred in predictions]
            logging.info(f"Generated predictions: {result}")
            return np.array(result)

        except Exception as e:
            raise USvisaException(e, sys) from e
