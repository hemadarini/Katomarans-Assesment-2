import logging
from playwright.sync_api import Page, Response, expect

logger = logging.getLogger(__name__)

class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def navigate(self, url: str) -> Response | None:
        logger.info(f"Navigating to {url}")
        return self.page.goto(url)

    def click(self, selector: str, timeout: float = 10000, force: bool = False) -> None:
        logger.info(f"Clicking element: {selector} (force={force})")
        self.page.locator(selector).wait_for(state="visible", timeout=timeout)
        self.page.click(selector, timeout=timeout, force=force)

    def fill(self, selector: str, text: str, timeout: float = 10000) -> None:
        logger.info(f"Filling element: {selector} with value: {text}")
        self.page.locator(selector).wait_for(state="visible", timeout=timeout)
        self.page.fill(selector, text, timeout=timeout)

    def get_text(self, selector: str, timeout: float = 10000) -> str:
        self.page.locator(selector).wait_for(state="visible", timeout=timeout)
        return self.page.locator(selector).inner_text(timeout=timeout)

    def check(self, selector: str, timeout: float = 10000) -> None:
        logger.info(f"Checking checkbox/radio: {selector}")
        self.page.locator(selector).wait_for(state="visible", timeout=timeout)
        self.page.check(selector, timeout=timeout)

    def wait_for_url_contains(self, partial_url: str, timeout: float = 10000) -> None:
        logger.info(f"Waiting for URL to contain: '{partial_url}'")
        self.page.wait_for_url(f"**{partial_url}**", timeout=timeout)

    def is_visible(self, selector: str, timeout: float = 5000) -> bool:
        try:
            self.page.locator(selector).wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False
