import os
import sys
import pymongo
import certifi
from dotenv import load_dotenv

from us_visa.constants import DATABASE_NAME, MONGODB_URL_KEY
from us_visa.exception import USvisaException
from us_visa.logger import logging

load_dotenv()
ca = certifi.where()


class MongoDBClient:
    """
    Class Name :   MongoDBClient
    Description :   This class creates a singleton connection to the MongoDB Atlas database.
    
    Output      :   Connection to MongoDB database
    On Failure  :   Raises USvisaException
    """
    client = None

    def __init__(self, database_name=DATABASE_NAME) -> None:
        try:
            if MongoDBClient.client is None:
                mongo_db_url = os.getenv(MONGODB_URL_KEY)
                if mongo_db_url is None:
                    # Fallback in case MONGODB_URL_KEY directly holds the connection string
                    if MONGODB_URL_KEY and str(MONGODB_URL_KEY).startswith("mongodb"):
                        mongo_db_url = MONGODB_URL_KEY
                    else:
                        raise Exception(f"Environment key: {MONGODB_URL_KEY} is not set.")
                
                if "localhost" in mongo_db_url:
                    MongoDBClient.client = pymongo.MongoClient(mongo_db_url)
                else:
                    # Standard connection first (default system SSL, works on Windows without TLS alert)
                    try:
                        client = pymongo.MongoClient(mongo_db_url)
                        client.admin.command('ping')
                        MongoDBClient.client = client
                        logging.info("MongoDB client connected using default TLS.")
                    except Exception as err:
                        logging.warning(f"Default connection failed ({err}), falling back to certifi CA bundle...")
                        try:
                            client = pymongo.MongoClient(mongo_db_url, tlsCAFile=ca)
                            client.admin.command('ping')
                            MongoDBClient.client = client
                            logging.info("MongoDB client connected using certifi CA bundle.")
                        except Exception as err2:
                            logging.warning(f"certifi connection failed ({err2}), trying with tlsAllowInvalidCertificates...")
                            client = pymongo.MongoClient(
                                mongo_db_url,
                                tls=True,
                                tlsAllowInvalidCertificates=True
                            )
                            client.admin.command('ping')
                            MongoDBClient.client = client
                            logging.info("MongoDB client connected with tlsAllowInvalidCertificates=True.")
            
            self.client = MongoDBClient.client
            self.database = self.client[database_name]
            self.database_name = database_name
            logging.info("MongoDB connection successful")
        except Exception as e:
            raise USvisaException(e, sys)
