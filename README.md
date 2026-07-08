# 🤖 DocGen AI — AI Documentation Generator

> Transform any GitHub repository into comprehensive, professional documentation using AI.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![React](https://img.shields.io/badge/react-19-blue.svg)

## ✨ Features

- **🧠 AI-Powered Analysis** — Local Ollama LLM analyzes every file in your codebase
- **📄 14 Documentation Types** — README, Architecture, API Docs, Database, Setup, Deployment, and more
- **📊 Auto Diagrams** — Architecture, Sequence, Flowchart, and ER diagrams via Mermaid.js
- **💬 AI Chat** — Ask questions about your codebase interactively
- **🔍 Full-Text Search** — Search across all documentation with Ctrl+K
- **🎨 Premium UI** — Dark/light mode, glassmorphism, animations, VS Code-style file explorer
- **📥 Export** — Download as Markdown or HTML
- **🔐 Private** — Everything runs locally, your code never leaves your machine

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────┐
│   React + Vite  │────▶│   FastAPI Backend     │────▶│  Ollama │
│   Tailwind CSS  │     │   Async Processing    │     │  (LLM)  │
└─────────────────┘     └──────────┬───────────┘     └─────────┘
                                   │
                               ┌───▼───┐
                               │MongoDB│
                               └───────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 20+**
- **MongoDB** (Atlas or local)
- **Ollama** (for local AI)
- **Git**

### 1. Start Ollama

```bash
ollama serve
ollama pull llama3.2
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Open the app

Navigate to **http://localhost:5173**

## 📁 Project Structure

```
TY_PROJECT/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuration
│   │   ├── core/
│   │   │   ├── database.py      # MongoDB connection
│   │   │   └── security.py      # Input validation
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models
│   │   ├── routes/
│   │   │   ├── projects.py      # Project CRUD
│   │   │   └── documents.py     # Doc retrieval, chat, export
│   │   ├── services/
│   │   │   ├── ai_service.py    # Ollama integration
│   │   │   ├── github_service.py # Repo cloning
│   │   │   ├── file_processor.py # File analysis
│   │   │   ├── doc_generator.py  # Documentation pipeline
│   │   │   └── export_service.py # Export functionality
│   │   └── utils/
│   │       ├── chunker.py       # File chunking
│   │       └── logger.py        # Logging
│   ├── .env                     # Environment variables
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx       # App header
│   │   │   ├── Sidebar.jsx      # Navigation sidebar
│   │   │   ├── DocViewer.jsx    # Markdown renderer
│   │   │   ├── DiagramViewer.jsx # Mermaid diagrams
│   │   │   ├── ApiViewer.jsx    # API endpoint viewer
│   │   │   ├── FileExplorer.jsx # File tree + analysis
│   │   │   ├── ChatPanel.jsx    # AI chat
│   │   │   └── SearchModal.jsx  # Search
│   │   ├── pages/
│   │   │   ├── LandingPage.jsx  # Home page
│   │   │   ├── DashboardPage.jsx # Project list
│   │   │   └── ProjectPage.jsx  # Doc viewer
│   │   ├── services/
│   │   │   └── api.js           # API client
│   │   ├── hooks/
│   │   │   └── useTheme.js      # Theme hook
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
└── README.md
```

## ⚙️ Environment Variables

Create `backend/.env`:

```env
MONGO_URI=mongodb+srv://admin:admin@app.1y5xkze.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=docgen
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
GITHUB_TOKEN=
```

## 📄 Generated Documentation Types

| # | Document | Description |
|---|----------|-------------|
| 1 | README.md | Project overview and getting started |
| 2 | ARCHITECTURE.md | System design and component architecture |
| 3 | API_DOCS.md | API endpoints and request/response formats |
| 4 | DATABASE.md | Database schema and data models |
| 5 | SETUP.md | Installation and configuration guide |
| 6 | DEPLOYMENT.md | Deployment strategies and CI/CD |
| 7 | TROUBLESHOOTING.md | Common issues and solutions |
| 8 | CHANGELOG.md | Version history template |
| 9 | SECURITY.md | Security practices and policies |
| 10 | PERFORMANCE.md | Performance optimization guide |
| 11 | SCALABILITY.md | Scaling strategies |
| 12 | TESTING.md | Testing strategy and examples |
| 13 | ROADMAP.md | Feature roadmap |
| 14 | LICENSE.md | License information |

## 📊 Auto-Generated Diagrams

- **Architecture Diagram** — Component relationships and data flow
- **Sequence Diagram** — Request/response flows
- **Flowchart** — Process and logic flows
- **ER Diagram** — Database entity relationships

All diagrams use **Mermaid.js** and are rendered in the browser.

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.
