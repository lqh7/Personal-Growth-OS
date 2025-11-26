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
  ReasoningStep
} from '@/types/chat'
import { RunEvent } from '@/types/chat'

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
        // Update content (full replacement)
        if (typeof chunk.content === 'string') {
          updateLastMessageContent(chunk.content)
        }
        break

      case RunEvent.ToolCallStarted:
      case RunEvent.ToolCallCompleted:
        // Update tool call
        if (chunk.tool) {
          updateToolCall(chunk.tool)
        }
        // Handle multiple tools
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

      default:
        // Ignore other events (RunOutput, MemoryUpdate, etc.)
        console.debug('[ChatStore] Unhandled event:', chunk.event)
        break
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
    processStreamChunk
  }
})
