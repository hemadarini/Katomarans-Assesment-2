import logging
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        logger.info("Navigating to login page...")
        page.goto("https://tichi-app-webapp-stage.web.app/login")
        
        # Enter a non-existing email to go to signup
        email = "test_dump_dom_123@throwawaymail.app"
        logger.info(f"Entering email: {email}")
        page.fill("input[type='email']", email)
        page.click("button:has-text('Continue')")
        
        logger.info("Waiting for redirect to signup page...")
        page.wait_for_url("**/sign-up**", timeout=15000)
        logger.info(f"Current URL: {page.url}")
        
        # Wait for inputs to be loaded
        page.wait_for_timeout(3000)
        
        # Dump all inputs
        inputs = page.locator("input").all()
        logger.info(f"Found {len(inputs)} inputs:")
        for idx, ip in enumerate(inputs):
            outer_html = ip.evaluate("el => el.outerHTML")
            logger.info(f"Input {idx}: {outer_html}")
            
        # Dump all buttons
        buttons = page.locator("button").all()
        logger.info(f"Found {len(buttons)} buttons:")
        for idx, btn in enumerate(buttons):
            outer_html = btn.evaluate("el => el.outerHTML")
            logger.info(f"Button {idx}: {outer_html}")
            
        browser.close()

if __name__ == "__main__":
    main()
