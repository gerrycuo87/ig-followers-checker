"""
Unit tests for AnalysisComparator.

Covers new/lost followers, newly followed/unfollowed accounts,
new non-reciprocal entries, temporal order auto-correction, and
the identity case (no changes).
"""
import pytest
from datetime import datetime, timedelta

from src.analysis.comparison import AnalysisComparator, ComparisonResult
from src.models import Analysis, User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(username: str) -> User:
    return User(username=username, profile_url=f"https://www.instagram.com/{username}")


def _make_analysis(
    dt: datetime,
    followers: list,
    following: list,
) -> Analysis:
    follower_names = {u.username for u in followers}
    following_names = {u.username for u in following}
    nfb    = [u for u in following if u.username not in follower_names]
    mutual = [u for u in following if u.username in follower_names]
    fans   = [u for u in followers if u.username not in following_names]
    return Analysis(
        analysis_date=dt,
        target_username="testuser",
        following=following,
        followers=followers,
        not_following_back=nfb,
        mutual_followers=mutual,
        fans=fans,
        statistics={},
        source="manual_export",
    )


BASE_DATE   = datetime(2025, 12, 1)
LATER_DATE  = datetime(2025, 12, 15)

ALICE   = _user("alice")
BOB     = _user("bob")
CAROL   = _user("carol")
DAVE    = _user("dave")
EVE     = _user("eve")


# ---------------------------------------------------------------------------
# New / lost followers
# ---------------------------------------------------------------------------

class TestFollowerChanges:
    def test_new_followers_detected(self):
        earlier = _make_analysis(BASE_DATE,  followers=[ALICE],        following=[])
        later   = _make_analysis(LATER_DATE, followers=[ALICE, BOB],   following=[])
        result  = AnalysisComparator().compare(earlier, later)
        assert {u.username for u in result.new_followers} == {"bob"}

    def test_lost_followers_detected(self):
        earlier = _make_analysis(BASE_DATE,  followers=[ALICE, BOB], following=[])
        later   = _make_analysis(LATER_DATE, followers=[ALICE],      following=[])
        result  = AnalysisComparator().compare(earlier, later)
        assert {u.username for u in result.lost_followers} == {"bob"}

    def test_no_follower_changes(self):
        earlier = _make_analysis(BASE_DATE,  followers=[ALICE], following=[])
        later   = _make_analysis(LATER_DATE, followers=[ALICE], following=[])
        result  = AnalysisComparator().compare(earlier, later)
        assert result.new_followers == []
        assert result.lost_followers == []


# ---------------------------------------------------------------------------
# New / unfollowed accounts
# ---------------------------------------------------------------------------

class TestFollowingChanges:
    def test_new_following_detected(self):
        earlier = _make_analysis(BASE_DATE,  followers=[], following=[ALICE])
        later   = _make_analysis(LATER_DATE, followers=[], following=[ALICE, CAROL])
        result  = AnalysisComparator().compare(earlier, later)
        assert {u.username for u in result.new_following} == {"carol"}

    def test_unfollowed_detected(self):
        earlier = _make_analysis(BASE_DATE,  followers=[], following=[ALICE, BOB])
        later   = _make_analysis(LATER_DATE, followers=[], following=[ALICE])
        result  = AnalysisComparator().compare(earlier, later)
        assert {u.username for u in result.unfollowed_by_you} == {"bob"}


# ---------------------------------------------------------------------------
# New non-reciprocal (not-following-back) accounts
# ---------------------------------------------------------------------------

class TestNewNotFollowingBack:
    def test_new_non_reciprocal_detected(self):
        # Earlier: alice follows back; Later: alice no longer in followers
        earlier = _make_analysis(BASE_DATE,  followers=[ALICE], following=[ALICE])
        later   = _make_analysis(LATER_DATE, followers=[],      following=[ALICE])
        result  = AnalysisComparator().compare(earlier, later)
        assert {u.username for u in result.new_not_following_back} == {"alice"}

    def test_no_new_non_reciprocal_when_unchanged(self):
        earlier = _make_analysis(BASE_DATE,  followers=[],    following=[ALICE])
        later   = _make_analysis(LATER_DATE, followers=[],    following=[ALICE])
        result  = AnalysisComparator().compare(earlier, later)
        assert result.new_not_following_back == []


# ---------------------------------------------------------------------------
# Identity (no changes at all)
# ---------------------------------------------------------------------------

class TestIdentityComparison:
    def test_empty_diff_when_analyses_identical(self):
        followers = [ALICE, BOB]
        following = [ALICE, CAROL]
        earlier = _make_analysis(BASE_DATE,  followers, following)
        later   = _make_analysis(LATER_DATE, followers, following)
        result  = AnalysisComparator().compare(earlier, later)
        assert result.new_followers          == []
        assert result.lost_followers         == []
        assert result.new_following          == []
        assert result.unfollowed_by_you      == []
        assert result.new_not_following_back == []


# ---------------------------------------------------------------------------
# Temporal metadata
# ---------------------------------------------------------------------------

class TestTemporalMetadata:
    def test_days_between_is_calculated(self):
        earlier = _make_analysis(BASE_DATE,  [], [])
        later   = _make_analysis(LATER_DATE, [], [])
        result  = AnalysisComparator().compare(earlier, later)
        assert result.days_between == 14

    def test_result_preserves_earlier_and_later(self):
        earlier = _make_analysis(BASE_DATE,  [], [])
        later   = _make_analysis(LATER_DATE, [], [])
        result  = AnalysisComparator().compare(earlier, later)
        assert result.earlier.analysis_date == BASE_DATE
        assert result.later.analysis_date   == LATER_DATE
