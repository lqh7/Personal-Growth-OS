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
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          创建笔记
        </el-button>
      </div>
    </div>

    <!-- Filters Bar -->
    <div class="filters-bar">
      <div class="filters-left">
        <el-input
          v-model="searchQuery"
          placeholder="语义搜索笔记..."
          clearable
          style="width: 300px"
          @keyup.enter="handleSearch"
          @clear="clearSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
          <template #append>
            <el-button @click="handleSearch" :loading="noteStore.loading">
              搜索
            </el-button>
          </template>
        </el-input>

        <el-select
          v-model="selectedTags"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="按标签筛选"
          clearable
          style="width: 240px"
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

        <el-select v-model="sortBy" placeholder="排序" style="width: 150px">
          <el-option label="最新更新" value="updated_at" />
          <el-option label="最早创建" value="created_at" />
          <el-option label="标题 A-Z" value="title" />
        </el-select>
      </div>

      <div class="filters-right">
        <el-button-group>
          <el-button :type="viewMode === 'grid' ? 'primary' : ''" @click="viewMode = 'grid'">
            <el-icon><Grid /></el-icon>
            网格
          </el-button>
          <el-button :type="viewMode === 'list' ? 'primary' : ''" @click="viewMode = 'list'">
            <el-icon><List /></el-icon>
            列表
          </el-button>
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

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingNote ? '编辑笔记' : '创建笔记'"
      width="700px"
    >
      <el-form :model="noteForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="noteForm.title" placeholder="笔记标题" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="noteForm.content"
            type="textarea"
            :rows="10"
            placeholder="支持 Markdown 格式"
          />
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="noteForm.source_url" placeholder="来源 URL（可选）" />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="noteForm.tag_names"
            multiple
            filterable
            allow-create
            placeholder="选择或创建标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in noteStore.tags"
              :key="tag.id"
              :label="tag.name"
              :value="tag.name"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeDialog">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="noteStore.loading">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- View Dialog -->
    <el-dialog v-model="showViewDialog" title="笔记详情" width="800px">
      <div v-if="viewingNote">
        <h2>{{ viewingNote.title }}</h2>
        <div class="note-meta">
          <el-tag
            v-for="tag in viewingNote.tags"
            :key="tag.id"
            size="small"
            style="margin-right: 8px"
          >
            {{ tag.name }}
          </el-tag>
          <span v-if="viewingNote.source_url" class="source-link">
            <el-icon><Link /></el-icon>
            <a :href="viewingNote.source_url" target="_blank">来源</a>
          </span>
        </div>
        <el-divider />
        <div class="note-content">
          {{ viewingNote.content }}
        </div>
      </div>
      <template #footer>
        <el-button @click="handleEdit">编辑</el-button>
        <el-button type="danger" @click="handleDelete">删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Link, Grid, List } from '@element-plus/icons-vue'
import { useNoteStore } from '@/stores/noteStore'
import NoteCard from '@/components/notes/NoteCard.vue'
import type { Note, RelatedNote } from '@/types'

const noteStore = useNoteStore()

// ============================================
// State
// ============================================
const showCreateDialog = ref(false)
const showViewDialog = ref(false)
const searchQuery = ref('')
const searchResults = ref<RelatedNote[]>([])
const editingNote = ref<Note | null>(null)
const viewingNote = ref<Note | null>(null)
const selectedTags = ref<number[]>([])
const sortBy = ref('updated_at')
const viewMode = ref<'grid' | 'list'>('grid')

const noteForm = ref({
  title: '',
  content: '',
  source_url: '',
  tag_names: [] as string[]
})

// ============================================
// Computed
// ============================================
const filteredNotes = computed(() => {
  let notes = [...noteStore.notes]

  // Filter by tags
  if (selectedTags.value.length > 0) {
    notes = notes.filter(note =>
      note.tags.some(tag => selectedTags.value.includes(tag.id))
    )
  }

  // Sort
  notes.sort((a, b) => {
    if (sortBy.value === 'updated_at') {
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    } else if (sortBy.value === 'created_at') {
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    } else if (sortBy.value === 'title') {
      return a.title.localeCompare(b.title)
    }
    return 0
  })

  return notes
})

onMounted(async () => {
  await Promise.all([
    noteStore.fetchNotes(),
    noteStore.fetchTags()
  ])
})

async function handleSearch() {
  if (!searchQuery.value) {
    return
  }

  try {
    searchResults.value = await noteStore.searchNotesSemantic(searchQuery.value)
    if (searchResults.value.length === 0) {
      ElMessage.info('未找到相关笔记')
    }
  } catch (error) {
    ElMessage.error('搜索失败')
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
  align-items: center;
  margin-bottom: $spacing-xl;
  padding: $spacing-lg;
  background-color: $bg-color-card;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;

  .filters-left {
    display: flex;
    gap: $spacing-md;
    flex: 1;
  }

  .filters-right {
    flex-shrink: 0;
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
</style>
