from fcoverage.utils.http import get_github_repo_details


def test_get_github_repo_details(mock_requests_get_github):
    result = get_github_repo_details("https://github.com/acme/dummy_project")
    assert result["owner"] == "acme"
    assert result["repo_name"] == "dummy_project"
    assert result["description"] == "This your first repo!"
