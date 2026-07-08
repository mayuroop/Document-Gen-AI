"""
Security utilities - input validation and sanitization.
"""
import re
from urllib.parse import urlparse


def validate_github_url(url: str) -> bool:
    """Validate that a URL is a legitimate GitHub repository URL."""
    if not url:
        return False

    # Clean the URL
    url = url.strip().rstrip("/")

    # Check for valid GitHub patterns
    patterns = [
        r"^https?://github\.com/[\w\-\.]+/[\w\-\.]+$",
        r"^https?://github\.com/[\w\-\.]+/[\w\-\.]+\.git$",
    ]

    for pattern in patterns:
        if re.match(pattern, url):
            return True

    return False


def sanitize_repo_url(url: str) -> str:
    """Sanitize and normalize a GitHub URL."""
    url = url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    return url


def extract_repo_info(url: str) -> dict:
    """Extract owner and repo name from GitHub URL."""
    url = sanitize_repo_url(url)
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")

    if len(parts) >= 2:
        return {
            "owner": parts[0],
            "repo": parts[1],
            "full_name": f"{parts[0]}/{parts[1]}",
        }
    return {"owner": "", "repo": "", "full_name": ""}


def is_safe_path(path: str) -> bool:
    """Check if a file path is safe (no traversal attacks)."""
    dangerous_patterns = ["..", "~", "$", "`", "|", ";", "&"]
    return not any(p in path for p in dangerous_patterns)
