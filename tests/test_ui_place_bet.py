"""UI end-to-end happy path - place a single bet.

A user bets a stake on the UI and checks the success receipt and, without
refreshing, that the UI reflects the decreased funds.

Assertions are spec-driven (no refresh after betting, as a real user would not
refresh). The live build fails several of them:
  * BUG-08 - the receipt reverses the teams ("Lyon vs Monaco").
  * BUG-09 - the receipt payout (€20.00) is not stake x odds (€21.50).
  * BUG-10 - the header balance stays stale at €120.00 after the bet (should
             be €110.00).
"""

from __future__ import annotations

import allure
import pytest
from pytest_check import check

from sportyqa.webdriver import BettingPage

# Stable, clearly-future fixture: Monaco (home) vs Lyon, odds 2.15.
MATCH_ID = "ligue-1-monaco-lyon-2026-10-14"
HOME, AWAY = "Monaco", "Lyon"
ODDS = 2.15
STAKE = "10.00"
STAKE_EUR = 10.0
EXPECTED_PAYOUT = f"{float(STAKE) * ODDS:.2f}"  # 21.50


@pytest.mark.ui
@allure.testcase("SC-01", "UI happy path - single bet end-to-end")
@allure.story("Place a single bet")
@allure.feature("Desktop UI")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Happy path: the UI shows the balance decrease after placing a bet")
def test_ui_happy_path_single_bet(clean_account, driver):
    with allure.step("Open the UI on a clean account (fixture reset it)"):
        page = BettingPage(driver)
        page.open()

    with allure.step("Record the balance the user sees before betting"):
        balance_before = page.header_balance()
        allure.attach(
            f"{balance_before:.2f}", "balance_before", allure.attachment_type.TEXT
        )

    with allure.step(f"Add HOME ({HOME} vs {AWAY}) and stake €{STAKE}"):
        page.select_odds(MATCH_ID, "HOME").fill_stake(STAKE)

    with allure.step("Place the bet and wait for the success receipt"):
        page.place_bet()
        receipt = page.wait_for_receipt()
        check.is_true(
            bool(receipt.bet_id), f"no Bet ID on the receipt ({receipt.bet_id!r})"
        )

    with allure.step("Assert the receipt keeps home-before-away order (per spec)"):
        check.equal(
            receipt.match.lower(),
            f"{HOME} vs {AWAY}".lower(),
            f"receipt teams {receipt.match!r} != 'Monaco vs Lyon' (BUG-08)",
        )

    with allure.step(f"Assert receipt payout equals stake * odds = €{EXPECTED_PAYOUT}"):
        check.equal(
            receipt.payout,
            f"€{EXPECTED_PAYOUT}",
            f"receipt payout {receipt.payout!r} != €{EXPECTED_PAYOUT} (BUG-09)",
        )

    with allure.step("Close the receipt to return to normal browsing"):
        receipt.close()

    with allure.step("The UI balance must reflect the stake having been taken out"):
        balance_after = page.header_balance()
        allure.attach(
            f"{balance_after:.2f}", "balance_after", allure.attachment_type.TEXT
        )
        expected = balance_before - STAKE_EUR
        check.equal(
            balance_after,
            expected,
            f"UI balance {balance_after:.2f} != {balance_before:.2f} - {STAKE_EUR:.2f} "
            f"= {expected:.2f} (BUG-10: header balance is not updated after a bet)",
        )
