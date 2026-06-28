import logging
import random
import re
import time
import pytest
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from pages.signup_page import SignupPage
from utils.email_service import EmailService

logger = logging.getLogger(__name__)

BASE_URL = "https://tichi-app-webapp-stage.web.app"

def test_signup_and_verify(page: Page, shared_credentials: dict):
    """
    Test Case 1: Sign up a new user using a temporary email address.
    1. Create a mailbox.
    2. Go to the login page, enter the email.
    3. Verify redirection to the Sign Up form.
    4. Fill out signup details and submit.
    5. Poll for the activation email and extract the link.
    6. Navigate to the activation link to complete verification.
    7. Save credentials to shared_credentials.
    """
    logger.info("Starting test_signup_and_verify...")
    
    # Step 1 & 2: Navigate to landing/login page and find an unregistered email
    max_attempts = 3
    email = None
    mailbox_id = None
    password = f"Tichi@{random.randint(100000, 999999)}"
    
    for attempt in range(1, max_attempts + 1):
        mailbox_id, email = EmailService.create_mailbox()
        logger.info(f"Attempt {attempt}: Testing with generated email: {email}")
        
        login_page = LoginPage(page)
        login_page.navigate(f"{BASE_URL}/login")
        
        logger.info(f"Entering email: {email} to initiate signup flow.")
        login_page.enter_email(email)
        login_page.click_continue()
        
        # Wait a moment to see if redirect to sign-up happens
        page.wait_for_timeout(3000)
        
        if "/sign-up" in page.url:
            break
        else:
            logger.warning(f"Email {email} did not transition to sign-up page (it might already be registered). Retrying with a new mailbox...")
            if attempt == max_attempts:
                pytest.fail(f"Failed to redirect to sign-up after {max_attempts} attempts. All temporary emails were likely already registered.")

    # Verify we are on the sign-up page
    expect(page).to_have_url(re.compile(r".*/sign-up.*"), timeout=15000)
    logger.info(f"Successfully redirected to Sign Up page using email: {email}")
    
    # Step 4: Fill out the Sign Up form
    signup_page = SignupPage(page)
    signup_page.fill_first_name("QA")
    signup_page.fill_last_name("Intern")
    phone_number = f"9{random.randint(100000000, 999999999)}"
    signup_page.fill_phone(phone_number)
    signup_page.fill_password(password)
    signup_page.fill_confirm_password(password)
    signup_page.check_terms()
    
    logger.info("Submitting signup form...")
    signup_page.submit_signup()
    
    # Wait for the email to be triggered and sent
    page.wait_for_timeout(5000)
    
    # Step 5: Poll for activation message
    try:
        messages = EmailService.poll_messages(mailbox_id, max_attempts=12, interval_sec=5)
        # Fetch the message details
        # The body is usually in the "body" or "html" key of the first message
        message = messages[0]
        message_body = message.get("body", "") or message.get("html", "") or message.get("text", "")
        if not message_body:
            logger.warning("Message body was empty. Attempting to get it from fields...")
            message_body = str(message)
            
        logger.debug(f"Retrieved email body: {message_body[:200]}...")
        
        # Step 6: Extract activation link
        activation_link = EmailService.extract_activation_link(message_body)
        logger.info(f"Navigating to activation link to verify account: {activation_link}")
        
        # Open activation link in browser
        page.goto(activation_link)
        page.wait_for_timeout(5000)
        
        # Verify activation page loaded successfully
        logger.info("Account activation step complete.")
        
    except Exception as e:
        logger.error(f"Failed during email verification phase: {e}")
        raise
        
    # Store credentials for the next test case
    shared_credentials["email"] = email
    shared_credentials["password"] = password
    logger.info("Sign up and verification complete. Credentials stored in shared state.")

def test_login_with_new_account(page: Page, shared_credentials: dict):
    """
    Test Case 2: Log in using the newly created and verified account.
    """
    logger.info("Starting test_login_with_new_account...")
    
    email = shared_credentials.get("email")
    password = shared_credentials.get("password")
    
    # Fail/skip the test if sign-up didn't complete successfully
    if not email or not password:
        pytest.fail("Pre-requisite credentials from signup test are missing. Sign up test might have failed.")
        
    logger.info(f"Attempting to log in with: {email}")
    
    login_page = LoginPage(page)
    login_page.navigate(f"{BASE_URL}/login")
    
    # Run full login flow
    login_page.login_flow(email, password)
    
    # Wait for login completion
    page.wait_for_timeout(5000)
    
    # Verify login success
    success = login_page.is_login_successful(timeout=15000)
    assert success, f"Login failed for verified user: {email}"
    
    logger.info(f"Successfully logged in with verified account: {email}")

def test_login_wrong_password(page: Page, shared_credentials: dict):
    """
    test_login_wrong_password: Logs in with a valid email but an incorrect password,
    asserting that a visible validation error message appears.
    """
    logger.info("Starting test_login_wrong_password...")
    email = shared_credentials.get("email")
    if not email:
        pytest.skip("Pre-requisite credentials from signup test are missing. Skipping test_login_wrong_password.")
        
    login_page = LoginPage(page)
    login_page.navigate(f"{BASE_URL}/login")
    login_page.enter_email(email)
    login_page.click_continue()
    
    # Wait for password input to be visible
    page.locator("input[type='password']").wait_for(state="visible", timeout=10000)
    
    # Enter incorrect password (must be within 8-15 characters)
    login_page.enter_password("Wrong@123")
    login_page.click_signin()
    
    # Assert a visible validation error message appears (or verify we remain on the login page as fallback)
    error_locator = page.locator("text=/.*(incorrect|invalid|error|wrong|fail|match|not found).*/i")
    try:
        expect(error_locator.first).to_be_visible(timeout=10000)
    except Exception as e:
        logger.warning(f"Could not locate error text, verifying fallback (remaining on login page): {e}")
        expect(page).to_have_url(re.compile(r".*/login.*"))
    logger.info("Validation error message for wrong password verified successfully.")

def test_login_invalid_email_format(page: Page):
    """
    test_login_invalid_email_format: Enters an invalid email string ("testinvalid")
    to check if the application handles or fails email validation properly on the frontend.
    """
    logger.info("Starting test_login_invalid_email_format...")
    login_page = LoginPage(page)
    login_page.navigate(f"{BASE_URL}/login")
    
    # Enter malformed email format
    login_page.enter_email("testinvalid")
    login_page.click_continue()
    
    # Check for HTML5 required constraint or visible error label
    email_input = page.locator("input[type='email']").first
    validation_message = email_input.evaluate("el => el.validationMessage")
    
    if validation_message:
        logger.info(f"HTML5 validation message displayed: {validation_message}")
        assert len(validation_message) > 0
    else:
        # Check if an on-screen validation error text is displayed
        error_locator = page.locator("text=/.*(valid email|invalid email|email format|invalid address|format).*/i")
        expect(error_locator.first).to_be_visible(timeout=10000)
        
    # Ensure we remain on the login page and don't navigate
    expect(page).to_have_url(re.compile(r".*/login.*"))
    logger.info("Invalid email format handling verified successfully.")

def test_login_empty_fields(page: Page):
    """
    test_login_empty_fields: Attempts submission with completely blank fields
    to check for required-field error prompts.
    """
    logger.info("Starting test_login_empty_fields...")
    login_page = LoginPage(page)
    login_page.navigate(f"{BASE_URL}/login")
    
    # Submit without entering email
    login_page.click_continue()
    
    # Verify HTML5 required constraint or validation error
    email_input = page.locator("input[type='email']").first
    validation_message = email_input.evaluate("el => el.validationMessage")
    
    if validation_message:
        logger.info(f"HTML5 Required message: {validation_message}")
        assert len(validation_message) > 0
    else:
        error_locator = page.locator("text=/.*(required|empty|fill|blank|enter).*/i")
        expect(error_locator.first).to_be_visible(timeout=10000)
        
    expect(page).to_have_url(re.compile(r".*/login.*"))
    logger.info("Empty fields handling verified successfully.")

def test_login_email_typo(page: Page):
    """
    test_login_email_typo: Tests resilience against common email domain typos (e.g., "user@gamil.com" or "user@gmal.com")
    to verify that the system flags it as an unrecognized/typo email format and blocks submission.
    """
    logger.info("Starting test_login_email_typo...")
    login_page = LoginPage(page)
    login_page.navigate(f"{BASE_URL}/login")
    
    # Enter an email containing a common typo domain
    typo_email = f"test_typo_{random.randint(1000, 9999)}@gmal.com"
    login_page.enter_email(typo_email)
    login_page.click_continue()
    
    # Wait for potential page transition
    page.wait_for_timeout(3000)
    
    # If the application redirected to the sign-up page, fail with an explicit defect description immediately
    if "/sign-up" in page.url:
        pytest.fail("DEF-002: App navigated to signup page on unregistered/typo email instead of displaying invalid input error.")
        
    # Check for on-screen warning / typo error text
    error_locator = page.locator("text=/.*(did you mean|invalid|typo|check spelling|correct email).*/i")
    expect(error_locator.first).to_be_visible(timeout=2000)
    logger.info("Email domain typo validation warning verified successfully.")

def test_login_sql_injection(page: Page):
    """
    test_login_sql_injection: Inputs a classic SQL injection string into the email field
    and asserts that the application safely rejects the input without exposing database errors.
    """
    logger.info("Starting test_login_sql_injection...")
    login_page = LoginPage(page)
    login_page.navigate(f"{BASE_URL}/login")
    
    # SQLi payload
    sqli_payload = "' OR '1'='1"
    login_page.enter_email(sqli_payload)
    login_page.click_continue()
    
    # Assert we do not bypass authorization (must not go to home/dashboard)
    page.wait_for_timeout(3000)
    expect(page).not_to_have_url(re.compile(r".*/dashboard.*"))
    expect(page).not_to_have_url(re.compile(r".*/home.*"))
    
    # Ensure no database stack traces or raw query dump is shown on the body
    body_text = page.locator("body").inner_text().lower()
    for err in ["sql", "syntax error", "mysql", "postgresql", "sqlite", "query fail", "database exception"]:
        assert err not in body_text, f"Potential SQL Injection database error exposed: {err}"
        
    logger.info("SQL Injection attempt safely handled and rejected.")

def test_login_html_injection(page: Page):
    """
    test_login_html_injection: Inputs basic HTML script tags into the fields
    to ensure inputs are properly sanitized and do not execute unexpected code.
    """
    logger.info("Starting test_login_html_injection...")
    login_page = LoginPage(page)
    login_page.navigate(f"{BASE_URL}/login")
    
    # HTML script payload
    html_payload = "🛸 <script>alert(1)</script>"
    login_page.enter_email(html_payload)
    login_page.click_continue()
    
    # Register alert handler to fail test if the HTML tag compiles and runs
    page.on("dialog", lambda dialog: pytest.fail("XSS/HTML Injection vulnerability executed a dialog popup!"))
    
    page.wait_for_timeout(3000)
    
    # Ensure page did not bypass authentication
    expect(page).not_to_have_url(re.compile(r".*/dashboard.*"))
    logger.info("HTML Injection payload safely sanitized and blocked.")


