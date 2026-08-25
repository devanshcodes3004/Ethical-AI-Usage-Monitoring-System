"""
mongodb.py

Handles MongoDB connection.
"""

import sys

from pymongo import MongoClient
from pymongo.database import Database

from config import DATABASE_NAME, MONGO_URI
from exception import CustomException


class MongoDB:

    def __init__(self):

        try:

            self.client = MongoClient(MONGO_URI)

            self.database = self.client[DATABASE_NAME]

        except Exception as e:

            raise CustomException(e, sys)

    def get_database(self) -> Database:

        return self.database

    def close_connection(self):

        self.client.close()