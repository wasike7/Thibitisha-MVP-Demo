"""
Thibitisha API Request/Response Models
OpenAPI-compatible Pydantic schemas.
"""
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from enum import Enum


class RiskTier(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Recommendation(str, Enum):
    PROCEED = "PROCEED"
    CHALLENGE = "CHALLENGE"
    BLOCK = "BLOCK"


class Amount(BaseModel):
    value: str = Field(..., example="5000.00")
    currency: str = Field(default="KES", example="KES")


class Location(BaseModel):
    latitude: float = Field(..., example=-1.2921)
    longitude: float = Field(..., example=36.8219)
    accuracy_meters: Optional[int] = Field(default=50, example=50)


class TransactionContext(BaseModel):
    timestamp: str = Field(..., example="2026-08-20T10:30:00+03:00")
    location: Optional[Location] = None
    channel: str = Field(default="MOBILE_APP", example="MOBILE_APP")
    ip_address: Optional[str] = Field(default=None, example="102.68.xxx.xxx")


class PayerInfo(BaseModel):
    msisdn_hash: str = Field(..., example="sha256$7d8e9f...a1b2c3")
    bank_account: Optional[str] = Field(default=None, example="****1234")
    device_fingerprint: Optional[str] = Field(default=None, example="fp_a3f7d9e2...")


class PayeeInfo(BaseModel):
    msisdn_hash: Optional[str] = Field(default=None, example="sha256$3a4b5c...d6e7f8")
    type: str = Field(default="PERSONAL", example="MERCHANT")
    till_number: Optional[str] = Field(default=None, example="123456")


class VerifyTransactionRequest(BaseModel):
    transaction_id: str = Field(..., example="TXN-2026-08-20-001")
    transaction_type: str = Field(default="P2P_TRANSFER", example="ATM_WITHDRAWAL")
    amount: Amount
    payer: PayerInfo
    payee: Optional[PayeeInfo] = None
    context: TransactionContext


class SignalDetail(BaseModel):
    name: str
    status: str
    risk_contribution: int
    details: Dict
    weight: float


class MNOCoverage(BaseModel):
    airtel: str = Field(default="AVAILABLE")
    safaricom: str = Field(default="AVAILABLE")
    telkom: str = Field(default="AVAILABLE")
    faiba: str = Field(default="AVAILABLE")


class VerifyTransactionResponse(BaseModel):
    verification_id: str
    status: str = Field(default="COMPLETED")
    risk_score: int = Field(..., ge=0, le=1000)
    risk_tier: RiskTier
    recommendation: Recommendation
    confidence: float = Field(..., ge=0, le=1)
    signals: List[SignalDetail]
    block_reasons: List[str]
    suggested_action: Optional[str]
    mno_coverage: MNOCoverage
    timestamp: str
    response_time_ms: int


class VerifyRecipientRequest(BaseModel):
    sender_msisdn: str = Field(..., example="2547XXXXXXXX")
    recipient_identifier: str = Field(..., example="2547XXXXXXXX")
    identifier_type: str = Field(default="MSISDN", example="MSISDN")
    amount: Amount
    context: Dict = Field(default_factory=dict)


class RecipientInfo(BaseModel):
    msisdn_masked: str
    name_match: str
    verified_since: Optional[str]
    badge: Optional[str]


class VerifyRecipientResponse(BaseModel):
    verification_id: str
    recipient: RecipientInfo
    risk_score: int
    risk_tier: RiskTier
    recommendation: Recommendation
    warnings: List[str]
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: int
    adapters: Dict


class StatsResponse(BaseModel):
    total_subscribers: int
    by_mno: Dict[str, int]
    by_fraud_profile: Dict[str, int]
