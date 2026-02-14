"""
Rich console display for Instagram Followers Checker.

Provides beautiful, coloured terminal output for analysis results using the
`rich` library.
"""
from datetime import datetime
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule

from ..models import Analysis, User

console = Console()


def _format_pct(value: float) -> Text:
    """Return a coloured percentage text: green ≥ 80%, yellow ≥ 50%, red < 50%."""
    s = f"{value:.1f}%"
    if value >= 80:
        return Text(s, style="bold green")
    elif value >= 50:
        return Text(s, style="bold yellow")
    else:
        return Text(s, style="bold red")


def _format_count(value: int) -> str:
    return f"{value:,}"


class ConsoleDisplay:
    """Rich console output for analysis results."""

    def __init__(self, use_colors: bool = True):
        """
        Initialize the display.

        Args:
            use_colors: If False, disable colour output (plain text mode).
        """
        self._console = Console(highlight=False) if use_colors else Console(highlight=False, no_color=True)

    # ------------------------------------------------------------------
    # Public display methods
    # ------------------------------------------------------------------

    def display_complete_analysis(self, analysis: Analysis, show_all: bool = False):
        """
        Display the full analysis report.

        Args:
            analysis: Analysis object with all results.
            show_all: If True, print the full not-following-back list instead of
                      capping at 20 entries.
        """
        self._print_header()
        self._print_overview(analysis)
        self._print_breakdown(analysis)
        limit = None if show_all else 20
        self._print_not_following_back(analysis.not_following_back, limit=limit)
        self._print_footer(analysis)

    def display_overview(self, analysis: Analysis):
        """Display overview section only."""
        self._print_overview(analysis)

    def display_breakdown(self, analysis: Analysis):
        """Display breakdown section only."""
        self._print_breakdown(analysis)

    def display_not_following_back(self, users: List[User], limit: Optional[int] = 20):
        """Display not-following-back list only."""
        self._print_not_following_back(users, limit=limit)

    # ------------------------------------------------------------------
    # Internal rendering
    # ------------------------------------------------------------------

    def _print_header(self):
        self._console.print()
        self._console.print(Rule("[bold cyan]Analysis Results[/bold cyan]", style="cyan"))

    def _print_overview(self, analysis: Analysis):
        stats = analysis.statistics

        table = Table(box=None, show_header=False, padding=(0, 2))
        table.add_column(style="dim")
        table.add_column()

        table.add_row("Target account",   f"[bold]@{analysis.target_username}[/bold]")
        table.add_row("Analysis date",    analysis.analysis_date.strftime("%Y-%m-%d %H:%M"))
        table.add_row("Data source",      analysis.source.replace("_", " ").title())
        table.add_row("Total followers",  f"[cyan]{_format_count(stats['total_followers'])}[/cyan]")
        table.add_row("Total following",  f"[cyan]{_format_count(stats['total_following'])}[/cyan]")
        table.add_row(
            "Follower / following ratio",
            f"[bold]{stats['follower_following_ratio']:.2f}[/bold] : 1"
        )

        self._console.print()
        self._console.print(Panel(table, title="[bold]Overview[/bold]", border_style="cyan", padding=(1, 2)))

    def _print_breakdown(self, analysis: Analysis):
        stats = analysis.statistics
        total_following = stats["total_following"]
        total_followers = stats["total_followers"]

        table = Table(box=box.SIMPLE_HEAD, show_header=True, padding=(0, 2))
        table.add_column("Category",   style="bold")
        table.add_column("Count",      justify="right")
        table.add_column("% following", justify="right")
        table.add_column("% followers", justify="right")

        # Not following back
        nfb_count = stats["not_following_back_count"]
        nfb_pct = (nfb_count / total_following * 100) if total_following else 0
        table.add_row(
            "[red]Not following back[/red]",
            f"[red]{_format_count(nfb_count)}[/red]",
            _format_pct(nfb_pct),
            "—",
        )

        # Mutual followers
        mutual_count = stats["mutual_followers_count"]
        mutual_pct = (mutual_count / total_following * 100) if total_following else 0
        table.add_row(
            "[green]Mutual followers[/green]",
            f"[green]{_format_count(mutual_count)}[/green]",
            _format_pct(mutual_pct),
            "—",
        )

        # Fans
        fans_count = stats["fans_count"]
        fans_pct = (fans_count / total_followers * 100) if total_followers else 0
        table.add_row(
            "[blue]Fans (follow you only)[/blue]",
            f"[blue]{_format_count(fans_count)}[/blue]",
            "—",
            _format_pct(fans_pct),
        )

        self._console.print()
        self._console.print(Panel(table, title="[bold]Breakdown[/bold]", border_style="cyan", padding=(1, 1)))

    def _print_not_following_back(self, users: List[User], limit: Optional[int] = 20):
        if not users:
            self._console.print()
            self._console.print(
                Panel(
                    "[bold green]Everyone you follow also follows you back! 🎉[/bold green]",
                    border_style="green",
                    padding=(1, 2),
                )
            )
            return

        table = Table(box=box.SIMPLE_HEAD, show_header=True, padding=(0, 2))
        table.add_column("#",        justify="right", style="dim")
        table.add_column("Username", style="bold red")

        display_count = len(users) if limit is None else min(limit, len(users))
        for i, user in enumerate(users[:display_count], 1):
            table.add_row(str(i), f"@{user.username}")

        title = f"[bold red]Not Following Back[/bold red] — {_format_count(len(users))} accounts"
        panel = Panel(table, title=title, border_style="red", padding=(1, 1))
        self._console.print()
        self._console.print(panel)

        if len(users) > display_count:
            remaining = len(users) - display_count
            self._console.print(
                f"  [dim]... and [bold]{_format_count(remaining)}[/bold] more "
                f"(use [bold]--all[/bold] to print all, or [bold]--format csv[/bold] to export)[/dim]"
            )

    def _print_footer(self, analysis: Analysis):
        self._console.print()
        self._console.print(Rule(style="dim"))
        self._console.print(
            "  [dim]Tip: print all in terminal with [bold]--all[/bold], "
            "or export with [bold]--format csv --output results.csv[/bold][/dim]"
        )
        self._console.print()
