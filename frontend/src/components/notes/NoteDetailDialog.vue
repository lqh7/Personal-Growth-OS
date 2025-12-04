<template>
  <el-dialog
    v-model="visible"
    :show-close="false"
    :close-on-click-modal="false"
    width="920px"
    class="note-detail-dialog"
    @close="handleClose"
  >
    <div class="note-detail-container">
      <!-- Header -->
      <header class="note-header">
        <div class="header-content">
          <div class="note-meta-line">
            <div class="template-badge" v-if="note.template">
              <span class="badge-icon">📋</span>
              <span class="badge-text">{{ note.template }}</span>
            </div>
            <div class="date-info">
              <time :datetime="note.created_at">
                {{ formatDate(note.created_at) }}
              </time>
            </div>
          </div>

          <h1 class="note-title" :class="{ editing: isEditing }">
            <span v-if="!isEditing" class="title-text">{{ note.title }}</span>
            <input
              v-else
              v-model="editForm.title"
              type="text"
              class="title-input"
              placeholder="无标题笔记"
              autofocus
            />
          </h1>

          <div class="note-tags" v-if="note.tags && note.tags.length > 0">
            <div
              v-for="tag in note.tags"
              :key="tag.id"
              class="tag-chip"
              :style="{ '--tag-color': tag.color || '#3b82f6' }"
            >
              <span class="tag-dot"></span>
              {{ tag.name }}
            </div>
          </div>
        </div>

        <button class="close-btn" @click="handleClose" title="关闭">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </header>

      <!-- Content Area -->
      <main class="note-content">
        <div v-if="!isEditing" class="content-view" @click="handleContentClick">
          <MdPreview
            :modelValue="processedContent"
            :theme="'light'"
            class="markdown-preview"
          />

          <!-- Source URL if exists -->
          <div v-if="note.source_url" class="source-reference">
            <div class="reference-label">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
              来源
            </div>
            <a :href="note.source_url" target="_blank" rel="noopener" class="source-link">
              {{ formatUrl(note.source_url) }}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
            </a>
          </div>

          <!-- Backlinks Section -->
          <div class="backlinks-section">
            <NoteBacklinks
              :note-id="note.id"
              @navigate="handleBacklinkNavigate"
            />
          </div>
        </div>

        <div v-else class="content-edit">
          <MdEditor
            v-model="editForm.content"
            :toolbars="editorToolbars"
            :theme="'light'"
            class="markdown-editor"
            placeholder="开始写作..."
          />

          <div class="edit-meta">
            <div class="meta-field">
              <label class="meta-label">来源链接</label>
              <input
                v-model="editForm.source_url"
                type="url"
                class="meta-input"
                placeholder="https://..."
              />
            </div>
          </div>
        </div>
      </main>

      <!-- Footer Actions -->
      <footer class="note-footer">
        <div class="footer-left">
          <div class="stat-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            <span>更新于 {{ formatRelativeTime(note.updated_at) }}</span>
          </div>
          <div class="stat-item" v-if="note.view_count">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            <span>{{ note.view_count }} 次查看</span>
          </div>
        </div>

        <div class="footer-actions">
          <button
            v-if="!isEditing"
            @click="startEdit"
            class="action-btn primary"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            编辑
          </button>

          <template v-else>
            <button @click="cancelEdit" class="action-btn">
              取消
            </button>
            <button @click="saveEdit" class="action-btn primary">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              保存
            </button>
          </template>

          <button @click="confirmDelete" class="action-btn danger">
            删除
          </button>
        </div>
      </footer>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Note } from '@/types'
import { MdEditor, MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import NoteBacklinks from './NoteBacklinks.vue'
import { useNoteStore } from '@/stores/noteStore'

interface Props {
  modelValue: boolean
  note: Note
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'update', data: Partial<Note>): void
  (e: 'delete'): void
  (e: 'navigate', noteId: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const noteStore = useNoteStore()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isEditing = ref(false)
const editForm = ref({
  title: '',
  content: '',
  source_url: ''
})

const editorToolbars = [
  'bold', 'italic', 'strikeThrough', '-',
  'title', 'quote', 'unorderedList', 'orderedList', '-',
  'code', 'codeRow', 'link', 'image', '-',
  'table', 'revoke', 'next', 'save'
]

// Process wiki links [[Title]] in content
const processedContent = computed(() => {
  if (!props.note.content) return ''

  // Replace [[Title]] with clickable wiki links
  // The link will be styled via CSS and handled via click event
  return props.note.content.replace(
    /\[\[([^\]]+)\]\]/g,
    (match, title) => {
      // Find the note by title
      const linkedNote = noteStore.notes.find(n => n.title === title)
      if (linkedNote) {
        return `<span class="wiki-link" data-note-id="${linkedNote.id}" data-note-title="${title}">${title}</span>`
      }
      // If note doesn't exist, show as broken link
      return `<span class="wiki-link broken" data-note-title="${title}">${title}</span>`
    }
  )
})

// Handle wiki link clicks
function handleContentClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (target.classList.contains('wiki-link')) {
    const noteId = target.dataset.noteId
    const noteTitle = target.dataset.noteTitle

    if (noteId) {
      handleBacklinkNavigate(parseInt(noteId))
    } else if (noteTitle) {
      ElMessage.info(`笔记 "${noteTitle}" 不存在，点击可创建`)
      // Could implement auto-create feature here
    }
  }
}

watch(() => props.note, (newNote) => {
  if (newNote) {
    editForm.value = {
      title: newNote.title,
      content: newNote.content,
      source_url: newNote.source_url || ''
    }
  }
}, { immediate: true })

function startEdit() {
  isEditing.value = true
  editForm.value = {
    title: props.note.title,
    content: props.note.content,
    source_url: props.note.source_url || ''
  }
}

function cancelEdit() {
  isEditing.value = false
}

async function saveEdit() {
  if (!editForm.value.title.trim()) {
    ElMessage.warning('标题不能为空')
    return
  }

  emit('update', {
    title: editForm.value.title,
    content: editForm.value.content,
    source_url: editForm.value.source_url || undefined
  })

  isEditing.value = false
  ElMessage.success('保存成功')
}

async function confirmDelete() {
  try {
    await ElMessageBox.confirm(
      '确定要删除这条笔记吗？此操作不可恢复。',
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    emit('delete')
  } catch {
    // User cancelled
  }
}

function handleClose() {
  if (isEditing.value) {
    ElMessageBox.confirm('有未保存的更改，确定要关闭吗？', '提示', {
      confirmButtonText: '关闭',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      visible.value = false
      isEditing.value = false
    }).catch(() => {})
  } else {
    visible.value = false
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays < 7) return `${diffDays} 天前`

  return formatDate(dateString)
}

function formatUrl(url: string): string {
  try {
    const urlObj = new URL(url)
    return urlObj.hostname + urlObj.pathname
  } catch {
    return url
  }
}

function handleBacklinkNavigate(noteId: number) {
  visible.value = false
  emit('navigate', noteId)
}
</script>

<style scoped lang="scss">
// Import custom fonts
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: dialogEnter 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

:deep(.el-dialog__header) {
  display: none;
}

:deep(.el-dialog__body) {
  padding: 0;
}

@keyframes dialogEnter {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.note-detail-container {
  display: flex;
  flex-direction: column;
  height: 85vh;
  max-height: 900px;
  background: linear-gradient(to bottom, #fafaf9 0%, #ffffff 100%);
}

.note-header {
  position: relative;
  padding: 48px 56px 32px;
  border-bottom: 1px solid #e7e5e4;
  background: white;

  .header-content {
    max-width: 720px;
  }

  .note-meta-line {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
  }

  .template-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border-radius: 20px;
    font-size: 13px;
    font-weight: 500;
    color: #92400e;
    box-shadow: 0 1px 3px rgba(251, 191, 36, 0.1);

    .badge-icon {
      font-size: 14px;
    }
  }

  .date-info {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: #78716c;
    letter-spacing: -0.01em;
  }

  .note-title {
    font-family: 'Crimson Pro', Georgia, serif;
    font-size: 42px;
    font-weight: 700;
    line-height: 1.2;
    color: #1c1917;
    margin: 0 0 20px;
    letter-spacing: -0.02em;
    transition: all 0.2s ease;

    &.editing {
      margin-bottom: 24px;
    }

    .title-text {
      display: block;
      background: linear-gradient(135deg, #1c1917 0%, #44403c 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .title-input {
      width: 100%;
      border: none;
      outline: none;
      background: transparent;
      font: inherit;
      color: inherit;
      padding: 8px 0;
      border-bottom: 2px solid #d6d3d1;
      transition: border-color 0.2s ease;

      &:focus {
        border-bottom-color: #0ea5e9;
      }

      &::placeholder {
        color: #a8a29e;
      }
    }
  }

  .note-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .tag-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: rgba(var(--tag-color-rgb, 59, 130, 246), 0.08);
    border: 1px solid rgba(var(--tag-color-rgb, 59, 130, 246), 0.2);
    border-radius: 12px;
    font-size: 13px;
    font-weight: 500;
    color: var(--tag-color, #3b82f6);
    transition: all 0.2s ease;

    &:hover {
      background: rgba(var(--tag-color-rgb, 59, 130, 246), 0.12);
      transform: translateY(-1px);
    }

    .tag-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: currentColor;
    }
  }

  .close-btn {
    position: absolute;
    top: 20px;
    right: 20px;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    background: transparent;
    color: #78716c;
    cursor: pointer;
    border-radius: 8px;
    transition: all 0.2s ease;

    &:hover {
      background: #f5f5f4;
      color: #1c1917;
    }

    &:active {
      transform: scale(0.95);
    }
  }
}

.note-content {
  flex: 1;
  overflow-y: auto;
  padding: 40px 56px;

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: #d6d3d1;
    border-radius: 4px;

    &:hover {
      background: #a8a29e;
    }
  }
}

.content-view {
  max-width: 720px;

  :deep(.markdown-preview) {
    font-family: 'Crimson Pro', Georgia, serif;
    font-size: 18px;
    line-height: 1.8;
    color: #292524;

    h1, h2, h3, h4, h5, h6 {
      font-weight: 700;
      letter-spacing: -0.02em;
      margin-top: 2em;
      margin-bottom: 0.75em;
      color: #1c1917;
    }

    h1 { font-size: 2.2em; }
    h2 { font-size: 1.8em; }
    h3 { font-size: 1.5em; }

    p {
      margin-bottom: 1.5em;
    }

    a {
      color: #0ea5e9;
      text-decoration: underline;
      text-decoration-thickness: 1px;
      text-underline-offset: 3px;
      transition: all 0.2s ease;

      &:hover {
        color: #0284c7;
        text-decoration-thickness: 2px;
      }
    }

    code {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.9em;
      background: #fafaf9;
      padding: 2px 6px;
      border-radius: 4px;
      border: 1px solid #e7e5e4;
    }

    pre {
      background: #1c1917;
      padding: 20px;
      border-radius: 12px;
      overflow-x: auto;

      code {
        background: transparent;
        border: none;
        color: #fafaf9;
      }
    }

    blockquote {
      border-left: 4px solid #0ea5e9;
      padding-left: 20px;
      margin: 1.5em 0;
      color: #57534e;
      font-style: italic;
    }

    // Wiki link styles
    .wiki-link {
      color: #0ea5e9;
      background: rgba(14, 165, 233, 0.1);
      padding: 2px 6px;
      border-radius: 4px;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.2s ease;
      font-weight: 500;

      &:hover {
        background: rgba(14, 165, 233, 0.2);
        color: #0284c7;
      }

      &.broken {
        color: #dc2626;
        background: rgba(220, 38, 38, 0.1);
        text-decoration: line-through;

        &:hover {
          background: rgba(220, 38, 38, 0.2);
          color: #991b1b;
        }
      }
    }

    ul, ol {
      padding-left: 1.5em;
      margin-bottom: 1.5em;

      li {
        margin-bottom: 0.5em;
      }
    }
  }

  .source-reference {
    margin-top: 40px;
    padding: 20px;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border: 1px solid #bae6fd;
    border-radius: 12px;

    .reference-label {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      font-weight: 600;
      color: #075985;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.05em;

      svg {
        color: #0ea5e9;
      }
    }

    .source-link {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 14px;
      color: #0c4a6e;
      text-decoration: none;
      transition: all 0.2s ease;

      &:hover {
        color: #075985;
        gap: 8px;

        svg {
          transform: translateX(2px) translateY(-2px);
        }
      }

      svg {
        transition: transform 0.2s ease;
      }
    }
  }

  .backlinks-section {
    margin-top: 40px;
    padding-top: 24px;
    border-top: 1px solid #e7e5e4;
  }
}

.content-edit {
  max-width: 720px;

  :deep(.markdown-editor) {
    border: 1px solid #e7e5e4;
    border-radius: 12px;
    overflow: hidden;

    .md-editor-toolbar {
      background: #fafaf9;
      border-bottom: 1px solid #e7e5e4;
    }
  }

  .edit-meta {
    margin-top: 24px;
  }

  .meta-field {
    .meta-label {
      display: block;
      font-size: 13px;
      font-weight: 600;
      color: #57534e;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .meta-input {
      width: 100%;
      padding: 12px 16px;
      border: 1px solid #e7e5e4;
      border-radius: 8px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 14px;
      color: #292524;
      transition: all 0.2s ease;

      &:focus {
        outline: none;
        border-color: #0ea5e9;
        box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1);
      }

      &::placeholder {
        color: #a8a29e;
      }
    }
  }
}

.note-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 56px;
  border-top: 1px solid #e7e5e4;
  background: white;

  .footer-left {
    display: flex;
    align-items: center;
    gap: 20px;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: #78716c;

    svg {
      color: #a8a29e;
    }
  }

  .footer-actions {
    display: flex;
    gap: 12px;
  }

  .action-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    background: #f5f5f4;
    color: #44403c;

    &:hover {
      background: #e7e5e4;
      transform: translateY(-1px);
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    &:active {
      transform: translateY(0);
    }

    &.primary {
      background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
      color: white;

      &:hover {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
      }
    }

    &.danger {
      background: transparent;
      color: #dc2626;

      &:hover {
        background: #fee2e2;
        color: #991b1b;
      }
    }

    svg {
      flex-shrink: 0;
    }
  }
}
</style>
