# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Personal Growth OS** is a "second brain" application designed to accelerate personal growth by helping users combat procrastination, solidify knowledge, and drive continuous self-improvement through data-driven reflection.

**Current Status**: MVP implementation in progress. Backend core features and database models are implemented. Frontend has basic UI structure with TasksView supporting Kanban/List views. RAG and advanced AI features are partially implemented.

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
- **LangGraph** (primary AI agent framework - state-driven workflows)
- LangChain Core (only for LLM interfaces, **NOT** chains)
- SQLAlchemy + SQLite
- ChromaDB (vector store)
- Mem0 (long-term memory)

**Data Layer (Three-Part Memory System):**
1. **SQLite** - Factual memory (structured data: tasks, notes metadata, projects, user config)
2. **ChromaDB** - Knowledge corpus (vectorized document chunks for RAG)
3. **Mem0** - Long-term memory (conversation history, context, user preferences)

### Architectural Principles

- **Frontend**: Pure presentation layer communicating via RESTful API
- **Backend**: Three-layer architecture
  - API Layer (`/app/api/endpoints/`) - Request handling and validation
  - Service Layer (`/app/services/`) - Core business logic
  - Data Access Layer (`/app/crud/`) - Database operations abstraction
- **Separation of Concerns**: Complex business logic encapsulated as stateful LangGraph agents (e.g., "Task Ignition Ritual")
- **LangGraph-First**: Use LangGraph StateGraph for all complex AI workflows, avoid LangChain chains

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

**Note**: This project includes Windows-specific command syntax in many places. When working on Windows, use the Windows commands provided. On Linux/Mac, use the alternative commands shown.

## Key Design Decisions

### Database Schema (SQLite)

Core entities with relationships:
- `projects` - Top-level organizational containers with `color` for UI differentiation
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
- `user_profile_memories` - Isolated table for AI assistant's understanding of user preferences (with `is_active` for soft deletion)

### Critical Features

1. **Task Ignition Ritual (任务启动仪式)** - IMPLEMENTED
   - Automatic task decomposition for vague/large tasks via LangGraph agent
   - Auto-retrieval of related historical notes/files from knowledge base
   - Generation of "minimum viable starting task" to reduce action friction

2. **Calendar/Schedule View (日程管理)** - IMPLEMENTED
   - Weekly schedule visualization with time-slot planning
   - Tasks with `start_time`/`end_time` display on calendar grid
   - Supports all-day tasks and time-specific tasks
   - Frontend components: WeekSchedule, TaskCard, AllDayTaskCard, AggregationBlock
   - Enables time-boxing and time-blocking workflows

3. **Flexible Task Deferral (灵活延后)** - PARTIAL
   - `snooze_until` database field implemented
   - UI/notification system pending

4. **Contextual Knowledge Resurrection (知识自动重现)** - PARTIAL
   - Semantic search API implemented via ChromaDB
   - Proactive suggestion UI pending

5. **Interactive Review Dashboard (可交互复盘仪表盘)** - PLANNED
   - Dual trigger: scheduled automatic + manual on-demand
   - Data-driven insight modules: task patterns, procrastination detection
   - ECharts integration ready in frontend

## Architecture Implementation Details

### Backend Structure

```
backend/app/
├── main.py                  # FastAPI entry point, CORS, router registration
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
│   ├── vector_store.py     # ChromaDB integration
│   └── memory_service.py   # Mem0 integration
├── agents/                 # LangGraph agents
│   └── task_igniter_agent.py  # Task decomposition agent (LangGraph StateGraph)
└── api/endpoints/          # FastAPI routers
    ├── tasks.py            # Task CRUD + /ignite endpoint
    ├── notes.py            # Note CRUD + semantic search
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
│   ├── tasks/              # Task list/Kanban components (TaskList, TaskCard)
│   ├── notes/              # Note list components (NoteCard)
│   ├── schedule/           # Calendar/schedule components (WeekSchedule, TaskCard, AllDayTaskCard, AggregationBlock, ConnectorLine)
│   ├── layout/             # Layout components (Sidebar, ChatPanel)
│   └── (other domain components as needed)
├── stores/                 # Pinia state management
│   ├── taskStore.ts        # Task state, CRUD operations
│   ├── noteStore.ts        # Note state
│   ├── projectStore.ts     # Project state
│   ├── chatStore.ts        # Chat history
│   └── uiStore.ts          # UI preferences (sidebar, theme)
├── api/
│   └── client.ts           # Axios client with base URL
├── composables/            # Vue composables (reusable logic)
│   ├── useKeyboardShortcuts.ts  # Global keyboard shortcuts
│   └── useTaskAdapter.ts   # Task data transformation
├── types/
│   └── index.ts            # TypeScript type definitions
├── utils/                  # Utility functions
└── assets/                 # Static assets (styles, images)
```

## Key Architectural Patterns

### LangGraph Agent Pattern (State-Driven)

The Task Igniter Agent ([task_igniter_agent.py](backend/app/agents/task_igniter_agent.py:1)) demonstrates the core LangGraph pattern:

1. **State Definition**: `TaskIgniterState` TypedDict with status tracking
   ```python
   class TaskIgniterState(TypedDict):
       user_input: str
       main_task_title: str
       main_task_description: str
       subtasks: Annotated[List[Dict], add]  # Uses reducer for accumulation
       minimum_viable_task_index: int
       related_notes: List[Dict]
       status: Literal["init", "analyzing", "decomposing", "retrieving", "completed", "error"]
       error_message: str | None
   ```

2. **Node Functions**: Each node is a pure function receiving state and returning partial updates
   - `analyze_task_node`: LLM extracts title/description
   - `decompose_task_node`: LLM creates 3-5 subtasks with JSON output
   - `retrieve_notes_node`: ChromaDB semantic search
   - `finalize_node`: Sets completion status

3. **Conditional Routing**: `route_after_analyze()`, `route_after_decompose()` for dynamic flow based on status

4. **Graph Compilation**:
   ```python
   builder = StateGraph(TaskIgniterState)
   builder.add_node("analyze_task", analyze_task_node)
   builder.add_conditional_edges("analyze_task", route_after_analyze)
   graph = builder.compile()
   ```

5. **Visualization Support**: `get_graph_visualization()` returns Mermaid diagram accessible via `/api/tasks/agent/visualization`

**CRITICAL PATTERN**: Always use LangGraph StateGraph for complex AI workflows. Do NOT use LangChain chains or legacy patterns.

### LLM Provider Abstraction

[llm_factory.py](backend/app/core/llm_factory.py:1) provides unified interface via `get_chat_model()`:

- Reads `LLM_PROVIDER` from env (openai/claude/ollama)
- Returns LangChain ChatModel interface
- Supports custom API base URLs via `OPENAI_API_BASE` / `ANTHROPIC_API_BASE` (for proxy/alternative endpoints)

**Usage Pattern**:
```python
from app.core.llm_factory import get_chat_model

llm = get_chat_model(temperature=0.7)
response = llm.invoke("Your prompt here")
```

When writing new agents, ALWAYS use `get_chat_model()` instead of hardcoding provider.

### Three-Layer Backend Architecture

**API Layer** ([endpoints/](backend/app/api/endpoints/)):
- FastAPI routers for request handling
- Pydantic schema validation only
- Thin layer - delegate to service layer or CRUD
- Example: `@router.post("/ignite")` calls agent.invoke()

**Service Layer** ([services/](backend/app/services/)):
- Core business logic
- Orchestrates CRUD operations
- Calls AI agents when needed
- **Never** contains raw SQL

**Data Access Layer** ([crud/](backend/app/crud/)):
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

## Implementation Guidelines

### Adding New Features

1. **Database Changes**:
   - Add models to [db/models.py](backend/app/db/models.py:1)
   - Create Pydantic schemas in [schemas/](backend/app/schemas/)
   - Add CRUD functions in [crud/](backend/app/crud/)

2. **API Endpoints**:
   - Add routes in [api/endpoints/](backend/app/api/endpoints/)
   - Register router in [main.py](backend/app/main.py:1)
   - Use dependency injection for `db: Session = Depends(get_db)`

3. **AI Features**:
   - Create LangGraph agents in [agents/](backend/app/agents/)
   - Follow [task_igniter_agent.py](backend/app/agents/task_igniter_agent.py:1) pattern
   - Always use `get_chat_model()` for LLM calls
   - Define state with TypedDict and use `Annotated[List, add]` for reducers

4. **Frontend Features**:
   - Create components in [components/](frontend/src/components/)
   - Add pages in [views/](frontend/src/views/)
   - Define Pinia stores in [stores/](frontend/src/stores/)
   - Add types to [types/index.ts](frontend/src/types/index.ts)

### Configuration Management

All settings via environment variables in `.env`:
- Copy `.env.example` to `.env`
- **Required**: `LLM_PROVIDER=openai|claude|ollama`
- **Required**: API keys for chosen provider
- **Optional**: Custom API endpoints (`OPENAI_API_BASE`, `ANTHROPIC_API_BASE`)
- ChromaDB path: `CHROMA_PERSIST_DIRECTORY=./chroma_data`
- Mem0 path: `MEM0_PERSIST_DIRECTORY=./mem0_data`

Access via [core/config.py](backend/app/core/config.py:1) `settings` object (Pydantic with validation).

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

## LangGraph Best Practices

1. **State Minimalism**: Only include necessary data in state TypedDict
2. **Node Single Responsibility**: Each node does one thing well
3. **Error Handling**: Every node should catch exceptions and update `status` field
4. **Type Safety**: Use TypedDict and Literal types for state definition
5. **Visualization**: Use `/api/tasks/agent/visualization` to debug agent flow
6. **Testing**: Write unit tests for individual node functions before graph compilation

## Testing and Quality Assurance

The project includes a specialized Claude Code agent for testing:

**Test Validator Agent** (`.claude/agents/test-validator.md`):
- Automatically invoked when testing is requested
- Validates API endpoints, frontend components, and LangGraph agents
- Checks architectural compliance (three-layer backend, LangGraph patterns)
- Tests both happy paths and error scenarios
- Provides detailed PASS/FAIL reports with actionable recommendations

**Manual Testing**:
- Backend: Use API documentation at http://localhost:8000/docs for interactive testing
- Frontend: Manual browser testing (no automated test framework currently)
- LangGraph Agents: Use `/api/tasks/agent/visualization` to inspect agent workflows

**No Formal Test Suite**: The project currently relies on manual testing and the test-validator agent. There is no pytest or vitest configuration.

## Documentation

Project documentation files:
- `/doc/需求.md` - Requirements and feature specifications (Chinese)
- `LANGGRAPH_ARCHITECTURE.md` - LangGraph implementation guide (English)
- `README.md` - Project overview and quick start
- `QUICKSTART.md` - Step-by-step setup guide
- `backend/README.md` - Backend-specific documentation
- `frontend/README.md` - Frontend-specific documentation

Refer to these documents for detailed specifications when implementing features.

## Quick Reference

**Database location**: `backend/personal_growth_os.db`
**Vector store**: `backend/chroma_data/` (ChromaDB)
**Memory store**: `backend/mem0_data/` (Mem0)
**API base URL**: `http://localhost:8000`
**Frontend URL**: `http://localhost:5173`
**API docs**: `http://localhost:8000/docs`

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

1. **DON'T** use LangChain chains - use LangGraph StateGraph instead
2. **DON'T** hardcode LLM provider - use `get_chat_model()`
3. **DON'T** put SQL queries in API endpoints - use CRUD layer
4. **DON'T** forget to handle LLM JSON parsing errors (strip markdown code blocks)
5. **DON'T** skip TypeScript type definitions when adding new features
6. **DO** check [LANGGRAPH_ARCHITECTURE.md](LANGGRAPH_ARCHITECTURE.md:1) before creating new agents
7. **DO** use `Annotated[List[Dict], add]` for accumulating state fields in LangGraph
