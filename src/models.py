"""
Data models for Instagram follower analysis.

These models provide a standardized representation for user data and analysis results,
allowing both manual export and API parsers to work with the same data structures.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class User:
    """
    Standardized user model for both manual export and API parsers.

    This model contains all possible fields, but only username is required.
    API mode provides extended fields (follower_count, is_verified, etc.)
    while manual export mode only provides basic fields (username, profile_url, timestamp).
    """
    username: str
    user_id: Optional[str] = None           # API mode: Instagram user ID
    full_name: Optional[str] = None         # API mode: Display name
    profile_url: str = ""                   # Both modes: Instagram profile URL
    timestamp: Optional[int] = None         # Both modes: When relationship started (Unix timestamp)

    # Extended fields (only available in API mode)
    follower_count: Optional[int] = None    # Number of followers this user has
    following_count: Optional[int] = None   # Number of accounts this user follows
    is_verified: Optional[bool] = None      # Whether account is verified (blue checkmark)
    is_private: Optional[bool] = None       # Whether account is private
    biography: Optional[str] = None         # User's bio text

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert User to dictionary for JSON serialization.

        Returns:
            Dictionary representation of User with all non-None fields
        """
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        Create User from dictionary (e.g., from JSON).

        Args:
            data: Dictionary containing user fields

        Returns:
            User instance
        """
        # Only use fields that exist in the User dataclass
        valid_fields = {
            'username', 'user_id', 'full_name', 'profile_url', 'timestamp',
            'follower_count', 'following_count', 'is_verified', 'is_private', 'biography'
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


@dataclass
class Analysis:
    """
    Analysis results container.

    Stores the complete results of a follower analysis, including:
    - Raw follower/following lists
    - Calculated relationships (mutual, not following back, fans)
    - Statistics and metadata
    """
    analysis_date: datetime                 # When this analysis was performed
    target_username: str                    # Username being analyzed

    # Raw data
    following: List[User]                   # Accounts the target follows
    followers: List[User]                   # Accounts that follow the target

    # Calculated relationships
    not_following_back: List[User] = field(default_factory=list)  # You follow, they don't
    mutual_followers: List[User] = field(default_factory=list)    # Both follow each other
    fans: List[User] = field(default_factory=list)                # They follow you, you don't

    # Metadata and statistics
    statistics: Dict[str, Any] = field(default_factory=dict)      # Calculated stats
    source: str = "unknown"                                        # "manual_export" or "api"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Analysis to dictionary for JSON serialization.

        Returns:
            Dictionary representation with all fields serialized
        """
        return {
            'analysis_date': self.analysis_date.isoformat(),
            'target_username': self.target_username,
            'following': [user.to_dict() for user in self.following],
            'followers': [user.to_dict() for user in self.followers],
            'not_following_back': [user.to_dict() for user in self.not_following_back],
            'mutual_followers': [user.to_dict() for user in self.mutual_followers],
            'fans': [user.to_dict() for user in self.fans],
            'statistics': self.statistics,
            'source': self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Analysis':
        """
        Create Analysis from dictionary (e.g., from JSON).

        Args:
            data: Dictionary containing analysis fields

        Returns:
            Analysis instance
        """
        return cls(
            analysis_date=datetime.fromisoformat(data['analysis_date']),
            target_username=data['target_username'],
            following=[User.from_dict(u) for u in data.get('following', [])],
            followers=[User.from_dict(u) for u in data.get('followers', [])],
            not_following_back=[User.from_dict(u) for u in data.get('not_following_back', [])],
            mutual_followers=[User.from_dict(u) for u in data.get('mutual_followers', [])],
            fans=[User.from_dict(u) for u in data.get('fans', [])],
            statistics=data.get('statistics', {}),
            source=data.get('source', 'unknown'),
        )

    def get_summary(self) -> Dict[str, int]:
        """
        Get a summary of the analysis with counts.

        Returns:
            Dictionary with count statistics
        """
        return {
            'total_following': len(self.following),
            'total_followers': len(self.followers),
            'not_following_back': len(self.not_following_back),
            'mutual_followers': len(self.mutual_followers),
            'fans': len(self.fans),
        }
