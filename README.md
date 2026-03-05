# Base Farming Bot 🔵

Automated Base L2 airdrop farming bot — DeFi rotation, NFT minting, bridge activity.

## Architecture

```
base-farming-bot/
├── backend/               # FastAPI backend (Python/uv)
│   ├── main.py            # FastAPI app, auth, SSE stream
│   ├── agent.py           # Main agent loop
│   ├── config.py          # Settings via pydantic-settings
│   ├── risk.py            # RiskManager: Kelly, drawdown, daily loss cap
│   └── strategies/
│       ├── defi_rotation.py      # Aerodrome, Uniswap, Aave, Compound, Morpho...
│       ├── nft_minter.py         # Zora, OpenSea Base mints
│       ├── bridge_activity.py    # Base Bridge, Across, Stargate, Hop
│       └── activity_scheduler.py # Anti-sybil timing
├── frontend/              # Next.js 14 + Tailwind dashboard
│   └── src/app/page.tsx   # Live dashboard: scores, events, risk metrics
├── Dockerfile
└── .env.example
```

## Quick Start

### Backend
```bash
cd backend
uv sync
uv run uvicorn backend.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## Configuration

Copy `.env.example` to `.env`:
```
SIMULATION_MODE=true        # Always start in sim mode
BASE_RPC_URL=https://mainnet.base.org
WALLET_ADDRESS=             # Your Base wallet
WALLET_PRIVATE_KEY=         # Private key (keep secret!)
BOT_API_KEY=                # API key for endpoints (empty = no auth)
MAX_DRAWDOWN_PCT=0.15       # 15% drawdown halts bot
DAILY_LOSS_CAP_USD=300.0    # $300/day loss cap
```

## Strategies

| Strategy | Protocols | Anti-sybil |
|---|---|---|
| DeFi Rotation | Aerodrome, Uniswap v3, Aave, Compound, Morpho, Moonwell, BaseSwap, SushiSwap | Randomized timing, rebalancing |
| NFT Minting | Zora Daily, Base Paint, Onchainsummer, Coinbase Verified ID, Base Name Service | Rarity-weighted, no burst minting |
| Bridge Activity | Base Bridge, Across, Stargate, Hop, Synapse | Max 2 pending, Poisson jitter |
| Activity Scheduler | All | Max 4/hour, 20/day, time-of-day weighting |

## Risk Management

- **Drawdown circuit breaker**: halts loop when drawdown ≥ `MAX_DRAWDOWN_PCT`
- **Daily loss cap**: halts loop when daily losses ≥ `DAILY_LOSS_CAP_USD`
- **Kelly sizing**: position sizes capped at `MAX_POSITION_PCT`
- **Daily reset**: counters reset at midnight

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Health check |
| GET | `/api/status` | Key | Agent status + risk metrics |
| POST | `/api/agent/start` | Key | Start agent |
| POST | `/api/agent/stop` | Key | Stop agent |
| POST | `/api/agent/resume` | Key | Resume after halt |
| GET | `/api/positions` | Key | All open positions |
| GET | `/api/events` | Key | Event history |
| GET | `/api/stream` | None | SSE live event stream |

## Disclaimer

SIMULATION MODE ONLY by default. Not financial advice.
