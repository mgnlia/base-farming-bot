"""Activity scheduler: anti-sybil aware timing, spread txns across time."""
import random
import time
from collections import deque
from datetime import datetime


class ActivityScheduler:
    """
    Manages transaction timing to mimic authentic human behavior.
    Anti-sybil principles:
    - No burst transactions (max N per hour)
    - Randomized inter-tx delays (Poisson-distributed)
    - Time-of-day weighting (active during business hours)
    - Cooldown after consecutive failures
    """

    def __init__(self, max_tx_per_hour: int = 5, max_tx_per_day: int = 20):
        self.max_tx_per_hour = max_tx_per_hour
        self.max_tx_per_day = max_tx_per_day
        self.tx_log: deque[float] = deque(maxlen=500)  # timestamps
        self._cooldown_until: float = 0.0
        self.total_tx: int = 0
        self.days_active: set[str] = set()

    def can_execute(self) -> bool:
        """Returns True if a new transaction is allowed right now."""
        now = time.time()

        # Cooldown check
        if now < self._cooldown_until:
            return False

        # Hourly rate limit
        hour_ago = now - 3600
        tx_last_hour = sum(1 for t in self.tx_log if t > hour_ago)
        if tx_last_hour >= self.max_tx_per_hour:
            return False

        # Daily rate limit
        today = datetime.now().strftime("%Y-%m-%d")
        tx_today = sum(1 for t in self.tx_log if datetime.fromtimestamp(t).strftime("%Y-%m-%d") == today)
        if tx_today >= self.max_tx_per_day:
            return False

        # Simulate human time-of-day: less active at night (UTC)
        hour = datetime.utcnow().hour
        if hour < 6 or hour > 23:
            if random.random() < 0.7:  # 70% skip during night hours
                return False

        # Randomized Poisson-style jitter
        if self.tx_log and random.random() < 0.4:
            return False

        return True

    def record_tx(self) -> None:
        now = time.time()
        self.tx_log.append(now)
        self.total_tx += 1
        today = datetime.now().strftime("%Y-%m-%d")
        self.days_active.add(today)

    def set_cooldown(self, seconds: float) -> None:
        self._cooldown_until = time.time() + seconds

    def get_stats(self) -> dict:
        now = time.time()
        hour_ago = now - 3600
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            "total_tx": self.total_tx,
            "tx_last_hour": sum(1 for t in self.tx_log if t > hour_ago),
            "tx_today": sum(1 for t in self.tx_log if datetime.fromtimestamp(t).strftime("%Y-%m-%d") == today),
            "days_active": len(self.days_active),
            "in_cooldown": time.time() < self._cooldown_until,
            "consistency_score": min(100.0, len(self.days_active) * 10),
        }
