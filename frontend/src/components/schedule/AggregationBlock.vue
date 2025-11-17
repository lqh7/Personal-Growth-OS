<template>
  <div
    class="aggregation-block"
    :class="{ 'small-block': isSmallBlock }"
    :style="{ top: `${top}px`, height: `${height}px` }"
  >
    <!-- Display all task titles -->
    <div class="aggregation-content">
      <div v-if="showTitles" class="all-task-titles">{{ allTaskTitles }}</div>
    </div>

    <!-- Aggregation Badge with Popover -->
    <el-popover
      placement="right"
      :width="300"
      trigger="hover"
      popper-class="aggregation-popover"
    >
      <template #reference>
        <div class="aggregation-badge">
          +{{ tasks.length }}
        </div>
      </template>

      <!-- Popover Content: List all tasks in this time slot -->
      <div class="task-list">
        <div class="task-list-header">
          该时间段的任务 ({{ tasks.length }})
        </div>
        <div
          v-for="task in sortedTasks"
          :key="task.id"
          class="task-item"
          :class="getPriorityClass(task.priority)"
          @click="$emit('task-click', task)"
        >
          <div class="task-item-time">{{ formatTaskTime(task) }}</div>
          <div class="task-item-title">{{ task.title }}</div>
          <div v-if="task.project" class="task-item-project">
            <span
              class="project-dot"
              :style="{ backgroundColor: task.project.color }"
            ></span>
            {{ task.project.name }}
          </div>
        </div>
      </div>
    </el-popover>
  </div>
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
  top: number
  height: number
  tasks: Task[]
  displayTask: Task  // The highest priority task to display
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'task-click', task: Task): void
}>()

// ============================================
// Computed
// ============================================

const sortedTasks = computed(() => {
  // Sort tasks by priority (descending) then by start time
  return [...props.tasks].sort((a, b) => {
    if (a.priority !== b.priority) {
      return b.priority - a.priority // Higher priority first
    }
    if (!a.startTime || !b.startTime) return 0
    return new Date(a.startTime).getTime() - new Date(b.startTime).getTime()
  })
})

const allTaskTitles = computed(() => {
  // Join all task titles with "、"
  return props.tasks.map(task => task.title).join('、')
})

const showTitles = computed(() => {
  // Hide titles when height < 15px (duration < 15 minutes)
  return props.height >= 15
})

const isSmallBlock = computed(() => {
  // Small block when height < 10px (duration < 10 minutes)
  return props.height < 10
})

// ============================================
// Methods
// ============================================

function getPriorityClass(priority: number): string {
  if (priority >= 4) return 'priority-high'
  if (priority >= 2) return 'priority-medium'
  return 'priority-low'
}

function formatTaskTime(task: Task): string {
  if (!task.startTime || !task.endTime) return ''

  const start = new Date(task.startTime)
  const end = new Date(task.endTime)

  const formatTime = (date: Date) => {
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  }

  // Check if cross-day
  const isCrossDay = start.getDate() !== end.getDate() ||
                     start.getMonth() !== end.getMonth() ||
                     start.getFullYear() !== end.getFullYear()

  if (isCrossDay) {
    const startDate = `${start.getMonth() + 1}/${start.getDate()}`
    const endDate = `${end.getMonth() + 1}/${end.getDate()}`
    return `${startDate} ${formatTime(start)} → ${endDate} ${formatTime(end)}`
  } else {
    return `${formatTime(start)}-${formatTime(end)}`
  }
}
</script>

<style scoped lang="scss">
$color-aggregation: #2d3748;
$color-priority-high: #ef4444;
$color-priority-medium: #3b82f6;
$color-priority-low: #10b981;
$color-text-primary: #1f2937;
$color-text-secondary: #6b7280;
$color-text-tertiary: #9ca3af;
$color-border: #e5e7eb;
$bg-color-hover: #f9fafb;
$spacing-xs: 4px;
$spacing-sm: 8px;
$spacing-md: 12px;
$radius-sm: 4px;
$radius-round: 50%;
$shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
$shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
$transition-fast: 0.15s ease;
$font-size-xs: 12px;
$font-size-sm: 14px;

.aggregation-block {
  position: absolute;
  left: 4px;
  right: 4px;
  background-color: $color-aggregation;
  border-radius: $radius-sm;
  padding: $spacing-xs $spacing-sm;
  cursor: pointer;
  transition: all $transition-fast;

  // Vertically center content
  display: flex;
  flex-direction: column;
  justify-content: center;

  &:hover {
    background-color: lighten($color-aggregation, 10%);
  }

  // Small block: no padding for height < 10px
  &.small-block {
    padding: 0;
    justify-content: center;
  }

  .aggregation-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
    z-index: 1;
    padding-right: 30px; // Make space for badge
  }

  .all-task-titles {
    font-size: 10px;
    font-weight: 500;
    color: white;
    line-height: 1.4;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
  }

  .aggregation-badge {
    position: absolute;
    top: 4px;
    right: 4px;
    background-color: $color-text-secondary;
    color: white;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: $radius-round;
    cursor: pointer;
    z-index: 10;
    box-shadow: $shadow-sm;
    transition: all $transition-fast;

    &:hover {
      background-color: darken($color-text-secondary, 10%);
      transform: scale(1.1);
    }
  }
}

// ============================================
// Popover Content Styles
// ============================================
.task-list {
  .task-list-header {
    font-size: $font-size-sm;
    font-weight: 600;
    color: $color-text-primary;
    padding-bottom: $spacing-sm;
    margin-bottom: $spacing-sm;
    border-bottom: 1px solid $color-border;
  }

  .task-item {
    padding: $spacing-sm;
    margin-bottom: $spacing-xs;
    border-radius: $radius-sm;
    border-left: 3px solid;
    background-color: $bg-color-hover;
    cursor: pointer;
    transition: all $transition-fast;

    &:hover {
      background-color: darken($bg-color-hover, 5%);
      transform: translateX(2px);
    }

    &:last-child {
      margin-bottom: 0;
    }

    // Priority colors (border-left only)
    &.priority-high {
      border-left-color: $color-priority-high;
      background-color: rgba($color-priority-high, 0.05);
    }

    &.priority-medium {
      border-left-color: $color-priority-medium;
      background-color: rgba($color-priority-medium, 0.05);
    }

    &.priority-low {
      border-left-color: $color-priority-low;
      background-color: rgba($color-priority-low, 0.05);
    }

    .task-item-time {
      font-size: $font-size-xs;
      color: $color-text-tertiary;
      margin-bottom: $spacing-xs;
    }

    .task-item-title {
      font-size: $font-size-sm;
      font-weight: 500;
      color: $color-text-primary;
      margin-bottom: $spacing-xs;
    }

    .task-item-project {
      display: flex;
      align-items: center;
      gap: $spacing-xs;
      font-size: $font-size-xs;
      color: $color-text-secondary;

      .project-dot {
        width: 6px;
        height: 6px;
        border-radius: $radius-round;
      }
    }
  }
}
</style>

<style lang="scss">
// Global popover styles (not scoped)
.aggregation-popover {
  padding: 12px !important;
}
</style>
