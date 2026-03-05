"""Activity Scheduler — anti-sybil randomised timing.

Spreads transactions across the day with human-like gaps (30-180 min).
Rotates through strategies: DeFi rotation, NFT minting, bridge activity.
"""
from __future__ import annotations
import asyncio, logging, random
from datetime import datetime, timezone
from config import settings
from state import FarmingState
from risk import RiskManager
from base_client import BaseClient
from strategies.defi_rotation import DeFiRotationStrategy
from strategies.nft_minter import NFTMintingStrategy
from strategies.bridge_activity import BridgeActivityStrategy

logger = logging.getLogger(__name__)

class ActivityScheduler:
    def __init__(self, state: FarmingState, risk: RiskManager, client: BaseClient) -> None:
        self.state = state
        self.risk = risk
        self.client = client
        self._defi = DeFiRotationStrategy(client=client)
        self._nft = NFTMintingStrategy(client=client)
        self._bridge = BridgeActivityStrategy(client=client)
        self._running = False
        self._task: asyncio.Task | None = None
        # Strategy weights — DeFi most frequent, bridge least
        self._strategies = [
            ("defi", 0.6, self._defi),
            ("nft", 0.3, self._nft),
            ("bridge", 0.1, self._bridge),
        ]

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("Scheduler started")

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Scheduler stopped")

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Scheduler error: %s", e)
            await asyncio.sleep(settings.scheduler_interval_seconds)

    async def _tick(self) -> None:
        wallet = settings.wallet_address
        if not wallet:
            return

        # Update balances
        try:
            eth = await self.client.get_eth_balance(wallet)
            usdc = await self.client.get_token_balance(settings.usdc_address, wallet)
            eth_price = await self.client.get_token_price_usd(settings.weth_address)
            self.state.eth_balance = eth
            self.state.usdc_balance = usdc
            self.state.portfolio_value_usd = eth * eth_price + usdc
        except Exception as e:
            logger.warning("Balance update failed: %s", e)

        # Check risk — can we transact?
        ok, reason = self.risk.can_transact(estimated_gas_usd=0.001)
        if not ok:
            self.state.status = "waiting"
            self.state.emit("info", f"Waiting: {reason}")
            self._update_score()
            return

        self.state.status = "running"

        # Pick strategy by weight
        r = random.random()
        cumulative = 0.0
        chosen_name, chosen_strategy = "defi", self._defi
        for name, weight, strategy in self._strategies:
            cumulative += weight
            if r < cumulative:
                chosen_name, chosen_strategy = name, strategy
                break

        # Execute
        result = await chosen_strategy.execute(wallet)
        if result and result.get("success"):
            gas_usd = result.get("gas_usd", 0.0)
            self.risk.record_transaction(gas_usd)
            self.state.total_transactions += 1
            self.state.transactions_today += 1
            self.state.gas_spent_today_usd = self.risk.gas_spent_today_usd
            self.state.gas_spent_total_usd += gas_usd
            self.state.last_tx_at = datetime.now(timezone.utc).isoformat()
            self.state.unique_protocols.add(result.get("protocol", chosen_name))
            self.state.emit("tx", f"[{chosen_name.upper()}] {result.get('action','tx')} ✓", result)
            logger.info("Tx executed: %s protocol=%s", chosen_name, result.get("protocol"))

        self._update_score()

    def _update_score(self) -> None:
        s = self.state
        # Activity score: txns relative to daily target
        s.activity_score = min(1.0, s.transactions_today / max(settings.daily_tx_target, 1))
        # Diversity score: unique protocols / total available
        s.diversity_score = min(1.0, len(s.unique_protocols) / 6.0)
        # Consistency score: days active (proxy via total txns)
        s.consistency_score = min(1.0, s.total_transactions / 100.0)
        # Composite airdrop score (0-100)
        s.airdrop_score = round(
            (s.activity_score * 0.4 + s.diversity_score * 0.4 + s.consistency_score * 0.2) * 100, 2
        )
