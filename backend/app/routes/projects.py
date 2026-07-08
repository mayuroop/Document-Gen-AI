"""
Project routes - CRUD operations for projects.
"""
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, HTTPException
from bson import ObjectId
from app.core.database import get_collection
from app.core.security import validate_github_url, extract_repo_info, sanitize_repo_url
from app.models.schemas import ProjectCreate, ProjectResponse, ProjectListResponse
from app.services.doc_generator import doc_generator

router = APIRouter(prefix="/api/projects", tags=["Projects"])


def _project_to_response(project: dict) -> dict:
    """Convert MongoDB project document to API response."""
    return {
        "id": str(project["_id"]),
        "repo_url": project.get("repo_url", ""),
        "repo_name": project.get("repo_name", ""),
        "owner": project.get("owner", ""),
        "status": project.get("status", "pending"),
        "file_count": project.get("file_count", 0),
        "progress": project.get("progress", 0),
        "error": project.get("error"),
        "created_at": project.get("created_at", datetime.utcnow()),
        "updated_at": project.get("updated_at", datetime.utcnow()),
    }


@router.post("", response_model=ProjectResponse)
async def create_project(
    body: ProjectCreate, background_tasks: BackgroundTasks
):
    """Create a new project and start documentation generation."""
    repo_url = sanitize_repo_url(body.repo_url)

    if not validate_github_url(repo_url):
        raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")

    info = extract_repo_info(repo_url)
    projects = get_collection("projects")

    # Check if project already exists
    existing = await projects.find_one({
        "repo_url": repo_url, "status": {"$ne": "failed"}
    })
    if existing:
        return _project_to_response(existing)

    # Create project
    project = {
        "repo_url": repo_url,
        "repo_name": info["repo"],
        "owner": info["owner"],
        "status": "pending",
        "file_count": 0,
        "progress": 0,
        "error": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await projects.insert_one(project)
    project["_id"] = result.inserted_id

    # Start background generation
    background_tasks.add_task(
        doc_generator.generate_for_project, str(result.inserted_id)
    )

    return _project_to_response(project)


@router.get("", response_model=ProjectListResponse)
async def list_projects():
    """List all projects."""
    projects = get_collection("projects")
    cursor = projects.find().sort("created_at", -1).limit(50)
    items = []
    async for project in cursor:
        items.append(_project_to_response(project))

    return {"projects": items, "total": len(items)}


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get a specific project."""
    projects = get_collection("projects")

    try:
        project = await projects.find_one({"_id": ObjectId(project_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return _project_to_response(project)


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and its documentation."""
    projects = get_collection("projects")
    documents = get_collection("documents")

    try:
        result = await projects.delete_one({"_id": ObjectId(project_id)})
        await documents.delete_many({"project_id": project_id})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"message": "Project deleted"}


@router.post("/{project_id}/regenerate")
async def regenerate_project(
    project_id: str, background_tasks: BackgroundTasks
):
    """Regenerate documentation for a project."""
    projects = get_collection("projects")

    try:
        project = await projects.find_one({"_id": ObjectId(project_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Reset status
    await projects.update_one(
        {"_id": ObjectId(project_id)},
        {
            "$set": {
                "status": "pending",
                "progress": 0,
                "error": None,
                "updated_at": datetime.utcnow(),
            }
        },
    )

    background_tasks.add_task(
        doc_generator.generate_for_project, project_id
    )

    return {"message": "Regeneration started"}
