from __future__ import annotations

import time
from collections.abc import Generator

import allure
import pytest

from sportyqa import config
from sportyqa.api_client import ApiClient, ApiError


@pytest.fixture(scope="session")
def api() -> ApiClient:
    """A requests-based client authenticated for the QA user."""
    return ApiClient(
        base_url=config.API_BASE_URL,
        user_id=config.QA_USER_ID,
        timeout=config.API_TIMEOUT_SECONDS,
    )


@pytest.fixture(scope="function")
def clean_account(api: ApiClient) -> Generator[None, None, None]:
    """Normalise the account to a known balance before a test, then tidy up."""
    with allure.step("Reset account to a known clean state"):
        api.reset_balance()
    time.sleep(config.SETTLE_SECONDS)  # wait for the persisted balance to settle
    yield
    with allure.step("Tidy-up: reset account"):
        try:
            api.reset_balance()
        except ApiError as exc:  # best-effort: don't fail the test on cleanup
            print(f"[conftest] tidy-up reset skipped: {exc}")


@pytest.fixture(scope="function")
def driver() -> Generator[None, None, None]:
    """Headless Chrome via Selenium Manager (yields, quits after test)."""
    from sportyqa.webdriver import new_driver

    drv = new_driver()
    yield drv
    drv.quit()
