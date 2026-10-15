"""Validation and business logic for employee/customer records."""

import base64
import hashlib
import re
import secrets
from datetime import datetime, timezone

from database.people_repository import PeopleRepository


class PeopleService:
    RECORD_TYPES = {"Employee", "Customer"}
    PASSWORD_ITERATIONS = 310_000

    def __init__(self):
        self.repository = PeopleRepository()

    @classmethod
    def _hash_password(cls, password):
        """Hash a password with a random salt; never persist the raw value."""
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            cls.PASSWORD_ITERATIONS,
        )
        salt_text = base64.urlsafe_b64encode(salt).decode("ascii")
        digest_text = base64.urlsafe_b64encode(digest).decode("ascii")
        return (
            "pbkdf2_sha256$" + str(cls.PASSWORD_ITERATIONS)
            + "$" + salt_text + "$" + digest_text
        )

    def add_record(
        self,
        record_type,
        record_id,
        full_name,
        age,
        phone,
        email="",
        department="",
        address="",
        password="",
    ):
        if record_type not in self.RECORD_TYPES:
            raise ValueError("Choose Employee or Customer.")

        record_id = (record_id or "").strip().upper()
        full_name = (full_name or "").strip()
        phone = (phone or "").strip()
        email = (email or "").strip()
        department = (department or "").strip()
        address = (address or "").strip()

        if not record_id:
            raise ValueError("An employee/customer ID is required.")
        if len(record_id) > 64:
            raise ValueError("ID must be 64 characters or fewer.")
        if not full_name:
            raise ValueError("Full name is required.")
        if not isinstance(age, int) or not 0 <= age <= 120:
            raise ValueError("Age must be between 0 and 120.")

        phone_digits = re.sub(r"\D", "", phone)
        if not 7 <= len(phone_digits) <= 15:
            raise ValueError("Enter a valid phone number with 7–15 digits.")

        if email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise ValueError("Enter a valid email address.")

        password_hash = None
        if password:
            if len(password) < 12:
                raise ValueError(
                    "If you add a password, use at least 12 characters."
                )
            password_hash = self._hash_password(password)

        record = {
            "record_id": record_id,
            "full_name": full_name,
            "age": age,
            "phone": phone,
            "email": email or None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if record_type == "Employee":
            record["department"] = department or None
        else:
            record["address"] = address or None

        # Store only a salted password hash, never the submitted password.
        if password_hash:
            record["password_hash"] = password_hash

        return self.repository.add_record(record_type, record)

    def list_records(self, record_type):
        if record_type not in self.RECORD_TYPES:
            raise ValueError("Choose Employee or Customer.")
        return self.repository.list_records(record_type)

    def delete_record(self, record_type, record_id):
        if record_type not in self.RECORD_TYPES:
            raise ValueError("Choose Employee or Customer.")
        return self.repository.delete_record(
            record_type, (record_id or "").strip().upper()
        )
