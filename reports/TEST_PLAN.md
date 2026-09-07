# Test Plan

**Scope:** Desktop web UI + REST API **Risk focus:** money-flow correctness,
data consistency across surfaces (list - bet slip - receipt - balance), boundary
enforcement, blocking of invalid / unintentional bets.

## Test Scenarios

### SC-01 - (Critical) UI Happy Path: place a single bet end-to-end and confirm receipt + balance consistency

**Risk & rationale:** This is the core user journey (bet slip, receipt,
balance). Cross-surface data consistency (match order, payout, and balance) is
where we expect UI-layer defects that the API cannot reveal. Highest business
value, provided the user has the option to go through a happy path.

**Steps:**

1. Reset balance; load `?user-id=...` UI; note header balance.
2. Pick a **future** game, e.g. Monaco vs Lyon
   (`ligue-1-monaco-lyon-2026-10-14`), click the **1** (HOME) odds @2.15.
3. In the bet slip enter stake €10.00.
4. Verify slip shows selection order, odds, stake, and potential payout.
5. Click **Place Bet**; observe "Placing..." then a terminal outcome (receipt or
   error).
6. Inspect the success receipt: team order, stake, odds, payout, timestamp, Bet
   ID.
7. Close receipt; confirm no active selection returns and header balance is
   correct after refresh.

**Expected result:** stake deducted exactly once; slip and receipt agree on
order ("Monaco vs Lyon"), odds (2.15), payout (€21.50 = 10 * 2.15); header +
slip balance both reflect the deduction consistently.

---

### SC-02 - (Critical) API: successful bet money-flow and boundary validation

**Risk & rationale:** Money math and limit enforcement live in the API. Under-
or over-charging, or accepting invalid stake amounts, is the highest-impact
failure and is fully testable at the API level.

**Steps:**

1. Reset balance; `GET /api/matches` to pick a future match id and its odds.
2. `POST /api/place-bet` with `matchId`, `selection` (HOME/DRAW/AWAY), and valid
   stakes.
3. Verify 200 response fields: `message`, odds, `payout = stake * odds`,
   `balance` reduced, `currency`.
4. Boundary: stake `1.00` and `100.00` accepted; `0.99`, `0`, `100.01`, and
   `1.001` rejected (expected 422 with clear message).
5. Verify each persisted balance by `GET /api/balance` after each accepted bet.

**Expected result:** 200 for in-range stakes with correct payout and single
correct deduction; correct 422 for out-of-range/precision; persisted state
consistent after each bet.

---

### SC-03 - (Critical) API: field, match-selection, auth, protocol & security hardening validation

**Risk & rationale:** Guarding against invalid selections/matches,
unauthorized/malformed calls and an underspecified surface is a core integrity +
security requirement. Broken handling (e.g., 500 on a client mistake), an
un-validated request schema, a wide-open CORS/method surface, and
silently-ignored payloads all indicate weak layering and can enable abuse. We
hold the API to strict request/response discipline even if the spec is
permissive.

**Steps:**

1. `selection` = HOME/DRAW/AWAY -> 200; `selection` = `home`, `draw`, missing ->
   422 invalid selection.
2. `matchId` blank/missing/unknown -> 422 (invalid match id / match not found).
3. Missing or empty `x-user-id` -> 401; `GET /api/matches` without auth -> 401.
4. **Unsupported methods:** PUT/PATCH/DELETE/HEAD/TRACE/CONNECT on each endpoint
   and OPTIONS where not required -> expect 405 (document any 400/204
   deviations) and an `Allow` header describing the permitted set. Assert only
   documented GET/POST are functionally available.
5. **Schema/body strictness:** non-object body -> 400; malformed JSON -> expect
   400 (flag 500). Submit unknown/injected fields (arbitrary `garbage`, spoofed
   `balance`), and **duplicate/conflicting required fields** (e.g., two `stake`
   values) -> confirm server ignores-or-rejects and never lets
   extraneous/duplicate data change the intended wager.
6. **CORS/Origin policy:** confirm origin allow-list and
   `Access-Control-Allow-*` are not blanket `*` given the API is authenticated
   via the `x-user-id` header/query (cross-site place-bet risk).
7. GET endpoints: confirm acceptance/refusal of a request body.

**Expected result:** correct error classes per spec; only required methods,
well-formed payload keys are honored; no 500 for a client-side malformed body;
CORS and schema do not permit cross-site or injected/duplicate-driven bets; any
deviation is reported as a security/hardening finding.

---

### SC-04 - (High) API + UI: insufficient-balance and rate/concurrency integrity on valid bets

**Risk & rationale:** Prevents over-committing funds or accepting bets a user
cannot cover. Confirms the single-active-bet rule when the user submits
quickly/concurrently and that betting beyond balance is blocked.

**Steps:**

1. Reset balance; issue a single bet whose stake **exceeds** current balance ->
   expect 422 insufficient balance and no mutation.
2. Fire multiple valid bets (each individually in-range) in sequence without
   reset -> confirm balance never goes negative.
3. Fire N simultaneous place-bet requests -> expect exactly one 200 and the rest
   409 (no double debit).
4. UI: attempt to place a bet beyond balance -> expect a clear "Insufficient
   balance" message and no balance mutation.

**Expected result:** no bet is placed that the balance cannot cover; only one
bet succeeds in any concurrent burst; no negative or double-charged balance.

---

### SC-05 - (High) API + UI: match catalog correctness (upcoming only) & currency consistency

**Risk & rationale:** The bet list and receipt must show only upcoming,
correctly-ordered matches and a consistent currency; presenting stale matches or
mixed currencies can cause user exodus.

**Steps:**

1. `GET /api/matches` and the UI list: assert all listed matches kick off
   on/after today (no past matches).
2. Confirm each match card shows `homeTeam` before `awayTeam` consistently
   through list -> slip -> receipt.
3. Compare `currency` across `GET /api/balance`, `POST /api/place-bet` response
   and reset; assert all EUR.

**Expected result:** only upcoming matches shown; home-before-away order
preserved everywhere; currency EUR everywhere.

---

### SC-06 - (Medium) API: reset-balance persisted-state consistency & receipt/UX close behaviors

**Risk & rationale (strategy):** Reset is a support/QA fixture and a
state-isolation control. Consistency between the reset response and the later
read is required for trustworthy automation and user trust.

**Steps:**

1. `POST /api/reset-balance` -> capture response `balance`.
2. `GET /api/balance` -> compare.
3. In UI, after a success receipt, verify error/close paths: closing receipt
   returns to a clean (no-selection) state; header balance reflects the true,
   latest balance without requiring a page refresh.

**Expected result:** persisted `GET /api/balance` equals the reset response
baseline and remains stable; receipt close clears selection; no refresh needed
to see true balance.

---

## Execution Priority (what we ran)

Top 3 executed (one UI + two API) to maximize coverage with bounded effort:

1. **SC-01 - UI happy path** (clean single execution).
2. **SC-02 - API money-flow & boundaries** (accepted/rejected stakes,
   payout/currency/balance).
3. **SC-03 - API field/match/auth/protocol/security validation** (extended for
   method-surface, schema strictness).

SC-04/05/06 were covered via targeted exploratory/API probes feeding the bug
report.
