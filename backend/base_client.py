"""Base L2 client — real and simulation modes."""
from __future__ import annotations
import asyncio, logging, random
from typing import Any
from config import settings

logger = logging.getLogger(__name__)

class BaseClient:
    def __init__(self) -> None:
        self._sim_prices: dict[str, float] = {
            settings.weth_address: 1800.0,
            settings.usdc_address: 1.0,
            settings.cbeth_address: 1900.0,
            settings.aero_address: 1.2,
        }
        self._sim_nonce = random.randint(50, 500)

    def _tx(self) -> str:
        return "0x" + "".join(random.choices("0123456789abcdef", k=64))

    async def get_token_price_usd(self, token: str) -> float:
        if settings.simulation_mode:
            base = self._sim_prices.get(token, 1.0)
            self._sim_prices[token] = base * (1 + random.gauss(0, 0.003))
            return self._sim_prices[token]
        raise NotImplementedError("Set SIMULATION_MODE=true")

    async def get_eth_balance(self, address: str) -> float:
        if settings.simulation_mode:
            return round(random.uniform(0.05, 0.5), 6)
        raise NotImplementedError

    async def get_token_balance(self, token: str, wallet: str) -> float:
        if settings.simulation_mode:
            return round(random.uniform(10, 500), 2)
        raise NotImplementedError

    async def get_gas_price_gwei(self) -> float:
        if settings.simulation_mode:
            return round(random.uniform(0.001, 0.05), 4)
        raise NotImplementedError

    async def _gas_usd(self, units: int = 200_000) -> float:
        gwei = await self.get_gas_price_gwei()
        eth_price = await self.get_token_price_usd(settings.weth_address)
        return gwei * units * 1e-9 * eth_price

    async def swap_aerodrome(self, from_token: str, to_token: str, amount_usd: float, wallet: str) -> dict[str, Any]:
        gas = await self._gas_usd(250_000)
        await asyncio.sleep(random.uniform(0.05, 0.2))
        self._sim_nonce += 1
        return {"success": True, "protocol": "aerodrome", "action": "swap", "from_token": from_token, "to_token": to_token, "amount_usd": amount_usd, "tx_hash": self._tx(), "gas_usd": gas}

    async def swap_uniswap_v3(self, from_token: str, to_token: str, amount_usd: float, wallet: str) -> dict[str, Any]:
        gas = await self._gas_usd(200_000)
        await asyncio.sleep(random.uniform(0.05, 0.2))
        self._sim_nonce += 1
        return {"success": True, "protocol": "uniswap_v3", "action": "swap", "from_token": from_token, "to_token": to_token, "amount_usd": amount_usd, "tx_hash": self._tx(), "gas_usd": gas}

    async def supply_aave(self, token: str, amount_usd: float, wallet: str) -> dict[str, Any]:
        gas = await self._gas_usd(300_000)
        await asyncio.sleep(random.uniform(0.05, 0.2))
        self._sim_nonce += 1
        return {"success": True, "protocol": "aave_v3", "action": "supply", "token": token, "amount_usd": amount_usd, "tx_hash": self._tx(), "gas_usd": gas}

    async def supply_morpho(self, token: str, amount_usd: float, wallet: str) -> dict[str, Any]:
        gas = await self._gas_usd(280_000)
        await asyncio.sleep(random.uniform(0.05, 0.2))
        self._sim_nonce += 1
        return {"success": True, "protocol": "morpho", "action": "supply", "token": token, "amount_usd": amount_usd, "tx_hash": self._tx(), "gas_usd": gas}

    async def mint_zora(self, collection: str, wallet: str) -> dict[str, Any]:
        gas = await self._gas_usd(150_000)
        await asyncio.sleep(random.uniform(0.05, 0.2))
        self._sim_nonce += 1
        return {"success": True, "protocol": "zora", "action": "mint", "collection": collection, "token_id": random.randint(1, 10000), "tx_hash": self._tx(), "gas_usd": gas}

    async def bridge_to_base(self, amount_eth: float, wallet: str) -> dict[str, Any]:
        gas = await self._gas_usd(100_000)
        await asyncio.sleep(random.uniform(0.05, 0.2))
        self._sim_nonce += 1
        return {"success": True, "protocol": "base_bridge", "action": "bridge", "amount_eth": amount_eth, "tx_hash": self._tx(), "gas_usd": gas}

    async def add_lp_aerodrome(self, token_a: str, token_b: str, amount_usd: float, wallet: str) -> dict[str, Any]:
        gas = await self._gas_usd(350_000)
        await asyncio.sleep(random.uniform(0.05, 0.2))
        self._sim_nonce += 1
        return {"success": True, "protocol": "aerodrome", "action": "add_liquidity", "token_a": token_a, "token_b": token_b, "amount_usd": amount_usd, "lp_tokens": round(amount_usd / 2, 6), "tx_hash": self._tx(), "gas_usd": gas}
