"""
Thibitisha In-Memory Data Store
Loads synthetic subscriber data for fast lookups.
In production, this would be Redis + PostgreSQL.
"""
import json
import os
from typing import Dict, Optional


class SubscriberStore:
    """In-memory store for subscriber data."""

    def __init__(self, data_path: str = "data/subscribers.json"):
        self._subscribers: Dict[str, Dict] = {}
        self._by_msisdn_hash: Dict[str, Dict] = {}
        self._by_id: Dict[str, Dict] = {}
        self._load_data(data_path)

    def _load_data(self, path: str):
        """Load subscriber data from JSON file."""
        if not os.path.exists(path):
            print(f"⚠️ Data file not found: {path}")
            print("   Run: python generate_data.py")
            return

        with open(path, 'r') as f:
            subscribers = json.load(f)

        for sub in subscribers:
            self._subscribers[sub["subscriber_id"]] = sub
            self._by_msisdn_hash[sub["msisdn_hash"]] = sub
            self._by_id[sub["id_number"]] = sub

        print(f"✅ Loaded {len(self._subscribers)} subscribers into memory")

    def get_by_msisdn_hash(self, msisdn_hash: str) -> Optional[Dict]:
        return self._by_msisdn_hash.get(msisdn_hash)

    def get_by_id(self, id_number: str) -> Optional[Dict]:
        return self._by_id.get(id_number)

    def get_by_subscriber_id(self, subscriber_id: str) -> Optional[Dict]:
        return self._subscribers.get(subscriber_id)

    def get_mno_data(self, mno: str) -> Dict[str, Dict]:
        """Get all subscribers for a specific MNO."""
        return {
            h: s for h, s in self._by_msisdn_hash.items()
            if s.get("mno") == mno
        }

    def count(self) -> int:
        return len(self._subscribers)

    def get_stats(self) -> Dict:
        """Get dataset statistics."""
        mno_counts = {}
        fraud_counts = {}

        for sub in self._subscribers.values():
            mno = sub.get("mno", "unknown")
            mno_counts[mno] = mno_counts.get(mno, 0) + 1

            profile = sub.get("fraud_profile", "normal")
            fraud_counts[profile] = fraud_counts.get(profile, 0) + 1

        return {
            "total_subscribers": self.count(),
            "by_mno": mno_counts,
            "by_fraud_profile": fraud_counts
        }
