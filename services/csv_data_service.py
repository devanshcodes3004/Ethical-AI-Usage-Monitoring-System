"""Import business CSVs and retrieve only relevant, non-sensitive context."""

import csv
import io
import re
from datetime import datetime, timezone

from database.db import MongoDB


COLLECTION_NAME = "business_csv_records"
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10_000
MAX_CONTEXT_RECORDS = 5

# Never import columns whose names suggest credentials, secrets, payment data,
# government identifiers, or personal contact/location information.
SENSITIVE_COLUMN_PATTERNS = (
    r"password", r"passwd", r"passcode", r"passphrase", r"credential",
    r"secret", r"api.?key", r"access.?token", r"refresh.?token",
    r"auth.?token", r"private.?key", r"\botp\b", r"\bpin\b",
    r"cvv", r"cvc", r"credit.?card", r"debit.?card", r"card.?number",
    r"bank.?account", r"\biban\b", r"\bssn\b", r"aadhaar", r"aadhar",
    r"\bpan\b", r"passport", r"date.?of.?birth", r"\bdob\b",
    r"phone", r"mobile", r"email", r"e.?mail", r"address",
    r"home.?location", r"personal.?number",
)
SENSITIVE_COLUMN_RE = re.compile(
    "|".join(f"(?:{pattern})" for pattern in SENSITIVE_COLUMN_PATTERNS),
    re.IGNORECASE,
)

SENSITIVE_REQUEST_RE = re.compile(
    r"\b(passwords?|passcodes?|passphrases?|credentials?|secrets?|"
    r"api[\s_-]*keys?|access[\s_-]*tokens?|refresh[\s_-]*tokens?|"
    r"private[\s_-]*keys?|otps?|cvv|cvc|credit[\s_-]*cards?|"
    r"bank[\s_-]*accounts?|social security numbers?|ssns?|aadhaar|aadhar|"
    r"passport numbers?)\b",
    re.IGNORECASE,
)
REQUEST_INTENT_RE = re.compile(
    r"\b(show|tell|give|find|get|fetch|reveal|display|list|retrieve|"
    r"provide|print|export|share|what(?:'s| is)|which|read|look up|"
    r"search for|return|send me|do you know)\b",
    re.IGNORECASE,
)

PII_VALUE_PATTERNS = [
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)"),
    re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
]


def is_sensitive_data_request(prompt):
    """Conservatively block direct requests to retrieve credential-like data."""
    return bool(
        SENSITIVE_REQUEST_RE.search(prompt or "")
        and REQUEST_INTENT_RE.search(prompt or "")
    )


class CSVDataService:
    """CSV upload and keyword retrieval backed by MongoDB."""

    def __init__(self):
        self.collection = MongoDB().get_database()[COLLECTION_NAME]
        self.collection.create_index(
            [("record_type", 1), ("source_file", 1), ("row_number", 1)],
            unique=True,
        )

    @staticmethod
    def _safe_cell(value):
        text = str(value or "").strip()
        if not text:
            return ""
        # Prevent spreadsheet formula execution if a preview is exported later.
        if text.startswith(("=", "+", "-", "@")):
            text = "'" + text
        return text[:2000]

    def import_csv(self, file_bytes, source_file, record_type):
        if record_type not in {"Customer", "Employee"}:
            raise ValueError("Choose Customer or Employee data.")
        if not file_bytes:
            raise ValueError("The uploaded CSV is empty.")
        if len(file_bytes) > MAX_FILE_BYTES:
            raise ValueError("CSV files must be 5 MB or smaller.")

        try:
            text = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("Save the CSV as UTF-8 and upload it again.") from exc

        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise ValueError("The CSV must contain a header row.")

        columns = {}
        dropped_columns = []
        for original in reader.fieldnames:
            normalized = re.sub(r"[^a-z0-9]+", "_", (original or "").strip().lower()).strip("_")
            if not normalized:
                continue
            if SENSITIVE_COLUMN_RE.search(normalized):
                dropped_columns.append(original)
            else:
                columns[original] = normalized

        if not columns:
            raise ValueError(
                "No safe columns were found. Remove credential and personal-contact columns."
            )

        records = []
        for row_number, raw_row in enumerate(reader, start=1):
            if row_number > MAX_ROWS:
                raise ValueError(f"CSV exceeds the {MAX_ROWS:,}-row limit.")
            safe_data = {
                columns[original]: self._safe_cell(raw_row.get(original, ""))
                for original in columns
            }
            if not any(safe_data.values()):
                continue
            records.append({
                "record_type": record_type,
                "source_file": (source_file or "uploaded.csv")[:200],
                "row_number": row_number,
                "data": safe_data,
                "imported_at": datetime.now(timezone.utc).isoformat(),
            })

        if not records:
            raise ValueError("No non-empty data rows were found.")

        # Re-uploading the same filename replaces that file's records only.
        self.collection.delete_many({
            "record_type": record_type,
            "source_file": (source_file or "uploaded.csv")[:200],
        })
        self.collection.insert_many(records, ordered=True)

        return {
            "rows_imported": len(records),
            "columns_kept": list(columns.values()),
            "columns_dropped": dropped_columns,
        }

    def list_sources(self):
        pipeline = [
            {"$group": {
                "_id": {"record_type": "$record_type", "source_file": "$source_file"},
                "rows": {"$sum": 1},
                "latest_import": {"$max": "$imported_at"},
            }},
            {"$sort": {"_id.record_type": 1, "_id.source_file": 1}},
        ]
        return list(self.collection.aggregate(pipeline))

    @staticmethod
    def _tokens(text):
        return {
            token for token in re.findall(r"[a-z0-9]{3,}", (text or "").casefold())
            if token not in {
                "the", "and", "for", "with", "from", "what", "when", "where",
                "which", "about", "customer", "customers", "employee", "employees",
                "please", "show", "tell", "give", "find", "list", "data",
            }
        }

    @staticmethod
    def _redact_values(value):
        text = str(value or "")
        for pattern in PII_VALUE_PATTERNS:
            text = pattern.sub("[REDACTED]", text)
        return text[:1000]

    def retrieve_context(self, prompt, record_types=("Customer", "Employee")):
        """Return a small keyword-matched context; never return dropped columns."""
        query_tokens = self._tokens(prompt)
        if not query_tokens:
            return ""

        candidates = self.collection.find(
            {"record_type": {"$in": list(record_types)}},
            {"_id": 0, "record_type": 1, "source_file": 1, "row_number": 1, "data": 1},
        ).limit(2000)

        ranked = []
        for item in candidates:
            data = item.get("data", {})
            searchable = " ".join(str(v) for v in data.values())
            row_tokens = self._tokens(searchable)
            overlap = query_tokens & row_tokens
            if not overlap:
                continue
            # Do not pass names, contact details, addresses, or arbitrary
            # identifier fields into the model context.
            safe_fields = {
                key: self._redact_values(value)
                for key, value in data.items()
                if not re.search(
                    r"(^|_)(name|email|phone|mobile|address|location|"
                    r"employee_id|customer_id|record_id|id|dob|birth)(_|$)",
                    key,
                    re.IGNORECASE,
                )
                and value
            }
            if safe_fields:
                ranked.append((
                    len(overlap),
                    item.get("record_type", "Business"),
                    item.get("source_file", ""),
                    item.get("row_number", 0),
                    safe_fields,
                ))

        ranked.sort(key=lambda row: row[0], reverse=True)
        selected = ranked[:MAX_CONTEXT_RECORDS]
        if not selected:
            return ""

        lines = []
        for _, record_type, source, row_number, fields in selected:
            safe_fields = "; ".join(f"{key}: {value}" for key, value in fields.items())
            lines.append(
                f"- Type: {record_type}; source: {source}; row: {row_number}; {safe_fields}"
            )
        return "\n".join(lines)
