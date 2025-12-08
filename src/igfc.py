from instagrapi import Client
from instagrapi.exceptions import (
    ClientError,
    ChallengeRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
)
import os
import time

# Configuration Constants
SESSION_FILE = "session.json"
MIN_DELAY = 2  # Minimum delay between requests (seconds)
MAX_DELAY = 5  # Maximum delay between requests (seconds)
OPERATION_COOLDOWN = 3  # Delay between major operations (seconds)

print("=" * 60)
print("Instagram Followers Checker")
print("=" * 60)
print("\nIMPORTANT NOTES:")
print("- Use a dedicated/test account (not your personal account)")
print("- This tool uses Instagram's API which may trigger security checks")
print("- If you get 'challenge_required', wait 6-24 hours before retrying")
print("- Don't run this script too frequently (max 2-3 times per day)")
print("=" * 60)
print()

# Login
client = Client()

# Configure conservative delay range to avoid rate limiting
client.delay_range = [MIN_DELAY, MAX_DELAY]

# Configure device settings to mimic a real device
client.set_device({
    "app_version": "269.0.0.18.75",
    "android_version": 26,
    "android_release": "8.0.0",
    "dpi": "480dpi",
    "resolution": "1080x1920",
    "manufacturer": "OnePlus",
    "device": "ONEPLUS A3003",
    "model": "OnePlus3",
    "cpu": "qcom"
})

# To be improved -> move to env variables (see TODO)
username = input("Enter your Instagram username: ")
password = input("Enter your Instagram password: ")

# Session persistence logic
logged_in = False

if os.path.exists(SESSION_FILE):
    print("Found existing session file, attempting to reuse...")
    try:
        client.load_settings(SESSION_FILE)
        client.login(username, password)

        # Verify session is still valid
        client.get_timeline_feed()
        print("Successfully logged in using saved session!")
        logged_in = True
    except Exception as e:
        print(f"Saved session invalid, performing fresh login. Error: {e}")
        os.remove(SESSION_FILE)

# If no valid session, perform fresh login
if not logged_in:
    try:
        print("Logging in to Instagram...")
        client.login(username, password)

        # Verify session is actually working
        print("Verifying session...")
        client.get_timeline_feed()

        # Save session for future use
        client.dump_settings(SESSION_FILE)
        print("Successfully logged in and saved session!")
        logged_in = True

    except (ClientError, ChallengeRequired, LoginRequired, PleaseWaitFewMinutes) as e:
        error_message = str(e)

        if isinstance(e, PleaseWaitFewMinutes):
            print("\n" + "!" * 60)
            print("RATE LIMITED - Too many requests")
            print("!" * 60)
            print("\nInstagram has temporarily blocked your account from making requests.")
            print("\nWHAT THIS MEANS:")
            print("- You've made too many login attempts or API requests")
            print("- Despite the error saying 'few minutes', you likely need to wait 6-24 hours")
            print("\nWHAT TO DO:")
            print("1. Stop running the script immediately")
            print("2. Wait at least 6-24 hours before trying again")
            print("3. Use a dedicated test account (not your main account)")
            print("4. Run the script max 1-2 times per day when it works")
            print("!" * 60)
            raise
        elif "challenge_required" in error_message or isinstance(e, ChallengeRequired):
            print("\n" + "!" * 60)
            print("INSTAGRAM SECURITY CHALLENGE REQUIRED")
            print("!" * 60)
            print("\nYour account has been flagged for verification.")
            print("\nWHAT TO DO NOW:")
            print("1. Open the Instagram app on your phone")
            print("2. Complete the security verification challenge")
            print("3. Wait 6-24 hours before running this script again")
            print("4. Consider using a dedicated test account instead")
            print("\nWHY THIS HAPPENED:")
            print("- Instagram detected automated activity")
            print("- Too many requests in short time")
            print("- Using automation tools triggers their anti-bot system")
            print("\nBEST PRACTICE:")
            print("- Use a throwaway/test account for automation")
            print("- Wait longer between script runs (24+ hours)")
            print("- Run the script less frequently")
            print("!" * 60)
        else:
            print(f"\nLogin failed: {error_message}")
            print("\nPossible solutions:")
            print("1. Wait 2-6 hours (Instagram may have rate-limited you)")
            print("2. Verify your credentials are correct")
            print("3. Try logging in via the Instagram app first")
            print("4. Check if your account requires 2FA verification")
        raise

    except Exception as e:
        print(f"Unexpected error during login: {e}")
        raise

if not logged_in:
    print("Failed to establish Instagram session. Exiting.")
    exit(1)

# Get target user profile
print()
target_username = input(
    "Enter the profile name you want to double check (leave blank if you want to check your own profile): "
) or username

# Add cooldown before starting operations
print(f"\nPreparing to fetch data (waiting {OPERATION_COOLDOWN}s to avoid rate limiting)...")
time.sleep(OPERATION_COOLDOWN)

# Get user ID using alternative method (workaround for instagrapi bug)
print(f"\n[1/3] Fetching user information for @{target_username}...")
try:
    user_info = client.user_info_by_username_v1(target_username)
    user_id = user_info.pk
    print(f"      Found user: {user_info.full_name} (@{user_info.username})")
except (ClientError, ChallengeRequired, LoginRequired, PleaseWaitFewMinutes) as e:
    if isinstance(e, PleaseWaitFewMinutes):
        print("\n" + "!" * 60)
        print("RATE LIMITED - Instagram blocked your request")
        print("!" * 60)
        print("You need to wait 6-24 hours before trying again.")
        print("!" * 60)
    elif "challenge_required" in str(e) or isinstance(e, ChallengeRequired):
        print("\n" + "!" * 60)
        print("CHALLENGE REQUIRED - Account verification needed")
        print("!" * 60)
        print("Wait 6-24 hours and use a dedicated test account.")
        print("!" * 60)
    elif isinstance(e, LoginRequired):
        print("\n" + "!" * 60)
        print("LOGIN REQUIRED - Session not authenticated")
        print("!" * 60)
        print("Instagram rejected the request even though login appeared to succeed.")
        print("\nPossible causes:")
        print("- Your account requires 2FA verification")
        print("- Instagram flagged the login as suspicious")
        print("- Rate limiting or anti-bot detection triggered")
        print("\nSuggestions:")
        print("1. Delete session.json and try again")
        print("2. Log into Instagram app first to clear any security flags")
        print("3. Wait 6-24 hours before retrying")
        print("4. Use a dedicated test account instead of your main account")
        print("!" * 60)
    raise

# Add cooldown between operations
time.sleep(OPERATION_COOLDOWN)

# Get followers and following dict using private API (more reliable)
print("\n[2/3] Fetching followers list (this may take a moment)...")
try:
    followers = client.user_followers_v1(user_id)
    print(f"      Retrieved {len(followers)} followers")
except (ClientError, ChallengeRequired, LoginRequired, PleaseWaitFewMinutes) as e:
    if isinstance(e, PleaseWaitFewMinutes):
        print("\n" + "!" * 60)
        print("RATE LIMITED - Too many requests")
        print("!" * 60)
        print("\nInstagram says 'wait a few minutes' but you likely need to wait 6-24 hours.")
        print("\nThis happened because:")
        print("- You've been running the script too frequently")
        print("- Instagram detected automated activity")
        print("\nNext steps:")
        print("1. STOP running the script now")
        print("2. Wait 6-24 hours minimum")
        print("3. When you retry, only run the script 1-2 times per day maximum")
        print("4. Consider using a dedicated test account")
        print("!" * 60)
    elif "challenge_required" in str(e) or isinstance(e, ChallengeRequired):
        print("\n" + "!" * 60)
        print("CHALLENGE REQUIRED - Account verification needed")
        print("!" * 60)
        print("Your account has been flagged. Wait 6-24 hours.")
        print("!" * 60)
    elif isinstance(e, LoginRequired):
        print("\n" + "!" * 60)
        print("LOGIN REQUIRED - Session expired or not authenticated")
        print("!" * 60)
        print("Delete session.json and try again after 6-24 hours.")
        print("!" * 60)
    else:
        print(f"Failed to fetch followers using v1 API: {e}")
        print("This usually means Instagram has rate-limited your account.")
        print("Wait 6-24 hours before trying again.")
    raise

# Add cooldown between operations
time.sleep(OPERATION_COOLDOWN)

print("\n[3/3] Fetching following list (this may take a moment)...")
try:
    followees = client.user_following_v1(user_id)
    print(f"      Retrieved {len(followees)} following")
except (ClientError, ChallengeRequired, LoginRequired, PleaseWaitFewMinutes) as e:
    if isinstance(e, PleaseWaitFewMinutes):
        print("\n" + "!" * 60)
        print("RATE LIMITED - Too many requests")
        print("!" * 60)
        print("\nInstagram says 'wait a few minutes' but you likely need to wait 6-24 hours.")
        print("Wait before retrying and use the script less frequently (max 1-2 times/day).")
        print("!" * 60)
    elif "challenge_required" in str(e) or isinstance(e, ChallengeRequired):
        print("\n" + "!" * 60)
        print("CHALLENGE REQUIRED - Account verification needed")
        print("!" * 60)
        print("Your account has been flagged. Wait 6-24 hours.")
        print("!" * 60)
    elif isinstance(e, LoginRequired):
        print("\n" + "!" * 60)
        print("LOGIN REQUIRED - Session expired or not authenticated")
        print("!" * 60)
        print("Delete session.json and try again after 6-24 hours.")
        print("!" * 60)
    else:
        print(f"Failed to fetch following using v1 API: {e}")
        print("This usually means Instagram has rate-limited your account.")
        print("Wait 6-24 hours before trying again.")
    raise

# Convert lists to dictionaries (v1 API returns lists, not dicts)
followers_dict = {user.pk: user for user in followers}
followees_dict = {user.pk: user for user in followees}

# Comparison of user IDs
print("\nAnalyzing follower data...")
followers_ids = set(followers_dict.keys())
followees_ids = set(followees_dict.keys())
not_following_back = followees_ids - followers_ids

# Display results
print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)
print(f"Total followers:  {len(followers_ids)}")
print(f"Total following:  {len(followees_ids)}")
print(f"Not following back: {len(not_following_back)} users")
print("=" * 60)

if not_following_back:
    print("\nUsers who don't follow you back:")
    print("-" * 60)
    for i, user_id in enumerate(sorted(not_following_back), 1):
        user = followees_dict[user_id]
        print(f"  {i:3d}. @{user.username:20s} - {user.full_name}")
    print("-" * 60)
else:
    print("\nGreat! Everyone you follow also follows you back!")

print("\n" + "=" * 60)
print("Analysis complete!")
print("=" * 60)
