import logging
import re
import time
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://throwawaymail.app/api"

class EmailService:
    @staticmethod
    def create_mailbox() -> tuple[str, str]:
        """
        Creates a temporary mailbox.
        Returns:
            Tuple of (mailbox_id, email_address)
        """
        url = f"{BASE_URL}/mailboxes"
        logger.info(f"Creating a new temporary mailbox at {url}...")
        try:
            response = requests.post(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            mailbox_id = data.get("mailbox_id") or data.get("id")
            address = data.get("address")
            if not mailbox_id or not address:
                raise ValueError(f"Invalid mailbox response structure: {data}")
            logger.info(f"Mailbox created successfully. ID: {mailbox_id}, Address: {address}")
            return mailbox_id, address
        except Exception as e:
            logger.error(f"Failed to create temporary mailbox: {e}")
            raise

    @staticmethod
    def poll_messages(mailbox_id: str, max_attempts: int = 12, interval_sec: int = 5) -> list[dict]:
        """
        Polls the mailbox messages endpoint every `interval_sec` seconds.
        Returns:
            List of messages when found (with details populated).
        Raises:
            TimeoutError: If no message arrives after max_attempts.
        """
        url = f"{BASE_URL}/mailboxes/{mailbox_id}/messages"
        logger.info(f"Polling messages from {url} (Attempts: {max_attempts}, Interval: {interval_sec}s)...")
        
        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                messages = response.json()
                
                msg_list = []
                if isinstance(messages, list) and len(messages) > 0:
                    msg_list = messages
                elif isinstance(messages, dict) and messages.get("messages"):
                    msg_list = messages.get("messages")
                
                if len(msg_list) > 0:
                    logger.info(f"Message received on attempt {attempt}/{max_attempts}!")
                    # Automatically fetch details for the first message to get the HTML/body content
                    first_msg = msg_list[0]
                    msg_id = first_msg.get("id") or first_msg.get("message_id")
                    if msg_id:
                        detail_url = f"{BASE_URL}/mailboxes/{mailbox_id}/messages/{msg_id}"
                        logger.info(f"Fetching full message detail from {detail_url}...")
                        detail_resp = requests.get(detail_url, timeout=10)
                        if detail_resp.status_code == 200:
                            # Return detailed message in a list for compatibility
                            return [detail_resp.json()]
                        else:
                            logger.warning(f"Failed to fetch message detail: {detail_resp.text}")
                    return msg_list
                
                logger.info(f"Attempt {attempt}/{max_attempts}: No messages yet. Retrying in {interval_sec}s...")
            except Exception as e:
                logger.warning(f"Attempt {attempt}/{max_attempts} failed with error: {e}. Retrying...")
            
            time.sleep(interval_sec)
            
        raise TimeoutError(f"No messages received for mailbox {mailbox_id} after {max_attempts * interval_sec} seconds.")

    @staticmethod
    def extract_activation_link(message_body: str) -> str:
        """
        Extracts the activation link from the email body.
        Looks for links matching the tichi-app-webapp-stage domain or similar activation patterns.
        """
        logger.info("Extracting activation link from message body...")
        # Match standard URLs starting with http/https
        links = re.findall(r'https?://[^\s"\'<>]+', message_body)
        logger.debug(f"All links found in email body: {links}")
        
        # Look for the Tichi stage URL or an activation URL
        for link in links:
            # Unescape html entities if any (e.g. &amp; -> &)
            clean_link = link.replace("&amp;", "&")
            if "tichi-app-webapp-stage" in clean_link or "activate" in clean_link or "verify" in clean_link:
                logger.info(f"Found activation/verification link: {clean_link}")
                return clean_link
                
        # If no specific tichi link was matched, try to return the first URL found that looks relevant
        if links:
            clean_link = links[0].replace("&amp;", "&")
            logger.info(f"Fallback to first URL found: {clean_link}")
            return clean_link
            
        raise ValueError("Could not find any activation or verification links in the email body.")
