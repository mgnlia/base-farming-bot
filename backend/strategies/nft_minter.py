"""NFT minting strategy: Zora, OpenSea Base, free/cheap mints."""
import random
import time
from dataclasses import dataclass, field


NFT_COLLECTIONS = [
    {"name": "Zora Daily", "platform": "Zora", "mint_cost_eth": 0.000777, "rarity": "common"},
    {"name": "Base Paint", "platform": "Zora", "mint_cost_eth": 0.001, "rarity": "common"},
    {"name": "Onchainsummer", "platform": "Zora", "mint_cost_eth": 0.000777, "rarity": "rare"},
    {"name": "Base Introduced", "platform": "OpenSea", "mint_cost_eth": 0.0, "rarity": "common"},
    {"name": "Base God", "platform": "OpenSea", "mint_cost_eth": 0.001, "rarity": "uncommon"},
    {"name": "Bald", "platform": "OpenSea", "mint_cost_eth": 0.0, "rarity": "common"},
    {"name": "Coinbase Verified ID", "platform": "Base", "mint_cost_eth": 0.0, "rarity": "legendary"},
    {"name": "Base Name Service", "platform": "Base", "mint_cost_eth": 0.002, "rarity": "uncommon"},
]


@dataclass
class NFTMint:
    collection: str
    platform: str
    token_id: int
    cost_eth: float
    rarity: str
    minted_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "collection": self.collection,
            "platform": self.platform,
            "token_id": self.token_id,
            "cost_eth": self.cost_eth,
            "rarity": self.rarity,
            "minted_at": self.minted_at,
        }


class NFTMinterStrategy:
    """Mints NFTs on Zora and OpenSea Base for on-chain activity score."""

    def __init__(self):
        self.mints: list[NFTMint] = []
        self.total_spent_eth: float = 0.0
        self._token_counter: int = random.randint(1000, 9999)

    def execute(self) -> list[dict]:
        events: list[dict] = []

        # Mint with randomized cadence (anti-sybil: not every tick)
        if random.random() < 0.15:
            collection = random.choice(NFT_COLLECTIONS)
            # Skip if already minted this collection recently
            recent = [m.collection for m in self.mints[-5:]]
            if collection["name"] in recent and random.random() < 0.7:
                return events

            self._token_counter += random.randint(1, 50)
            mint = NFTMint(
                collection=collection["name"],
                platform=collection["platform"],
                token_id=self._token_counter,
                cost_eth=collection["mint_cost_eth"],
                rarity=collection["rarity"],
            )
            self.mints.append(mint)
            self.total_spent_eth += collection["mint_cost_eth"]
            events.append({
                "type": "nft_mint",
                "collection": mint.collection,
                "platform": mint.platform,
                "token_id": mint.token_id,
                "cost_eth": mint.cost_eth,
                "rarity": mint.rarity,
                "simulated": True,
                "timestamp": time.time(),
            })

        return events

    def get_mints(self) -> list[dict]:
        return [m.to_dict() for m in self.mints[-50:]]

    def get_mint_count(self) -> int:
        return len(self.mints)

    def get_nft_score(self) -> float:
        """Score based on diversity and rarity."""
        if not self.mints:
            return 0.0
        rarity_weights = {"common": 1, "uncommon": 3, "rare": 7, "legendary": 20}
        raw = sum(rarity_weights.get(m.rarity, 1) for m in self.mints)
        platforms = len({m.platform for m in self.mints})
        return min(100.0, raw * platforms * 0.5)
