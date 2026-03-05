"""NFT Minting Strategy — Zora and OpenSea Base free/cheap mints."""

import random
import asyncio
from datetime import datetime, timezone
from typing import Any

from config import settings

NFT_PLATFORMS = ["Zora", "OpenSea Base", "Sound.xyz", "Manifold"]
NFT_COLLECTIONS = [
    "Base Summer 2026",
    "Onchain Vibes",
    "Base OG Pass",
    "Creator Economy #1",
    "Base Ecosystem NFT",
    "Zora Daily Drop",
]


def _sim_mint(platform: str, collection: str, mint_price: float) -> dict[str, Any]:
    gas_cost = random.uniform(0.01, 0.05)
    return {
        "type": "nft_mint",
        "platform": platform,
        "collection": collection,
        "token_id": random.randint(1, 99999),
        "mint_price_eth": mint_price,
        "gas_cost_eth": gas_cost,
        "total_cost_eth": mint_price + gas_cost,
        "tx_hash": f"0x{''.join(random.choices('0123456789abcdef', k=64))}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "simulated": True,
    }


async def execute_nft_minting() -> list[dict[str, Any]]:
    """Mint free/cheap NFTs on Base to build creator economy footprint."""
    results = []

    if settings.simulation_mode:
        num_mints = random.randint(1, 3)
        for _ in range(num_mints):
            await asyncio.sleep(0.05)
            platform = random.choice(NFT_PLATFORMS)
            collection = random.choice(NFT_COLLECTIONS)
            # Mostly free mints, occasionally small price
            mint_price = 0.0 if random.random() < 0.7 else random.uniform(0.0001, 0.001)
            results.append(_sim_mint(platform, collection, mint_price))
    else:
        raise NotImplementedError("Live minting requires private key and funded wallet")

    return results


async def get_nft_holdings() -> list[dict[str, Any]]:
    """Return current NFT holdings."""
    if settings.simulation_mode:
        holdings = []
        for i in range(random.randint(3, 8)):
            holdings.append(
                {
                    "collection": random.choice(NFT_COLLECTIONS),
                    "platform": random.choice(NFT_PLATFORMS),
                    "token_id": random.randint(1, 99999),
                    "acquired_at": datetime.now(timezone.utc).isoformat(),
                    "estimated_value_eth": round(random.uniform(0, 0.01), 6),
                }
            )
        return holdings
    return []
