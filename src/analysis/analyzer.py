"""
Pure follower analysis engine.

This module contains the core comparison logic for analyzing follower relationships.
It works with standardized User lists from any parser (manual export or API).
"""
from datetime import datetime
from typing import List, Dict, Any
import logging

from ..models import User, Analysis

logger = logging.getLogger(__name__)


class FollowerAnalyzer:
    """
    Pure analysis engine for follower relationships.

    This class performs comparisons between followers and following lists to identify:
    - Accounts that don't follow you back
    - Mutual followers (both follow each other)
    - Fans (follow you but you don't follow them)

    This analyzer is parser-agnostic - it works with User lists from both
    manual export and API parsers.
    """

    def __init__(self):
        """Initialize the analyzer."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def analyze(
        self,
        followers: List[User],
        following: List[User],
        target_username: str,
        source: str = "unknown"
    ) -> Analysis:
        """
        Perform complete follower analysis.

        Args:
            followers: List of User objects representing accounts that follow the target
            following: List of User objects representing accounts the target follows
            target_username: Username being analyzed
            source: Source of the data ("manual_export" or "api")

        Returns:
            Analysis object containing all results and statistics
        """
        self.logger.info(
            f"Starting analysis for @{target_username}: "
            f"{len(followers)} followers, {len(following)} following"
        )

        # Perform comparisons
        not_following_back = self.not_following_back(followers, following)
        mutual_followers = self.mutual_followers(followers, following)
        fans = self.fans(followers, following)

        # Calculate statistics
        statistics = self.calculate_statistics(
            followers, following, not_following_back, mutual_followers, fans
        )

        # Create analysis object
        analysis = Analysis(
            analysis_date=datetime.now(),
            target_username=target_username,
            following=following,
            followers=followers,
            not_following_back=not_following_back,
            mutual_followers=mutual_followers,
            fans=fans,
            statistics=statistics,
            source=source,
        )

        self.logger.info(
            f"Analysis complete: {len(not_following_back)} not following back, "
            f"{len(mutual_followers)} mutual, {len(fans)} fans"
        )

        return analysis

    def not_following_back(self, followers: List[User], following: List[User]) -> List[User]:
        """
        Find accounts you follow but don't follow you back.

        Args:
            followers: List of accounts that follow you
            following: List of accounts you follow

        Returns:
            List of User objects representing accounts not following back
        """
        # Create set of follower usernames for fast lookup
        follower_usernames = {user.username.lower() for user in followers}

        # Find following accounts not in followers
        not_following_back = [
            user for user in following
            if user.username.lower() not in follower_usernames
        ]

        self.logger.debug(f"Found {len(not_following_back)} accounts not following back")
        return not_following_back

    def mutual_followers(self, followers: List[User], following: List[User]) -> List[User]:
        """
        Find accounts that follow each other (mutual followers).

        Args:
            followers: List of accounts that follow you
            following: List of accounts you follow

        Returns:
            List of User objects representing mutual followers
        """
        # Create set of follower usernames for fast lookup
        follower_usernames = {user.username.lower() for user in followers}

        # Find following accounts that are also followers
        mutual = [
            user for user in following
            if user.username.lower() in follower_usernames
        ]

        self.logger.debug(f"Found {len(mutual)} mutual followers")
        return mutual

    def fans(self, followers: List[User], following: List[User]) -> List[User]:
        """
        Find accounts that follow you but you don't follow back (fans).

        Args:
            followers: List of accounts that follow you
            following: List of accounts you follow

        Returns:
            List of User objects representing fans
        """
        # Create set of following usernames for fast lookup
        following_usernames = {user.username.lower() for user in following}

        # Find followers not in following
        fans = [
            user for user in followers
            if user.username.lower() not in following_usernames
        ]

        self.logger.debug(f"Found {len(fans)} fans")
        return fans

    def calculate_statistics(
        self,
        followers: List[User],
        following: List[User],
        not_following_back: List[User],
        mutual_followers: List[User],
        fans: List[User]
    ) -> Dict[str, Any]:
        """
        Calculate various statistics from the analysis.

        Args:
            followers: All followers
            following: All following
            not_following_back: Users not following back
            mutual_followers: Mutual followers
            fans: Fans

        Returns:
            Dictionary containing calculated statistics
        """
        total_followers = len(followers)
        total_following = len(following)

        # Avoid division by zero
        follow_ratio = total_followers / total_following if total_following > 0 else 0
        mutual_ratio = len(mutual_followers) / total_following if total_following > 0 else 0
        not_following_back_ratio = len(not_following_back) / total_following if total_following > 0 else 0
        fan_ratio = len(fans) / total_followers if total_followers > 0 else 0

        # Extended statistics (only available if users have extended fields from API)
        verified_not_following_back = sum(
            1 for user in not_following_back if user.is_verified
        )

        large_accounts_not_following_back = sum(
            1 for user in not_following_back
            if user.follower_count and user.follower_count >= 10000
        )

        private_accounts_not_following_back = sum(
            1 for user in not_following_back if user.is_private
        )

        statistics = {
            # Counts
            'total_followers': total_followers,
            'total_following': total_following,
            'not_following_back_count': len(not_following_back),
            'mutual_followers_count': len(mutual_followers),
            'fans_count': len(fans),

            # Ratios
            'follower_following_ratio': round(follow_ratio, 2),
            'mutual_ratio': round(mutual_ratio, 4),
            'not_following_back_ratio': round(not_following_back_ratio, 4),
            'fan_ratio': round(fan_ratio, 4),

            # Percentages (more readable)
            'not_following_back_percentage': round(not_following_back_ratio * 100, 2),
            'mutual_percentage': round(mutual_ratio * 100, 2),
            'fan_percentage': round(fan_ratio * 100, 2),

            # Extended stats (may be 0 if using manual export mode)
            'verified_not_following_back': verified_not_following_back,
            'large_accounts_not_following_back': large_accounts_not_following_back,
            'private_accounts_not_following_back': private_accounts_not_following_back,
        }

        return statistics

    def sort_by_follower_count(self, users: List[User], reverse: bool = True) -> List[User]:
        """
        Sort users by follower count (if available).

        Args:
            users: List of User objects
            reverse: If True, sort descending (highest first)

        Returns:
            Sorted list of users (users without follower_count are placed last)
        """
        # Separate users with and without follower count
        with_count = [u for u in users if u.follower_count is not None]
        without_count = [u for u in users if u.follower_count is None]

        # Sort users with count
        with_count.sort(key=lambda u: u.follower_count, reverse=reverse)

        # Return combined list
        return with_count + without_count

    def filter_verified(self, users: List[User]) -> List[User]:
        """
        Filter to only verified users.

        Args:
            users: List of User objects

        Returns:
            List containing only verified users
        """
        return [user for user in users if user.is_verified]

    def filter_by_follower_count(
        self,
        users: List[User],
        min_count: int = 0,
        max_count: int = None
    ) -> List[User]:
        """
        Filter users by follower count range.

        Args:
            users: List of User objects
            min_count: Minimum follower count (inclusive)
            max_count: Maximum follower count (inclusive), None for no limit

        Returns:
            Filtered list of users
        """
        filtered = []
        for user in users:
            if user.follower_count is None:
                continue
            if user.follower_count < min_count:
                continue
            if max_count is not None and user.follower_count > max_count:
                continue
            filtered.append(user)

        return filtered
