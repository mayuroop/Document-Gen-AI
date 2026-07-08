"""
File chunking utilities for processing large files.
"""
import os
from typing import Generator


# File extensions to process
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".cpp", ".c", ".h", ".hpp", ".cs", ".rb", ".php", ".swift",
    ".kt", ".scala", ".r", ".sql", ".graphql", ".proto",
    ".json", ".yaml", ".yml", ".toml", ".xml", ".env",
    ".md", ".txt", ".rst", ".html", ".css", ".scss", ".less",
    ".dockerfile", ".sh", ".bash", ".zsh", ".ps1",
    ".tf", ".hcl",  # Terraform
}

# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "vendor", "target",
    ".idea", ".vscode", ".vs", "coverage", ".cache",
    "egg-info", ".eggs", ".tox", ".mypy_cache",
}

# Max chunk size in characters
MAX_CHUNK_SIZE = 3000


def should_process_file(filepath: str, max_size_kb: int = 500) -> bool:
    """Determine if a file should be processed."""
    # Check extension
    ext = os.path.splitext(filepath)[1].lower()
    basename = os.path.basename(filepath).lower()

    # Special files without extensions
    special_files = {"dockerfile", "makefile", "rakefile", "gemfile", "procfile"}
    if ext not in SUPPORTED_EXTENSIONS and basename not in special_files:
        return False

    # Check file size
    try:
        size_kb = os.path.getsize(filepath) / 1024
        if size_kb > max_size_kb:
            return False
    except OSError:
        return False

    return True


def should_skip_directory(dirname: str) -> bool:
    """Check if a directory should be skipped."""
    return dirname in SKIP_DIRS or dirname.startswith(".")


def get_processable_files(repo_path: str, max_size_kb: int = 500) -> list[dict]:
    """Walk a repo directory and return list of processable files."""
    files = []

    for root, dirs, filenames in os.walk(repo_path):
        # Filter out directories to skip
        dirs[:] = [d for d in dirs if not should_skip_directory(d)]

        for filename in filenames:
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, repo_path)

            if should_process_file(filepath, max_size_kb):
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    files.append({
                        "path": rel_path.replace("\\", "/"),
                        "content": content,
                        "extension": os.path.splitext(filename)[1].lower(),
                        "size": len(content),
                    })
                except Exception:
                    continue

    return files


def chunk_content(content: str, max_size: int = MAX_CHUNK_SIZE) -> list[str]:
    """Split content into chunks, trying to break at logical boundaries."""
    if len(content) <= max_size:
        return [content]

    chunks = []
    lines = content.split("\n")
    current_chunk = []
    current_size = 0

    for line in lines:
        line_size = len(line) + 1  # +1 for newline
        if current_size + line_size > max_size and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_size = line_size
        else:
            current_chunk.append(line)
            current_size += line_size

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def get_language_from_extension(ext: str) -> str:
    """Map file extension to programming language name."""
    mapping = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".jsx": "React JSX", ".tsx": "React TSX", ".java": "Java",
        ".go": "Go", ".rs": "Rust", ".cpp": "C++", ".c": "C",
        ".cs": "C#", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift",
        ".kt": "Kotlin", ".scala": "Scala", ".r": "R",
        ".sql": "SQL", ".json": "JSON", ".yaml": "YAML",
        ".yml": "YAML", ".toml": "TOML", ".xml": "XML",
        ".md": "Markdown", ".html": "HTML", ".css": "CSS",
        ".scss": "SCSS", ".sh": "Shell", ".dockerfile": "Dockerfile",
        ".tf": "Terraform", ".graphql": "GraphQL", ".proto": "Protobuf",
    }
    return mapping.get(ext, "Unknown")
