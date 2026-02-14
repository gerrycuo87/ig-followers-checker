"""
Instagram follower analysis orchestration.
"""
import time
from typing import Dict

from .storage.cache import CacheManager
from .parsers.instagram_api import InstagramClient
from .config import OPERATION_COOLDOWN


class FollowerAnalyzer:
    """Orchestrates the Instagram follower analysis workflow."""

    def __init__(self, cache_manager: CacheManager, ig_client: InstagramClient):
        """
        Initialize analyzer with dependencies.

        Args:
            cache_manager: CacheManager instance for persistence
            ig_client: InstagramClient instance for API calls
        """
        self.cache = cache_manager
        self.client = ig_client

    def run_analysis(self, target_username: str) -> None:
        """
        Run the complete analysis workflow.

        Args:
            target_username: Instagram username to analyze
        """
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
        """
        Fetch following list incrementally (Step 1).

        Args:
            username: Instagram username
            user_id: Instagram user ID
            progress: Progress dictionary
        """
        print("\n" + "=" * 60)
        print("[2/3]: Fetching FOLLOWING List (Incremental)")
        print("=" * 60)

        if progress["following"]["complete"]:
            print(f"✓ Following list already complete ({progress['following']['count']} accounts)")
            return

        # Get current state
        current_cursor = progress["following"].get("next_cursor", "")
        current_count = progress["following"]["count"]

        print(f"Fetching @{username}'s following list...")
        if current_count > 0:
            print(f"      Resuming from {current_count} already fetched accounts")

        # Fetch next batch
        following_batch, next_cursor = self.client.fetch_following_batch(user_id, cursor=current_cursor)

        # Convert to dictionary and merge with existing data
        following_dict = progress["following"]["data"]
        for user in following_batch:
            following_dict[str(user.pk)] = self.cache.user_to_dict(user)

        # Update progress
        progress["following"]["data"] = following_dict
        progress["following"]["count"] = len(following_dict)
        progress["following"]["next_cursor"] = next_cursor if next_cursor else ""
        progress["following"]["complete"] = not next_cursor  # Complete if no more cursor

        # Display progress
        if progress["following"]["complete"]:
            print(f"      ✓ Following list COMPLETE: {len(following_dict)} accounts total")
        else:
            print(f"      ✓ Fetched batch: {len(following_batch)} accounts")
            print(f"      ✓ Total so far: {len(following_dict)} accounts")
            print(f"      ⏳ More following to fetch - run again to continue")

        # Save progress
        self.cache.save_progress(username, progress)

    def _fetch_followers_incremental(self, username: str, user_id: str, progress: Dict) -> None:
        """
        Fetch followers incrementally (Step 2).

        Args:
            username: Instagram username
            user_id: Instagram user ID
            progress: Progress dictionary
        """
        print("\n" + "=" * 60)
        print("[3/3]: Fetching FOLLOWERS List (Incremental)")
        print("=" * 60)

        # Check if followers list is already complete
        if progress["followers"]["complete"]:
            print(f"✓ Followers list already complete ({progress['followers']['count']} accounts)")
            return

        # Check if following list is complete first
        if not progress["following"]["complete"]:
            print("⏳ Waiting for following list to complete first")
            print("   Run the script again to continue fetching following accounts")
            return

        # Get current state
        current_cursor = progress["followers"].get("next_cursor", "")
        current_count = progress["followers"]["count"]

        print(f"Fetching @{username}'s followers list...")
        if current_count > 0:
            print(f"      Resuming from {current_count} already fetched accounts")

        # Fetch next batch
        followers_batch, next_cursor = self.client.fetch_followers_batch(user_id, cursor=current_cursor)

        # Convert to dictionary and merge with existing data
        followers_dict = progress["followers"]["data"]
        for user in followers_batch:
            followers_dict[str(user.pk)] = self.cache.user_to_dict(user)

        # Update progress
        progress["followers"]["data"] = followers_dict
        progress["followers"]["count"] = len(followers_dict)
        progress["followers"]["next_cursor"] = next_cursor if next_cursor else ""
        progress["followers"]["complete"] = not next_cursor  # Complete if no more cursor

        # Display progress
        if progress["followers"]["complete"]:
            print(f"      ✓ Followers list COMPLETE: {len(followers_dict)} accounts total")
        else:
            print(f"      ✓ Fetched batch: {len(followers_batch)} accounts")
            print(f"      ✓ Total so far: {len(followers_dict)} accounts")
            print(f"      ⏳ More followers to fetch - run again to continue")

        # Save progress
        self.cache.save_progress(username, progress)

    def _display_status(self, progress: Dict) -> None:
        """
        Display current analysis status.

        Args:
            progress: Progress dictionary
        """
        print("\n" + "=" * 60)
        print("EXECUTION SUMMARY")
        print("=" * 60)

        # Following status
        following_complete = progress["following"]["complete"]
        following_count = progress["following"]["count"]

        if following_complete:
            print(f"✓ Following list: COMPLETE ({following_count} accounts)")
        else:
            print(f"⏳ Following list: IN PROGRESS ({following_count} accounts fetched so far)")
            print(f"   Run the script again to fetch more following accounts")

        # Followers status (will be updated in Step 2)
        followers_complete = progress["followers"]["complete"]
        followers_count = progress["followers"]["count"]

        if followers_count > 0:
            if followers_complete:
                print(f"✓ Followers list: COMPLETE ({followers_count} accounts)")
            else:
                print(f"⏳ Followers list: IN PROGRESS ({followers_count} accounts fetched so far)")
        else:
            print(f"⏳ Followers list: NOT STARTED (will begin after following is complete)")

        print(f"\n✓ Progress saved to: {self.cache.get_cache_path(progress['target_username'])}")

        if not following_complete:
            print("\n⚠ IMPORTANT: Following list is not yet complete!")
            print("   Run the script again tomorrow to fetch the next batch")
            print("   This helps avoid Instagram rate limiting")
        elif not followers_complete and followers_count == 0:
            print("\nNext: Run again to start fetching followers incrementally")

        print("=" * 60)
