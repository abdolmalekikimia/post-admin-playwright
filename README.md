# Admin Portal Playwright QA Portfolio

## QA ownership and AI-generated implementation

This portfolio reflects my QA work, business-workflow context, test-scope direction,
execution and review of results against requirements. I guided the automation
approach and used AI tools to generate the code implementation; I did not
independently write the Python code or implement the framework from scratch.

The code is evidence of an AI-assisted QA workflow, not a claim of independently
assessed Python programming or software-engineering proficiency. Scenario proposals,
technical analysis and documentation also used AI assistance. Only the executed
checks and documented evidence support the stated validation scope.


Sanitized portfolio representation of professional QA work for a postal sorting administration portal. Built with Python, Pytest, Playwright and Page Objects. Architecture, scenario direction and outcome review were owned by the QA author; implementation used AI assistance.

## Coverage demonstrated

- Authentication, navigation and access control scenarios.
- Discrepancy report filters, results, pagination and error states.
- Device and edge administration workflows with deterministic API testbeds.
- Per-test browser contexts, failure screenshots, Allure attachments and HTML reporting.

## What can run publicly

This repository contains test code, not the company's frontend or backend. Feature mocks still require a compatible frontend; some fixtures also use live login. Mocked API checks do not demonstrate end-to-end backend correctness. Company hosts, credentials, deployment assets, generated reports and internal coverage documents are excluded. Sample identifiers are synthetic.

By default the application tests are skipped. A public green collection job is not evidence of a live integration pass. Enable only against a compatible demo system you own; some scenarios perform writes.

## Setup

Requires Python 3.11+.

```sh
python -m venv .venv
python -m pip install -r requirements.txt
python -m playwright install chromium
python -m pytest --collect-only -q
```

Activate the virtual environment before installing. Copy `.env.example` to `.env` and configure your demo URL and credentials. Set `RUN_DEMO_TESTS=1` to run the application suite. Do not commit `.env` or test output.

No company frontend, real accounts or test results are included. This is a code portfolio with explicit execution limitations, not a claim of independently implemented code or complete system coverage.
