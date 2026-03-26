"""
Unit tests for HistoryManager.

Uses a temporary directory for all disk I/O so the real data/history/
folder is never touched.
"""
import json
import pytest
from datetime import datetime
from pathlib import Path

from src.storage.history import HistoryManager
from src.models import Analysis, User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user(username: str) -> User:
    return User(username=username, profile_url=f"https://www.instagram.com/{username}")


def _make_analysis(dt: datetime, following=None, followers=None) -> Analysis:
    following = following or [_user("alice"), _user("bob")]
    followers = followers or [_user("alice"), _user("charlie")]
    not_fb = [u for u in following if u.username not in {f.username for f in followers}]
    mutual = [u for u in following if u.username in {f.username for f in followers}]
    fans   = [u for u in followers if u.username not in {u2.username for u2 in following}]
    return Analysis(
        analysis_date=dt,
        target_username="testuser",
        following=following,
        followers=followers,
        not_following_back=not_fb,
        mutual_followers=mutual,
        fans=fans,
        statistics={"total_following": len(following), "total_followers": len(followers)},
        source="manual_export",
    )


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

class TestSaveLoad:
    def test_save_creates_file(self, tmp_path):
        hm = HistoryManager(tmp_path)
        a = _make_analysis(datetime(2025, 12, 15, 14, 30, 0))
        path = hm.save_analysis(a)
        assert path.exists()
        assert path.suffix == ".json"

    def test_filename_uses_analysis_date(self, tmp_path):
        hm = HistoryManager(tmp_path)
        a = _make_analysis(datetime(2025, 12, 15, 14, 30, 0))
        path = hm.save_analysis(a)
        assert "2025-12-15" in path.name

    def test_round_trip_preserves_data(self, tmp_path):
        hm = HistoryManager(tmp_path)
        original = _make_analysis(datetime(2025, 12, 15, 14, 30, 0))
        path = hm.save_analysis(original)
        loaded = hm.load_analysis(path.name)

        assert loaded.target_username == original.target_username
        assert loaded.source == original.source
        assert {u.username for u in loaded.following} == {u.username for u in original.following}
        assert {u.username for u in loaded.followers} == {u.username for u in original.followers}

    def test_load_by_date_prefix(self, tmp_path):
        hm = HistoryManager(tmp_path)
        a = _make_analysis(datetime(2025, 12, 15, 14, 30, 0))
        hm.save_analysis(a)
        loaded = hm.load_analysis("2025-12-15")
        assert loaded.target_username == "testuser"

    def test_load_ambiguous_prefix_raises(self, tmp_path):
        hm = HistoryManager(tmp_path)
        hm.save_analysis(_make_analysis(datetime(2025, 12, 15, 10, 0, 0)))
        hm.save_analysis(_make_analysis(datetime(2025, 12, 15, 11, 0, 0)))
        with pytest.raises(ValueError, match="Multiple analyses match"):
            hm.load_analysis("2025-12-15")

    def test_load_nonexistent_raises(self, tmp_path):
        hm = HistoryManager(tmp_path)
        with pytest.raises(FileNotFoundError):
            hm.load_analysis("1999-01-01")

    def test_load_corrupted_file_raises(self, tmp_path):
        (tmp_path / "analysis-2025-12-15-000000.json").write_text("not json", encoding="utf-8")
        hm = HistoryManager(tmp_path)
        with pytest.raises(ValueError, match="corrupted"):
            hm.load_analysis("2025-12-15")


# ---------------------------------------------------------------------------
# list_analyses
# ---------------------------------------------------------------------------

class TestListAnalyses:
    def test_returns_newest_first(self, tmp_path):
        hm = HistoryManager(tmp_path)
        hm.save_analysis(_make_analysis(datetime(2025, 12, 1)))
        hm.save_analysis(_make_analysis(datetime(2025, 12, 15)))
        entries = hm.list_analyses()
        dates = [e["date"] for e in entries]
        assert dates == sorted(dates, reverse=True)

    def test_empty_directory_returns_empty_list(self, tmp_path):
        hm = HistoryManager(tmp_path)
        assert hm.list_analyses() == []

    def test_entry_has_required_keys(self, tmp_path):
        hm = HistoryManager(tmp_path)
        hm.save_analysis(_make_analysis(datetime(2025, 12, 15)))
        entry = hm.list_analyses()[0]
        for key in ("filename", "date", "target_username", "following", "followers"):
            assert key in entry

    def test_corrupted_file_skipped(self, tmp_path):
        (tmp_path / "analysis-2025-01-01-000000.json").write_text("bad", encoding="utf-8")
        hm = HistoryManager(tmp_path)
        # Should not raise, just skip the corrupted file
        entries = hm.list_analyses()
        assert entries == []


# ---------------------------------------------------------------------------
# latest
# ---------------------------------------------------------------------------

class TestLatest:
    def test_returns_none_on_empty(self, tmp_path):
        hm = HistoryManager(tmp_path)
        assert hm.latest() is None

    def test_returns_most_recent(self, tmp_path):
        hm = HistoryManager(tmp_path)
        hm.save_analysis(_make_analysis(datetime(2025, 12, 1)))
        hm.save_analysis(_make_analysis(datetime(2025, 12, 15)))
        latest = hm.latest()
        assert latest is not None


# ---------------------------------------------------------------------------
# clean
# ---------------------------------------------------------------------------

class TestClean:
    def test_deletes_old_files(self, tmp_path):
        hm = HistoryManager(tmp_path)
        for day in range(1, 16):  # 15 analyses
            hm.save_analysis(_make_analysis(datetime(2025, 12, day)))
        deleted = hm.clean(keep=10)
        assert deleted == 5
        assert len(list(tmp_path.glob("analysis-*.json"))) == 10

    def test_no_files_to_delete(self, tmp_path):
        hm = HistoryManager(tmp_path)
        for day in range(1, 6):  # 5 analyses
            hm.save_analysis(_make_analysis(datetime(2025, 12, day)))
        deleted = hm.clean(keep=10)
        assert deleted == 0

    def test_keeps_n_most_recent(self, tmp_path):
        hm = HistoryManager(tmp_path)
        for day in range(1, 16):
            hm.save_analysis(_make_analysis(datetime(2025, 12, day)))
        hm.clean(keep=3)
        remaining = sorted(tmp_path.glob("analysis-*.json"), reverse=True)
        assert len(remaining) == 3
        # The most recent (day 15, 14, 13) should be kept
        assert "2025-12-15" in remaining[0].name
