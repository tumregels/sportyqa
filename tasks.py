"""Invoke tasks for sportyqa: lint, test, and allure reporting."""

from __future__ import annotations

import shutil

from invoke import task

ALLURE_RESULTS = "allure-results"
ALLURE_REPORT = "allure-report"
JUNIT_XML = "junit.xml"


@task
def install(c):
    """Sync dependencies via uv. Will install .venv if missing."""
    c.run("uv sync")


@task
def precommit_setup(c):
    """Install the pre-commit git hook."""
    c.run("uv run pre-commit install")


@task
def precommit_update(c):
    """Update pre-commit hooks to their latest pinned revisions."""
    c.run("uv run pre-commit autoupdate")


@task(help={"fix": "apply autofixes for lint violations"})
def lint(c, fix=False):
    """Check code style with ruff (pass --fix to autofix)."""
    c.run(f"uv run ruff check {'--fix ' if fix else ''}.")


@task
def format(c, check=False):
    """Format code with ruff (pass --check to only verify)."""
    c.run(f"uv run ruff format {'--check ' if check else ''}.")


@task(
    help={
        "m": "pytest -m expression to filter by marker (e.g. api, ui)",
        "junit": "also write a JUnit XML report to junit.xml",
    },
    default=True,
)
def test(c, m=None, verbose=True, junit=False):
    """Run the pytest suite, recording Allure results."""
    args = [f"--alluredir={ALLURE_RESULTS}"]
    if verbose:
        args.append("-v")
    if m:
        args.append(f"-m {m!r}")
    if junit:
        args.append(f"--junitxml={JUNIT_XML}")
    c.run(f"uv run pytest {' '.join(args)}")


@task(help={"junit": "also write a JUnit XML report to junit.xml"})
def api(c, junit=False):
    """Run only the API test suite."""
    args = [f"--alluredir={ALLURE_RESULTS}", "-v"]
    if junit:
        args.append(f"--junitxml={JUNIT_XML}")
    c.run(f"uv run pytest -m api {' '.join(args)}")


@task(help={"junit": "also write a JUnit XML report to junit.xml"})
def ui(c, junit=False):
    """Run only the UI (Selenium) test suite."""
    args = [f"--alluredir={ALLURE_RESULTS}", "-v"]
    if junit:
        args.append(f"--junitxml={JUNIT_XML}")
    c.run(f"uv run pytest -m ui {' '.join(args)}")


@task
def report(c, serve=False):
    """Generate (and optionally serve) the Allure HTML report from results."""
    if not shutil.which("allure"):
        print(
            "allure CLI not found on PATH; skipping report generation (brew install allure)."
        )
        return
    if serve:
        c.run(f"allure serve {ALLURE_RESULTS}")
    else:
        c.run(f"allure generate {ALLURE_RESULTS} -o {ALLURE_REPORT} --clean")


@task
def clean(c):
    """Remove test/report artifacts and Python caches."""
    c.run(
        f"rm -rf {ALLURE_RESULTS} {ALLURE_REPORT} {JUNIT_XML} .pytest_cache .ruff_cache"
    )
    c.run("find . -type d -name __pycache__ -not -path './.venv/*' -exec rm -rf {} +")


@task()
def all(c):
    """Lint, then run the full test suite and generate the Allure report."""
    lint(c)
    test(c)
    report(c)
