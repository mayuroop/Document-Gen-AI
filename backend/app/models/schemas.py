"""
Pydantic models for Projects and Documents.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    PENDING = "pending"
    CLONING = "cloning"
    PROCESSING = "processing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ProjectCreate(BaseModel):
    repo_url: str = Field(..., description="GitHub repository URL")


class ProjectResponse(BaseModel):
    id: str
    repo_url: str
    repo_name: str
    owner: str
    status: ProjectStatus
    file_count: int = 0
    progress: int = 0
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int


class DiagramData(BaseModel):
    type: str  # architecture, sequence, flowchart, er
    title: str
    mermaid_code: str


class DocumentationData(BaseModel):
    readme: str = ""
    architecture: str = ""
    api_docs: str = ""
    database: str = ""
    setup: str = ""
    deployment: str = ""
    troubleshooting: str = ""
    changelog: str = ""
    security: str = ""
    performance: str = ""
    scalability: str = ""
    testing: str = ""
    roadmap: str = ""
    license: str = ""


class DocumentResponse(BaseModel):
    id: str
    project_id: str
    documentation: DocumentationData
    diagrams: list[DiagramData] = []
    file_analyses: list[dict] = []
    api_endpoints: list[dict] = []
    created_at: datetime
    updated_at: datetime


class FileAnalysis(BaseModel):
    path: str
    language: str
    summary: str
    functions: list[str] = []
    classes: list[str] = []
    imports: list[str] = []
    apis: list[dict] = []
    purpose: str = ""


class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    sources: list[str] = []


class ExportRequest(BaseModel):
    format: str = "markdown"  # markdown, html
    sections: list[str] = []  # empty = all sections
