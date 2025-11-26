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

  // 中国传统色系渐变 - 宋瓷雅韵
  const gradients = [
    'linear-gradient(135deg, rgba(168, 197, 186, 0.25) 0%, rgba(136, 179, 168, 0.35) 100%)', // 天青渐变
    'linear-gradient(135deg, rgba(212, 165, 165, 0.25) 0%, rgba(193, 138, 122, 0.35) 100%)', // 藕荷渐变
    'linear-gradient(135deg, rgba(158, 179, 191, 0.25) 0%, rgba(127, 168, 157, 0.35) 100%)', // 烟雨蓝渐变
    'linear-gradient(135deg, rgba(217, 167, 106, 0.25) 0%, rgba(196, 149, 88, 0.35) 100%)',  // 琥珀黄渐变
    'linear-gradient(135deg, rgba(184, 212, 201, 0.25) 0%, rgba(157, 197, 184, 0.35) 100%)', // 浅粉青渐变
    'linear-gradient(135deg, rgba(127, 168, 157, 0.25) 0%, rgba(106, 150, 136, 0.35) 100%)'  // 梅子青渐变
  ]

  const gradientIndex = props.note.id % gradients.length
  return {
    background: gradients[gradientIndex],
    backdropFilter: 'blur(10px)'
  }
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
@import '@/assets/styles/animations.scss';

.note-card-notion {
  @include card-base;
  @include hover-gloss;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  animation: fadeInScale 0.6s cubic-bezier(0.4, 0, 0.2, 1) both;

  &:hover {
    transform: translateY(-6px) scale(1.02);
    box-shadow: $shadow-lg;
    border-color: rgba(136, 179, 168, 0.4);
  }

  &.is-pinned {
    border-left: 4px solid $color-primary;
    background: linear-gradient(145deg,
      rgba(253, 252, 248, 1) 0%,
      rgba(245, 243, 237, 0.98) 100%);
    box-shadow: 0 4px 16px rgba(136, 179, 168, 0.15);

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: linear-gradient(135deg,
        rgba(136, 179, 168, 0.05) 0%,
        transparent 100%);
      pointer-events: none;
    }
  }
}

.card-cover {
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  border-radius: $radius-lg $radius-lg 0 0;
  overflow: hidden;

  // 水墨纹理叠加
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
      radial-gradient(circle at 30% 40%, rgba(255, 255, 255, 0.15) 0%, transparent 50%),
      radial-gradient(circle at 70% 60%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
    pointer-events: none;
  }

  .card-emoji {
    font-size: 56px;
    filter: drop-shadow(0 4px 8px rgba(58, 58, 58, 0.15));
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 1;
  }
}

// 悬停时emoji微动
.note-card-notion:hover .card-cover .card-emoji {
  transform: scale(1.1) rotate(5deg);
}

.card-body {
  padding: $spacing-xl;
  background: linear-gradient(180deg,
    rgba(253, 252, 248, 1) 0%,
    rgba(253, 252, 248, 0.98) 100%);
}

.card-title {
  font-size: $font-size-lg + 2px;
  font-weight: $font-weight-semibold;
  color: $color-text-primary;
  margin: 0 0 $spacing-lg 0;
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  line-height: 1.5;
  letter-spacing: 0.3px;

  .title-text {
    flex: 1;
    @include text-ellipsis;
    transition: color 0.2s;
  }

  .pin-icon,
  .favorite-icon {
    font-size: $font-size-lg;
    flex-shrink: 0;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .pin-icon {
    filter: drop-shadow(0 1px 2px rgba(136, 179, 168, 0.3));
  }

  .favorite-icon {
    filter: drop-shadow(0 1px 2px rgba(217, 167, 106, 0.3));
  }

  &:hover .title-text {
    color: $color-primary-dark;
  }

  &:hover .pin-icon,
  &:hover .favorite-icon {
    transform: scale(1.2);
  }
}

.card-preview {
  font-size: $font-size-md;
  color: $color-text-regular;
  line-height: 1.8;
  margin: 0 0 $spacing-xl 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 5.4em; // 3 lines * 1.8 line-height
  letter-spacing: 0.3px;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  flex-wrap: wrap;
  padding-top: $spacing-md;
  border-top: 1px solid rgba(217, 212, 201, 0.2);
  font-size: $font-size-sm;
  color: $color-text-secondary;

  // 覆盖Element Plus标签样式
  :deep(.el-tag) {
    border-radius: $radius-round;
    padding: 4px 12px;
    font-size: $font-size-xs;
    font-weight: $font-weight-medium;
    letter-spacing: 0.3px;
    border: 1.5px solid currentColor;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      transform: scale(1.05);
      box-shadow: 0 2px 8px rgba(136, 179, 168, 0.2);
    }
  }

  .more-tags {
    font-size: $font-size-xs;
    color: $color-text-tertiary;
    padding: 4px 8px;
    background: rgba(136, 179, 168, 0.08);
    border-radius: $radius-round;
    font-weight: $font-weight-medium;
  }

  .footer-right {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: $spacing-lg;
  }

  .view-count {
    display: flex;
    align-items: center;
    gap: 6px;
    color: $color-text-secondary;
    font-size: $font-size-sm;
    transition: color 0.2s;

    &:hover {
      color: $color-primary;
    }

    .el-icon {
      font-size: $font-size-md;
    }
  }

  .update-time {
    color: $color-text-secondary;
    font-size: $font-size-sm;
    font-weight: $font-weight-normal;
  }
}
</style>
