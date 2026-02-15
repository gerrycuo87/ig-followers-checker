"""
Analysis comparison for Instagram Followers Checker.

Compares two Analysis snapshots and surfaces what changed between them.
"""
from dataclasses import dataclass, field
from typing import List

from ..models import Analysis, User


@dataclass
class ComparisonResult:
    """Differences between two analyses."""
    earlier: Analysis
    later: Analysis
    days_between: int

    new_followers: List[User] = field(default_factory=list)       # Gained since earlier
    lost_followers: List[User] = field(default_factory=list)      # Unfollowed you
    new_following: List[User] = field(default_factory=list)       # You newly followed
    unfollowed_by_you: List[User] = field(default_factory=list)   # You unfollowed
    new_not_following_back: List[User] = field(default_factory=list)  # Newly non-reciprocal


class AnalysisComparator:
    """Compare two Analysis snapshots and return a ComparisonResult."""

    def compare(self, earlier: Analysis, later: Analysis) -> ComparisonResult:
        """
        Compare an earlier analysis against a later one.

        Args:
            earlier: The older analysis snapshot.
            later:   The more recent analysis snapshot.

        Returns:
            ComparisonResult with all difference lists populated.
        """
        delta = (later.analysis_date - earlier.analysis_date).days

        earlier_followers = {u.username for u in earlier.followers}
        later_followers   = {u.username for u in later.followers}

        earlier_following = {u.username for u in earlier.following}
        later_following   = {u.username for u in later.following}

        earlier_nfb = {u.username for u in earlier.not_following_back}
        later_nfb   = {u.username for u in later.not_following_back}

        # Build lookup maps from the *later* analysis for user objects
        later_followers_map  = {u.username: u for u in later.followers}
        later_following_map  = {u.username: u for u in later.following}

        # Build lookup maps from the *earlier* analysis for lost entries
        earlier_followers_map = {u.username: u for u in earlier.followers}
        earlier_following_map = {u.username: u for u in earlier.following}

        new_followers = [
            later_followers_map[u] for u in (later_followers - earlier_followers)
        ]
        lost_followers = [
            earlier_followers_map[u] for u in (earlier_followers - later_followers)
        ]
        new_following = [
            later_following_map[u] for u in (later_following - earlier_following)
        ]
        unfollowed_by_you = [
            earlier_following_map[u] for u in (earlier_following - later_following)
        ]
        new_not_following_back = [
            later_following_map[u]
            for u in (later_nfb - earlier_nfb)
            if u in later_following_map
        ]

        return ComparisonResult(
            earlier=earlier,
            later=later,
            days_between=delta,
            new_followers=sorted(new_followers, key=lambda u: u.username),
            lost_followers=sorted(lost_followers, key=lambda u: u.username),
            new_following=sorted(new_following, key=lambda u: u.username),
            unfollowed_by_you=sorted(unfollowed_by_you, key=lambda u: u.username),
            new_not_following_back=sorted(new_not_following_back, key=lambda u: u.username),
        )
