# Strategy

## Reasons for choosing specific tests

API test - valid money flow - is the foundation of any service, and it should do
the core tasks flowlessly. Can be compared with the foundation of a building.
Once done correctly you are ready for most of the earthquakes. The design, i.e.
UI inside the building can have some flows, but as long as the foundation is
rock solid, the resident will be safe.

UI test - the happy path - is the guarantee that most of the clients stay. There
can be some issues in the UI, some stuff may feel visually appealing or not, not
smooth, maybe even slow - but as long as the happy path holds and the api is
rock solid, the business will function as expected.

## What to leave for manual testing

- validate over multiple browsers

- a smooth ui check, visually appealing (different resolutions)

- validate filter behavior: date selection range, min/max for odds - still
  important, somewhat easy to spot manually

- random action injection during testing, like refresh during submission, double
  click on submit

- allow creation of test users and balances

- testing with blocked url to check how ui handles a failing endpoint

## Scaling recommendations

- Add a schema validation layer, so the api accepts only what is defined in the
  spec and rejects anything else.

- execute api suite on every PR, run E2E tests on schedule.

- try to avoid parallel execution as long as possible. most of the time its not
  needed.

- resolve spec inconsistencies (inside feature spec pdf, different between
  minimum stake value 1.00 vs 1.01)

- minimise mock tests where possible - as reallity drift bites back very fast

- use JUnit XML reports. JUnit XML is the standard format for exchanging test
  results between testing frameworks and CI systems

- report screenshots on error, just to make life easy for everyone.

- use soft assertions to execute all asserts in the test, before failing the
  test. pytest-check used in the ui test.

- use python logging module or [structlog](https://www.structlog.org/en/stable/)
  to get the reasons of a failing test.
