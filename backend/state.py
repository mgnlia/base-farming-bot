from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass
class FarmingState:
    status: str = "idle"
    halt_reason: str = ""
    wallet_address: str = ""
    eth_balance: float = 0.0
    usdc_balance: float = 0.0
    portfolio_value_usd: float = 0.0
    total_transactions: int = 0
    transactions_today: int = 0
    unique_protocols: set[str] = field(default_factory=set)
    unique_tokens: set[str] = field(default_factory=set)
    airdrop_score: float = 0.0
    activity_score: float = 0.0
    diversity_score: float = 0.0
    consistency_score: float = 0.0
    gas_spent_today_usd: float = 0.0
    gas_spent_total_usd: float = 0.0
    events: list[dict[str, Any]] = field(default_factory=list)
    started_at: str = ""
    last_tx_at: str = ""
    last_update: str = ""

    def emit(self, event_type: str, message: str, data: dict[str, Any] | None = None) -> None:
        entry = {
            "type": event_type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
        }
        self.events.append(entry)
        if len(self.events) > 200:
            self.events = self.events[-200:]
        self.last_update = entry["timestamp"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "halt_reason": self.halt_reason,
            "wallet_address": self.wallet_address,
            "eth_balance": self.eth_balance,
            "usdc_balance": self.usdc_balance,
            "portfolio_value_usd": self.portfolio_value_usd,
            "total_transactions": self.total_transactions,
            "transactions_today": self.transactions_today,
            "unique_protocols": list(self.unique_protocols),
            "unique_tokens": list(self.unique_tokens),
            "airdrop_score": round(self.airdrop_score, 2),
            "activity_score": round(self.activity_score, 4),
            "diversity_score": round(self.diversity_score, 4),
            "consistency_score": round(self.consistency_score, 4),
            "gas_spent_today_usd": round(self.gas_spent_today_usd, 4),
            "gas_spent_total_usd": round(self.gas_spent_total_usd, 4),
            "started_at": self.started_at,
            "last_tx_at": self.last_tx_at,
            "last_update": self.last_update,
        }
