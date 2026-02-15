"""
Main CLI orchestration for Instagram Followers Checker.

This module handles argument parsing and routing to the appropriate mode
(manual export or API mode).
"""
import argparse
from pathlib import Path
import sys
from typing import Optional

from .manual_mode import run_manual_mode
from ..storage.history import HistoryManager
from ..output.display import ConsoleDisplay
from ..analysis.comparison import AnalysisComparator
from ..models import Analysis


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog='igfc',
        description='Instagram Followers Checker - Dual Mode Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Manual Export Mode (Recommended):
    python igfc.py analyze --export ~/Downloads/instagram-export
    python igfc.py analyze --interactive

  API Mode (Experimental):
    python igfc.py api --username myuser --experimental

  Other Commands:
    python igfc.py history --list
    python igfc.py help --download-guide

For more information, visit: https://github.com/yourusername/ig-followers-checker
        """
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Analyze command (manual export mode - recommended)
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze followers using manual export (recommended)',
        description='Analyze your Instagram followers using a manual data export'
    )
    analyze_parser.add_argument(
        '--export',
        type=str,
        metavar='PATH',
        help='Path to Instagram export directory or ZIP file'
    )
    analyze_parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode (prompts for export path)'
    )
    analyze_parser.add_argument(
        '--no-color',
        dest='no_color',
        action='store_true',
        help='Disable colours in console output (plain text)'
    )
    analyze_parser.add_argument(
        '--save',
        action='store_true',
        help='Save analysis to history'
    )
    analyze_parser.add_argument(
        '--format',
        type=str,
        choices=['console', 'csv', 'json', 'txt'],
        default='console',
        help='Output format (default: console)'
    )
    analyze_parser.add_argument(
        '--output',
        type=str,
        metavar='FILE',
        help='Output file path (for csv/json/txt formats)'
    )
    analyze_parser.add_argument(
        '--category',
        type=str,
        choices=['not_following_back', 'mutual_followers', 'fans', 'all'],
        default='not_following_back',
        help='Which category to export for csv format (default: not_following_back)'
    )
    analyze_parser.add_argument(
        '--all',
        dest='show_all',
        action='store_true',
        help='Print the full not-following-back list in the terminal (default: top 20)'
    )
    analyze_parser.add_argument(
        '--since',
        dest='since_days',
        type=int,
        metavar='DAYS',
        help='Only show not-following-back accounts followed in the last N days'
    )

    # API command (experimental mode - not recommended)
    api_parser = subparsers.add_parser(
        'api',
        help='Use API mode (experimental - not recommended)',
        description='EXPERIMENTAL: Use Instagram API to fetch follower data'
    )
    api_parser.add_argument(
        '--username',
        type=str,
        required=True,
        help='Your Instagram username'
    )
    api_parser.add_argument(
        '--target',
        type=str,
        help='Target username to analyze (default: your own account)'
    )
    api_parser.add_argument(
        '--experimental',
        action='store_true',
        required=True,
        help='Required flag to acknowledge API mode risks'
    )

    # Compare command
    compare_parser = subparsers.add_parser(
        'compare',
        help='Compare two analyses',
        description='Compare current analysis with a previous one'
    )
    compare_parser.add_argument(
        '--current',
        type=str,
        metavar='PATH',
        help='Path to current analysis'
    )
    compare_parser.add_argument(
        '--previous',
        type=str,
        metavar='PATH',
        help='Path to previous analysis'
    )
    compare_parser.add_argument(
        '--history',
        action='store_true',
        help='Compare with last analysis from history'
    )

    # Export command — runs analysis + exports to file in one step
    export_parser = subparsers.add_parser(
        'export',
        help='Analyze and export results directly to a file',
        description='Run analysis on an Instagram export and save results to a file'
    )
    export_parser.add_argument(
        '--export',
        type=str,
        required=True,
        metavar='PATH',
        help='Path to Instagram export directory'
    )
    export_parser.add_argument(
        '--format',
        type=str,
        choices=['csv', 'json', 'txt'],
        required=True,
        help='Output file format'
    )
    export_parser.add_argument(
        '--output',
        type=str,
        required=True,
        metavar='FILE',
        help='Output file path'
    )
    export_parser.add_argument(
        '--category',
        type=str,
        choices=['not_following_back', 'mutual_followers', 'fans', 'all'],
        default='not_following_back',
        help='Which category to export for csv format (default: not_following_back)'
    )

    # History command
    history_parser = subparsers.add_parser(
        'history',
        help='View analysis history',
        description='Manage and view historical analyses'
    )
    history_parser.add_argument(
        '--list',
        action='store_true',
        help='List all saved analyses'
    )
    history_parser.add_argument(
        '--view',
        type=str,
        metavar='DATE',
        help='View specific analysis by date'
    )
    history_parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean old analyses'
    )

    # Help command
    help_parser = subparsers.add_parser(
        'help',
        help='Show detailed help',
        description='Display detailed help and guides'
    )
    help_parser.add_argument(
        '--download-guide',
        action='store_true',
        help='Show Instagram data download guide'
    )

    return parser


def show_default_help():
    """
    Display default help when no command is provided.
    """
    print("""
╔══════════════════════════════════════════════════════════════╗
║          Instagram Followers Checker                         ║
╚══════════════════════════════════════════════════════════════╝

Usage: python igfc.py <command> [options]

Commands:
  analyze          Analyze followers (manual export mode - recommended) ⭐
  api              Use API mode (experimental - not recommended) ⚠️
  compare          Compare two analyses
  export           Export results to file
  history          View analysis history
  help             Show detailed help

Manual Export Mode (Recommended):
  python igfc.py analyze --export ~/Downloads/instagram-export
  python igfc.py analyze --interactive

API Mode (Experimental):
  python igfc.py api --username myuser --experimental

For detailed help: python igfc.py --help
For interactive mode: python igfc.py analyze --interactive
For download guide: python igfc.py help --download-guide
""")


def show_download_guide():
    """
    Display Instagram data download guide.
    """
    print("""
╔══════════════════════════════════════════════════════════════╗
║          Instagram Data Download Guide                       ║
╚══════════════════════════════════════════════════════════════╝

Step 1: Request Your Data
  1. Open Instagram app or website
  2. Go to: Settings → Security → Download Data
  3. Click "Request Download"
  4. Choose JSON format (not HTML)
  5. Submit request

Step 2: Wait for Email
  • Instagram will email you when data is ready
  • Usually takes 24-48 hours
  • Check spam folder if you don't see it

Step 3: Download the ZIP File
  • Click the link in the email
  • Download the ZIP file to your computer
  • Extract the ZIP file

Step 4: Run Analysis
  • Locate the extracted folder
  • Run: python igfc.py analyze --export /path/to/extracted/folder

That's it! Your analysis will be ready instantly.

Note: This only works for YOUR OWN account (can't analyze others)
""")


def run_compare_command(args) -> int:
    """Handle the ``compare`` subcommand."""
    import json

    history = HistoryManager()
    comparator = AnalysisComparator()

    if args.history:
        # Compare the two most recent saved analyses
        entries = history.list_analyses()
        if len(entries) < 2:
            print("Error: Need at least two saved analyses to compare.")
            print("Run: python igfc.py analyze --export PATH --save")
            return 1
        later   = history.load_analysis(entries[0]["filename"])
        earlier = history.load_analysis(entries[1]["filename"])

    elif args.current and args.previous:
        # Load from explicit file paths
        def _load(path_str: str) -> Analysis:
            p = Path(path_str).expanduser().resolve()
            if not p.exists():
                raise FileNotFoundError(f"File not found: {p}")
            return Analysis.from_dict(json.loads(p.read_text(encoding="utf-8")))
        try:
            earlier = _load(args.previous)
            later   = _load(args.current)
        except (FileNotFoundError, KeyError) as e:
            print(f"Error: {e}")
            return 1

    else:
        print("Error: Provide --history or both --current and --previous.")
        print("Example: python igfc.py compare --history")
        return 1

    # Ensure correct temporal order
    if later.analysis_date < earlier.analysis_date:
        earlier, later = later, earlier

    result = comparator.compare(earlier, later)
    display = ConsoleDisplay()
    display.display_comparison(result)
    return 0


def run_history_command(args) -> int:
    """Handle the ``history`` subcommand."""
    history = HistoryManager()

    if args.list:
        entries = history.list_analyses()
        if not entries:
            print("No saved analyses found.")
            print("Run: python igfc.py analyze --export PATH --save")
            return 0
        print(f"\n{'#':<4} {'Date':<22} {'Account':<20} {'Following':>10} {'Followers':>10} {'Not back':>10}")
        print("-" * 80)
        for i, e in enumerate(entries, 1):
            date_str = e['date'][:16].replace('T', ' ')
            print(
                f"{i:<4} {date_str:<22} @{e['target_username']:<19} "
                f"{e['following']:>10,} {e['followers']:>10,} {e['not_following_back']:>10,}"
            )
        print()
        return 0

    elif args.view:
        try:
            analysis = history.load_analysis(args.view)
        except (FileNotFoundError, ValueError) as e:
            print(f"Error: {e}")
            return 1
        display = ConsoleDisplay()
        display.display_complete_analysis(analysis)
        return 0

    elif args.clean:
        deleted = history.clean(keep=10)
        if deleted:
            print(f"✓ Deleted {deleted} old analysis file(s) (kept the 10 most recent).")
        else:
            print("Nothing to clean (10 or fewer analyses saved).")
        return 0

    else:
        # No flag provided — default to --list behaviour
        return run_history_command(type('A', (), {'list': True, 'view': None, 'clean': False})())


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    # Create parser
    parser = create_parser()

    # Parse arguments
    if argv is None:
        argv = sys.argv[1:]

    # Show default help if no arguments
    if not argv:
        show_default_help()
        return 0

    args = parser.parse_args(argv)

    # Handle commands
    try:
        if args.command == 'analyze':
            return run_manual_mode(args)

        elif args.command == 'api':
            try:
                from .api_mode import run_api_mode
            except ImportError as e:
                print(f"Error: API mode dependencies are not installed ({e})")
                print("Install them with: pip install instagrapi")
                return 1
            return run_api_mode(args)

        elif args.command == 'compare':
            return run_compare_command(args)

        elif args.command == 'export':
            # Reuse manual mode runner; it picks up --format, --output, --category
            args.interactive = False
            args.save = False
            return run_manual_mode(args)

        elif args.command == 'history':
            return run_history_command(args)

        elif args.command == 'help':
            if args.download_guide:
                show_download_guide()
                return 0
            else:
                parser.print_help()
                return 0

        else:
            show_default_help()
            return 0

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 130
    except Exception as e:
        print(f"\nError: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
