# Thibitisha Platform
## Cross-Telco Trust Infrastructure for Kenya

> **⚠️ DEVELOPMENT VERSION** — This is a functional prototype using synthetic data. No real MNO connections. No real subscriber data. Safe to run anywhere.

---

## What This Is

Thibitisha is a real-time fraud prevention API that verifies the integrity of a phone line **before** a transaction or authentication event occurs. It checks:

- **SIM swap recency** across all 4 Kenyan MNOs
- **Device fingerprint** consistency
- **Location proximity** to home base
- **Transaction velocity** patterns
- **Behavioral anomalies**

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Bank App  │────▶│  Thibitisha  │────▶│  MNO Adapters   │
│  /Consumer  │     │     API      │     │ (Mock for dev)  │
└─────────────┘     └──────────────┘     └─────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Risk Scoring │
                    │   Engine     │
                    └──────────────┘
```

## Quick Start

### 1. Clone & Setup

```bash
git clone <repo-url>
cd thibitisha-platform
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate Synthetic Data

```bash
python generate_data.py
```

This creates `data/subscribers.json` with 10,000 fake Kenyan subscribers including fraud profiles.

### 3. Run the API

```bash
uvicorn main:app --reload --port 8000
```

### 4. Open the Docs

Visit: [http://localhost:8000/docs](http://localhost:8000/docs)

Interactive Swagger UI with all endpoints.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check + MNO adapter status |
| GET | `/stats` | Dataset statistics |
| POST | `/v1/verify/transaction` | Verify transaction before execution |
| POST | `/v1/verify/recipient` | Verify recipient before sending money |
| POST | `/v1/verify/sim-swap` | Direct SIM swap status check |
| GET | `/v1/merchants/{till_number}` | Merchant verification lookup |

---

## Test a Verification

### Safe Transaction (Should return PROCEED)

```bash
curl -X POST "http://localhost:8000/v1/verify/transaction" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "TXN-001",
    "amount": {"value": "5000.00", "currency": "KES"},
    "payer": {
      "msisdn_hash": "sha256$7d8e9f...a1b2c3",
      "device_fingerprint": "fp_known_device"
    },
    "context": {
      "timestamp": "2026-08-20T10:30:00+03:00",
      "location": {"latitude": -1.2921, "longitude": 36.8219},
      "channel": "MOBILE_APP"
    }
  }'
```

### Response

```json
{
  "verification_id": "VRF-20260820-a1b2c3",
  "risk_score": 145,
  "risk_tier": "LOW",
  "recommendation": "PROCEED",
  "confidence": 0.94,
  "signals": [...],
  "mno_coverage": {
    "airtel": "AVAILABLE",
    "safaricom": "AVAILABLE",
    "telkom": "AVAILABLE",
    "faiba": "AVAILABLE"
  },
  "response_time_ms": 127
}
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Project Structure

```
thibitisha-platform/
├── main.py                      # FastAPI application
├── generate_data.py             # Synthetic data generator
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── data/                        # Generated data (gitignored)
│   ├── subscribers.json
│   └── lookups.json
├── thibitisha/
│   ├── core/
│   │   ├── risk_engine.py       # Risk scoring algorithm
│   │   └── data_store.py        # In-memory data store
│   ├── adapters/
│   │   └── mno_adapter.py       # MNO adapter interface + mocks
│   └── api/
│       └── schemas.py           # Pydantic models
└── tests/
    └── test_api.py              # API tests
```

---

## Risk Scoring Weights

| Signal | Weight | Source |
|--------|--------|--------|
| SIM Swap Recency | 35% | MNO APIs |
| Device Fingerprint | 25% | Device Intel |
| Location Proximity | 20% | IP + Cell Tower |
| Transaction Velocity | 15% | Internal Cache |
| Behavioral Pattern | 5% | ML Model |

---

## This Week's Roadmap

| Day | Task | Deliverable |
|-----|------|-------------|
| **Mon** | Setup + data generation | Running API with 10K subscribers |
| **Tue** | Risk engine tuning | Accurate fraud detection on synthetic data |
| **Wed** | API hardening + tests | 100% test coverage on core endpoints |
| **Thu** | Connect demo UI to real API | Interactive demo with live backend |
| **Fri** | Documentation + CA prep | Pitch-ready platform + API docs |

---

## Next Steps (After This Week)

1. **CA Sandbox Application** — Apply for regulatory sandbox status
2. **Airtel Test API** — Connect to Airtel's test environment
3. **Bank Pilot** — Onboard 2 partner banks for live testing
4. **Production Hardening** — PostgreSQL, Redis, Kubernetes, security audit

---

## License

Proprietary — Thibitisha Trust Utility Ltd (Incorporation Pending)

## Contact

[Your Name] — Founder, Thibitisha
[Email] | [Phone]


## Bank Integration Endpoints

Thibitisha provides bank-specific endpoints that simulate exactly how a Kenyan bank would integrate:

### `POST /v1/bank/authorize-transfer`
Simulates fund transfer authorization. Called AFTER PIN validation, BEFORE OTP is sent.

**Bank Decision Logic:**
| Risk Tier | Bank Action | OTP Sent | Customer Message |
|-----------|-------------|----------|-----------------|
| LOW | APPROVED | Yes | "Enter OTP to complete" |
| MEDIUM | CHALLENGE | Yes + alert | "OTP sent + security alert" |
| HIGH | CHALLENGE | No | "Visit branch for verification" |
| CRITICAL | BLOCKED | No | "Transaction blocked. Account frozen." |

### `POST /v1/bank/authorize-login`
Simulates mobile/internet banking login. Called AFTER password check, BEFORE OTP.

### `POST /v1/bank/atm-cardless`
Simulates cardless ATM withdrawal authorization.

### `GET /v1/bank/fraud-summary`
Returns bank dashboard metrics: blocked transactions, fraud prevention rate, top signals.

## How a Bank Integrates (Code Example)

```python
from thibitisha import Client

client = Client(
    client_id="KCB-BANK-001",
    client_secret="...",
    cert_path="/path/to/kcb-mtls.crt"
)

def authorize_transfer(transaction):
    # Step 1: Validate PIN (existing)
    if not validate_pin(transaction.user_id, transaction.pin):
        return {"status": "DENIED", "reason": "INVALID_PIN"}

    # Step 2: THIBITISHA CHECK (NEW)
    result = client.bank_authorize_transfer(
        transaction_id=transaction.id,
        customer_id=transaction.user_id,
        customer_phone_hash=hash_phone(transaction.phone),
        amount_kes=transaction.amount,
        device_fingerprint=transaction.device_fp
    )

    # Step 3: Act on result
    if result["bank_decision"] == "BLOCKED":
        freeze_account(transaction.user_id)
        alert_fraud_team(result)
        return {"status": "BLOCKED", "message": result["customer_notification"]}

    elif result["bank_decision"] == "CHALLENGE":
        if result["otp_sent"]:
            send_otp_with_alert(transaction.phone)
            return {"status": "CHALLENGE", "message": result["customer_notification"]}
        else:
            return {"status": "BLOCKED", "message": result["customer_notification"]}

    else:  # APPROVED
        send_otp(transaction.phone)
        return {"status": "APPROVED", "message": result["customer_notification"]}
```
