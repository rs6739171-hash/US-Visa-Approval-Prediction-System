import json
import inspect
import unittest
from unittest.mock import MagicMock
from app import app, health_check, index_get, index_post, predict_api, USvisaPredictRequest


def run_sync(coro):
    """
    Executes a coroutine synchronously step-by-step without requiring
    an OS event loop socketpair, making it robust in restricted network environments.
    """
    while True:
        try:
            val = coro.send(None)
            if inspect.isawaitable(val):
                sub_res = run_sync(val)
                val = coro.send(sub_res)
        except StopIteration as e:
            return e.value


class TestApp(unittest.TestCase):

    def test_health_check(self):
        """Test the health check endpoint returns 200 and healthy status."""
        response = run_sync(health_check())
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.body.decode("utf-8"))
        self.assertEqual(body.get("status"), "healthy")

    def test_index_get(self):
        """Test GET / renders the prediction form HTML."""
        mock_request = MagicMock()
        response = run_sync(index_get(mock_request))
        self.assertEqual(response.status_code, 200)
        content = response.body.decode("utf-8")
        self.assertIn("US Visa Approval Prediction", content)
        self.assertIn("Predict Visa Status", content)

    def test_predict_api_certified(self):
        """Test REST API predicts Certified for qualifying applicant."""
        payload = USvisaPredictRequest(
            continent="South America",
            education_of_employee="Doctorate",
            has_job_experience="N",
            requires_job_training="N",
            no_of_employees=1221,
            yr_of_estab=1980,
            region_of_employment="South",
            prevailing_wage=31374.88,
            unit_of_wage="Year",
            full_time_position="Y",
        )
        response = run_sync(predict_api(payload))
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.body.decode("utf-8"))
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["prediction"], "Certified")

    def test_predict_api_denied(self):
        """Test REST API predicts Denied for non-qualifying applicant."""
        payload = USvisaPredictRequest(
            continent="North America",
            education_of_employee="Bachelor's",
            has_job_experience="N",
            requires_job_training="N",
            no_of_employees=2479,
            yr_of_estab=1978,
            region_of_employment="West",
            prevailing_wage=108.04,
            unit_of_wage="Hour",
            full_time_position="Y",
        )
        response = run_sync(predict_api(payload))
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.body.decode("utf-8"))
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["prediction"], "Denied")

    def test_index_post_certified(self):
        """Test POST / form submission renders Certified banner."""
        mock_request = MagicMock()
        mock_form_data = {
            "continent": "South America",
            "education_of_employee": "Doctorate",
            "has_job_experience": "N",
            "requires_job_training": "N",
            "no_of_employees": "1221",
            "yr_of_estab": "1980",
            "region_of_employment": "South",
            "prevailing_wage": "31374.88",
            "unit_of_wage": "Year",
            "full_time_position": "Y",
        }
        
        async def mock_form():
            return mock_form_data

        mock_request.form = mock_form
        response = run_sync(index_post(mock_request))
        self.assertEqual(response.status_code, 200)
        content = response.body.decode("utf-8")
        self.assertIn("Visa Status: Certified", content)

    def test_index_post_denied(self):
        """Test POST / form submission renders Denied banner."""
        mock_request = MagicMock()
        mock_form_data = {
            "continent": "North America",
            "education_of_employee": "Bachelor's",
            "has_job_experience": "N",
            "requires_job_training": "N",
            "no_of_employees": "2479",
            "yr_of_estab": "1978",
            "region_of_employment": "West",
            "prevailing_wage": "108.04",
            "unit_of_wage": "Hour",
            "full_time_position": "Y",
        }
        
        async def mock_form():
            return mock_form_data

        mock_request.form = mock_form
        response = run_sync(index_post(mock_request))
        self.assertEqual(response.status_code, 200)
        content = response.body.decode("utf-8")
        self.assertIn("Visa Status: Denied", content)

    def test_index_post_with_small_company_age_input(self):
        """Test POST / with a company age like 22 renders successfully without validation error."""
        mock_request = MagicMock()
        mock_form_data = {
            "continent": "Asia",
            "education_of_employee": "Doctorate",
            "has_job_experience": "Y",
            "requires_job_training": "N",
            "no_of_employees": "1500",
            "yr_of_estab": "22",
            "region_of_employment": "Northeast",
            "prevailing_wage": "700",
            "unit_of_wage": "Month",
            "full_time_position": "N",
        }

        async def mock_form():
            return mock_form_data

        mock_request.form = mock_form
        response = run_sync(index_post(mock_request))
        self.assertEqual(response.status_code, 200)
        content = response.body.decode("utf-8")
        self.assertIn("Visa Status:", content)

    def test_index_post_invalid_input(self):
        """Test POST / handles invalid input gracefully without crashing."""
        mock_request = MagicMock()
        mock_form_data = {
            "continent": "Asia",
            "education_of_employee": "Master's",
            "no_of_employees": "invalid_integer",
        }

        async def mock_form():
            return mock_form_data

        mock_request.form = mock_form
        response = run_sync(index_post(mock_request))
        self.assertEqual(response.status_code, 200)
        content = response.body.decode("utf-8")
        self.assertIn("Error:", content)


if __name__ == "__main__":
    unittest.main()
