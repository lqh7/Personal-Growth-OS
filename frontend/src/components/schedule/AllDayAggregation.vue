<template>
  <div class="allday-aggregation">
    <!-- Display all task titles -->
    <div class="aggregation-content">
      <div class="all-task-titles">{{ allTaskTitles }}</div>
    </div>

    <!-- Aggregation Badge with Popover -->
    <el-popover
      placement="bottom"
      :width="300"
      trigger="hover"
      popper-class="allday-aggregation-popover"
    >
      <template #reference>
        <div class="aggregation-badge">
          +{{ tasks.length }}
        </div>
      </template>

      <!-- Popover Content: List all tasks -->
      <div class="task-list">
        <div class="task-list-header">
          全天任务 ({{ tasks.length }})
        </div>
        <div
          v-for="task in sortedTasks"
          :key="task.id"
          class="task-item"
          :class="getPriorityClass(task.priority)"
          @click="$emit('task-click', task)"
        >
          <div class="task-item-title">{{ task.title }}</div>
          <div class="task-item-time">{{ formatTaskTime(task) }}</div>
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
  tasks: Task[]
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

  const formatDate = (date: Date) => {
    return `${date.getMonth() + 1}/${date.getDate()}`
  }

  // Check if cross-day
  const isCrossDay = start.getDate() !== end.getDate() ||
                     start.getMonth() !== end.getMonth() ||
                     start.getFullYear() !== end.getFullYear()

  if (isCrossDay) {
    const startDate = formatDate(start)
    const endDate = formatDate(end)
    return `${startDate} ${formatTime(start)} → ${endDate} ${formatTime(end)}`
  } else {
    return `${formatTime(start)}-${formatTime(end)}`
  }
}
</script>

<style scoped lang="scss">
$color-aggregation: #e5e7eb;
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

.allday-aggregation {
  height: 100%;
  display: flex;
  align-items: center;
  background-color: $color-aggregation;
  border-radius: $radius-sm;
  padding: 2px 6px;
  cursor: pointer;
  transition: all $transition-fast;
  position: relative;

  &:hover {
    background-color: darken($color-aggregation, 5%);
  }

  .aggregation-content {
    flex: 1;
    display: flex;
    align-items: center;
    padding-right: 24px; // Make space for badge
    overflow: hidden;
  }

  .all-task-titles {
    font-size: 10px;
    font-weight: 500;
    color: $color-text-primary;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .aggregation-badge {
    position: absolute;
    right: 4px;
    top: 50%;
    transform: translateY(-50%);
    background-color: $color-text-secondary;
    color: white;
    font-size: 9px;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: $radius-round;
    cursor: pointer;
    z-index: 10;
    box-shadow: $shadow-sm;
    transition: all $transition-fast;

    &:hover {
      background-color: darken($color-text-secondary, 10%);
      transform: translateY(-50%) scale(1.1);
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

    .task-item-title {
      font-size: $font-size-sm;
      font-weight: 500;
      color: $color-text-primary;
      margin-bottom: $spacing-xs;
    }

    .task-item-time {
      font-size: $font-size-xs;
      color: $color-text-tertiary;
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
.allday-aggregation-popover {
  padding: 12px !important;
}
</style>
