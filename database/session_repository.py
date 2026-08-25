"""
session_repository.py

Handles database operations related to chat sessions.
"""

import sys

from bson import ObjectId

from database.collections import SESSIONS_COLLECTION
from database.db import MongoDB
from database.models import SessionDocument

from exception import CustomException


class SessionRepository:

    def __init__(self):

        database = MongoDB().get_database()
        self.collection = database[SESSIONS_COLLECTION]

    def create_session(
        self,
        session: SessionDocument
    ) -> str:

        try:

            result = self.collection.insert_one(
                session.model_dump()
            )

            return str(result.inserted_id)

        except Exception as e:
            raise CustomException(e, sys)

    def get_session(
        self,
        session_id: str
    ):

        try:

            document = self.collection.find_one(
                {"_id": ObjectId(session_id)}
            )

            if document is None:
                return None

            return {
                "session_id": str(document["_id"]),
                "user_id": document["user_id"],
                "title": document["title"],
                "created_at": document["created_at"],
                "updated_at": document["updated_at"],
                "is_deleted": document["is_deleted"]
            }

        except Exception as e:
            raise CustomException(e, sys)

    def get_user_sessions(
        self,
        user_id: str
    ):

        try:

            documents = self.collection.find(
                {
                    "user_id": user_id,
                    "is_deleted": False
                }
            ).sort("updated_at", -1)

            sessions = []

            for document in documents:

                sessions.append(
                    {
                        "session_id": str(document["_id"]),
                        "title": document["title"],
                        "created_at": document["created_at"],
                        "updated_at": document["updated_at"]
                    }
                )

            return sessions

        except Exception as e:
            raise CustomException(e, sys)

    def update_session_title(
        self,
        session_id: str,
        title: str
    ):

        try:

            return self.collection.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {
                        "title": title
                    }
                }
            )

        except Exception as e:
            raise CustomException(e, sys)

    def update_session_timestamp(
        self,
        session_id: str,
        timestamp
    ):

        try:

            return self.collection.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {
                        "updated_at": timestamp
                    }
                }
            )

        except Exception as e:
            raise CustomException(e, sys)

    def delete_session(
        self,
        session_id: str
    ):

        try:

            return self.collection.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {
                        "is_deleted": True
                    },
                    "$currentDate": {
                        "updated_at": True
                    }
                }
            )

        except Exception as e:
            raise CustomException(e, sys)