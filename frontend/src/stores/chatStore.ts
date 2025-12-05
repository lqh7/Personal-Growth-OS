/**
 * Chat Store - Pinia State Management for AI Assistant
 *
 * This store manages:
 * - Real-time streaming chat messages with LangGraph Agent
 * - Session history management
 * - Tool calls, reasoning steps, and knowledge retrieval references
 * - ChatPanel UI state
 *
 * Migrated from agent-ui (React/Zustand) to Vue3/Pinia
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type {
  ChatMessage,
  SessionEntry,
  RunResponseContent,
  ToolCall,
  ReasoningStep,
  UICommand,
  ToastPayload,
  RefreshPayload
} from '@/types/chat'
import { RunEvent } from '@/types/chat'
import { ElMessage } from 'element-plus'
import { useTaskStore } from './taskStore'
import { useNoteStore } from './noteStore'
import { useProjectStore } from './projectStore'

export const useChatStore = defineStore('chat', () => {
  // ============================================================================
  // State - Messages
  // ============================================================================

  /**
   * Current chat messages in active session
   */
  const messages = ref<ChatMessage[]>([])

  /**
   * Streaming state
   */
  const isStreaming = ref(false)
  const streamingErrorMessage = ref('')

  // ============================================================================
  // State - Sessions
  // ============================================================================

  /**
   * Current active session ID
   */
  const currentSessionId = ref<string | null>(null)

  /**
   * Session history list
   */
  const sessions = ref<SessionEntry[]>([])
  const isSessionsLoading = ref(false)

  // ============================================================================
  // State - UI
  // ============================================================================

  /**
   * Chat input reference (for focus management)
   */
  const chatInputRef = ref<HTMLTextAreaElement | null>(null)

  /**
   * ChatPanel visibility (right sidebar)
   */
  const isChatPanelVisible = ref(true) // 默认打开用于测试

  /**
   * Current task context (for task-specific chat)
   */
  const currentTaskId = ref<number | null>(null)

  // ============================================================================
  // Computed
  // ============================================================================

  /**
   * Check if there are any messages
   */
  const hasMessages = computed(() => messages.value.length > 0)

  /**
   * Get last message
   */
  const lastMessage = computed(() => {
    return messages.value.length > 0
      ? messages.value[messages.value.length - 1]
      : null
  })

  /**
   * Check if can send message (not streaming)
   */
  const canSendMessage = computed(() => !isStreaming.value)

  /**
   * Get current session name
   */
  const currentSessionName = computed(() => {
    if (!currentSessionId.value) return null
    const session = sessions.value.find((s) => s.session_id === currentSessionId.value)
    return session?.session_name || null
  })

  // ============================================================================
  // Actions - Message Management
  // ============================================================================

  /**
   * Add a message to the list
   */
  function addMessage(message: ChatMessage) {
    messages.value.push(message)
  }

  /**
   * Update the last message content (for streaming)
   */
  function updateLastMessageContent(content: string) {
    if (messages.value.length === 0) return

    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg.role === 'assistant') {
      lastMsg.content = content
    }
  }

  /**
   * Append content to last message (incremental streaming)
   * Note: Currently we use full content update, not incremental
   */
  function appendToLastMessage(content: string) {
    if (messages.value.length === 0) return

    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg.role === 'assistant') {
      lastMsg.content += content
    }
  }

  /**
   * Add or update tool call in last message
   * Uses tool_call_id or tool_name+created_at as unique identifier
   */
  function updateToolCall(toolCall: ToolCall) {
    if (messages.value.length === 0) return

    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg.role !== 'assistant') return

    if (!lastMsg.tool_calls) {
      lastMsg.tool_calls = []
    }

    // Find existing tool call by ID or name+timestamp
    const toolCallId =
      toolCall.tool_call_id ||
      `${toolCall.tool_name}-${toolCall.created_at}`

    const existingIndex = lastMsg.tool_calls.findIndex(
      (tc) =>
        (tc.tool_call_id && tc.tool_call_id === toolCall.tool_call_id) ||
        (!tc.tool_call_id &&
          `${tc.tool_name}-${tc.created_at}` === toolCallId)
    )

    if (existingIndex >= 0) {
      // Update existing tool call (merge)
      lastMsg.tool_calls[existingIndex] = {
        ...lastMsg.tool_calls[existingIndex],
        ...toolCall
      }
    } else {
      // Add new tool call
      lastMsg.tool_calls.push(toolCall)
    }
  }

  /**
   * Add reasoning step to last message
   */
  function addReasoningStep(step: ReasoningStep) {
    if (messages.value.length === 0) return

    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg.role !== 'assistant') return

    if (!lastMsg.extra_data) {
      lastMsg.extra_data = {}
    }
    if (!lastMsg.extra_data.reasoning_steps) {
      lastMsg.extra_data.reasoning_steps = []
    }

    lastMsg.extra_data.reasoning_steps.push(step)
  }

  /**
   * Set references in last message (knowledge retrieval)
   */
  function setReferences(references: any) {
    if (messages.value.length === 0) return

    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg.role !== 'assistant') return

    if (!lastMsg.extra_data) {
      lastMsg.extra_data = {}
    }

    lastMsg.extra_data.references = references
  }

  /**
   * Mark last message as having streaming error
   */
  function setLastMessageError(error: boolean) {
    if (messages.value.length === 0) return

    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg.role === 'assistant') {
      lastMsg.streamingError = error
    }
  }

  /**
   * Clear all messages and reset session
   */
  function clearMessages() {
    messages.value = []
    currentSessionId.value = null
    currentTaskId.value = null
    streamingErrorMessage.value = ''
  }

  // ============================================================================
  // Actions - Session Management
  // ============================================================================

  /**
   * Set current session ID
   */
  function setCurrentSessionId(sessionId: string | null) {
    currentSessionId.value = sessionId
  }

  /**
   * Add or update session in list
   */
  function upsertSession(session: SessionEntry) {
    const existingIndex = sessions.value.findIndex(
      (s) => s.session_id === session.session_id
    )

    if (existingIndex >= 0) {
      // Update existing session
      sessions.value[existingIndex] = {
        ...sessions.value[existingIndex],
        ...session
      }
    } else {
      // Add to beginning of list (most recent first)
      sessions.value.unshift(session)
    }
  }

  /**
   * Remove session from list
   */
  function removeSession(sessionId: string) {
    sessions.value = sessions.value.filter((s) => s.session_id !== sessionId)

    // Clear current session if it's the one being removed
    if (currentSessionId.value === sessionId) {
      clearMessages()
    }
  }

  /**
   * Set sessions list
   */
  function setSessions(sessionList: SessionEntry[]) {
    sessions.value = sessionList
  }

  /**
   * Set sessions loading state
   */
  function setSessionsLoading(loading: boolean) {
    isSessionsLoading.value = loading
  }

  // ============================================================================
  // Actions - UI State
  // ============================================================================

  /**
   * Set streaming state
   */
  function setStreaming(streaming: boolean) {
    isStreaming.value = streaming
  }

  /**
   * Set streaming error message
   */
  function setStreamingError(error: string) {
    streamingErrorMessage.value = error
  }

  /**
   * Toggle ChatPanel visibility
   */
  function toggleChatPanel() {
    isChatPanelVisible.value = !isChatPanelVisible.value
  }

  /**
   * Show ChatPanel
   */
  function showChatPanel() {
    isChatPanelVisible.value = true
  }

  /**
   * Hide ChatPanel
   */
  function hideChatPanel() {
    isChatPanelVisible.value = false
  }

  /**
   * Set current task context
   */
  function setCurrentTaskId(taskId: number | null) {
    currentTaskId.value = taskId
  }

  /**
   * Open ChatPanel with task context
   * Convenience method for task-specific chat
   */
  function openChatWithTask(taskId: number) {
    setCurrentTaskId(taskId)
    showChatPanel()
    focusChatInput()
  }

  /**
   * Focus chat input
   */
  function focusChatInput() {
    // Use requestAnimationFrame to ensure DOM is ready
    requestAnimationFrame(() => {
      if (chatInputRef.value) {
        chatInputRef.value.focus()
      }
    })
  }

  // ============================================================================
  // Actions - Send Message
  // ============================================================================

  // WebSocket instance
  let ws: WebSocket | null = null

  /**
   * Send message to AI agent using WebSocket
   * Replaces SSE streaming with WebSocket for better bidirectional communication
   */
  async function sendMessage(message: string): Promise<void> {
    // 1. Precondition check
    if (isStreaming.value) {
      console.warn('[ChatStore] Already streaming, ignoring new message')
      return
    }

    // Clear previous errors
    setStreamingError('')

    // 2. Add user message
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}_user`,
      role: 'user',
      content: message,
      created_at: Date.now()
    }
    addMessage(userMessage)

    // 3. Create assistant placeholder message
    const assistantMessage: ChatMessage = {
      id: `msg_${Date.now()}_assistant`,
      role: 'assistant',
      content: '',
      created_at: Date.now()
    }
    addMessage(assistantMessage)

    // 4. Set streaming state
    setStreaming(true)

    try {
      // 5. Connect to WebSocket if not already connected
      const wsUrl = 'ws://localhost:8000/api/chat/ws/agents/orchestrator/chat'

      if (!ws || ws.readyState !== WebSocket.OPEN) {
        ws = new WebSocket(wsUrl)

        ws.onopen = () => {
          console.log('[ChatStore] WebSocket connected')
        }

        ws.onmessage = (event) => {
          try {
            const chunk: RunResponseContent = JSON.parse(event.data)
            processStreamChunk(chunk)
          } catch (parseError) {
            console.error('[ChatStore] Failed to parse WebSocket message:', parseError)
          }
        }

        ws.onerror = (error) => {
          console.error('[ChatStore] WebSocket error:', error)
          setLastMessageError(true)
          setStreamingError('WebSocket connection error')
          setStreaming(false)
        }

        ws.onclose = () => {
          console.log('[ChatStore] WebSocket closed')
          setStreaming(false)
        }

        // Wait for connection to open
        await new Promise<void>((resolve, reject) => {
          if (!ws) {
            reject(new Error('WebSocket is null'))
            return
          }

          const timeout = setTimeout(() => {
            reject(new Error('WebSocket connection timeout'))
          }, 5000)

          ws.addEventListener('open', () => {
            clearTimeout(timeout)
            resolve()
          }, { once: true })

          ws.addEventListener('error', (error) => {
            clearTimeout(timeout)
            reject(error)
          }, { once: true })
        })
      }

      // 6. Send message via WebSocket
      const payload = {
        type: 'message',
        content: message,
        session_id: currentSessionId.value || undefined,
        dependencies: currentTaskId.value
          ? { task_id: currentTaskId.value }
          : undefined
      }

      ws.send(JSON.stringify(payload))

    } catch (error: any) {
      // 7. Error handling
      console.error('[ChatStore] sendMessage error:', error)
      setLastMessageError(true)
      setStreamingError(error.message || 'Unknown error occurred')
      setStreaming(false)

      // Close WebSocket on error
      if (ws) {
        ws.close()
        ws = null
      }
    }
  }

  /**
   * Close WebSocket connection
   */
  function closeWebSocket() {
    if (ws) {
      ws.close()
      ws = null
      console.log('[ChatStore] WebSocket connection closed manually')
    }
  }

  // ============================================================================
  // Actions - Stream Event Processing
  // ============================================================================

  /**
   * Process streaming chunk from API
   * This is the core logic for handling different RunEvent types
   *
   * @param chunk - Streaming event from /api/chat/stream
   */
  function processStreamChunk(chunk: RunResponseContent) {
    switch (chunk.event) {
      case RunEvent.RunStarted:
        // Set session ID if provided
        if (chunk.session_id) {
          setCurrentSessionId(chunk.session_id)
        }
        break

      case RunEvent.RunContent:
        // Append content (incremental streaming)
        if (typeof chunk.content === 'string') {
          appendToLastMessage(chunk.content)
        }
        break

      case RunEvent.ToolCallStarted:
        // Tool call started - create new tool call entry
        if (chunk.event_data) {
          const toolCall: ToolCall = {
            role: 'assistant',
            content: null,
            tool_call_id: `tool_${Date.now()}`,
            tool_name: chunk.event_data.tool_name || 'unknown',
            tool_args: chunk.event_data.tool_args || {},
            tool_call_error: false,
            metrics: { time: 0 },
            created_at: chunk.created_at || Date.now()
          }
          updateToolCall(toolCall)
        }
        // Legacy format support (if tool object provided)
        if (chunk.tool) {
          updateToolCall(chunk.tool)
        }
        if (chunk.tools && chunk.tools.length > 0) {
          chunk.tools.forEach((tool) => updateToolCall(tool))
        }
        break

      case RunEvent.ToolCallCompleted:
        // Tool call completed - update with result
        if (chunk.event_data) {
          // Find the most recent tool call with matching name
          const lastMsg = messages.value[messages.value.length - 1]
          if (lastMsg && lastMsg.tool_calls && lastMsg.role === 'assistant') {
            const matchingTool = lastMsg.tool_calls
              .slice()
              .reverse()
              .find((tc) => tc.tool_name === chunk.event_data!.tool_name && !tc.content)

            if (matchingTool) {
              // Ensure content is string or null
              matchingTool.content = typeof chunk.content === 'string' ? chunk.content : null
              // Calculate execution time if possible
              const executionTime = chunk.created_at - matchingTool.created_at
              matchingTool.metrics = { time: executionTime }
            }
          }
        }
        // Legacy format support
        if (chunk.tool) {
          updateToolCall(chunk.tool)
        }
        if (chunk.tools && chunk.tools.length > 0) {
          chunk.tools.forEach((tool) => updateToolCall(tool))
        }
        break

      case RunEvent.ReasoningStep:
        // Add reasoning step
        if (chunk.extra_data?.reasoning_steps) {
          chunk.extra_data.reasoning_steps.forEach((step) => {
            addReasoningStep(step)
          })
        }
        break

      case RunEvent.RunCompleted:
        // Final update with all data
        if (chunk.content && typeof chunk.content === 'string') {
          updateLastMessageContent(chunk.content)
        }
        if (chunk.extra_data?.references) {
          setReferences(chunk.extra_data.references)
        }

        // Update session in list
        if (chunk.session_id) {
          const firstUserMessage = messages.value.find((m) => m.role === 'user')
          upsertSession({
            session_id: chunk.session_id,
            session_name: firstUserMessage?.content.substring(0, 50) || '新对话',
            created_at: Date.now(),
            message_count: messages.value.length
          })
        }
        break

      case RunEvent.RunError:
        // Mark as error
        setLastMessageError(true)
        if (typeof chunk.content === 'string') {
          setStreamingError(chunk.content)
        } else if (chunk.event_data) {
          setStreamingError(JSON.stringify(chunk.event_data))
        }
        break

      case RunEvent.UICommand:
        // Handle UI command from backend (Dynamic Skills)
        if (chunk.event_data) {
          handleUICommand(chunk.event_data as unknown as UICommand)
        }
        break

      case RunEvent.SkillActivated:
        // Handle skill activation notification
        if (chunk.event_data) {
          console.log('[ChatStore] Skill activated:', chunk.event_data)
          // Could show a loading indicator or badge
        }
        break

      default:
        // Ignore other events (RunOutput, MemoryUpdate, etc.)
        console.debug('[ChatStore] Unhandled event:', chunk.event)
        break
    }
  }

  // ============================================================================
  // Actions - UI Command Handler (Dynamic Skills)
  // ============================================================================

  /**
   * Handle UI commands from backend
   * Supports: toast, refresh, navigate, modal
   */
  function handleUICommand(command: UICommand) {
    console.log('[ChatStore] Handling UI command:', command)

    switch (command.type) {
      case 'toast': {
        const payload = command.payload as ToastPayload
        const messageType = payload.type || 'info'
        ElMessage[messageType](payload.message)
        break
      }

      case 'refresh': {
        const payload = command.payload as RefreshPayload
        refreshData(payload.target)
        break
      }

      case 'navigate': {
        // Navigate to a route (future implementation)
        const path = (command.payload as Record<string, unknown>).path as string
        if (path) {
          console.log('[ChatStore] Navigate to:', path)
          // Could use router.push(path) if needed
        }
        break
      }

      case 'modal': {
        // Open a modal (future implementation)
        console.log('[ChatStore] Open modal:', command.payload)
        break
      }

      default:
        console.warn('[ChatStore] Unknown UI command type:', command.type)
    }
  }

  /**
   * Refresh data based on target
   */
  async function refreshData(target: 'tasks' | 'notes' | 'projects' | 'all') {
    console.log('[ChatStore] Refreshing data:', target)

    try {
      if (target === 'tasks' || target === 'all') {
        const taskStore = useTaskStore()
        await taskStore.fetchTasks()
      }

      if (target === 'notes' || target === 'all') {
        const noteStore = useNoteStore()
        await noteStore.fetchNotes()
      }

      if (target === 'projects' || target === 'all') {
        const projectStore = useProjectStore()
        await projectStore.fetchProjects()
      }
    } catch (error) {
      console.error('[ChatStore] Failed to refresh data:', error)
    }
  }

  // ============================================================================
  // Return Store
  // ============================================================================

  return {
    // State - Messages
    messages,
    isStreaming,
    streamingErrorMessage,

    // State - Sessions
    currentSessionId,
    sessions,
    isSessionsLoading,

    // State - UI
    chatInputRef,
    isChatPanelVisible,
    currentTaskId,

    // Computed
    hasMessages,
    lastMessage,
    canSendMessage,
    currentSessionName,

    // Actions - Messages
    addMessage,
    updateLastMessageContent,
    appendToLastMessage,
    updateToolCall,
    addReasoningStep,
    setReferences,
    setLastMessageError,
    clearMessages,

    // Actions - Sessions
    setCurrentSessionId,
    upsertSession,
    removeSession,
    setSessions,
    setSessionsLoading,

    // Actions - UI
    setStreaming,
    setStreamingError,
    toggleChatPanel,
    showChatPanel,
    hideChatPanel,
    setCurrentTaskId,
    openChatWithTask,
    focusChatInput,

    // Actions - Stream Processing
    processStreamChunk,
    sendMessage,
    closeWebSocket,

    // Actions - UI Commands (Dynamic Skills)
    handleUICommand,
    refreshData
  }
})
