/**
 * TypeScript type definitions for Personal Growth OS
 */

export interface Task {
  id: number
  title: string
  description?: string
  status: 'pending' | 'in_progress' | 'completed' | 'overdue'
  priority: number
  due_date?: string
  start_time?: string
  end_time?: string
  snooze_until?: string
  parent_task_id?: number
  project_id?: number
  created_at: string
  updated_at: string
  completed_at?: string
  subtasks?: Task[]
}

export interface TaskCreate {
  title: string
  description?: string
  status?: string
  priority?: number
  due_date?: string
  start_time?: string
  end_time?: string
  snooze_until?: string
  parent_task_id?: number
  project_id?: number
}

export interface TaskIgnitionRequest {
  task_description: string
  project_id?: number
}

export interface TaskIgnitionResponse {
  main_task: Task
  subtasks: Task[]
  minimum_viable_task: Task
  related_notes: Array<{
    note_id: number
    title: string
    similarity_score: number
  }>
}

export interface Note {
  id: number
  title: string
  content: string
  source_url?: string
  project_id?: number
  created_at: string
  updated_at: string
  tags: Tag[]
  project?: Project

  // Iteration 1: Core enhancements
  cover_image?: string
  emoji?: string
  is_pinned: boolean
  is_favorited: boolean
  view_count: number
  sort_order: number

  // Iteration 2: Attachments + Templates
  template_id?: number
  attachments: Attachment[]
  template?: Template

  // Iteration 3: Wiki Links + Folders
  parent_note_id?: number
}

export interface NoteCreate {
  title: string
  content: string
  source_url?: string
  project_id?: number
  tag_names?: string[]
  template_id?: number
}

export interface Tag {
  id: number
  name: string
  color?: string
  created_at: string
}

export interface RelatedNote {
  note: Note
  similarity_score: number
}

export interface Project {
  id: number
  name: string
  description?: string
  color?: string
  is_system?: boolean
  created_at: string
  updated_at: string
}

export interface SearchHistory {
  id: number
  query_text: string
  result_count: number
  timestamp: string
}

// Iteration 2: Attachments + Templates

export interface Attachment {
  id: number
  note_id: number
  filename: string
  filepath: string
  filesize: number
  mimetype: string
  created_at: string
}

export interface Template {
  id: number
  name: string
  description?: string
  content_template: string
  icon?: string
  category?: string
  created_at: string
  updated_at: string
}

export interface TemplateCreate {
  name: string
  description?: string
  content_template: string
  icon?: string
  category?: string
}

export interface TemplateRenderResponse {
  content: string
  template_name: string
  suggested_title: string
}

// Iteration 3: Wiki Links + Folders

export interface NoteLink {
  id: number
  source_note_id: number
  target_note_id: number
  link_type: string
  created_at: string
}

export interface Backlink {
  note_id: number
  note_title: string
  link_type: string
  created_at: string
}
