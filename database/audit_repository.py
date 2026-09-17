"""
audit_repository.py

Handles database operations related to governance audit logs.
"""

import sys

from bson import ObjectId

from database.collections import AUDIT_LOGS_COLLECTION
from database.db import MongoDB
from database.models import AuditLogDocument

from exception import CustomException


class AuditRepository:

    def __init__(self):
        database = MongoDB().get_database()
        self.collection = database[AUDIT_LOGS_COLLECTION]

    def save_log(
        self,
        log: AuditLogDocument
    ):
        try:
            result = self.collection.insert_one(
                log.model_dump()
            )

            return str(result.inserted_id)

        except Exception as e:
            raise CustomException(e, sys)

    def get_log(
        self,
        log_id: str
    ):
        try:
            return self.collection.find_one(
                {
                    "_id": ObjectId(log_id)
                }
            )

        except Exception as e:
            raise CustomException(e, sys)

    def get_user_logs(
        self,
        user_id: str
    ):
        try:
            return list(
                self.collection.find(
                    {
                        "user_id": user_id
                    }
                ).sort(
                    "timestamp",
                    -1
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
                ).sort(
                    "timestamp",
                    -1
                )
            )

        except Exception as e:
            raise CustomException(e, sys)

    def get_recent_blocked_requests(
        self,
        limit: int = 10
    ):
        try:
            return list(
                self.collection.find(
                    {
                        "decision": "BLOCK"
                    },
                    {
                        "_id": 0,
                        "session_id": 1,
                        "user_id": 1,
                        "message_id": 1,
                        "prompt": 1,
                        "risk_score": 1,
                        "risk_level": 1,
                        "decision": 1,
                        "categories": 1,
                        "reason": 1,
                        "confidence": 1,
                        "selected_model": 1,
                        "timestamp": 1
                    }
                ).sort(
                    "timestamp",
                    -1
                ).limit(limit)
            )

        except Exception as e:
            raise CustomException(e, sys)

    def delete_log(
        self,
        log_id: str
    ):
        try:
            return self.collection.delete_one(
                {
                    "_id": ObjectId(log_id)
                }
            )

        except Exception as e:
            raise CustomException(e, sys)