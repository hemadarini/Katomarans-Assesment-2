import logging
from playwright.sync_api import Page, expect
from pages.base_page import BasePage

logger = logging.getLogger(__name__)

class SignupPage(BasePage):
    # Flexible locators with fallbacks to handle dynamic fields
    FIRST_NAME_SELECTORS = ["#firstName", "input[placeholder*='First Name' i]"]
    LAST_NAME_SELECTORS = ["#lastName", "input[placeholder*='Last Name' i]"]
    PHONE_SELECTORS = ["#phoneNumber", "input[type='tel']"]
    PASSWORD_SELECTORS = ["#password", "input[type='password']"]
    CONFIRM_PASSWORD_SELECTORS = ["#confirmPassword", "input[type='confirmPassword']"]
    TERMS_CHECKBOX_SELECTORS = ["#remember", "button#remember", "input[type='checkbox']"]
    SIGNUP_BUTTON_SELECTORS = ["button[type='submit']", "button:has-text('Sign Up')"]

    def _fill_fallback(self, selectors: list[str], value: str, field_name: str) -> None:
        for selector in selectors:
            try:
                if self.page.locator(selector).is_visible():
                    self.fill(selector, value)
                    logger.info(f"Filled {field_name} using selector: '{selector}'")
                    return
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed for field {field_name}: {e}")
        
        # If no visible selector worked, try the first one anyways to trigger failure/log
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

    def fill_first_name(self, first_name: str) -> None:
        self._fill_fallback(self.FIRST_NAME_SELECTORS, first_name, "First Name")

    def fill_last_name(self, last_name: str) -> None:
        self._fill_fallback(self.LAST_NAME_SELECTORS, last_name, "Last Name")

    def fill_phone(self, phone: str) -> None:
        self._fill_fallback(self.PHONE_SELECTORS, phone, "Phone Number")

    def fill_password(self, password: str) -> None:
        self._fill_fallback(self.PASSWORD_SELECTORS, password, "Password")

    def fill_confirm_password(self, password: str) -> None:
        # If confirm password field doesn't exist or is same locator, handle gracefully
        # First check if the page actually has a separate confirm password field
        # E.g. we might have two input[type='password'] on the page
        passwords = self.page.locator("input[type='password']")
        if passwords.count() > 1:
            self._fill_fallback(self.CONFIRM_PASSWORD_SELECTORS, password, "Confirm Password")
        else:
            logger.info("Confirm password field does not seem to exist or is not visible. Skipping.")

    def check_terms(self) -> None:
        logger.info("Clicking the terms checkbox/button (#remember)...")
        self.page.locator("#remember").click(timeout=10000, force=True)

    def submit_signup(self) -> None:
        self._click_fallback(self.SIGNUP_BUTTON_SELECTORS, "Sign Up Submit Button")
        # Fallback: if we are still on the signup page after a brief wait, press Enter on confirmPassword field
        self.page.wait_for_timeout(1500)
        if "/sign-up" in self.page.url:
            logger.info("Still on signup page after submit click, attempting Enter press on confirmPassword field...")
            try:
                self.page.locator("#confirmPassword").press("Enter")
            except Exception as e:
                logger.debug(f"Failed to press Enter on confirmPassword: {e}")
