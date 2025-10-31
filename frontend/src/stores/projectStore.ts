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

  async function createProject(data: {
    name: string
    description?: string
    color: string
  }) {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.post('/projects/', data)
      projects.value.push(response.data)
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to create project'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateProject(id: number, data: {
    name?: string
    description?: string
    color?: string
  }) {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.put(`/projects/${id}`, data)
      const index = projects.value.findIndex(p => p.id === id)
      if (index !== -1) {
        projects.value[index] = response.data
      }
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to update project'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteProject(id: number) {
    loading.value = true
    error.value = null

    try {
      await apiClient.delete(`/projects/${id}`)
      projects.value = projects.value.filter(p => p.id !== id)
    } catch (e: any) {
      error.value = e.message || 'Failed to delete project'
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
    createProject,
    updateProject,
    deleteProject,
    getProjectById
  }
})
