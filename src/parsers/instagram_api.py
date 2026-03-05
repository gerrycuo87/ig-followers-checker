"""
Instagram API client wrapper with authentication and error handling.
"""
import logging
import os
from typing import List, Tuple

from instagrapi import Client
from instagrapi.exceptions import (
    ClientError,
    ChallengeRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
)

from ..config import (
    SESSION_FILE,
    MIN_DELAY,
    MAX_DELAY,
    DEVICE_SETTINGS,
    FOLLOWING_BATCH_SIZE,
    FOLLOWERS_BATCH_SIZE,
)

logger = logging.getLogger(__name__)


class InstagramClient:
    """Handles all Instagram API interactions with error handling."""

    def __init__(self):
        """Initialize Instagram client with configuration."""
        self.client = Client()
        self._configure_client()
        self.logged_in = False
        self.username = None

    def _configure_client(self):
        """Configure client settings for rate limiting and device mimicking."""
        # Conservative delay range to avoid rate limiting
        self.client.delay_range = [MIN_DELAY, MAX_DELAY]

        # Configure device settings to mimic a real device
        self.client.set_device(DEVICE_SETTINGS)

    def login(self, username: str, password: str) -> bool:
        """
        Login to Instagram with session persistence.

        Args:
            username: Instagram username
            password: Instagram password

        Returns:
            True if login successful

        Raises:
            Exception: On login failure
        """
        self.username = username

        # Try to load existing session
        if os.path.exists(SESSION_FILE):
            logger.info("Found existing session file, attempting to reuse...")
            try:
                self.client.load_settings(SESSION_FILE)
                self.client.login(username, password)

                # Verify session is still valid
                self.client.get_timeline_feed()
                logger.info("Successfully logged in using saved session!")
                self.logged_in = True
                return True
            except Exception as e:
                logger.warning(f"Saved session invalid, performing fresh login. Error: {e}")
                os.remove(SESSION_FILE)

        # Fresh login
        try:
            logger.info("Logging in to Instagram...")
            self.client.login(username, password)

            # Verify session is actually working
            logger.info("Verifying session...")
            self.client.get_timeline_feed()

            # Save session for future use
            self.client.dump_settings(SESSION_FILE)
            logger.info("Successfully logged in and saved session!")
            self.logged_in = True
            return True

        except (ClientError, ChallengeRequired, LoginRequired, PleaseWaitFewMinutes) as e:
            self._handle_login_error(e)
            raise

        except Exception as e:
            logger.error(f"Unexpected error during login: {e}")
            raise

    def _handle_login_error(self, e: Exception):
        """
        Handle and display appropriate error messages for login failures.

        Args:
            e: Exception that occurred during login
        """
        error_message = str(e)

        if isinstance(e, PleaseWaitFewMinutes):
            logger.error("=" * 60)
            logger.error("RATE LIMITED - Too many requests")
            logger.error("Instagram has temporarily blocked your account from making requests.")
            logger.error("WHAT THIS MEANS:")
            logger.error("- You've made too many login attempts or API requests")
            logger.error("- Despite the error saying 'few minutes', you likely need to wait 6-24 hours")
            logger.error("WHAT TO DO:")
            logger.error("1. Stop running the script immediately")
            logger.error("2. Wait at least 6-24 hours before trying again")
            logger.error("3. Use a dedicated test account (not your main account)")
            logger.error("4. Run the script max 1-2 times per day when it works")
            logger.error("=" * 60)
        elif "challenge_required" in error_message or isinstance(e, ChallengeRequired):
            logger.error("=" * 60)
            logger.error("INSTAGRAM SECURITY CHALLENGE REQUIRED")
            logger.error("Your account has been flagged for verification.")
            logger.error("WHAT TO DO NOW:")
            logger.error("1. Open the Instagram app on your phone")
            logger.error("2. Complete the security verification challenge")
            logger.error("3. Wait 6-24 hours before running this script again")
            logger.error("4. Consider using a dedicated test account instead")
            logger.error("WHY THIS HAPPENED:")
            logger.error("- Instagram detected automated activity")
            logger.error("- Too many requests in short time")
            logger.error("- Using automation tools triggers their anti-bot system")
            logger.error("BEST PRACTICE:")
            logger.error("- Use a throwaway/test account for automation")
            logger.error("- Wait longer between script runs (24+ hours)")
            logger.error("- Run the script less frequently")
            logger.error("=" * 60)
        else:
            logger.error(f"Login failed: {error_message}")
            logger.error("Possible solutions:")
            logger.error("1. Wait 2-6 hours (Instagram may have rate-limited you)")
            logger.error("2. Verify your credentials are correct")
            logger.error("3. Try logging in via the Instagram app first")
            logger.error("4. Check if your account requires 2FA verification")

    def get_user_info(self, username: str):
        """
        Fetch user information by username.

        Args:
            username: Instagram username

        Returns:
            User information object

        Raises:
            Exception: On API error
        """
        try:
            user_info = self.client.user_info_by_username_v1(username)
            return user_info
        except (ClientError, ChallengeRequired, LoginRequired, PleaseWaitFewMinutes) as e:
            self._handle_api_error(e, "fetch user information")
            raise

    def fetch_following_batch(
        self, user_id: str, cursor: str = "", limit: int = FOLLOWING_BATCH_SIZE
    ) -> Tuple[List, str]:
        """
        Fetch a batch of following accounts with pagination support.

        Args:
            user_id: Instagram user ID
            cursor: Pagination cursor (max_id)
            limit: Maximum number of following to fetch

        Returns:
            Tuple of (list of users, next_cursor)

        Raises:
            Exception: On API error
        """
        try:
            # Use user_following_v1_chunk for pagination support
            users, next_cursor = self.client.user_following_v1_chunk(
                user_id, max_amount=limit, max_id=cursor
            )
            return users, next_cursor
        except (ClientError, ChallengeRequired, LoginRequired, PleaseWaitFewMinutes) as e:
            self._handle_api_error(e, "fetch following list")
            raise

    def fetch_followers_batch(
        self, user_id: str, cursor: str = "", limit: int = FOLLOWERS_BATCH_SIZE
    ) -> Tuple[List, str]:
        """
        Fetch a batch of followers with pagination support.

        Args:
            user_id: Instagram user ID
            cursor: Pagination cursor (max_id)
            limit: Maximum number of followers to fetch

        Returns:
            Tuple of (list of users, next_cursor)

        Raises:
            Exception: On API error
        """
        try:
            # Use user_followers_v1_chunk for pagination support
            users, next_cursor = self.client.user_followers_v1_chunk(
                user_id, max_amount=limit, max_id=cursor
            )
            return users, next_cursor
        except (ClientError, ChallengeRequired, LoginRequired, PleaseWaitFewMinutes) as e:
            self._handle_api_error(e, "fetch followers list")
            raise

    def _handle_api_error(self, e: Exception, operation: str):
        """
        Handle and display appropriate error messages for API failures.

        Args:
            e: Exception that occurred
            operation: Description of the operation that failed
        """
        if isinstance(e, PleaseWaitFewMinutes):
            logger.error("=" * 60)
            logger.error("RATE LIMITED - Too many requests")
            logger.error(f"Failed to {operation} - Instagram blocked your request.")
            logger.error("Instagram says 'wait a few minutes' but you likely need to wait 6-24 hours.")
            logger.error("This happened because:")
            logger.error("- You've been running the script too frequently")
            logger.error("- Instagram detected automated activity")
            logger.error("Next steps:")
            logger.error("1. STOP running the script now")
            logger.error("2. Wait 6-24 hours minimum")
            logger.error("3. When you retry, only run the script 1-2 times per day maximum")
            logger.error("4. Consider using a dedicated test account")
            logger.error("=" * 60)
        elif "challenge_required" in str(e) or isinstance(e, ChallengeRequired):
            logger.error("=" * 60)
            logger.error("CHALLENGE REQUIRED - Account verification needed")
            logger.error("Your account has been flagged. Wait 6-24 hours.")
            logger.error("=" * 60)
        elif isinstance(e, LoginRequired):
            logger.error("=" * 60)
            logger.error("LOGIN REQUIRED - Session expired or not authenticated")
            logger.error(f"Failed to {operation} - session may have expired.")
            logger.error("Delete session.json and try again after 6-24 hours.")
            logger.error("=" * 60)
        else:
            logger.error(f"Failed to {operation}: {e}")
            logger.error("This usually means Instagram has rate-limited your account.")
            logger.error("Wait 6-24 hours before trying again.")
