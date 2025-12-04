/**
 * Note Store - Pinia state management for notes
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Note, NoteCreate, RelatedNote, Tag, SearchHistory, Backlink, PaginatedNotes } from '@/types'
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

  // Iteration 1: Core enhancements

  async function togglePin(noteId: number, pinned: boolean): Promise<Note> {
    try {
      const response = await apiClient.put(`/notes/${noteId}/pin`, null, {
        params: { pinned }
      })
      const index = notes.value.findIndex(n => n.id === noteId)
      if (index !== -1) {
        notes.value[index] = response.data
      }
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to toggle pin'
      throw e
    }
  }

  async function toggleFavorite(noteId: number, favorited: boolean): Promise<Note> {
    try {
      const response = await apiClient.put(`/notes/${noteId}/favorite`, null, {
        params: { favorited }
      })
      const index = notes.value.findIndex(n => n.id === noteId)
      if (index !== -1) {
        notes.value[index] = response.data
      }
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to toggle favorite'
      throw e
    }
  }

  async function fetchSearchHistory(limit = 10): Promise<SearchHistory[]> {
    try {
      const response = await apiClient.get('/notes/search/history', {
        params: { limit }
      })
      return response.data
    } catch (e: any) {
      console.error('Failed to fetch search history:', e)
      return []
    }
  }

  // ============================================
  // Text Search
  // ============================================

  async function searchNotesText(query: string, limit = 20): Promise<Note[]> {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.get('/notes/search/text', {
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

  // ============================================
  // Paginated Fetch
  // ============================================

  async function fetchNotesPaginated(page = 1, size = 20): Promise<PaginatedNotes> {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.get('/notes/paginated', {
        params: { page, size }
      })
      notes.value = response.data.items
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to fetch notes'
      throw e
    } finally {
      loading.value = false
    }
  }

  // ============================================
  // Batch Operations
  // ============================================

  async function batchPin(noteIds: number[], pinned: boolean): Promise<Note[]> {
    loading.value = true
    try {
      const response = await apiClient.post('/notes/batch/pin', {
        note_ids: noteIds,
        pinned
      })
      // Update local state
      for (const updatedNote of response.data) {
        const index = notes.value.findIndex(n => n.id === updatedNote.id)
        if (index !== -1) {
          notes.value[index] = updatedNote
        }
      }
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to batch pin notes'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function batchFavorite(noteIds: number[], favorited: boolean): Promise<Note[]> {
    loading.value = true
    try {
      const response = await apiClient.post('/notes/batch/favorite', {
        note_ids: noteIds,
        pinned: favorited  // API uses 'pinned' field
      })
      // Update local state
      for (const updatedNote of response.data) {
        const index = notes.value.findIndex(n => n.id === updatedNote.id)
        if (index !== -1) {
          notes.value[index] = updatedNote
        }
      }
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to batch favorite notes'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function batchDelete(noteIds: number[]): Promise<{ deleted: number; total: number }> {
    loading.value = true
    try {
      const response = await apiClient.post('/notes/batch/delete', {
        note_ids: noteIds
      })
      // Remove deleted notes from local state
      notes.value = notes.value.filter(n => !noteIds.includes(n.id))
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to batch delete notes'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function batchTag(noteIds: number[], tagNames: string[], mode: 'add' | 'replace' = 'add'): Promise<Note[]> {
    loading.value = true
    try {
      const response = await apiClient.post('/notes/batch/tag', {
        note_ids: noteIds,
        tag_names: tagNames,
        mode
      })
      // Update local state
      for (const updatedNote of response.data) {
        const index = notes.value.findIndex(n => n.id === updatedNote.id)
        if (index !== -1) {
          notes.value[index] = updatedNote
        }
      }
      await fetchTags()  // Refresh tags list
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to batch tag notes'
      throw e
    } finally {
      loading.value = false
    }
  }

  // ============================================
  // Iteration 3: Links
  // ============================================

  async function fetchBacklinks(noteId: number): Promise<Backlink[]> {
    try {
      const response = await apiClient.get(`/links/note/${noteId}/backlinks`)
      return response.data
    } catch (e: any) {
      console.error('Failed to fetch backlinks:', e)
      return []
    }
  }

  async function createLink(sourceNoteId: number, targetNoteId: number, linkType = 'wiki'): Promise<any> {
    try {
      const response = await apiClient.post('/links/', {
        source_note_id: sourceNoteId,
        target_note_id: targetNoteId,
        link_type: linkType
      })
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to create link'
      throw e
    }
  }

  async function syncNoteLinks(noteId: number): Promise<void> {
    try {
      await apiClient.post(`/links/note/${noteId}/sync`)
    } catch (e: any) {
      console.error('Failed to sync note links:', e)
      throw e
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
    fetchNotesPaginated,
    fetchTags,
    createNote,
    updateNote,
    deleteNote,
    searchNotesSemantic,
    searchNotesText,
    togglePin,
    toggleFavorite,
    fetchSearchHistory,

    // Batch Operations
    batchPin,
    batchFavorite,
    batchDelete,
    batchTag,

    // Links
    fetchBacklinks,
    createLink,
    syncNoteLinks
  }
})
