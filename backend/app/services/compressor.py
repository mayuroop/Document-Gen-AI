"""
Smart Code Compressor - Compresses entire repo into dense, structured blocks
for efficient AI documentation generation (18-25 calls total).

Strategy:
  1. Parse code locally (AST for Python, regex for JS/TS/Java)
  2. Extract signatures, routes, models, key logic
  3. Group by purpose (routes, models, services, config)
  4. Build a single compressed context document
  5. Skip per-file AI calls entirely
"""
import os
import re
import ast
import logging
from dataclasses import dataclass, field
from app.utils.chunker import (
    get_processable_files,
    get_language_from_extension,
    SKIP_DIRS,
)

logger = logging.getLogger(__name__)

# Max characters per compressed block
MAX_BLOCK_SIZE = 1500
# Max snippet lines to keep
MAX_SNIPPET_LINES = 12


@dataclass
class ExtractedInfo:
    """Extracted information from a single file."""
    path: str
    language: str
    functions: list = field(default_factory=list)
    classes: list = field(default_factory=list)
    api_routes: list = field(default_factory=list)
    db_models: list = field(default_factory=list)
    imports: list = field(default_factory=list)
    snippets: list = field(default_factory=list)
    summary_hint: str = ""


# ─── Python AST Parser ───────────────────────────────────────────────

def _parse_python(content: str, path: str) -> ExtractedInfo:
    info = ExtractedInfo(path=path, language="Python")
    try:
        tree = ast.parse(content)
    except SyntaxError:
        info.summary_hint = "Unparseable Python file"
        return info

    for node in ast.walk(tree):
        # Imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", None) or ""
            names = [a.name for a in node.names]
            imp = f"from {module} import {', '.join(names)}" if module else f"import {', '.join(names)}"
            info.imports.append(imp)

        # Functions
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = []
            for a in node.args.args:
                ann = ""
                if a.annotation:
                    try:
                        ann = f": {ast.unparse(a.annotation)}"
                    except Exception:
                        pass
                args.append(f"{a.arg}{ann}")

            ret = ""
            if node.returns:
                try:
                    ret = f" -> {ast.unparse(node.returns)}"
                except Exception:
                    pass

            sig = f"{'async ' if isinstance(node, ast.AsyncFunctionDef) else ''}def {node.name}({', '.join(args)}){ret}"
            doc = ast.get_docstring(node) or ""
            decorators = []
            for d in node.decorator_list:
                try:
                    decorators.append(f"@{ast.unparse(d)}")
                except Exception:
                    pass

            func_entry = {"signature": sig, "docstring": doc[:120], "decorators": decorators, "line": node.lineno}
            info.functions.append(func_entry)

            # Detect API routes (FastAPI / Flask)
            for dec_str in decorators:
                route_match = re.search(r'\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)', dec_str, re.I)
                if route_match:
                    info.api_routes.append({
                        "method": route_match.group(1).upper(),
                        "path": route_match.group(2),
                        "handler": node.name,
                        "docstring": doc[:80],
                    })

        # Classes
        elif isinstance(node, ast.ClassDef):
            doc = ast.get_docstring(node) or ""
            bases = []
            for b in node.bases:
                try:
                    bases.append(ast.unparse(b))
                except Exception:
                    pass

            methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            attrs = []
            for n in node.body:
                if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
                    try:
                        ann = ast.unparse(n.annotation)
                        attrs.append(f"{n.target.id}: {ann}")
                    except Exception:
                        attrs.append(n.target.id)

            cls_entry = {
                "name": node.name,
                "bases": bases,
                "docstring": doc[:120],
                "methods": methods[:15],
                "attributes": attrs[:15],
                "line": node.lineno,
            }
            info.classes.append(cls_entry)

            # Detect DB models
            model_bases = {"Model", "BaseModel", "Document", "Base", "DeclarativeBase", "SQLModel"}
            if any(b in model_bases for b in bases):
                info.db_models.append({
                    "name": node.name,
                    "fields": attrs[:20],
                    "bases": bases,
                })

    # Build a key snippet (first class or first few functions)
    lines = content.split("\n")
    if info.classes:
        start = info.classes[0]["line"] - 1
        info.snippets.append("\n".join(lines[start:start + MAX_SNIPPET_LINES]))
    elif info.functions:
        start = info.functions[0]["line"] - 1
        info.snippets.append("\n".join(lines[start:start + MAX_SNIPPET_LINES]))

    return info


# ─── JS/TS Regex Parser ──────────────────────────────────────────────

def _parse_js_ts(content: str, path: str, lang: str) -> ExtractedInfo:
    info = ExtractedInfo(path=path, language=lang)

    # Imports
    for m in re.finditer(r'import\s+.*?from\s+["\']([^"\']+)["\']', content):
        info.imports.append(m.group(0)[:100])

    # Functions (arrow + regular)
    for m in re.finditer(
        r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', content
    ):
        info.functions.append({"signature": f"function {m.group(1)}({m.group(2)[:60]})", "line": content[:m.start()].count("\n") + 1})

    # Arrow functions assigned to const
    for m in re.finditer(
        r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>', content
    ):
        info.functions.append({"signature": f"const {m.group(1)} = ({m.group(2)[:60]}) =>", "line": content[:m.start()].count("\n") + 1})

    # Classes
    for m in re.finditer(r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{', content):
        info.classes.append({"name": m.group(1), "bases": [m.group(2)] if m.group(2) else [], "line": content[:m.start()].count("\n") + 1})

    # Express/Fastify routes
    for m in re.finditer(
        r'(?:app|router|server)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)', content, re.I
    ):
        info.api_routes.append({"method": m.group(1).upper(), "path": m.group(2)})

    # React components
    for m in re.finditer(r'(?:export\s+default\s+)?function\s+([A-Z]\w+)\s*\(', content):
        info.summary_hint += f"React component: {m.group(1)}; "

    # DB models (Mongoose / Sequelize / Prisma patterns)
    for m in re.finditer(r'(?:mongoose\.model|Schema)\s*\(\s*["\'](\w+)', content):
        info.db_models.append({"name": m.group(1), "fields": []})

    # Key snippet
    lines = content.split("\n")
    if info.api_routes:
        for m in re.finditer(r'(?:app|router)\.(get|post|put|delete)', content):
            start = content[:m.start()].count("\n")
            info.snippets.append("\n".join(lines[start:start + MAX_SNIPPET_LINES]))
            break
    elif info.functions:
        start = info.functions[0].get("line", 1) - 1
        info.snippets.append("\n".join(lines[start:start + MAX_SNIPPET_LINES]))

    return info


# ─── Java Regex Parser ───────────────────────────────────────────────

def _parse_java(content: str, path: str) -> ExtractedInfo:
    info = ExtractedInfo(path=path, language="Java")

    for m in re.finditer(r'class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?\s*\{', content):
        info.classes.append({"name": m.group(1), "bases": [m.group(2)] if m.group(2) else []})

    for m in re.finditer(
        r'(?:public|private|protected)?\s*(?:static\s+)?(?:\w+)\s+(\w+)\s*\(([^)]*)\)', content
    ):
        info.functions.append({"signature": f"{m.group(1)}({m.group(2)[:60]})"})

    for m in re.finditer(r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)\s*\(\s*["\']?([^"\')\s]+)', content):
        method_map = {"GetMapping": "GET", "PostMapping": "POST", "PutMapping": "PUT", "DeleteMapping": "DELETE", "RequestMapping": "ALL"}
        info.api_routes.append({"method": method_map.get(m.group(1), "GET"), "path": m.group(2)})

    for m in re.finditer(r'@(Entity|Table|Document)', content):
        cls = re.search(r'class\s+(\w+)', content[m.end():m.end()+200])
        if cls:
            info.db_models.append({"name": cls.group(1), "fields": []})

    return info


# ─── Config/Doc Parsers ──────────────────────────────────────────────

def _parse_config(content: str, path: str, ext: str) -> ExtractedInfo:
    info = ExtractedInfo(path=path, language=get_language_from_extension(ext))
    # Keep config files mostly as-is but truncated
    info.snippets.append(content[:MAX_BLOCK_SIZE])
    if "package.json" in path:
        info.summary_hint = "NPM package manifest"
    elif "requirements" in path:
        info.summary_hint = "Python dependencies"
    elif "docker" in path.lower():
        info.summary_hint = "Docker configuration"
    return info


def _parse_markdown(content: str, path: str) -> ExtractedInfo:
    info = ExtractedInfo(path=path, language="Markdown")
    # Extract headings and first paragraph
    headings = re.findall(r'^#+\s+(.+)$', content, re.M)
    info.summary_hint = f"Headings: {', '.join(headings[:10])}"
    info.snippets.append(content[:800])
    return info


# ─── Main Compressor ─────────────────────────────────────────────────

PARSER_MAP = {
    ".py": lambda c, p: _parse_python(c, p),
    ".js": lambda c, p: _parse_js_ts(c, p, "JavaScript"),
    ".jsx": lambda c, p: _parse_js_ts(c, p, "React JSX"),
    ".ts": lambda c, p: _parse_js_ts(c, p, "TypeScript"),
    ".tsx": lambda c, p: _parse_js_ts(c, p, "React TSX"),
    ".java": lambda c, p: _parse_java(c, p),
}

CONFIG_EXTS = {".json", ".yaml", ".yml", ".toml", ".xml", ".env", ".dockerfile", ".tf"}
DOC_EXTS = {".md", ".txt", ".rst"}


class CodeCompressor:
    """
    Compresses an entire repository into a structured, information-dense
    context block suitable for AI documentation generation.

    Result: ~18-25 AI calls total (14 docs + 4 diagrams + optional chat).
    """

    def __init__(self, max_file_size_kb: int = 500):
        self.max_file_size_kb = max_file_size_kb

    def compress_repository(self, repo_path: str) -> dict:
        """
        Compress entire repo into structured blocks.
        Returns a dict with compressed context and extracted metadata.
        """
        logger.info(f"🗜️  Compressing repository: {repo_path}")

        files = get_processable_files(repo_path, self.max_file_size_kb)
        logger.info(f"Found {len(files)} files to compress")

        all_extractions: list[ExtractedInfo] = []
        for f in files:
            ext = f["extension"]
            parser = PARSER_MAP.get(ext)
            if parser:
                info = parser(f["content"], f["path"])
            elif ext in CONFIG_EXTS:
                info = _parse_config(f["content"], f["path"], ext)
            elif ext in DOC_EXTS:
                info = _parse_markdown(f["content"], f["path"])
            else:
                info = ExtractedInfo(path=f["path"], language=get_language_from_extension(ext))
                info.snippets.append(f["content"][:600])
            all_extractions.append(info)

        # Build compressed output
        compressed = self._build_compressed_context(all_extractions, files)
        logger.info(
            f"✅ Compression complete: {len(compressed['context'])} chars, "
            f"{compressed['stats']['total_functions']} functions, "
            f"{compressed['stats']['total_classes']} classes, "
            f"{compressed['stats']['total_routes']} API routes"
        )
        return compressed

    def _build_compressed_context(self, extractions: list[ExtractedInfo], raw_files: list) -> dict:
        """Build the final compressed context document."""

        # Collect stats
        all_functions = []
        all_classes = []
        all_routes = []
        all_models = []
        all_imports = set()
        file_analyses = []

        for info in extractions:
            all_functions.extend(info.functions)
            all_classes.extend(info.classes)
            all_routes.extend(info.api_routes)
            all_models.extend(info.db_models)
            all_imports.update(info.imports[:5])

            # Build per-file analysis (for frontend display)
            file_analyses.append({
                "path": info.path,
                "language": info.language,
                "summary": info.summary_hint or self._auto_summary(info),
                "functions": [f.get("signature", f.get("name", "")) for f in info.functions[:10]],
                "classes": [c.get("name", "") for c in info.classes],
                "imports": info.imports[:8],
                "apis": info.api_routes,
                "key_logic": "",
            })

        # ── Build the dense context string ──
        parts = []

        # 1. File tree
        parts.append("## PROJECT FILE STRUCTURE")
        for f in raw_files:
            parts.append(f"  {f['path']} ({f['extension']}, {f['size']}B)")

        # 2. API Routes
        if all_routes:
            parts.append("\n## API ENDPOINTS")
            for r in all_routes:
                handler = r.get("handler", "")
                doc = r.get("docstring", "")
                parts.append(f"  {r.get('method','?')} {r.get('path','?')} → {handler}  {doc}")

        # 3. Database Models
        if all_models:
            parts.append("\n## DATABASE MODELS")
            for m in all_models:
                fields = ", ".join(m.get("fields", [])[:12])
                parts.append(f"  {m['name']} [{', '.join(m.get('bases', []))}]: {fields}")

        # 4. Classes
        if all_classes:
            parts.append("\n## CLASSES")
            for c in all_classes:
                methods = ", ".join(c.get("methods", [])[:8])
                attrs = ", ".join(c.get("attributes", [])[:6])
                bases = ", ".join(c.get("bases", []))
                doc = c.get("docstring", "")
                parts.append(f"  class {c['name']}({bases}): {doc}")
                if attrs:
                    parts.append(f"    attrs: {attrs}")
                if methods:
                    parts.append(f"    methods: {methods}")

        # 5. Functions (grouped by file)
        parts.append("\n## FUNCTIONS & SIGNATURES")
        for info in extractions:
            if info.functions:
                parts.append(f"\n  # {info.path}")
                for f in info.functions[:12]:
                    sig = f.get("signature", str(f))
                    decs = " ".join(f.get("decorators", []))
                    doc = f.get("docstring", "")
                    line = f"    {decs} {sig}" if decs else f"    {sig}"
                    if doc:
                        line += f"  // {doc}"
                    parts.append(line)

        # 6. Key Code Snippets (most important files)
        parts.append("\n## KEY CODE SNIPPETS")
        snippet_count = 0
        for info in extractions:
            if info.snippets and snippet_count < 15:
                parts.append(f"\n  ### {info.path}")
                parts.append(f"  ```{info.language.lower()}")
                parts.append(info.snippets[0][:MAX_BLOCK_SIZE])
                parts.append("  ```")
                snippet_count += 1

        # 7. Key Dependencies
        if all_imports:
            parts.append("\n## KEY DEPENDENCIES")
            for imp in sorted(all_imports)[:30]:
                parts.append(f"  {imp}")

        context = "\n".join(parts)

        return {
            "context": context,
            "file_analyses": file_analyses,
            "api_endpoints": all_routes,
            "db_models": all_models,
            "stats": {
                "total_files": len(raw_files),
                "total_functions": len(all_functions),
                "total_classes": len(all_classes),
                "total_routes": len(all_routes),
                "total_models": len(all_models),
                "context_size_chars": len(context),
            },
            "file_tree": self._build_tree(raw_files),
        }

    def _auto_summary(self, info: ExtractedInfo) -> str:
        """Generate a quick summary from extracted info."""
        parts = []
        if info.api_routes:
            parts.append(f"{len(info.api_routes)} API routes")
        if info.classes:
            parts.append(f"Classes: {', '.join(c['name'] for c in info.classes[:3])}")
        if info.functions:
            parts.append(f"{len(info.functions)} functions")
        if info.db_models:
            parts.append(f"DB models: {', '.join(m['name'] for m in info.db_models)}")
        return "; ".join(parts) if parts else f"{info.language} file"

    def _build_tree(self, files: list) -> dict:
        """Build a file tree dict from file list."""
        tree = {}
        for f in files:
            parts = f["path"].split("/")
            current = tree
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = {"type": "file", "extension": f["extension"], "size": f["size"]}
        return tree


compressor = CodeCompressor()
