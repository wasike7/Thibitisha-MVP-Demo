# Thibitisha — Bank-Side Integration Analysis
## How Kenyan Bank Fraud Works & Where Thibitisha Stops It
### September 2026 | Confidential

---

## 1. How Bank Fraud Actually Happens in Kenya Today

Based on current industry reporting and bank security disclosures, here is the exact attack chain:

### The SIM Swap Attack Chain (Most Common)

```
STEP 1          STEP 2              STEP 3              STEP 4              STEP 5
┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Phishing│───▶│ Social Eng  │───▶│ SIM Swap    │───▶│ OTP Intercept│───▶│ Fund Transfer│
│ /Leak   │    │ at MNO Agent│    │ (New SIM)   │    │ via SMS     │    │ (M-PESA/Bank)│
└─────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
   │                │                  │                  │                  │
   │                │                  │                  │                  │
   ▼                ▼                  ▼                  ▼                  ▼
Get ID +        Convince agent     Attacker gets      Bank sends OTP     Money is gone
phone number    to issue new SIM    control of         to attacker's      in < 3 minutes
from dark web   using fake ID       victim's number    new SIM
                or bribery
```

**Key insight:** The bank's fraud detection system sees a **legitimate login** (correct credentials) and a **legitimate OTP** (correctly entered). The bank has **no way to know** the phone line has been compromised. cite🛠web_search:18#6:~:text=Stolen personal data from phishing or leaks...SIM swap at telecom agents...OTP interception...Instant fund transfers

### Attack Variants

| Variant | How It Works | Bank's Blind Spot |
|---------|-------------|-------------------|
| **Classic SIM Swap** | Attacker gets new SIM with victim's number | Bank doesn't know SIM was swapped |
| **Insider SIM Swap** | Corrupt MNO agent does the swap off-books | No audit trail in MNO systems |
| **OTP Forwarding Scam** | Victim tricked into sharing OTP via social engineering | Bank sees "user authorized" |
| **Device Swap + SIM** | New device + new SIM simultaneously | Bank sees new device but no SIM context |
| **Merchant Till Fraud** | Fake merchant till collects payments | Bank verifies till number, not merchant identity |

---

## 2. How Kenyan Banks Currently Prevent Fraud

### Current Stack (As of 2026)

**Layer 1: Rule-Based Systems**
- Transaction amount thresholds (e.g., flag > KSh 100,000)
- Velocity checks (e.g., > 5 transactions/hour)
- Geographic checks (e.g., transaction from outside Kenya)
- Time-based rules (e.g., transactions at 3 AM)

**Layer 2: OTP via SMS**
- 4-6 digit code sent to registered mobile number
- Expires in 2 minutes cite🛠web_search:18#11:~:text=Email and SMS OTP expires within 2 minutes
- Single-use only
- **Critical weakness:** Assumes the phone is in the owner's possession

**Layer 3: Behavioral Analytics (Emerging)**
- AI-driven pattern analysis cite🛠web_search:18#0:~:text=a majority of Kenyan banks have quietly embedded artificial intelligence...helping banks detect fraud in real time
- Device fingerprinting
- Typing cadence, mouse movement (web banking)
- **Critical weakness:** Learns slowly; SIM swap is a sudden change

**Layer 4: Manual Review**
- Fraud team reviews flagged transactions
- Callback to customer
- **Critical weakness:** Takes hours; fraudster is gone in minutes

### The Gap Thibitisha Fills

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CURRENT BANK FRAUD STACK                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   User Login ──▶ Password Check ──▶ OTP via SMS ──▶ Transaction Approved   │
│        │                                                                    │
│        │         [NO CHECK: Is the phone line compromised?]                  │
│        │                                                                    │
│        ▼                                                                    │
│   Fraudster has credentials + controls SIM ──▶ OTP intercepted ──▶ FUNDS    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    WITH THIBITISHA INTEGRATION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   User Login ──▶ Password Check ──▶ THIBITISHA CHECK ──▶ OTP via SMS       │
│        │                              │                                     │
│        │                              │  SIM swap? Device match? Location?  │
│        │                              │  Risk Score: 892 (CRITICAL)         │
│        │                              ▼                                     │
│        │                        BLOCK ──▶ Alert fraud team                  │
│        │                        No OTP sent                                 │
│        │                                                                  │
│   Fraudster has credentials + controls SIM ──▶ CANNOT GET OTP ──▶ SAFE     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Exact Integration Points — Where Thibitisha Plugs In

### Integration Point A: Login Authentication (Pre-OTP)

**When:** After password validation, BEFORE OTP is sent
**Thibitisha Query:** `POST /v1/verify/transaction`
**What it checks:**
- Has the user's registered phone been SIM-swapped recently?
- Is the login device consistent with history?
- Is the login location reasonable?

**Bank Action:**
| Risk Tier | Action |
|-----------|--------|
| LOW | Send OTP normally |
| MEDIUM | Send OTP + push notification alert to app |
| HIGH | BLOCK login, require branch visit or video call |
| CRITICAL | BLOCK + freeze account + alert fraud team |

### Integration Point B: Transaction Authorization (Pre-OTP)

**When:** After user initiates transfer/withdrawal, BEFORE OTP is sent
**Thibitisha Query:** `POST /v1/verify/transaction`
**What it checks:**
- Same as login PLUS:
- Is the recipient verified? (merchant badge check)
- Transaction velocity anomaly?
- Amount vs. historical pattern?

**Bank Action:**
| Risk Tier | Action |
|-----------|--------|
| LOW | Send OTP, proceed normally |
| MEDIUM | Send OTP + require additional security question |
| HIGH | BLOCK transaction, notify customer via alternate channel |
| CRITICAL | BLOCK + flag for investigation + temporarily freeze account |

### Integration Point C: New Payee / Beneficiary Addition

**When:** User adds a new recipient
**Thibitisha Query:** `POST /v1/verify/recipient`
**What it checks:**
- Is the recipient's phone line legitimate?
- Has the recipient been flagged by other banks?
- Merchant verification (if till/paybill)

### Integration Point D: ATM Withdrawal (Cardless)

**When:** User initiates cardless ATM withdrawal
**Thibitisha Query:** `POST /v1/verify/transaction`
**What it checks:**
- Phone line integrity
- ATM location vs. user's usual location
- Time of day anomaly

### Integration Point E: Batch / Standing Orders

**When:** Scheduled payments execute
**Thibitisha Query:** `POST /v1/verify/transaction` (async)
**What it checks:**
- Account holder's line status at execution time
- Recipient status

---

## 4. The Bank Transaction Flow — With & Without Thibitisha

### Flow 1: Mobile Banking Fund Transfer

```
WITHOUT THIBITISHA:
┌─────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ Customer│──▶│ Bank App    │──▶│ Bank Core   │──▶│ SMS Gateway │──▶│ Customer    │
│         │   │ (Enter PIN) │   │ (Validate)  │   │ (Send OTP)  │   │ (Enter OTP) │
└─────────┘   └─────────────┘   └─────────────┘   └─────────────┘   └──────┬──────┘
                                                                            │
                                                                            ▼
                                                                     ┌─────────────┐
                                                                     │ Bank Core   │
                                                                     │ (Transfer)  │
                                                                     └─────────────┘

PROBLEM: If SIM is swapped, fraudster gets OTP. Bank has no way to know.


WITH THIBITISHA:
┌─────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ Customer│──▶│ Bank App    │──▶│ Bank Core   │──▶│ THIBITISHA  │──▶│ Risk Score  │
│         │   │ (Enter PIN) │   │ (Validate)  │   │ API         │   │ < 200ms     │
└─────────┘   └─────────────┘   └─────────────┘   └──────┬──────┘   └──────┬──────┘
                                                         │                   │
                              ┌──────────────────────────┘                   │
                              │ Risk Score > 750?                            │
                              │ YES ──▶ BLOCK, no OTP sent                   │
                              │ NO  ──▶ Continue to SMS Gateway              │
                              ▼                                              │
                       ┌─────────────┐                                       │
                       │ SMS Gateway │◀──────────────────────────────────────┘
                       │ (Send OTP)  │
                       └──────┬──────┘
                              │
                              ▼
                       ┌─────────────┐
                       │ Customer    │
                       │ (Enter OTP) │
                       └──────┬──────┘
                              │
                              ▼
                       ┌─────────────┐
                       │ Bank Core   │
                       │ (Transfer)  │
                       └─────────────┘

SOLUTION: If SIM is swapped, Thibitisha catches it BEFORE OTP is sent.
```

### Flow 2: Internet Banking Login

```
WITHOUT THIBITISHA:
User enters username/password ──▶ Valid ──▶ Send OTP to SMS ──▶ User enters OTP ──▶ Logged in

WITH THIBITISHA:
User enters username/password ──▶ Valid ──▶ Thibitisha Check ──▶
    ├─ LOW risk ──▶ Send OTP ──▶ Login
    ├─ MEDIUM ──▶ Send OTP + email alert
    ├─ HIGH ──▶ BLOCK + "Contact branch"
    └─ CRITICAL ──▶ BLOCK + freeze account + fraud alert
```

### Flow 3: ATM Cardless Withdrawal

```
WITHOUT THIBITISHA:
User requests withdrawal via app ──▶ Bank generates code ──▶ SMS code to user ──▶
User enters code at ATM ──▶ ATM dispenses cash

WITH THIBITISHA:
User requests withdrawal via app ──▶ Thibitisha Check ──▶
    ├─ SAFE ──▶ Generate code ──▶ SMS ──▶ ATM dispenses
    ├─ SUSPICIOUS ──▶ Require additional app confirmation
    └─ FRAUD ──▶ BLOCK + "Visit branch"
```

---

## 5. The KCB Case Study — Why This Matters

KCB Bank Kenya, East Africa's largest banking group, reported:
- **201 fraud incidents** in recent period
- **Sh760,000 written off** due to fraud and forgeries cite🛠web_search:18#3:~:text=The group wrote off Sh760,000 due to fraud and forgeries...while recording 201 fraud incidents and blocking
- Fired **60 staff** to combat digital fraud cite🛠web_search:18#3:~:text=KCB Fires 60 Staff to Combat Digital Fraud

**What this tells us:**
1. Even the largest bank with the biggest security budget is struggling
2. Internal fraud is a significant component (hence staff firings)
3. The cost is real — Sh760K is just what they *admitted* to writing off
4. They're investing in IT asset management and visibility, but not real-time telco-layer intelligence cite🛠web_search:18#12:~:text=KCB Bank Kenya saves $23.3M and achieves 98% IT visibility

**Thibitisha's value proposition to KCB:**
- Stop fraud *before* OTP is sent, not after money is gone
- Cross-bank intelligence (if fraudster hits Equity first, KCB knows)
- No additional infrastructure on bank side — just an API call

---

## 6. Integration Architecture for Banks

### Option 1: Direct API Integration (Recommended for Pilot)

```
Bank Core Banking System (CBS)
    │
    │ HTTP POST /v1/verify/transaction
    │ (mTLS + OAuth 2.0)
    ▼
┌─────────────────────────────────────┐
│  Thibitisha API Gateway (Kong)      │
│  • Rate limiting: 10K req/min       │
│  • Auth: mTLS + JWT                 │
│  • Request validation               │
└─────────────────────────────────────┘
    │
    │ Internal gRPC
    ▼
┌─────────────────────────────────────┐
│  Risk Scoring Engine                │
│  • Query MNO adapters (async)       │
│  • Calculate composite score        │
│  • < 200ms response                 │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  MNO Adapters (Airtel, Safaricom,   │
│  Telkom, Faiba)                     │
│  • SIM swap data                    │
│  • Device info                      │
│  • Location (with consent)          │
└─────────────────────────────────────┘
```

**Bank code example:**
```python
from thibitisha import Client

# Initialize (done once at app startup)
client = Client(
    client_id="KCB-BANK-001",
    client_secret="...",
    cert_path="/path/to/kcb-mtls.crt"
)

# Inside transaction authorization flow
def authorize_transfer(transaction):
    # Step 1: Validate credentials (existing)
    if not validate_password(transaction.user_id, transaction.password):
        return {"status": "DENIED", "reason": "INVALID_CREDENTIALS"}

    # Step 2: THIBITISHA CHECK (NEW)
    verification = client.verify_transaction(
        transaction_id=transaction.id,
        payer_msisdn_hash=hash_msisdn(transaction.registered_phone),
        amount_kes=transaction.amount,
        device_fingerprint=transaction.device_fp,
        location={"latitude": tx.lat, "longitude": tx.lon}
    )

    # Step 3: Act on Thibitisha result
    if verification.risk_tier == "CRITICAL":
        freeze_account(transaction.user_id)
        alert_fraud_team(transaction, verification)
        return {"status": "DENIED", "reason": "SECURITY_BLOCK"}

    elif verification.risk_tier == "HIGH":
        return {"status": "CHALLENGE", "method": "BRANCH_VISIT"}

    elif verification.risk_tier == "MEDIUM":
        # Send OTP but also send push notification
        otp = generate_otp(transaction.user_id)
        send_sms(transaction.phone, otp)
        send_push_notification(transaction.user_id, "Unusual transaction detected")
        return {"status": "OTP_SENT_WITH_ALERT"}

    else:  # LOW
        # Business as usual
        otp = generate_otp(transaction.user_id)
        send_sms(transaction.phone, otp)
        return {"status": "OTP_SENT"}
```

### Option 2: Middleware Integration (For Banks with Legacy Systems)

For banks with old core banking systems that can't easily integrate APIs:

```
Bank Internet Banking Portal
    │
    │ (No changes to bank code)
    ▼
┌─────────────────────────────────────┐
│  Thibitisha Middleware              │
│  (Deployed inside bank datacenter)  │
│  • Intercepts HTTP requests         │
│  • Injects verification step        │
│  • Forwards to CBS                  │
└─────────────────────────────────────┘
    │
    ▼
Bank Core Banking System (unchanged)
```

### Option 3: Switch-Level Integration (PesaLink / KEPSS)

For maximum impact, integrate at the national payment switch level:

```
Bank A ──▶                    ┌─────────────────┐
Bank B ──▶  PesaLink Switch ──▶ Thibitisha Layer ──▶ Settlement
Bank C ──▶                    └─────────────────┘
```

**Advantage:** Every bank gets protection without individual integration.
**Challenge:** Requires KBA / CBK coordination.

---

## 7. Updated MVP Demo — Bank-Side Simulation

The updated MVP will simulate:

1. **Bank Admin Dashboard** — See transactions flowing through Thibitisha
2. **Real-time blocking** — Watch a fraudulent transaction get stopped
3. **Fraud analyst view** — See why a transaction was blocked (all 4 signals)
4. **Customer notification** — See what the customer sees when blocked
5. **Audit trail** — Immutable log of every decision

### Demo Scenarios

| Scenario | Bank Action | Thibitisha Result | Customer Experience |
|----------|------------|-------------------|---------------------|
| **Normal Transfer** | Query Thibitisha | Risk: 89 (LOW) | OTP sent, transfer completes |
| **SIM Swap Fraud** | Query Thibitisha | Risk: 892 (CRITICAL) | "Transaction blocked for security. Contact branch." |
| **New Device** | Query Thibitisha | Risk: 412 (MEDIUM) | OTP sent + push alert: "New device detected" |
| **Merchant Payment** | Query Thibitisha + Merchant API | Risk: 67 (LOW), Merchant: PLATINUM | OTP sent, payment completes |
| **Suspicious Recipient** | Query Thibitisha | Risk: 750 (HIGH) | "Recipient unverified. Confirm at branch." |

---

## 8. Metrics That Matter to Banks

| Metric | Current (Without Thibitisha) | Target (With Thibitisha) |
|--------|------------------------------|--------------------------|
| Fraud detection speed | Hours (batch review) | < 200ms (real-time) |
| SIM swap fraud blocked | ~0% (blind to SIM swaps) | > 85% |
| False positive rate | N/A | < 2% |
| Customer friction | High (branch visits for disputes) | Low (silent verification) |
| Fraud write-offs | Sh760K+ (KCB example) | -80% reduction |
| Regulatory compliance | Reactive (report after fraud) | Proactive (prevent before fraud) |

---

*Document prepared for bank partnership discussions and CA sandbox application.*
