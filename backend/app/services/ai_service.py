"""
AI Service - Ollama local LLM integration for code analysis and documentation.
"""
import logging
import httpx
import asyncio
import json
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Handles all AI interactions via Ollama local LLM."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.timeout = 120.0
        self._semaphore = asyncio.Semaphore(3)  # Limit concurrent requests

    async def _call_ollama(self, prompt: str, system: str = "") -> str:
        """Make a request to Ollama API."""
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 4096,
            },
        }

        async with self._semaphore:
            for attempt in range(3):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.post(url, json=payload)
                        response.raise_for_status()
                        data = response.json()
                        return data.get("response", "")
                except httpx.TimeoutException:
                    logger.warning(
                        f"Ollama timeout (attempt {attempt + 1}/3)"
                    )
                    if attempt == 2:
                        return "[AI analysis timed out]"
                    await asyncio.sleep(2 ** attempt)
                except httpx.HTTPStatusError as e:
                    logger.error(f"Ollama HTTP error: {e}")
                    return f"[AI error: {e.response.status_code}]"
                except httpx.ConnectError:
                    logger.error(
                        "Cannot connect to Ollama. Is it running on "
                        f"{self.base_url}?"
                    )
                    return (
                        "[Ollama is not running. Start it with: ollama serve]"
                    )
                except Exception as e:
                    logger.error(f"Ollama error: {e}")
                    return f"[AI error: {str(e)}]"

        return "[AI analysis failed]"

    async def analyze_file(self, file_path: str, content: str, language: str) -> dict:
        """Analyze a single file and extract structured information."""
        system = (
            "You are an expert code analyst. Analyze the given code file and "
            "extract structured information. Respond ONLY with valid JSON."
        )

        prompt = f"""Analyze this {language} file at path `{file_path}`:

```{language.lower()}
{content[:3000]}
```

Return a JSON object with these fields:
{{
    "summary": "Brief description of what this file does",
    "purpose": "The role of this file in the project",
    "functions": ["list of function/method names"],
    "classes": ["list of class names"],
    "imports": ["key imports/dependencies"],
    "apis": [
        {{
            "method": "GET/POST/PUT/DELETE",
            "path": "/api/endpoint",
            "description": "what it does"
        }}
    ],
    "database_models": ["list of database model/schema names if any"],
    "key_logic": "Description of the main logic/algorithm"
}}

If a field doesn't apply, use an empty list or empty string."""

        response = await self._call_ollama(prompt, system)

        # Try to parse JSON from response
        try:
            # Extract JSON from response if wrapped in text
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(response[json_start:json_end])
                parsed["path"] = file_path
                parsed["language"] = language
                return parsed
        except json.JSONDecodeError:
            pass

        return {
            "path": file_path,
            "language": language,
            "summary": response[:500] if response else "Analysis unavailable",
            "purpose": "",
            "functions": [],
            "classes": [],
            "imports": [],
            "apis": [],
            "database_models": [],
            "key_logic": "",
        }

    async def generate_documentation(
        self, doc_type: str, project_context: str
    ) -> str:
        """Generate a specific documentation section."""
        prompts = {
            "readme": (
                "Generate a comprehensive README.md for this project. Include: "
                "project title, description, features, tech stack, "
                "installation instructions, usage examples, project structure, "
                "contributing guidelines, and license information."
            ),
            "architecture": (
                "Generate an ARCHITECTURE.md document. Include: system overview, "
                "component architecture, data flow, technology choices and "
                "rationale, design patterns used, module interactions, and "
                "scalability considerations."
            ),
            "api_docs": (
                "Generate API_DOCS.md documentation. Include: all API endpoints "
                "found, request/response formats, authentication, error codes, "
                "and example requests. Format as a professional API reference."
            ),
            "database": (
                "Generate DATABASE.md documentation. Include: database schema, "
                "models/entities, relationships, indexes, migrations strategy, "
                "and data flow patterns."
            ),
            "setup": (
                "Generate SETUP.md with detailed setup instructions. Include: "
                "prerequisites, environment setup, dependency installation, "
                "configuration, database setup, and first run instructions."
            ),
            "deployment": (
                "Generate DEPLOYMENT.md. Include: deployment strategies, "
                "Docker setup, CI/CD pipeline, environment variables, "
                "cloud deployment guides, and monitoring setup."
            ),
            "troubleshooting": (
                "Generate TROUBLESHOOTING.md. Include: common issues, "
                "error messages and solutions, debugging tips, FAQ, "
                "and support contacts."
            ),
            "changelog": (
                "Generate a CHANGELOG.md template. Include a structured "
                "format with version numbers, dates, and categories: "
                "Added, Changed, Deprecated, Removed, Fixed, Security."
            ),
            "security": (
                "Generate SECURITY.md. Include: security practices, "
                "authentication/authorization, data protection, "
                "vulnerability reporting, and compliance considerations."
            ),
            "performance": (
                "Generate PERFORMANCE.md. Include: performance benchmarks, "
                "optimization strategies, caching approach, monitoring, "
                "and load testing guidelines."
            ),
            "scalability": (
                "Generate SCALABILITY.md. Include: scaling strategy, "
                "horizontal vs vertical scaling, load balancing, "
                "database scaling, and microservices considerations."
            ),
            "testing": (
                "Generate TESTING.md. Include: testing strategy, "
                "unit tests, integration tests, e2e tests, "
                "test coverage, and CI integration."
            ),
            "roadmap": (
                "Generate ROADMAP.md. Include: current version features, "
                "planned features, milestones, timeline estimates, "
                "and contribution areas."
            ),
            "license": (
                "Generate a LICENSE.md section describing the licensing. "
                "Default to MIT License unless the project specifies otherwise."
            ),
        }

        instruction = prompts.get(doc_type, f"Generate {doc_type} documentation.")

        system = (
            "You are a senior technical writer creating professional "
            "documentation. Write clear, comprehensive, well-structured "
            "markdown documentation. Use proper headings, code blocks, "
            "tables, and lists."
        )

        prompt = f"""{instruction}

Based on this project analysis:

{project_context[:6000]}

Generate professional, detailed markdown documentation. Use proper markdown formatting with headers, code blocks, tables, and lists."""

        return await self._call_ollama(prompt, system)

    async def generate_diagram(
        self, diagram_type: str, project_context: str
    ) -> dict:
        """Generate a Mermaid diagram with detailed, syntax-safe prompts."""

        diagram_instructions = {
            "architecture": (
                "Create a detailed Mermaid.js ARCHITECTURE diagram using `graph TB` format.\n"
                "Show the full system architecture with these layers:\n"
                "  - Client/UI layer (frontend, browser)\n"
                "  - API/Gateway layer (routes, controllers)\n"
                "  - Service/Business logic layer\n"
                "  - Data/Storage layer (database, cache, file system)\n"
                "  - External services (APIs, AI models, third-party)\n\n"
                "Use subgraphs to group related components. Use descriptive labels.\n"
                "Show data flow direction with arrows and edge labels.\n\n"
                "EXAMPLE of correct syntax:\n"
                "graph TB\n"
                "    subgraph Frontend\n"
                "        A[React App] --> B[API Client]\n"
                "    end\n"
                "    subgraph Backend\n"
                "        C[REST API] --> D[Auth Service]\n"
                "        C --> E[Business Logic]\n"
                "    end\n"
                "    subgraph Storage\n"
                "        F[(MongoDB)]\n"
                "        G[(Redis Cache)]\n"
                "    end\n"
                "    B -->|HTTP Requests| C\n"
                "    E -->|Read/Write| F\n"
                "    D -->|Sessions| G\n\n"
                "RULES:\n"
                "- Start with `graph TB`\n"
                "- Use square brackets [Label] for components\n"
                "- Use cylinder [(DB Name)] for databases\n"
                "- Use curly braces {Decision} for decision points\n"
                "- Do NOT use parentheses inside brackets\n"
                "- Use `subgraph Name` and `end` to group layers\n"
                "- Add edge labels with |label text|\n"
                "- Node IDs must be simple alphanumeric (A, B1, userSvc etc.)\n"
            ),
            "sequence": (
                "Create a detailed Mermaid.js SEQUENCE diagram using `sequenceDiagram` format.\n"
                "Show the main user workflow from start to finish:\n"
                "  1. User initiates an action\n"
                "  2. Request flows through each system component\n"
                "  3. Processing steps with any branching logic\n"
                "  4. Response flows back to user\n\n"
                "Include at least 4-6 participants and 8-12 message exchanges.\n"
                "Use alt/else blocks for error handling or branching.\n"
                "Use notes to highlight important steps.\n\n"
                "EXAMPLE of correct syntax:\n"
                "sequenceDiagram\n"
                "    participant U as User\n"
                "    participant FE as Frontend\n"
                "    participant API as Backend API\n"
                "    participant DB as Database\n"
                "    U->>FE: Submit form\n"
                "    FE->>API: POST /api/resource\n"
                "    API->>API: Validate input\n"
                "    alt Valid input\n"
                "        API->>DB: Insert record\n"
                "        DB-->>API: Success\n"
                "        API-->>FE: 201 Created\n"
                "        FE-->>U: Show success\n"
                "    else Invalid input\n"
                "        API-->>FE: 400 Bad Request\n"
                "        FE-->>U: Show error\n"
                "    end\n"
                "    Note over API,DB: Data is persisted\n\n"
                "RULES:\n"
                "- Start with `sequenceDiagram` on its own line\n"
                "- Define participants with `participant X as Label`\n"
                "- Use `->>` for solid arrows (requests)\n"
                "- Use `-->>` for dashed arrows (responses)\n"
                "- Participant aliases must be alphanumeric only, no spaces or special chars\n"
                "- Do NOT use parentheses or brackets in message text\n"
                "- Use `alt` / `else` / `end` for conditional blocks\n"
                "- Use `Note over X,Y: text` for notes\n"
            ),
            "flowchart": (
                "Create a detailed Mermaid.js FLOWCHART using `flowchart TD` format.\n"
                "Show the complete application process flow:\n"
                "  1. Entry point / trigger\n"
                "  2. Input validation and processing steps\n"
                "  3. Decision points with Yes/No branches\n"
                "  4. Main processing pipeline\n"
                "  5. Output / completion states\n"
                "  6. Error handling paths\n\n"
                "Include at least 10-15 nodes with clear labels.\n"
                "Use different shapes for different node types.\n\n"
                "EXAMPLE of correct syntax:\n"
                "flowchart TD\n"
                "    A([Start]) --> B[Receive Input]\n"
                "    B --> C{Valid?}\n"
                "    C -->|Yes| D[Process Data]\n"
                "    C -->|No| E[Return Error]\n"
                "    D --> F[Transform]\n"
                "    F --> G{Success?}\n"
                "    G -->|Yes| H[Save to DB]\n"
                "    G -->|No| I[Log Error]\n"
                "    H --> J([End])\n"
                "    E --> J\n"
                "    I --> J\n\n"
                "RULES:\n"
                "- Start with `flowchart TD`\n"
                "- Use ([Label]) for start/end nodes (stadium shape)\n"
                "- Use [Label] for process steps\n"
                "- Use {Label} for decision diamonds\n"
                "- Use [(Label)] for database operations\n"
                "- Add edge labels with |label text|\n"
                "- Do NOT use parentheses inside square brackets\n"
                "- Node IDs must be simple: A, B, step1, etc.\n"
                "- Always show error/failure paths\n"
            ),
            "er": (
                "Create a detailed Mermaid.js ER DIAGRAM using `erDiagram` format.\n"
                "Show all database entities, their fields, and relationships.\n"
                "For each entity include:\n"
                "  - Primary key fields marked with PK\n"
                "  - Foreign key fields marked with FK\n"
                "  - Field types (string, int, boolean, datetime)\n"
                "  - At least 4-6 meaningful fields per entity\n\n"
                "Show relationships between all entities using proper cardinality.\n\n"
                "EXAMPLE of correct syntax:\n"
                "erDiagram\n"
                "    USER ||--o{ ORDER : places\n"
                "    ORDER ||--|{ ORDER_ITEM : contains\n"
                "    PRODUCT ||--o{ ORDER_ITEM : included_in\n"
                "    USER {\n"
                "        string id PK\n"
                "        string name\n"
                "        string email\n"
                "        datetime created_at\n"
                "    }\n"
                "    ORDER {\n"
                "        string id PK\n"
                "        string user_id FK\n"
                "        string status\n"
                "        float total\n"
                "        datetime created_at\n"
                "    }\n"
                "    PRODUCT {\n"
                "        string id PK\n"
                "        string name\n"
                "        float price\n"
                "        int stock\n"
                "    }\n\n"
                "RULES:\n"
                "- Start with `erDiagram` on its own line\n"
                "- Entity names MUST be UPPERCASE with only letters, numbers, underscores\n"
                "- NO hyphens in entity names (use underscores instead)\n"
                "- Define relationships BEFORE entity field blocks\n"
                "- Relationship syntax: ENTITY_A ||--o{ ENTITY_B : label\n"
                "- Cardinality: ||--|| one-to-one, ||--o{ one-to-many, }o--o{ many-to-many\n"
                "- Field syntax inside braces: `type name` or `type name PK`\n"
                "- Every open brace { must have a matching close brace }\n"
                "- Include at least 3-5 entities with meaningful fields\n"
            ),
        }

        instruction = diagram_instructions.get(
            diagram_type, f"Create a {diagram_type} diagram."
        )

        system = (
            "You are an expert Mermaid.js diagram creator. "
            "You MUST return ONLY raw Mermaid diagram code. "
            "NEVER wrap in markdown code fences (no ``` at all). "
            "NEVER add explanations, comments, or text before/after the diagram. "
            "The output must start directly with the diagram type keyword "
            "(graph, flowchart, sequenceDiagram, or erDiagram). "
            "Ensure all syntax is valid for Mermaid.js v10."
        )

        prompt = f"""{instruction}

Analyze this project and create a meaningful, detailed diagram:

{project_context[:5000]}

IMPORTANT: Output ONLY the raw Mermaid code. No text, no fences, no explanation.
Start directly with the diagram type keyword."""

        mermaid_code = await self._call_ollama(prompt, system)

        # Clean up the response
        mermaid_code = mermaid_code.strip()
        # Remove any markdown fences
        if mermaid_code.startswith("```"):
            lines = mermaid_code.split("\n")
            mermaid_code = "\n".join(lines[1:])
        mermaid_code = mermaid_code.replace("```", "").strip()

        return {
            "type": diagram_type,
            "title": f"{diagram_type.replace('_', ' ').title()} Diagram",
            "mermaid_code": mermaid_code,
        }

    async def chat_about_project(
        self, message: str, project_context: str
    ) -> str:
        """Answer questions about a project."""
        system = (
            "You are an AI assistant that helps developers understand "
            "codebases. Answer questions clearly and concisely based on "
            "the project analysis provided. If you're not sure, say so."
        )

        prompt = f"""Project Context:
{project_context[:5000]}

User Question: {message}

Provide a helpful, accurate answer based on the project analysis."""

        return await self._call_ollama(prompt, system)

    async def check_health(self) -> bool:
        """Check if Ollama is running and the model is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [m.get("name", "").split(":")[0] for m in models]
                    return self.model.split(":")[0] in model_names
        except Exception:
            pass
        return False

    async def generate_api_descriptions(self, project_id: str, api_endpoints: list[dict], project_context: str):
        """Background task to generate missing descriptions for API endpoints."""
        from app.core.database import get_collection
        import asyncio
        
        if not api_endpoints:
            return
            
        logger.info(f"Starting background generation of API descriptions for {project_id}")
        documents = get_collection("documents")
        
        system = (
            "You are an API documentation expert. Generate a concise, single-sentence "
            "description for the given API endpoint based on its path, method, and project context. "
            "Return ONLY the description, no quotes, no extra text."
        )
        
        for api in api_endpoints:
            desc = api.get("description", "")
            if not desc or desc == "No description" or desc.lower() == "unknown":
                logger.info(f"Generating description for {api.get('method', 'GET')} {api.get('path', 'unknown')} ...")
                
                prompt = (
                    f"Project Context:\n{project_context[:3000]}\n\n"
                    f"Endpoint: {api.get('method')} {api.get('path')}\n\n"
                    "Provide a concise 1-sentence description for what this endpoint does."
                )
                
                try:
                    new_desc = await self._call_ollama(prompt, system)
                    api["description"] = new_desc.strip('"\'\n ')
                    
                    # Save in real-time
                    await documents.update_one(
                        {"project_id": project_id},
                        {"$set": {"api_endpoints": api_endpoints}}
                    )
                except Exception as e:
                    logger.error(f"Failed to generate description for {api.get('path')}: {e}")
                    
                # Small delay to not overwhelm the LLM
                await asyncio.sleep(1)
                
        logger.info(f"Finished background generation of API descriptions for {project_id}")


ai_service = AIService()
