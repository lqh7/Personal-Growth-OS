<template>
  <div class="week-schedule">
    <!-- Header with Week Navigation -->
    <div class="schedule-header">
      <el-button-group>
        <el-button @click="previousWeek">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <el-button @click="today">今天</el-button>
        <el-button @click="nextWeek">
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </el-button-group>

      <div class="week-range">
        {{ weekRangeText }}
      </div>
    </div>

    <!-- Schedule Grid -->
    <div class="schedule-grid">
      <!-- Time Column -->
      <div class="time-column">
        <div class="time-header">时间</div>
        <div
          v-for="hour in hours"
          :key="hour"
          class="time-slot"
        >
          {{ formatHour(hour) }}
        </div>
      </div>

      <!-- Day Columns -->
      <div
        v-for="(day, index) in weekDays"
        :key="day.date.toISOString()"
        class="day-column"
        :class="{ 'is-today': isToday(day.date) }"
      >
        <!-- Day Header -->
        <div class="day-header">
          <div class="day-name">{{ day.name }}</div>
          <div class="day-date" :class="{ 'is-today-date': isToday(day.date) }">
            {{ day.date.getDate() }}
          </div>
          <div class="day-task-count">{{ day.tasks.length }}</div>
        </div>

        <!-- Time Slots -->
        <div class="day-slots">
          <div
            v-for="hour in hours"
            :key="`${day.date.toISOString()}-${hour}`"
            class="time-slot"
            :data-slot-key="`${day.date.toISOString()}-${hour}`"
            @click="handleSlotClick(day.date, hour)"
            @dragover.prevent="handleDragOver($event)"
            @drop="handleDrop(day.date, hour, $event)"
          >
            <!-- Drag Preview Overlay -->
            <div v-if="dragOverSlot === `${day.date.toISOString()}-${hour}`" class="drag-preview">
              <div class="drag-preview-task">
                <div class="task-title">{{ draggingTask?.title }}</div>
                <div v-if="draggingTask?.project" class="task-project">
                  <span
                    class="project-dot"
                    :style="{ backgroundColor: draggingTask.project.color }"
                  ></span>
                  {{ draggingTask.project.name }}
                </div>
              </div>
            </div>

            <!-- Tasks in this time slot -->
            <div
              v-for="task in getTasksAtTime(day.tasks, hour)"
              :key="task.id"
              class="schedule-task"
              :class="[
                `priority-${task.priority}`,
                { 'is-completed': task.completed }
              ]"
              :style="{ height: calculateTaskHeight(task) }"
              @click.stop="handleTaskClick(task)"
            >
              <div class="task-time">{{ formatTaskTime(task) }}</div>
              <div class="task-title">{{ task.title }}</div>
              <div v-if="task.project" class="task-project">
                <span
                  class="project-dot"
                  :style="{ backgroundColor: task.project.color }"
                ></span>
                {{ task.project.name }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Floating Tasks (No Time) -->
    <div v-if="floatingTasks.length > 0" class="floating-tasks">
      <div class="floating-tasks-header">
        <span>📋 无时间任务（拖拽到日程表可指定时间）</span>
        <span class="task-count">{{ floatingTasks.length }}</span>
      </div>
      <div class="floating-tasks-list">
        <div
          v-for="task in floatingTasks"
          :key="task.id"
          class="floating-task-item"
          draggable="true"
          @dragstart="handleDragStart(task, $event)"
          @dragend="handleDragEnd"
          @click="handleTaskClick(task)"
        >
          <el-checkbox v-model="task.completed" @change="$emit('task-complete', task)" />
          <span class="task-title" :class="{ 'is-completed': task.completed }">
            {{ task.title }}
          </span>
          <el-button
            text
            size="small"
            @click.stop="$emit('task-snooze', task.id)"
          >
            <el-icon><Clock /></el-icon>
            延后
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ArrowLeft, ArrowRight, Clock } from '@element-plus/icons-vue'

// ============================================
// Types
// ============================================
interface Task {
  id: string
  title: string
  description?: string
  status: 'pending' | 'in_progress' | 'completed'
  priority: number
  dueDate?: Date
  startTime?: Date // Changed from dueTime
  endTime?: Date // New field
  completed: boolean
  project?: {
    id: string
    name: string
    color: string
  }
}

interface WeekDay {
  name: string
  date: Date
  tasks: Task[]
}

// ============================================
// Props & Emits
// ============================================
const props = defineProps<{
  tasks: Task[]
}>()

const emit = defineEmits<{
  (e: 'task-click', task: Task): void
  (e: 'task-complete', task: Task): void
  (e: 'task-snooze', taskId: string): void
  (e: 'slot-click', date: Date, hour: number): void
  (e: 'task-drop', taskId: string, date: Date, hour: number): void
}>()

// ============================================
// State
// ============================================
const currentWeekStart = ref(getStartOfWeek(new Date()))
const hours = Array.from({ length: 14 }, (_, i) => i + 8) // 8:00 - 21:00
const draggingTask = ref<Task | null>(null)
const dragOverSlot = ref<string | null>(null)

// ============================================
// Computed
// ============================================
const weekDays = computed<WeekDay[]>(() => {
  const days: WeekDay[] = []
  const dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

  for (let i = 0; i < 7; i++) {
    const date = new Date(currentWeekStart.value)
    date.setDate(date.getDate() + i)

    days.push({
      name: dayNames[i],
      date,
      tasks: getTasksForDay(date)
    })
  }

  return days
})

const weekRangeText = computed(() => {
  const start = currentWeekStart.value
  const end = new Date(start)
  end.setDate(end.getDate() + 6)

  const formatDate = (date: Date) => {
    return `${date.getMonth() + 1}月${date.getDate()}日`
  }

  return `${formatDate(start)} - ${formatDate(end)}`
})

const floatingTasks = computed(() => {
  return props.tasks.filter(task => !task.startTime && !task.completed)
})

// ============================================
// Methods
// ============================================
function getStartOfWeek(date: Date): Date {
  const d = new Date(date)
  const day = d.getDay()
  const diff = day === 0 ? -6 : 1 - day // Monday as first day
  d.setDate(d.getDate() + diff)
  d.setHours(0, 0, 0, 0)
  return d
}

function getTasksForDay(date: Date): Task[] {
  return props.tasks.filter(task => {
    if (!task.startTime) return false
    const taskDate = new Date(task.startTime)
    return (
      taskDate.getFullYear() === date.getFullYear() &&
      taskDate.getMonth() === date.getMonth() &&
      taskDate.getDate() === date.getDate()
    )
  })
}

function getTasksAtTime(dayTasks: Task[], hour: number): Task[] {
  return dayTasks.filter(task => {
    if (!task.startTime) return false
    const taskDate = new Date(task.startTime)
    return taskDate.getHours() === hour
  })
}

function calculateTaskHeight(task: Task): string {
  // If no end_time, default to 30 minutes (half slot)
  if (!task.endTime || !task.startTime) {
    return '30px'
  }

  const start = new Date(task.startTime)
  const end = new Date(task.endTime)
  const durationMinutes = (end.getTime() - start.getTime()) / (1000 * 60)

  // 60px per hour
  const height = (durationMinutes / 60) * 60
  return `${Math.max(height, 30)}px`
}

function formatHour(hour: number): string {
  return `${hour.toString().padStart(2, '0')}:00`
}

function formatTaskTime(task: Task): string {
  if (!task.startTime) return ''

  const start = new Date(task.startTime)
  const startStr = `${start.getHours().toString().padStart(2, '0')}:${start.getMinutes().toString().padStart(2, '0')}`

  if (!task.endTime) {
    return startStr
  }

  const end = new Date(task.endTime)
  const endStr = `${end.getHours().toString().padStart(2, '0')}:${end.getMinutes().toString().padStart(2, '0')}`

  return `${startStr}-${endStr}`
}

function isToday(date: Date): boolean {
  const today = new Date()
  return (
    date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate()
  )
}

function previousWeek() {
  const newDate = new Date(currentWeekStart.value)
  newDate.setDate(newDate.getDate() - 7)
  currentWeekStart.value = newDate
}

function nextWeek() {
  const newDate = new Date(currentWeekStart.value)
  newDate.setDate(newDate.getDate() + 7)
  currentWeekStart.value = newDate
}

function today() {
  currentWeekStart.value = getStartOfWeek(new Date())
}

function handleSlotClick(date: Date, hour: number) {
  emit('slot-click', date, hour)
}

function handleTaskClick(task: Task) {
  emit('task-click', task)
}

function handleDragStart(task: Task, event: DragEvent) {
  draggingTask.value = task
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('taskId', task.id)
    // Make drag image transparent to show preview instead
    const img = new Image()
    img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
    event.dataTransfer.setDragImage(img, 0, 0)
  }
}

function handleDragEnd() {
  draggingTask.value = null
  dragOverSlot.value = null
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }

  // Update drag preview position
  const target = event.currentTarget as HTMLElement
  if (target) {
    const slotKey = target.getAttribute('data-slot-key')
    if (slotKey) {
      dragOverSlot.value = slotKey
    }
  }
}

function handleDragLeave(event: DragEvent) {
  // Clear preview when leaving slot
  const target = event.currentTarget as HTMLElement
  const relatedTarget = event.relatedTarget as HTMLElement

  // Only clear if we're actually leaving the slot (not just entering a child)
  if (!target.contains(relatedTarget)) {
    dragOverSlot.value = null
  }
}

function handleDrop(date: Date, hour: number, event: DragEvent) {
  event.preventDefault()
  dragOverSlot.value = null
  const taskId = event.dataTransfer?.getData('taskId')
  if (taskId) {
    emit('task-drop', taskId, date, hour)
  }
  draggingTask.value = null
}
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';
@import '@/assets/styles/mixins.scss';

.week-schedule {
  display: flex;
  flex-direction: column;
  gap: $spacing-lg;
}

// ============================================
// Header
// ============================================
.schedule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: $spacing-md;
  border-bottom: 1px solid $color-border;

  .week-range {
    font-size: $font-size-md;
    font-weight: 600;
    color: $color-text-primary;
  }
}

// ============================================
// Schedule Grid
// ============================================
.schedule-grid {
  display: grid;
  grid-template-columns: 60px repeat(7, 1fr);
  gap: 0;
  border: 1px solid $color-border;
  border-radius: $radius-md;
  overflow: hidden;
  background-color: white;
}

// Time Column
.time-column {
  border-right: 1px solid $color-border;
  background-color: $bg-color-hover;

  .time-header {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: $font-size-xs;
    font-weight: 600;
    color: $color-text-secondary;
    border-bottom: 1px solid $color-border;
  }

  .time-slot {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: $font-size-xs;
    color: $color-text-tertiary;
    border-bottom: 1px solid $color-border;
  }
}

// Day Column
.day-column {
  border-right: 1px solid $color-border;
  position: relative;

  &:last-child {
    border-right: none;
  }

  &.is-today {
    background-color: rgba($color-primary, 0.02);

    .day-header {
      background-color: rgba($color-primary, 0.1);
    }
  }

  .day-header {
    height: 60px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: $spacing-xs;
    border-bottom: 1px solid $color-border;
    background-color: $bg-color-hover;

    .day-name {
      font-size: $font-size-xs;
      color: $color-text-secondary;
    }

    .day-date {
      font-size: $font-size-md;
      font-weight: 600;
      color: $color-text-primary;

      &.is-today-date {
        color: white;
        background-color: $color-primary;
        width: 28px;
        height: 28px;
        border-radius: $radius-round;
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }

    .day-task-count {
      font-size: $font-size-xs;
      color: $color-text-tertiary;
    }
  }

  .day-slots {
    .time-slot {
      height: 60px;
      border-bottom: 1px solid $color-border;
      position: relative;
      cursor: pointer;
      transition: background-color $transition-fast;

      &:hover {
        background-color: rgba($color-primary, 0.05);
      }
    }
  }
}

// ============================================
// Drag Preview
// ============================================
.drag-preview {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba($color-primary, 0.1);
  border: 2px dashed $color-primary;
  border-radius: $radius-sm;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  pointer-events: none;

  .drag-preview-task {
    background-color: white;
    padding: $spacing-sm;
    border-radius: $radius-sm;
    box-shadow: $shadow-md;
    max-width: 90%;

    .task-title {
      font-size: $font-size-sm;
      font-weight: 500;
      color: $color-text-primary;
      margin-bottom: $spacing-xs;
      @include text-ellipsis;
    }

    .task-project {
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

// ============================================
// Schedule Task
// ============================================
.schedule-task {
  position: absolute;
  left: 4px;
  right: 4px;
  top: 2px;
  padding: $spacing-xs $spacing-sm;
  border-radius: $radius-sm;
  border-left: 3px solid;
  background-color: white;
  box-shadow: $shadow-sm;
  cursor: pointer;
  transition: all $transition-fast;
  overflow: hidden;
  z-index: 1;

  &:hover {
    box-shadow: $shadow-md;
    transform: translateY(-1px);
    z-index: 2;
  }

  &.is-completed {
    opacity: 0.6;
    text-decoration: line-through;
  }

  // Priority colors
  &.priority-5,
  &.priority-4 {
    border-color: $color-danger;
    background-color: rgba($color-danger, 0.05);
  }

  &.priority-3,
  &.priority-2 {
    border-color: $color-warning;
    background-color: rgba($color-warning, 0.05);
  }

  &.priority-1,
  &.priority-0 {
    border-color: $color-primary;
    background-color: rgba($color-primary, 0.05);
  }

  .task-time {
    font-size: $font-size-xs;
    color: $color-text-tertiary;
    margin-bottom: 2px;
  }

  .task-title {
    font-size: $font-size-xs;
    font-weight: 500;
    color: $color-text-primary;
    margin-bottom: 2px;
    @include text-ellipsis;
  }

  .task-project {
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

// ============================================
// Floating Tasks
// ============================================
.floating-tasks {
  padding: $spacing-md;
  background-color: $bg-color-hover;
  border-radius: $radius-md;
  border: 2px dashed $color-border;

  .floating-tasks-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-md;
    font-size: $font-size-sm;
    font-weight: 500;
    color: $color-text-primary;

    .task-count {
      background-color: $color-primary;
      color: white;
      font-size: $font-size-xs;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: $radius-round;
    }
  }

  .floating-tasks-list {
    display: flex;
    flex-direction: column;
    gap: $spacing-sm;
  }

  .floating-task-item {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    padding: $spacing-sm $spacing-md;
    background-color: white;
    border-radius: $radius-sm;
    cursor: move;
    transition: all $transition-fast;

    &:hover {
      background-color: darken(white, 2%);
      box-shadow: $shadow-sm;
    }

    .task-title {
      flex: 1;
      font-size: $font-size-sm;
      color: $color-text-primary;

      &.is-completed {
        text-decoration: line-through;
        color: $color-text-tertiary;
      }
    }
  }
}
</style>
