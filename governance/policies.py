"""
policies.py

Persistence and rule evaluation for configurable organization AI policies.
Policies are stored in MongoDB and evaluated before model-based risk analysis.
"""

from datetime import datetime, timezone
from typing import Any

from database.db import MongoDB

COLLECTION_NAME = "governance_policies"

DEFAULT_POLICIES = [
    {
        "name": "Block prompt injection",
        "category": "Prompt Injection",
        "action": "BLOCK",
        "enabled": True,
        "description": "Block requests that attempt to override instructions or reveal hidden prompts.",
        "keywords": ["ignore previous instructions", "reveal system prompt", "reveal hidden prompt", "jailbreak"],
        "created_at": None,
    },
    {
        "name": "Warn on sensitive data",
        "category": "Sensitive Data",
        "action": "WARN",
        "enabled": True,
        "description": "Warn about common sensitive-data indicators and review before processing.",
        "keywords": ["api key", "password", "credit card", "social security number"],
        "created_at": None,
    },
]


class PolicyRepository:
    def __init__(self):
        self.collection = MongoDB().get_database()[COLLECTION_NAME]
        self.collection.create_index("name", unique=True)

    def list_policies(self):
        policies = list(self.collection.find({}, {"_id": 0}).sort("created_at", 1))
        if not policies:
            now = datetime.now(timezone.utc).isoformat()
            for policy in DEFAULT_POLICIES:
                item = {**policy, "created_at": now}
                self.collection.update_one(
                    {"name": item["name"]},
                    {"$setOnInsert": item},
                    upsert=True,
                )
            policies = list(self.collection.find({}, {"_id": 0}).sort("created_at", 1))
        return policies

    def save_policy(self, policy: dict[str, Any]):
        policy["created_at"] = policy.get("created_at") or datetime.now(timezone.utc).isoformat()
        self.collection.update_one({"name": policy["name"]}, {"$set": policy}, upsert=True)

    def delete_policy(self, name: str):
        self.collection.delete_one({"name": name})


class PolicyService:
    ACTIONS = {"ALLOW", "WARN", "BLOCK"}

    def __init__(self):
        self.repository = PolicyRepository()

    def list_policies(self):
        return self.repository.list_policies()

    def save_policy(self, name, category, action, description, keywords, enabled=True):
        name = (name or "").strip()
        category = (category or "").strip()
        description = (description or "").strip()
        terms = [x.strip() for x in (keywords or []) if x.strip()]
        if not name or not category:
            raise ValueError("Policy name and category are required.")
        if action not in self.ACTIONS:
            raise ValueError("Action must be ALLOW, WARN, or BLOCK.")
        self.repository.save_policy({
            "name": name,
            "category": category,
            "action": action,
            "description": description,
            "keywords": terms,
            "enabled": bool(enabled),
            "created_at": None,
        })

    def delete_policy(self, name):
        self.repository.delete_policy(name)

    def evaluate(self, prompt: str):
        """Return the strongest enabled matching keyword policy."""
        text = (prompt or "").casefold()
        matches = []
        for policy in self.list_policies():
            if not policy.get("enabled", True):
                continue
            keywords = policy.get("keywords") or []
            if keywords and any(term.casefold() in text for term in keywords if term.strip()):
                matches.append(policy)
        # Safety precedence: BLOCK > WARN > ALLOW.
        precedence = {"BLOCK": 3, "WARN": 2, "ALLOW": 1}
        matches.sort(key=lambda p: precedence.get(p.get("action", "WARN"), 0), reverse=True)
        return matches[0] if matches else None
