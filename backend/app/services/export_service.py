"""
Export service - generates downloadable documentation in various formats.
"""
import logging
from app.core.database import get_collection
import markdown

logger = logging.getLogger(__name__)

DOC_SECTION_NAMES = {
    "readme": "README",
    "architecture": "ARCHITECTURE",
    "api_docs": "API_DOCS",
    "database": "DATABASE",
    "setup": "SETUP",
    "deployment": "DEPLOYMENT",
    "troubleshooting": "TROUBLESHOOTING",
    "changelog": "CHANGELOG",
    "security": "SECURITY",
    "performance": "PERFORMANCE",
    "scalability": "SCALABILITY",
    "testing": "TESTING",
    "roadmap": "ROADMAP",
    "license": "LICENSE",
}


class ExportService:
    """Handles exporting documentation to various formats."""

    async def export_markdown(
        self, project_id: str, sections: list[str] | None = None
    ) -> dict[str, str]:
        """Export documentation as markdown files."""
        documents = get_collection("documents")
        doc = await documents.find_one({"project_id": project_id})

        if not doc:
            return {}

        documentation = doc.get("documentation", {})
        result = {}

        for key, content in documentation.items():
            if sections and key not in sections:
                continue
            filename = f"{DOC_SECTION_NAMES.get(key, key.upper())}.md"
            result[filename] = content

        # Add diagrams as a combined file
        diagrams = doc.get("diagrams", [])
        if diagrams:
            diagram_md = "# Project Diagrams\n\n"
            for diagram in diagrams:
                diagram_md += f"## {diagram.get('title', 'Diagram')}\n\n"
                diagram_md += f"```mermaid\n{diagram.get('mermaid_code', '')}\n```\n\n"
            result["DIAGRAMS.md"] = diagram_md

        return result

    async def export_html(self, project_id: str) -> str:
        """Export documentation as a single HTML page."""
        md_files = await self.export_markdown(project_id)

        if not md_files:
            return "<html><body><p>No documentation found.</p></body></html>"

        html_parts = [
            """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Documentation</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6; color: #1a1a2e; background: #f8f9fa;
            max-width: 900px; margin: 0 auto; padding: 2rem;
        }
        h1 { color: #6c5ce7; border-bottom: 3px solid #6c5ce7; padding-bottom: 0.5rem; margin: 2rem 0 1rem; }
        h2 { color: #2d3436; margin: 1.5rem 0 0.5rem; }
        h3 { color: #636e72; margin: 1rem 0 0.5rem; }
        code { background: #e9ecef; padding: 0.2rem 0.4rem; border-radius: 4px; font-size: 0.9em; }
        pre { background: #1a1a2e; color: #a8e6cf; padding: 1rem; border-radius: 8px; overflow-x: auto; margin: 1rem 0; }
        pre code { background: none; color: inherit; }
        table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
        th, td { border: 1px solid #dee2e6; padding: 0.75rem; text-align: left; }
        th { background: #6c5ce7; color: white; }
        blockquote { border-left: 4px solid #6c5ce7; padding-left: 1rem; color: #636e72; margin: 1rem 0; }
        .section { background: white; padding: 2rem; border-radius: 12px; margin: 1.5rem 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        hr { border: none; border-top: 2px solid #e9ecef; margin: 2rem 0; }
    </style>
</head>
<body>"""
        ]

        md_converter = markdown.Markdown(
            extensions=["tables", "fenced_code", "toc"]
        )

        for filename, content in md_files.items():
            section_title = filename.replace(".md", "").replace("_", " ")
            html_content = md_converter.convert(content)
            html_parts.append(
                f'<div class="section">'
                f"<h1>{section_title}</h1>"
                f"{html_content}"
                f"</div>"
            )
            md_converter.reset()

        html_parts.append("</body></html>")
        return "\n".join(html_parts)


export_service = ExportService()
