# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Personal Growth OS** is a "second brain" application designed to accelerate personal growth by helping users combat procrastination, solidify knowledge, and drive continuous self-improvement through data-driven reflection.

**Current Status**: MVP in active development. Backend uses **Agno** for AI agents, with ChromaDB for RAG. Frontend features weekly schedule view, task kanban with floating task column, AI chat panel, and comprehensive task/note management. Chinese character encoding is fully supported.

**IMPORTANT**: The actual implementation uses **Agno** framework, NOT LangGraph. Reference `backend/app/agents/task_igniter_agno.py` for the agent implementation pattern.

### Core Mission (Three Pillars)

1. **对抗拖延 (Combat Procrastination)**: Reduce friction in starting tasks through guided task decomposition and contextual knowledge retrieval
2. **固化知识 (Solidify Knowledge)**: Capture and automatically resurface relevant knowledge when needed
3. **驱动复盘 (Drive Reflection)**: Transform personal experience into actionable optimization strategies through data-driven insights

## Architecture

### Tech Stack

**Frontend:**
- Vue 3 + TypeScript + Composition API
- Vite (build tool)
- Pinia (state management)
- Element Plus (UI components)
- ECharts (data visualization)
- md-editor-v3 (Markdown editing)

**Backend:**
- FastAPI (Python 3.10+)
- **Agno** (lightweight AI agent framework)
- SQLAlchemy + **PostgreSQL** (cloud-hosted)
- **pgvector** extension (vector similarity search)

**Data Layer:**
- **PostgreSQL + pgvector** - Unified database solution (cloud-hosted)
  - Structured data: tasks, notes, projects, user config
  - Vector data: note embeddings for semantic search
  - Advantages: Single data source, ACID transactions, cloud backup

### Architectural Principles

- **Frontend**: Pure presentation layer communicating via RESTful API
- **Backend**: Three-layer architecture
  - API Layer (`/app/api/endpoints/`) - Request handling and validation
  - Service Layer (`/app/services/`) - Core business logic
  - Data Access Layer (`/app/crud/`) - Database operations abstraction
- **Separation of Concerns**: Complex AI logic encapsulated as Agno Agents with declarative configuration
- **Agent-First**: Use Agno's declarative agent definitions with automatic tool management and user memory

## Development Commands

### Backend Setup

```bash
cd backend

# Create virtual environment (first time only)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env with your LLM API keys

# Run development server (with auto-reload)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Or directly:
python app/main.py

# Backend runs on http://localhost:8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies (first time only)
npm install

# Run development server (with HMR)
npm run dev

# Build for production (includes TypeScript type checking via vue-tsc)
npm run build

# Preview production build
npm run preview

# Frontend runs on http://localhost:5173
```

**Note**: TypeScript errors will prevent production builds. The project uses `vue-tsc` for strict type checking. There is no separate linting command - type checking happens during build.

### Running Full Stack

For development, run both backend and frontend simultaneously in separate terminals:

**Terminal 1 (Backend)**:
```bash
cd backend
venv\Scripts\activate  # Windows
python -m uvicorn app.main:app --reload
```

**Terminal 2 (Frontend)**:
```bash
cd frontend
npm run dev
```

Then access the application at http://localhost:5173 (frontend automatically proxies API requests to http://localhost:8000).

### Testing the API

Once backend is running, access API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

Example API calls:
```bash
# Test task ignition (AI task decomposition)
curl -X POST "http://localhost:8000/api/tasks/ignite" \
  -H "Content-Type: application/json" \
  -d '{"task_description": "准备项目演示"}'

# Semantic search notes
curl "http://localhost:8000/api/notes/search/semantic?query=项目管理&limit=5"

# Create a task with time slots
curl -X POST "http://localhost:8000/api/tasks/" \
  -H "Content-Type: application/json" \
  -d '{"title": "测试任务", "start_time": "2025-10-31T14:00:00", "end_time": "2025-10-31T15:30:00", "project_id": 1}'

# Get agent visualization (Mermaid diagram)
curl "http://localhost:8000/api/tasks/agent/visualization"
```

### Database Management

Database file: `backend/personal_growth_os.db` (auto-created on first run in backend directory)

To reset database during development:
```bash
# Windows (from project root):
cd backend
if exist personal_growth_os.db del personal_growth_os.db
cd ..

# Linux/Mac (from project root):
cd backend && rm -f personal_growth_os.db && cd ..

# Or from backend directory:
# Windows: if exist personal_growth_os.db del personal_growth_os.db
# Linux/Mac: rm -f personal_growth_os.db
```

**Utility Scripts** (in `backend/utils/`):
- `clear_tasks.py` - Clear all tasks from database (useful for testing)
- `check_encoding.py` - Verify UTF-8 encoding in database
- `debug_snooze_display.py` - Debug snooze functionality and display logic
- `migrate_system_project.py` - Database migration for system project protection

**Test Scripts** (in `tests/`):
- `legacy/run_tests.py` - Lightweight integration tests for core API functionality
- `legacy/test_integration.py` - Comprehensive end-to-end tests covering all features
- `legacy/check_pending_tasks.py` - Check pending tasks in database
- `legacy/check_scheduled_tasks.py` - Check scheduled tasks in database
- `legacy/test_frontend_filter.py` - Test frontend filter behavior
- `fixtures/create_test_data.py` - Generate sample projects and tasks for testing
- `fixtures/create_test_tasks.py` - Generate sample tasks with various statuses

See `tests/README.md` and `backend/utils/README.md` for detailed usage instructions.

**Note**: This project includes Windows-specific command syntax in many places. When working on Windows, use the Windows commands provided. On Linux/Mac, use the alternative commands shown.

## Key Design Decisions

### Database Schema (SQLite)

Core entities with relationships:
- `projects` - Top-level organizational containers with `color` for UI differentiation and `is_system` flag for protection
- `notes` - Knowledge storage with `source_url` for traceability and `content` for RAG
- `tasks` - Action items with rich scheduling and tracking capabilities:
  - **Status tracking**: `status` (pending/in_progress/completed/archived)
  - **Prioritization**: `priority` (1-5 scale, indexed for efficient sorting)
  - **Time management**:
    - `due_date` - Task deadline
    - `snooze_until` - Flexible deferral (postpone without guilt)
    - `start_time` - Scheduled start time (for calendar view)
    - `end_time` - Scheduled end time (for time-blocking)
    - `estimated_hours` - Effort estimation (for capacity planning)
  - **Organization**: `project_id`, `parent_task_id` (for subtasks)
- `tags` + `note_tags` - Many-to-many relationship for knowledge organization

### Critical Features

1. **Task Ignition Ritual (任务启动仪式)** - IMPLEMENTED (Agno)
   - Automatic task decomposition for vague/large tasks via Agno Agent
   - Tool-based knowledge retrieval (search_knowledge_base, format_task_summary)
   - Generation of "minimum viable starting task" to reduce action friction
   - **Implementation**: `backend/app/agents/task_igniter_agno.py` using Agno declarative agent with function tools

2. **Calendar/Schedule View (日程管理)** - IMPLEMENTED
   - Weekly schedule visualization with time-slot planning (8:00-21:00 viewport)
   - Tasks with `start_time`/`end_time` display on calendar grid with minute-level precision (1px = 1min)
   - Supports all-day tasks, time-specific tasks, and truncation effects for events outside viewport
   - Task overlap detection using sweep-line algorithm with automatic aggregation blocks
   - Floating task column for tasks without scheduled time (collapsible)
   - Frontend components: WeekSchedule, TaskCard, AllDayTaskCard, AggregationBlock
   - Enables time-boxing and time-blocking workflows
   - **Note**: Drag-and-drop was removed 2025-11-13; time editing now done via edit dialog

3. **Flexible Task Deferral (灵活延后)** - IMPLEMENTED
   - `snooze_until` database field with timezone handling
   - Snooze button in task kanban floating task column
   - Tasks auto-reappear when snooze expires
   - Display in dedicated "延后任务" section on DashboardView

4. **Contextual Knowledge Resurrection (知识自动重现)** - PARTIAL
   - Semantic search API implemented via ChromaDB
   - Proactive suggestion UI pending

5. **Attachment Management (附件管理)** - IMPLEMENTED
   - File upload/download API (`/attachments/*`)
   - Support for multiple file types with size limits
   - **Implementation**: `backend/app/api/endpoints/attachments.py` + `services/file_storage.py`
   - Integration with notes system for contextual file management

6. **Note Linking System (笔记链接)** - IMPLEMENTED
   - Bidirectional links between notes (Wiki-style knowledge graph)
   - Backlinks API to discover notes referencing current note
   - **Implementation**: `backend/app/api/endpoints/links.py`
   - Enables building personal knowledge networks

7. **Interactive Review Dashboard (可交互复盘仪表盘)** - PLANNED
   - Dual trigger: scheduled automatic + manual on-demand
   - Data-driven insight modules: task patterns, procrastination detection
   - ECharts integration ready in frontend

8. **AI Chat Interface (AI对话助手)** - IMPLEMENTED
   - Collapsible chat panel integrated into main layout
   - SSE (Server-Sent Events) streaming for real-time responses
   - Session management with persistent chat history
   - Integration with Task Igniter Agent
   - **Implementation**: `frontend/src/components/chat/` + `backend/app/api/endpoints/chat.py`

9. **Settings Management (配置管理)** - IMPLEMENTED
   - Frontend settings page for LLM configuration
   - Support for multiple providers (OpenAI/Claude/Ollama)
   - Auto-save to `backend/.env` with hot-reload
   - **Implementation**: `frontend/src/views/SettingsView.vue` + `backend/app/api/endpoints/settings.py`

## Architecture Implementation Details

### Backend Structure

```
backend/app/
├── main.py                  # FastAPI entry point, CORS, UTF-8 encoding middleware
├── core/
│   ├── config.py           # Settings (Pydantic BaseSettings from .env)
│   └── llm_factory.py      # LLM provider abstraction (OpenAI/Claude/Ollama)
├── db/
│   ├── database.py         # SQLAlchemy engine and session management
│   └── models.py           # SQLAlchemy ORM models (all entities)
├── schemas/                # Pydantic models for API validation
│   ├── task.py
│   ├── note.py
│   └── project.py
├── crud/                   # Database operations layer
│   ├── crud_task.py
│   ├── crud_note.py
│   └── crud_project.py
├── services/               # Business logic layer
│   ├── vector_store.py     # pgvector integration (semantic search)
│   ├── memory_service.py   # Memory management (legacy)
│   ├── file_storage.py     # File upload/download service
│   └── chunking.py         # Text chunking service (for RAG)
├── agents/                 # Agno agents
│   └── task_igniter_agno.py  # Task decomposition Agno Agent
└── api/endpoints/          # FastAPI routers
    ├── tasks.py            # Task CRUD + /ignite endpoint
    ├── notes.py            # Note CRUD + semantic search
    ├── chat.py             # AI chat interface (SSE streaming)
    ├── settings.py         # LLM configuration management
    ├── attachments.py      # Attachment management
    ├── links.py            # Note linking system
    └── projects.py         # Project CRUD
```

### Frontend Structure

```
frontend/src/
├── App.vue                 # Root component
├── main.ts                 # Entry point, Vue app initialization
├── router/index.ts         # Vue Router configuration
├── layouts/
│   └── MainLayout.vue      # Sidebar + main content layout
├── views/                  # Route-level pages
│   ├── DashboardView.vue   # Overview dashboard
│   ├── TasksView.vue       # Kanban + List view with filtering
│   ├── NotesView.vue       # Note management
│   └── ReviewView.vue      # Review dashboard
├── components/
│   ├── tasks/              # Task list/Kanban components
│   ├── notes/              # Note list components
│   ├── schedule/           # Calendar/schedule components (WeekSchedule, AllDayTaskCard, AggregationBlock)
│   ├── chat/               # AI chat components (ChatPanel, Messages, SessionList)
│   └── layout/             # Layout components (Sidebar)
├── stores/                 # Pinia state management
│   ├── taskStore.ts        # Task state, CRUD operations
│   ├── noteStore.ts        # Note state
│   ├── projectStore.ts     # Project state
│   ├── chatStore.ts        # Chat history and streaming
│   ├── settingsStore.ts    # LLM configuration
│   └── uiStore.ts          # UI preferences (sidebar, chat panel)
├── api/
│   └── client.ts           # Axios client with base URL
├── composables/            # Vue composables (reusable logic)
│   ├── useKeyboardShortcuts.ts  # Global keyboard shortcuts
│   ├── useTaskAdapter.ts   # Task data transformation
│   ├── useChatStream.ts    # SSE streaming for chat
│   └── useStreamParser.ts  # Parse streaming JSON responses
├── types/
│   └── index.ts            # TypeScript type definitions
├── utils/                  # Utility functions
└── assets/                 # Static assets (styles, images)
```

## Key Architectural Patterns

### Agno Agent Pattern

The Task Igniter Agent (backend/app/agents/task_igniter_agno.py:1) demonstrates the Agno pattern:

1. **Tool Definition**: Define Python functions that agents can call
   ```python
   def search_knowledge_base(query: str, limit: int = 5) -> List[Dict[str, Any]]:
       """Search the knowledge base for related notes."""
       # Implementation
       return results

   def format_task_summary(main_title: str, subtasks: List[Dict]) -> str:
       """Format task decomposition results."""
       # Implementation
       return formatted_summary
   ```

2. **Agent Creation**: Declarative configuration with OpenAI-compatible model
   ```python
   from agno.agent import Agent
   from agno.models.openai import OpenAIChat

   model = OpenAIChat(
       id="gpt-4",
       api_key=settings.OPENAI_API_KEY,
       base_url=settings.OPENAI_API_BASE
   )

   agent = Agent(
       id="task-igniter",
       name="Task Igniter Agent",
       model=model,
       instructions="你是一个任务分解专家...",
       tools=[search_knowledge_base, format_task_summary],
       markdown=True,
       stream_intermediate_steps=True
   )
   ```

3. **Execution**:
   ```python
   # Synchronous
   response = agent.run(user_input, stream=False)

   # Asynchronous
   response = await agent.arun(user_input, stream=False)
   ```

**Key Principles**:
- Declarative agent configuration (no manual state management)
- Functions passed directly as tools (automatic schema generation)
- Built-in streaming and markdown support
- OpenAI-compatible API for multiple LLM providers

### LLM Provider Integration

The system supports multiple LLM providers via `core/llm_factory.py`:

```python
from app.core.llm_factory import get_chat_model

# Get configured LLM
llm = get_chat_model(temperature=0.7)

# Invoke
response = llm.invoke("Your prompt here")
```

Configuration is centralized in `.env`:
- `LLM_PROVIDER=openai|claude|ollama`
- API keys and base URLs for each provider

### Three-Layer Backend Architecture

**API Layer** (endpoints/):
- FastAPI routers for request handling
- Pydantic schema validation only
- Thin layer - delegate to service layer or CRUD
- Example: `@router.post("/ignite")` calls `agent.invoke()`

**Service Layer** (services/):
- Core business logic
- Orchestrates CRUD operations
- Calls AI agents when needed
- **Never** contains raw SQL

**Data Access Layer** (crud/):
- SQLAlchemy query abstraction
- All database operations isolated here
- Functions accept `db: Session` as first parameter

### Frontend State Management (Pinia)

Stores follow consistent pattern:
```typescript
export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])

  async function fetchTasks() {
    const response = await api.get('/tasks/')
    tasks.value = response.data
  }

  return { tasks, fetchTasks }
})
```

### Database & Memory Architecture

**PostgreSQL + pgvector** (cloud-hosted):
- **Relational tables**: tasks, notes, projects, tags (SQLAlchemy ORM)
- **Vector storage**: note_embeddings table with pgvector extension
  - Embedding dimension: 384 (all-MiniLM-L6-v2 model)
  - Index type: IVFFlat for fast similarity search
  - Distance metric: Cosine similarity
- **Benefits**:
  - Single database eliminates sync issues between SQLite and ChromaDB
  - ACID transactions ensure data consistency
  - Cloud deployment enables remote access and automatic backups
  - Native SQL joins between relational and vector data

### SSE Streaming Architecture (Chat Interface)

The chat interface uses Server-Sent Events (SSE) for real-time streaming:

**Backend** (`backend/app/api/endpoints/chat.py`):
- FastAPI `StreamingResponse` with `text/event-stream` content type
- Agent responses streamed incrementally as they're generated
- Event types: `RunStarted`, `RunContent`, `RunCompleted`, `ToolCallStarted`, etc.

**Frontend** (`frontend/src/composables/useChatStream.ts`):
- EventSource API for SSE connection
- Incremental JSON parsing using brace counting
- Automatic message assembly from partial chunks
- Connection cleanup on component unmount

**Format**:
```
data: {"event_type": "RunContent", "content": "partial text..."}

data: {"event_type": "ToolCallStarted", "tool_name": "search_knowledge_base"}

data: {"event_type": "RunCompleted", "final_response": "..."}
```

## Implementation Guidelines

### Adding New Features

1. **Database Changes**:
   - Add models to backend/app/db/models.py:1
   - Create Pydantic schemas in backend/app/schemas/
   - Add CRUD functions in backend/app/crud/

2. **API Endpoints**:
   - Add routes in backend/app/api/endpoints/
   - Register router in backend/app/main.py:1
   - Use dependency injection for `db: Session = Depends(get_db)`

3. **AI Features using Agno**:
   - Define tool functions (plain Python functions with docstrings)
   - Create Agent with declarative configuration
   - Pass tools as list of function references
   - Configure model (OpenAI-compatible)
   - Expose via API endpoint (sync or async)
   - Reference backend/app/agents/task_igniter_agno.py:1 for pattern

4. **Frontend Features**:
   - Create components in frontend/src/components/
   - Add pages in frontend/src/views/
   - Define Pinia stores in frontend/src/stores/
   - Add types to frontend/src/types/index.ts

### Configuration Management

**Two-File Configuration System**:

1. **`.env.example`** (project root) - Template with documentation
   - Committed to Git
   - Contains placeholder API keys
   - Includes all advanced options (database, vector store, etc.)
   - Use as reference for available settings

2. **`backend/.env`** - Actual runtime configuration
   - **NOT committed to Git** (.gitignore)
   - Contains real API keys
   - Auto-generated by frontend Settings page
   - This is the file FastAPI reads

**Configuration Methods**:

**Method 1: Frontend Settings Page (Recommended)**
1. Start backend and frontend
2. Navigate to http://localhost:5173/settings
3. Configure LLM provider and API key
4. Click "Save" - auto-writes to `backend/.env`
5. Hot-reload - no restart needed

**Method 2: Manual Configuration**
```bash
cp .env.example backend/.env
# Edit backend/.env with real API keys
# Restart backend service
```

**Key Settings**:
- `LLM_PROVIDER=openai|claude|ollama` (required)
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` (required for respective provider)
- `OPENAI_API_BASE` / `ANTHROPIC_API_BASE` (optional, for custom endpoints)
- `DATABASE_URL=postgresql://user:password@host:5432/dbname` (required, cloud PostgreSQL)
- `EMBEDDING_MODEL=all-MiniLM-L6-v2` (for local embedding generation)

Access via `backend/app/core/config.py:1` `settings` object (Pydantic with validation).

**IMPORTANT**: Always edit `backend/.env`, not the root `.env.example`!

### Error Handling Patterns

**Backend**:
```python
from fastapi import HTTPException

if not result:
    raise HTTPException(status_code=404, detail="Task not found")
```

**Frontend**:
```typescript
try {
  await taskStore.fetchTasks()
} catch (error) {
  ElMessage.error('Failed to load tasks')
}
```

## Agno Best Practices

1. **Tool Design**: Keep tools focused and single-purpose with clear docstrings
2. **Type Hints**: Use Python type hints for automatic schema generation
3. **Instructions**: Write clear, detailed system instructions in Chinese for better results
4. **Model Config**: Use OpenAI-compatible models via `OpenAIChat` wrapper
5. **Streaming**: Enable `stream_intermediate_steps=True` for transparent tool calls
6. **Error Handling**: Let Agno handle retries; implement graceful fallbacks in tools

## Testing and Quality Assurance

**Manual Testing**:
- Backend: Use API documentation at http://localhost:8000/docs for interactive testing
- Frontend: Manual browser testing (no automated test framework currently)
- Agno Agents: Test via direct `agent.run()` calls or API endpoints

**Integration Testing Scripts** (in `tests/legacy/`):
- `run_tests.py` - Lightweight integration tests for core API functionality
- `test_integration.py` - Comprehensive end-to-end tests covering all features

Run integration tests:
```bash
# Ensure backend is running first (http://localhost:8000)
python tests/legacy/run_tests.py
# Or the comprehensive version:
python tests/legacy/test_integration.py
```

See `tests/README.md` for more details on available test scripts and fixtures.

## Documentation

Project documentation files:
- **`doc/系统现状总结.md`** ⭐ - **Current implementation status** (most accurate, use this first!)
- `doc/需求分析.md` - Requirements and feature specifications (Chinese)
- `doc/框架选型.md` - Framework selection rationale (explains Agno choice)
- `doc/后端详细设计.md` - Backend detailed design (may reference older LangGraph plans)
- `doc/前端详细设计.md` - Frontend detailed design
- `doc/日程表详细设计.md` - Schedule view implementation details
- `.env.README.md` - Environment configuration guide
- `README.md` - Project overview and quick start
- `CLAUDE.md` - This file (development guide for Claude Code)

**Important**: Some older docs may reference LangGraph or future features. Always check `系统现状总结.md` for current implementation status.

## Quick Reference

**Database**: PostgreSQL (cloud-hosted, configured via `DATABASE_URL` in `.env`)
**Vector extension**: pgvector (installed on PostgreSQL server)
**API base URL**: `http://localhost:8000`
**Frontend URL**: `http://localhost:5173`
**API docs**: `http://localhost:8000/docs`

**Frontend Routes**:
- `/` or `/dashboard` - Dashboard overview
- `/tasks` - Task management (Kanban + List + Schedule)
- `/notes` - Note management (Markdown editor)
- `/review` - Data review dashboard (planned)
- `/settings` - LLM configuration (OpenAI/Claude/Ollama)

## Environment Configuration

The `.claude/settings.json` file is configured with:
```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
```

This allows Claude Code to execute commands and make file changes without requesting permission for each action, enabling faster development workflows.

## Common Pitfalls to Avoid

1. **DON'T** put SQL queries in API endpoints - use CRUD layer
2. **DON'T** skip TypeScript type definitions when adding new features
3. **DON'T** forget UTF-8 encoding for Chinese characters (FastAPI uses `UTF8JSONResponse` + middleware)
4. **DON'T** use LangGraph patterns - this project uses Agno
5. **DO** use Agno for AI agents with declarative configuration
6. **DO** refer to backend/app/agents/task_igniter_agno.py:1 for Agno patterns
7. **DO** refer to doc/日程表详细设计.md for schedule view implementation details
8. **DO** refer to doc/系统现状总结.md for current implementation status

## Known Implementation Details

### Chinese Character Encoding
The backend uses a custom `UTF8JSONResponse` class and middleware to ensure proper Chinese character display:
- `UTF8JSONResponse` with `ensure_ascii=False` in `app/main.py`
- Middleware adds `charset=utf-8` to all JSON responses
- This resolves issues with Chinese task titles, descriptions, and project names

### Task Time Management
- **Unassigned tasks** (no `start_time`): Tasks are "未安排" (unassigned), displayed in floating column
- **Scheduled tasks** (`start_time` + `end_time`): Display on weekly schedule with minute precision
- **Snoozed tasks** (`snooze_until`): Hidden until snooze expires, then reappear
- **All-day events**: Tasks spanning 8:00-21:00 viewport display in dedicated all-day row
- Time editing is done through task edit dialog (drag-and-drop removed as of 2025-11-13)

### Project Management
- **System project**: ID=1 "默认" project marked with `is_system=True`
- **Protection**: System projects cannot be deleted or renamed (API returns 403 Forbidden)
- **Task assignment**: All tasks must have a `project_id` (defaults to 1 in creation form)
- **Project tree structure**:
  - **未安排** (status node, fixed at top) - Tasks without `start_time`
  - **Regular projects** (including "默认" system project) - Tasks grouped by `project_id`
  - **已完成** (status node, fixed at bottom) - Tasks with `status='completed'`

### Schedule View Rendering
- Uses continuous rendering (no segmentation by hour)
- Overlap detection via sweep-line algorithm groups overlapping tasks into gray aggregation blocks
- 1 minute = 1 pixel positioning precision
- Truncation indicators (zigzag + arrow + time label) for events outside 8:00-21:00 viewport

## Technology Stack Clarification

**IMPORTANT**: This project uses **Agno** for AI agents, NOT LangGraph. Some older documentation may reference LangGraph, but the actual implementation has migrated to Agno for its lighter weight and declarative approach.

**Framework Evolution**:
- Initial plan: LangGraph (state-driven workflow)
- Current implementation: **Agno** (declarative agent configuration)
- Reason: Simpler API, better developer experience, less boilerplate

Refer to:
- `doc/系统现状总结.md` - Current implementation status
- `doc/框架选型.md` - Framework selection rationale
- `backend/app/agents/task_igniter_agno.py` - Reference implementation
