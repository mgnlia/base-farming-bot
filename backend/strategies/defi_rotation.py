"""DeFi rotation strategy: swaps, lending, LP across Base protocols."""
import random
import time
from dataclasses import dataclass, field


PROTOCOLS = [
    {"name": "Aerodrome", "type": "dex", "base_apy": 0.42, "apy_vol": 0.12, "weight": 0.20},
    {"name": "Uniswap v3", "type": "dex", "base_apy": 0.28, "apy_vol": 0.08, "weight": 0.18},
    {"name": "Aave v3", "type": "lending", "base_apy": 0.09, "apy_vol": 0.02, "weight": 0.15},
    {"name": "Compound v3", "type": "lending", "base_apy": 0.07, "apy_vol": 0.02, "weight": 0.12},
    {"name": "Morpho", "type": "lending", "base_apy": 0.13, "apy_vol": 0.03, "weight": 0.12},
    {"name": "Moonwell", "type": "lending", "base_apy": 0.11, "apy_vol": 0.03, "weight": 0.10},
    {"name": "BaseSwap", "type": "dex", "base_apy": 0.35, "apy_vol": 0.10, "weight": 0.08},
    {"name": "SushiSwap", "type": "dex", "base_apy": 0.22, "apy_vol": 0.07, "weight": 0.05},
]

PAIRS = ["ETH/USDC", "USDC/cbETH", "ETH/AERO", "USDC/DAI", "cbETH/ETH", "WBTC/ETH"]


@dataclass
class DeFiPosition:
    protocol: str
    pool: str
    position_type: str  # swap | lend | lp
    deposited: float
    apy: float
    earned: float = 0.0
    tx_count: int = 0
    opened_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "protocol": self.protocol,
            "pool": self.pool,
            "position_type": self.position_type,
            "deposited": round(self.deposited, 2),
            "apy": round(self.apy, 4),
            "earned": round(self.earned, 4),
            "tx_count": self.tx_count,
            "opened_at": self.opened_at,
        }


class DeFiRotationStrategy:
    """Rotates capital across 8+ Base DeFi protocols for maximum footprint."""

    def __init__(self):
        self.positions: list[DeFiPosition] = []
        self.total_earned: float = 0.0
        self.swap_count: int = 0
        self.protocol_coverage: set[str] = set()

    def _apy(self, proto: dict) -> float:
        return max(0.01, proto["base_apy"] + random.gauss(0, proto["apy_vol"]))

    def execute(self, available_capital: float) -> list[dict]:
        events: list[dict] = []

        # Accrue yields on existing positions
        for pos in self.positions:
            elapsed = 6.0 / (365 * 24 * 3600)
            earned = pos.deposited * pos.apy * elapsed
            pos.earned += earned
            self.total_earned += earned

        # Opportunistic swap (anti-sybil: randomized, not every tick)
        if random.random() < 0.35:
            pair = random.choice(PAIRS)
            proto = random.choice([p for p in PROTOCOLS if p["type"] == "dex"])
            amount = available_capital * random.uniform(0.02, 0.08)
            self.swap_count += 1
            self.protocol_coverage.add(proto["name"])
            events.append({
                "type": "swap",
                "protocol": proto["name"],
                "pair": pair,
                "amount_usd": round(amount, 2),
                "simulated": True,
                "timestamp": time.time(),
            })

        # Open new position if under-deployed
        if len(self.positions) < 6 and available_capital > 200 and random.random() < 0.25:
            proto = random.choice(PROTOCOLS)
            existing = {p.protocol for p in self.positions}
            # Prefer uncovered protocols for diversity
            uncovered = [p for p in PROTOCOLS if p["name"] not in existing]
            if uncovered:
                proto = random.choice(uncovered)
            deposit = available_capital * random.uniform(0.08, 0.18)
            apy = self._apy(proto)
            pos_type = "lp" if proto["type"] == "dex" else "lend"
            pool = random.choice(PAIRS) if pos_type == "lp" else f"{random.choice(['USDC','ETH','cbETH'])} Pool"
            pos = DeFiPosition(
                protocol=proto["name"],
                pool=pool,
                position_type=pos_type,
                deposited=deposit,
                apy=apy,
            )
            self.positions.append(pos)
            self.protocol_coverage.add(proto["name"])
            events.append({
                "type": "defi_deposit",
                "protocol": proto["name"],
                "pool": pool,
                "position_type": pos_type,
                "amount": round(deposit, 2),
                "apy": round(apy, 4),
                "timestamp": time.time(),
            })

        # Rotate worst-performing position (rebalance)
        if len(self.positions) >= 3 and random.random() < 0.06:
            worst = min(self.positions, key=lambda p: p.apy)
            if worst.apy < 0.04:
                events.append({
                    "type": "defi_withdraw",
                    "protocol": worst.protocol,
                    "pool": worst.pool,
                    "earned": round(worst.earned, 4),
                    "timestamp": time.time(),
                })
                self.positions.remove(worst)

        return events

    def get_positions(self) -> list[dict]:
        return [p.to_dict() for p in self.positions]

    def get_total_earned(self) -> float:
        return self.total_earned

    def get_protocol_coverage(self) -> int:
        return len(self.protocol_coverage)
