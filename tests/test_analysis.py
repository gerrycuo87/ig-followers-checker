"""
Unit tests for FollowerAnalyzer.

Covers not_following_back, mutual_followers, fans, statistics,
empty-list edge cases, and case-insensitive username matching.
"""
import pytest
from src.analysis.analyzer import FollowerAnalyzer
from src.models import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(username: str, **kwargs) -> User:
    return User(username=username, profile_url=f"https://www.instagram.com/{username}", **kwargs)


def _analyze(followers, following):
    return FollowerAnalyzer().analyze(followers, following, target_username="testuser", source="manual_export")


# ---------------------------------------------------------------------------
# Core relationship sets
# ---------------------------------------------------------------------------

class TestNotFollowingBack:
    def test_basic(self):
        followers = [_user("alice")]
        following = [_user("alice"), _user("bob")]
        analysis = _analyze(followers, following)
        nfb = {u.username for u in analysis.not_following_back}
        assert nfb == {"bob"}

    def test_all_reciprocal(self):
        users = [_user("alice"), _user("bob")]
        analysis = _analyze(users, users)
        assert analysis.not_following_back == []

    def test_none_reciprocal(self):
        followers = [_user("alice")]
        following = [_user("bob"), _user("carol")]
        analysis = _analyze(followers, following)
        assert len(analysis.not_following_back) == 2

    def test_case_insensitive(self):
        followers = [_user("Alice")]
        following = [_user("alice")]
        analysis = _analyze(followers, following)
        assert analysis.not_following_back == []


class TestMutualFollowers:
    def test_basic(self):
        followers = [_user("alice"), _user("charlie")]
        following = [_user("alice"), _user("bob")]
        analysis = _analyze(followers, following)
        mutual = {u.username for u in analysis.mutual_followers}
        assert mutual == {"alice"}

    def test_no_mutual(self):
        analysis = _analyze([_user("alice")], [_user("bob")])
        assert analysis.mutual_followers == []

    def test_all_mutual(self):
        users = [_user("alice"), _user("bob")]
        analysis = _analyze(users, users)
        assert len(analysis.mutual_followers) == 2


class TestFans:
    def test_basic(self):
        followers = [_user("alice"), _user("bob")]
        following = [_user("alice")]
        analysis = _analyze(followers, following)
        fans = {u.username for u in analysis.fans}
        assert fans == {"bob"}

    def test_no_fans(self):
        analysis = _analyze([], [_user("alice")])
        assert analysis.fans == []

    def test_all_fans(self):
        analysis = _analyze([_user("alice"), _user("bob")], [])
        assert len(analysis.fans) == 2


# ---------------------------------------------------------------------------
# Empty lists
# ---------------------------------------------------------------------------

class TestEmptyLists:
    def test_empty_both(self):
        analysis = _analyze([], [])
        assert analysis.not_following_back == []
        assert analysis.mutual_followers == []
        assert analysis.fans == []

    def test_empty_followers(self):
        analysis = _analyze([], [_user("alice")])
        assert analysis.not_following_back == [_user("alice")]
        assert analysis.mutual_followers == []
        assert analysis.fans == []

    def test_empty_following(self):
        analysis = _analyze([_user("alice")], [])
        assert analysis.not_following_back == []
        assert analysis.mutual_followers == []
        assert analysis.fans == [_user("alice")]


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

class TestStatistics:
    def setup_method(self):
        followers = [_user("alice"), _user("bob"), _user("carol")]
        following = [_user("alice"), _user("dave")]
        self.analysis = _analyze(followers, following)

    def test_total_counts(self):
        s = self.analysis.statistics
        assert s["total_followers"] == 3
        assert s["total_following"] == 2

    def test_not_following_back_count(self):
        assert self.analysis.statistics["not_following_back_count"] == 1  # dave

    def test_mutual_count(self):
        assert self.analysis.statistics["mutual_followers_count"] == 1  # alice

    def test_fans_count(self):
        assert self.analysis.statistics["fans_count"] == 2  # bob, carol

    def test_percentages_sum_to_100(self):
        s = self.analysis.statistics
        total = s["not_following_back_percentage"] + s["mutual_percentage"]
        assert abs(total - 100.0) < 0.01

    def test_follower_following_ratio(self):
        # 3 followers / 2 following = 1.5
        assert self.analysis.statistics["follower_following_ratio"] == 1.5

    def test_zero_following_no_division_error(self):
        analysis = _analyze([_user("alice")], [])
        assert analysis.statistics["follower_following_ratio"] == 0
        assert analysis.statistics["not_following_back_percentage"] == 0

    def test_zero_followers_no_division_error(self):
        analysis = _analyze([], [_user("alice")])
        assert analysis.statistics["fan_percentage"] == 0
