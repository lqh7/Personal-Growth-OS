<template>
  <div
    class="note-card-notion"
    :class="{ 'is-pinned': note.is_pinned }"
    @click="$emit('click')"
  >
    <!-- Cover Image or Gradient Background -->
    <div class="card-cover" :style="coverStyle">
      <span v-if="note.emoji" class="card-emoji">{{ note.emoji }}</span>
    </div>

    <!-- Card Body -->
    <div class="card-body">
      <!-- Title with Pin/Favorite Icons -->
      <h4 class="card-title">
        <span v-if="note.is_pinned" class="pin-icon">📌</span>
        <span class="title-text">{{ note.title }}</span>
        <span v-if="note.is_favorited" class="favorite-icon">⭐</span>
      </h4>

      <!-- Content Preview (3 lines max) -->
      <p class="card-preview">{{ truncatedContent }}</p>

      <!-- Footer Meta -->
      <div class="card-footer">
        <!-- Project Tag -->
        <el-tag
          v-if="note.project"
          size="small"
          :color="note.project.color"
          :style="{
            backgroundColor: note.project.color,
            color: '#fff',
            border: 'none'
          }"
        >
          {{ note.project.name }}
        </el-tag>

        <!-- Tags -->
        <el-tag
          v-for="tag in note.tags.slice(0, 2)"
          :key="tag.id"
          size="small"
          type="info"
          effect="plain"
        >
          {{ tag.name }}
        </el-tag>
        <span v-if="note.tags.length > 2" class="more-tags">+{{ note.tags.length - 2 }}</span>

        <div class="footer-right">
          <!-- View Count -->
          <span v-if="note.view_count > 0" class="view-count">
            <el-icon><View /></el-icon>
            {{ note.view_count }}
          </span>

          <!-- Update Time -->
          <span class="update-time">{{ formatTime(note.updated_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { View } from '@element-plus/icons-vue'
import type { Note } from '@/types'

interface Props {
  note: Note
  similarityScore?: number
}

const props = defineProps<Props>()

defineEmits<{
  (e: 'click'): void
}>()

// Truncate content to max 150 characters for preview
const truncatedContent = computed(() => {
  const plainText = props.note.content
    .replace(/[#*`_~\[\]]/g, '') // Remove Markdown symbols
    .replace(/\n+/g, ' ') // Replace newlines with spaces
    .trim()

  return plainText.length > 150
    ? plainText.substring(0, 150) + '...'
    : plainText
})

// Cover style: use cover_image if available, otherwise gradient
const coverStyle = computed(() => {
  if (props.note.cover_image) {
    return {
      backgroundImage: `url(${props.note.cover_image})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    }
  }

  // Default gradient based on note ID for variety
  const gradients = [
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
    'linear-gradient(135deg, #30cfd0 0%, #330867 100%)'
  ]

  const gradientIndex = props.note.id % gradients.length
  return { background: gradients[gradientIndex] }
})

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
    day: '2-digit'
  })
}
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';
@import '@/assets/styles/mixins.scss';

.note-card-notion {
  border: 1px solid transparent;
  border-radius: $radius-lg;
  background: white;
  overflow: hidden;
  transition: all $transition-base ease;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

  &:hover {
    border-color: $color-border;
    background-color: #fafafa;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  &.is-pinned {
    border-color: rgba($color-primary, 0.3);
    background: linear-gradient(135deg, #f5f7fa 0%, #f0f2ff 100%);
  }
}

.card-cover {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;

  .card-emoji {
    font-size: 48px;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
  }
}

.card-body {
  padding: $spacing-lg;
}

.card-title {
  font-size: $font-size-lg;
  font-weight: 600;
  color: $color-text-primary;
  margin: 0 0 $spacing-md 0;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  line-height: 1.4;

  .title-text {
    flex: 1;
    @include text-ellipsis;
  }

  .pin-icon,
  .favorite-icon {
    font-size: $font-size-md;
    flex-shrink: 0;
  }

  .pin-icon {
    color: $color-primary;
  }

  .favorite-icon {
    color: #f59e0b;
  }
}

.card-preview {
  font-size: $font-size-sm;
  color: $color-text-secondary;
  line-height: 1.6;
  margin: 0 0 $spacing-lg 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 4.8em; // 3 lines minimum
}

.card-footer {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  flex-wrap: wrap;
  font-size: $font-size-xs;
  color: $color-text-tertiary;

  .more-tags {
    font-size: $font-size-xs;
    color: $color-text-tertiary;
  }

  .footer-right {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: $spacing-md;
  }

  .view-count {
    display: flex;
    align-items: center;
    gap: 4px;
    color: $color-text-tertiary;
  }

  .update-time {
    color: $color-text-tertiary;
  }
}

// Dark mode support (optional)
@media (prefers-color-scheme: dark) {
  .note-card-notion {
    background: #1e1e1e;
    border-color: #333;

    &:hover {
      background-color: #252525;
      border-color: #444;
    }

    &.is-pinned {
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
  }

  .card-title {
    color: #e0e0e0;
  }

  .card-preview {
    color: #b0b0b0;
  }

  .card-footer {
    color: #888;
  }
}
</style>
