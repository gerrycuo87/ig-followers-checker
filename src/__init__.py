"""
Instagram Followers Checker - A tool for analyzing Instagram follower/following lists.

This package provides functionality to:
- Fetch Instagram follower and following lists incrementally
- Compare lists to find who doesn't follow you back
- Cache progress to avoid rate limiting
- Handle Instagram API errors gracefully
"""

__version__ = "0.2.0"
__author__ = "Gerardo Cuozzo"

# Import main classes for easier access
from .models import User, Analysis
from .parsers.manual_export import ManualExportParser
from .storage.cache import CacheManager

# Optional imports (require external dependencies)
try:
    from .parsers.instagram_api import InstagramClient
    from .analyzer import FollowerAnalyzer
    from .cli import main
    _has_api_support = True
except ImportError:
    InstagramClient = None
    FollowerAnalyzer = None
    main = None
    _has_api_support = False

__all__ = [
    "User",
    "Analysis",
    "ManualExportParser",
    "CacheManager",
    "InstagramClient",
    "FollowerAnalyzer",
    "main",
]