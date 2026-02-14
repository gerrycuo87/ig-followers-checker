"""
Manual export mode workflow for Instagram Followers Checker.

This module handles the primary/recommended mode where users analyze
their Instagram data using official data exports.
"""
from pathlib import Path
from typing import Optional
import argparse

from ..parsers.manual_export import ManualExportParser
from ..analysis.analyzer import FollowerAnalyzer
from ..output.display import ConsoleDisplay
from ..output.export import AnalysisExporter
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

  [3] Help & documentation
  [4] Exit

""")

    try:
        choice = input("Choice [1-4]: ").strip()

        if choice == '1':
            export_path_str = input("\nEnter path to Instagram export (folder or ZIP): ").strip()
            if not export_path_str:
                print("Error: Export path is required")
                return 1

            class _Args:
                export = export_path_str
                interactive = True
                save = False
                format = 'console'
                output = None
                category = 'not_following_back'

            return run_manual_mode(_Args())

        elif choice == '2':
            print("\nAPI mode requires command-line usage with --experimental flag")
            print("Run: python igfc.py api --username YOUR_USERNAME --experimental")
            return 1

        elif choice == '3':
            print("\nRun: python igfc.py help --download-guide")
            return 0

        elif choice == '4':
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
        Path to export, or None if cancelled.
    """
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


def run_manual_mode(args: argparse.Namespace) -> int:
    """
    Run manual export analysis mode.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    try:
        # Resolve export path
        if args.interactive or not getattr(args, 'export', None):
            export_path = prompt_for_export_path()
            if export_path is None:
                return 1
        else:
            export_path = Path(args.export).expanduser().resolve()
            if not export_path.exists():
                print(f"Error: Export path does not exist: {export_path}")
                return 1

        # Parse export files
        print("\n🔍 Parsing Instagram export...")
        parser = ManualExportParser()
        followers, following = parser.parse_export_directory(export_path)
        print(f"✓ Found {len(followers):,} followers")
        print(f"✓ Found {len(following):,} following")

        # Run analysis
        print("\n🔬 Analyzing relationships...")
        analyzer = FollowerAnalyzer()
        analysis = analyzer.analyze(
            followers=followers,
            following=following,
            target_username="unknown",
            source="manual_export",
        )
        print("✓ Analysis complete")

        # Output
        fmt = getattr(args, 'format', 'console')
        output_path = getattr(args, 'output', None)

        if fmt == 'console':
            use_colors = not getattr(args, 'no_color', False)
            show_all = getattr(args, 'show_all', False)
            display = ConsoleDisplay(use_colors=use_colors)
            display.display_complete_analysis(analysis, show_all=show_all)

        elif fmt in ('csv', 'json', 'txt'):
            if not output_path:
                print(f"Error: --output is required when using --format {fmt}")
                return 1
            _export(analysis, fmt, Path(output_path), getattr(args, 'category', 'not_following_back'))

        else:
            print(f"Error: Unknown format '{fmt}'")
            return 1

        # Save to history placeholder (Phase 2)
        if getattr(args, 'save', False):
            print("\n[History tracking coming in a future update]")

        return 0

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        return 1
    except ValueError as e:
        print(f"\nError: {e}")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def _export(analysis: Analysis, fmt: str, output_path: Path, category: str) -> None:
    """Run the appropriate exporter and print a confirmation message."""
    exporter = AnalysisExporter(analysis)

    if fmt == 'csv':
        count = exporter.to_csv(output_path, category=category)
    elif fmt == 'json':
        count = exporter.to_json(output_path)
    elif fmt == 'txt':
        count = exporter.to_txt(output_path)
    else:
        raise ValueError(f"Unknown format: {fmt}")

    print(f"\n✓ Exported {count:,} records to {output_path}")
