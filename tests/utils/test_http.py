from fcoverage.utils.http import get_github_repo_details

def test_get_github_repo_details(mock_requests_get_github):
    result = get_github_repo_details("https://github.com/octocat/Hello-World")
    assert result['owner'] == "octocat"
    assert result['repo_name'] == "Hello-World"
    assert result['description'] == "This your first repo!"