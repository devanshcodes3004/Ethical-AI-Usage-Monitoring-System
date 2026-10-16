"""Import business CSVs and retrieve only relevant, non-sensitive context."""

import csv
import io
import re
from datetime import datetime, timezone
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from database.db import MongoDB


COLLECTION_NAME = "business_csv_records"
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10_000
MAX_CONTEXT_RECORDS = 5
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Never import columns whose names suggest credentials, secrets, payment data,
# government identifiers, or personal contact/location information.
SENSITIVE_COLUMN_PATTERNS = (
    r"password", r"passwd", r"passcode", r"passphrase", r"credential", r"\bpwd\b",
    r"secret", r"api.?key", r"access.?token", r"refresh.?token",
    r"auth.?token", r"private.?key", r"(^|_)otp(_|$)", r"(^|_)pin(_|$)",
    r"cvv", r"cvc", r"credit.?card", r"debit.?card", r"card.?number",
    r"bank.?account", r"(^|_)iban(_|$)", r"(^|_)ssn(_|$)", r"aadhaar", r"aadhar",
    r"(^|_)pan(_|$)", r"passport", r"date.?of.?birth", r"(^|_)dob(_|$)",
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
    re.compile(
        r"\b(password|passwd|passcode|api[\s_-]*key|access[\s_-]*token|"
        r"secret|credential|otp|pin)\b\s*[:=]\s*[^\s,;]+",
        re.IGNORECASE,
    ),
]


def _remove_explicit_exclusion_clauses(prompt):
    """Ignore clearly negated clauses when deciding whether data disclosure is requested.

    Example: "Show issue IDs. Do not include passwords or phone numbers."
    The first clause remains subject to policy checks; the exclusion clause must
    not itself trigger a sensitive-data block.
    """
    text = (prompt or "").casefold()
    clauses = re.split(
        r"(?<=[.!?;])\s+|,\s*(?=(?:but\s+)?(?:do not|don't|dont|never|exclude|excluding|without)\b)",
        text,
    )
    return " ".join(
        clause for clause in clauses
        if not re.match(
            r"^\s*(?:(?:but|and)\s+)?(?:do not|don't|dont|never|exclude|excluding|without)\b",
            clause,
        )
    )


def is_sensitive_data_request(prompt):
    """Block requests for secrets or customer contact data, but allow support analytics."""
    text = _remove_explicit_exclusion_clauses(prompt)
    if not text.strip():
        return False

    contact_terms = re.search(
        r"\b(phone|mobile|cell(?:ular)?|telephone|email|e-mail|contact details?|home address|street address)\b",
        text,
    )
    disclosure_intent = re.search(
        r"\b(show|tell|give|find|get|fetch|reveal|display|list|retrieve|provide|print|export|share|read|return|send|what|which|who|all|every|each)\b",
        text,
    )
    customer_scope = re.search(r"\b(customer|customers|client|clients|user|users)\b", text)
    broad_contact_scope = re.search(r"\b(all|every|each)\b", text)
    if contact_terms and disclosure_intent and (customer_scope or broad_contact_scope):
        return True

    secret_terms = re.search(
        r"\b(passwords?|passcodes?|passphrases?|credentials?|secrets?|api[\s_-]*keys?|access[\s_-]*tokens?|refresh[\s_-]*tokens?|private[\s_-]*keys?|otps?|cvv|cvc|credit[\s_-]*cards?|bank[\s_-]*accounts?|social security numbers?|ssns?|aadhaar|aadhar|passport numbers?)\b",
        text,
    )
    if not secret_terms:
        return False

    direct_disclosure = re.search(
        r"\b(show|tell me|give me|reveal|display|list|retrieve|export|share|print|send me|what is|what are|what's|which is|which are|read|fetch)\b.{0,120}\b(passwords?|passcodes?|passphrases?|credentials?|secrets?|api[\s_-]*keys?|access[\s_-]*tokens?|refresh[\s_-]*tokens?|private[\s_-]*keys?|otps?|cvv|cvc|credit[\s_-]*cards?|bank[\s_-]*accounts?|ssns?|aadhaar|aadhar|passport numbers?)\b",
        text,
    )
    support_topic = re.search(
        r"\b(reset|recovery|forgot|change|policy|security|issue|issues|error|problem|problems|complaint|complaints|how many|count|trend|trends|frequency|frequent|common)\b",
        text,
    )
    if direct_disclosure:
        safe_reset_question = re.search(
            r"\b(password|passcode|credential)\s+(reset|recovery|issue|problem|error)\b",
            text,
        )
        explicit_retrieval = re.search(
            r"\b(show|give|reveal|display|list|retrieve|export|share|send me)\b.{0,100}\b(password|passcode|credential)\b",
            text,
        )
        if safe_reset_question and not re.search(
            r"\b(password|passcode|credential)\s+(for|of|belonging to)\b", text
        ):
            return False
        return True
    # Asking about the frequency or causes of password-reset issues is safe.
    if support_topic and re.search(r"\b(password|passcode|credential)\s+(reset|recovery|issue|problem|error)\b", text):
        return False
    return False

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
        if text.startswith(("=", "+", "-", "@")):
            text = "'" + text
        # Redact recognizable PII and labeled secrets in free-text cells too.
        return CSVDataService._redact_values(text)[:2000]

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
            normalized = re.sub(
                r"[^a-z0-9]+", "_", (original or "").strip().lower()
            ).strip("_")
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

        # Batch embeddings to avoid loading/running the encoder once per row.
        texts = [self._record_text(record["data"]) for record in records]
        vectors = self._embedding_model().encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            batch_size=64,
            show_progress_bar=False,
        )
        for record, vector in zip(records, vectors):
            record["embedding"] = vector.astype(float).tolist()

        source = (source_file or "uploaded.csv")[:200]
        # Re-uploading the same filename replaces that file's records only.
        self.collection.delete_many({
            "record_type": record_type,
            "source_file": source,
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

    def delete_source(self, record_type, source_file):
        if record_type not in {"Customer", "Employee"}:
            raise ValueError("Choose Customer or Employee data.")
        result = self.collection.delete_many({
            "record_type": record_type,
            "source_file": source_file,
        })
        return result.deleted_count

    @staticmethod
    def is_business_data_question(prompt):
        """Recognize questions that should be answered from imported records."""
        text = (prompt or "").casefold()
        mentions_data = re.search(
            r"\b(customer|customers|client|clients|employee|employees|staff|"
            r"ticket|tickets|case|cases|complaint|complaints|record|records)\b",
            text,
        )
        asks_for_data = re.search(
            r"\b(show|list|summari[sz]e|what|which|how many|find|tell me about|"
            r"status|open|pending|resolved|data|records|issue|issues|problem|"
            r"problems|complaint|complaints|ticket|tickets|case|cases)\b",
            text,
        )
        return bool(mentions_data and asks_for_data)

    @staticmethod
    @lru_cache(maxsize=1)
    def _embedding_model():
        return SentenceTransformer(EMBEDDING_MODEL_NAME)

    @staticmethod
    def _record_text(data):
        return " ".join(
            f"{key.replace('_', ' ')}: {value}"
            for key, value in data.items()
            if value and not SENSITIVE_COLUMN_RE.search(key)
        )

    @staticmethod
    def _embed_text(text):
        vector = CSVDataService._embedding_model().encode(
            text, normalize_embeddings=True, convert_to_numpy=True
        )
        return vector.astype(float).tolist()

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

    def retrieve_context(self, prompt, record_types=None):
        """Retrieve relevant safe CSV rows using sentence-embedding similarity."""
        prompt_text = (prompt or "").casefold()
        if not prompt_text.strip():
            return ""

        if record_types is None:
            if any(term in prompt_text for term in ("customer", "client", "complaint", "ticket")):
                record_types = ("Customer",)
            elif any(term in prompt_text for term in ("employee", "staff", "worker")):
                record_types = ("Employee",)
            else:
                record_types = ("Customer", "Employee")

        query_vector = np.asarray(self._embed_text(prompt), dtype=float)
        candidates = self.collection.find(
            {"record_type": {"$in": list(record_types)}},
            {"_id": 1, "record_type": 1, "source_file": 1, "row_number": 1, "data": 1, "embedding": 1},
        ).limit(5000)

        ranked = []
        excluded_context_key_re = re.compile(
            r"(^|_)(name|email|phone|mobile|telephone|address|location|employee_id|record_id|id|dob|birth|password|passwd|credential|secret|token|api_key)(_|$)",
            re.IGNORECASE,
        )
        safe_identifier_keys = {"customer_id", "ticket_id", "case_id", "order_id", "issue_id"}
        for item in candidates:
            data = item.get("data", {})
            if not isinstance(data, dict):
                continue
            searchable_text = self._record_text(data)
            if not searchable_text:
                continue
            embedding = item.get("embedding")
            if not isinstance(embedding, list) or len(embedding) != len(query_vector):
                embedding = self._embed_text(searchable_text)
                self.collection.update_one({"_id": item["_id"]}, {"$set": {"embedding": embedding}})
            vector = np.asarray(embedding, dtype=float)
            denom = float(np.linalg.norm(vector) * np.linalg.norm(query_vector))
            similarity = float(np.dot(vector, query_vector) / denom) if denom else 0.0
            safe_fields = {
                key: self._redact_values(value)
                for key, value in data.items()
                if (key in safe_identifier_keys or not excluded_context_key_re.search(key)) and value
            }
            if safe_fields and similarity >= 0.18:
                ranked.append((similarity, item.get("record_type", "Business"), item.get("source_file", ""), item.get("row_number", 0), safe_fields))

        ranked.sort(key=lambda row: row[0], reverse=True)
        selected = ranked[:MAX_CONTEXT_RECORDS]
        if not selected:
            return ""
        lines = []
        for score, record_type, source, row_number, fields in selected:
            safe_fields = "; ".join(f"{key}: {value}" for key, value in fields.items())
            lines.append(f"- Type: {record_type}; relevance: {score:.2f}; source: {source}; row: {row_number}; {safe_fields}")
        return "\n".join(lines)

    @staticmethod
    def _problem_bucket(label):
        """Group free-text complaint descriptions into useful recurring categories."""
        text = (label or "").casefold()
        patterns = (
            ("Delivery or shipping delays", r"\b(del[io]ver(?:y|ies)|delivery|deliver|shipping|shipment|late|delayed|courier|tracking)\b"),
            ("Payment or billing problems", r"\b(payment|paid|billing|bill|charged|charge|transaction|upi|card declined)\b"),
            ("Refund or return problems", r"\b(refund|return|replacement|exchange|reimburse)\b"),
            ("Login or account access", r"\b(login|log in|sign.?in|password|account access|locked out|otp)\b"),
            ("Product quality or damaged item", r"\b(damaged|broken|defect|defective|quality|faulty|wrong item)\b"),
            ("Order cancellation or order status", r"\b(cancel|cancellation|order status|order missing|not received)\b"),
            ("App or website problems", r"\b(app|website|web site|crash|bug|loading|error page|technical issue)\b"),
            ("Customer support problems", r"\b(customer service|support|agent|representative|no response|not responding)\b"),
        )
        for category, pattern in patterns:
            if re.search(pattern, text):
                return category
        return re.sub(r"\s+", " ", CSVDataService._redact_values(label).strip())[:180]

    def get_customers_with_problems(self, prompt="", limit=10):
        """Return minimized customer issue records; list results default to at most 10."""
        # Normal display requests are capped at 10. A trusted internal count
        # may pass None to inspect all matching unique customers.
        max_results = None if limit is None else max(1, min(int(limit), 10))
        documents = self.collection.find({"record_type": "Customer"}, {"_id": 0, "data": 1})
        active_statuses = {
            "open", "pending", "in progress", "in-progress", "escalated",
            "unresolved", "waiting", "under review", "on hold",
        }
        closed_statuses = {"resolved", "closed", "complete", "completed", "fixed"}
        category_fields = (
            "problem_category", "issue_category", "complaint_category", "problem_type",
            "issue_type", "complaint_type", "category", "type",
        )
        text_fields = (
            "problem", "issue", "complaint", "ticket_subject", "subject",
            "description", "issue_description", "customer_problem",
        )
        known_categories = {
            "delivery or shipping delays", "payment or billing problems",
            "refund or return problems", "login or account access",
            "product quality or damaged item", "order cancellation or order status",
            "app or website problems", "customer support problems",
        }
        query_bucket = self._problem_bucket(prompt)
        filter_category = query_bucket.casefold() if query_bucket.casefold() in known_categories else None
        matches = []
        seen_ids = set()

        for document in documents:
            data = document.get("data", {})
            if not isinstance(data, dict):
                continue
            normalized = {
                re.sub(r"[^a-z0-9]+", "_", str(key).casefold()).strip("_"): value
                for key, value in data.items()
            }
            customer_id = next(
                (str(normalized[key]).strip() for key in ("customer_id", "customerid", "client_id", "clientid")
                 if normalized.get(key) and str(normalized[key]).strip()),
                "",
            )
            if not customer_id or customer_id in seen_ids:
                continue

            status = str(normalized.get("status", "")).strip().casefold()
            if status in closed_statuses:
                continue
            if status and status not in active_statuses:
                continue

            raw_label = next(
                (str(normalized[field]).strip() for field in category_fields
                 if normalized.get(field) and str(normalized[field]).strip()),
                "",
            )
            if raw_label:
                problem = self._redact_values(raw_label)[:180]
                problem_bucket = self._problem_bucket(raw_label)
            else:
                raw_label = next(
                    (str(normalized[field]).strip() for field in text_fields
                     if normalized.get(field) and str(normalized[field]).strip()),
                    "",
                )
                if not raw_label:
                    continue
                problem_bucket = self._problem_bucket(raw_label)
                problem = problem_bucket

            if filter_category and problem_bucket.casefold() != filter_category:
                continue

            # Return only the minimum fields needed for follow-up.
            matches.append({
                "customer_id": customer_id[:100],
                "problem": problem,
                "status": status or "unspecified",
            })
            seen_ids.add(customer_id)
            if max_results is not None and len(matches) >= max_results:
                break

        return matches

    def count_customers_with_problems(self, prompt=""):
        """Count unique customers with matching unresolved/active problem records.

        Uses the same category and status filters as the safe customer-list route,
        but does not apply the 10-result presentation cap.
        """
        return len(self.get_customers_with_problems(prompt, limit=None))

    def get_top_customer_problems(self, limit=2):
        """Count recurring customer problem categories without exposing personal data."""
        limit = max(1, min(int(limit), 10))
        documents = self.collection.find({"record_type": "Customer"}, {"_id": 0, "data": 1})
        counts, labels = {}, {}
        category_fields = (
            "problem_category", "issue_category", "complaint_category", "problem_type",
            "issue_type", "complaint_type", "category", "type",
        )
        text_fields = (
            "problem", "issue", "complaint", "ticket_subject", "subject",
            "description", "issue_description", "customer_problem",
        )
        for document in documents:
            data = document.get("data", {})
            if not isinstance(data, dict):
                continue
            normalized = {
                re.sub(r"[^a-z0-9]+", "_", str(key).casefold()).strip("_"): value
                for key, value in data.items()
            }
            raw_label = next(
                (str(normalized[field]).strip() for field in category_fields
                 if normalized.get(field) and str(normalized[field]).strip()),
                "",
            )
            if raw_label:
                label = self._redact_values(raw_label)[:180]
            else:
                raw_label = next(
                    (str(normalized[field]).strip() for field in text_fields
                     if normalized.get(field) and str(normalized[field]).strip()),
                    "",
                )
                if not raw_label:
                    continue
                label = self._problem_bucket(raw_label)
            key = re.sub(r"[^a-z0-9]+", " ", label.casefold()).strip()
            if key:
                counts[key] = counts.get(key, 0) + 1
                labels.setdefault(key, label)
        ranked = sorted(counts, key=lambda key: (-counts[key], labels[key].casefold()))
        return [{"problem": labels[key], "count": counts[key]} for key in ranked[:limit]]
