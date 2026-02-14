"""
Simple test for ManualExportParser.

This is a basic test to verify the parser works with sample Instagram export files.
"""
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Direct import to avoid loading all dependencies
from src.parsers.manual_export import ManualExportParser
from src.models import User


def test_manual_export_parser():
    """Test parsing sample Instagram export files."""
    # Get path to fixtures
    fixtures_dir = Path(__file__).parent / 'fixtures'

    # Initialize parser
    parser = ManualExportParser()

    # Parse the export directory
    try:
        followers, following = parser.parse_export_directory(fixtures_dir)

        print(f"✓ Successfully parsed export")
        print(f"  Followers: {len(followers)}")
        print(f"  Following: {len(following)}")

        # Display followers
        print("\nFollowers:")
        for follower in followers:
            print(f"  - @{follower.username} (URL: {follower.profile_url}, Timestamp: {follower.timestamp})")

        # Display following
        print("\nFollowing:")
        for user in following:
            print(f"  - @{user.username} (URL: {user.profile_url}, Timestamp: {user.timestamp})")

        print("\n✓ All tests passed!")
        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_manual_export_parser()
    sys.exit(0 if success else 1)
