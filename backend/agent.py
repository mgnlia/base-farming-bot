"""Main agent loop: orchestrates all Base farming strategies."""
import asyncio
import time
from collections import deque
from datetime import date

from backend.config import settings
from backend.risk import RiskManager
from backend.strategies.activity_scheduler import ActivityScheduler
from backend.strategies.bridge_activity import BridgeActivityStrategy
from backend.strategies.defi_rotation import DeFiRotationStrategy
from backend.strategies.nft_minter import NFTMinterStrategy


class BaseFarmingAgent:
    """Orchestrates DeFi rotation, NFT minting, and bridge activity on Base L2."""

    def __init__(self):
        self.risk = RiskManager(
            max_position_pct=settings.MAX_POSITION_PCT,
            max_drawdown_pct=settings.MAX_DRAWDOWN_PCT,
            kelly_fraction=settings.KELLY_FRACTION,
            daily_loss_cap_usd=settings.DAILY_LOSS_CAP_USD,
        )
        self.defi = DeFiRotationStrategy()
        self.nft = NFTMinterStrategy()
        self.bridge = BridgeActivityStrategy()
        self.scheduler = ActivityScheduler(
            max_tx_per_hour=4,
            max_tx_per_day=settings.MAX_TRADES_PER_DAY,
        )

        self.portfolio_value: float = settings.INITIAL_PORTFOLIO_VALUE
        self.cash: float = settings.INITIAL_PORTFOLIO_VALUE
        self.realized_pnl: float = 0.0
        self.status: str = "stopped"
        self.started_at: float | None = None

        # Bounded event log — deque never invalidates SSE iterators
        self.events: deque[dict] = deque(maxlen=500)

        self._task: asyncio.Task | None = None
        self._event_callbacks: list = []
        self._current_day: date = date.today()
        self._trade_count_today: int = 0
        self._daily_loss_today: float = 0.0

    def _check_daily_reset(self) -> None:
        today = date.today()
        if today != self._current_day:
            self._current_day = today
            self._trade_count_today = 0
            self._daily_loss_today = 0.0
            self.risk.check_daily_reset()

    def add_event_callback(self, cb) -> None:
        self._event_callbacks.append(cb)

    def remove_event_callback(self, cb) -> None:
        if cb in self._event_callbacks:
            self._event_callbacks.remove(cb)

    async def _emit(self, event: dict) -> None:
        self.events.append(event)
        for cb in list(self._event_callbacks):
            try:
                await cb(event)
            except Exception:
                pass

    async def _run_loop(self) -> None:
        self.status = "running"
        self.started_at = time.time()
        self.risk.peak_value = self.portfolio_value

        await self._emit({"type": "agent_started", "portfolio_value": self.portfolio_value, "timestamp": time.time()})

        while self.status == "running":
            try:
                self._check_daily_reset()

                # Drawdown circuit breaker
                if not self.risk.update_drawdown(self.portfolio_value):
                    await self._emit({"type": "risk_halt", "reason": "drawdown", "drawdown": self.risk.current_drawdown, "timestamp": time.time()})
                    self.status = "halted"
                    break

                # Daily loss cap
                if self._daily_loss_today <= -settings.DAILY_LOSS_CAP_USD:
                    await self._emit({"type": "risk_halt", "reason": "daily_loss_cap", "daily_loss": self._daily_loss_today, "timestamp": time.time()})
                    self.status = "halted"
                    break

                # Anti-sybil scheduler gate
                can_act = self.scheduler.can_execute()

                if can_act:
                    # DeFi rotation
                    for event in self.defi.execute(self.cash * 0.6):
                        if event.get("type") in ("swap", "defi_deposit"):
                            self.scheduler.record_tx()
                            self._trade_count_today += 1
                        await self._emit(event)

                    # NFT minting
                    for event in self.nft.execute():
                        self.scheduler.record_tx()
                        self._trade_count_today += 1
                        await self._emit(event)

                    # Bridge activity
                    for event in self.bridge.execute(self.cash * 0.15):
                        if event.get("type") == "bridge_initiated":
                            self.scheduler.record_tx()
                            self._trade_count_today += 1
                        await self._emit(event)

                # Update portfolio
                defi_earned = self.defi.get_total_earned()
                self.portfolio_value = self.cash + defi_earned

                await self._emit({
                    "type": "status_update",
                    "portfolio_value": round(self.portfolio_value, 2),
                    "realized_pnl": round(self.realized_pnl, 2),
                    "defi_earned": round(defi_earned, 4),
                    "protocol_coverage": self.defi.get_protocol_coverage(),
                    "nft_count": self.nft.get_mint_count(),
                    "bridge_score": round(self.bridge.get_bridge_score(), 1),
                    "nft_score": round(self.nft.get_nft_score(), 1),
                    "trade_count_today": self._trade_count_today,
                    "scheduler": self.scheduler.get_stats(),
                    "timestamp": time.time(),
                })

                await asyncio.sleep(settings.AGENT_LOOP_INTERVAL)

            except asyncio.CancelledError:
                break
            except Exception as e:
                await self._emit({"type": "error", "message": str(e), "timestamp": time.time()})
                await asyncio.sleep(settings.AGENT_LOOP_INTERVAL)

    async def start(self) -> dict:
        if self.status == "running":
            return {"status": "already_running"}
        self._task = asyncio.create_task(self._run_loop())
        return {"status": "started"}

    async def stop(self) -> dict:
        self.status = "stopped"
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        return {"status": "stopped"}

    async def resume(self) -> dict:
        if self.status == "halted":
            self.risk.peak_value = self.portfolio_value
            self.risk.current_drawdown = 0.0
        return await self.start()

    def get_status(self) -> dict:
        return {
            "status": self.status,
            "simulation_mode": settings.SIMULATION_MODE,
            "portfolio_value": round(self.portfolio_value, 2),
            "cash": round(self.cash, 2),
            "realized_pnl": round(self.realized_pnl, 2),
            "defi_earned": round(self.defi.get_total_earned(), 4),
            "protocol_coverage": self.defi.get_protocol_coverage(),
            "nft_count": self.nft.get_mint_count(),
            "nft_score": round(self.nft.get_nft_score(), 1),
            "bridge_score": round(self.bridge.get_bridge_score(), 1),
            "trade_count_today": self._trade_count_today,
            "daily_loss_today": round(self._daily_loss_today, 2),
            "risk_metrics": self.risk.get_metrics(),
            "scheduler": self.scheduler.get_stats(),
            "started_at": self.started_at,
        }


agent = BaseFarmingAgent()
