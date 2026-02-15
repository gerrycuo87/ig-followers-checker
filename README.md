# Instagram Followers Checker

A Python tool to analyze your Instagram followers and following lists, helping you identify who doesn't follow you back.

Two modes are available:
- **Manual Export Mode** (recommended) — safe, fast, ToS-compliant
- **API Mode** (experimental) — slow, risky, requires daily runs for weeks

---

## Table of Contents

- [Quick Start](#quick-start)
- [Manual Export Mode](#manual-export-mode-recommended)
- [API Mode](#api-mode-experimental)
- [Installation](#installation)
- [Usage](#usage)
- [Understanding the Output](#understanding-the-output)
- [History & Comparison](#history--comparison)
- [Project Structure](#project-structure)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [License](#license)

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Analyze your Instagram export (recommended)
python igfc.py analyze --export ~/Downloads/instagram-export

# Show all available commands
python igfc.py --help
```

---

## Manual Export Mode (Recommended)

This is the primary and recommended way to use the tool.

**Why use it:**
- 100% ToS-compliant — zero risk of account ban
- Fast — download takes ~48 hours, analysis is instant
- Reliable — no API failures or rate limiting
- Complete — all followers and following in one file
- Only works for your own account

### How to get your Instagram export

1. Open Instagram → **Settings** → **Security** → **Download Data**
2. Select **JSON** format and request the download
3. Wait for Instagram's email (~48 hours)
4. Download and extract the ZIP file
5. Run the tool:

```bash
python igfc.py analyze --export /path/to/extracted-folder
```

---

## API Mode (Experimental)

This mode fetches data directly from Instagram's API.

> **⚠️ WARNING:** API mode violates Instagram's Terms of Service and risks account suspension. It is extremely slow (16–40 days for large accounts) and must be run daily for weeks. Use Manual Export Mode instead whenever possible.

API mode is only useful if you need to analyze **someone else's public account** and fully understand and accept the risks.

```bash
python igfc.py api --username YOUR_USERNAME --experimental
```

The `--experimental` flag is required and triggers multiple confirmation prompts.

---

## Installation

**Requirements:** Python 3.8 or higher

```bash
git clone https://github.com/yourusername/ig-followers-checker.git
cd ig-followers-checker

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Command reference

```bash
# General
python igfc.py                                                   # Show help
python igfc.py --help                                            # Full command documentation
python igfc.py help --download-guide                             # Step-by-step export guide

# Analyze — display results in the terminal
python igfc.py analyze --export PATH                             # Coloured console output
python igfc.py analyze --export PATH --no-color                  # No colours (boxes kept)
python igfc.py analyze --export PATH --all                       # Print full not-following-back list
python igfc.py analyze --export PATH --since 30                  # Only accounts followed in last 30 days
python igfc.py analyze --export PATH --save                      # Save analysis to history
python igfc.py analyze --interactive                             # Prompt for path interactively

# Analyze — export results directly to a file
python igfc.py analyze --export PATH --format csv --output results.csv
python igfc.py analyze --export PATH --format csv --output results.csv --category all
python igfc.py analyze --export PATH --format json --output results.json
python igfc.py analyze --export PATH --format txt  --output results.txt

# Export command — same as analyze but skips the console display
python igfc.py export --export PATH --format csv  --output results.csv
python igfc.py export --export PATH --format json --output results.json
python igfc.py export --export PATH --format txt  --output results.txt

# History
python igfc.py history --list                                    # List all saved analyses
python igfc.py history --view 2025-12-15                         # View a specific saved analysis
python igfc.py history --clean                                   # Delete old analyses (keeps 10 most recent)

# Compare two analyses
python igfc.py compare --history                                 # Compare the two most recent saves
python igfc.py compare --current new.json --previous old.json    # Compare specific files

# API mode (experimental)
python igfc.py api --username USER --experimental                # See warnings above
```

### CSV category filter

When exporting to CSV you can choose which group to include via `--category`:

| Value | Description |
|-------|-------------|
| `not_following_back` | Accounts you follow that don't follow back *(default)* |
| `mutual_followers` | Accounts you both follow each other |
| `fans` | Accounts that follow you but you don't follow back |
| `all` | All three groups combined (adds a `category` column) |

### Interactive mode

Running `python igfc.py analyze --interactive` prompts you for the export path instead of requiring it on the command line.

---

## Understanding the Output

The default console output has four sections (rendered with colours in a modern terminal):

**Overview** — follower/following counts, ratio, analysis date, and data source.

**Breakdown** — the three relationship categories with counts and percentages. Percentages are colour-coded: green (≥ 80%), yellow (≥ 50%), red (< 50%).

**Insights** — a set of human-readable observations derived from the numbers (e.g. ratios, fan count, reciprocity rate).

**Not Following Back** — numbered list of accounts, top 20 by default. Use `--all` to print the full list, or `--format csv` to export it.

```
─────────────────────── Analysis Results ───────────────────────

╭──────────────────────── Overview ─────────────────────────────╮
│  Target account               @yourname                       │
│  Analysis date                2025-12-15 14:30                │
│  Data source                  Manual Export                   │
│  Total followers              7,827                           │
│  Total following              905                             │
│  Follower / following ratio   8.65 : 1                        │
╰───────────────────────────────────────────────────────────────╯

╭──────────────────────── Breakdown ────────────────────────────╮
│  Category                Count   % following   % followers    │
│  ─────────────────────────────────────────────────────────    │
│  Not following back        123         13.6%              —   │
│  Mutual followers          782         86.4%              —   │
│  Fans (follow you only)  7,045             —          90.0%   │
╰───────────────────────────────────────────────────────────────╯

╭──────────────────────── Insights ─────────────────────────────╮
│  • 13.6% of accounts you follow don't follow you back (123)   │
│  • 86.4% of accounts you follow are mutual followers          │
│  • 7,045 accounts follow you that you don't follow back       │
│  • Your follower / following ratio is 8.65 : 1 (excellent)   │
╰───────────────────────────────────────────────────────────────╯

╭──────────── Not Following Back — 123 accounts ─────────────────╮
│   1  @account_one                                              │
│   2  @account_two                                              │
│  ...                                                           │
╰────────────────────────────────────────────────────────────────╯
  ... and 103 more (use --all to print all, or --format csv to export)
```

| Category | Description |
|----------|-------------|
| Not Following Back | Accounts you follow that don't follow you back |
| Mutual Followers | Accounts you both follow each other |
| Fans | Accounts that follow you but you don't follow back |

---

## History & Comparison

Save any analysis and compare snapshots over time to track follower changes.

### Saving an analysis

```bash
python igfc.py analyze --export PATH --save
```

Saves the result to `data/history/analysis-YYYY-MM-DD-HHMMSS.json`.

### Listing and viewing past analyses

```bash
python igfc.py history --list          # table of all saved runs
python igfc.py history --view 2025-12-15   # re-display a past analysis
python igfc.py history --clean         # delete all but the 10 most recent
```

### Comparing two analyses

```bash
python igfc.py compare --history                              # two most recent saves
python igfc.py compare --current new.json --previous old.json # specific files
```

The comparison output shows a summary table and colour-coded lists for:
- New followers gained
- Followers lost
- Accounts you newly followed
- Accounts you unfollowed
- Accounts that are newly not following you back

---

## Project Structure

```
ig-followers-checker/
├── igfc.py                          # Main entry point
├── src/
│   ├── models.py                    # User and Analysis data models
│   ├── config.py                    # Configuration constants
│   ├── analyzer.py                  # API mode orchestrator
│   │
│   ├── parsers/
│   │   ├── manual_export.py         # Instagram JSON export parser
│   │   └── instagram_api.py         # API-based data fetcher
│   │
│   ├── analysis/
│   │   ├── analyzer.py              # Core comparison logic (parser-agnostic)
│   │   ├── comparison.py            # Compare two Analysis snapshots
│   │   ├── filters.py               # Filter users by timestamp, count, etc.
│   │   └── statistics.py            # Human-readable insights engine
│   │
│   ├── storage/
│   │   ├── cache.py                 # Progress cache for API mode
│   │   └── history.py               # Save / load / list past analyses
│   │
│   ├── output/
│   │   ├── display.py               # Rich console display
│   │   └── export.py                # CSV / JSON / TXT export
│   │
│   └── cli/
│       ├── main.py                  # CLI entry point and argument parsing
│       ├── manual_mode.py           # Manual export workflow
│       └── api_mode.py              # API mode workflow with warnings
│
├── data/
│   └── history/                     # Saved analyses (gitignored)
│
└── tests/
    └── fixtures/                    # Sample export data for tests
```

---

## Limitations

### Manual Export Mode
- Only works for your own account
- Requires a one-time manual download step (~48 hour wait)
- Export must be re-downloaded for updated data
- No extended metadata (follower counts, verified status, etc.)

### API Mode
- Violates Instagram Terms of Service
- Very slow: 16–40 days for accounts with 8k–20k followers
- Must be run daily; can fail mid-process
- Risk of account suspension

---

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is provided as-is for educational purposes. Use at your own risk.

**Disclaimer:** The API mode uses unofficial Instagram APIs and may violate Instagram's Terms of Service. The authors are not responsible for any consequences, including account restrictions or bans.
