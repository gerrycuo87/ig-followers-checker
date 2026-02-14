"""
Manual export mode workflow for Instagram Followers Checker.

This module handles the primary/recommended mode where users analyze
their Instagram data using official data exports.
"""
import sys
from pathlib import Path
from typing import Optional
import argparse

from ..parsers.manual_export import ManualExportParser
from ..analysis.analyzer import FollowerAnalyzer
from ..models import Analysis


def show_interactive_menu() -> int:
    """
    Show interactive menu for mode selection.

    Returns:
        Exit code
    """
    print("""
╔══════════════════════════════════════════════════════════════╗
║          Instagram Followers Checker                         ║
╚══════════════════════════════════════════════════════════════╝

Choose analysis mode:

  [1] Manual Export Analysis (RECOMMENDED) ⭐
      ✓ Safe, fast, reliable
      → Requires Instagram data export

  [2] API Mode (EXPERIMENTAL) ⚠️
      ⚠ Slow, risky, not recommended
      → Read warnings before proceeding

  [3] View analysis history
  [4] Help & documentation
  [5] Exit

""")

    try:
        choice = input("Choice [1-5]: ").strip()

        if choice == '1':
            # Manual export mode
            export_path = input("\nEnter path to Instagram export (folder or ZIP): ").strip()
            if not export_path:
                print("Error: Export path is required")
                return 1

            # Create mock args object
            class Args:
                export = export_path
                interactive = True
                save = False
                format = 'console'
                output = None

            return run_manual_mode(Args())

        elif choice == '2':
            print("\nAPI mode requires command-line usage with --experimental flag")
            print("Run: python igfc.py api --username YOUR_USERNAME --experimental")
            return 1

        elif choice == '3':
            print("\nHistory functionality not yet implemented")
            return 1

        elif choice == '4':
            print("\nDocumentation functionality not yet implemented")
            print("For now, run: python igfc.py help --download-guide")
            return 0

        elif choice == '5':
            print("\nGoodbye!")
            return 0

        else:
            print(f"\nInvalid choice: {choice}")
            return 1

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 130


def prompt_for_export_path() -> Optional[Path]:
    """
    Interactively prompt user for export path.

    Returns:
        Path to export, or None if cancelled
    """
    print("\n" + "=" * 60)
    print("Manual Export Analysis")
    print("=" * 60)
    print("\nNeed help downloading your Instagram data?")
    print("Run: python igfc.py help --download-guide")
    print()

    export_path_str = input("Enter path to Instagram export (folder or ZIP): ").strip()

    if not export_path_str:
        print("Error: Export path is required")
        return None

    export_path = Path(export_path_str).expanduser().resolve()

    if not export_path.exists():
        print(f"Error: Path does not exist: {export_path}")
        return None

    return export_path


def display_analysis_results(analysis: Analysis):
    """
    Display analysis results to console.

    Args:
        analysis: Analysis object with results
    """
    print("\n" + "=" * 60)
    print("Analysis Results")
    print("=" * 60)
    print()

    # Overview
    print("📊 Overview:")
    print(f"   • Target Username:     @{analysis.target_username}")
    print(f"   • Total Following:     {len(analysis.following):,}")
    print(f"   • Total Followers:     {len(analysis.followers):,}")
    print(f"   • Analysis Date:       {analysis.analysis_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   • Data Source:         {analysis.source}")
    print()

    # Breakdown
    stats = analysis.statistics
    print("📈 Breakdown:")
    print(f"   • Not Following Back:  {len(analysis.not_following_back):,} accounts ({stats.get('not_following_back_percentage', 0):.1f}%)")
    print(f"   • Mutual Followers:    {len(analysis.mutual_followers):,} accounts ({stats.get('mutual_percentage', 0):.1f}%)")
    print(f"   • Fans (follow you):   {len(analysis.fans):,} accounts")
    print()

    # Ratios
    print("📊 Ratios:")
    print(f"   • Follower/Following:  {stats.get('follower_following_ratio', 0):.2f}:1")
    print()

    # Top accounts not following back
    if analysis.not_following_back:
        print("┌" + "─" * 58 + "┐")
        print("│ Accounts Not Following Back:" + " " * 30 + "│")
        print("├" + "─" * 58 + "┤")

        # Show up to 20 accounts
        display_count = min(20, len(analysis.not_following_back))
        for i, user in enumerate(analysis.not_following_back[:display_count], 1):
            username = f"@{user.username}"
            print(f"│  {i:2d}. {username:<52} │")

        if len(analysis.not_following_back) > display_count:
            remaining = len(analysis.not_following_back) - display_count
            print(f"│  ... and {remaining} more" + " " * (49 - len(str(remaining))) + "│")

        print("└" + "─" * 58 + "┘")
    else:
        print("✅ All accounts you follow are following you back!")

    print()


def run_manual_mode(args: argparse.Namespace) -> int:
    """
    Run manual export analysis mode.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        # Get export path
        if args.interactive or not args.export:
            export_path = prompt_for_export_path()
            if export_path is None:
                return 1
        else:
            export_path = Path(args.export).expanduser().resolve()

            if not export_path.exists():
                print(f"Error: Export path does not exist: {export_path}")
                return 1

        # Parse export
        print("\n🔍 Parsing Instagram export...")
        parser = ManualExportParser()

        followers, following = parser.parse_export_directory(export_path)

        print(f"✓ Found {len(followers):,} followers")
        print(f"✓ Found {len(following):,} following")

        # Analyze
        print("\n🔬 Analyzing relationships...")
        analyzer = FollowerAnalyzer()

        # Try to detect username from export (if available)
        target_username = "unknown"  # TODO: Extract from export if possible

        analysis = analyzer.analyze(
            followers=followers,
            following=following,
            target_username=target_username,
            source="manual_export"
        )

        print("✓ Analysis complete")

        # Display results based on format
        if args.format == 'console':
            display_analysis_results(analysis)
        elif args.format in ['csv', 'json', 'txt']:
            if not args.output:
                print(f"Error: --output required for {args.format} format")
                return 1
            print(f"\nExport to {args.format} not yet implemented")
            print(f"Would export to: {args.output}")
            return 1
        else:
            print(f"Error: Unknown format: {args.format}")
            return 1

        # Save to history if requested
        if args.save:
            print("\n💾 Saving to history...")
            print("History functionality not yet implemented")

        return 0

    except FileNotFoundError as e:
        print(f"\nError: File not found: {e}")
        return 1
    except ValueError as e:
        print(f"\nError: {e}")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
