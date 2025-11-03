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
            <template v-if="getTasksAtTime(day.tasks, day.date, hour).length > 0">
              <template v-for="(task, taskIndex) in getTasksAtTime(day.tasks, day.date, hour)" :key="task.id">
                <!-- Only show the first task, hide the rest -->
                <div
                  v-if="taskIndex === 0"
                  class="schedule-task"
                  :class="[
                    `priority-${task.priority}`,
                    { 'is-completed': task.completed, 'has-overflow': getActiveTasksAtTime(day.tasks, day.date, hour).length > 1 }
                  ]"
                  :style="{ height: calculateTaskHeight(task, day.date) }"
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

                  <!-- Overflow Badge: Show +N if there are active overlapping tasks -->
                  <el-popover
                    v-if="getActiveTasksAtTime(day.tasks, day.date, hour).length > 1"
                    placement="right"
                    :width="300"
                    trigger="hover"
                  >
                    <template #reference>
                      <div class="task-overflow-badge" @click.stop>
                        +{{ getActiveTasksAtTime(day.tasks, day.date, hour).length - 1 }}
                      </div>
                    </template>

                    <!-- Popover Content: List all active tasks in this time slot -->
                    <div class="task-overflow-list">
                      <div class="overflow-list-header">
                        该时间段的所有任务 ({{ getActiveTasksAtTime(day.tasks, day.date, hour).length }})
                      </div>
                      <div
                        v-for="overflowTask in getActiveTasksAtTime(day.tasks, day.date, hour)"
                        :key="overflowTask.id"
                        class="overflow-task-item"
                        :class="[`priority-${overflowTask.priority}`, { 'is-completed': overflowTask.completed }]"
                        @click="handleTaskClick(overflowTask)"
                      >
                        <div class="overflow-task-time">{{ formatTaskTime(overflowTask) }}</div>
                        <div class="overflow-task-title">{{ overflowTask.title }}</div>
                        <div v-if="overflowTask.project" class="overflow-task-project">
                          <span
                            class="project-dot"
                            :style="{ backgroundColor: overflowTask.project.color }"
                          ></span>
                          {{ overflowTask.project.name }}
                        </div>
                      </div>
                    </div>
                  </el-popover>
                </div>
              </template>
            </template>
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

    const taskStart = new Date(task.startTime)
    const taskEnd = task.endTime ? new Date(task.endTime) : new Date(taskStart.getTime() + 60 * 60 * 1000) // Default 1 hour

    // Create day boundaries (00:00 to 23:59:59.999)
    const dayStart = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 0, 0, 0, 0)
    const dayEnd = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 23, 59, 59, 999)

    // Check if task time range overlaps with this day
    // Task overlaps if: taskStart < dayEnd AND taskEnd > dayStart
    return taskStart < dayEnd && taskEnd > dayStart
  })
}

function getTasksAtTime(dayTasks: Task[], currentDate: Date, hour: number): Task[] {
  return dayTasks.filter(task => {
    if (!task.startTime) return false

    const taskStart = new Date(task.startTime)

    // Check if task starts on the current day
    const taskStartDate = new Date(taskStart.getFullYear(), taskStart.getMonth(), taskStart.getDate())
    const currentDayDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate())
    const isTaskStartDay = taskStartDate.getTime() === currentDayDate.getTime()

    if (isTaskStartDay) {
      // Task starts on this day: show only at its start hour
      return taskStart.getHours() === hour
    } else {
      // Task started on a previous day (cross-day task): show only at first hour (8:00)
      return hour === 8 // First hour in the schedule
    }
  })
}

function getActiveTasksAtTime(dayTasks: Task[], currentDate: Date, hour: number): Task[] {
  return dayTasks.filter(task => {
    if (!task.startTime) return false

    const taskStart = new Date(task.startTime)
    const taskEnd = task.endTime ? new Date(task.endTime) : new Date(taskStart.getTime() + 60 * 60 * 1000) // Default 1 hour

    // Create slot time boundaries (e.g., 8:00-9:00)
    const slotStart = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), hour, 0, 0, 0)
    const slotEnd = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), hour + 1, 0, 0, 0)

    // Task is active in this slot if: taskStart < slotEnd AND taskEnd > slotStart
    return taskStart < slotEnd && taskEnd > slotStart
  })
}

function calculateTaskHeight(task: Task, currentDate: Date): string {
  // If no end_time, default to 1 hour (60px full slot)
  if (!task.endTime || !task.startTime) {
    return '60px'
  }

  const taskStart = new Date(task.startTime)
  const taskEnd = new Date(task.endTime)

  // Check if task starts on the current day
  const taskStartDate = new Date(taskStart.getFullYear(), taskStart.getMonth(), taskStart.getDate())
  const currentDayDate = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate())
  const isTaskStartDay = taskStartDate.getTime() === currentDayDate.getTime()

  let effectiveStart: Date
  let effectiveEnd: Date

  if (isTaskStartDay) {
    // Task starts on this day
    effectiveStart = taskStart
    // If task ends on a later day, limit to end of current day
    const dayEnd = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), 23, 59, 59, 999)
    effectiveEnd = taskEnd > dayEnd ? dayEnd : taskEnd
  } else {
    // Task started on a previous day (cross-day task)
    // Start from beginning of current day (00:00)
    effectiveStart = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), 0, 0, 0, 0)
    // End at task end time or end of current day, whichever is earlier
    const dayEnd = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), 23, 59, 59, 999)
    effectiveEnd = taskEnd > dayEnd ? dayEnd : taskEnd
  }

  const durationMinutes = (effectiveEnd.getTime() - effectiveStart.getTime()) / (1000 * 60)

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

  // Check if task spans multiple days
  const isCrossDay = start.getDate() !== end.getDate() ||
                     start.getMonth() !== end.getMonth() ||
                     start.getFullYear() !== end.getFullYear()

  if (isCrossDay) {
    // Cross-day format: "11/3 20:00 → 11/4 10:00"
    const startDate = `${start.getMonth() + 1}/${start.getDate()}`
    const endDate = `${end.getMonth() + 1}/${end.getDate()}`
    const startTime = `${start.getHours().toString().padStart(2, '0')}:${start.getMinutes().toString().padStart(2, '0')}`
    const endTime = `${end.getHours().toString().padStart(2, '0')}:${end.getMinutes().toString().padStart(2, '0')}`

    return `${startDate} ${startTime} → ${endDate} ${endTime}`
  } else {
    // Same day format: "14:00-15:30"
    const endStr = `${end.getHours().toString().padStart(2, '0')}:${end.getMinutes().toString().padStart(2, '0')}`
    return `${startStr}-${endStr}`
  }
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

  // Overflow Badge
  .task-overflow-badge {
    position: absolute;
    top: 4px;
    right: 4px;
    background-color: $color-primary;
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
      background-color: darken($color-primary, 10%);
      transform: scale(1.1);
    }
  }

  // Add visual indicator when task has overflow
  &.has-overflow {
    &::after {
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      width: 0;
      height: 0;
      border-style: solid;
      border-width: 0 20px 20px 0;
      border-color: transparent rgba($color-primary, 0.2) transparent transparent;
      border-top-right-radius: $radius-sm;
    }
  }
}

// ============================================
// Task Overflow Popover List
// ============================================
.task-overflow-list {
  .overflow-list-header {
    font-size: $font-size-sm;
    font-weight: 600;
    color: $color-text-primary;
    padding-bottom: $spacing-sm;
    margin-bottom: $spacing-sm;
    border-bottom: 1px solid $color-border;
  }

  .overflow-task-item {
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

    .overflow-task-time {
      font-size: $font-size-xs;
      color: $color-text-tertiary;
      margin-bottom: $spacing-xs;
    }

    .overflow-task-title {
      font-size: $font-size-sm;
      font-weight: 500;
      color: $color-text-primary;
      margin-bottom: $spacing-xs;
    }

    .overflow-task-project {
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
