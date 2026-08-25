"""
message_repository.py

Handles database operations related to messages.
"""

import sys

from bson import ObjectId

from database.collections import MESSAGES_COLLECTION
from database.db import MongoDB
from database.models import MessageDocument
from exception import CustomException


class MessageRepository:

    def __init__(self):

        database = MongoDB().get_database()

        self.collection = database[MESSAGES_COLLECTION]

    def save_message(self, message: MessageDocument) -> str:

        try:

            result = self.collection.insert_one(message.model_dump())

            return str(result.inserted_id)

        except Exception as e:

            raise CustomException(e, sys)

    def get_message(self, message_id: str):

        try:

            document = self.collection.find_one(
                {"_id": ObjectId(message_id)}
            )

            if document is None:
                return None

            document.pop("_id", None)

            return MessageDocument(**document)

        except Exception as e:

            raise CustomException(e, sys)

    def get_session_messages(self, session_id: str):

        try:

            documents = self.collection.find(
                {"session_id": session_id}
            ).sort("timestamp", 1)

            return [
                MessageDocument(**{k: v for k, v in doc.items() if k != "_id"})
                for doc in documents
            ]

        except Exception as e:

            raise CustomException(e, sys)

    def delete_message(self, message_id: str):

        try:

            return self.collection.delete_one(
                {"_id": ObjectId(message_id)}
            )

        except Exception as e:

            raise CustomException(e, sys)