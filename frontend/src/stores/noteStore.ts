/**
 * Note Store - Pinia state management for notes
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Note, NoteCreate, RelatedNote, Tag } from '@/types'
import apiClient from '@/api/client'

export const useNoteStore = defineStore('note', () => {
  // State
  const notes = ref<Note[]>([])
  const tags = ref<Tag[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Actions
  async function fetchNotes(projectId?: number) {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.get('/notes/', {
        params: { project_id: projectId }
      })
      notes.value = response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch notes'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchTags() {
    try {
      const response = await apiClient.get('/notes/tags/')
      tags.value = response.data
    } catch (e: any) {
      console.error('Failed to fetch tags:', e)
    }
  }

  async function createNote(noteData: NoteCreate): Promise<Note> {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.post('/notes/', noteData)
      notes.value.unshift(response.data)
      await fetchTags() // Refresh tags
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to create note'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateNote(noteId: number, updates: Partial<NoteCreate>): Promise<Note> {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.put(`/notes/${noteId}`, updates)
      const index = notes.value.findIndex(n => n.id === noteId)
      if (index !== -1) {
        notes.value[index] = response.data
      }
      await fetchTags() // Refresh tags
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to update note'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteNote(noteId: number) {
    loading.value = true
    error.value = null

    try {
      await apiClient.delete(`/notes/${noteId}`)
      notes.value = notes.value.filter(n => n.id !== noteId)
    } catch (e: any) {
      error.value = e.message || 'Failed to delete note'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function searchNotesSemantic(query: string, limit = 5): Promise<RelatedNote[]> {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.get('/notes/search/semantic', {
        params: { query, limit }
      })
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to search notes'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    notes,
    tags,
    loading,
    error,

    // Actions
    fetchNotes,
    fetchTags,
    createNote,
    updateNote,
    deleteNote,
    searchNotesSemantic
  }
})
