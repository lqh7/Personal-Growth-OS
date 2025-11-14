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
}

export interface NoteCreate {
  title: string
  content: string
  source_url?: string
  project_id?: number
  tag_names?: string[]
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
