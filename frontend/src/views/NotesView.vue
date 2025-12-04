<template>
  <div class="notes-view">
    <!-- Header with actions -->
    <div class="view-header">
      <div class="header-left">
        <h1 class="page-title">笔记管理</h1>
        <div class="header-stats">
          <span class="stat-item">共 {{ noteStore.notes.length }} 条</span>
          <span v-if="selectedTags.length > 0" class="stat-divider">·</span>
          <span v-if="selectedTags.length > 0" class="stat-item">已筛选 {{ filteredNotes.length }} 条</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          创建笔记
        </el-button>
      </div>
    </div>

    <!-- Filters Bar -->
    <div class="filters-bar">
      <div class="filters-left">
        <!-- Search with History Dropdown -->
        <el-autocomplete
          v-model="searchQuery"
          :fetch-suggestions="querySearchHistory"
          placeholder="搜索笔记标题和内容..."
          clearable
          class="filter-search"
          @keyup.enter="handleSearch"
          @clear="clearSearch"
          @select="handleHistorySelect"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
          <template #append>
            <el-button @click="handleSearch" :loading="isSearching || noteStore.loading">
              {{ isSearching ? '搜索中...' : '搜索' }}
            </el-button>
          </template>
          <template #default="{ item }">
            <div class="history-item">
              <el-icon><Clock /></el-icon>
              <span class="history-text">{{ item.value }}</span>
              <el-icon
                class="delete-icon"
                @mousedown.prevent="handleDeleteHistory(item.value)"
              >
                <CircleCloseFilled />
              </el-icon>
            </div>
          </template>
        </el-autocomplete>

        <el-select
          v-model="selectedTags"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="按标签筛选"
          clearable
          class="filter-tags"
        >
          <el-option
            v-for="tag in noteStore.tags"
            :key="tag.id"
            :label="tag.name"
            :value="tag.id"
          >
            <span class="tag-option">
              <span class="tag-color-dot" :style="{ backgroundColor: tag.color }"></span>
              {{ tag.name }}
            </span>
          </el-option>
        </el-select>

        <el-select v-model="sortBy" placeholder="排序" class="filter-sort">
          <el-option label="最新更新" value="updated_at_desc" />
          <el-option label="最早更新" value="updated_at_asc" />
          <el-option label="最新创建" value="created_at_desc" />
          <el-option label="标题 A-Z" value="title_asc" />
          <el-option label="标题 Z-A" value="title_desc" />
        </el-select>

        <!-- Quick Filters (Iteration 1) -->
        <el-button-group>
          <el-button
            :type="quickFilter === 'pinned' ? 'primary' : ''"
            @click="toggleQuickFilter('pinned')"
          >
            📌 置顶
            <el-badge v-if="pinnedCount > 0" :value="pinnedCount" class="quick-filter-badge" />
          </el-button>
          <el-button
            :type="quickFilter === 'favorited' ? 'primary' : ''"
            @click="toggleQuickFilter('favorited')"
          >
            ⭐ 收藏
            <el-badge v-if="favoritedCount > 0" :value="favoritedCount" class="quick-filter-badge" />
          </el-button>
          <el-button
            :type="quickFilter === 'recent' ? 'primary' : ''"
            @click="toggleQuickFilter('recent')"
          >
            🕒 最近
          </el-button>
        </el-button-group>
      </div>

      <div class="filters-right">
        <el-button-group>
          <el-tooltip content="网格视图">
            <el-button :type="viewMode === 'grid' ? 'primary' : ''" @click="viewMode = 'grid'">
              <el-icon><Grid /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="列表视图">
            <el-button :type="viewMode === 'list' ? 'primary' : ''" @click="viewMode = 'list'">
              <el-icon><List /></el-icon>
            </el-button>
          </el-tooltip>
        </el-button-group>
      </div>
    </div>

    <!-- Notes Display -->
    <div class="notes-content">
      <!-- Search Results -->
      <div v-if="searchResults.length > 0" class="search-results-section">
        <div class="section-header">
          <h3>
            <el-icon><Search /></el-icon>
            搜索结果 ({{ searchResults.length }})
          </h3>
          <el-button text @click="clearSearch">清除搜索</el-button>
        </div>
        <div :class="viewMode === 'grid' ? 'notes-grid' : 'notes-list'">
          <NoteCard
            v-for="result in searchResults"
            :key="result.note.id"
            :note="result.note"
            :similarity-score="result.similarity_score"
            @click="handleNoteClick(result.note)"
            @toggle-pin="handleTogglePin"
            @toggle-favorite="handleToggleFavorite"
          />
        </div>
      </div>

      <!-- Filtered Notes -->
      <div v-else>
        <div :class="viewMode === 'grid' ? 'notes-grid' : 'notes-list'">
          <NoteCard
            v-for="note in filteredNotes"
            :key="note.id"
            :note="note"
            @click="handleNoteClick(note)"
            @toggle-pin="handleTogglePin"
            @toggle-favorite="handleToggleFavorite"
          />
        </div>
        <el-empty
          v-if="filteredNotes.length === 0 && noteStore.notes.length === 0"
          description="暂无笔记，点击右上角创建第一条笔记"
        />
        <el-empty
          v-else-if="filteredNotes.length === 0"
          description="没有找到符合条件的笔记"
        />
      </div>
    </div>

    <!-- Template Selection Dialog -->
    <el-dialog
      v-model="showTemplateDialog"
      title="选择模板"
      width="900px"
      top="5vh"
    >
      <TemplateSelector
        @select="handleTemplateSelect"
        @cancel="handleTemplateCanel"
      />
    </el-dialog>

    <!-- Create/Edit Dialog - Notion-style Clean Layout -->
    <el-dialog
      v-model="showCreateDialog"
      :show-close="false"
      width="900px"
      top="5vh"
      class="note-editor-dialog"
    >
      <template #header>
        <div class="clean-header-v2">
          <el-button text @click="closeDialog">取消</el-button>
          <el-button
            type="primary"
            @click="handleSave"
            :loading="noteStore.loading"
          >
            {{ editingNote ? '保存' : '创建' }}
          </el-button>
        </div>
      </template>

      <div class="clean-content">
        <!-- Title Input - Large, Notion-style -->
        <input
          v-model="noteForm.title"
          class="clean-title"
          placeholder="无标题"
        />

        <!-- Editor - Seamless integration -->
        <div class="clean-editor">
          <MdEditor
            v-model="noteForm.content"
            :language="'zh-CN'"
            :preview="true"
            :toolbars="editorToolbars"
            :style="{ height: '550px' }"
            theme="light"
          >
            <template #defToolbars>
              <NormalToolbar title="插入笔记链接" @click="showNoteLinkPicker = true">
                <template #trigger>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
                    <path d="M10 6v2H5v11h11v-5h2v6a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h6zm11-3v8h-2V6.413l-7.793 7.794-1.414-1.414L17.585 5H13V3h8z"/>
                  </svg>
                </template>
              </NormalToolbar>
            </template>
          </MdEditor>
        </div>
      </div>

      <template #footer>
        <div class="clean-footer-v2">
          <div class="meta-row">
            <el-select
              v-model="noteForm.tag_names"
              multiple
              filterable
              allow-create
              placeholder="添加标签"
              size="small"
              class="footer-tags"
            >
              <el-option
                v-for="tag in noteStore.tags"
                :key="tag.id"
                :label="tag.name"
                :value="tag.name"
              />
            </el-select>

            <el-input
              v-model="noteForm.source_url"
              placeholder="来源链接（可选）"
              size="small"
              class="footer-source"
              clearable
            >
              <template #prefix>
                <el-icon><Link /></el-icon>
              </template>
            </el-input>
          </div>

          <span v-if="editingNote" class="footer-time">
            上次编辑: {{ formatTime(editingNote.updated_at) }}
          </span>
        </div>
      </template>
    </el-dialog>

    <!-- Note Link Picker Dialog -->
    <el-dialog
      v-model="showNoteLinkPicker"
      title="选择要链接的笔记"
      width="500px"
      class="note-link-picker-dialog"
    >
      <el-input
        v-model="linkSearchQuery"
        placeholder="搜索笔记..."
        clearable
        style="margin-bottom: 16px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>

      <div class="note-link-list">
        <div
          v-for="note in filteredNotesForLink"
          :key="note.id"
          class="note-link-item"
          @click="insertNoteLink(note)"
        >
          <span class="note-title">{{ note.title }}</span>
          <span class="note-date">{{ formatTime(note.updated_at) }}</span>
        </div>
        <el-empty v-if="filteredNotesForLink.length === 0" description="没有找到笔记" />
      </div>
    </el-dialog>

    <!-- View Dialog - New High-Quality Design -->
    <NoteDetailDialog
      v-if="viewingNote"
      v-model="showViewDialog"
      :note="viewingNote"
      @update="handleNoteUpdate"
      @delete="handleDelete"
      @navigate="handleNavigateToNote"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Link, Grid, List, Clock, EditPen, Close,
  PriceTag, Paperclip, Check, CircleCloseFilled
} from '@element-plus/icons-vue'
import { useNoteStore } from '@/stores/noteStore'
import NoteCard from '@/components/notes/NoteCard.vue'
import TemplateSelector from '@/components/notes/TemplateSelector.vue'
import NoteDetailDialog from '@/components/notes/NoteDetailDialog.vue'
import type { Note, RelatedNote, TemplateRenderResponse } from '@/types'
import { templateStorage } from '@/services/templateStorage'
import { MdEditor, MdPreview, NormalToolbar } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'

const noteStore = useNoteStore()

// ============================================
// State
// ============================================
const showCreateDialog = ref(false)
const showViewDialog = ref(false)
const showTemplateDialog = ref(false)
const searchQuery = ref('')
const searchResults = ref<RelatedNote[]>([])
const editingNote = ref<Note | null>(null)
const viewingNote = ref<Note | null>(null)
const selectedTags = ref<number[]>([])
const sortBy = ref('updated_at_desc')
const viewMode = ref<'grid' | 'list'>('grid')

// Iteration 1: Quick filters
const quickFilter = ref<'pinned' | 'favorited' | 'recent' | null>(null)
const titleFocused = ref(false)
const isSearching = ref(false)

// ============================================
// localStorage Search History
// ============================================
const SEARCH_HISTORY_KEY = 'note_search_history'
const MAX_HISTORY_ITEMS = 10

interface LocalSearchHistory {
  query: string
  timestamp: number
}

function getLocalSearchHistory(): LocalSearchHistory[] {
  try {
    const data = localStorage.getItem(SEARCH_HISTORY_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

function saveSearchToHistory(query: string) {
  const history = getLocalSearchHistory()
  // Remove existing duplicate
  const filtered = history.filter(h => h.query !== query)
  // Add to front
  filtered.unshift({ query, timestamp: Date.now() })
  // Limit count
  const trimmed = filtered.slice(0, MAX_HISTORY_ITEMS)
  localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(trimmed))
}

function deleteSearchHistory(query: string) {
  const history = getLocalSearchHistory()
  const filtered = history.filter(h => h.query !== query)
  localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(filtered))
}

// Iteration 2: Templates
const useTemplate = ref(false)

// Note Link Picker
const showNoteLinkPicker = ref(false)
const linkSearchQuery = ref('')

const noteForm = ref({
  title: '',
  content: '',
  source_url: '',
  tag_names: [] as string[]
})

// Markdown editor toolbar configuration
// 0 = custom toolbar slot (for note link button)
const editorToolbars = [
  'bold',
  'underline',
  'italic',
  'strikeThrough',
  '-',
  'title',
  'sub',
  'sup',
  'quote',
  'unorderedList',
  'orderedList',
  'task',
  '-',
  'codeRow',
  'code',
  'link',
  'image',
  'table',
  0,
  '-',
  'revoke',
  'next',
  '=',
  'pageFullscreen',
  'fullscreen',
  'preview',
  'catalog'
]

// ============================================
// Computed
// ============================================
const filteredNotes = computed(() => {
  let notes = [...noteStore.notes]

  // Apply quick filter
  if (quickFilter.value === 'pinned') {
    notes = notes.filter(n => n.is_pinned)
  } else if (quickFilter.value === 'favorited') {
    notes = notes.filter(n => n.is_favorited)
  } else if (quickFilter.value === 'recent') {
    const sevenDaysAgo = new Date()
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
    notes = notes.filter(n => new Date(n.updated_at) > sevenDaysAgo)
  }

  // Filter by tags
  if (selectedTags.value.length > 0) {
    notes = notes.filter(note =>
      note.tags.some(tag => selectedTags.value.includes(tag.id))
    )
  }

  // Sort
  notes.sort((a, b) => {
    switch (sortBy.value) {
      case 'updated_at_desc':
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
      case 'updated_at_asc':
        return new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime()
      case 'created_at_desc':
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      case 'title_asc':
        return a.title.localeCompare(b.title, 'zh-CN')
      case 'title_desc':
        return b.title.localeCompare(a.title, 'zh-CN')
      default:
        return 0
    }
  })

  return notes
})

const pinnedCount = computed(() =>
  noteStore.notes.filter(n => n.is_pinned).length
)

const favoritedCount = computed(() =>
  noteStore.notes.filter(n => n.is_favorited).length
)

// Filtered notes for link picker (exclude current editing note)
const filteredNotesForLink = computed(() => {
  const query = linkSearchQuery.value.toLowerCase()
  return noteStore.notes
    .filter(n => n.id !== editingNote.value?.id) // Exclude current note
    .filter(n => !query || n.title.toLowerCase().includes(query))
    .slice(0, 20) // Limit display count
})

onMounted(async () => {
  await Promise.all([
    noteStore.fetchNotes(),
    noteStore.fetchTags()
  ])
})

// Note: Real-time search disabled - search only triggers on button click or Enter key

async function handleSearch() {
  if (!searchQuery.value || !searchQuery.value.trim()) {
    return
  }

  const query = searchQuery.value.trim()
  // Save to localStorage (with deduplication)
  saveSearchToHistory(query)

  isSearching.value = true
  try {
    searchResults.value = await noteStore.searchNotesSemantic(query)
    if (searchResults.value.length === 0) {
      ElMessage.info('未找到相关笔记')
    }
  } catch (error) {
    console.error('Search failed:', error)
    ElMessage.error('搜索失败')
  } finally {
    isSearching.value = false
  }
}

function clearSearch() {
  searchQuery.value = ''
  searchResults.value = []
}

function handleNoteClick(note: Note) {
  viewingNote.value = note
  showViewDialog.value = true
}

async function handleNoteUpdate(updates: Partial<Note>) {
  if (!viewingNote.value) return

  try {
    await noteStore.updateNote(viewingNote.value.id, updates)
    // Refresh the viewing note
    const updatedNote = noteStore.notes.find(n => n.id === viewingNote.value!.id)
    if (updatedNote) {
      viewingNote.value = updatedNote
    }
  } catch (error) {
    console.error('Failed to update note:', error)
    ElMessage.error('更新失败')
  }
}

function handleEdit() {
  if (viewingNote.value) {
    editingNote.value = viewingNote.value
    noteForm.value = {
      title: viewingNote.value.title,
      content: viewingNote.value.content,
      source_url: viewingNote.value.source_url || '',
      tag_names: viewingNote.value.tags.map(t => t.name)
    }
    showViewDialog.value = false
    showCreateDialog.value = true
  }
}

async function handleDelete() {
  if (!viewingNote.value) return

  try {
    await ElMessageBox.confirm('确定要删除这篇笔记吗？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await noteStore.deleteNote(viewingNote.value.id)
    showViewDialog.value = false
    viewingNote.value = null
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function handleSave() {
  if (!noteForm.value.title || !noteForm.value.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }

  try {
    if (editingNote.value) {
      await noteStore.updateNote(editingNote.value.id, noteForm.value)
      ElMessage.success('笔记更新成功')
    } else {
      await noteStore.createNote(noteForm.value)
      ElMessage.success('笔记创建成功')
    }
    closeDialog()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

function closeDialog() {
  showCreateDialog.value = false
  editingNote.value = null
  noteForm.value = {
    title: '',
    content: '',
    source_url: '',
    tag_names: []
  }
}

// Format relative time
function formatTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`

  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function openCreateDialog() {
  // Check if templates exist in localStorage
  const templates = templateStorage.getAllTemplates()
  useTemplate.value = templates.length > 0
  if (useTemplate.value) {
    showTemplateDialog.value = true
  } else {
    showCreateDialog.value = true
  }
}

function handleTemplateSelect(rendered: TemplateRenderResponse) {
  showTemplateDialog.value = false
  noteForm.value.title = rendered.suggested_title
  noteForm.value.content = rendered.content
  showCreateDialog.value = true
}

function handleTemplateCanel() {
  showTemplateDialog.value = false
  showCreateDialog.value = true
}

function toggleQuickFilter(filter: 'pinned' | 'favorited' | 'recent') {
  quickFilter.value = quickFilter.value === filter ? null : filter
}

function querySearchHistory(queryString: string, cb: Function) {
  if (!queryString) {
    const history = getLocalSearchHistory()
    cb(history.map(h => ({ value: h.query })))
  } else {
    cb([])
  }
}

function handleDeleteHistory(query: string) {
  deleteSearchHistory(query)
}

// Insert note link [[Title]] at the end of content
function insertNoteLink(note: Note) {
  const linkText = `[[${note.title}]]`
  noteForm.value.content += linkText
  showNoteLinkPicker.value = false
  linkSearchQuery.value = ''
  ElMessage.success(`已插入链接: ${note.title}`)
}

function handleHistorySelect(item: { value: string }) {
  searchQuery.value = item.value
  handleSearch()
}

// Quick actions handlers
async function handleTogglePin(noteId: number, pinned: boolean) {
  try {
    await noteStore.togglePin(noteId, pinned)
    ElMessage.success(pinned ? '已置顶' : '已取消置顶')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

async function handleToggleFavorite(noteId: number, favorited: boolean) {
  try {
    await noteStore.toggleFavorite(noteId, favorited)
    ElMessage.success(favorited ? '已收藏' : '已取消收藏')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// Handle navigation from backlinks
function handleNavigateToNote(noteId: number) {
  const note = noteStore.notes.find(n => n.id === noteId)
  if (note) {
    viewingNote.value = note
    showViewDialog.value = true
  } else {
    ElMessage.warning('笔记不存在或已被删除')
  }
}
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';
@import '@/assets/styles/mixins.scss';

.notes-view {
  max-width: 1600px;
  margin: 0 auto;
}

// ============================================
// Header
// ============================================
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: $spacing-xl;

  .header-left {
    .page-title {
      font-size: $font-size-xxl;
      font-weight: 600;
      color: $color-text-primary;
      margin: 0 0 $spacing-sm 0;
    }

    .header-stats {
      display: flex;
      align-items: center;
      gap: $spacing-md;
      font-size: $font-size-sm;
      color: $color-text-secondary;

      .stat-divider {
        color: $color-text-tertiary;
      }
    }
  }

  .header-actions {
    display: flex;
    gap: $spacing-md;
  }
}

// ============================================
// Filters
// ============================================
.filters-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: $spacing-xl;
  padding: $spacing-lg;
  background-color: $bg-color-card;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  flex-wrap: wrap;
  gap: $spacing-md;

  .filters-left {
    display: flex;
    gap: $spacing-md;
    flex: 1;
    flex-wrap: wrap;
    align-items: center;
    min-width: 0; // 防止 flex 子元素溢出
  }

  .filters-right {
    flex-shrink: 0;
  }

  // 响应式筛选器元素
  .filter-search {
    width: 280px;
    min-width: 200px;
    flex-shrink: 1;
  }

  .filter-tags {
    width: 180px;
    min-width: 140px;
    flex-shrink: 1;
  }

  .filter-sort {
    width: 130px;
    min-width: 110px;
    flex-shrink: 1;
  }
}

.tag-option {
  display: flex;
  align-items: center;
  gap: $spacing-sm;

  .tag-color-dot {
    width: 10px;
    height: 10px;
    border-radius: $radius-round;
    flex-shrink: 0;
  }
}

// ============================================
// Notes Content
// ============================================
.notes-content {
  min-height: 400px;
}

.search-results-section {
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-lg;
    padding: $spacing-md $spacing-lg;
    background-color: rgba($color-primary, 0.05);
    border-radius: $radius-md;
    border-left: 4px solid $color-primary;

    h3 {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      margin: 0;
      font-size: $font-size-lg;
      font-weight: 600;
      color: $color-primary;
    }
  }
}

.notes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: $spacing-lg;
}

.notes-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

// ============================================
// Dialog Styles
// ============================================
.note-meta {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  margin: $spacing-lg 0;
}

.source-link {
  display: flex;
  align-items: center;
  gap: $spacing-xs;
  font-size: $font-size-sm;
  color: $color-primary;

  a {
    color: $color-primary;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}

.note-content {
  white-space: pre-wrap;
  line-height: 1.6;
  color: $color-text-regular;
  font-size: $font-size-sm;
}

// ============================================
// Notion-style Clean Note Editor
// ============================================

:deep(.note-editor-dialog) {
  .el-dialog__header {
    padding: 16px 24px;
    margin: 0;
    border-bottom: 1px solid #e8e8e8;
    background: #fff;
  }

  .el-dialog__body {
    padding: 0;
    max-height: calc(90vh - 140px);
    overflow-y: auto;
    background: #fff;

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: transparent;
    }

    &::-webkit-scrollbar-thumb {
      background: #d0d0d0;
      border-radius: 3px;

      &:hover {
        background: #b0b0b0;
      }
    }
  }

  .el-dialog__footer {
    padding: 12px 24px;
    border-top: 1px solid #e8e8e8;
    background: #fafafa;
  }
}

.clean-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;

    .header-tags {
      min-width: 200px;
      max-width: 300px;
    }

    .header-source {
      min-width: 250px;
      max-width: 350px;
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.clean-content {
  padding: 40px 80px;
  background: #fff;

  .clean-title {
    width: 100%;
    font-size: 32px;
    font-weight: 700;
    line-height: 1.4;
    color: #1a1a1a;
    border: none;
    outline: none;
    background: transparent;
    padding: 0;
    margin-bottom: 20px;

    &::placeholder {
      color: #d0d0d0;
      font-weight: 700;
    }
  }

  .clean-editor {
    margin-bottom: 30px;

    :deep(.md-editor) {
      border: none;
      box-shadow: none;
    }
  }

  .clean-attachments {
    margin-top: 40px;
    padding-top: 24px;
    border-top: 1px solid #e8e8e8;

    .attachments-title {
      font-size: 14px;
      font-weight: 600;
      color: #606060;
      margin-bottom: 16px;
    }
  }
}

.clean-footer {
  display: flex;
  justify-content: center;
  align-items: center;

  .footer-time {
    font-size: 12px;
    color: #999;
  }
}

// ============================================
// New v2 Layout Styles (Notion-style)
// ============================================
.clean-header-v2 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  border-bottom: 1px solid #e8e8e8;
}

.clean-footer-v2 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;

  .meta-row {
    display: flex;
    gap: 12px;
    flex: 1;
  }

  .footer-tags {
    min-width: 200px;
    max-width: 280px;
  }

  .footer-source {
    min-width: 200px;
    max-width: 300px;
  }

  .footer-time {
    font-size: 12px;
    color: #999;
    flex-shrink: 0;
  }
}

// ============================================
// Search History Item Styles
// ============================================
.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 4px 0;

  .history-text {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .delete-icon {
    color: #c0c4cc;
    cursor: pointer;
    opacity: 0;
    transition: all 0.2s ease;
    font-size: 14px;

    &:hover {
      color: #f56c6c;
    }
  }

  &:hover .delete-icon {
    opacity: 1;
  }
}

// ============================================
// Note Link Picker Styles
// ============================================
.note-link-list {
  max-height: 400px;
  overflow-y: auto;
}

.note-link-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background 0.2s ease;

  &:hover {
    background: #f5f7fa;
  }

  &:last-child {
    border-bottom: none;
  }

  .note-title {
    font-weight: 500;
    color: #303133;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-right: 12px;
  }

  .note-date {
    font-size: 12px;
    color: #909399;
    flex-shrink: 0;
  }
}
</style>
