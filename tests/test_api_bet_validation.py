"""API test - bet placement validation & money rule.

Covers two spec business rules against the betting API:

  1. A valid bet pays/stakes correctly and invalid selections/stakes are
     rejected with the documented codes (money/validation rule).
  2. A user can never be placed in a negative balance by betting beyond the
     funds they hold (sequential overdraw rule, spec 4.1).

The last scenario is intentionally *red* against the live build because the
server lets a second bet take the balance below zero (see BUG-02 in the bug
report); the assertion records that regression. Anchored to TEST_PLAN SC-02.
"""

from __future__ import annotations

import allure
import pytest

from sportyqa.config import STAKE_MIN


@pytest.mark.api
@allure.testcase("SC-02", "API money-flow & validation business rule")
@allure.story("Place a single bet")
@allure.feature("REST API")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title(
    "place-bet: valid bet pays correctly; invalid input rejected; balance never overdrawn"
)
def test_place_bet_validation_and_money_rule(api, clean_account):
    with allure.step("Resolve an upcoming fixture to bet on"):
        match = api.upcoming_match()
        assert match is not None, "no upcoming fixture found to bet on"
        match_id = match["id"]
        odds = float(match["odds"]["home"])
        allure.attach(match_id, "match_id", allure.attachment_type.TEXT)
        allure.attach(str(odds), "home_odds", allure.attachment_type.TEXT)

    with allure.step("Place a valid minimum bet (HOME)"):
        status, body = api.place_bet(match_id, "HOME", STAKE_MIN)
        assert status == 200, f"expected 200, got {status}: {body}"

    with allure.step("Verify payout math (stake x odds) on the response"):
        reported_payout = body["payout"]
        expected_payout = round(STAKE_MIN * odds, 2)
        assert reported_payout == expected_payout, (
            f"payout mismatch: got {reported_payout}, expected {expected_payout}"
        )

    with allure.step("Invalid selection is rejected with 422"):
        for bad in ("TIE", "home", ""):
            status, body = api.place_bet(match_id, bad, STAKE_MIN)
            assert status == 422, (
                f"expected 422 for selection={bad!r}, got {status}: {body}"
            )
            assert body.get("error") == "invalid_selection", body

    with allure.step("Below-minimum stake is rejected with 422"):
        status, body = api.place_bet(match_id, "HOME", STAKE_MIN - 0.01)
        assert status == 422, f"expected 422 for stake below min, got {status}: {body}"
        assert body.get("error") == "invalid_stake_min", body

    with allure.step(
        "Bet 40 then 100: a second uncovered bet must not overdraw the balance"
    ):
        # Reset to a known baseline so this scenario is deterministic.
        with allure.step("Reset account to the clean baseline"):
            api.reset_balance()
            baseline = api.get_balance()["balance"]  # 120.00 on the QA account

        with allure.step("Bet EUR 40.00 (within available funds -> 200)"):
            status, body = api.place_bet(match_id, "HOME", 40.0)
            assert status == 200, f"expected 200 for EUR 40 bet, got {status}: {body}"
            after_first = api.get_balance()["balance"]  # 80.00
            assert after_first == baseline - 40.0, (
                f"after EUR 40 stake balance {after_first} != {baseline - 40.0}"
            )

        with allure.step("Bet EUR 100.00 when only EUR 80 remains -> must be rejected"):
            status, body = api.place_bet(match_id, "AWAY", 100.0)

        if status == 200:
            # Conforming spec: the bet must NOT be accepted; it exceeds funds.
            settled = api.get_balance()["balance"]
            assert settled >= 0, (
                f"balance went negative: {baseline} - 40 - 100 -> {settled} "
                "(BUG-02: sequential bets overdraw without an insufficient-balance guard)"
            )
            raise AssertionError(
                "bet of EUR 100 was accepted although only EUR 80 was available "
                f"(balance after: {settled}) (BUG-02)"
            )
        # Expected conforming behaviour: rejected with insufficient balance.
        assert status == 422 and body.get("error") == "insufficient_balance", (
            f"expected 422 insufficient_balance, got {status}: {body}"
        )
