/**
 * Chat API Client
 *
 * Provides API functions for chat/agent interactions:
 * 1. List available agents
 * 2. Run agent (streaming)
 * 3. Session management (list, get, delete)
 * 4. Health check
 */

import apiClient from './client'
import type {
  SessionList,
  SessionHistoryResponse,
  ChatStreamRequest
} from '@/types/chat'

/**
 * Agent metadata
 */
export interface AgentInfo {
  id: string
  name: string
  description: string
  capabilities?: string[]
}

/**
 * Agents list response
 */
export interface AgentsListResponse {
  agents: AgentInfo[]
}

/**
 * Health check response
 */
export interface HealthCheckResponse {
  status: string
  service: string
  agents: string[]
  timestamp: number
}

// ============================================================================
// Agent Operations
// ============================================================================

/**
 * List available agents
 */
export async function listAgents(): Promise<AgentsListResponse> {
  const response = await apiClient.get<AgentsListResponse>('/chat/agents')
  return response.data
}

/**
 * Run agent (non-streaming mode)
 *
 * Note: For streaming, use useChatStream composable instead.
 *
 * @param agentId - Agent identifier
 * @param request - Chat request payload
 */
export async function runAgent(
  agentId: string,
  request: ChatStreamRequest
): Promise<any> {
  const formData = new URLSearchParams()
  formData.append('message', request.message)
  formData.append('stream', 'False') // Non-streaming

  if (request.session_id) {
    formData.append('session_id', request.session_id)
  }

  if (request.task_id) {
    const dependencies = JSON.stringify({ task_id: request.task_id })
    formData.append('dependencies', dependencies)
  }

  const response = await apiClient.post(
    `/chat/agents/${agentId}/runs`,
    formData.toString(),
    {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    }
  )

  return response.data
}

// ============================================================================
// Session Management
// ============================================================================

/**
 * Get session history list
 *
 * @param agentId - Optional filter by agent ID
 * @param limit - Maximum number of sessions to return
 * @param offset - Number of sessions to skip
 */
export async function getSessions(
  agentId?: string,
  limit = 20,
  offset = 0
): Promise<SessionList> {
  const params: Record<string, any> = { limit, offset }

  if (agentId) {
    params.agent_id = agentId
  }

  const response = await apiClient.get<SessionList>('/chat/sessions', { params })
  return response.data
}

/**
 * Get message history for a specific session
 *
 * @param sessionId - Session identifier
 */
export async function getSessionHistory(
  sessionId: string
): Promise<SessionHistoryResponse> {
  const response = await apiClient.get<SessionHistoryResponse>(
    `/chat/sessions/${sessionId}`
  )
  return response.data
}

/**
 * Delete a session and its message history
 *
 * @param sessionId - Session identifier
 */
export async function deleteSession(sessionId: string): Promise<void> {
  await apiClient.delete(`/chat/sessions/${sessionId}`)
}

// ============================================================================
// Health Check
// ============================================================================

/**
 * Check agent service health
 */
export async function checkHealth(): Promise<HealthCheckResponse> {
  const response = await apiClient.get<HealthCheckResponse>('/chat/health')
  return response.data
}

// ============================================================================
// Export all functions
// ============================================================================

export default {
  listAgents,
  runAgent,
  getSessions,
  getSessionHistory,
  deleteSession,
  checkHealth,
}
