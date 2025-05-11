import requests


def get_github_repo_details(repo_url):
    """
    Extracts the owner and repository name from a GitHub repository URL.

    Args:
        repo_url (str): The GitHub repository URL.

    Returns:
        tuple: A tuple containing the owner and repository name.
    """
    if "github.com" not in repo_url:
        raise ValueError("Invalid GitHub URL")

    parts = repo_url.split("/")
    if len(parts) < 5:
        raise ValueError("Invalid GitHub URL format")

    owner = parts[3]
    repo_name = parts[4]

    url = f"https://api.github.com/repos/{owner}/{repo_name}"
    response = requests.get(url)

    if response.status_code == 200:
        metadata = response.json()
        return {
            "owner": metadata["owner"]["login"],
            "repo_name": metadata["name"],
            "description": metadata["description"]
        }
    else:
        raise Exception(f"Failed to fetch metadata: {response.status_code} - {response.text}")
