from instagrapi import Client
from instagrapi.exceptions import (
    ClientError,
    ChallengeRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
)
import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple

# Configuration Constants
SESSION_FILE = "session.json"
CACHE_DIR = Path("cache")
MIN_DELAY = 2  # Minimum delay between requests (seconds)
MAX_DELAY = 5  # Maximum delay between requests (seconds)
OPERATION_COOLDOWN = 3  # Delay between major operations (seconds)
FOLLOWING_BATCH_SIZE = 0  # 0 = fetch all following in one go (usually small enough)
FOLLOWERS_BATCH_SIZE = 500  # Fetch followers in batches to avoid rate limiting

# Ensure cache directory exists
CACHE_DIR.mkdir(exist_ok=True)


# ============================================================================
# CacheManager Class - Handles all cache/persistence operations
# ============================================================================
class CacheManager:
    """Manages progress caching and persistence to JSON files."""

    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_path(self, username: str) -> Path:
        """Get the cache file path for a given username."""
        return self.cache_dir / f"{username}_progress.json"

    def load_progress(self, username: str) -> Optional[Dict]:
        """Load progress from cache file if it exists."""
        cache_path = self.get_cache_path(username)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load cache file: {e}")
                return None
        return None

    def save_progress(self, username: str, progress_data: Dict) -> None:
        """Save progress to cache file."""
        cache_path = self.get_cache_path(username)
        try:
            # Add timestamp
            progress_data["last_updated"] = datetime.now().isoformat()

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
            print(f"      ✓ Progress saved to {cache_path}")
        except Exception as e:
            print(f"Warning: Could not save progress: {e}")

    @staticmethod
    def user_to_dict(user) -> Dict:
        """Convert instagrapi User object to dictionary for JSON serialization."""
        return {
            "pk": str(user.pk),
            "username": user.username,
            "full_name": user.full_name,
            "profile_pic_url": getattr(user, "profile_pic_url", ""),
            "is_verified": getattr(user, "is_verified", False),
            "is_private": getattr(user, "is_private", False),
        }

    def create_empty_progress(self, username: str, user_id: str) -> Dict:
        """Create empty progress structure for a new analysis."""
        return {
            "target_username": username,
            "target_user_id": str(user_id),
            "following": {
                "complete": False,
                "count": 0,
                "data": {},
            },
            "followers": {
                "complete": False,
                "count": 0,
                "data": {},
                "next_cursor": "",
            },
        }


# ============================================================================
# InstagramClient Class - Wraps Instagram API interactions
# ============================================================================
class InstagramClient:
    """Handles all Instagram API interactions with error handling."""

    def __init__(self):
        self.client = Client()
        self._configure_client()
        self.logged_in = False
        self.username = None

    def _configure_client(self):
        """Configure client settings for rate limiting and device mimicking."""
        # Conservative delay range to avoid rate limiting
        self.client.delay_range = [MIN_DELAY, MAX_DELAY]

        # Configure device settings to mimic a real device
        self.client.set_device({
            "app_version": "269.0.0.18.75",
            "android_version": 26,
            "android_release": "8.0.0",
            "dpi": "480dpi",
            "resolution": "1080x1920",
            "manufacturer": "OnePlus",
            "device": "ONEPLUS A3003",
            "model": "OnePlus3",
            "cpu": "qcom"
        })

    def login(self, username: str, password: str) -> bool:
        """
        Login to Instagram with session persistence.
        Returns True if login successful, raises exception on failure.
        """
        self.username = username

        # Try to load existing session
        if os.path.exists(SESSION_FILE):
            print("Found existing session file, attempting to reuse...")
            try:
                self.client.load_settings(SESSION_FILE)
                self.client.login(username, password)

                # Verify session is still valid
                self.client.get_timeline_feed()
                print("Successfully logged in using saved session!")
                self.logged_in = True
                return True
            except Exception as e:
                print(f"Saved session invalid, performing fresh login. Error: {e}")
                os.remove(SESSION_FILE)

        # Fresh login
        try:
            print("Logging in to Instagram...")
            self.client.login(username, password)

            # Verify session is actually working
            print("Verifying session...")
            self.client.get_timeline_feed()

            # Save session for future use
            self.client.dump_settings(SESSION_FILE)
            print("Successfully logged in and saved session!")
            self.logged_in = True
            return True

        except (ClientError, ChallengeRequired, LoginRequired, PleaseWaitFewMinutes) as e:
            self._handle_login_error(e)
            raise

        except Exception as e:
            print(f"Unexpected error during login: {e}")
            raise

    def _handle_login_error(self, e: Exception):
        """Handle and display appropriate error messages for login failures."""
        error_message = str(e)

        if isinstance(e, PleaseWaitFewMinutes):
            print("\n" + "!" * 60)
            print("RATE LIMITED - Too many requests")
            print("!" * 60)
            print("\nInstagram has temporarily blocked your account from making requests.")
            print("\nWHAT THIS MEANS:")
            print("- You've made too many login attempts or API requests")
            print("- Despite the error saying 'few minutes', you likely need to wait 6-24 hours")
            print("\nWHAT TO DO:")
            print("1. Stop running the script immediately")
            print("2. Wait at least 6-24 hours before trying again")
            print("3. Use a dedicated test account (not your main account)")
            print("4. Run the script max 1-2 times per day when it works")
            print("!" * 60)
        elif "challenge_required" in error_message or isinstance(e, ChallengeRequired):
            print("\n" + "!" * 60)
            print("INSTAGRAM SECURITY CHALLENGE REQUIRED")
            print("!" * 60)
            print("\nYour account has been flagged for verification.")
            print("\nWHAT TO DO NOW:")
            print("1. Open the Instagram app on your phone")
            print("2. Complete the security verification challenge")
            print("3. Wait 6-24 hours before running this script again")
            print("4. Consider using a dedicated test account instead")
            print("\nWHY THIS HAPPENED:")
            print("- Instagram detected automated activity")
            print("- Too many requests in short time")
            print("- Using automation tools triggers their anti-bot system")
            print("\nBEST PRACTICE:")
            print("- Use a throwaway/test account for automation")
            print("- Wait longer between script runs (24+ hours)")
            print("- Run the script less frequently")
            print("!" * 60)
        else:
            print(f"\nLogin failed: {error_message}")
            print("\nPossible solutions:")
            print("1. Wait 2-6 hours (Instagram may have rate-limited you)")
            print("2. Verify your credentials are correct")
            print("3. Try logging in via the Instagram app first")
            print("4. Check if your account requires 2FA verification")

    def get_user_info(self, username: str):
        """Fetch user information by username."""
        try:
            user_info = self.client.user_info_by_username_v1(username)
            return user_info
        except (ClientError, ChallengeRequired, LoginRequired, PleaseWaitFewMinutes) as e:
            self._handle_api_error(e, "fetch user information")
            raise

    def fetch_following_complete(self, user_id: str) -> List:
        """Fetch complete following list for a user."""
        try:
            following_list = self.client.user_following_v1(user_id, amount=FOLLOWING_BATCH_SIZE)
            return following_list
        except (ClientError, ChallengeRequired, LoginRequired, PleaseWaitFewMinutes) as e:
            self._handle_api_error(e, "fetch following list")
            raise

    def fetch_followers_batch(self, user_id: str, cursor: str = "", limit: int = FOLLOWERS_BATCH_SIZE) -> Tuple[List, str]:
        """
        Fetch a batch of followers with pagination support.
        Returns: (list of users, next_cursor)
        TODO: Implement in Step 2
        """
        # Placeholder for Step 2 implementation
        raise NotImplementedError("Incremental followers fetching will be implemented in Step 2")

    def _handle_api_error(self, e: Exception, operation: str):
        """Handle and display appropriate error messages for API failures."""
        if isinstance(e, PleaseWaitFewMinutes):
            print("\n" + "!" * 60)
            print("RATE LIMITED - Too many requests")
            print("!" * 60)
            print(f"\nFailed to {operation} - Instagram blocked your request.")
            print("\nInstagram says 'wait a few minutes' but you likely need to wait 6-24 hours.")
            print("\nThis happened because:")
            print("- You've been running the script too frequently")
            print("- Instagram detected automated activity")
            print("\nNext steps:")
            print("1. STOP running the script now")
            print("2. Wait 6-24 hours minimum")
            print("3. When you retry, only run the script 1-2 times per day maximum")
            print("4. Consider using a dedicated test account")
            print("!" * 60)
        elif "challenge_required" in str(e) or isinstance(e, ChallengeRequired):
            print("\n" + "!" * 60)
            print("CHALLENGE REQUIRED - Account verification needed")
            print("!" * 60)
            print("Your account has been flagged. Wait 6-24 hours.")
            print("!" * 60)
        elif isinstance(e, LoginRequired):
            print("\n" + "!" * 60)
            print("LOGIN REQUIRED - Session expired or not authenticated")
            print("!" * 60)
            print(f"Failed to {operation} - session may have expired.")
            print("Delete session.json and try again after 6-24 hours.")
            print("!" * 60)
        else:
            print(f"Failed to {operation}: {e}")
            print("This usually means Instagram has rate-limited your account.")
            print("Wait 6-24 hours before trying again.")


# ============================================================================
# FollowerAnalyzer Class - Main orchestration and analysis logic
# ============================================================================
class FollowerAnalyzer:
    """Orchestrates the Instagram follower analysis workflow."""

    def __init__(self, cache_manager: CacheManager, ig_client: InstagramClient):
        self.cache = cache_manager
        self.client = ig_client

    def run_analysis(self, target_username: str) -> None:
        """Run the complete analysis workflow."""
        # Get user information
        print(f"\n[1/3] Fetching user information for @{target_username}...")
        time.sleep(OPERATION_COOLDOWN)

        user_info = self.client.get_user_info(target_username)
        user_id = str(user_info.pk)
        print(f"      Found user: {user_info.full_name} (@{user_info.username})")

        time.sleep(OPERATION_COOLDOWN)

        # Load or create progress
        print(f"\nChecking for existing progress for @{target_username}...")
        progress = self.cache.load_progress(target_username)

        if progress:
            print(f"      ✓ Found existing progress from {progress.get('last_updated', 'unknown')}")
        else:
            print("      No existing progress found, starting fresh analysis")
            progress = self.cache.create_empty_progress(target_username, user_id)

        # STEP 1: Fetch FOLLOWING list
        self._fetch_following(target_username, user_id, progress)

        # STEP 2: Fetch FOLLOWERS list (incremental - will be implemented next)
        self._fetch_followers_incremental(target_username, user_id, progress)

        # Display final status
        self._display_status(progress)

    def _fetch_following(self, username: str, user_id: str, progress: Dict) -> None:
        """Fetch complete following list (Step 1)."""
        print("\n" + "=" * 60)
        print("[2/3]: Fetching FOLLOWING List")
        print("=" * 60)

        if progress["following"]["complete"]:
            print(f"✓ Following list already complete ({progress['following']['count']} accounts)")
            return

        print("Fetching your following list (this is usually quick)...")
        following_list = self.client.fetch_following_complete(user_id)

        # Convert to dictionary keyed by user_id
        following_dict = {
            str(user.pk): self.cache.user_to_dict(user)
            for user in following_list
        }

        # Update progress
        progress["following"]["data"] = following_dict
        progress["following"]["count"] = len(following_dict)
        progress["following"]["complete"] = True

        print(f"      ✓ Following list complete: {len(following_dict)} accounts")

        # Save progress
        self.cache.save_progress(username, progress)

    def _fetch_followers_incremental(self, username: str, user_id: str, progress: Dict) -> None:
        """Fetch followers incrementally (Step 2 - to be implemented)."""
        print("\n" + "=" * 60)
        print("[3/3]: Fetching FOLLOWERS List (Incremental)")
        print("=" * 60)
        print("⚠ NOTE: Incremental followers fetching will be implemented in Step 2")
        print("For now, following list fetch is complete and working!")

    def _display_status(self, progress: Dict) -> None:
        """Display current analysis status."""
        print("\n" + "=" * 60)
        print("STEP 1 COMPLETE!")
        print("=" * 60)
        print(f"✓ Following list: {progress['following']['count']} accounts")
        print(f"✓ Progress saved to: {self.cache.get_cache_path(progress['target_username'])}")
        print("\nNext steps:")
        print("1. Verify the cache file was created successfully")
        print("2. Check that the following data is correctly stored")
        print("3. Prepare for Step 2: Incremental followers fetching")
        print("=" * 60)


# ============================================================================
# Main Entry Point
# ============================================================================
def print_welcome():
    """Display welcome message and important notes."""
    print("=" * 60)
    print("Instagram Followers Checker - Incremental Mode")
    print("=" * 60)
    print("\nIMPORTANT NOTES:")
    print("- Use a dedicated/test account (not your personal account)")
    print("- This tool fetches data incrementally over multiple days")
    print("- Run once per day to avoid rate limiting")
    print("- You'll get results immediately, improving with each run")
    print("=" * 60)
    print()


def get_credentials() -> Tuple[str, str]:
    """Get Instagram credentials from user input."""
    username = input("Enter your Instagram username: ")
    password = input("Enter your Instagram password: ")
    return username, password


def get_target_username(default_username: str) -> str:
    """Get target username to analyze."""
    target = input(
        "Enter the profile name you want to double check (leave blank if you want to check your own profile): "
    )
    return target or default_username


def main():
    """Main entry point for the Instagram Followers Checker."""
    # Display welcome message
    print_welcome()

    # Initialize components
    cache_manager = CacheManager()
    ig_client = InstagramClient()
    analyzer = FollowerAnalyzer(cache_manager, ig_client)

    try:
        # Get credentials and login
        username, password = get_credentials()
        ig_client.login(username, password)

        if not ig_client.logged_in:
            print("Failed to establish Instagram session. Exiting.")
            return 1

        # Get target username
        print()
        target_username = get_target_username(username)

        # Run analysis
        analyzer.run_analysis(target_username)

        return 0

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 130
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
