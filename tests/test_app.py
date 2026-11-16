import asyncio
import unittest
from unittest.mock import MagicMock
from app import app, health_check, index_get, index_post, predict_api, USvisaPredictRequest


class TestApp(unittest.TestCase):

    def test_health_check(self):
        response = asyncio.run(health_check())
        self.assertEqual(response.status_code, 200)

    def test_index_get(self):
        mock_request = MagicMock()
        response = asyncio.run(index_get(mock_request))
        self.assertEqual(response.status_code, 200)

    def test_predict_api(self):
        payload = USvisaPredictRequest(
            continent="Europe",
            education_of_employee="Doctorate",
            has_job_experience="Y",
            requires_job_training="N",
            no_of_employees=50000,
            yr_of_estab=1995,
            region_of_employment="Northeast",
            prevailing_wage=150000.0,
            unit_of_wage="Year",
            full_time_position="Y",
        )
        response = asyncio.run(predict_api(payload))
        self.assertEqual(response.status_code, 200)

    def test_index_post(self):
        mock_request = MagicMock()
        mock_form_data = {
            "continent": "Asia",
            "education_of_employee": "Master's",
            "has_job_experience": "Y",
            "requires_job_training": "N",
            "no_of_employees": "14513",
            "region_of_employment": "West",
            "prevailing_wage": "592.2029",
            "unit_of_wage": "Hour",
            "full_time_position": "Y",
            "yr_of_estab": "2007",
        }
        
        async def mock_form():
            return mock_form_data

        mock_request.form = mock_form
        response = asyncio.run(index_post(mock_request))
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
