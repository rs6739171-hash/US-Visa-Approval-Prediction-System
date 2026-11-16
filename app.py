import os
import sys
from typing import Optional
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import uvicorn

from us_visa.constants import APP_HOST, APP_PORT
from us_visa.exception import USvisaException
from us_visa.logger import logging
from us_visa.pipline.prediction_pipeline import USvisaData, USvisaClassifier
from us_visa.pipline.training_pipeline import TrainPipeline


# Initialize FastAPI application
app = FastAPI(
    title="US Visa Approval Prediction System",
    description="Production-grade Machine Learning API & Web Interface for predicting US visa approval statuses.",
    version="1.0.0",
)

# Enable CORS for external frontends or integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets if static directory exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 template renderer
templates = Jinja2Templates(directory="templates")


# Pydantic schema for programmatic REST API predictions
class USvisaPredictRequest(BaseModel):
    continent: str = Field(..., example="Asia")
    education_of_employee: str = Field(..., example="Master's")
    has_job_experience: str = Field(..., example="Y")
    requires_job_training: str = Field(..., example="N")
    no_of_employees: int = Field(..., example=14513)
    yr_of_estab: int = Field(..., example=2007)
    region_of_employment: str = Field(..., example="West")
    prevailing_wage: float = Field(..., example=592.2029)
    unit_of_wage: str = Field(..., example="Hour")
    full_time_position: str = Field(..., example="Y")


@app.get("/health", tags=["Health Check"])
async def health_check():
    """
    Health check endpoint for container orchestrators (AWS ECS, Docker, ALB).
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "service": "US Visa Approval Prediction API"},
    )


@app.get("/", response_class=HTMLResponse, tags=["Web Interface"])
async def index_get(request: Request):
    """
    Renders the web frontend form for interactive manual predictions.
    """
    return templates.TemplateResponse(
        request=request,
        name="usvisa.html",
        context={"context": None},
    )


@app.post("/", response_class=HTMLResponse, tags=["Web Interface"])
async def index_post(request: Request):
    """
    Handles form submission from the web interface, runs prediction,
    and returns the rendered HTML page with prediction result.
    """
    try:
        form = await request.form()

        usvisa_data = USvisaData(
            continent=form.get("continent"),
            education_of_employee=form.get("education_of_employee"),
            has_job_experience=form.get("has_job_experience"),
            requires_job_training=form.get("requires_job_training"),
            no_of_employees=int(form.get("no_of_employees")),
            yr_of_estab=int(form.get("yr_of_estab")),
            region_of_employment=form.get("region_of_employment"),
            prevailing_wage=float(form.get("prevailing_wage")),
            unit_of_wage=form.get("unit_of_wage"),
            full_time_position=form.get("full_time_position"),
        )

        input_df = usvisa_data.get_usvisa_input_data_frame()
        classifier = USvisaClassifier()
        predictions = classifier.predict(input_df)

        status_result = predictions[0]
        logging.info(f"Web prediction generated successfully: {status_result}")

        return templates.TemplateResponse(
            request=request,
            name="usvisa.html",
            context={"context": status_result},
        )

    except Exception as e:
        logging.error(f"Error occurred during web prediction: {e}")
        return templates.TemplateResponse(
            request=request,
            name="usvisa.html",
            context={"context": f"Error: {str(e)}"},
        )


@app.post("/predict", tags=["REST API"])
async def predict_api(payload: USvisaPredictRequest):
    """
    REST API endpoint for programmatic inference via JSON payloads.
    """
    try:
        logging.info("Received prediction request via REST API")
        usvisa_data = USvisaData(
            continent=payload.continent,
            education_of_employee=payload.education_of_employee,
            has_job_experience=payload.has_job_experience,
            requires_job_training=payload.requires_job_training,
            no_of_employees=payload.no_of_employees,
            yr_of_estab=payload.yr_of_estab,
            region_of_employment=payload.region_of_employment,
            prevailing_wage=payload.prevailing_wage,
            unit_of_wage=payload.unit_of_wage,
            full_time_position=payload.full_time_position,
        )

        input_df = usvisa_data.get_usvisa_input_data_frame()
        classifier = USvisaClassifier()
        predictions = classifier.predict(input_df)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "prediction": predictions[0],
                "message": "Visa status prediction generated successfully.",
            },
        )

    except Exception as e:
        logging.error(f"Error during API prediction: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "error", "message": str(e)},
        )


@app.get("/train", tags=["Model Training"])
async def train_pipeline_trigger():
    """
    Triggers the end-to-end training pipeline asynchronously.
    """
    try:
        logging.info("Training pipeline triggered via /train endpoint")
        train_pipeline = TrainPipeline()
        train_pipeline.run_pipeline()
        return Response(content="Training pipeline executed successfully!", media_type="text/plain")
    except Exception as e:
        logging.error(f"Error executing training pipeline: {e}")
        return Response(content=f"Error executing training pipeline: {str(e)}", status_code=500)


if __name__ == "__main__":
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
