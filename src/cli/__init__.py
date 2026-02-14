"""
CLI module for Instagram Followers Checker.

This module provides the command-line interface with dual modes:
- Manual Export Mode (recommended): Analyze Instagram data exports
- API Mode (experimental): Fetch data directly from Instagram API
"""
from .main import main

__all__ = ['main']
