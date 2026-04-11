"""Minimal debug test to pinpoint fixture hang"""
import pytest
from httpx import AsyncClient, ASGITransport

from api.main import app
from api.database import get_db


@pytest.mark.be
async def test_with_real_fixtures(client, seed_data):
    """Test using the real conftest fixtures"""
    import allure
    print(f"\n[debug] seed partner={seed_data['partner'].id}")
    res = await client.get("/health")
    print(f"[debug] response: {res.status_code}")
    assert res.status_code == 200
    print("[debug] PASSED")
