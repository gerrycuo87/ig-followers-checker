"""
Instagram manual export parser.

Parses Instagram's official JSON data export files to extract follower and following information.
Handles multiple export format versions and directory structures.
"""
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

from ..models import User

logger = logging.getLogger(__name__)


class ManualExportParser:
    """
    Parse Instagram's official JSON export files.

    Instagram allows users to download their data officially (Settings → Privacy → Download Data).
    This parser handles the exported JSON files to extract followers and following lists.

    Supports multiple export formats:
    - Legacy format: followers_1.json, following.json
    - Newer format: connections/followers_and_following/followers_1.json
    - Handles different JSON structures across Instagram versions
    """

    # Possible file names for followers (Instagram changes these occasionally)
    FOLLOWERS_FILENAMES = [
        'followers_1.json',
        'followers.json',
    ]

    # Possible file names for following
    FOLLOWING_FILENAMES = [
        'following.json',
    ]

    # Possible subdirectories where files might be located
    POSSIBLE_SUBDIRS = [
        '',  # Root of export
        'connections',
        'connections/followers_and_following',
        'followers_and_following',
    ]

    def __init__(self):
        """Initialize the manual export parser."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse_export_directory(self, export_path: Path) -> Tuple[List[User], List[User]]:
        """
        Parse Instagram export directory to extract followers and following lists.

        Args:
            export_path: Path to extracted Instagram export folder

        Returns:
            Tuple of (followers_list, following_list)

        Raises:
            FileNotFoundError: If export directory or required files not found
            ValueError: If JSON files are corrupted or invalid format
        """
        export_path = Path(export_path)

        if not export_path.exists():
            raise FileNotFoundError(f"Export directory not found: {export_path}")

        if not export_path.is_dir():
            raise ValueError(f"Export path is not a directory: {export_path}")

        # Find the JSON files
        self.logger.info(f"Searching for export files in: {export_path}")
        export_files = self._find_export_files(export_path)

        if not export_files.get('followers'):
            raise FileNotFoundError(
                f"Followers file not found in export. Searched for: {self.FOLLOWERS_FILENAMES}"
            )

        if not export_files.get('following'):
            raise FileNotFoundError(
                f"Following file not found in export. Searched for: {self.FOLLOWING_FILENAMES}"
            )

        # Parse the files
        self.logger.info(f"Parsing followers from: {export_files['followers']}")
        followers = self._parse_followers(export_files['followers'])

        self.logger.info(f"Parsing following from: {export_files['following']}")
        following = self._parse_following(export_files['following'])

        self.logger.info(
            f"Successfully parsed {len(followers)} followers and {len(following)} following"
        )

        return followers, following

    def _find_export_files(self, export_path: Path) -> Dict[str, Optional[Path]]:
        """
        Locate followers and following JSON files in the export directory.

        Instagram's export structure varies by version and date. This method
        searches multiple possible locations and file names.

        Args:
            export_path: Root directory of the Instagram export

        Returns:
            Dictionary with 'followers' and 'following' keys mapping to file paths
        """
        found_files = {
            'followers': None,
            'following': None,
        }

        # Search for followers file
        for subdir in self.POSSIBLE_SUBDIRS:
            search_dir = export_path / subdir if subdir else export_path
            if not search_dir.exists():
                continue

            for filename in self.FOLLOWERS_FILENAMES:
                file_path = search_dir / filename
                if file_path.exists():
                    self.logger.debug(f"Found followers file: {file_path}")
                    found_files['followers'] = file_path
                    break

            if found_files['followers']:
                break

        # Search for following file
        for subdir in self.POSSIBLE_SUBDIRS:
            search_dir = export_path / subdir if subdir else export_path
            if not search_dir.exists():
                continue

            for filename in self.FOLLOWING_FILENAMES:
                file_path = search_dir / filename
                if file_path.exists():
                    self.logger.debug(f"Found following file: {file_path}")
                    found_files['following'] = file_path
                    break

            if found_files['following']:
                break

        return found_files

    def _parse_followers(self, json_path: Path) -> List[User]:
        """
        Parse followers JSON file.

        Instagram's followers file format (as of 2024-2025):
        {
          "relationships_followers": [
            {
              "string_list_data": [
                {
                  "href": "https://www.instagram.com/username",
                  "value": "username",
                  "timestamp": 1702857600
                }
              ]
            }
          ]
        }

        Or older format:
        [
          {
            "string_list_data": [
              {
                "href": "https://www.instagram.com/username",
                "value": "username",
                "timestamp": 1702857600
              }
            ]
          }
        ]

        Args:
            json_path: Path to followers JSON file

        Returns:
            List of User objects representing followers

        Raises:
            ValueError: If JSON is invalid or unexpected format
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {json_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error reading {json_path}: {e}")

        followers = []

        # Handle newer format with "relationships_followers" wrapper
        if isinstance(data, dict) and 'relationships_followers' in data:
            follower_entries = data['relationships_followers']
        elif isinstance(data, list):
            # Older format: direct list
            follower_entries = data
        else:
            raise ValueError(
                f"Unexpected JSON structure in {json_path}. "
                f"Expected dict with 'relationships_followers' or list."
            )

        # Parse each follower entry
        for entry in follower_entries:
            if not isinstance(entry, dict):
                self.logger.warning(f"Skipping invalid follower entry: {entry}")
                continue

            # Extract user data from string_list_data
            string_list_data = entry.get('string_list_data', [])
            if not string_list_data:
                self.logger.warning(f"Skipping entry with no string_list_data: {entry}")
                continue

            for user_data in string_list_data:
                try:
                    # Pass parent entry to handle new format with 'title' field
                    user = self._create_user_from_export_data(user_data, parent_entry=entry)
                    followers.append(user)
                except Exception as e:
                    self.logger.warning(f"Failed to parse follower: {user_data}. Error: {e}")

        return followers

    def _parse_following(self, json_path: Path) -> List[User]:
        """
        Parse following JSON file.

        Format is similar to followers file:
        {
          "relationships_following": [
            {
              "string_list_data": [
                {
                  "href": "https://www.instagram.com/username",
                  "value": "username",
                  "timestamp": 1702857600
                }
              ]
            }
          ]
        }

        Args:
            json_path: Path to following JSON file

        Returns:
            List of User objects representing accounts being followed

        Raises:
            ValueError: If JSON is invalid or unexpected format
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {json_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error reading {json_path}: {e}")

        following = []

        # Handle newer format with "relationships_following" wrapper
        if isinstance(data, dict) and 'relationships_following' in data:
            following_entries = data['relationships_following']
        elif isinstance(data, list):
            # Older format: direct list
            following_entries = data
        else:
            raise ValueError(
                f"Unexpected JSON structure in {json_path}. "
                f"Expected dict with 'relationships_following' or list."
            )

        # Parse each following entry
        for entry in following_entries:
            if not isinstance(entry, dict):
                self.logger.warning(f"Skipping invalid following entry: {entry}")
                continue

            # Extract user data from string_list_data
            string_list_data = entry.get('string_list_data', [])
            if not string_list_data:
                self.logger.warning(f"Skipping entry with no string_list_data: {entry}")
                continue

            for user_data in string_list_data:
                try:
                    # Pass parent entry to handle new format with 'title' field
                    user = self._create_user_from_export_data(user_data, parent_entry=entry)
                    following.append(user)
                except Exception as e:
                    self.logger.warning(f"Failed to parse following: {user_data}. Error: {e}")

        return following

    def _create_user_from_export_data(self, data: Dict, parent_entry: Optional[Dict] = None) -> User:
        """
        Create a User object from Instagram export data.

        Supports multiple export formats:

        Old format (data contains username):
        {
          "href": "https://www.instagram.com/username",
          "value": "username",
          "timestamp": 1702857600
        }

        New format (parent_entry contains username):
        Parent entry: {"title": "username", "string_list_data": [...]}
        Data: {
          "href": "https://www.instagram.com/_u/username",
          "timestamp": 1702857600
        }

        Args:
            data: Dictionary containing user data from string_list_data
            parent_entry: Optional parent entry that may contain 'title' field

        Returns:
            User object with fields populated from export

        Raises:
            ValueError: If username cannot be determined from either source
        """
        # Try to get username from multiple sources (new format first, then old)
        username = None

        # NEW FORMAT: Check parent entry for 'title' field (must be non-empty)
        if parent_entry and parent_entry.get('title'):
            username = parent_entry['title']

        # OLD FORMAT: Check data for 'value' field
        elif 'value' in data:
            username = data['value']

        # FALLBACK: Try to extract from href
        elif 'href' in data:
            # Extract username from URL like "https://www.instagram.com/_u/username"
            href = data['href']
            username = href.rstrip('/').split('/')[-1]
            # Remove '_u/' prefix if present
            if username == '_u' and '/_u/' in href:
                username = href.split('/_u/')[-1].rstrip('/')

        if not username:
            raise ValueError(f"Could not determine username from data: {data}")

        # Profile URL from href (or construct default)
        profile_url = data.get('href', f"https://www.instagram.com/{username}")

        # Timestamp when the relationship started
        timestamp = data.get('timestamp')

        # Create User with available fields
        # Note: Manual export doesn't provide extended fields like follower_count, is_verified, etc.
        return User(
            username=username,
            profile_url=profile_url,
            timestamp=timestamp,
        )
