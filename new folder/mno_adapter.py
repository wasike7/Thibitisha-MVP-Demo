"""
Thibitisha MNO Adapter Layer
Abstract interface + mock implementations for all 4 Kenyan MNOs.
In production, these connect to real MNO APIs via private VPC.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from datetime import datetime


class MNOAdapter(ABC):
    """Abstract base class for MNO adapters."""

    @property
    @abstractmethod
    def mno_name(self) -> str:
        pass

    @abstractmethod
    async def get_sim_swap_info(self, msisdn_hash: str) -> Dict:
        """Return SIM swap information for a subscriber."""
        pass

    @abstractmethod
    async def get_device_info(self, msisdn_hash: str) -> Dict:
        """Return device information for a subscriber."""
        pass

    @abstractmethod
    async def get_location(self, msisdn_hash: str) -> Dict:
        """Return approximate location (with user consent)."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict:
        """Return adapter health status."""
        pass


class MockMNOAdapter(MNOAdapter):
    """Mock MNO adapter using synthetic data."""

    def __init__(self, mno_name: str, data_store: Dict):
        self._mno_name = mno_name
        self._data = data_store
        self._healthy = True

    @property
    def mno_name(self) -> str:
        return self._mno_name

    async def get_sim_swap_info(self, msisdn_hash: str) -> Dict:
        subscriber = self._data.get(msisdn_hash)
        if not subscriber:
            return {"status": "NOT_FOUND", "mno": self._mno_name}

        return {
            "status": "FOUND",
            "mno": self._mno_name,
            "last_swap_date": subscriber.get("last_sim_swap"),
            "swap_count_90d": subscriber.get("swap_count_90d", 0),
            "line_active": subscriber.get("consent_status") == "active"
        }

    async def get_device_info(self, msisdn_hash: str) -> Dict:
        subscriber = self._data.get(msisdn_hash)
        if not subscriber:
            return {"status": "NOT_FOUND", "mno": self._mno_name}

        device = subscriber.get("device", {})
        return {
            "status": "FOUND",
            "mno": self._mno_name,
            "device_fingerprint": device.get("fingerprint"),
            "brand": device.get("brand"),
            "model": device.get("model"),
            "imei": device.get("imei")
        }

    async def get_location(self, msisdn_hash: str) -> Dict:
        subscriber = self._data.get(msisdn_hash)
        if not subscriber:
            return {"status": "NOT_FOUND", "mno": self._mno_name}

        return {
            "status": "FOUND",
            "mno": self._mno_name,
            "home_county": subscriber.get("home_county"),
            "home_latitude": subscriber.get("home_latitude"),
            "home_longitude": subscriber.get("home_longitude"),
            "accuracy": "CELL_TOWER_APPROX"
        }

    async def health_check(self) -> Dict:
        return {
            "mno": self._mno_name,
            "status": "HEALTHY" if self._healthy else "DEGRADED",
            "latency_ms": 45,
            "last_sync": datetime.now().isoformat()
        }

    def set_healthy(self, healthy: bool):
        self._healthy = healthy


class MNOAdapterManager:
    """Manages all MNO adapters and aggregates responses."""

    def __init__(self):
        self.adapters: List[MNOAdapter] = []

    def register_adapter(self, adapter: MNOAdapter):
        self.adapters.append(adapter)

    async def query_all(self, msisdn_hash: str) -> Dict:
        """Query all MNOs and aggregate results."""
        import asyncio

        results = {}
        for adapter in self.adapters:
            try:
                swap_info = await adapter.get_sim_swap_info(msisdn_hash)
                results[adapter.mno_name] = {
                    "sim_swap": swap_info,
                    "status": "AVAILABLE"
                }
            except Exception as e:
                results[adapter.mno_name] = {
                    "status": "ERROR",
                    "error": str(e)
                }

        return results

    async def get_health_status(self) -> Dict:
        """Get health status of all adapters."""
        import asyncio

        health = {}
        for adapter in self.adapters:
            try:
                health[adapter.mno_name] = await adapter.health_check()
            except Exception as e:
                health[adapter.mno_name] = {"status": "UNREACHABLE", "error": str(e)}

        return health
