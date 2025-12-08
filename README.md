# Instagram Followers Checker

A Python tool to analyze your Instagram followers and following lists, helping you identify who doesn't follow you back.

## Table of Contents

- [Instagram Followers Checker](#instagram-followers-checker)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Important Warnings](#important-warnings)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Configuration](#configuration)
    - [Session Persistence](#session-persistence)
    - [Rate Limiting Settings](#rate-limiting-settings)
    - [Device Settings](#device-settings)
  - [Understanding the Output](#understanding-the-output)
  - [Common Errors \& Troubleshooting](#common-errors--troubleshooting)
    - [1. `LoginRequired` Error](#1-loginrequired-error)
    - [2. `PleaseWaitFewMinutes` Error](#2-pleasewaitfewminutes-error)
    - [3. `ChallengeRequired` Error](#3-challengerequired-error)
    - [4. Session File Errors](#4-session-file-errors)
  - [Best Practices](#best-practices)
  - [Limitations](#limitations)
  - [Future Improvements](#future-improvements)
  - [Contributing](#contributing)
  - [License](#license)

## Features

- Login with session persistence (saves session to avoid repeated logins)
- Fetch followers and following lists for any public Instagram profile
- Compare lists to find users who don't follow you back
- Conservative rate limiting to avoid triggering Instagram's anti-bot protection
- Comprehensive error handling for common Instagram API issues
- Device mimicking to appear as a legitimate mobile client

## Important Warnings

**PLEASE READ BEFORE USING:**

1. **Use a dedicated test account** - Do NOT use your main Instagram account
2. **Instagram's API is restrictive** - This tool uses unofficial APIs that may trigger security checks
3. **Rate limiting is strict** - Running this script too frequently will get your account temporarily blocked
4. **Wait times are real** - If you get rate-limited, you must wait 6-24 hours before retrying
5. **Run sparingly** - Maximum 1-2 times per day when it works
6. **Account risks** - Your account may be flagged, require verification challenges, or be temporarily restricted

**Instagram considers automation tools against their Terms of Service. Use at your own risk.**

## Prerequisites

- Python 3.8 or higher
- An Instagram account (preferably a test/throwaway account)
- Stable internet connection

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/ig-followers-checker.git
   cd ig-followers-checker
   ```

2. **Create and activate a virtual environment:**

   ```bash
   # On Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate

   # On Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the script:**

   ```bash
   python src/igfc.py
   ```

2. **Follow the prompts:**
   - Enter your Instagram username
   - Enter your Instagram password
   - Enter the target profile to analyze (or leave blank to analyze your own profile)

3. **Wait for the analysis:**
   The script will:
   - Log into Instagram
   - Fetch user information
   - Retrieve followers list
   - Retrieve following list
   - Compare and display results

## Configuration

### Session Persistence

The tool automatically saves your login session to `session.json` to avoid repeated logins. This helps reduce the risk of rate limiting.

**To force a fresh login:**

```bash
rm session.json
```

### Rate Limiting Settings

The script uses conservative delays between requests (configurable in `src/igfc.py`):

- `MIN_DELAY = 2` seconds (minimum delay between requests)
- `MAX_DELAY = 5` seconds (maximum delay between requests)
- `OPERATION_COOLDOWN = 3` seconds (delay between major operations)

**Do not reduce these values** - they help prevent rate limiting.

### Device Settings

The tool mimics a OnePlus 3 device running Android 8.0. These settings are configured to appear as a legitimate mobile client to Instagram.

## Understanding the Output

The script provides a detailed analysis:

```text
============================================================
RESULTS
============================================================
Total followers:  150
Total following:  200
Not following back: 50 users
============================================================

Users who don't follow you back:
------------------------------------------------------------
    1. @username1            - Full Name 1
    2. @username2            - Full Name 2
    ...
------------------------------------------------------------
```

## Common Errors & Troubleshooting

### 1. `LoginRequired` Error

**Symptoms:** `403 Forbidden` error when fetching user data, despite successful login

**Causes:**

- Session not fully authenticated
- 2FA required but not completed
- Instagram flagged the login as suspicious

**Solutions:**

- Delete `session.json` and try again
- Log into Instagram app first to clear security flags
- Wait 6-24 hours before retrying
- Ensure 2FA is disabled on the test account

### 2. `PleaseWaitFewMinutes` Error

**Symptoms:** `401 Unauthorized` error with message "Please wait a few minutes before you try again"

**Causes:**

- Too many requests in a short period
- Instagram detected automated activity
- Account is temporarily rate-limited

**Solutions:**

- **STOP running the script immediately**
- Wait 6-24 hours (not just "a few minutes")
- Use a dedicated test account
- Run the script less frequently (max 1-2 times/day)

### 3. `ChallengeRequired` Error

**Symptoms:** Account flagged for verification

**Causes:**

- Instagram's anti-bot system detected suspicious activity
- Too many automated requests

**Solutions:**

- Complete the security challenge in the Instagram app
- Wait 6-24 hours before retrying
- Use a dedicated test account for automation
- Run the script less frequently

### 4. Session File Errors

**Symptoms:** Errors loading `session.json`

**Solutions:**

- Delete the session file: `rm session.json`
- The script will create a fresh session on next run

## Best Practices

1. **Use a Test Account**
   - Create a dedicated Instagram account for testing
   - Don't use your main personal account

2. **Run Sparingly**
   - Maximum 1-2 times per day
   - Don't run multiple times in quick succession
   - Allow 12-24 hours between runs

3. **Monitor for Errors**
   - If you get rate-limited, STOP immediately
   - Wait the full 6-24 hours before retrying
   - Don't try to "work around" rate limits

4. **Keep Dependencies Updated**

   ```bash
   pip install --upgrade -r requirements.txt
   ```

5. **Review Instagram's Terms**
   - Understand the risks
   - Know that automation may violate Instagram's ToS

## Limitations

- **Only works with public profiles** (or profiles you follow)
- **Rate limited by Instagram** - Cannot be used frequently
- **No 2FA support** - Must disable 2FA on the account
- **Unofficial API** - May break if Instagram changes their API
- **Account risks** - May trigger security checks or temporary bans
- **No historical tracking** (planned for future versions)
- **No export functionality** (planned for future versions)

## Future Improvements

Planned enhancements:

- **Code modularization** - Break into reusable modules
- **Environment variables** - Store credentials securely
- **Export options** - Save results to JSON/CSV/TXT
- **Historical tracking** - Compare changes over time
- **Web UI** - Flask/FastAPI dashboard
- **Enhanced analysis** - Mutual followers, fans, ghost followers
- **Docker support** - Containerized deployment
- **CI/CD pipeline** - Jenkins/GitHub Actions integration
- **Better error recovery** - Automatic retry with exponential backoff

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is provided as-is for educational purposes. Use at your own risk.

**Disclaimer:** This tool uses unofficial Instagram APIs and may violate Instagram's Terms of Service. The authors are not responsible for any consequences of using this tool, including but not limited to account restrictions, bans, or other penalties imposed by Instagram.

---

**Created with [instagrapi](https://github.com/adw0rd/instagrapi)** - A Python library for Instagram's private API.
