import logging
import pytest
from playwright.sync_api import sync_playwright, Page

# Configure root logger to output detailed log statements
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)s)",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def shared_credentials() -> dict:
    """
    Session-scoped fixture to share account credentials
    created during the signup test with the login test.
    """
    return {}

@pytest.fixture(scope="session")
def playwright_instance():
    logger.info("Initializing Playwright...")
    with sync_playwright() as p:
        yield p
    logger.info("Playwright closed.")

@pytest.fixture(scope="session")
def browser(playwright_instance):
    logger.info("Launching Chromium browser in headed mode...")
    # Set headless=False and add slow_mo so you can watch execution live
    browser = playwright_instance.chromium.launch(
        headless=False,
        slow_mo=1000,
        args=["--no-sandbox"]
    )
    yield browser
    logger.info("Closing Chromium browser...")
    browser.close()

@pytest.fixture(scope="function")
def page(browser):
    logger.info("Creating new browser context and page...")
    # Set standard viewport size
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        accept_downloads=True
    )
    page = context.new_page()
    yield page
    logger.info("Closing page and context...")
    context.close()


# Custom hooks for styling pytest-html reports and user-friendly naming

FRIENDLY_NAMES = {
    "test_signup_and_verify": "User Account Registration & Email Verification Flow",
    "test_login_with_new_account": "Successful Login using Verified Account Credentials",
    "test_login_wrong_password": "Login Validation - Incorrect Password Attempt",
    "test_login_invalid_email_format": "Input Validation - Malformed Email Format Check",
    "test_login_empty_fields": "Input Validation - Blank / Empty Fields Check",
    "test_login_email_typo": "Resilience Check - Common Email Domain Typo Handling",
    "test_login_sql_injection": "Security Check - SQL Injection Vector Sanitization",
    "test_login_html_injection": "Security Check - XSS / HTML Script Injection Sanitization",
    "test_successful_logout": "User Session Management - Successful Logout and Clear Session"
}

def pytest_html_results_table_row(report, cells):
    if len(cells) > 1:
        for key, friendly in FRIENDLY_NAMES.items():
            if key in report.nodeid:
                cells[1] = f'<td class="col-name">{friendly}</td>'
                break

def pytest_html_report_title(report):
    # Set custom report title in pytest-html v4
    report.title = "Tichi Webapp QA Test Suite Execution Report"

def pytest_html_results_summary(prefix, summary, postfix, session):
    # Inject modern, premium dark-theme CSS style rules into the report
    prefix.extend([
        """
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
                background-color: #0f172a !important;
                color: #cbd5e1 !important;
                margin: 40px !important;
            }
            h1 {
                color: #38bdf8 !important;
                font-weight: 700 !important;
                text-align: center !important;
                margin-bottom: 25px !important;
                border-bottom: 2px solid #334155 !important;
                padding-bottom: 15px !important;
            }
            .summary {
                background: #1e293b !important;
                border: 1px solid #334155 !important;
                border-radius: 8px !important;
                padding: 20px !important;
                color: #e2e8f0 !important;
                margin-bottom: 25px !important;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
            }
            #results-table {
                width: 100% !important;
                border-collapse: collapse !important;
                margin-top: 20px !important;
                background: #1e293b !important;
                border-radius: 8px !important;
                overflow: hidden !important;
                border: 1px solid #334155 !important;
            }
            #results-table th {
                background-color: #334155 !important;
                color: #38bdf8 !important;
                font-weight: 600 !important;
                padding: 12px 16px !important;
                font-size: 14px !important;
                border-bottom: 2px solid #475569 !important;
            }
            #results-table td {
                padding: 12px 16px !important;
                border-bottom: 1px solid #334155 !important;
                font-size: 13px !important;
                color: #cbd5e1 !important;
            }
            #results-table tr:hover {
                background-color: #334155 !important;
            }
            #results-table tr.passed {
                background-color: rgba(16, 185, 129, 0.1) !important;
            }
            #results-table tr.failed {
                background-color: rgba(239, 68, 68, 0.1) !important;
            }
            #results-table tr.skipped {
                background-color: rgba(245, 158, 11, 0.1) !important;
            }
            .passed td:first-child {
                border-left: 5px solid #10b981 !important;
            }
            .failed td:first-child {
                border-left: 5px solid #ef4444 !important;
            }
            .skipped td:first-child {
                border-left: 5px solid #f59e0b !important;
            }
            .passed { color: #10b981 !important; font-weight: bold; }
            .failed { color: #ef4444 !important; font-weight: bold; }
            .skipped { color: #f59e0b !important; font-weight: bold; }
            #show-all-details, #show-all-details-label {
                color: #38bdf8 !important;
            }
        </style>
        """
    ])
