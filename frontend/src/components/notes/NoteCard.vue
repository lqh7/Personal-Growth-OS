<template>
  <el-card class="note-card" shadow="hover" @click="emit('click')">
    <template #header>
      <div class="card-header">
        <h4>{{ note.title }}</h4>
        <span v-if="similarityScore" class="similarity-badge">
          {{ (similarityScore * 100).toFixed(0) }}% 相关
        </span>
      </div>
    </template>

    <div class="note-preview">
      {{ truncatedContent }}
    </div>

    <div class="note-footer">
      <div class="tags">
        <el-tag
          v-for="tag in note.tags.slice(0, 3)"
          :key="tag.id"
          size="small"
          :color="tag.color"
        >
          {{ tag.name }}
        </el-tag>
        <span v-if="note.tags.length > 3" class="more-tags">
          +{{ note.tags.length - 3 }}
        </span>
      </div>
      <span class="date">{{ formatDate(note.updated_at) }}</span>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Note } from '@/types'

const props = defineProps<{
  note: Note
  similarityScore?: number
}>()

const emit = defineEmits<{
  click: []
}>()

const truncatedContent = computed(() => {
  const maxLength = 150
  if (props.note.content.length > maxLength) {
    return props.note.content.substring(0, maxLength) + '...'
  }
  return props.note.content
})

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.note-card {
  cursor: pointer;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.note-card:hover {
  transform: translateY(-2px);
  transition: transform 0.2s;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  flex: 1;
}

.similarity-badge {
  background-color: #409eff;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.note-preview {
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 16px;
  flex: 1;
}

.note-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  flex: 1;
}

.more-tags {
  font-size: 12px;
  color: #909399;
}

.date {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
  margin-left: 8px;
}
</style>
