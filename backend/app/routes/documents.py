"""
Documentation routes - fetch generated docs, diagrams, chat, export.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from app.core.database import get_collection
from app.models.schemas import ChatMessage, ExportRequest
from app.services.ai_service import ai_service
from app.services.export_service import export_service

router = APIRouter(prefix="/api/docs", tags=["Documentation"])


@router.get("/{project_id}")
async def get_documentation(project_id: str):
    """Get all documentation for a project."""
    documents = get_collection("documents")
    doc = await documents.find_one({"project_id": project_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Documentation not found")

    return {
        "id": str(doc["_id"]),
        "project_id": doc["project_id"],
        "documentation": doc.get("documentation", {}),
        "diagrams": doc.get("diagrams", []),
        "file_analyses": doc.get("file_analyses", [])[:50],
        "api_endpoints": doc.get("api_endpoints", []),
        "file_tree": doc.get("file_tree", {}),
    }


@router.get("/{project_id}/section/{section}")
async def get_section(project_id: str, section: str):
    """Get a specific documentation section."""
    documents = get_collection("documents")
    doc = await documents.find_one({"project_id": project_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Documentation not found")

    documentation = doc.get("documentation", {})
    if section not in documentation:
        raise HTTPException(status_code=404, detail=f"Section '{section}' not found")

    return {"section": section, "content": documentation[section]}


@router.get("/{project_id}/diagrams")
async def get_diagrams(project_id: str):
    """Get all diagrams for a project."""
    documents = get_collection("documents")
    doc = await documents.find_one({"project_id": project_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Documentation not found")

    return {"diagrams": doc.get("diagrams", [])}


@router.get("/{project_id}/apis")
async def get_api_endpoints(project_id: str):
    """Get discovered API endpoints."""
    documents = get_collection("documents")
    doc = await documents.find_one({"project_id": project_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Documentation not found")

    return {"endpoints": doc.get("api_endpoints", [])}


@router.get("/{project_id}/files")
async def get_file_tree(project_id: str):
    """Get the file tree structure."""
    documents = get_collection("documents")
    doc = await documents.find_one({"project_id": project_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Documentation not found")

    return {
        "file_tree": doc.get("file_tree", {}),
        "file_analyses": doc.get("file_analyses", []),
    }


@router.post("/{project_id}/chat")
async def chat_about_project(project_id: str, body: ChatMessage):
    """Chat with AI about the project."""
    documents = get_collection("documents")
    doc = await documents.find_one({"project_id": project_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Documentation not found")

    context = doc.get("project_context", "")
    response = await ai_service.chat_about_project(body.message, context)

    return {"response": response, "sources": []}


@router.post("/{project_id}/export")
async def export_documentation(project_id: str, body: ExportRequest):
    """Export documentation in specified format."""
    if body.format == "html":
        html = await export_service.export_html(project_id)
        return HTMLResponse(content=html)
    else:
        # Default: markdown
        files = await export_service.export_markdown(
            project_id, body.sections or None
        )
        if not files:
            raise HTTPException(
                status_code=404, detail="No documentation to export"
            )
        return files


@router.get("/{project_id}/search")
async def search_documentation(project_id: str, q: str = ""):
    """Search through documentation content."""
    if not q or len(q) < 2:
        return {"results": []}

    documents = get_collection("documents")
    doc = await documents.find_one({"project_id": project_id})

    if not doc:
        return {"results": []}

    results = []
    query_lower = q.lower()

    # Search through documentation sections
    documentation = doc.get("documentation", {})
    for section, content in documentation.items():
        if query_lower in content.lower():
            # Find the relevant snippet
            idx = content.lower().find(query_lower)
            start = max(0, idx - 100)
            end = min(len(content), idx + 200)
            snippet = content[start:end]

            results.append({
                "type": "documentation",
                "section": section,
                "snippet": f"...{snippet}...",
                "match_count": content.lower().count(query_lower),
            })

    # Search through file analyses
    for analysis in doc.get("file_analyses", []):
        summary = analysis.get("summary", "")
        if query_lower in summary.lower() or query_lower in analysis.get("path", "").lower():
            results.append({
                "type": "file",
                "section": analysis.get("path", ""),
                "snippet": summary[:200],
                "match_count": 1,
            })

    # Sort by match count
    results.sort(key=lambda x: x["match_count"], reverse=True)

    return {"results": results[:20]}


@router.post("/{project_id}/generate-api-descriptions")
async def trigger_api_descriptions(project_id: str):
    """Trigger background generation of missing API descriptions."""
    from app.services.ai_service import ai_service
    import asyncio

    documents = get_collection("documents")
    doc = await documents.find_one({"project_id": project_id})

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    api_endpoints = doc.get("api_endpoints", [])
    project_context = doc.get("project_context", "")

    if not api_endpoints:
        return {"message": "No API endpoints found to process"}

    # Start background task
    asyncio.create_task(
        ai_service.generate_api_descriptions(project_id, api_endpoints, project_context)
    )

    return {"message": "Background generation started"}
