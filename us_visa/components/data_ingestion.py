import os
import sys
import numpy as np
import pandas as pd
from pandas import DataFrame
from sklearn.model_selection import train_test_split

from us_visa.configuration.mongo_db_connection import MongoDBClient
from us_visa.constants import DATABASE_NAME
from us_visa.entity.config_entity import DataIngestionConfig
from us_visa.entity.artifact_entity import DataIngestionArtifact
from us_visa.exception import USvisaException
from us_visa.logger import logging


class DataIngestion:
    def __init__(self, data_ingestion_config: DataIngestionConfig = DataIngestionConfig()):
        """
        :param data_ingestion_config: configuration for data ingestion
        """
        try:
            self.data_ingestion_config = data_ingestion_config
        except Exception as e:
            raise USvisaException(e, sys)

    def export_data_into_feature_store(self) -> DataFrame:
        """
        Method Name :   export_data_into_feature_store
        Description :   This method exports data from MongoDB into feature store
        
        Output      :   Returns data as pandas DataFrame
        On Failure  :   Raises USvisaException
        """
        try:
            logging.info("Exporting data from mongodb")
            try:
                mongo_client = MongoDBClient(database_name=DATABASE_NAME)
                collection = mongo_client.database[self.data_ingestion_config.collection_name]
                
                df = pd.DataFrame(list(collection.find()))
                logging.info(f"Shape of dataframe fetched from MongoDB: {df.shape}")

                if len(df) == 0:
                    raise Exception("No documents found in MongoDB collection")

                if "_id" in df.columns:
                    df = df.drop(columns=["_id"])
            except Exception as mongo_err:
                logging.warning(
                    f"MongoDB connection/fetch failed: {mongo_err}. "
                    "Falling back to local Visadataset.csv..."
                )
                local_data_path = os.path.join("notebook", "Visadataset.csv")
                if not os.path.exists(local_data_path):
                    local_data_path = "Visadataset.csv"
                if os.path.exists(local_data_path):
                    df = pd.read_csv(local_data_path)
                    logging.info(f"Successfully loaded {len(df)} records from local dataset: {local_data_path}")
                else:
                    raise mongo_err

            df.replace({"na": np.nan}, inplace=True)

            feature_store_file_path = self.data_ingestion_config.feature_store_file_path
            dir_path = os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path, exist_ok=True)
            logging.info(f"Saving exported data into feature store file path: {feature_store_file_path}")
            df.to_csv(feature_store_file_path, index=False, header=True)
            return df
        except Exception as e:
            raise USvisaException(e, sys)

    def split_data_as_train_test(self, dataframe: DataFrame) -> None:
        """
        Method Name :   split_data_as_train_test
        Description :   This method splits the dataframe into train and test sets
        
        Output      :   Saves train.csv and test.csv into ingested directory
        On Failure  :   Raises USvisaException
        """
        try:
            logging.info("Entered split_data_as_train_test method of DataIngestion class")
            train_set, test_set = train_test_split(
                dataframe, test_size=self.data_ingestion_config.train_test_split_ratio
            )
            logging.info("Performed train test split on the dataframe")

            dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)
            os.makedirs(dir_path, exist_ok=True)

            logging.info("Exporting train and test file path.")
            train_set.to_csv(self.data_ingestion_config.training_file_path, index=False, header=True)
            test_set.to_csv(self.data_ingestion_config.testing_file_path, index=False, header=True)
            logging.info("Exported train and test file path successfully.")
        except Exception as e:
            raise USvisaException(e, sys)

    def initiate_data_ingestion(self) -> DataIngestionArtifact:
        """
        Method Name :   initiate_data_ingestion
        Description :   This method initiates the data ingestion components of training pipeline
        
        Output      :   train set and test set are created as the data ingestion artifacts
        On Failure  :   Raises USvisaException
        """
        try:
            logging.info("Entered initiate_data_ingestion method of DataIngestion class")
            dataframe = self.export_data_into_feature_store()
            self.split_data_as_train_test(dataframe=dataframe)

            data_ingestion_artifact = DataIngestionArtifact(
                trained_file_path=self.data_ingestion_config.training_file_path,
                test_file_path=self.data_ingestion_config.testing_file_path,
            )
            logging.info(f"Data ingestion artifact: {data_ingestion_artifact}")
            logging.info("Exited initiate_data_ingestion method of DataIngestion class")
            return data_ingestion_artifact
        except Exception as e:
            raise USvisaException(e, sys)
