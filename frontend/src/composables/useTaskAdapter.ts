/**
 * Task Adapter - Convert between API format and View format
 */
import { useProjectStore } from '@/stores/projectStore'
import type { Task } from '@/types'

export interface ViewTask {
  id: string
  title: string
  description?: string
  status: 'pending' | 'in_progress' | 'completed' | 'overdue'
  priority: number
  startTime?: Date
  endTime?: Date
  dueDate?: Date
  completed: boolean
  project?: {
    id: string
    name: string
    color: string
  }
  snoozeUntil?: Date
}

export function useTaskAdapter() {
  const projectStore = useProjectStore()

  /**
   * Convert API Task to View Task format
   */
  function toViewTask(apiTask: Task): ViewTask {
    const project = apiTask.project_id
      ? projectStore.getProjectById(apiTask.project_id)
      : undefined

    return {
      id: String(apiTask.id),
      title: apiTask.title,
      description: apiTask.description,
      status: apiTask.status,
      priority: apiTask.priority,
      startTime: apiTask.start_time ? new Date(apiTask.start_time) : undefined,
      endTime: apiTask.end_time ? new Date(apiTask.end_time) : undefined,
      // Use end_time as dueDate (截止时间就是结束时间)
      dueDate: apiTask.end_time ? new Date(apiTask.end_time) : undefined,
      completed: apiTask.status === 'completed',
      project: project ? {
        id: String(project.id),
        name: project.name,
        color: project.color || '#667eea'
      } : undefined,
      snoozeUntil: apiTask.snooze_until ? new Date(apiTask.snooze_until) : undefined
    }
  }

  /**
   * Format Date to local datetime string (preserves timezone)
   * Converts: 2025-11-03 14:00 → "2025-11-03T14:00:00"
   */
  function formatLocalDateTime(date: Date): string {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')

    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
  }

  /**
   * Convert View Task to API format for create/update
   */
  function toApiTask(viewTask: Partial<ViewTask>) {
    const apiTask: any = {}

    if (viewTask.title !== undefined) apiTask.title = viewTask.title
    if (viewTask.description !== undefined) apiTask.description = viewTask.description
    if (viewTask.status !== undefined) apiTask.status = viewTask.status
    if (viewTask.priority !== undefined) apiTask.priority = viewTask.priority

    if (viewTask.startTime) {
      apiTask.start_time = formatLocalDateTime(viewTask.startTime)
    }

    if (viewTask.endTime) {
      apiTask.end_time = formatLocalDateTime(viewTask.endTime)
    }

    if (viewTask.dueDate) {
      apiTask.due_date = formatLocalDateTime(viewTask.dueDate)
    }

    if (viewTask.project?.id) {
      apiTask.project_id = Number(viewTask.project.id)
    }

    if (viewTask.snoozeUntil) {
      apiTask.snooze_until = viewTask.snoozeUntil.toISOString()
    }

    return apiTask
  }

  /**
   * Extract time (HH:mm) from ISO date string
   */
  function extractTime(isoDate: string): string {
    const date = new Date(isoDate)
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  }

  return {
    toViewTask,
    toApiTask
  }
}
