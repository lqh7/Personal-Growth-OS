/**
 * Task Adapter - Convert between API format and View format
 */
import { useProjectStore } from '@/stores/projectStore'
import type { Task } from '@/types'

export interface ViewTask {
  id: string
  title: string
  description?: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
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
      dueDate: apiTask.due_date ? new Date(apiTask.due_date) : undefined,
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
   * Convert View Task to API format for create/update
   */
  function toApiTask(viewTask: Partial<ViewTask>) {
    const apiTask: any = {}

    if (viewTask.title !== undefined) apiTask.title = viewTask.title
    if (viewTask.description !== undefined) apiTask.description = viewTask.description
    if (viewTask.status !== undefined) apiTask.status = viewTask.status
    if (viewTask.priority !== undefined) apiTask.priority = viewTask.priority

    if (viewTask.startTime) {
      apiTask.start_time = viewTask.startTime.toISOString()
    }

    if (viewTask.endTime) {
      apiTask.end_time = viewTask.endTime.toISOString()
    }

    if (viewTask.dueDate) {
      apiTask.due_date = viewTask.dueDate.toISOString()
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
