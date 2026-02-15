"""
User-list filters for Instagram Followers Checker.

Filters work with both manual export and API data. Filters that require
extended metadata (follower count, verified status, private flag) will
emit a clear warning and return an empty list when applied to manual
export data that lacks that information.
"""
import warnings
from datetime import datetime, timezone
from typing import List, Optional

from ..models import User


class AnalysisFilter:
    """
    Filter a list of User objects by various criteria.

    All methods are pure functions — they do not modify the input list.
    Methods that depend on API-only metadata raise a UserWarning when
    the required field is absent from the first user in the list.
    """

    def by_timestamp(self, users: List[User], days: int) -> List[User]:
        """
        Return users whose relationship started within the last *days* days.

        Works with both manual export and API data (both include a timestamp).
        Users without a timestamp are excluded silently.

        Args:
            users: List of User objects to filter.
            days:  Maximum age of the relationship in days.

        Returns:
            Filtered list.
        """
        if not users:
            return []
        cutoff = datetime.now(tz=timezone.utc).timestamp() - days * 86400
        return [u for u in users if u.timestamp is not None and u.timestamp >= cutoff]

    def by_follower_count(
        self,
        users: List[User],
        min_count: int = 0,
        max_count: Optional[int] = None,
    ) -> List[User]:
        """
        Return users whose follower count falls within [min_count, max_count].

        *API mode only* — returns [] with a warning for manual export data.

        Args:
            users:     List of User objects to filter.
            min_count: Lower bound (inclusive). Default 0.
            max_count: Upper bound (inclusive). None means no upper limit.

        Returns:
            Filtered list.
        """
        if not users:
            return []
        if users[0].follower_count is None:
            warnings.warn(
                "by_follower_count requires API mode data. "
                "Manual export does not include follower counts.",
                UserWarning,
                stacklevel=2,
            )
            return []
        result = [u for u in users if u.follower_count is not None and u.follower_count >= min_count]
        if max_count is not None:
            result = [u for u in result if u.follower_count <= max_count]
        return result

    def verified_only(self, users: List[User]) -> List[User]:
        """
        Return only verified accounts.

        *API mode only* — returns [] with a warning for manual export data.

        Args:
            users: List of User objects to filter.

        Returns:
            Filtered list.
        """
        if not users:
            return []
        if users[0].is_verified is None:
            warnings.warn(
                "verified_only requires API mode data. "
                "Manual export does not include verification status.",
                UserWarning,
                stacklevel=2,
            )
            return []
        return [u for u in users if u.is_verified]

    def private_only(self, users: List[User]) -> List[User]:
        """
        Return only private accounts.

        *API mode only* — returns [] with a warning for manual export data.

        Args:
            users: List of User objects to filter.

        Returns:
            Filtered list.
        """
        if not users:
            return []
        if users[0].is_private is None:
            warnings.warn(
                "private_only requires API mode data. "
                "Manual export does not include privacy status.",
                UserWarning,
                stacklevel=2,
            )
            return []
        return [u for u in users if u.is_private]
