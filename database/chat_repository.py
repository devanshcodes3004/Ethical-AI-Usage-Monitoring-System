"""
user_repository.py

Handles database operations related to users.
"""

import sys

from bson import ObjectId

from database.collections import USERS_COLLECTION
from database.models import UserDocument
from database.db import MongoDB

from exception import CustomException


class UserRepository:

    def __init__(self):

        database = MongoDB().get_database()

        self.collection = database[USERS_COLLECTION]

    def create_user(self, user: UserDocument):

        try:

            result = self.collection.insert_one(
                user.model_dump()
            )

            return str(result.inserted_id)

        except Exception as e:

            raise CustomException(e, sys)

    def get_user_by_email(self, email: str):

        try:

            return self.collection.find_one(
                {
                    "email": email
                }
            )

        except Exception as e:

            raise CustomException(e, sys)

    def get_user_by_id(self, user_id: str):

        try:

            return self.collection.find_one(
                {
                    "_id": ObjectId(user_id)
                }
            )

        except Exception as e:

            raise CustomException(e, sys)

    def update_user(self, user_id: str, updated_data: dict):

        try:

            return self.collection.update_one(
                {
                    "_id": ObjectId(user_id)
                },
                {
                    "$set": updated_data
                }
            )

        except Exception as e:

            raise CustomException(e, sys)

    def delete_user(self, user_id: str):

        try:

            return self.collection.delete_one(
                {
                    "_id": ObjectId(user_id)
                }
            )

        except Exception as e:

            raise CustomException(e, sys)