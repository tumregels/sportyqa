# sportyqa

## setup

Install the `uv` python package and project manager from the
[uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

Execute the following two commands from the terminal

    uv sync
    uv tool install invoke

Export your user-id into the terminal

    export QA_USER_ID=your-user-id

All the project is configured now. To execute the tests

    inv test

To see all available tasks run

    inv --list

## reports

- [Test Plan](reports/TEST_PLAN.md)
- [Strategy](reports/STRATEGY.md)
- [Bug Reports](reports/BUG_REPORTS.md)
