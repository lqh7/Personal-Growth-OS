<template>
  <!-- All-Day Task Card with Detail Popover -->
  <el-popover
    placement="bottom"
    :width="250"
    trigger="hover"
    popper-class="allday-task-detail-popover"
  >
    <template #reference>
      <div
        class="schedule-allday-task-card"
        :style="taskStyle"
        @click="$emit('task-click', task)"
      >
        <span class="task-title">{{ task.title }}</span>
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
      <div v-if="task.project" class="detail-item">
        <span class="detail-label">项目:</span>
        <span class="detail-value">
          <span
            class="project-dot"
            :style="{ backgroundColor: task.project.color }"
          ></span>
          {{ task.project.name }}
        </span>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { computed } from 'vue'

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
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'task-click', task: Task): void
}>()

// ============================================
// Computed
// ============================================

// Helper function: Convert hex color to rgba with opacity
function hexToRgba(hex: string, opacity: number): string {
  hex = hex.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${opacity})`
}

const taskStyle = computed(() => {
  const hexColor = props.task.project?.color || '#667eea' // 默认紫色
  // 项目颜色 + 优先级透明度
  // 公式: 0.5 + (priority × 0.1)，范围 0.5-1.0
  // 优先级0=50%, 优先级5=100%
  const opacity = Math.min(1.0, 0.5 + (props.task.priority * 0.1))
  return {
    backgroundColor: hexToRgba(hexColor, opacity)
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
</script>

<style scoped lang="scss">
$color-priority-high: #ef4444;
$color-priority-medium: #3b82f6;
$color-priority-low: #10b981;
$color-text-primary: #1f2937;
$color-text-secondary: #6b7280;
$spacing-xs: 4px;
$spacing-sm: 8px;
$radius-sm: 4px;
$transition-fast: 0.15s ease;
$font-size-xs: 12px;
$font-size-sm: 14px;

// 使用独立的类名，避免与全局样式冲突
.schedule-allday-task-card {
  height: 100%;
  display: flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: $radius-sm;
  color: white;
  cursor: pointer;
  transition: all $transition-fast;
  white-space: nowrap;
  overflow: hidden;

  // 增强对比度
  border: 1px solid rgba(0, 0, 0, 0.2);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);

  // 禁用任何伪元素覆盖
  &::before,
  &::after {
    content: none !important;
    display: none !important;
  }

  &:hover {
    filter: brightness(1.1);
    transform: translateY(-1px);
  }

  .task-title {
    font-size: 10px;
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
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
.allday-task-detail-popover {
  padding: 12px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}
</style>
