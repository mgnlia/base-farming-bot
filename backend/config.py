"""Configuration for Base L2 Airdrop Farming Bot."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SIMULATION_MODE: bool = True
    BASE_RPC_URL: str = "https://mainnet.base.org"
    WALLET_ADDRESS: str = ""
    WALLET_PRIVATE_KEY: str = ""
    BOT_API_KEY: str = ""

    # Portfolio
    INITIAL_PORTFOLIO_VALUE: float = 10000.0
    MAX_POSITION_PCT: float = 0.20
    MAX_DRAWDOWN_PCT: float = 0.15
    DAILY_LOSS_CAP_USD: float = 300.0
    MAX_TRADES_PER_DAY: int = 20

    # Agent
    AGENT_LOOP_INTERVAL: float = 6.0
    KELLY_FRACTION: float = 0.4

    # Token addresses on Base mainnet
    usdc_address: str = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    weth_address: str = "0x4200000000000000000000000000000000000006"
    cbeth_address: str = "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22"
    aero_address: str = "0x940181a94A35A4569E4529A3CDfB74e38FD98631"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}


settings = Settings()
