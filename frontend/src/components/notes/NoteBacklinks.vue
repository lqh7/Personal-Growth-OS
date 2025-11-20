<template>
  <div class="note-backlinks">
    <h4 class="backlinks-title">
      <el-icon><Link /></el-icon>
      反向链接 ({{ backlinks.length }})
    </h4>

    <div v-if="backlinks.length === 0" class="empty-state">
      暂无其他笔记链接到此笔记
    </div>

    <div v-else class="backlinks-list">
      <div
        v-for="backlink in backlinks"
        :key="backlink.note_id"
        class="backlink-item"
        @click="$emit('navigate', backlink.note_id)"
      >
        <el-icon class="link-icon"><Document /></el-icon>
        <div class="backlink-info">
          <span class="backlink-title">{{ backlink.note_title }}</span>
          <span class="backlink-date">{{ formatDate(backlink.created_at) }}</span>
        </div>
        <el-icon class="arrow-icon"><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Link, Document, ArrowRight } from '@element-plus/icons-vue'
import type { Backlink } from '@/types'
import apiClient from '@/api/client'

interface Props {
  noteId: number
}

const props = defineProps<Props>()

defineEmits<{
  (e: 'navigate', noteId: number): void
}>()

const backlinks = ref<Backlink[]>([])
const loading = ref(false)

onMounted(() => {
  fetchBacklinks()
})

watch(() => props.noteId, () => {
  fetchBacklinks()
})

async function fetchBacklinks() {
  try {
    loading.value = true
    const response = await apiClient.get(`/links/note/${props.noteId}/backlinks`)
    backlinks.value = response.data
  } catch (error) {
    console.error('Failed to fetch backlinks:', error)
    ElMessage.error('加载反向链接失败')
  } finally {
    loading.value = false
  }
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';

.note-backlinks {
  .backlinks-title {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    font-size: $font-size-md;
    font-weight: 600;
    color: $color-text-primary;
    margin-bottom: $spacing-md;
  }

  .empty-state {
    text-align: center;
    padding: $spacing-xl;
    color: $color-text-tertiary;
    font-size: $font-size-sm;
  }

  .backlinks-list {
    display: flex;
    flex-direction: column;
    gap: $spacing-sm;
  }

  .backlink-item {
    display: flex;
    align-items: center;
    padding: $spacing-md;
    border: 1px solid $color-border;
    border-radius: $radius-md;
    cursor: pointer;
    transition: all $transition-base;

    &:hover {
      background-color: #fafafa;
      border-color: $color-primary;
      transform: translateX(4px);
    }

    .link-icon {
      font-size: 20px;
      color: $color-primary;
      margin-right: $spacing-md;
      flex-shrink: 0;
    }

    .backlink-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 4px;

      .backlink-title {
        font-size: $font-size-md;
        color: $color-text-primary;
        font-weight: 500;
      }

      .backlink-date {
        font-size: $font-size-xs;
        color: $color-text-tertiary;
      }
    }

    .arrow-icon {
      font-size: 16px;
      color: $color-text-tertiary;
      flex-shrink: 0;
    }
  }
}
</style>
