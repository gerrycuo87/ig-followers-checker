"""
Historical analysis storage for Instagram Followers Checker.

Saves each analysis to disk and supports listing, loading, and cleaning
past analyses for comparison over time.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

from ..models import Analysis

# Default storage directory (relative to project root)
_HISTORY_DIR = Path(__file__).resolve().parents[2] / "data" / "history"


class HistoryManager:
    """Persist and retrieve past analyses."""

    def __init__(self, history_dir: Optional[Path] = None):
        self._dir = history_dir or _HISTORY_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save_analysis(self, analysis: Analysis) -> Path:
        """
        Persist an analysis to disk.

        The file is named ``analysis-YYYY-MM-DD-HHMMSS.json`` using the
        analysis's own ``analysis_date``.

        Args:
            analysis: Completed analysis to save.

        Returns:
            Path to the saved JSON file.
        """
        filename = "analysis-" + analysis.analysis_date.strftime("%Y-%m-%d-%H%M%S") + ".json"
        path = self._dir / filename
        path.write_text(json.dumps(analysis.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def list_analyses(self) -> List[Dict[str, Any]]:
        """
        Return metadata for all saved analyses, newest first.

        Each entry contains:
            - ``filename``: the JSON file name
            - ``date``: ISO-format string of analysis_date
            - ``target_username``: account that was analysed
            - ``following``: number of following
            - ``followers``: number of followers
            - ``not_following_back``: count of non-reciprocal follows

        Returns:
            List of metadata dicts, sorted newest-first.
        """
        entries = []
        for path in sorted(self._dir.glob("analysis-*.json"), reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                stats = data.get("statistics", {})
                entries.append({
                    "filename": path.name,
                    "date": data.get("analysis_date", "unknown"),
                    "target_username": data.get("target_username", "unknown"),
                    "following": stats.get("total_following", len(data.get("following", []))),
                    "followers": stats.get("total_followers", len(data.get("followers", []))),
                    "not_following_back": stats.get("not_following_back_count",
                                                     len(data.get("not_following_back", []))),
                })
            except (json.JSONDecodeError, KeyError):
                # Skip corrupted files silently
                continue
        return entries

    def load_analysis(self, identifier: str) -> Analysis:
        """
        Load an analysis by date prefix or exact filename.

        Args:
            identifier: A date prefix (e.g. ``"2025-12-15"``) or the
                        exact filename (e.g. ``"analysis-2025-12-15-143022.json"``).

        Returns:
            Loaded Analysis object.

        Raises:
            FileNotFoundError: When no matching file is found.
            ValueError: When more than one file matches the prefix.
        """
        candidates = self._resolve_identifier(identifier)
        if not candidates:
            raise FileNotFoundError(f"No saved analysis matches '{identifier}'")
        if len(candidates) > 1:
            names = ", ".join(p.name for p in candidates)
            raise ValueError(
                f"Multiple analyses match '{identifier}': {names}. "
                "Use a more specific identifier."
            )
        data = json.loads(candidates[0].read_text(encoding="utf-8"))
        return Analysis.from_dict(data)

    def latest(self) -> Optional[Analysis]:
        """
        Return the most recently saved analysis, or None if history is empty.

        Returns:
            Analysis object or None.
        """
        paths = sorted(self._dir.glob("analysis-*.json"), reverse=True)
        if not paths:
            return None
        data = json.loads(paths[0].read_text(encoding="utf-8"))
        return Analysis.from_dict(data)

    def clean(self, keep: int = 10) -> int:
        """
        Delete old analyses, keeping only the ``keep`` most recent ones.

        Args:
            keep: Number of analyses to retain (default 10).

        Returns:
            Number of files deleted.
        """
        paths = sorted(self._dir.glob("analysis-*.json"), reverse=True)
        to_delete = paths[keep:]
        for p in to_delete:
            p.unlink()
        return len(to_delete)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_identifier(self, identifier: str) -> List[Path]:
        """Return all history files matching the identifier."""
        # Exact filename match
        exact = self._dir / identifier
        if exact.exists():
            return [exact]
        # Prefix match against filenames
        return [p for p in self._dir.glob("analysis-*.json") if identifier in p.name]
