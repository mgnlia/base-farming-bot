"""Bridge activity strategy: Base Bridge + cross-chain for on-chain footprint."""
import random
import time
from dataclasses import dataclass, field


BRIDGES = [
    {"name": "Base Bridge (Official)", "from_chain": "Ethereum", "to_chain": "Base", "avg_time_s": 180},
    {"name": "Base Bridge (Official)", "from_chain": "Base", "to_chain": "Ethereum", "avg_time_s": 604800},
    {"name": "Across Protocol", "from_chain": "Ethereum", "to_chain": "Base", "avg_time_s": 60},
    {"name": "Across Protocol", "from_chain": "Base", "to_chain": "Optimism", "avg_time_s": 60},
    {"name": "Stargate", "from_chain": "Arbitrum", "to_chain": "Base", "avg_time_s": 120},
    {"name": "Hop Protocol", "from_chain": "Base", "to_chain": "Polygon", "avg_time_s": 90},
    {"name": "Synapse", "from_chain": "Base", "to_chain": "BNB Chain", "avg_time_s": 150},
]

TOKENS = ["ETH", "USDC", "USDT", "DAI", "cbETH"]


@dataclass
class BridgeTx:
    bridge: str
    from_chain: str
    to_chain: str
    token: str
    amount_usd: float
    status: str  # pending | completed
    initiated_at: float = field(default_factory=time.time)
    completed_at: float | None = None

    def to_dict(self) -> dict:
        return {
            "bridge": self.bridge,
            "from_chain": self.from_chain,
            "to_chain": self.to_chain,
            "token": self.token,
            "amount_usd": round(self.amount_usd, 2),
            "status": self.status,
            "initiated_at": self.initiated_at,
            "completed_at": self.completed_at,
        }


class BridgeActivityStrategy:
    """Simulates cross-chain bridge activity for Base ecosystem footprint."""

    def __init__(self):
        self.transactions: list[BridgeTx] = []
        self.total_volume_usd: float = 0.0

    def execute(self, available_capital: float) -> list[dict]:
        events: list[dict] = []

        # Complete pending txns
        now = time.time()
        for tx in self.transactions:
            if tx.status == "pending":
                bridge_cfg = next((b for b in BRIDGES if b["name"] == tx.bridge), None)
                if bridge_cfg:
                    elapsed = now - tx.initiated_at
                    if elapsed >= bridge_cfg["avg_time_s"] * 0.1:  # sim: 10% of real time
                        tx.status = "completed"
                        tx.completed_at = now
                        events.append({
                            "type": "bridge_completed",
                            "bridge": tx.bridge,
                            "from_chain": tx.from_chain,
                            "to_chain": tx.to_chain,
                            "token": tx.token,
                            "amount_usd": tx.amount_usd,
                            "timestamp": now,
                        })

        # Initiate new bridge tx (randomized cadence)
        pending = sum(1 for t in self.transactions if t.status == "pending")
        if pending < 2 and random.random() < 0.08 and available_capital > 50:
            bridge_cfg = random.choice(BRIDGES)
            token = random.choice(TOKENS)
            amount = available_capital * random.uniform(0.03, 0.12)
            tx = BridgeTx(
                bridge=bridge_cfg["name"],
                from_chain=bridge_cfg["from_chain"],
                to_chain=bridge_cfg["to_chain"],
                token=token,
                amount_usd=amount,
                status="pending",
            )
            self.transactions.append(tx)
            self.total_volume_usd += amount
            events.append({
                "type": "bridge_initiated",
                "bridge": tx.bridge,
                "from_chain": tx.from_chain,
                "to_chain": tx.to_chain,
                "token": token,
                "amount_usd": round(amount, 2),
                "simulated": True,
                "timestamp": now,
            })

        return events

    def get_transactions(self, limit: int = 30) -> list[dict]:
        return [t.to_dict() for t in self.transactions[-limit:]]

    def get_bridge_score(self) -> float:
        completed = [t for t in self.transactions if t.status == "completed"]
        chains = len({t.to_chain for t in completed} | {t.from_chain for t in completed})
        bridges = len({t.bridge for t in completed})
        return min(100.0, len(completed) * 5 + chains * 8 + bridges * 10)
