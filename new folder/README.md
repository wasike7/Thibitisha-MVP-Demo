# Thibitisha Demo-MVP

Thibitisha is a functional MVP for cross-telco transaction trust checks. The original single-file demo is served by a local Node.js API that calculates verification outcomes and persists verification history in JSON.

## Run locally

Requirements: Node.js 18 or newer.

```powershell
cd Thibitisha-Demo-MVP
npm start
```

Open `http://localhost:3000` in a browser. The API is available at `/api` on the same origin.

## API

- `GET /api/health` checks service availability.
- `GET /api/verifications` returns persisted verification records.
- `POST /api/verifications` accepts `{ "scenario": "safe" | "simswap" | "merchant" }` and returns a scored decision.
- `GET /api/merchants?q=123456` looks up the demo merchant.
- `POST /api/merchant-transactions` authorizes a synthetic payment after merchant verification.

Verification records are stored in `data/verifications.json` for this MVP. Replace that store with a database and real MNO adapters before production use; the current scenarios intentionally remain simulated.

