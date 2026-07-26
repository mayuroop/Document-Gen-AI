"""
GitHub repository cloning and management service.
"""
import os
import shutil
import logging
import io
import zipfile
import httpx
from pathlib import Path

# Disable GitPython executable lookup failure in serverless environments (Vercel)
os.environ["GIT_PYTHON_REFRESH"] = "0"
os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = "git"

try:
    from git import Repo, GitCommandError
    HAS_GIT = True
except Exception:
    Repo = None
    GitCommandError = Exception
    HAS_GIT = False

from app.config import settings
from app.core.security import validate_github_url, sanitize_repo_url, extract_repo_info

logger = logging.getLogger(__name__)


class GitHubService:
    """Handles GitHub repo cloning and management."""

    def __init__(self):
        clone_path_str = getattr(settings, "effective_clone_dir", settings.clone_dir)
        self.clone_dir = Path(clone_path_str)
        try:
            self.clone_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            self.clone_dir = Path("/tmp/cloned_repos")
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

    async def _download_zip(self, owner: str, repo: str, clone_path: Path):
        """Fallback method to download repo as zip archive when git executable is not available."""
        urls = [
            f"https://api.github.com/repos/{owner}/{repo}/zipball",
            f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip",
            f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip",
        ]
        headers = {"User-Agent": "FastAPI-DocGen"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        download_success = False
        content = None

        async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
            for url in urls:
                try:
                    res = await client.get(url, headers=headers)
                    if res.status_code == 200:
                        content = res.content
                        download_success = True
                        break
                except Exception as e:
                    logger.warning(f"Failed zip fetch from {url}: {e}")

        if not download_success or not content:
            raise RuntimeError(f"Failed to download repository archive for {owner}/{repo}")

        with zipfile.ZipFile(io.BytesIO(content)) as z:
            members = z.namelist()
            top_dir = members[0].split("/")[0] if members and "/" in members[0] else ""
            clone_path.mkdir(parents=True, exist_ok=True)
            for member in members:
                if member.endswith("/"):
                    continue
                if top_dir and member.startswith(top_dir + "/"):
                    rel_name = member[len(top_dir) + 1:]
                else:
                    rel_name = member
                if not rel_name:
                    continue
                target_file = clone_path / rel_name
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with z.open(member) as src, open(target_file, "wb") as dst:
                    shutil.copyfileobj(src, dst)

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

        logger.info(f"📥 Fetching {info['full_name']} to {clone_path}")

        cloned_with_git = False
        if HAS_GIT and Repo is not None:
            try:
                auth_url = self._get_auth_url(clean_url)
                Repo.clone_from(
                    auth_url,
                    str(clone_path),
                    depth=1,
                    no_single_branch=False,
                )
                cloned_with_git = True
                logger.info(f"✅ Successfully cloned {info['full_name']} with git")
            except Exception as e:
                logger.warning(f"Git clone failed or unavailable ({e}), falling back to zip download...")

        if not cloned_with_git:
            await self._download_zip(info["owner"], info["repo"], clone_path)
            logger.info(f"✅ Successfully downloaded {info['full_name']} via zip archive")

        return {
            "clone_path": str(clone_path),
            "owner": info["owner"],
            "repo": info["repo"],
            "full_name": info["full_name"],
        }

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
