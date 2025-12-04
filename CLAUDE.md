# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Personal Growth OS** is a "second brain" application designed to accelerate personal growth by helping users combat procrastination, solidify knowledge, and drive continuous self-improvement through data-driven reflection.

**Current Status**: MVP in active development. Backend uses **LangGraph 1.0** for AI agents, **llama-index 0.14.6** for RAG, with **PostgreSQL + pgvector** for unified data and vector storage. Frontend features weekly schedule view, task kanban with floating task column, AI chat panel, and comprehensive task/note management. Chinese character encoding is fully supported.

**IMPORTANT**: The actual implementation uses **LangGraph 1.0** framework. Reference `backend/app/agents/task_igniter_langgraph.py` for the agent implementation pattern. Tool integration (FastMCP/RAG) will be added in future iterations.

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
- **LangGraph 1.0** (state-of-the-art AI agent framework by LangChain)
- **llama-index 0.14.6** (RAG and data framework for LLM apps) - 计划集成
- SQLAlchemy + **PostgreSQL** (cloud-hosted)
- **pgvector** extension (vector similarity search)
- sentence-transformers (现有embedding实现)

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
- **Separation of Concerns**: Complex AI logic encapsulated as LangGraph StateGraph with declarative configuration
- **Agent-First**: Use LangGraph's state-based agent definitions (tool integration planned for future)

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

**PostgreSQL + pgvector** (cloud-hosted): The database is hosted on a remote PostgreSQL server with pgvector extension for vector similarity search.

**Configuration**: Set `DATABASE_URL` in `backend/.env`:
```bash
DATABASE_URL=postgresql://username:password@host:5432/personal_growth_os
```

**Database initialization**: Tables and pgvector extension are auto-created on first startup. The system will:
1. Create pgvector extension: `CREATE EXTENSION IF NOT EXISTS vector`
2. Create all tables defined in `models.py`
3. Create default "默认" project if not exists

**To reset database** (use with caution - deletes all data):
```sql
-- Connect to PostgreSQL and drop/recreate database
DROP DATABASE personal_growth_os;
CREATE DATABASE personal_growth_os;
-- Extension will be recreated on app startup
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

**Reference Implementations** (in `library/`):
- `open_deep_research/` - Original open_deep_research implementation (inspiration for deep_researcher agent)
- `DingtalkChatbot/` - DingTalk chatbot library reference
- `apscheduler/` - APScheduler library reference

See `tests/README.md` and `backend/utils/README.md` for detailed usage instructions.

**Note**: This project includes Windows-specific command syntax in many places. When working on Windows, use the Windows commands provided. On Linux/Mac, use the alternative commands shown.

## Key Design Decisions

### Database Schema (PostgreSQL)

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

1. **Task Ignition Ritual (任务启动仪式)** - IMPLEMENTED (LangGraph)
   - Automatic task decomposition for vague/large tasks via LangGraph StateGraph
   - Pure LLM-based reasoning (tool integration planned for future)
   - Generation of "minimum viable starting task" to reduce action friction
   - **Implementation**: `backend/app/agents/task_igniter_langgraph.py` using LangGraph StateGraph
   - **Future**: Tool-based knowledge retrieval (RAG) and task formatting tools

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
   - **Task Reminder System** - DingTalk integration with APScheduler
     - Automatic reminders for due tasks and task start times
     - Configurable via `ENABLE_TASK_REMINDER`, `DINGTALK_WEBHOOK`, `DINGTALK_SECRET` in `.env`
     - Implementation: `backend/app/core/scheduler.py`

4. **Contextual Knowledge Resurrection (知识自动重现)** - IMPLEMENTED
   - Semantic search API implemented via **llama-index PGVectorStore**
   - Note embeddings auto-generated on create/update using llama-index embedding models
   - Vector similarity search with cosine distance through llama-index QueryEngine
   - Supports hybrid retrieval (text + vector)
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
│   ├── llm_factory.py      # LLM provider abstraction (LangGraph + llama-index)
│   ├── llm_utils.py        # JWT authentication support for LLM proxies
│   ├── scheduler.py        # APScheduler for task reminders
│   └── langgraph_checkpoint.py  # LangGraph PostgreSQL checkpointer
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
│   ├── vector_store.py     # pgvector integration (现有实现)
│   ├── file_storage.py     # File upload/download service
│   └── chunking.py         # Text chunking
├── agents/                 # LangGraph agents
│   └── task_igniter_langgraph.py  # Task decomposition LangGraph agent
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

### LangGraph Agent Pattern

The Task Igniter Agent (backend/app/agents/task_igniter_langgraph.py) demonstrates the LangGraph 1.0 pattern:

**Core Concepts**:

1. **StateGraph Architecture**: State-based agent workflow built on a directed graph
   - Nodes represent processing steps (agent reasoning, error handling)
   - Edges define flow between nodes (normal transitions and conditional routing)
   - State is a TypedDict that flows through the graph

2. **Graph Construction** (current implementation):
   - Define agent node that invokes LLM
   - Simple linear flow: Entry → Agent → END
   - Compile graph into executable runnable

3. **Execution Modes**:
   - Synchronous: graph.invoke() for blocking execution
   - Asynchronous: graph.ainvoke() for async workflows
   - Streaming: graph.astream_events() for real-time updates

**Key Features**:
- Pure LLM-based reasoning (no tools in current version)
- Streaming support for incremental responses via SSE
- Multi-provider support (OpenAI, Claude, Ollama)
- State management via message-based architecture

**Future Enhancements** (planned):
- Tool integration for knowledge retrieval and task formatting
- Conditional routing based on LLM tool calls
- Integration with llama-index for RAG capabilities

Reference implementation: backend/app/agents/task_igniter_langgraph.py

### Deep Task Researcher Architecture (LangGraph 1.0)

**NEW**: The system now includes a sophisticated multi-layer research agent inspired by open_deep_research, implementing advanced LangGraph 1.0 patterns for intelligent task decomposition.

**Architecture Overview**:

The Deep Task Researcher uses a **three-layer hierarchical structure**:

```
┌─────────────────────────────────────────────────┐
│           Main: Deep Task Researcher            │
│  (clarify → research_brief → supervisor → final) │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  Subgraph: Supervisor        │
        │  (delegate → tools → reflect)│
        └──────────┬───────────────────┘
                   │
                   ▼ (ConductResearch tool call)
    ┌──────────────────────────────────────┐
    │  Subgraph: Researcher                │
    │  (search → think → compress)         │
    └──────────────────────────────────────┘
```

**Key Features**:

1. **Command API**: Type-safe routing with `Command[Literal["node1", "node2"]]` return types
2. **Structured Output**: Forces LLM to return Pydantic models via `.with_structured_output()`
3. **Tool Integration**:
   - `search_knowledge_base`: RAG tool using pgvector semantic search
   - `think_tool`: Strategic reflection for better decision-making
4. **Subgraph Delegation**: Supervisor delegates research tasks to multiple Researcher agents running in parallel
5. **Automatic Clarification**: Detects vague user input and asks clarifying questions before proceeding
6. **Persistent Sessions**: Uses LangGraph PostgreSQL checkpointer for conversation history

**File Structure**:

```
backend/app/agents/deep_researcher/
├── __init__.py                 # Package exports
├── state.py                    # All state definitions + Pydantic models
├── prompts.py                  # System prompts adapted from open_deep_research
├── tools.py                    # search_knowledge_base + think_tool
├── researcher_graph.py         # Researcher subgraph (search → compress)
├── supervisor_graph.py         # Supervisor subgraph (delegate → collect)
└── main_graph.py              # Main graph (clarify → decompose)
```

**State Definitions**:

- **DeepTaskState** (Main graph): Messages, clarification flag, research brief, notes, final output
- **SupervisorState** (Supervisor): Supervisor messages, research brief, notes, iteration count
- **ResearcherState** (Researcher): Researcher messages, research topic, tool iterations, compressed research

**Pydantic Models** (Structured Outputs):

- `ClarifyWithUser`: Whether clarification is needed + question/verification
- `ResearchBrief`: Detailed research question generated from user messages
- `TaskDecomposition`: Main task + subtasks + minimum viable task index
- `Subtask`: Title, description, priority (1-5)
- `ConductResearch`: Tool for supervisor to delegate research
- `Summary`: Compressed research findings

**Agent Selection**:

The Chat API (`/api/chat/agents/{agent_id}/runs`) now supports two agents:

1. **`task-igniter`**: Legacy single-layer agent (simple, fast)
2. **`deep-task-researcher`**: New three-layer research agent (comprehensive, slow)

Usage example:
```bash
curl --location 'http://localhost:8000/api/chat/agents/deep-task-researcher/runs' \
  --header 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'message=准备项目演示PPT' \
  --data-urlencode 'stream=True'
```

**Workflow**:

1. **Clarify Node**: Checks if user intent is clear. If not, returns clarifying question and ends.
2. **Write Research Brief**: Converts user message into detailed research question.
3. **Research Supervisor**: Delegates research to Supervisor subgraph:
   - Supervisor decides which research tasks to delegate
   - Spawns Researcher agents in parallel using `asyncio.gather()`
   - Each Researcher searches knowledge base and thinks strategically
   - Results are compressed and returned to Supervisor
4. **Final Decomposition**: Generates structured task decomposition with:
   - Main task title + description
   - 3-5 subtasks (each with title, description, priority)
   - Minimum viable task index (lowest friction starting point)

**Tool Call Visualization**:

The frontend chat interface now displays tool calls in real-time:
- **ToolCallBadge** component shows tool name, arguments, and results
- Hover popover displays detailed execution info
- Execution time calculated and displayed
- SSE events: `ToolCallStarted` → `ToolCallCompleted`

**Reference Files**:
- Implementation: `backend/app/agents/deep_researcher/main_graph.py`
- API integration: `backend/app/api/endpoints/chat.py` (lines 78-103)
- Frontend store: `frontend/src/stores/chatStore.ts` (lines 507-555)
- UI component: `frontend/src/components/chat/ToolCallBadge.vue`

**Performance Considerations**:
- Supervisor can spawn multiple Researchers (configurable, default: 2 max)
- Maximum research iterations: 6 (prevents infinite loops)
- Each Researcher can make up to 10 tool calls
- Typical response time: 5-15 seconds for complex tasks

**When to Use Deep Task Researcher**:
- User input is vague or needs clarification
- Task requires domain knowledge from notes/documents
- Complex multi-step projects needing strategic breakdown
- When quality > speed (tradeoff: slower but more thorough)

### LLM Provider Integration

The system supports multiple LLM providers through unified configuration in `.env`:
- `LLM_PROVIDER=openai|claude|ollama`
- Provider-specific API keys and base URLs

**For LangGraph Agents**:
- Use `core/llm_factory.py::get_langgraph_model()` to get LangChain LLM instance
- **Alternative**: Use `core/llm_utils.py::get_langchain_llm_with_auth()` for JWT authentication support
  - Automatically detects JWT tokens (starts with "eyJ") vs standard API keys
  - Supports proxy services that use JWT in Authorization header (e.g., TrendMicro proxy)
- Returns ChatOpenAI, ChatAnthropic, or ChatOllama based on configuration
- Automatically configures API keys and endpoints

**For llama-index RAG**:
- Use `core/llm_factory.py::get_llamaindex_llm()` for LLM
- Use `core/llm_factory.py::get_llamaindex_embed_model()` for embeddings
- Supports OpenAI, Anthropic, or local embedding models
- llama-index ServiceContext automatically manages these components

**Embedding Models**:
- OpenAI: text-embedding-3-small (1536 dimensions)
- Local: sentence-transformers models (e.g., all-MiniLM-L6-v2, 384 dimensions)
- Configured via llama-index embedding integrations

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

Stores follow composition API pattern with reactive state:
- Use `defineStore` with setup function syntax
- Reactive state with `ref()` and `computed()`
- Async actions for API calls
- Return public API for component consumption

Example stores: taskStore, noteStore, projectStore, chatStore, settingsStore, uiStore

### Database & Memory Architecture

**PostgreSQL + pgvector (via llama-index)**:
- **Relational tables**: tasks, notes, projects, tags (SQLAlchemy ORM)
- **Vector storage**: Managed by llama-index PGVectorStore
  - Embedding dimension: Configurable (384 or 1536 based on model)
  - Index type: IVFFlat automatically managed by llama-index
  - Distance metric: Cosine similarity
  - Hybrid search: Combines text and vector retrieval
- **Benefits**:
  - Single database eliminates sync issues
  - ACID transactions ensure data consistency
  - llama-index abstracts vector operations
  - Cloud deployment ready with automatic backups
  - Native SQL joins between relational and vector data
- **llama-index Integration**:
  - VectorStoreIndex for semantic search
  - ServiceContext for LLM and embedding configuration
  - QueryEngine for flexible retrieval strategies

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

**Format**: JSON events with event_type field (RunContent, ToolCallStarted, RunCompleted, etc.)

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

3. **AI Features using LangGraph**:
   - Create StateGraph with defined nodes and edges
   - Define agent node that invokes LLM
   - Add edges (linear flow or conditional routing)
   - Compile graph and expose via API endpoint
   - Reference backend/app/agents/task_igniter_langgraph.py for pattern
   - Tool integration (optional): Use @tool decorator or ToolNode

4. **RAG Features** (current implementation):
   - Use existing vector_store.py for semantic search
   - Embeddings via sentence-transformers
   - pgvector for vector similarity matching
   - Future: Migrate to llama-index for advanced RAG capabilities

5. **Frontend Features**:
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
  - Supports both standard API keys (sk-...) and JWT tokens (eyJ...) for proxy services
- `OPENAI_API_BASE` / `ANTHROPIC_API_BASE` (optional, for custom endpoints)
- `DATABASE_URL=postgresql://user:password@host:5432/dbname` (required, cloud PostgreSQL)
- `EMBEDDING_MODEL=all-MiniLM-L6-v2` (for local embedding generation)
- `ENABLE_TASK_REMINDER=True` (optional, enable DingTalk task reminders)
- `DINGTALK_WEBHOOK` / `DINGTALK_SECRET` (optional, for DingTalk notifications)

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

## LangGraph + llama-index Best Practices

### LangGraph Agent Development

1. **State Design**: Use TypedDict with clear field annotations for agent state
   - Keep state minimal - only data needed for routing decisions
   - Use Annotated with reducer functions for list fields

2. **Graph Structure**: Favor simple, linear flows over complex branching
   - Use conditional edges for tool routing
   - Leverage prebuilt components (ToolNode, tools_condition)

3. **Tool Integration**: Use FastMCP for clean tool definitions
   - One MCP server per agent or logical grouping
   - Async tool functions for I/O operations
   - Type hints for automatic JSON Schema generation

4. **Error Handling**: Implement error nodes in graph
   - Use try/except in node functions
   - Add retry logic with exponential backoff

5. **Streaming**: Use `astream_events` for real-time updates
   - Stream tool calls and LLM tokens separately
   - Implement proper event filtering for frontend

### llama-index RAG Development

1. **Index Design**: One index per data type (notes, tasks, etc.)
   - Use PGVectorStore for persistent storage
   - Configure appropriate chunk size (default 512)

2. **Query Engines**: Choose the right engine type
   - VectorIndexRetriever for pure semantic search
   - RetrieverQueryEngine with postprocessors for advanced filtering
   - SubQuestionQueryEngine for complex multi-step queries

3. **Embeddings**: Use consistent embed_model across indexing and querying
   - OpenAI embeddings for best quality
   - Local models (sentence-transformers) for privacy

4. **Performance**: Implement caching and lazy loading
   - Cache ServiceContext and query engines
   - Use `as_query_engine()` method for efficiency

## Testing and Quality Assurance

**Manual Testing**:
- Backend: Use API documentation at http://localhost:8000/docs for interactive testing
- Frontend: Manual browser testing (no automated test framework currently)
- LangGraph Agents: Test via direct `graph.invoke()` calls or API endpoints

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
- **`doc/interview-logs/`** - STAR-format technical solution logs for interview preparation
  - `2025-12-03-chat-streaming-react-agent.md` - Chat streaming + create_react_agent migration
  - `2025-12-02-chat-checkpointer-async-fix.md` - AsyncPostgresSaver fix
  - Indexed by technology stack, problem type, and keywords
- `doc/需求分析.md` - Requirements and feature specifications (Chinese)
- `doc/框架选型.md` - Framework selection rationale (explains LangGraph choice)
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
4. **DON'T** use outdated agent frameworks - this project uses **LangGraph 1.0**
5. **DO** use LangGraph StateGraph for all agent workflows
6. **DO** refer to backend/app/agents/task_igniter_langgraph.py for LangGraph patterns
7. **DO** check LangGraph官方文档 for latest best practices
8. **DO** refer to doc/系统现状总结.md for current implementation status
9. **DO** use sentence-transformers for embeddings (暂时保持现有实现)
10. **DO** use existing vector_store.py for RAG功能 (暂时保持现有实现)

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

**IMPORTANT**: This project uses **LangGraph 1.0** for AI agents and **llama-index 0.14.6** for RAG framework, with **PostgreSQL + pgvector** for unified data storage.

**Current Implementation**:
- **Agent Framework**: LangGraph 1.0 (StateGraph-based orchestration)
- **RAG Framework**: llama-index 0.14.6 (specialized data framework for LLM applications)
- **Tool Integration**: FastMCP (standard tool protocol for LangGraph)
- **Database**: PostgreSQL + pgvector (cloud-hosted, unified storage)
- **Embedding**: Managed by llama-index (sentence-transformers backend)

**Framework Evolution**:
- Initial plan: LangGraph + SQLite + ChromaDB
- Early implementation: Agno + PostgreSQL + sentence-transformers (manual RAG)
- **Current**: **LangGraph 1.0** + **llama-index 0.14.6** + PostgreSQL + pgvector
- Reason: Industry-standard frameworks, better ecosystem, professional RAG capabilities, long-term maintainability

**Database Migration (2025-11)**: Migrated from dual-database (SQLite + ChromaDB) to unified PostgreSQL + pgvector:
- Single data source eliminates sync issues
- ACID transactions for data consistency
- pgvector extension for efficient vector similarity search (managed by llama-index)
- Cloud deployment enables remote access and automatic backups

**Key Dependencies**:

LangGraph Ecosystem:
- `langgraph>=0.2.0` - State-based agent orchestration
- `langgraph-checkpoint-postgres>=2.0.0` - LangGraph PostgreSQL persistence
- `langchain>=0.3.0` - Core LangChain library
- `langchain-openai` / `langchain-anthropic` / `langchain-community` - LLM integrations
- `psycopg-binary>=3.2.0` - PostgreSQL driver for LangGraph checkpointer

Vector & Embeddings:
- `sentence-transformers>=2.2.0` - Embedding generation
- `pgvector>=0.2.4` - Vector similarity search

Database:
- `psycopg2-binary>=2.9.9` - PostgreSQL driver for SQLAlchemy
- `sqlalchemy==2.0.36` - ORM

Task Scheduling & Notifications:
- `apscheduler==3.10.4` - Task reminder scheduling
- `DingtalkChatbot>=1.5.7` - DingTalk notification integration

**Dependencies Removed**:
- `agno` - Replaced by LangGraph 1.0

**Future Dependencies** (planned):
- `llama-index` - Advanced RAG framework
- `fastmcp` - Tool integration protocol
- `mem0ai` - User memory management

**Reference Documentation**:
- LangGraph: https://langchain-ai.github.io/langgraph/
- llama-index: https://docs.llamaindex.ai/
- `doc/系统现状总结.md` - Current implementation status
- `doc/框架选型.md` - Framework selection rationale
- `backend/app/agents/task_igniter_langgraph.py` - Reference implementation
