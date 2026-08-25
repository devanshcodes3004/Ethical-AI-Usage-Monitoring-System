"""
auth_service.py

Handles user authentication.
"""

from database.models import UserDocument
from database.user_repository import UserRepository


class AuthService:

    def __init__(self):

        self.user_repository = UserRepository()

    def register(self, user: UserDocument):

        return self.user_repository.create_user(user)

    def login(
        self,
        email: str,
        password: str
    ):

        user = self.user_repository.get_user_by_email(email)

        if user is None:

            return None

        if user["password"] != password:

            return None

        return user