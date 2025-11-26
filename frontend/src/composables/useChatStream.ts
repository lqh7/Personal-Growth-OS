/**
 * useChatStream - Streaming Response Handler Composable
 *
 * Handles Server-Sent Events (SSE) streaming from AgentOS API.
 * Integrates with chatStore for state management.
 *
 * Key features:
 * 1. Fetch API with ReadableStream support
 * 2. Incremental JSON parsing using useStreamParser
 * 3. Real-time state updates via chatStore
 * 4. Error handling and retry logic
 */

import { ref } from 'vue'
import type { RunResponseContent, ChatStreamRequest } from '@/types/chat'
import { useStreamParser } from './useStreamParser'
import { useChatStore } from '@/stores/chatStore'

/**
 * Stream configuration options
 */
export interface StreamOptions {
  /**
   * Base URL for API (default: /api/chat)
   */
  baseUrl?: string

  /**
   * Timeout in milliseconds (default: 300000 = 5 minutes)
   */
  timeout?: number

  /**
   * Abort signal for cancellation
   */
  signal?: AbortSignal
}

/**
 * Composable for handling chat streaming
 */
export function useChatStream() {
  const chatStore = useChatStore()
  const { parseStreamChunk } = useStreamParser()

  const isStreaming = ref(false)
  const streamError = ref<string | null>(null)

  /**
   * Stream chat response from AgentOS API
   *
   * @param agentId - Agent identifier (e.g., "task-igniter")
   * @param request - Chat stream request payload
   * @param options - Stream configuration options
   */
  async function streamChat(
    agentId: string,
    request: ChatStreamRequest,
    options: StreamOptions = {}
  ): Promise<void> {
    const {
      baseUrl = '/api/chat',
      timeout = 300000, // 5 minutes
      signal
    } = options

    // Reset error state
    streamError.value = null
    isStreaming.value = true
    chatStore.setStreaming(true)

    // Create abort controller for timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)

    // Combine signals if provided
    const finalSignal = signal
      ? createCombinedSignal(signal, controller.signal)
      : controller.signal

    try {
      // Build form data (AgentOS uses application/x-www-form-urlencoded)
      const formData = new URLSearchParams()
      formData.append('message', request.message)
      formData.append('stream', request.stream !== false ? 'True' : 'False')

      if (request.session_id) {
        formData.append('session_id', request.session_id)
      }

      if (request.task_id) {
        // Pass task_id via dependencies JSON
        const dependencies = JSON.stringify({ task_id: request.task_id })
        formData.append('dependencies', dependencies)
      }

      // Make streaming request
      const response = await fetch(`${baseUrl}/agents/${agentId}/runs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
        signal: finalSignal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      // Get readable stream
      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Response body is not readable')
      }

      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      // Read stream chunks
      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          break
        }

        // Decode chunk and append to buffer
        const text = decoder.decode(value, { stream: true })
        buffer += text

        // Parse complete JSON objects from buffer
        buffer = parseStreamChunk(buffer, (chunk: RunResponseContent) => {
          // Process chunk via chatStore
          chatStore.processStreamChunk(chunk)
        })
      }

      // Process any remaining buffer
      if (buffer.trim()) {
        console.warn('[useChatStream] Unparsed buffer remaining:', buffer)
      }

    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'

      console.error('[useChatStream] Stream error:', errorMessage)
      streamError.value = errorMessage

      // Update store with error
      chatStore.setStreamingError(errorMessage)
      chatStore.setLastMessageError(true)

    } finally {
      clearTimeout(timeoutId)
      isStreaming.value = false
      chatStore.setStreaming(false)
    }
  }

  /**
   * Cancel ongoing stream (if using manual AbortController)
   */
  function cancelStream(controller: AbortController) {
    controller.abort()
    chatStore.setStreaming(false)
    isStreaming.value = false
  }

  return {
    streamChat,
    cancelStream,
    isStreaming,
    streamError,
  }
}

/**
 * Helper: Combine multiple AbortSignals
 */
function createCombinedSignal(...signals: AbortSignal[]): AbortSignal {
  const controller = new AbortController()

  for (const signal of signals) {
    if (signal.aborted) {
      controller.abort()
      return controller.signal
    }

    signal.addEventListener('abort', () => controller.abort(), { once: true })
  }

  return controller.signal
}
