"""
GitHub repository cloning and management service.
"""
import os
import shutil
import logging
from pathlib import Path
from git import Repo, GitCommandError
from app.config import settings
from app.core.security import validate_github_url, sanitize_repo_url, extract_repo_info

logger = logging.getLogger(__name__)


class GitHubService:
    """Handles GitHub repo cloning and management."""

    def __init__(self):
        self.clone_dir = Path(settings.clone_dir)
        self.clone_dir.mkdir(parents=True, exist_ok=True)
        self.github_token = settings.github_token

    def _get_clone_path(self, owner: str, repo: str) -> Path:
        """Get the local path for a cloned repo."""
        return self.clone_dir / f"{owner}__{repo}"

    def _get_auth_url(self, url: str) -> str:
        """Add authentication token to URL if available."""
        if self.github_token:
            return url.replace("https://", f"https://{self.github_token}@")
        return url

    async def clone_repo(self, repo_url: str) -> dict:
        """
        Clone a GitHub repository.
        Returns dict with clone info.
        """
        if not validate_github_url(repo_url):
            raise ValueError(f"Invalid GitHub URL: {repo_url}")

        clean_url = sanitize_repo_url(repo_url)
        info = extract_repo_info(clean_url)
        clone_path = self._get_clone_path(info["owner"], info["repo"])

        # Remove existing clone if present
        if clone_path.exists():
            shutil.rmtree(clone_path, ignore_errors=True)

        try:
            logger.info(f"📥 Cloning {info['full_name']} to {clone_path}")
            auth_url = self._get_auth_url(clean_url)

            # Clone with depth=1 for speed
            Repo.clone_from(
                auth_url,
                str(clone_path),
                depth=1,
                no_single_branch=False,
            )

            logger.info(f"✅ Successfully cloned {info['full_name']}")

            return {
                "clone_path": str(clone_path),
                "owner": info["owner"],
                "repo": info["repo"],
                "full_name": info["full_name"],
            }

        except GitCommandError as e:
            logger.error(f"❌ Git clone failed: {e}")
            raise RuntimeError(f"Failed to clone repository: {str(e)}")

    async def cleanup_repo(self, owner: str, repo: str):
        """Remove a cloned repository."""
        clone_path = self._get_clone_path(owner, repo)
        if clone_path.exists():
            shutil.rmtree(clone_path, ignore_errors=True)
            logger.info(f"🗑️ Cleaned up {owner}/{repo}")

    def get_repo_path(self, owner: str, repo: str) -> str | None:
        """Get path to cloned repo if it exists."""
        clone_path = self._get_clone_path(owner, repo)
        if clone_path.exists():
            return str(clone_path)
        return None


github_service = GitHubService()
