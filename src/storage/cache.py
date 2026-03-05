"""
Cache management for Instagram follower analysis progress.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from ..config import CACHE_DIR

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages progress caching and persistence to JSON files."""

    def __init__(self, cache_dir: Path = CACHE_DIR):
        """
        Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)

    def get_cache_path(self, username: str) -> Path:
        """
        Get the cache file path for a given username.

        Args:
            username: Instagram username

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{username}_progress.json"

    def load_progress(self, username: str) -> Optional[Dict]:
        """
        Load progress from cache file if it exists.

        Args:
            username: Instagram username

        Returns:
            Progress dictionary if found, None otherwise
        """
        cache_path = self.get_cache_path(username)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load cache file: {e}")
                return None
        return None

    def save_progress(self, username: str, progress_data: Dict) -> None:
        """
        Save progress to cache file.

        Args:
            username: Instagram username
            progress_data: Progress data dictionary
        """
        cache_path = self.get_cache_path(username)
        try:
            # Add timestamp
            progress_data["last_updated"] = datetime.now().isoformat()

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Progress saved to {cache_path}")
        except Exception as e:
            logger.warning(f"Could not save progress: {e}")

    @staticmethod
    def user_to_dict(user) -> Dict:
        """
        Convert instagrapi User object to dictionary for JSON serialization.

        Args:
            user: instagrapi User object

        Returns:
            Dictionary with user data
        """
        return {
            "pk": str(user.pk),
            "username": user.username,
            "full_name": user.full_name,
            "profile_pic_url": getattr(user, "profile_pic_url", ""),
            "is_verified": getattr(user, "is_verified", False),
            "is_private": getattr(user, "is_private", False),
        }

    def create_empty_progress(self, username: str, user_id: str) -> Dict:
        """
        Create empty progress structure for a new analysis.

        Args:
            username: Instagram username
            user_id: Instagram user ID

        Returns:
            Empty progress dictionary
        """
        return {
            "target_username": username,
            "target_user_id": str(user_id),
            "following": {
                "complete": False,
                "count": 0,
                "data": {},
                "next_cursor": "",
            },
            "followers": {
                "complete": False,
                "count": 0,
                "data": {},
                "next_cursor": "",
            },
        }
