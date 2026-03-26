"""
Unit tests for ManualExportParser.

Covers both new and old Instagram export formats, missing-file and
corrupted-JSON error paths, the various filename/subdirectory layouts
Instagram has used over time, and ZIP archive auto-extraction.
"""
import json
import zipfile
import pytest
from pathlib import Path

from src.parsers.manual_export import ManualExportParser
from src.models import User

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(tmp_path: Path, filename: str, content) -> Path:
    """Write *content* (dict/list) as JSON at tmp_path/filename."""
    p = tmp_path / filename
    p.write_text(json.dumps(content), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# New-format: "relationships_followers" / "relationships_following" wrapper
# ---------------------------------------------------------------------------

class TestNewFormat:
    def test_parse_followers_from_fixtures(self):
        parser = ManualExportParser()
        followers, _ = parser.parse_export_directory(FIXTURES)
        assert len(followers) == 3
        usernames = {u.username for u in followers}
        assert usernames == {"follower1", "follower2", "follower3"}

    def test_parse_following_from_fixtures(self):
        parser = ManualExportParser()
        _, following = parser.parse_export_directory(FIXTURES)
        assert len(following) == 2
        usernames = {u.username for u in following}
        assert usernames == {"following1", "following2"}

    def test_followers_have_profile_url(self):
        parser = ManualExportParser()
        followers, _ = parser.parse_export_directory(FIXTURES)
        for u in followers:
            assert u.profile_url.startswith("https://www.instagram.com/")

    def test_followers_have_timestamp(self):
        parser = ManualExportParser()
        followers, _ = parser.parse_export_directory(FIXTURES)
        for u in followers:
            assert u.timestamp is not None
            assert isinstance(u.timestamp, int)

    def test_returns_user_objects(self):
        parser = ManualExportParser()
        followers, following = parser.parse_export_directory(FIXTURES)
        assert all(isinstance(u, User) for u in followers)
        assert all(isinstance(u, User) for u in following)


# ---------------------------------------------------------------------------
# Old format: bare list with "value" field
# ---------------------------------------------------------------------------

class TestOldFormat:
    def test_parse_old_followers_format(self, tmp_path):
        old_followers = [
            {"string_list_data": [{"href": "https://www.instagram.com/a", "value": "a", "timestamp": 1}]},
            {"string_list_data": [{"href": "https://www.instagram.com/b", "value": "b", "timestamp": 2}]},
        ]
        old_following = {
            "relationships_following": [
                {"title": "", "string_list_data": [{"href": "https://www.instagram.com/c", "value": "c", "timestamp": 3}]},
            ]
        }
        _write(tmp_path, "followers_1.json", old_followers)
        _write(tmp_path, "following.json", old_following)

        parser = ManualExportParser()
        followers, _ = parser.parse_export_directory(tmp_path)
        assert {u.username for u in followers} == {"a", "b"}

    def test_old_format_fixtures_file(self, tmp_path):
        """Fixture file followers_old.json is a valid old-format file."""
        old_data = json.loads((FIXTURES / "followers_old.json").read_text())
        following_data = {"relationships_following": [
            {"title": "", "string_list_data": [{"href": "https://www.instagram.com/x", "value": "x", "timestamp": 1}]}
        ]}
        (tmp_path / "followers_1.json").write_text(json.dumps(old_data), encoding="utf-8")
        _write(tmp_path, "following.json", following_data)

        parser = ManualExportParser()
        followers, _ = parser.parse_export_directory(tmp_path)
        assert {u.username for u in followers} == {"oldfollower1", "oldfollower2"}


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

class TestErrorPaths:
    def test_missing_directory_raises_file_not_found(self, tmp_path):
        parser = ManualExportParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_export_directory(tmp_path / "nonexistent")

    def test_both_files_missing_raises_file_not_found(self, tmp_path):
        parser = ManualExportParser()
        with pytest.raises(FileNotFoundError, match="Could not find followers or following"):
            parser.parse_export_directory(tmp_path)

    def test_only_followers_missing_raises_file_not_found(self, tmp_path):
        _write(tmp_path, "following.json", {"relationships_following": []})
        parser = ManualExportParser()
        with pytest.raises(FileNotFoundError, match="Followers file not found"):
            parser.parse_export_directory(tmp_path)

    def test_only_following_missing_raises_file_not_found(self, tmp_path):
        _write(tmp_path, "followers_1.json", {"relationships_followers": []})
        parser = ManualExportParser()
        with pytest.raises(FileNotFoundError, match="Following file not found"):
            parser.parse_export_directory(tmp_path)

    def test_corrupted_followers_json_raises_value_error(self, tmp_path):
        (tmp_path / "followers_1.json").write_text("{invalid json", encoding="utf-8")
        _write(tmp_path, "following.json", {"relationships_following": []})
        parser = ManualExportParser()
        with pytest.raises(ValueError, match="not valid JSON"):
            parser.parse_export_directory(tmp_path)

    def test_corrupted_following_json_raises_value_error(self, tmp_path):
        _write(tmp_path, "followers_1.json", {"relationships_followers": []})
        (tmp_path / "following.json").write_text("not json at all", encoding="utf-8")
        parser = ManualExportParser()
        with pytest.raises(ValueError, match="not valid JSON"):
            parser.parse_export_directory(tmp_path)

    def test_unexpected_json_structure_raises_value_error(self, tmp_path):
        _write(tmp_path, "followers_1.json", {"unexpected_key": []})
        _write(tmp_path, "following.json", {"relationships_following": []})
        parser = ManualExportParser()
        with pytest.raises(ValueError, match="Unexpected JSON structure"):
            parser.parse_export_directory(tmp_path)

    def test_path_is_file_not_dir_raises_value_error(self, tmp_path):
        f = tmp_path / "somefile.json"
        f.write_text("{}", encoding="utf-8")
        parser = ManualExportParser()
        with pytest.raises(ValueError, match="not a directory"):
            parser.parse_export_directory(f)


# ---------------------------------------------------------------------------
# Subdirectory search
# ---------------------------------------------------------------------------

class TestSubdirectorySearch:
    def test_finds_files_in_connections_subfolder(self, tmp_path):
        subdir = tmp_path / "connections" / "followers_and_following"
        subdir.mkdir(parents=True)
        _write(subdir, "followers_1.json", {"relationships_followers": [
            {"title": "", "string_list_data": [{"href": "https://www.instagram.com/sub1", "value": "sub1", "timestamp": 1}]}
        ]})
        _write(subdir, "following.json", {"relationships_following": [
            {"title": "", "string_list_data": [{"href": "https://www.instagram.com/sub2", "value": "sub2", "timestamp": 2}]}
        ]})

        parser = ManualExportParser()
        followers, following = parser.parse_export_directory(tmp_path)
        assert followers[0].username == "sub1"
        assert following[0].username == "sub2"


# ---------------------------------------------------------------------------
# ZIP archive support
# ---------------------------------------------------------------------------

def _make_zip(zip_path: Path, followers_data, following_data) -> Path:
    """Create a ZIP archive containing followers and following JSON files."""
    with zipfile.ZipFile(zip_path, 'w') as zf:
        zf.writestr("followers_1.json", json.dumps(followers_data))
        zf.writestr("following.json", json.dumps(following_data))
    return zip_path


_ZIP_FOLLOWERS = {"relationships_followers": [
    {"title": "zipuser1", "string_list_data": [{"href": "https://www.instagram.com/zipuser1", "timestamp": 1}]}
]}
_ZIP_FOLLOWING = {"relationships_following": [
    {"title": "zipfollow1", "string_list_data": [{"href": "https://www.instagram.com/zipfollow1", "timestamp": 2}]}
]}


class TestZipSupport:
    def test_zip_is_accepted_and_parsed(self, tmp_path):
        """Parser accepts a .zip archive directly."""
        zip_path = _make_zip(tmp_path / "export.zip", _ZIP_FOLLOWERS, _ZIP_FOLLOWING)
        parser = ManualExportParser()
        followers, following = parser.parse_export_directory(zip_path)
        assert {u.username for u in followers} == {"zipuser1"}
        assert {u.username for u in following} == {"zipfollow1"}

    def test_zip_extracts_to_sibling_directory(self, tmp_path):
        """ZIP is extracted to a directory named after the ZIP stem."""
        zip_path = _make_zip(tmp_path / "myexport.zip", _ZIP_FOLLOWERS, _ZIP_FOLLOWING)
        ManualExportParser().parse_export_directory(zip_path)
        assert (tmp_path / "myexport").is_dir()

    def test_zip_rerun_skips_extraction(self, tmp_path):
        """Re-running with the same ZIP skips extraction when the directory already exists."""
        zip_path = _make_zip(tmp_path / "export.zip", _ZIP_FOLLOWERS, _ZIP_FOLLOWING)
        parser = ManualExportParser()

        # First run — extracts
        parser.parse_export_directory(zip_path)
        assert (tmp_path / "export").is_dir()

        # Corrupt the ZIP so a re-extraction attempt would fail
        zip_path.write_bytes(b"not a zip")

        # Second run — must use existing directory, not try to re-extract
        parser.parse_export_directory(zip_path)

    def test_invalid_zip_raises_value_error(self, tmp_path):
        """A .zip file that is not a valid ZIP archive raises ValueError."""
        fake_zip = tmp_path / "export.zip"
        fake_zip.write_bytes(b"this is not a zip file")
        with pytest.raises(ValueError, match="not a valid ZIP"):
            ManualExportParser().parse_export_directory(fake_zip)
