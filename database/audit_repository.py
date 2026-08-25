"""
audit_repository.py

Handles database operations related to governance audit logs.
"""

import sys

from bson import ObjectId

from database.collections import AUDIT_LOGS_COLLECTION
from database.models import AuditLogDocument
from database.db import MongoDB

from exception import CustomException


class AuditRepository:

    def __init__(self):

        database = MongoDB().get_database()

        self.collection = database[AUDIT_LOGS_COLLECTION]

    def save_log(self, log: AuditLogDocument):

        try:

            result = self.collection.insert_one(
                log.model_dump()
            )

            return str(result.inserted_id)

        except Exception as e:

            raise CustomException(e, sys)

    def get_log(self, log_id: str):

        try:

            return self.collection.find_one(

                {
                    "_id": ObjectId(log_id)
                }

            )

        except Exception as e:

            raise CustomException(e, sys)

    def get_user_logs(self, user_id: str):

        try:

            return list(

                self.collection.find(

                    {
                        "user_id": user_id
                    }

                )

            )

        except Exception as e:

            raise CustomException(e, sys)

    def get_high_risk_logs(self):

        try:

            return list(

                self.collection.find(

                    {
                        "risk_level": "HIGH"
                    }

                )

            )

        except Exception as e:

            raise CustomException(e, sys)

    def delete_log(self, log_id: str):

        try:

            return self.collection.delete_one(

                {
                    "_id": ObjectId(log_id)
                }

            )

        except Exception as e:

            raise CustomException(e, sys)