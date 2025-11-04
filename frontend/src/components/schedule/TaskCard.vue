<template>
  <!-- Task Card with Detail Popover -->
  <el-popover
    placement="right"
    :width="250"
    trigger="hover"
    popper-class="task-detail-popover"
  >
    <template #reference>
      <div
        class="task-card"
        :class="[priorityClass, { 'truncated-top': isTruncatedTop, 'truncated-bottom': isTruncatedBottom }]"
        :style="cardStyle"
        @click="$emit('task-click', task)"
      >
        <!-- Top Truncation Indicator -->
        <div v-if="isTruncatedTop" class="truncation-indicator truncation-top">
          <el-icon class="truncation-arrow"><ArrowUp /></el-icon>
          <span class="truncation-time">{{ formatTime(task.startTime) }}</span>
        </div>

        <!-- Task Content (only title) -->
        <div class="task-content">
          <div v-if="showTitle" class="task-title">{{ task.title }}</div>
        </div>

        <!-- Bottom Truncation Indicator -->
        <div v-if="isTruncatedBottom" class="truncation-indicator truncation-bottom">
          <span class="truncation-time">{{ formatTime(task.endTime) }}</span>
          <el-icon class="truncation-arrow"><ArrowDown /></el-icon>
        </div>
      </div>
    </template>

    <!-- Popover Content: Task Details -->
    <div class="task-details">
      <div class="detail-item">
        <span class="detail-label">标题:</span>
        <span class="detail-value">{{ task.title }}</span>
      </div>
      <div class="detail-item">
        <span class="detail-label">开始:</span>
        <span class="detail-value">{{ startTimeText }}</span>
      </div>
      <div class="detail-item">
        <span class="detail-label">结束:</span>
        <span class="detail-value">{{ endTimeText }}</span>
      </div>
      <div class="detail-item">
        <span class="detail-label">优先级:</span>
        <span class="detail-value">{{ priorityText }}</span>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowUp, ArrowDown } from '@element-plus/icons-vue'

interface Task {
  id: string
  title: string
  description?: string
  status: 'pending' | 'in_progress' | 'completed'
  priority: number
  startTime?: Date
  endTime?: Date
  completed: boolean
  project?: {
    id: string
    name: string
    color: string
  }
}

interface Props {
  task: Task
  top: number              // Absolute position from 8:00 (in px)
  height: number           // Height in px
  renderStartTime: Date    // Actual render start time
  renderEndTime: Date      // Actual render end time
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'task-click', task: Task): void
}>()

// ============================================
// Computed
// ============================================

const priorityClass = computed(() => {
  const priority = props.task.priority
  if (priority >= 4) return 'priority-high'
  if (priority >= 2) return 'priority-medium'
  return 'priority-low'
})

const isTruncatedTop = computed(() => {
  if (!props.task.startTime) return false
  const taskStart = new Date(props.task.startTime)
  // Truncated if task starts before render starts
  return taskStart < props.renderStartTime
})

const isTruncatedBottom = computed(() => {
  if (!props.task.endTime) return false
  const taskEnd = new Date(props.task.endTime)
  // Truncated if task ends after render ends
  return taskEnd > props.renderEndTime
})

const showTitle = computed(() => {
  // Hide title when height < 15px (duration < 15 minutes)
  return props.height >= 15
})

const cardStyle = computed(() => {
  return {
    top: `${props.top}px`,
    height: `${props.height}px`
  }
})

const formatDateTime = (date: Date) => {
  const year = date.getFullYear()
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}`
}

const startTimeText = computed(() => {
  if (!props.task.startTime) return ''
  return formatDateTime(new Date(props.task.startTime))
})

const endTimeText = computed(() => {
  if (!props.task.endTime) return ''
  return formatDateTime(new Date(props.task.endTime))
})

const priorityText = computed(() => {
  const priority = props.task.priority
  if (priority >= 4) return '高'
  if (priority >= 2) return '中'
  return '低'
})

function formatTime(time?: Date): string {
  if (!time) return ''
  const date = new Date(time)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}
</script>

<style scoped lang="scss">
$color-priority-high: #ef4444;
$color-priority-medium: #3b82f6;
$color-priority-low: #10b981;
$color-text-primary: #1f2937;
$color-text-secondary: #6b7280;
$color-text-tertiary: #9ca3af;
$spacing-xs: 4px;
$spacing-sm: 8px;
$radius-sm: 4px;
$shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
$shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
$transition-fast: 0.15s ease;
$font-size-xs: 12px;
$font-size-sm: 14px;

.task-card {
  position: absolute;
  left: 4px;
  right: 4px;
  padding: $spacing-xs $spacing-sm;
  border-radius: $radius-sm;
  color: white;
  cursor: pointer;
  transition: all $transition-fast;
  overflow: hidden;
  z-index: 1;

  // Vertically center content
  display: flex;
  flex-direction: column;
  justify-content: center;

  &:hover {
    box-shadow: $shadow-md;
    transform: translateY(-1px);
    z-index: 2;
  }

  // Priority colors (full background)
  &.priority-high {
    background-color: $color-priority-high;
  }

  &.priority-medium {
    background-color: $color-priority-medium;
  }

  &.priority-low {
    background-color: $color-priority-low;
  }

  // Truncation effects
  &.truncated-top {
    border-top-left-radius: 0;
    border-top-right-radius: 0;

    // Zigzag top edge
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background:
        linear-gradient(135deg, transparent 25%, currentColor 25%) -5px 0,
        linear-gradient(225deg, transparent 25%, currentColor 25%) 5px 0,
        linear-gradient(315deg, transparent 25%, currentColor 25%) 5px 0,
        linear-gradient(45deg, transparent 25%, currentColor 25%) -5px 0;
      background-size: 10px 4px;
      background-repeat: repeat-x;
      opacity: 0.8;
    }
  }

  &.truncated-bottom {
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;

    // Zigzag bottom edge
    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      height: 4px;
      background:
        linear-gradient(135deg, currentColor 25%, transparent 25%) -5px 0,
        linear-gradient(225deg, currentColor 25%, transparent 25%) 5px 0,
        linear-gradient(315deg, currentColor 25%, transparent 25%) 5px 0,
        linear-gradient(45deg, currentColor 25%, transparent 25%) -5px 0;
      background-size: 10px 4px;
      background-repeat: repeat-x;
      opacity: 0.8;
    }
  }

  .task-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
    position: relative;
    z-index: 1;
    // Content vertically centered by parent flexbox
  }

  .task-time {
    font-size: $font-size-xs;
    opacity: 0.9;
    font-weight: 500;
  }

  .task-title {
    font-size: $font-size-xs;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  .task-project {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    font-size: 10px;
    opacity: 0.9;

    .project-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      border: 1px solid rgba(255, 255, 255, 0.5);
    }
  }

  .truncation-indicator {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    font-size: 10px;
    font-weight: 600;
    position: relative;
    z-index: 2;

    &.truncation-top {
      margin-bottom: $spacing-xs;
      padding-top: 6px;
    }

    &.truncation-bottom {
      margin-top: $spacing-xs;
      padding-bottom: 6px;
    }

    .truncation-arrow {
      font-size: 12px;
    }

    .truncation-time {
      opacity: 0.95;
    }
  }
}

// ============================================
// Popover Styles
// ============================================
.task-details {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  padding: $spacing-xs;

  .detail-item {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    font-size: $font-size-sm;

    .detail-label {
      color: $color-text-secondary;
      font-weight: 500;
      min-width: 48px;
    }

    .detail-value {
      color: $color-text-primary;
      display: flex;
      align-items: center;
      gap: $spacing-xs;

      .project-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
      }
    }
  }
}
</style>

<style lang="scss">
// Global style for Popover (not scoped)
.task-detail-popover {
  padding: 12px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}
</style>
