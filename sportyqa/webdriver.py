"""Chrome driver factory + small page-objects for the bet-slip / receipt flow."""

from __future__ import annotations

import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from . import config


def new_driver(options: Options | None = None) -> webdriver.Chrome:
    """Start Chrome; Selenium Manager provisions the matching chromedriver."""
    opts = options or Options()
    if config.HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1366,768")  # most common laptop
    return webdriver.Chrome(options=opts)


class BettingPage:
    """The fixtures list + bet slip, with shared WebDriverWait helpers."""

    ODDS_BUTTON = (By.CSS_SELECTOR, "#odds-{match_id}-{selection}")
    STAKE_INPUT = (By.ID, "bet-slip-stake-input")
    SLIP_SELECTED_TEAMS = (By.CLASS_NAME, "betSelectionTeams")
    SLIP_ODDS = (By.CLASS_NAME, "betSelectionOdds")
    SLIP_POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")
    PLACE_BET_BUTTON = (By.ID, "bet-slip-place-bet")
    HEADER_BALANCE = (By.ID, "header-balance")
    RECEIPT_MODAL = (By.ID, "modal-success")

    def __init__(
        self,
        driver: webdriver.Chrome,
        user_id: str = config.QA_USER_ID,
    ):
        self.driver = driver
        self.wait = WebDriverWait(driver, config.UI_TIMEOUT_SECONDS)
        self.url = f"{config.API_BASE_URL}/?user-id={user_id}"

    def open(self) -> BettingPage:
        """Load the betting UI."""
        self.driver.get(self.url)
        return self

    def _visible(self, locator: tuple) -> WebElement:
        return self.wait.until(EC.visibility_of_element_located(locator))

    def _text(self, locator: tuple) -> str:
        return self._visible(locator).text.strip()

    @property
    def selected_teams(self) -> str:
        """Teams in the bet slip once an odds button is picked ('Monaco vs Lyon')."""
        return self._text(self.SLIP_SELECTED_TEAMS)

    @property
    def potential_payout(self) -> str:
        """Live slip payout for the current stake ('€21.50')."""
        return self._text(self.SLIP_POTENTIAL_PAYOUT)

    @property
    def slip_odds(self) -> str:
        """Selected odds shown in the slip ('Odds: 2.15')."""
        return self._text(self.SLIP_ODDS)

    @property
    def header_balance_text(self) -> str:
        """Raw header text ('account_balance_wallet\nBalance: €120.00')."""
        return self._text(self.HEADER_BALANCE)

    def header_balance(self) -> float:
        """Current header balance shown to the user (e.g 120.0).

        On a fresh load the header briefly renders €0.00, so resolve once a positive amount is visible.
        """

        def _amount(driver) -> float:
            text = driver.find_element(*self.HEADER_BALANCE).text
            match = re.search(r"[\d.,]+", text)
            amount = float(match.group().replace(",", "")) if match else 0.0
            return amount if amount > 0 else False

        return self.wait.until(_amount)

    def select_odds(self, match_id: str, selection: str) -> BettingPage:
        """Click a 1/X/2 odds button for a fixture on the match list."""
        by, template = self.ODDS_BUTTON
        btn = self.wait.until(
            EC.element_to_be_clickable(
                (by, template.format(match_id=match_id, selection=selection.lower()))
            )
        )
        # Odds rows can sit under the sticky header; use a JS click to be safe.
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", btn
        )
        self.driver.execute_script("arguments[0].click();", btn)
        return self

    def fill_stake(self, stake: str) -> BettingPage:
        self._visible(self.STAKE_INPUT).send_keys(stake)
        return self

    def place_bet(self) -> BettingPage:
        self.wait.until(EC.element_to_be_clickable(self.PLACE_BET_BUTTON)).click()
        return self

    def wait_for_receipt(self) -> Receipt:
        """Wait for and wrap the success modal that appears after placing a bet."""
        modal = self._visible(self.RECEIPT_MODAL)
        return Receipt(self.driver, modal)


class Receipt:
    """Read-only view of the success modal ('#modal-success')."""

    BET_ID = (By.ID, "modal-success-bet-id")
    MATCH = (By.ID, "modal-success-match")
    STAKE = (By.ID, "modal-success-stake")
    ODDS = (By.ID, "modal-success-odds")
    PAYOUT = (By.ID, "modal-success-payout")
    PLACED_AT = (By.ID, "modal-success-placed-at")
    CLOSE_BUTTON = (By.ID, "modal-success-close")

    def __init__(self, driver: webdriver.Chrome, modal: WebElement):
        self.driver = driver
        self._modal = modal

    def _text(self, locator: tuple) -> str:
        return self._modal.find_element(*locator).text.strip()

    @property
    def bet_id(self) -> str:
        """Receipt id of the placed bet ('#B-29263')."""
        return self._text(self.BET_ID)

    @property
    def match(self) -> str:
        """Teams as printed on the receipt ('Lyon vs Monaco')."""
        return self._text(self.MATCH)

    @property
    def stake(self) -> str:
        """Staked amount printed on the receipt ('€10.00')."""
        return self._text(self.STAKE)

    @property
    def odds(self) -> str:
        """Decimal odds printed on the receipt ('2.15')."""
        return self._text(self.ODDS)

    @property
    def payout(self) -> str:
        """Potential payout printed on the receipt ('€21.50')."""
        return self._text(self.PAYOUT)

    @property
    def placed_at(self) -> str:
        """Timestamp the bet was placed ('Today, 04:11 PM')."""
        return self._text(self.PLACED_AT)

    def close(self) -> None:
        """Dismiss the receipt so the user can see the post-bet balance."""
        self._modal.find_element(*self.CLOSE_BUTTON).click()
