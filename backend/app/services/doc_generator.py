"""
Documentation generator - orchestrates the full documentation pipeline.
Supports two modes:
  - Compressor ON  (USE_COMPRESSOR=true):  ~18 AI calls (local parsing + 14 docs + 4 diagrams)
  - Compressor OFF (USE_COMPRESSOR=false): ~50+ AI calls (per-file AI analysis + 14 docs + 4 diagrams)
"""
import logging
import asyncio
from datetime import datetime
from app.config import settings
from app.services.ai_service import ai_service
from app.services.file_processor import file_processor
from app.services.github_service import github_service
from app.services.compressor import compressor
from app.core.database import get_collection
from bson import ObjectId

logger = logging.getLogger(__name__)

DOC_TYPES = [
    "readme", "architecture", "api_docs", "database", "setup",
    "deployment", "troubleshooting", "changelog", "security",
    "performance", "scalability", "testing", "roadmap", "license",
]

DIAGRAM_TYPES = ["architecture", "sequence", "flowchart", "er"]


class DocGenerator:
    """Orchestrates the full documentation generation pipeline."""

    async def generate_for_project(self, project_id: str):
        """
        Full pipeline: clone → compress/process → generate docs + diagrams.
        """
        projects = get_collection("projects")
        documents = get_collection("documents")

        try:
            project = await projects.find_one({"_id": ObjectId(project_id)})
            if not project:
                logger.error(f"Project {project_id} not found")
                return

            repo_url = project["repo_url"]
            use_compressor = settings.use_compressor

            mode = "COMPRESSOR" if use_compressor else "LEGACY"
            logger.info(f"🚀 Starting generation [{mode}] for {repo_url}")

            # ── Step 1: Clone ──
            await self._update(projects, project_id, "cloning", 5)
            clone_info = await github_service.clone_repo(repo_url)
            clone_path = clone_info["clone_path"]

            # ── Step 2: Process / Compress ──
            await self._update(projects, project_id, "processing", 10)

            if use_compressor:
                # FAST MODE: Local AST/regex parsing, zero AI calls
                compressed = compressor.compress_repository(clone_path)
                project_context = (
                    f"# Project: {clone_info['full_name']}\n"
                    f"{compressed['context']}"
                )
                file_analyses = compressed["file_analyses"]
                api_endpoints = compressed["api_endpoints"]
                file_tree = compressed["file_tree"]
                file_count = compressed["stats"]["total_files"]

                await projects.update_one(
                    {"_id": ObjectId(project_id)},
                    {"$set": {
                        "file_count": file_count,
                        "progress": 30,
                        "updated_at": datetime.utcnow(),
                    }},
                )

                logger.info(
                    f"🗜️  Compressed: {compressed['stats']['context_size_chars']} chars, "
                    f"{compressed['stats']['total_functions']} funcs, "
                    f"{compressed['stats']['total_routes']} routes"
                )

            else:
                # LEGACY MODE: Per-file AI analysis
                categorized = await file_processor.process_repository(clone_path)
                all_files = (
                    categorized["source_files"]
                    + categorized["config_files"]
                    + categorized["doc_files"]
                )

                await projects.update_one(
                    {"_id": ObjectId(project_id)},
                    {"$set": {"file_count": len(all_files), "progress": 20, "updated_at": datetime.utcnow()}},
                )

                # Per-file AI analysis
                await self._update(projects, project_id, "processing", 25)
                file_analyses = []
                batch_size = 3
                for i in range(0, min(len(all_files), 50), batch_size):
                    batch = all_files[i : i + batch_size]
                    tasks = [
                        ai_service.analyze_file(
                            f["path"], f["content"][:3000],
                            file_processor.prepare_file_for_ai(f)[0]["language"]
                        )
                        for f in batch
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in results:
                        if isinstance(result, dict):
                            file_analyses.append(result)

                    progress = 25 + int((i / max(len(all_files), 1)) * 30)
                    await self._update(projects, project_id, "processing", min(progress, 55))

                project_context = self._build_legacy_context(clone_info, categorized, file_analyses)

                api_endpoints = []
                for analysis in file_analyses:
                    if analysis.get("apis"):
                        for api in analysis["apis"]:
                            api["source_file"] = analysis.get("path", "")
                            api_endpoints.append(api)

                file_tree = file_processor.get_file_tree(all_files)

            # ── Step 3: Generate 14 documentation sections (14 AI calls) ──
            await self._update(projects, project_id, "generating", 35 if use_compressor else 60)

            documentation = {}
            for i, doc_type in enumerate(DOC_TYPES):
                logger.info(f"📝 [{i+1}/18] Generating {doc_type}")
                doc_content = await ai_service.generate_documentation(
                    doc_type, project_context
                )
                documentation[doc_type] = doc_content

                if use_compressor:
                    progress = 35 + int(((i + 1) / len(DOC_TYPES)) * 50)
                else:
                    progress = 60 + int(((i + 1) / len(DOC_TYPES)) * 25)
                await self._update(projects, project_id, "generating", min(progress, 90))

            # ── Step 4: Generate 4 diagrams (4 AI calls) ──
            await self._update(projects, project_id, "generating", 90)

            diagrams = []
            for j, diagram_type in enumerate(DIAGRAM_TYPES):
                logger.info(f"📊 [{15 + j}/18] Generating {diagram_type} diagram")
                diagram = await ai_service.generate_diagram(
                    diagram_type, project_context
                )
                diagrams.append(diagram)

            # ── Step 5: Save to database ──
            doc_record = {
                "project_id": project_id,
                "documentation": documentation,
                "diagrams": diagrams,
                "file_analyses": file_analyses[:100],
                "api_endpoints": api_endpoints,
                "file_tree": file_tree,
                "project_context": project_context[:15000],
                "compressed_mode": use_compressor,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            await documents.update_one(
                {"project_id": project_id},
                {"$set": doc_record},
                upsert=True,
            )

            await projects.update_one(
                {"_id": ObjectId(project_id)},
                {"$set": {"status": "completed", "progress": 100, "updated_at": datetime.utcnow()}},
            )

            total_calls = 18 if use_compressor else (len(file_analyses) + 18)
            logger.info(f"✅ Done! {total_calls} AI calls total [{mode}]")

            # Background generation of API descriptions
            if settings.gen_api_description and api_endpoints:
                logger.info(f"Queueing background API description generation for {project_id}")
                asyncio.create_task(
                    ai_service.generate_api_descriptions(project_id, api_endpoints, project_context)
                )

            # Cleanup
            await github_service.cleanup_repo(clone_info["owner"], clone_info["repo"])

        except Exception as e:
            logger.error(f"❌ Generation failed for {project_id}: {e}", exc_info=True)
            await projects.update_one(
                {"_id": ObjectId(project_id)},
                {"$set": {"status": "failed", "error": str(e), "updated_at": datetime.utcnow()}},
            )

    async def _update(self, projects, project_id: str, status: str, progress: int):
        """Helper to update project status."""
        await projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"status": status, "progress": progress, "updated_at": datetime.utcnow()}},
        )

    def _build_legacy_context(self, clone_info: dict, categorized: dict, analyses: list[dict]) -> str:
        """Build context from per-file AI analyses (legacy mode)."""
        parts = [
            f"# Project: {clone_info['full_name']}",
            f"Total files: {categorized['total_files']}",
            f"Source: {len(categorized['source_files'])}, Config: {len(categorized['config_files'])}, Docs: {len(categorized['doc_files'])}",
            "\n## File Structure:",
        ]

        all_files = categorized["source_files"] + categorized["config_files"] + categorized["doc_files"]
        for f in all_files[:60]:
            parts.append(f"- {f['path']} ({f['extension']})")

        parts.append("\n## File Analyses:")
        for analysis in analyses[:30]:
            parts.append(f"\n### {analysis.get('path', 'Unknown')}")
            parts.append(f"Language: {analysis.get('language', 'Unknown')}")
            parts.append(f"Summary: {analysis.get('summary', 'N/A')}")
            if analysis.get("functions"):
                parts.append(f"Functions: {', '.join(analysis['functions'][:10])}")
            if analysis.get("classes"):
                parts.append(f"Classes: {', '.join(analysis['classes'][:10])}")
            if analysis.get("apis"):
                for api in analysis["apis"][:5]:
                    parts.append(f"API: {api.get('method', '?')} {api.get('path', '?')} - {api.get('description', '')}")

        return "\n".join(parts)


doc_generator = DocGenerator()
