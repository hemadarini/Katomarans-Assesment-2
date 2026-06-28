import logging
from playwright.sync_api import Page, expect
from pages.base_page import BasePage

logger = logging.getLogger(__name__)

class LoginPage(BasePage):
    EMAIL_SELECTORS = ["input[type='email']", "input[name='email']", "input[placeholder*='email' i]"]
    CONTINUE_BUTTON_SELECTORS = ["button:has-text('Continue')", "button[type='submit']", "button:has-text('Sign In')"]
    PASSWORD_SELECTORS = ["input[type='password']", "input[name='password']"]
    SIGNIN_BUTTON_SELECTORS = ["button:has-text('Sign In')", "button:has-text('Login')", "button[type='submit']"]
    
    # Success indicator selectors (e.g. Profile icon, navbar dashboard link, logout button, etc.)
    DASHBOARD_SELECTORS = ["a[href*='dashboard']", "button:has-text('Logout')", "button:has-text('Profile')", ".profile-menu", "div:has-text('Dashboard')"]

    def _fill_fallback(self, selectors: list[str], value: str, field_name: str) -> None:
        for selector in selectors:
            try:
                if self.page.locator(selector).is_visible():
                    self.fill(selector, value)
                    logger.info(f"Filled {field_name} using selector: '{selector}'")
                    return
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed for field {field_name}: {e}")
        
        logger.warning(f"No visible selector found for {field_name}, trying fallback: '{selectors[0]}'")
        self.fill(selectors[0], value)

    def _click_fallback(self, selectors: list[str], field_name: str) -> None:
        for selector in selectors:
            try:
                if self.page.locator(selector).is_visible():
                    self.click(selector, force=True)
                    logger.info(f"Clicked {field_name} using selector: '{selector}'")
                    return
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed for field {field_name}: {e}")
        
        logger.warning(f"No visible selector found for {field_name}, trying fallback: '{selectors[0]}'")
        self.click(selectors[0], force=True)

    def enter_email(self, email: str) -> None:
        self._fill_fallback(self.EMAIL_SELECTORS, email, "Email")
        # Press Tab to trigger blur and run client-side validation
        try:
            self.page.locator("input[type='email']").press("Tab")
            self.page.wait_for_timeout(500)
        except Exception as e:
            logger.debug(f"Blurring email field failed: {e}")

    def click_continue(self) -> None:
        self._click_fallback(self.CONTINUE_BUTTON_SELECTORS, "Continue Button")
        # If we are still on the login page after clicking, try pressing Enter on the email input
        self.page.wait_for_timeout(1000)
        if "/login" in self.page.url:
            logger.info("Still on login page after Continue click, attempting Enter key press on email field...")
            try:
                self.page.locator("input[type='email']").press("Enter")
            except Exception as e:
                logger.debug(f"Failed to press Enter: {e}")

    def enter_password(self, password: str) -> None:
        self._fill_fallback(self.PASSWORD_SELECTORS, password, "Password")

    def click_signin(self) -> None:
        self._click_fallback(self.SIGNIN_BUTTON_SELECTORS, "Sign In Button")

    def login_flow(self, email: str, password: str) -> None:
        """
        Runs the full login flow:
        - Enter email
        - Click Continue
        - Enter password
        - Click Sign In
        """
        self.enter_email(email)
        self.click_continue()
        
        # Wait a short moment for password field to appear
        self.page.wait_for_timeout(1000)
        
        self.enter_password(password)
        self.click_signin()

    def is_login_successful(self, timeout: float = 15000) -> bool:
        """
        Checks if the login was successful by waiting for dashboard elements or URL change.
        """
        logger.info("Checking if login was successful...")
        # Check if URL changed away from /login
        try:
            self.page.wait_for_function("() => !window.location.href.includes('/login')", timeout=timeout)
            logger.info("URL changed. No longer on login page.")
            return True
        except Exception:
            logger.warning("URL did not change away from login page in time.")
            
        # Try checking for dashboard indicators
        for selector in self.DASHBOARD_SELECTORS:
            if self.is_visible(selector, timeout=2000):
                logger.info(f"Login success confirmed via indicator: '{selector}'")
                return True
                
        return False
