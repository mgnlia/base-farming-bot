"""Risk management: Kelly sizing, drawdown circuit breaker, daily loss cap."""
from datetime import date


class RiskManager:
    def __init__(
        self,
        max_position_pct: float = 0.20,
        max_drawdown_pct: float = 0.15,
        kelly_fraction: float = 0.4,
        daily_loss_cap_usd: float = 300.0,
    ):
        self.max_position_pct = max_position_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.kelly_fraction = kelly_fraction
        self.daily_loss_cap_usd = daily_loss_cap_usd

        self.peak_value: float = 0.0
        self.current_drawdown: float = 0.0
        self.daily_loss_usd: float = 0.0
        self._current_day: date = date.today()

    def kelly_size(self, win_prob: float, win_loss_ratio: float) -> float:
        """Kelly criterion position size capped at max_position_pct."""
        if win_prob <= 0 or win_loss_ratio <= 0:
            return 0.0
        kelly = win_prob - (1 - win_prob) / win_loss_ratio
        kelly = max(0.0, kelly) * self.kelly_fraction
        return min(kelly, self.max_position_pct)

    def update_drawdown(self, portfolio_value: float) -> bool:
        """Returns True if within drawdown limit."""
        if portfolio_value > self.peak_value:
            self.peak_value = portfolio_value
        if self.peak_value > 0:
            self.current_drawdown = (self.peak_value - portfolio_value) / self.peak_value
        return self.current_drawdown < self.max_drawdown_pct

    def record_loss(self, loss_usd: float) -> bool:
        """Record realized loss. Returns True if still within daily cap."""
        if loss_usd < 0:
            self.daily_loss_usd += loss_usd
        return self.daily_loss_usd > -self.daily_loss_cap_usd

    def check_daily_reset(self) -> bool:
        """Reset daily counters at midnight. Returns True if reset occurred."""
        today = date.today()
        if today != self._current_day:
            self._current_day = today
            self.daily_loss_usd = 0.0
            return True
        return False

    def is_halted(self) -> bool:
        return self.current_drawdown >= self.max_drawdown_pct

    def get_metrics(self) -> dict:
        return {
            "peak_value": round(self.peak_value, 2),
            "current_drawdown": round(self.current_drawdown, 4),
            "max_drawdown_pct": self.max_drawdown_pct,
            "max_position_pct": self.max_position_pct,
            "daily_loss_usd": round(self.daily_loss_usd, 2),
            "daily_loss_cap_usd": self.daily_loss_cap_usd,
            "is_halted": self.is_halted(),
        }
