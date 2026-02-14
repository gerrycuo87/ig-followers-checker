"""
API mode workflow for Instagram Followers Checker.

This module handles the EXPERIMENTAL API mode where users fetch follower data
directly from Instagram's API. This mode is NOT RECOMMENDED due to:
- Violation of Instagram Terms of Service
- High risk of account ban
- Very slow (16-40 days for complete results)
- Requires daily execution for weeks
"""
import argparse
from typing import Tuple

from ..storage.cache import CacheManager
from ..parsers.instagram_api import InstagramClient
from ..analyzer import FollowerAnalyzer


def show_api_warning() -> bool:
    """
    Display API mode warnings and get user confirmation.

    Returns:
        True if user accepts risks, False otherwise
    """
    print("\n" + "=" * 60)
    print("⚠️  WARNING: API Mode - Read Carefully")
    print("=" * 60)
    print()
    print("You are about to use the EXPERIMENTAL API mode.")
    print()
    print("RISKS:")
    print("  • Violates Instagram Terms of Service")
    print("  • HIGH RISK of account ban/suspension")
    print("  • Requires 16-40 days for complete results")
    print("  • Must run script DAILY for weeks")
    print("  • May fail mid-process despite incremental approach")
    print("  • Instagram actively blocks automated access")
    print()
    print("RECOMMENDATION:")
    print("  Use Manual Export mode instead:")
    print("  - 100% safe and ToS compliant")
    print("  - Complete results in 48 hours")
    print("  - Run: python igfc.py analyze --export PATH")
    print()

    response = input("Do you understand and accept these risks? [yes/NO]: ").strip().lower()

    if response != 'yes':
        print("\nWise choice! Please use manual export mode instead.")
        return False

    print()
    print("=" * 60)
    print("⚠️  FINAL WARNING")
    print("=" * 60)
    print()
    print("Are you absolutely sure you want to proceed with API mode?")
    print("This could result in your Instagram account being banned.")
    print()

    final_response = input('Type "I ACCEPT THE RISKS" to continue: ').strip()

    if final_response != "I ACCEPT THE RISKS":
        print("\nOperation cancelled. Please use manual export mode instead.")
        return False

    print()
    print("⚠️  Proceeding with API mode at your own risk...")
    print()
    return True


def print_welcome():
    """Display welcome message and important notes for API mode."""
    print("=" * 60)
    print("Instagram Followers Checker - API Mode (EXPERIMENTAL)")
    print("=" * 60)
    print("\nIMPORTANT NOTES:")
    print("- Use a dedicated/test account (not your personal account)")
    print("- This tool fetches data incrementally over multiple days")
    print("- Run once per day to avoid rate limiting")
    print("- You'll get results immediately, improving with each run")
    print("=" * 60)
    print()


def get_credentials() -> Tuple[str, str]:
    """
    Get Instagram credentials from user input.

    Returns:
        Tuple of (username, password)
    """
    username = input("Enter your Instagram username: ")
    password = input("Enter your Instagram password: ")
    return username, password


def get_target_username(default_username: str) -> str:
    """
    Get target username to analyze.

    Args:
        default_username: Default username (logged in user)

    Returns:
        Target username to analyze
    """
    target = input(
        "Enter the profile name you want to analyze (leave blank for your own profile): "
    )
    return target or default_username


def run_api_mode(args: argparse.Namespace) -> int:
    """
    Run API mode analysis.

    Args:
        args: Parsed command-line arguments with:
            - username: Instagram username
            - target: Target username (optional)
            - experimental: Must be True to proceed

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Verify experimental flag
    if not args.experimental:
        print("Error: API mode requires --experimental flag")
        print("This flag acknowledges you understand the risks.")
        print()
        print("Run: python igfc.py api --username USER --experimental")
        return 1

    # Show warnings and get confirmation
    if not show_api_warning():
        return 1

    try:
        # Display welcome message
        print_welcome()

        # Initialize components
        cache_manager = CacheManager()
        ig_client = InstagramClient()
        analyzer = FollowerAnalyzer(cache_manager, ig_client)

        # Get credentials
        username = args.username
        password = input(f"Enter password for @{username}: ")

        # Login
        print(f"\n🔐 Logging in as @{username}...")
        ig_client.login(username, password)

        if not ig_client.logged_in:
            print("❌ Failed to establish Instagram session.")
            print("Possible reasons:")
            print("  - Incorrect credentials")
            print("  - Two-factor authentication enabled")
            print("  - Account flagged by Instagram")
            return 1

        print("✓ Login successful")

        # Get target username
        target_username = args.target if args.target else username

        if target_username != username:
            print(f"\n🎯 Target account: @{target_username}")

        # Run analysis
        print(f"\n🔬 Starting incremental analysis for @{target_username}...")
        print("This will fetch data in batches to avoid rate limiting.")
        print()

        analyzer.run_analysis(target_username)

        return 0

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 130
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
