"""MongoDB persistence for employee and customer records."""

from pymongo.errors import DuplicateKeyError

from database.db import MongoDB


class PeopleRepository:
    """Store employee and customer records in separate collections."""

    COLLECTIONS = {
        "Employee": "employee_records",
        "Customer": "customer_records",
    }

    def __init__(self):
        database = MongoDB().get_database()
        self.collections = {
            record_type: database[collection_name]
            for record_type, collection_name in self.COLLECTIONS.items()
        }
        for collection in self.collections.values():
            collection.create_index("record_id", unique=True)

    def _collection(self, record_type):
        if record_type not in self.collections:
            raise ValueError("Record type must be Employee or Customer.")
        return self.collections[record_type]

    def add_record(self, record_type, record):
        """Insert a record. Record IDs must be unique within their type."""
        try:
            result = self._collection(record_type).insert_one(dict(record))
        except DuplicateKeyError as exc:
            raise ValueError(
                f"That {record_type.lower()} ID already exists."
            ) from exc
        return str(result.inserted_id)

    def list_records(self, record_type):
        """Never return password hashes to the UI."""
        projection = {"_id": 0, "password_hash": 0}
        return list(
            self._collection(record_type)
            .find({}, projection)
            .sort("created_at", -1)
        )

    def delete_record(self, record_type, record_id):
        result = self._collection(record_type).delete_one(
            {"record_id": record_id}
        )
        return result.deleted_count > 0
