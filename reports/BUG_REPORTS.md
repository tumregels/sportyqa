# Bug Reports

## Bounded effort

These are the core 6 bugs

* BUG-01, BUG-02, BUG-05 (SC-02), 
* BUG-11 (SC-03),
* BUG-08, BUG-10 (SC-01)

Other reported bugs are marked with **EXTRA**.

---

## BUG-01 - Negative stake accepted; balance increased

**Severity:** Critical

**Found in:** SC-02 (API)

**Reproduction steps:**

  1. `POST /api/reset-balance`
  2. `POST /api/place-bet` `{"matchId":"ligue-1-monaco-lyon-2026-10-14","selection":"HOME","stake":-10}`.
  3. `GET /api/balance`.

**Expected vs Actual:**

  - Expected: 422 - stake must be a positive number (spec 4.1 / 3).
  - Actual: **200** "Bet placed successfully", `payout:-24.5`, and balance increased from 120 to 130**.

**Business impact:** A user can place negative-stake bets that **credit** their balance and obtain funds; financial loss and fraud for the business.

---

## BUG-02 - Sequential valid bets overdraw balance into negative

**Severity:** Critical

**Found in:** SC-02 (API)

**Reproduction steps:**

  1. `POST /api/reset-balance`
  2. Twice `POST /api/place-bet` `{"matchId":"ligue-1-monaco-lyon-2026-10-14","selection":"HOME","stake":100}`.
  3. Read `GET /api/balance` after each api call.

**Expected vs Actual:**

  - Expected: the second bet (stake 100 > remaining 20) blocked with 422 insufficient balance.
  - Actual: second bet returned **200**, balance **−80**.

**Business impact:** Users can spend money they do not have.

---

## BUG-05 - place-bet response reports currency "USD"

**Severity:** High

**Found in:** SC-02 (API)

**Reproduction steps:**

  1. `POST /api/reset-balance`
  2. Successful `POST /api/place-bet`
  3. Read `currency` field
  4. Compare to `GET /api/balance`.

**Expected vs Actual:** Expected `EUR` (as returned by `/api/balance` and reset). Actual **`USD`**.

**Business impact:** Conflicting currency across endpoints can corrupt downstream bookkeeping, receipts and confuse clients.

---

## BUG-08 - Success receipt reverses the teams order

**Severity:** High

**Found in:** SC-01 (UI)

**Reproduction steps:**

  1. Load UI; select future match Monaco vs Lyon (home Monaco) HOME odds is 2.15; stake €10.
  2. Place bet; open success receipt.

**Expected vs Actual:** Expected "Monaco vs Lyon" (home first). Actual receipt shows **"Lyon vs Monaco"**.

**Business impact:** Reversing home/away on a receipt misrepresents the selection made and endup with clients leaving the platform.

---

## BUG-10 - Header balance not updated after a successful bet (until refresh)

**Severity:** High

**Found in:** SC-01 (UI)

**Reproduction steps:**

  1. Header balance €120. Place €10 bet; success receipt shows. Read the header balance.
  2. Refresh; read header balance again.

**Expected vs Actual:** Expected header €110 immediately after (stake recorded). Actual header **still €120.00** right after the receipt; after refresh it becomes **€110.00**.

**Business impact:** User is misled about available funds until a manual refresh, which can lead to attempting bets they cannot afford or mistrusting the app; UI balance inconsistent with server state.

---

## BUG-11 - Request schema accepts arbitrary, injected and duplicate/conflicting fields

**Severity:** High

**Found in:** SC-03 (API)

**Reproduction steps:**

  1. `POST /api/place-bet` with valid required fields plus unknown/injected fields (e.g. `"garbage":"x","hackme":"<script>",...,"balance":999999`) → server returns 200.
  2. Send two `stake` values in one body, e.g. `{"matchId":"...","selection":"HOME","stake":1,"stake":50}`.

**Expected vs Actual:** 

  * Expected - extraneous/injected fields rejected (schema discipline).

  * Actual - arbitrary + prototype/spoof fields accepted (200, no sanitisation) (consistent with OpenAPI `additionalProperties:true` and spec 'extra fields may be ignored'); on a **duplicate `stake` (1 then 50) the server honours the LAST value**.

**Business impact:** The server does not control what it ingests; duplicate/conflicting fields can place an unexpected bet. Xpoofed fields create attack surface for denial or tampering.

---

## EXTRA BUG-03 - Concurrency guard not atomic; two simultaneous bets accepted (double charge)

**Severity:** Critical

**Found in:** SC-04 (API)

**Reproduction steps:**

  1. `POST /api/reset-balance`
  2. Fire 5-15 concurrent `POST /api/place-bet` requests (same stake, same user, future match).
  3. Read `GET /api/balance`, check HTTP codes

**Expected vs Actual:**

  - Expected (spec: idle bet only / 409 in-progress): exactly one 200, rest 409, single transaction.
  - Actual: **two requests returned 200**; balance **120 -> 115 -> 110** for what should be one logical bet.

**Business impact:** A retry/double-submit charges a user for **two bets**

**Note** Intermittent - hard to capture

---

## EXTRA BUG-04 - Malformed JSON body returns HTTP 500 (should be 400)

**Severity:** High

**Found in:** SC-03 (API)

**Reproduction steps:** `POST /api/place-bet` with a malformed (invalid) JSON body and valid `x-user-id`.

**Expected vs Actual:** Expected 400 (`invalid_json` per spec + OpenAPI). Actual **HTTP 500**.

**Business impact:** Can have security implications. Poor integration surface for clients.

---

## EXTRA BUG-06 - reset-balance response does not match persisted balance

**Severity:** High

**Found in:** SC-06 (API)

**Reproduction steps:** 

  1. `POST /api/reset-balance`, read response `balance`
  2. Read `GET /api/balance` 

**Expected vs Actual:** Expected both `125.50` (configured initial, spec), but persisted as `120` on `GET /api/balance`.

**Business impact:** Inconsistent baseline and state undermine QA automation, wrong reset flow.

---

## EXTRA BUG-07 - Past matches served (catalog not filtered to upcoming)

**Severity:** High

**Found in:** SC-05 (UI)

**Reproduction steps:** Get the UI match list; compare each `kickoffDate` to today (2026-09-06).
 
**Expected vs Actual:** Expected only upcoming/pre-match games (spec §1). More than half of the matches have kickoff before today; UI shows a "PAST" badge for them and allows to place a bet.

**Business impact:** Users can bet on already-started/expired events

---

## EXTRA BUG-09 - Success receipt shows wrong payout

**Severity:** High

**Found in:** SC-01 (UI)

**Reproduction steps:** Bet €10 at odds 2.15 (Monaco vs Lyon); read the bet slip "Potential Payout" and the success receipt "Potential Payout".

**Expected vs Actual:** Expected €21.50 (10 * 2.15) on both. Bet slip showed **€21.50**, receipt showed **€20.00**.

**Business impact:** The user will be confused and loose trust on the platform.

---

## Notes / validated-as-correct (execution record; no bug raised)

- Stake boundaries: 0.99/0/100.01/1.001 correctly rejected with 422 messages; 1.00 and 100.00 accepted.
- Selection & match-id validation correct (only HOME/DRAW/AWAY; blank/unknown → 422).
- Missing/malformed auth → 401; unsupported method → 405; non-object body → 400.
- In a clean single bet the money flow is correct (120 -> 110 once, Bet ID generated, slip math 10 * 2.15 = 21.50).
- The odds * stake math is correct in the API and bet slip; the payout discrepancy is in the receipt (see BUG-09).
- "PAST" matches present in the same data feed (BUG-07) were excluded from all valid-bet scenarios; only future fixtures used for placement tests.

---

## Security finding (advisory; verify ownership) - wide-open CORS with header-based auth, and undeclared method handling

- **Finding:** each endpoint answers `OPTIONS` → 204 with `Access-Control-Allow-Origin: *`, `Allow-Methods: POST, OPTIONS`, `Allow-Headers: X-User-Id`. The app authenticates via the `x-user-id` **header/query** (not an HttpOnly cookie). A `*` origin allow-list combined with a reusable, URL-visible `user-id` allows any website to make authenticated calls (cross-site bet placement) if a victim's `user-id` is known/leaked.

- **Method surface:** PUT/PATCH/DELETE/HEAD/TRACE → 405 (correct); `CONNECT` → 400 (inconsistent); `OPTIONS` un-restricted; 405 responses expose no `Allow` header; GET endpoints silently accept (ignore) a body.

- **Recommendation:** verify the intended CORS/origin policy and whether `*` is deliberate; restrict allowed origins; consider re-checking that only GET/POST are advertised (`Allow` header) and document the 400–`CONNECT` deviation. Notify DevOps team.
