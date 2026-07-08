"""
File processing service - traverses repos and prepares files for AI analysis.
"""
import logging
from app.utils.chunker import (
    get_processable_files,
    chunk_content,
    get_language_from_extension,
)
from app.config import settings

logger = logging.getLogger(__name__)


class FileProcessor:
    """Processes repository files for AI analysis."""

    def __init__(self):
        self.max_file_size_kb = settings.max_file_size_kb

    async def process_repository(self, repo_path: str) -> dict:
        """
        Process all files in a repository.
        Returns structured data about the repo.
        """
        logger.info(f"📂 Processing repository at: {repo_path}")

        files = get_processable_files(repo_path, self.max_file_size_kb)
        logger.info(f"Found {len(files)} processable files")

        # Categorize files
        categorized = {
            "source_files": [],
            "config_files": [],
            "doc_files": [],
            "total_files": len(files),
        }

        source_exts = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
            ".cpp", ".c", ".cs", ".rb", ".php", ".swift", ".kt", ".scala",
        }
        config_exts = {
            ".json", ".yaml", ".yml", ".toml", ".xml", ".env",
            ".dockerfile", ".tf",
        }
        doc_exts = {".md", ".txt", ".rst"}

        for file_info in files:
            ext = file_info["extension"]
            if ext in source_exts:
                categorized["source_files"].append(file_info)
            elif ext in config_exts:
                categorized["config_files"].append(file_info)
            elif ext in doc_exts:
                categorized["doc_files"].append(file_info)
            else:
                categorized["source_files"].append(file_info)

        logger.info(
            f"Categorized: {len(categorized['source_files'])} source, "
            f"{len(categorized['config_files'])} config, "
            f"{len(categorized['doc_files'])} docs"
        )

        return categorized

    def prepare_file_for_ai(self, file_info: dict) -> list[dict]:
        """
        Prepare a file for AI analysis by chunking if necessary.
        Returns list of chunks with metadata.
        """
        chunks = chunk_content(file_info["content"])
        language = get_language_from_extension(file_info["extension"])

        return [
            {
                "path": file_info["path"],
                "language": language,
                "extension": file_info["extension"],
                "chunk_index": i,
                "total_chunks": len(chunks),
                "content": chunk,
            }
            for i, chunk in enumerate(chunks)
        ]

    def get_file_tree(self, files: list[dict]) -> dict:
        """Build a file tree structure from file list."""
        tree = {}
        for f in files:
            parts = f["path"].split("/")
            current = tree
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = {
                "type": "file",
                "extension": f["extension"],
                "size": f["size"],
            }
        return tree


file_processor = FileProcessor()
