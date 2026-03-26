"""
Unit tests for AnalysisFilter.

Covers timestamp filtering, API-only filter warnings, and edge cases
like empty lists and all-None timestamps.
"""
import time
import warnings
import pytest
from src.analysis.filters import AnalysisFilter
from src.models import User


def _user(username: str, **kwargs) -> User:
    return User(username=username, profile_url=f"https://www.instagram.com/{username}", **kwargs)


def _now() -> int:
    return int(time.time())


# ---------------------------------------------------------------------------
# by_timestamp
# ---------------------------------------------------------------------------

class TestByTimestamp:
    def test_keeps_recent_entry(self):
        users = [_user("alice", timestamp=_now() - 3600)]  # 1 hour ago
        result = AnalysisFilter().by_timestamp(users, days=30)
        assert result == users

    def test_excludes_old_entry(self):
        users = [_user("old", timestamp=_now() - 60 * 86400)]  # 60 days ago
        result = AnalysisFilter().by_timestamp(users, days=30)
        assert result == []

    def test_excludes_entries_without_timestamp(self):
        users = [_user("no_ts", timestamp=None)]
        result = AnalysisFilter().by_timestamp(users, days=30)
        assert result == []

    def test_empty_list(self):
        assert AnalysisFilter().by_timestamp([], days=30) == []

    def test_mixed_list(self):
        recent = _user("recent", timestamp=_now() - 86400)      # 1 day ago
        old    = _user("old",    timestamp=_now() - 60 * 86400)  # 60 days ago
        no_ts  = _user("no_ts",  timestamp=None)
        result = AnalysisFilter().by_timestamp([recent, old, no_ts], days=30)
        assert result == [recent]

    def test_boundary_is_inclusive(self):
        # Exactly at the cutoff (with small buffer for execution time)
        ts = _now() - 30 * 86400 + 60  # 30 days ago + 1 minute buffer
        users = [_user("edge", timestamp=ts)]
        result = AnalysisFilter().by_timestamp(users, days=30)
        assert result == users


# ---------------------------------------------------------------------------
# by_follower_count (API-only)
# ---------------------------------------------------------------------------

class TestByFollowerCount:
    def test_filters_correctly_with_api_data(self):
        users = [
            _user("small",  follower_count=100),
            _user("medium", follower_count=5_000),
            _user("large",  follower_count=50_000),
        ]
        result = AnalysisFilter().by_follower_count(users, min_count=1_000, max_count=10_000)
        assert [u.username for u in result] == ["medium"]

    def test_warns_on_manual_export_data(self):
        users = [_user("alice")]  # follower_count is None
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = AnalysisFilter().by_follower_count(users, min_count=0)
        assert result == []
        assert any("API mode" in str(w.message) for w in caught)

    def test_empty_list_no_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = AnalysisFilter().by_follower_count([], min_count=0)
        assert result == []
        assert not caught

    def test_no_upper_bound(self):
        users = [_user("a", follower_count=1_000_000)]
        result = AnalysisFilter().by_follower_count(users, min_count=0)
        assert result == users


# ---------------------------------------------------------------------------
# verified_only (API-only)
# ---------------------------------------------------------------------------

class TestVerifiedOnly:
    def test_returns_only_verified(self):
        users = [
            _user("vip",     is_verified=True),
            _user("regular", is_verified=False),
        ]
        result = AnalysisFilter().verified_only(users)
        assert [u.username for u in result] == ["vip"]

    def test_warns_on_manual_export_data(self):
        users = [_user("alice")]  # is_verified is None
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = AnalysisFilter().verified_only(users)
        assert result == []
        assert any("API mode" in str(w.message) for w in caught)

    def test_empty_list_no_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = AnalysisFilter().verified_only([])
        assert result == []
        assert not caught


# ---------------------------------------------------------------------------
# private_only (API-only)
# ---------------------------------------------------------------------------

class TestPrivateOnly:
    def test_returns_only_private(self):
        users = [
            _user("hidden", is_private=True),
            _user("public", is_private=False),
        ]
        result = AnalysisFilter().private_only(users)
        assert [u.username for u in result] == ["hidden"]

    def test_warns_on_manual_export_data(self):
        users = [_user("alice")]  # is_private is None
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = AnalysisFilter().private_only(users)
        assert result == []
        assert any("API mode" in str(w.message) for w in caught)
