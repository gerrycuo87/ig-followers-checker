"""
Export analysis results to CSV, JSON, and TXT formats.
"""
import csv
import json
from pathlib import Path
from typing import List

from ..models import Analysis, User


class AnalysisExporter:
    """
    Export analysis results to various file formats.

    All exports are UTF-8 encoded to support international usernames.
    """

    # Categories available for export
    CATEGORIES = ("not_following_back", "mutual_followers", "fans", "all")

    def __init__(self, analysis: Analysis):
        """
        Args:
            analysis: Analysis object containing results to export.
        """
        self.analysis = analysis

    # ------------------------------------------------------------------
    # Public export methods
    # ------------------------------------------------------------------

    def to_csv(self, output_path: Path, category: str = "not_following_back") -> int:
        """
        Export to CSV.

        Args:
            output_path: Destination file path.
            category: Which set of users to export.
                      One of: "not_following_back", "mutual_followers", "fans", "all".

        Returns:
            Number of rows written.

        Raises:
            ValueError: If category is unknown.
            IOError: If the file cannot be written.
        """
        users, include_category_col = self._resolve_users(category)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["username", "profile_url", "timestamp"]
            if include_category_col:
                fieldnames.append("category")

            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()

            for entry in users:
                row = {
                    "username": entry["username"],
                    "profile_url": entry["profile_url"],
                    "timestamp": entry.get("timestamp", ""),
                }
                if include_category_col:
                    row["category"] = entry["_category"]
                writer.writerow(row)

        return len(users)

    def to_json(self, output_path: Path) -> int:
        """
        Export the complete analysis to JSON.

        Args:
            output_path: Destination file path.

        Returns:
            Total number of users written across all categories.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "analysis_date": self.analysis.analysis_date.isoformat(),
            "target_username": self.analysis.target_username,
            "source": self.analysis.source,
            "statistics": self.analysis.statistics,
            "not_following_back": [u.to_dict() for u in self.analysis.not_following_back],
            "mutual_followers":   [u.to_dict() for u in self.analysis.mutual_followers],
            "fans":               [u.to_dict() for u in self.analysis.fans],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        total = (
            len(self.analysis.not_following_back)
            + len(self.analysis.mutual_followers)
            + len(self.analysis.fans)
        )
        return total

    def to_txt(self, output_path: Path) -> int:
        """
        Export to a human-readable plain-text report.

        Args:
            output_path: Destination file path.

        Returns:
            Total number of users written across all categories.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        a = self.analysis
        s = a.statistics
        lines: List[str] = []

        # Header
        lines += [
            "INSTAGRAM FOLLOWERS ANALYSIS",
            "=" * 50,
            f"Generated:  {a.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Account:    @{a.target_username}",
            f"Source:     {a.source.replace('_', ' ').title()}",
            "",
            "OVERVIEW",
            "-" * 30,
            f"Total followers:   {s['total_followers']:,}",
            f"Total following:   {s['total_following']:,}",
            f"Follower ratio:    {s['follower_following_ratio']:.2f}:1",
            "",
            "BREAKDOWN",
            "-" * 30,
            f"Not following back:  {s['not_following_back_count']:,}  ({s['not_following_back_percentage']:.1f}% of following)",
            f"Mutual followers:    {s['mutual_followers_count']:,}  ({s['mutual_percentage']:.1f}% of following)",
            f"Fans:                {s['fans_count']:,}  ({s['fan_percentage']:.1f}% of followers)",
            "",
        ]

        # Not following back list
        lines.append(f"NOT FOLLOWING BACK ({len(a.not_following_back):,})")
        lines.append("-" * 30)
        for user in a.not_following_back:
            lines.append(f"@{user.username}")
        lines.append("")

        # Fans list
        lines.append(f"FANS — follow you but you don't follow back ({len(a.fans):,})")
        lines.append("-" * 30)
        for user in a.fans:
            lines.append(f"@{user.username}")
        lines.append("")

        # Mutual followers list
        lines.append(f"MUTUAL FOLLOWERS ({len(a.mutual_followers):,})")
        lines.append("-" * 30)
        for user in a.mutual_followers:
            lines.append(f"@{user.username}")
        lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return len(a.not_following_back) + len(a.fans) + len(a.mutual_followers)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_users(self, category: str):
        """
        Return a flat list of user dicts for the requested category.

        Returns:
            Tuple of (list_of_dicts, include_category_column).
        """
        if category not in self.CATEGORIES:
            raise ValueError(
                f"Unknown category '{category}'. "
                f"Choose from: {', '.join(self.CATEGORIES)}"
            )

        if category == "all":
            users = []
            for cat, user_list in [
                ("not_following_back", self.analysis.not_following_back),
                ("mutual_follower",    self.analysis.mutual_followers),
                ("fan",                self.analysis.fans),
            ]:
                for u in user_list:
                    d = u.to_dict()
                    d["_category"] = cat
                    users.append(d)
            return users, True
        else:
            user_list = getattr(self.analysis, category)
            return [u.to_dict() for u in user_list], False
