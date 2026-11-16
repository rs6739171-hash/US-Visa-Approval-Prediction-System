import os
import unittest
import pandas as pd
import numpy as np

from us_visa.constants import CURRENT_YEAR
from us_visa.pipline.prediction_pipeline import USvisaData, USvisaClassifier
from us_visa.exception import USvisaException


class TestPredictionPipeline(unittest.TestCase):

    def setUp(self):
        self.sample_payload = {
            "continent": "Asia",
            "education_of_employee": "Master's",
            "has_job_experience": "Y",
            "requires_job_training": "N",
            "no_of_employees": 14513,
            "region_of_employment": "West",
            "prevailing_wage": 592.2029,
            "unit_of_wage": "Hour",
            "full_time_position": "Y",
            "yr_of_estab": 2007,
        }

    def test_usvisa_data_creation_with_yr_of_estab(self):
        """Test USvisaData properly calculates company_age from yr_of_estab"""
        visa_data = USvisaData(**self.sample_payload)
        df = visa_data.get_usvisa_input_data_frame()

        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertIn("company_age", df.columns)
        self.assertNotIn("yr_of_estab", df.columns)
        self.assertEqual(df["company_age"].iloc[0], CURRENT_YEAR - 2007)
        self.assertEqual(df["continent"].iloc[0], "Asia")

    def test_usvisa_data_creation_with_small_number_as_company_age(self):
        """Test USvisaData handles small numbers like 22 as direct company age"""
        payload = self.sample_payload.copy()
        payload["yr_of_estab"] = 22

        visa_data = USvisaData(**payload)
        df = visa_data.get_usvisa_input_data_frame()

        self.assertEqual(df["company_age"].iloc[0], 22)
        self.assertNotIn("yr_of_estab", df.columns)

    def test_usvisa_data_creation_with_direct_company_age(self):
        """Test USvisaData when company_age is directly supplied"""
        payload = self.sample_payload.copy()
        payload.pop("yr_of_estab")
        payload["company_age"] = 15

        visa_data = USvisaData(**payload)
        df = visa_data.get_usvisa_input_data_frame()

        self.assertEqual(df["company_age"].iloc[0], 15)
        self.assertNotIn("yr_of_estab", df.columns)

    def test_usvisa_data_missing_age_raises_exception(self):
        """Test that omitting both yr_of_estab and company_age raises USvisaException"""
        payload = self.sample_payload.copy()
        payload.pop("yr_of_estab")

        visa_data = USvisaData(**payload)
        with self.assertRaises(USvisaException):
            visa_data.get_usvisa_input_data_frame()

    def test_single_record_prediction(self):
        """Test USvisaClassifier predicts either 'Certified' or 'Denied' for a single record"""
        visa_data = USvisaData(**self.sample_payload)
        df = visa_data.get_usvisa_input_data_frame()

        classifier = USvisaClassifier()
        predictions = classifier.predict(df)

        self.assertIsInstance(predictions, np.ndarray)
        self.assertEqual(len(predictions), 1)
        self.assertIn(predictions[0], ["Certified", "Denied"])

    def test_batch_record_prediction(self):
        """Test USvisaClassifier predicts on batch DataFrame records"""
        sample_1 = USvisaData(**self.sample_payload).get_usvisa_input_data_frame()
        sample_2_payload = self.sample_payload.copy()
        sample_2_payload.update({
            "continent": "Europe",
            "education_of_employee": "Doctorate",
            "prevailing_wage": 120000.0,
            "unit_of_wage": "Year",
            "yr_of_estab": 1998,
        })
        sample_2 = USvisaData(**sample_2_payload).get_usvisa_input_data_frame()

        batch_df = pd.concat([sample_1, sample_2], ignore_index=True)

        classifier = USvisaClassifier()
        predictions = classifier.predict(batch_df)

        self.assertEqual(len(predictions), 2)
        for pred in predictions:
            self.assertIn(pred, ["Certified", "Denied"])


if __name__ == "__main__":
    unittest.main()
