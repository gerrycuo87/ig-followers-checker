from instagrapi import Client

# Login
client = Client()
# To be improved -> move to env variables (see TODO)
username = input("Enter your Instagram username: ")
password = input("Enter your Instagram password: ")

client.login(username, password)

# Get target user profile
target_username = input(
    "Enter the profile name you want to double check (leave blank if you want to check your own profile): "
) or username
user_id = client.user_id_from_username(target_username)

# Get followers and following dict
followers = client.user_followers(user_id)
followees = client.user_following(user_id)

# Comparison of user IDs
followers_ids = set(followers)
followees_ids = set(followees)
not_following_back = followees_ids - followers_ids

# Get actual user objects from user IDs and display usernames
print(f"\nNot following back: {len(not_following_back)} users:")
for userId in not_following_back:
    user = followees[userId]
    print(f"  - @{user.username} ({user.full_name})")
