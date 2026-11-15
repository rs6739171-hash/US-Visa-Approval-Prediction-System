# 🇺🇸 US Visa Approval Prediction System

An end-to-end, production-grade Machine Learning & MLOps project that predicts whether a US visa application will be **Certified** or **Denied** based on applicant qualifications, employer attributes, and prevailing wage metrics.

---

## 📌 Project Overview

Every year, millions of foreign professionals apply for US work visas. The manual evaluation process is labor-intensive, time-consuming, and prone to backlogs. This project builds a complete automated prediction engine using machine learning classification models, deployed as a scalable **FastAPI** web application with automated CI/CD deployment pipelines on **AWS**.

---

## 🛠️ Tech Stack & Tools

* **Core Language:** Python (3.10)
* **Machine Learning & Modeling:** `scikit-learn`, `xgboost`, `catboost`, `imbalanced-learn`
* **Data Processing:** `pandas`, `numpy`, `scipy`
* **Data Visualization:** `matplotlib`, `seaborn`, `plotly`
* **Database:** `MongoDB Atlas` (cloud data store)
* **Model Serialization:** `dill`
* **Web Framework:** `FastAPI`, `uvicorn`, `Jinja2`
* **Cloud & Storage:** `AWS S3` (artifact/model registry), `AWS ECR`, `AWS EC2`
* **Data Drift & Monitoring:** `Evidently AI`
* **DevOps & Containerization:** `Docker`, `GitHub Actions` (CI/CD)

---

## 📂 Project Architecture & Directory Structure

```text
US-Visa-Approval-Prediction-System/
│
├── config/
│   ├── model.yaml                    # Model hyperparameters and evaluation thresholds
│   └── schema.yaml                   # Dataset schema and column type definitions
│
├── notebook/
│   ├── Visadataset.csv               # Raw dataset
│   └── mongodb_demo.ipynb            # MongoDB connection & data upload prototype
│
├── us_visa/                          # Core application package
│   ├── components/                   # Modular pipeline components
│   │   ├── data_ingestion.py         # Pulls data from MongoDB & performs train-test split
│   │   ├── data_validation.py        # Schema validation & data drift detection
│   │   ├── data_transformation.py    # Preprocessing, scaling, encoding & SMOTE
│   │   ├── model_trainer.py          # Model training & hyperparameter tuning
│   │   ├── model_evaluation.py       # Performance evaluation against S3 production model
│   │   └── model_pusher.py           # Pushes winning model & preprocessor to S3
│   │
│   ├── configuration/                # Cloud & database connection configs
│   │   ├── aws_connection.py         # AWS S3 client management
│   │   └── mongo_db_connection.py    # MongoDB Atlas connection client
│   │
│   ├── constants/                    # Project-wide constants & pipeline configurations
│   ├── entity/                       # Data contract dataclasses (config & artifact entities)
│   ├── exception/                    # Custom exception handling with file & line tracing
│   ├── logger/                       # Custom timestamped file & console logging
│   ├── pipline/                      # Training & Prediction execution pipelines
│   └── utils/                        # Common helper utilities (YAML, dill, numpy, etc.)
│
├── app.py                            # FastAPI entry point for web UI and REST API
├── demo.py                           # Pipeline testing & demonstration script
├── Dockerfile                        # Docker container configuration
├── requirements.txt                  # Python dependencies
├── setup.py                          # Packaging script for editable install (-e .)
└── README.md
```

---

## 🔄 Machine Learning Pipeline Workflow

1. **Data Ingestion**:
   * Reads raw records from MongoDB Atlas.
   * Exports dataset into feature store and splits into training and testing sets.
2. **Data Validation**:
   * Validates dataset columns, data types, and value distributions against `config/schema.yaml`.
   * Checks for data drift between reference and current datasets using Evidently.
3. **Data Transformation**:
   * Performs imputation, standard scaling, and one-hot encoding on categorical features.
   * Balances target classes (`Certified` vs `Denied`) using SMOTE (`imbalanced-learn`).
   * Saves the fitted preprocessor artifact (`preprocessing.pkl`).
4. **Model Trainer**:
   * Trains multiple classification models (e.g., Random Forest, XGBoost, CatBoost).
   * Performs hyperparameter tuning and evaluates test metrics (Accuracy, F1-Score, Precision, Recall).
5. **Model Evaluation & Pusher**:
   * Compares the newly trained model against the currently active production model stored in AWS S3.
   * If the new model achieves better performance above the acceptance threshold, it is pushed to the AWS S3 production bucket.

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/US-Visa-Approval-Prediction-System.git
cd US-Visa-Approval-Prediction-System
```

### 2. Create and Activate Virtual Environment
> [!IMPORTANT]
> Python **3.10** is recommended for full compatibility with legacy MLOps dependencies.

```bash
# Using Conda:
conda create -n visa python=3.10 -y
conda activate visa

# Or using uv:
uv venv --python 3.10
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:

```env
MONGODB_URL="mongodb+srv://<username>:<password>@cluster0.xxx.mongodb.net/?retryWrites=true&w=majority"
AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
AWS_DEFAULT_REGION="us-east-1"
```

---

## 💻 Running the Application

### Train the Pipeline
To trigger the automated training pipeline and push artifacts:
```bash
python demo.py
```

### Launch the Web App
Start the FastAPI server:
```bash
python app.py
```
Open your browser and navigate to:
* **Web Interface:** `http://localhost:8080`
* **API Documentation (Swagger UI):** `http://localhost:8080/docs`

---

## 🐳 Docker & CI/CD Deployment

### Build & Run via Docker
```bash
# Build Docker image
docker build -t us-visa-app .

# Run Docker container
docker run -p 8080:8080 --env-file .env us-visa-app
```

### CI/CD Pipeline (GitHub Actions & AWS)
1. Code pushed to the `main` branch triggers the GitHub Actions workflow.
2. Continuous Integration runs linting and unit tests.
3. Continuous Delivery builds the Docker image and pushes it to **Amazon ECR**.
4. Continuous Deployment pulls the latest image onto an **Amazon EC2** instance and runs the containerized FastAPI service.

---

## 📜 License
This project is licensed under the [MIT License](LICENSE).
