/**
 * Chat System Type Definitions
 * Adapted from agent-ui for Personal Growth OS
 */

// ============================================================================
// Event Types
// ============================================================================

/**
 * Run event types from LangGraph Agent streaming
 */
export enum RunEvent {
  // Agent Run Events
  RunStarted = 'RunStarted',
  RunContent = 'RunContent',
  RunCompleted = 'RunCompleted',
  RunError = 'RunError',
  RunOutput = 'RunOutput',

  // Tool Call Events
  ToolCallStarted = 'ToolCallStarted',
  ToolCallCompleted = 'ToolCallCompleted',

  // Reasoning Events
  ReasoningStarted = 'ReasoningStarted',
  ReasoningStep = 'ReasoningStep',
  ReasoningCompleted = 'ReasoningCompleted',

  // Memory Events
  MemoryUpdateStarted = 'MemoryUpdateStarted',
  MemoryUpdateCompleted = 'MemoryUpdateCompleted',

  // Control Events
  RunCancelled = 'RunCancelled',
  RunPaused = 'RunPaused',
  RunContinued = 'RunContinued'
}

// ============================================================================
// Tool Call Types
// ============================================================================

/**
 * Tool call information with metrics
 */
export interface ToolCall {
  role: 'user' | 'tool' | 'system' | 'assistant'
  content: string | null
  tool_call_id: string
  tool_name: string
  tool_args: Record<string, unknown>
  tool_call_error: boolean
  metrics: {
    time: number  // Execution time in milliseconds
  }
  created_at: number
}

// ============================================================================
// Reasoning Types
// ============================================================================

/**
 * Agent reasoning step
 */
export interface ReasoningStep {
  title: string
  action?: string
  result: string
  reasoning: string
  confidence?: number
  next_action?: string
}

/**
 * Reasoning message (alternative format)
 */
export interface ReasoningMessage {
  role: 'user' | 'tool' | 'system' | 'assistant'
  content: string | null
  tool_call_id?: string
  tool_name?: string
  tool_args?: Record<string, unknown>
  tool_call_error?: boolean
  metrics?: {
    time: number
  }
  created_at?: number
}

// ============================================================================
// Reference Types (RAG Knowledge Retrieval)
// ============================================================================

/**
 * Knowledge base reference data
 */
export interface ReferenceData {
  query: string
  references: Reference[]
  time?: number
}

/**
 * Single reference/citation
 */
export interface Reference {
  content: string
  meta_data: {
    chunk: number
    chunk_size: number
    note_id?: number        // Added for Personal Growth OS
    note_title?: string     // Added for Personal Growth OS
  }
  name: string  // Document name
}

// ============================================================================
// Message Types
// ============================================================================

/**
 * Chat message structure
 * Core data type for message list display
 */
export interface ChatMessage {
  id?: string  // Unique message identifier
  role: 'user' | 'assistant' | 'system'
  content: string
  streamingError?: boolean
  created_at: number
  task_id?: number  // Added: link to specific task context
  tool_calls?: ToolCall[]
  extra_data?: {
    reasoning_steps?: ReasoningStep[]
    reasoning_messages?: ReasoningMessage[]
    references?: ReferenceData[]
  }
}

// ============================================================================
// Session Types
// ============================================================================

/**
 * Chat session entry
 */
export interface SessionEntry {
  session_id: string
  session_name: string  // First user message or custom name
  created_at: number
  updated_at?: number
  message_count?: number  // Added for display
}

/**
 * Session list with pagination
 */
export interface SessionList {
  sessions: SessionEntry[]
  total: number
  page: number
  page_size: number
}

// ============================================================================
// Streaming Response Types
// ============================================================================

/**
 * Run response content from streaming API
 * This is the format received from /api/chat/stream endpoint
 */
/**
 * Event data for tool calls
 */
export interface ToolCallEventData {
  tool_name: string
  tool_args?: Record<string, unknown>
  tool_result?: string
}

export interface RunResponseContent {
  content?: string | object
  content_type: string
  event: RunEvent
  event_data?: ToolCallEventData
  messages?: Array<{
    role: string
    content: string | null
    created_at: number
  }>
  metrics?: object
  model?: string
  run_id?: string
  agent_id?: string
  session_id?: string
  tool?: ToolCall
  tools?: ToolCall[]
  created_at: number
  extra_data?: {
    reasoning_steps?: ReasoningStep[]
    reasoning_messages?: ReasoningMessage[]
    references?: ReferenceData[]
  }
}

/**
 * New streaming format (event + data structure)
 * Used for format detection and conversion
 */
export interface NewFormatData {
  event: string
  data: string | Record<string, unknown>
}

// ============================================================================
// API Request/Response Types
// ============================================================================

/**
 * Chat stream request payload
 */
export interface ChatStreamRequest {
  message: string
  task_id?: number
  session_id?: string | null
  stream?: boolean
}

/**
 * Chat session history response
 */
export interface SessionHistoryResponse {
  session_id: string
  messages: ChatMessage[]
  created_at: number
  updated_at: number
}

// ============================================================================
// UI Component Props Types
// ============================================================================

/**
 * Message item component props
 */
export interface MessageItemProps {
  message: ChatMessage
  isLastMessage?: boolean
}

/**
 * Reasoning steps component props
 */
export interface ReasoningStepsProps {
  steps: ReasoningStep[]
}

/**
 * References component props
 */
export interface ReferencesProps {
  references: ReferenceData[]
}

/**
 * Tool call badge component props
 */
export interface ToolCallBadgeProps {
  toolCall: ToolCall
}

/**
 * Session list component props
 */
export interface SessionListProps {
  sessions: SessionEntry[]
  currentSessionId?: string | null
  loading?: boolean
}
