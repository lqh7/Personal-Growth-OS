<template>
  <div class="notes-view">
    <!-- Header with actions -->
    <div class="view-header">
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        创建笔记
      </el-button>
      <el-input
        v-model="searchQuery"
        placeholder="语义搜索笔记..."
        style="width: 300px; margin-left: 12px"
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button @click="handleSearch" :loading="noteStore.loading">
            <el-icon><Search /></el-icon>
          </el-button>
        </template>
      </el-input>
    </div>

    <!-- Search Results -->
    <div v-if="searchResults.length > 0" class="search-results">
      <h3>搜索结果</h3>
      <el-button text @click="clearSearch">清除</el-button>
      <div class="notes-grid">
        <NoteCard
          v-for="result in searchResults"
          :key="result.note.id"
          :note="result.note"
          :similarity-score="result.similarity_score"
          @click="handleNoteClick(result.note)"
        />
      </div>
    </div>

    <!-- All Notes -->
    <div v-else>
      <h3>所有笔记</h3>
      <div class="notes-grid">
        <NoteCard
          v-for="note in noteStore.notes"
          :key="note.id"
          :note="note"
          @click="handleNoteClick(note)"
        />
      </div>
      <el-empty v-if="noteStore.notes.length === 0" description="暂无笔记" />
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
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Link } from '@element-plus/icons-vue'
import { useNoteStore } from '@/stores/noteStore'
import NoteCard from '@/components/notes/NoteCard.vue'
import type { Note, RelatedNote } from '@/types'

const noteStore = useNoteStore()

const showCreateDialog = ref(false)
const showViewDialog = ref(false)
const searchQuery = ref('')
const searchResults = ref<RelatedNote[]>([])
const editingNote = ref<Note | null>(null)
const viewingNote = ref<Note | null>(null)

const noteForm = ref({
  title: '',
  content: '',
  source_url: '',
  tag_names: [] as string[]
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

<style scoped>
.notes-view {
  max-width: 1400px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 24px;
  display: flex;
  align-items: center;
}

.search-results {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 24px;
}

.search-results h3 {
  display: inline-block;
  margin-right: 12px;
}

.notes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

h3 {
  color: #303133;
  margin-bottom: 16px;
}

.note-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
}

.source-link {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #409eff;
}

.source-link a {
  color: #409eff;
  text-decoration: none;
}

.note-content {
  white-space: pre-wrap;
  line-height: 1.6;
  color: #606266;
}
</style>
