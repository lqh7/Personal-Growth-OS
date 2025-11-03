/**
 * Task Store - Pinia state management for tasks
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Task, TaskCreate, TaskIgnitionRequest, TaskIgnitionResponse } from '@/types'
import apiClient from '@/api/client'

export const useTaskStore = defineStore('task', () => {
  // State
  const tasks = ref<Task[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const pendingTasks = computed(() =>
    tasks.value.filter(t => t.status === 'pending')
  )

  const inProgressTasks = computed(() =>
    tasks.value.filter(t => t.status === 'in_progress')
  )

  const completedTasks = computed(() =>
    tasks.value.filter(t => t.status === 'completed')
  )

  const finishedTasks = computed(() =>
    tasks.value.filter(t => t.status === 'completed' || t.status === 'overdue')
  )

  // Actions
  async function fetchTasks(includeSnoozed = false) {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.get('/tasks/', {
        params: { include_snoozed: includeSnoozed }
      })
      tasks.value = response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch tasks'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createTask(taskData: TaskCreate): Promise<Task> {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.post('/tasks/', taskData)
      tasks.value.push(response.data)
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to create task'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateTask(taskId: number, updates: Partial<TaskCreate>): Promise<Task> {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.put(`/tasks/${taskId}`, updates)
      const index = tasks.value.findIndex(t => t.id === taskId)
      if (index !== -1) {
        tasks.value[index] = response.data
      }
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to update task'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteTask(taskId: number) {
    loading.value = true
    error.value = null

    try {
      await apiClient.delete(`/tasks/${taskId}`)
      tasks.value = tasks.value.filter(t => t.id !== taskId)
    } catch (e: any) {
      error.value = e.message || 'Failed to delete task'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function snoozeTask(taskId: number, snoozeUntil: string): Promise<Task> {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.post(`/tasks/${taskId}/snooze`, null, {
        params: { snooze_until: snoozeUntil }
      })
      const index = tasks.value.findIndex(t => t.id === taskId)
      if (index !== -1) {
        tasks.value[index] = response.data
      }
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to snooze task'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function igniteTask(request: TaskIgnitionRequest): Promise<TaskIgnitionResponse> {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.post('/tasks/ignite', request)
      // Add all tasks to the store
      const result = response.data as TaskIgnitionResponse
      tasks.value.push(result.main_task)
      tasks.value.push(...result.subtasks)
      return result
    } catch (e: any) {
      error.value = e.message || 'Failed to ignite task'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    tasks,
    loading,
    error,

    // Computed
    pendingTasks,
    inProgressTasks,
    completedTasks,
    finishedTasks,

    // Actions
    fetchTasks,
    createTask,
    updateTask,
    deleteTask,
    snoozeTask,
    igniteTask
  }
})
