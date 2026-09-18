"""
Thibitisha Risk Scoring Engine
Calculates real-time risk scores based on multi-signal analysis.
All data is synthetic for development.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass
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


@dataclass
class RiskSignal:
    name: str
    status: str
    risk_contribution: int
    details: Dict
    weight: float


@dataclass
class RiskResult:
    risk_score: int
    risk_tier: RiskTier
    recommendation: Recommendation
    confidence: float
    signals: List[RiskSignal]
    block_reasons: List[str]
    suggested_action: Optional[str]
    response_time_ms: int
    timestamp: str


class RiskScoringEngine:
    """
    Multi-signal risk scoring engine.

    Signal Weights:
    - SIM Swap Recency: 35%
    - Device Fingerprint: 25%
    - Location Proximity: 20%
    - Transaction Velocity: 15%
    - Behavioral Pattern: 5%
    """

    def __init__(self):
        self.weights = {
            "sim_swap": 0.35,
            "device": 0.25,
            "location": 0.20,
            "velocity": 0.15,
            "behavioral": 0.05
        }

        # Score thresholds
        self.thresholds = {
            RiskTier.LOW: 300,
            RiskTier.MEDIUM: 500,
            RiskTier.HIGH: 750,
            RiskTier.CRITICAL: 1000
        }

    def calculate_sim_swap_score(self, subscriber: Dict, context: Dict) -> RiskSignal:
        """Score based on SIM swap history."""
        last_swap_str = subscriber.get("last_sim_swap")
        swap_count_90d = subscriber.get("swap_count_90d", 0)

        if not last_swap_str:
            # No swap history - safe
            return RiskSignal(
                name="SIM Swap",
                status="SAFE",
                risk_contribution=0,
                details={
                    "last_swap_date": None,
                    "days_since_swap": None,
                    "swap_count_90d": 0,
                    "message": "No SIM swap detected"
                },
                weight=self.weights["sim_swap"]
            )

        last_swap = datetime.fromisoformat(last_swap_str)
        now = datetime.now()
        days_since = (now - last_swap).days
        hours_since = (now - last_swap).total_seconds() / 3600

        # Calculate raw score (0-1000 for this signal)
        if hours_since < 24:
            raw_score = 1000  # Critical - swapped today
        elif days_since < 3:
            raw_score = 800
        elif days_since < 7:
            raw_score = 600
        elif days_since < 30:
            raw_score = 400
        elif days_since < 90:
            raw_score = 200
        else:
            raw_score = 50

        # Multiple swaps multiplier
        if swap_count_90d >= 3:
            raw_score = min(1000, raw_score * 1.5)
        elif swap_count_90d >= 2:
            raw_score = min(1000, raw_score * 1.2)

        contribution = int(raw_score * self.weights["sim_swap"])

        status = "SAFE" if days_since > 30 else ("WARN" if days_since > 7 else "DANGER")

        return RiskSignal(
            name="SIM Swap",
            status=status,
            risk_contribution=contribution,
            details={
                "last_swap_date": last_swap_str,
                "days_since_swap": days_since,
                "hours_since_swap": round(hours_since, 1),
                "swap_count_90d": swap_count_90d,
                "message": f"Last swap {days_since} days ago" if days_since >= 1 else f"Last swap {int(hours_since)} hours ago"
            },
            weight=self.weights["sim_swap"]
        )

    def calculate_device_score(self, subscriber: Dict, context: Dict) -> RiskSignal:
        """Score based on device fingerprint match."""
        device = subscriber.get("device", {})
        provided_fingerprint = context.get("device_fingerprint")

        if not provided_fingerprint:
            # No device fingerprint provided - neutral
            return RiskSignal(
                name="Device",
                status="UNKNOWN",
                risk_contribution=50,
                details={
                    "device_match": None,
                    "known_device": True,
                    "device_brand": device.get("brand"),
                    "message": "No device fingerprint provided in request"
                },
                weight=self.weights["device"]
            )

        stored_fingerprint = device.get("fingerprint")

        if provided_fingerprint == stored_fingerprint:
            # Exact match
            return RiskSignal(
                name="Device",
                status="MATCH",
                risk_contribution=0,
                details={
                    "device_match": True,
                    "known_device": True,
                    "device_brand": device.get("brand"),
                    "device_model": device.get("model"),
                    "message": "Device fingerprint matches known device"
                },
                weight=self.weights["device"]
            )
        else:
            # Mismatch - potential fraud
            return RiskSignal(
                name="Device",
                status="MISMATCH",
                risk_contribution=int(900 * self.weights["device"]),
                details={
                    "device_match": False,
                    "known_device": False,
                    "expected_brand": device.get("brand"),
                    "expected_model": device.get("model"),
                    "message": "Unknown device detected - possible account takeover"
                },
                weight=self.weights["device"]
            )

    def calculate_location_score(self, subscriber: Dict, context: Dict) -> RiskSignal:
        """Score based on location proximity to home base."""
        tx_location = context.get("location", {})

        if not tx_location or not tx_location.get("latitude"):
            return RiskSignal(
                name="Location",
                status="UNKNOWN",
                risk_contribution=25,
                details={
                    "proximity_match": None,
                    "distance_km": None,
                    "home_county": subscriber.get("home_county"),
                    "message": "No location data provided"
                },
                weight=self.weights["location"]
            )

        home_lat = subscriber.get("home_latitude", 0)
        home_lon = subscriber.get("home_longitude", 0)
        tx_lat = tx_location.get("latitude", 0)
        tx_lon = tx_location.get("longitude", 0)

        # Simple Euclidean distance (good enough for demo)
        # 1 degree lat ≈ 111km, 1 degree lon ≈ 111km * cos(lat)
        import math
        lat_diff = abs(home_lat - tx_lat)
        lon_diff = abs(home_lon - tx_lon) * math.cos(math.radians(home_lat))
        distance_km = math.sqrt(lat_diff**2 + lon_diff**2) * 111

        if distance_km < 5:
            raw_score = 0
            status = "NEARBY"
        elif distance_km < 50:
            raw_score = 150
            status = "CLOSE"
        elif distance_km < 200:
            raw_score = 400
            status = "DISTANT"
        elif distance_km < 500:
            raw_score = 700
            status = "FAR"
        else:
            raw_score = 950
            status = "ANOMALY"

        return RiskSignal(
            name="Location",
            status=status,
            risk_contribution=int(raw_score * self.weights["location"]),
            details={
                "proximity_match": distance_km < 50,
                "distance_km": round(distance_km, 1),
                "home_county": subscriber.get("home_county"),
                "home_coordinates": [home_lat, home_lon],
                "message": f"{round(distance_km, 1)}km from home base"
            },
            weight=self.weights["location"]
        )

    def calculate_velocity_score(self, subscriber: Dict, context: Dict) -> RiskSignal:
        """Score based on transaction velocity (mock for demo)."""
        # In production, this would query actual transaction history
        # For demo, we use the fraud profile to simulate velocity
        fraud_profile = subscriber.get("fraud_profile", "normal")

        if fraud_profile == "multiple_swaps":
            return RiskSignal(
                name="Velocity",
                status="HIGH",
                risk_contribution=int(600 * self.weights["velocity"]),
                details={
                    "transactions_24h": 12,
                    "amount_24h_kes": 187000,
                    "message": "Unusually high transaction velocity"
                },
                weight=self.weights["velocity"]
            )
        elif fraud_profile == "sim_swap_recent":
            return RiskSignal(
                name="Velocity",
                status="ELEVATED",
                risk_contribution=int(300 * self.weights["velocity"]),
                details={
                    "transactions_24h": 5,
                    "amount_24h_kes": 45000,
                    "message": "Elevated activity after SIM swap"
                },
                weight=self.weights["velocity"]
            )
        else:
            return RiskSignal(
                name="Velocity",
                status="NORMAL",
                risk_contribution=0,
                details={
                    "transactions_24h": random.randint(1, 4),
                    "amount_24h_kes": random.randint(2000, 25000),
                    "message": "Transaction velocity within normal range"
                },
                weight=self.weights["velocity"]
            )

    def calculate_behavioral_score(self, subscriber: Dict, context: Dict) -> RiskSignal:
        """Score based on behavioral patterns (mock ML model)."""
        fraud_profile = subscriber.get("fraud_profile", "normal")

        if fraud_profile == "normal":
            return RiskSignal(
                name="Behavioral",
                status="NORMAL",
                risk_contribution=0,
                details={
                    "pattern_match": 0.94,
                    "message": "Behavioral patterns consistent with history"
                },
                weight=self.weights["behavioral"]
            )
        else:
            return RiskSignal(
                name="Behavioral",
                status="ANOMALOUS",
                risk_contribution=int(400 * self.weights["behavioral"]),
                details={
                    "pattern_match": 0.23,
                    "message": "Behavioral anomaly detected"
                },
                weight=self.weights["behavioral"]
            )

    def calculate_risk(self, subscriber: Dict, context: Dict) -> RiskResult:
        """Calculate comprehensive risk score."""
        start_time = datetime.now()

        # Calculate all signals
        signals = [
            self.calculate_sim_swap_score(subscriber, context),
            self.calculate_device_score(subscriber, context),
            self.calculate_location_score(subscriber, context),
            self.calculate_velocity_score(subscriber, context),
            self.calculate_behavioral_score(subscriber, context)
        ]

        # Sum contributions
        total_score = sum(s.risk_contribution for s in signals)
        total_score = min(1000, max(0, total_score))

        # Determine tier
        if total_score < self.thresholds[RiskTier.LOW]:
            tier = RiskTier.LOW
        elif total_score < self.thresholds[RiskTier.MEDIUM]:
            tier = RiskTier.MEDIUM
        elif total_score < self.thresholds[RiskTier.HIGH]:
            tier = RiskTier.HIGH
        else:
            tier = RiskTier.CRITICAL

        # Determine recommendation
        if tier == RiskTier.LOW:
            recommendation = Recommendation.PROCEED
        elif tier == RiskTier.MEDIUM:
            recommendation = Recommendation.CHALLENGE
        elif tier == RiskTier.HIGH:
            recommendation = Recommendation.BLOCK
        else:
            recommendation = Recommendation.BLOCK

        # Block reasons
        block_reasons = []
        suggested_action = None

        for signal in signals:
            if signal.status in ["DANGER", "MISMATCH", "ANOMALY"]:
                block_reasons.append(f"{signal.name.upper()}_ALERT")

        if tier == RiskTier.CRITICAL:
            suggested_action = "REQUIRE_IN_BRANCH_VERIFICATION"
        elif tier == RiskTier.HIGH:
            suggested_action = "REQUIRE_VIDEO_CALL_VERIFICATION"
        elif tier == RiskTier.MEDIUM:
            suggested_action = "SEND_ADDITIONAL_OTP"

        # Confidence based on data completeness
        confidence = 0.85
        if any(s.status == "UNKNOWN" for s in signals):
            confidence -= 0.1

        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return RiskResult(
            risk_score=total_score,
            risk_tier=tier,
            recommendation=recommendation,
            confidence=round(confidence, 2),
            signals=signals,
            block_reasons=block_reasons,
            suggested_action=suggested_action,
            response_time_ms=elapsed_ms,
            timestamp=datetime.now().isoformat()
        )
