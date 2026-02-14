#!/usr/bin/env python3
"""
Instagram Followers Checker - Entry point script.

This is the main entry point for running the Instagram Followers Checker.

Usage:
    python igfc.py                    # Show help
    python igfc.py analyze --export PATH  # Manual export mode (recommended)
    python igfc.py api --username USER --experimental  # API mode (experimental)

For more information: python igfc.py --help
"""

from src.cli import main

if __name__ == "__main__":
    exit(main())
