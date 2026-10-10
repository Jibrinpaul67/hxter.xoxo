import requests
from getpass import getpass

API = "https://api.github.com"


def get_all_pages(url, headers):
    """Fetch every page of a GitHub API list."""
    results = []
    page = 1

    while True:
        response = requests.get(
            url,
            headers=headers,
            params={"per_page": 100, "page": page},
            timeout=30,
        )
        response.raise_for_status()

        batch = response.json()
        if not batch:
            break

        results.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    return results


def main():
    token = getpass("Enter your GitHub token: ").strip()

    if not token:
        print("No token provided.")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        response = requests.get(
            f"{API}/user", headers=headers, timeout=30
        )
        response.raise_for_status()
        me = response.json()

        username = me["login"]
        print(f"\nLogged in as: @{username}")
        print("Fetching followers and following...")

        following = get_all_pages(
            f"{API}/user/following", headers
        )
        followers = get_all_pages(
            f"{API}/user/followers", headers
        )

        follower_names = {
            user["login"].lower() for user in followers
        }

        not_following_back = [
            user for user in following
            if user["login"].lower() not in follower_names
        ]

        print(f"\nYou follow: {len(following)}")
        print(f"Your followers: {len(followers)}")
        print(
            "Not following you back: "
            f"{len(not_following_back)}"
        )

        if not not_following_back:
            print("\nEveryone you follow follows you back!")
            return

        print("\n--- ACCOUNTS NOT FOLLOWING YOU BACK ---")

        for index, user in enumerate(not_following_back, 1):
            print(
                f"{index}. @{user['login']} - "
                f"https://github.com/{user['login']}"
            )

        print("\nOptions:")
        print("1. Unfollow selected accounts")
        print("2. Unfollow ALL accounts on this list")
        print("3. Exit without unfollowing")

        choice = input("\nChoose (1/2/3): ").strip()

        if choice == "3":
            print("No accounts unfollowed.")
            return

        if choice == "1":
            selected = input(
                "Enter account numbers separated by commas "
                "(e.g. 1,3,5): "
            )

            try:
                indexes = sorted({
                    int(item.strip()) for item in selected.split(",")
                })

                if any(
                    index < 1 or index > len(not_following_back)
                    for index in indexes
                ):
                    print("Invalid account number.")
                    return

                targets = [
                    not_following_back[index - 1]
                    for index in indexes
                ]

            except ValueError:
                print("Invalid input.")
                return

        elif choice == "2":
            targets = not_following_back
        else:
            print("Invalid choice.")
            return

        print("\nYou are about to unfollow:")
        for user in targets:
            print(f"- @{user['login']}")

        confirm = input(
            f"\nConfirm unfollowing {len(targets)} accounts? "
            "Type YES to proceed: "
        )

        if confirm != "YES":
            print("Cancelled. No accounts unfollowed.")
            return

        for user in targets:
            response = requests.delete(
                f"{API}/user/following/{user['login']}",
                headers=headers,
                timeout=30,
            )

            if response.status_code == 204:
                print(f"Unfollowed @{user['login']}")
            else:
                print(
                    f"Failed: @{user['login']} "
                    f"(HTTP {response.status_code})"
                )

        print("\nFinished!")

    except requests.RequestException as error:
        print(f"\nGitHub API error: {error}")
        print(
            "Check your internet connection, token, "
            "permissions, and GitHub API rate limits."
        )


if __name__ == "__main__":
    main()