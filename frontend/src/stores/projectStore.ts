/**
 * Project Store - Pinia state management for projects
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Project } from '@/types'
import apiClient from '@/api/client'

export const useProjectStore = defineStore('project', () => {
  // State
  const projects = ref<Project[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function fetchProjects() {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.get('/projects/')
      projects.value = response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch projects'
      throw e
    } finally {
      loading.value = false
    }
  }

  function getProjectById(id: number) {
    return projects.value.find(p => p.id === id)
  }

  return {
    // State
    projects,
    loading,
    error,

    // Actions
    fetchProjects,
    getProjectById
  }
})
