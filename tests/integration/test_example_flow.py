# tests/integration/test_example_flow.py
#
# Integration tests — full-stack end-to-end flows
# ต้องรัน BE + FE พร้อมกัน (docker compose up)
# รัน: pytest tests/integration -v  หรือ  pytest -m integration

import pytest


@pytest.mark.integration
@pytest.mark.skip(reason="Placeholder — implement after BE/FE features are ready")
def test_placeholder_auth_flow():
    """
    TC-INT-AUTH-01: Login flow end-to-end
    1. POST /auth/login → temp token
    2. POST /auth/pin → JWT
    3. Playwright: navigate / → redirect /dashboard
    """
    pass
