"""
Statistics and insights engine for Instagram Followers Checker.

Generates human-readable insight strings from a completed Analysis object.
"""
import logging
from typing import List

from ..models import Analysis

logger = logging.getLogger(__name__)


class InsightsEngine:
    """Generate human-readable insights from an analysis."""

    def generate(self, analysis: Analysis) -> List[str]:
        """
        Return a list of insight strings derived from the analysis.

        All percentages are pre-formatted; no raw numbers are exposed —
        the strings are ready to display directly to the user.

        Args:
            analysis: Completed Analysis object.

        Returns:
            List of insight strings (may be empty if data is insufficient).
        """
        stats = analysis.statistics
        insights: List[str] = []

        total_following = stats.get("total_following", 0)
        total_followers = stats.get("total_followers", 0)
        nfb_count = stats.get("not_following_back_count", 0)
        mutual_count = stats.get("mutual_followers_count", 0)
        fans_count = stats.get("fans_count", 0)
        ratio = stats.get("follower_following_ratio", 0.0)

        if total_following == 0 and total_followers == 0:
            return insights

        # --- Not-following-back rate ---
        if total_following > 0:
            nfb_pct = nfb_count / total_following * 100
            insights.append(
                f"{nfb_pct:.1f}% of accounts you follow don't follow you back "
                f"({nfb_count:,} accounts)"
            )

        # --- Mutual rate ---
        if total_following > 0:
            mutual_pct = mutual_count / total_following * 100
            insights.append(
                f"{mutual_pct:.1f}% of accounts you follow are mutual followers"
            )

        # --- Fans ---
        if fans_count > 0:
            insights.append(
                f"{fans_count:,} account{'s' if fans_count != 1 else ''} follow you "
                f"that you don't follow back"
            )
        elif total_followers > 0:
            insights.append("You follow back everyone who follows you")

        # --- Follower / following ratio ---
        if total_following > 0 and total_followers > 0:
            if ratio >= 5:
                quality = "excellent"
            elif ratio >= 2:
                quality = "healthy"
            elif ratio >= 1:
                quality = "balanced"
            else:
                quality = "you follow more than follow you"
            insights.append(
                f"Your follower / following ratio is {ratio:.2f} : 1 ({quality})"
            )

        # --- Edge cases ---
        if nfb_count == 0 and total_following > 0:
            insights.append("Everyone you follow also follows you back!")

        return insights
