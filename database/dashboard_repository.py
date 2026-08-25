"""
dashboard_repository.py

Handles dashboard related database operations.
"""

import sys

from database.collections import (
    AUDIT_LOGS_COLLECTION,
    MESSAGES_COLLECTION,
    SESSIONS_COLLECTION
)
from database.db import MongoDB

from exception import CustomException


class DashboardRepository:

    def __init__(self):

        database = MongoDB().get_database()

        self.sessions = database[SESSIONS_COLLECTION]
        self.messages = database[MESSAGES_COLLECTION]
        self.audit_logs = database[AUDIT_LOGS_COLLECTION]

    def get_total_sessions(self):

        try:

            return self.sessions.count_documents(
                {"is_deleted": False}
            )

        except Exception as e:
            raise CustomException(e, sys)

    def get_total_messages(self):

        try:

            return self.messages.count_documents({})

        except Exception as e:
            raise CustomException(e, sys)

    def get_allowed_requests(self):

        try:

            return self.audit_logs.count_documents(
                {"decision": "ALLOW"}
            )

        except Exception as e:
            raise CustomException(e, sys)

    def get_blocked_requests(self):

        try:

            return self.audit_logs.count_documents(
                {"decision": "BLOCK"}
            )

        except Exception as e:
            raise CustomException(e, sys)

    def get_average_risk_score(self):

        try:

            result = list(
                self.audit_logs.aggregate(
                    [
                        {
                            "$group": {
                                "_id": None,
                                "average": {
                                    "$avg": "$risk_score"
                                }
                            }
                        }
                    ]
                )
            )

            return 0 if not result else round(
                result[0]["average"],
                2
            )

        except Exception as e:
            raise CustomException(e, sys)

    def get_highest_risk_score(self):

        try:

            document = self.audit_logs.find_one(
                sort=[("risk_score", -1)]
            )

            if document is None:
                return 0

            return document["risk_score"]

        except Exception as e:
            raise CustomException(e, sys)

    def get_model_usage(self):

        try:

            return list(
                self.audit_logs.aggregate(
                    [
                        {
                            "$group": {
                                "_id": "$selected_model",
                                "count": {
                                    "$sum": 1
                                }
                            }
                        }
                    ]
                )
            )

        except Exception as e:
            raise CustomException(e, sys)

    def get_top_categories(self):

        try:

            return list(
                self.audit_logs.aggregate(
                    [
                        {"$unwind": "$categories"},
                        {
                            "$group": {
                                "_id": "$categories",
                                "count": {
                                    "$sum": 1
                                }
                            }
                        },
                        {"$sort": {"count": -1}},
                        {"$limit": 5}
                    ]
                )
            )

        except Exception as e:
            raise CustomException(e, sys)

    def get_recent_blocked_requests(self):

        try:

            return list(
                self.audit_logs.find(
                    {"decision": "BLOCK"},
                    {
                        "_id": 0,
                        "reason": 1,
                        "timestamp": 1
                    }
                ).sort(
                    "timestamp",
                    -1
                ).limit(5)
            )

        except Exception as e:
            raise CustomException(e, sys)