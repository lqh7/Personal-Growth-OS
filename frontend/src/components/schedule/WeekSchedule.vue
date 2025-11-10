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
        <!-- Date Header Row -->
        <div class="time-header">
          <div class="date-label"></div>
        </div>

        <!-- All-day Label Row -->
        <div class="all-day-label-row">
          <div class="all-day-label">全天</div>
        </div>

        <!-- Time Slots -->
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
        v-for="day in weekDays"
        :key="day.date.toISOString()"
        class="day-column"
        :class="{ 'is-today': isToday(day.date) }"
      >
        <!-- Day Header (Date only, 45px) -->
        <div class="day-header">
          <div class="day-name">{{ day.name }}</div>
          <div class="day-date" :class="{ 'is-today-date': isToday(day.date) }">
            {{ formatDayDate(day.date) }}
          </div>
        </div>

        <!-- All-day Events Area (20px height, independent row) -->
        <div class="all-day-events">
          <!-- Single all-day task -->
          <AllDayTaskCard
            v-if="day.allDayTasks.length === 1"
            :task="day.allDayTasks[0]"
            @task-click="handleTaskClick"
          />

          <!-- Multiple all-day tasks (aggregation) -->
          <AllDayAggregation
            v-else-if="day.allDayTasks.length > 1"
            :tasks="day.allDayTasks"
            @task-click="handleTaskClick"
          />

          <!-- No all-day tasks (placeholder) -->
          <div v-else class="all-day-empty">

          </div>
        </div>

        <!-- Time Slots Container (780px = 13 hours × 60px) -->
        <div
          class="day-slots"
          @click="handleSlotClick(day.date, $event)"
          @dragover.prevent="handleDragOver($event, day.date)"
          @drop="handleDrop(day.date, $event)"
        >
          <!-- Hour Grid Lines (background) -->
          <div
            v-for="hour in hours"
            :key="`grid-${hour}`"
            class="hour-grid-line"
            :style="{ top: `${(hour - 8) * 60}px` }"
          ></div>

          <!-- Half-Hour Grid Lines (lighter, between full hours) -->
          <div
            v-for="hour in hours.slice(0, -1)"
            :key="`half-grid-${hour}`"
            class="half-hour-grid-line"
            :style="{ top: `${(hour - 8) * 60 + 30}px` }"
          ></div>

          <!-- Drag Preview Overlay -->
          <div
            v-if="dragPreview && dragPreview.date.toDateString() === day.date.toDateString()"
            class="drag-preview"
            :style="{ top: `${dragPreview.top}px`, height: '60px' }"
          >
            <div class="drag-preview-content">
              {{ draggingTask?.title }}
            </div>
          </div>

          <!-- Render Items (TaskCard or AggregationBlock) -->
          <template v-for="item in day.renderItems" :key="item.id">
            <!-- Independent Task: Use TaskCard -->
            <TaskCard
              v-if="item.type === 'task'"
              :task="item.task"
              :top="item.top"
              :height="item.height"
              :render-start-time="item.renderStartTime"
              :render-end-time="item.renderEndTime"
              @task-click="handleTaskClick"
            />

            <!-- Overlapping Tasks: Use AggregationBlock -->
            <AggregationBlock
              v-else-if="item.type === 'aggregation'"
              :tasks="item.tasks"
              :display-task="item.displayTask"
              :top="item.top"
              :height="item.height"
              @task-click="handleTaskClick"
            />
          </template>
        </div>
      </div>
    </div>

    <!-- Floating Tasks (No Time) - Always Visible -->
    <div
      class="floating-tasks"
      :class="{ 'is-drag-over': isDragOverFloatingArea }"
      @dragover.prevent="handleFloatingAreaDragOver"
      @dragleave="handleFloatingAreaDragLeave"
      @drop="handleFloatingAreaDrop"
    >
      <div class="floating-tasks-header">
        <span>📋 无时间任务（拖拽到日程表可指定时间）</span>
        <span v-if="floatingTasks.length > 0" class="task-count">{{ floatingTasks.length }}</span>
      </div>

      <!-- Task List (when tasks exist) -->
      <div v-if="floatingTasks.length > 0" class="floating-tasks-list">
        <div
          v-for="task in floatingTasks"
          :key="task.id"
          class="floating-task-item"
          draggable="true"
          @dragstart="handleDragStart(task, $event)"
          @dragend="handleDragEnd"
          @click="handleTaskClick(task)"
        >
          <el-checkbox
            v-model="task.completed"
            @change="$emit('task-complete', task)"
            @click.stop
          />
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

      <!-- Empty State (when no tasks) -->
      <div v-else class="floating-tasks-empty">
        <el-icon class="empty-icon"><Calendar /></el-icon>
        <p class="empty-title">暂无待办任务</p>
        <p class="empty-hint">将日程表上的任务拖到这里可标记为"稍后安排"</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ArrowLeft, ArrowRight, Clock, Calendar } from '@element-plus/icons-vue'
import TaskCard from './TaskCard.vue'
import AggregationBlock from './AggregationBlock.vue'
import AllDayTaskCard from './AllDayTaskCard.vue'
import AllDayAggregation from './AllDayAggregation.vue'

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
  startTime?: Date
  endTime?: Date
  completed: boolean
  project?: {
    id: string
    name: string
    color: string
  }
}

interface TaskRenderItem {
  type: 'task'
  id: string
  task: Task
  top: number
  height: number
  renderStartTime: Date
  renderEndTime: Date
}

interface AggregationRenderItem {
  type: 'aggregation'
  id: string
  tasks: Task[]
  displayTask: Task
  top: number
  height: number
}

type RenderItem = TaskRenderItem | AggregationRenderItem

interface WeekDay {
  name: string
  date: Date
  tasks: Task[]
  allDayTasks: Task[]
  renderItems: RenderItem[]
}

interface DragPreview {
  date: Date
  top: number
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
const hours = Array.from({ length: 13 }, (_, i) => i + 8) // 8:00 - 20:00
const draggingTask = ref<Task | null>(null)
const dragPreview = ref<DragPreview | null>(null)
const isDragOverFloatingArea = ref(false)

// Constants
const SCHEDULE_START_HOUR = 8
const SCHEDULE_END_HOUR = 21
const MINUTES_PER_PIXEL = 1 // 1 minute = 1 px

// ============================================
// Computed
// ============================================
const weekDays = computed<WeekDay[]>(() => {
  const days: WeekDay[] = []
  const dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

  for (let i = 0; i < 7; i++) {
    const date = new Date(currentWeekStart.value)
    date.setDate(date.getDate() + i)

    const dayTasks = getTasksForDay(date)
    const allDayTasks = dayTasks.filter(t => isAllDayTask(t, date))
    const timedTasks = dayTasks.filter(t => !isAllDayTask(t, date))

    days.push({
      name: dayNames[i],
      date,
      tasks: dayTasks,
      allDayTasks,
      renderItems: computeRenderItems(timedTasks, date)
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
// Sweep Line Algorithm for Overlap Detection
// ============================================
interface TimeEvent {
  time: number  // Minutes from schedule start
  type: 'start' | 'end'
  task: Task
}

function computeRenderItems(tasks: Task[], currentDate: Date): RenderItem[] {
  if (tasks.length === 0) return []

  const renderItems: RenderItem[] = []

  // Build time events for sweep line
  const events: TimeEvent[] = []

  tasks.forEach(task => {
    if (!task.startTime) return

    const taskStart = new Date(task.startTime)
    const taskEnd = task.endTime ? new Date(task.endTime) : new Date(taskStart.getTime() + 60 * 60 * 1000)

    // Calculate render boundaries within schedule (8:00 - 21:00)
    const scheduleStart = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), SCHEDULE_START_HOUR, 0, 0)
    const scheduleEnd = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), SCHEDULE_END_HOUR, 0, 0)

    const renderStart = taskStart < scheduleStart ? scheduleStart : taskStart
    const renderEnd = taskEnd > scheduleEnd ? scheduleEnd : taskEnd

    // Skip if task is completely outside schedule
    if (renderEnd <= scheduleStart || renderStart >= scheduleEnd) return

    // Convert to minutes from schedule start
    const startMinutes = Math.floor((renderStart.getTime() - scheduleStart.getTime()) / (1000 * 60))
    const endMinutes = Math.floor((renderEnd.getTime() - scheduleStart.getTime()) / (1000 * 60))

    events.push({ time: startMinutes, type: 'start', task })
    events.push({ time: endMinutes, type: 'end', task })
  })

  // Sort events by time, then by type (end before start to avoid false overlap)
  events.sort((a, b) => {
    if (a.time !== b.time) return a.time - b.time
    return a.type === 'end' ? -1 : 1
  })

  // Sweep line to detect overlapping segments
  const activeTasksSet = new Set<Task>()
  let lastTime = 0

  for (let i = 0; i < events.length; i++) {
    const event = events[i]

    // Before processing this event, check if we need to render segment from lastTime to event.time
    if (activeTasksSet.size > 0 && event.time > lastTime) {
      const segmentTasks = Array.from(activeTasksSet)
      const top = lastTime * MINUTES_PER_PIXEL
      const height = (event.time - lastTime) * MINUTES_PER_PIXEL

      if (segmentTasks.length === 1) {
        // Independent task
        const task = segmentTasks[0]
        const taskStart = new Date(task.startTime!)
        const taskEnd = task.endTime ? new Date(task.endTime) : new Date(taskStart.getTime() + 60 * 60 * 1000)

        const scheduleStart = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), SCHEDULE_START_HOUR, 0, 0)
        const scheduleEnd = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), SCHEDULE_END_HOUR, 0, 0)
        const renderStartTime = taskStart < scheduleStart ? scheduleStart : taskStart
        const renderEndTime = taskEnd > scheduleEnd ? scheduleEnd : taskEnd

        renderItems.push({
          type: 'task',
          id: `task-${task.id}-${lastTime}`,
          task,
          top,
          height,
          renderStartTime,
          renderEndTime
        })
      } else {
        // Overlapping tasks: create aggregation block
        // Find highest priority task to display
        const highestPriorityTask = segmentTasks.reduce((max, task) =>
          task.priority > max.priority ? task : max
        , segmentTasks[0])

        renderItems.push({
          type: 'aggregation',
          id: `agg-${lastTime}-${event.time}`,
          tasks: segmentTasks,
          displayTask: highestPriorityTask,
          top,
          height
        })
      }
    }

    // Process event
    if (event.type === 'start') {
      activeTasksSet.add(event.task)
    } else {
      activeTasksSet.delete(event.task)
    }

    lastTime = event.time
  }

  // Merge consecutive items of the same type
  return mergeConsecutiveItems(renderItems)
}

function mergeConsecutiveItems(items: RenderItem[]): RenderItem[] {
  if (items.length === 0) return []

  const merged: RenderItem[] = []
  let current = items[0]

  for (let i = 1; i < items.length; i++) {
    const next = items[i]

    // Check if can merge
    const canMerge =
      current.type === next.type &&
      current.top + current.height === next.top &&
      (current.type === 'task'
        ? current.task.id === (next as TaskRenderItem).task.id
        : setsEqual(
            new Set(current.tasks.map(t => t.id)),
            new Set((next as AggregationRenderItem).tasks.map(t => t.id))
          ))

    if (canMerge) {
      // Merge: extend height
      current.height += next.height
      if (current.type === 'task') {
        current.renderEndTime = (next as TaskRenderItem).renderEndTime
      }
    } else {
      merged.push(current)
      current = next
    }
  }

  merged.push(current)
  return merged
}

function arraysEqual(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false
  }
  return true
}

function setsEqual(a: Set<string>, b: Set<string>): boolean {
  if (a.size !== b.size) return false
  for (const item of a) {
    if (!b.has(item)) return false
  }
  return true
}

// ============================================
// Helper Functions
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
    const taskEnd = task.endTime ? new Date(task.endTime) : new Date(taskStart.getTime() + 60 * 60 * 1000)

    // Create day boundaries (00:00 to 23:59:59.999)
    const dayStart = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 0, 0, 0, 0)
    const dayEnd = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 23, 59, 59, 999)

    // Task overlaps with this day if: taskStart < dayEnd AND taskEnd > dayStart
    return taskStart < dayEnd && taskEnd > dayStart
  })
}

function isAllDayTask(task: Task, currentDate: Date): boolean {
  // All-day task: starts at or before 8:00 AND ends at or after 21:00 on the given date
  if (!task.startTime) return false

  const taskStart = new Date(task.startTime)
  const taskEnd = task.endTime ? new Date(task.endTime) : new Date(taskStart.getTime() + 60 * 60 * 1000)

  // Create day boundaries (8:00 and 21:00 of currentDate)
  const day8am = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), 8, 0, 0)
  const day9pm = new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), 21, 0, 0)

  // Task is all-day if it starts at or before 8:00 AND ends at or after 21:00
  return taskStart <= day8am && taskEnd >= day9pm
}

function formatHour(hour: number): string {
  return `${hour.toString().padStart(2, '0')}:00`
}

function formatDayDate(date: Date): string {
  const month = date.getMonth() + 1
  const day = date.getDate()
  return `${month}月${day}日`
}

function isToday(date: Date): boolean {
  const today = new Date()
  return (
    date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate()
  )
}

function getPriorityClass(priority: number): string {
  if (priority >= 4) return 'priority-high'
  if (priority >= 2) return 'priority-medium'
  return 'priority-low'
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

function handleSlotClick(date: Date, event: MouseEvent) {
  const target = event.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const clickY = event.clientY - rect.top

  // Calculate hour from click position (60px per hour)
  const minutesFromStart = Math.floor(clickY / MINUTES_PER_PIXEL)
  const hour = SCHEDULE_START_HOUR + Math.floor(minutesFromStart / 60)

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
    // Transparent drag image
    const img = new Image()
    img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
    event.dataTransfer.setDragImage(img, 0, 0)
  }
}

function handleDragEnd() {
  draggingTask.value = null
  dragPreview.value = null
}

function handleDragOver(event: DragEvent, date: Date) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }

  // Calculate preview position
  const target = event.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const offsetY = event.clientY - rect.top

  // Snap to 15-minute boundaries (more flexible than hourly)
  const minutesFromStart = Math.floor(offsetY / MINUTES_PER_PIXEL)
  const snappedMinutes = Math.floor(minutesFromStart / 15) * 15
  const top = snappedMinutes * MINUTES_PER_PIXEL

  dragPreview.value = { date, top }
}

function handleDrop(date: Date, event: DragEvent) {
  event.preventDefault()

  const taskId = event.dataTransfer?.getData('taskId')
  if (!taskId) return

  // Calculate time from drop position with 15-minute precision
  const target = event.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const offsetY = event.clientY - rect.top
  const minutesFromStart = Math.floor(offsetY / MINUTES_PER_PIXEL)
  // Snap to 15-minute boundaries
  const snappedMinutes = Math.floor(minutesFromStart / 15) * 15
  const hour = SCHEDULE_START_HOUR + Math.floor(snappedMinutes / 60)
  const minute = snappedMinutes % 60

  emit('task-drop', taskId, date, hour, minute)

  dragPreview.value = null
  draggingTask.value = null
}

// ============================================
// Floating Area Drag Handlers
// ============================================
function handleFloatingAreaDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
  isDragOverFloatingArea.value = true
}

function handleFloatingAreaDragLeave() {
  isDragOverFloatingArea.value = false
}

function handleFloatingAreaDrop(event: DragEvent) {
  event.preventDefault()
  isDragOverFloatingArea.value = false

  const taskId = event.dataTransfer?.getData('taskId')
  if (!taskId) return

  // Emit event to remove time from task (convert to floating task)
  emit('task-drop', taskId, null as any, -1, -1) // Special signal: -1 means remove time

  draggingTask.value = null
}
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';
@import '@/assets/styles/mixins.scss';

// Color constants
$color-priority-high: #ef4444;
$color-priority-medium: #3b82f6;
$color-priority-low: #10b981;
$color-aggregation: #e5e7eb;

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

// ============================================
// Time Column
// ============================================
.time-column {
  border-right: 1px solid $color-border;
  background-color: $bg-color-hover;

  .time-header {
    height: 45px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid $color-border;

    .date-label {
      font-size: 10px;
      color: $color-text-secondary;
    }
  }

  .all-day-label-row {
    height: 25px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: 1px solid $color-border;

    .all-day-label {
      font-size: 10px;
      font-weight: 600;
      color: $color-text-secondary;
    }
  }

  .time-slot {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: $color-text-tertiary;
    border-top: 1px solid $color-border;
  }
}

// ============================================
// Day Column
// ============================================
.day-column {
  border-right: 1px solid $color-border;
  position: relative;

  &:last-child {
    border-right: none;
  }

  &.is-today {
    background-color: rgba($color-primary, 0.02);

    .day-header {
      background-color: rgba($color-primary, 0.05);
    }

    .all-day-events {
      background-color: rgba($color-primary, 0.03);
    }
  }

  .day-header {
    height: 45px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    border-bottom: 1px solid $color-border;
    background-color: $bg-color-hover;

    .day-name {
      font-size: 14px;
      font-weight: 600;
      color: $color-text-primary;
    }

    .day-date {
      font-size: 12px;
      font-weight: 400;
      color: $color-text-secondary;

      &.is-today-date {
        color: white;
        background-color: $color-primary;
        padding: 2px 8px;
        border-radius: $radius-sm;
        font-weight: 500;
      }
    }
  }

  .all-day-events {
    min-height: 25px;
    max-height: 25px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: $spacing-xs;
    border-bottom: 1px solid $color-border;
    overflow-y: auto;
    overflow-x: hidden;
    background-color: $bg-color-hover;

    .all-day-empty {
      font-size: 10px;
      color: transparent;
      width: 100%;
    }
  }

  .day-slots {
    position: relative;
    height: 780px; // 13 hours × 60px
    background-color: white;
    cursor: pointer;

    &:hover {
      background-color: rgba($color-primary, 0.01);
    }

    // Hour grid lines (background)
    .hour-grid-line {
      position: absolute;
      left: 0;
      right: 0;
      height: 0;
      border-top: 1px solid $color-border;
      pointer-events: none;
      z-index: 0;
    }

    .half-hour-grid-line {
      position: absolute;
      left: 0;
      right: 0;
      height: 0;
      border-top: 1px dashed rgba($color-border, 0.5);
      pointer-events: none;
      z-index: 0;
    }

    // Drag preview
    .drag-preview {
      position: absolute;
      left: 4px;
      right: 4px;
      background-color: rgba($color-primary, 0.1);
      border: 2px dashed $color-primary;
      border-radius: $radius-sm;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 5;
      pointer-events: none;

      .drag-preview-content {
        background-color: white;
        padding: $spacing-xs $spacing-sm;
        border-radius: $radius-sm;
        font-size: 12px;
        font-weight: 500;
        color: $color-text-primary;
        box-shadow: $shadow-sm;
        max-width: 90%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
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
  transition: all $transition-fast;

  // Drag-over feedback
  &.is-drag-over {
    border-color: $color-primary;
    background-color: rgba($color-primary, 0.05);
    box-shadow: 0 0 0 4px rgba($color-primary, 0.1);
  }

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
      font-size: 12px;
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

  // Empty State
  .floating-tasks-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: $spacing-xl $spacing-md;
    text-align: center;

    .empty-icon {
      font-size: 48px;
      color: $color-text-tertiary;
      margin-bottom: $spacing-md;
    }

    .empty-title {
      margin: 0 0 $spacing-xs 0;
      font-size: $font-size-md;
      font-weight: 500;
      color: $color-text-secondary;
    }

    .empty-hint {
      margin: 0;
      font-size: $font-size-sm;
      color: $color-text-tertiary;
      line-height: 1.5;
    }
  }
}
</style>
