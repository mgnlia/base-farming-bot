"""Unit tests for Base Farming Bot."""
from fastapi.testclient import TestClient

from backend.risk import RiskManager
from backend.strategies.defi_rotation import DeFiRotationStrategy
from backend.strategies.nft_minter import NFTMinterStrategy
from backend.strategies.bridge_activity import BridgeActivityStrategy
from backend.strategies.activity_scheduler import ActivityScheduler
from backend.main import app


client = TestClient(app)


# ─── RiskManager ───────────────────────────────────────────────────────────────

def test_kelly_size_normal():
    rm = RiskManager()
    size = rm.kelly_size(0.6, 2.0)
    assert 0 < size <= rm.max_position_pct


def test_kelly_size_zero_prob():
    rm = RiskManager()
    assert rm.kelly_size(0, 2.0) == 0.0


def test_kelly_size_capped():
    rm = RiskManager(max_position_pct=0.10)
    size = rm.kelly_size(0.99, 100.0)
    assert size <= 0.10


def test_drawdown_halt():
    rm = RiskManager(max_drawdown_pct=0.10)
    rm.update_drawdown(10000)
    within = rm.update_drawdown(8900)  # 11% drawdown
    assert within is False
    assert rm.is_halted()


def test_drawdown_ok():
    rm = RiskManager(max_drawdown_pct=0.15)
    rm.update_drawdown(10000)
    within = rm.update_drawdown(9000)  # 10% drawdown
    assert within is True


def test_daily_loss_cap():
    rm = RiskManager(daily_loss_cap_usd=100.0)
    ok = rm.record_loss(-50.0)
    assert ok is True
    ok2 = rm.record_loss(-60.0)
    assert ok2 is False


def test_daily_reset():
    rm = RiskManager()
    rm.daily_loss_usd = -200.0
    from unittest.mock import patch
    from datetime import date

    future_date = date(2099, 1, 2)
    with patch("backend.risk.date") as mock_date:
        mock_date.today.return_value = future_date
        reset = rm.check_daily_reset()
    assert reset is True
    assert rm.daily_loss_usd == 0.0


def test_metrics_keys():
    rm = RiskManager()
    m = rm.get_metrics()
    for key in ("peak_value", "current_drawdown", "max_drawdown_pct", "is_halted", "daily_loss_usd"):
        assert key in m


# ─── DeFiRotation ──────────────────────────────────────────────────────────────

def test_defi_execute_returns_list():
    s = DeFiRotationStrategy()
    events = s.execute(5000.0)
    assert isinstance(events, list)


def test_defi_positions_format():
    s = DeFiRotationStrategy()
    for _ in range(20):
        s.execute(5000.0)
    positions = s.get_positions()
    assert isinstance(positions, list)
    for p in positions:
        assert "protocol" in p
        assert "deposited" in p


# ─── NFTMinter ─────────────────────────────────────────────────────────────────

def test_nft_execute_returns_list():
    s = NFTMinterStrategy()
    events = s.execute()
    assert isinstance(events, list)


def test_nft_score_non_negative():
    s = NFTMinterStrategy()
    for _ in range(50):
        s.execute()
    assert s.get_nft_score() >= 0.0


# ─── BridgeActivity ────────────────────────────────────────────────────────────

def test_bridge_execute_returns_list():
    s = BridgeActivityStrategy()
    events = s.execute(5000.0)
    assert isinstance(events, list)


def test_bridge_score_non_negative():
    s = BridgeActivityStrategy()
    assert s.get_bridge_score() >= 0.0


# ─── ActivityScheduler ─────────────────────────────────────────────────────────

def test_scheduler_can_execute():
    s = ActivityScheduler()
    result = s.can_execute()
    assert isinstance(result, bool)


def test_scheduler_cooldown():
    s = ActivityScheduler()
    s.set_cooldown(9999)
    assert s.can_execute() is False


def test_scheduler_stats_keys():
    s = ActivityScheduler()
    stats = s.get_stats()
    for key in ("total_tx", "tx_last_hour", "tx_today", "days_active"):
        assert key in stats


# ─── API endpoints ─────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_status_no_auth_required_when_key_empty():
    r = client.get("/api/status")
    assert r.status_code == 200
    data = r.json()
    assert "portfolio_value" in data
    assert "risk_metrics" in data


def test_positions_endpoint():
    r = client.get("/api/positions")
    assert r.status_code == 200
    data = r.json()
    assert "defi_positions" in data
    assert "nft_mints" in data
    assert "bridge_transactions" in data


def test_events_endpoint():
    r = client.get("/api/events")
    assert r.status_code == 200
    assert "events" in r.json()


def test_scheduler_endpoint():
    r = client.get("/api/scheduler")
    assert r.status_code == 200


def test_auth_enforced_when_key_set(monkeypatch):
    import backend.config as cfg
    monkeypatch.setattr(cfg.settings, "BOT_API_KEY", "secret123")
    r = client.get("/api/status", headers={"X-API-Key": "wrong"})
    assert r.status_code == 401


def test_auth_passes_with_correct_key(monkeypatch):
    import backend.config as cfg
    monkeypatch.setattr(cfg.settings, "BOT_API_KEY", "secret123")
    r = client.get("/api/status", headers={"X-API-Key": "secret123"})
    assert r.status_code == 200
