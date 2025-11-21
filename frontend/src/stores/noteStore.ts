/**
 * Note Store - Pinia state management for notes
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Note, NoteCreate, RelatedNote, Tag, SearchHistory, Attachment, Backlink } from '@/types'
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

  // Iteration 2: Attachments

  async function fetchAttachments(noteId: number): Promise<Attachment[]> {
    try {
      const response = await apiClient.get(`/attachments/note/${noteId}`)
      return response.data
    } catch (e: any) {
      console.error('Failed to fetch attachments:', e)
      return []
    }
  }

  async function uploadAttachment(noteId: number, file: File): Promise<Attachment> {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('note_id', String(noteId))

    try {
      const response = await apiClient.post('/attachments/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        params: { note_id: noteId }
      })
      return response.data
    } catch (e: any) {
      error.value = e.message || 'Failed to upload attachment'
      throw e
    }
  }

  async function downloadAttachment(attachmentId: number): Promise<void> {
    try {
      const response = await apiClient.get(`/attachments/${attachmentId}/download`, {
        responseType: 'blob'
      })
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', response.headers['content-disposition']?.split('filename=')[1] || 'download')
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (e: any) {
      error.value = e.message || 'Failed to download attachment'
      throw e
    }
  }

  async function deleteAttachment(attachmentId: number): Promise<void> {
    try {
      await apiClient.delete(`/attachments/${attachmentId}`)
    } catch (e: any) {
      error.value = e.message || 'Failed to delete attachment'
      throw e
    }
  }

  // Iteration 3: Links

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
    fetchTags,
    createNote,
    updateNote,
    deleteNote,
    searchNotesSemantic,
    togglePin,
    toggleFavorite,
    fetchSearchHistory,

    // Attachments
    fetchAttachments,
    uploadAttachment,
    downloadAttachment,
    deleteAttachment,

    // Links
    fetchBacklinks,
    createLink,
    syncNoteLinks
  }
})
