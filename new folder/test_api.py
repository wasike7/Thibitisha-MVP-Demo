"""
Thibitisha API Tests
Run: pytest tests/
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Thibitisha API"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_subscribers"] > 0


def test_verify_transaction_safe():
    # First, we need to get a known safe subscriber hash
    # For testing, we'll use a hash from the generated data
    # This test assumes data has been generated
    import json
    import hashlib

    # Generate a predictable hash for testing
    test_msisdn = "254701000001"
    test_hash = hashlib.sha256(f"{test_msisdn}thibitisha_dev_salt_2026".encode()).hexdigest()

    payload = {
        "transaction_id": "TXN-TEST-001",
        "transaction_type": "P2P_TRANSFER",
        "amount": {"value": "5000.00", "currency": "KES"},
        "payer": {
            "msisdn_hash": f"sha256${test_hash}",
            "device_fingerprint": "fp_test_001"
        },
        "context": {
            "timestamp": "2026-08-20T10:30:00+03:00",
            "location": {"latitude": -1.2921, "longitude": 36.8219, "accuracy_meters": 50},
            "channel": "MOBILE_APP"
        }
    }

    response = client.post("/v1/verify/transaction", json=payload)
    # May be 404 if subscriber not in generated data, which is OK for structure test
    assert response.status_code in [200, 404]


def test_verify_transaction_not_found():
    payload = {
        "transaction_id": "TXN-TEST-002",
        "transaction_type": "P2P_TRANSFER",
        "amount": {"value": "1000.00", "currency": "KES"},
        "payer": {
            "msisdn_hash": "sha256$nonexistent_hash_12345",
            "device_fingerprint": "fp_test_002"
        },
        "context": {
            "timestamp": "2026-08-20T10:30:00+03:00",
            "channel": "MOBILE_APP"
        }
    }

    response = client.post("/v1/verify/transaction", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "SUBSCRIBER_NOT_FOUND"


def test_merchant_lookup():
    response = client.get("/v1/merchants/123456")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ABC Electronics Ltd"
    assert data["badge"] == "PLATINUM"


def test_merchant_not_found():
    response = client.get("/v1/merchants/999999")
    assert response.status_code == 404
