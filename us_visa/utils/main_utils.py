import os
import sys
import numpy as np
import pandas as pd
import dill
import yaml

from us_visa.exception import USvisaException
from us_visa.logger import logging


def read_yaml_file(file_path: str) -> dict:
    """
    Reads a YAML file and returns its content as a dictionary.
    """
    try:
        with open(file_path, "rb") as yaml_file:
            return yaml.safe_load(yaml_file)
    except Exception as e:
        raise USvisaException(e, sys) from e


def write_yaml_file(file_path: str, content: object, replace: bool = False) -> None:
    """
    Writes data content into a YAML file.
    """
    try:
        if replace and os.path.exists(file_path):
            os.remove(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as file:
            yaml.dump(content, file)
    except Exception as e:
        raise USvisaException(e, sys) from e


def load_object(file_path: str) -> object:
    """
    Loads a serialized Python object from a file path using dill.
    """
    try:
        if not os.path.exists(file_path):
            raise Exception(f"The file: {file_path} does not exist")
        with open(file_path, "rb") as file_obj:
            return dill.load(file_obj)
    except Exception as e:
        raise USvisaException(e, sys) from e


def save_object(file_path: str, obj: object) -> None:
    """
    Saves a Python object to a file path using dill.
    """
    try:
        logging.info("Entered the save_object method of main_utils")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as file_obj:
            dill.dump(obj, file_obj)
        logging.info("Exited the save_object method of main_utils")
    except Exception as e:
        raise USvisaException(e, sys) from e


def load_numpy_array_data(file_path: str) -> np.ndarray:
    """
    Loads a NumPy array from a binary file.
    """
    try:
        with open(file_path, "rb") as file_obj:
            return np.load(file_obj)
    except Exception as e:
        raise USvisaException(e, sys) from e


def save_numpy_array_data(file_path: str, array: np.ndarray) -> None:
    """
    Saves a NumPy array to a binary file.
    """
    try:
        dir_path = os.path.dirname(file_path)
        os.makedirs(dir_path, exist_ok=True)
        with open(file_path, "wb") as file_obj:
            np.save(file_obj, array)
    except Exception as e:
        raise USvisaException(e, sys) from e


def drop_columns(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """
    Drops specified columns from a pandas DataFrame.
    """
    try:
        logging.info(f"Entered drop_columns with cols: {cols}")
        df = df.drop(columns=[col for col in cols if col in df.columns], errors="ignore")
        logging.info("Exited drop_columns successfully")
        return df
    except Exception as e:
        raise USvisaException(e, sys) from e
