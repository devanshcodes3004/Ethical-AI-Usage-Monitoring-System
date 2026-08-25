"""
session_service.py

Provides business logic for managing chat sessions.
"""

import sys
from typing import Optional

from database.models import SessionDocument
from database.session_repository import SessionRepository

from exception import CustomException


class SessionService:

    def __init__(self):

        self.session_repository = SessionRepository()

    def create_session(
        self,
        user_id: str,
        title: Optional[str] = None
    ) -> str:

        try:

            session = SessionDocument(
                user_id=user_id,
                title=title or "New Chat"
            )

            return self.session_repository.create_session(
                session
            )

        except Exception as e:
            raise CustomException(e, sys)

    def get_session(
        self,
        session_id: str
    ):

        try:

            return self.session_repository.get_session(
                session_id
            )

        except Exception as e:
            raise CustomException(e, sys)

    def get_user_sessions(
        self,
        user_id: str
    ):

        try:

            return self.session_repository.get_user_sessions(
                user_id
            )

        except Exception as e:
            raise CustomException(e, sys)

    def rename_session(
        self,
        session_id: str,
        title: str
    ):

        try:

            return self.session_repository.update_session_title(
                session_id,
                title
            )

        except Exception as e:
            raise CustomException(e, sys)

    def delete_session(
        self,
        session_id: str
    ) -> bool:

        try:

            result = self.session_repository.delete_session(
                session_id
            )

            return result.modified_count > 0

        except Exception as e:
            raise CustomException(e, sys)