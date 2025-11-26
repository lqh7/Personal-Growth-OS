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

    <!-- Schedule Container with Fixed Header -->
    <div class="schedule-container">
      <!-- Fixed Header Row (日期和全天) -->
      <div class="schedule-fixed-header">
        <div class="header-grid">
          <!-- Time Column Header -->
          <div class="time-column-header">
            <div class="time-header">
              <div class="date-label"></div>
            </div>
            <div class="all-day-label-row">
              <div class="all-day-label">全天</div>
            </div>
          </div>

          <!-- Day Headers -->
          <div
            v-for="day in weekDays"
            :key="`header-${day.date.toISOString()}`"
            class="day-column-header"
            :class="{ 'is-today': isToday(day.date) }"
          >
            <div class="day-header">
              <div class="day-name">{{ day.name }}</div>
              <div class="day-date" :class="{ 'is-today-date': isToday(day.date) }">
                {{ formatDayDate(day.date) }}
              </div>
            </div>
            <div class="all-day-events">
              <AllDayTaskCard
                v-if="day.allDayTasks.length === 1"
                :task="day.allDayTasks[0]"
                @task-click="handleTaskClick"
              />
              <AllDayAggregation
                v-else-if="day.allDayTasks.length > 1"
                :tasks="day.allDayTasks"
                @task-click="handleTaskClick"
              />
              <div v-else class="all-day-empty"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Scrollable Time Slots Area -->
      <div class="schedule-scroll-area">
        <div class="schedule-grid">
          <!-- Time Column -->
          <div class="time-column">
            <div
              v-for="hour in hours"
              :key="hour"
              class="time-slot"
            >
              {{ formatHour(hour) }}
            </div>
          </div>

          <!-- Day Columns (Time Slots Only) -->
          <div
            v-for="day in weekDays"
            :key="day.date.toISOString()"
            class="day-column"
            :class="{ 'is-today': isToday(day.date) }"
          >
            <div
              class="day-slots"
              @click="handleSlotClick(day.date, $event)"
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

              <!-- Render Items (TaskCard or AggregationBlock) -->
              <template v-for="item in day.renderItems" :key="item.id">
                <TaskCard
                  v-if="item.type === 'task'"
                  :task="item.task"
                  :top="item.top"
                  :height="item.height"
                  :render-start-time="item.renderStartTime"
                  :render-end-time="item.renderEndTime"
                  @task-click="handleTaskClick"
                />
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
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
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

// ============================================
// Props & Emits
// ============================================
const props = defineProps<{
  tasks: Task[]
}>()

const emit = defineEmits<{
  (e: 'task-click', task: Task): void
  (e: 'slot-click', date: Date, hour: number): void
}>()

// ============================================
// State
// ============================================
const currentWeekStart = ref(getStartOfWeek(new Date()))
const hours = Array.from({ length: 13 }, (_, i) => i + 8) // 8:00 - 20:00

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
// Schedule Container (包含固定头部和滚动区域)
// ============================================
.schedule-container {
  border: 1px solid $color-border;
  border-radius: $radius-md;
  overflow: hidden;
  background-color: white;
}

// ============================================
// Fixed Header (日期和全天行)
// ============================================
.schedule-fixed-header {
  background-color: white;
  border-bottom: 2px solid $color-border;

  .header-grid {
    display: grid;
    grid-template-columns: 60px repeat(7, 1fr);
    gap: 0;
  }

  .time-column-header {
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

      .all-day-label {
        font-size: 10px;
        font-weight: 600;
        color: $color-text-secondary;
      }
    }
  }

  .day-column-header {
    border-right: 1px solid $color-border;

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
      overflow-y: auto;
      overflow-x: hidden;
      background-color: $bg-color-hover;

      .all-day-empty {
        font-size: 10px;
        color: transparent;
        width: 100%;
      }
    }
  }
}

// ============================================
// Scrollable Area (时间槽)
// ============================================
.schedule-scroll-area {
  // 不设置固定max-height，让日程表完整显示所有时间槽
  // 如果需要在特定容器中限制高度，由父组件通过CSS控制
  overflow-y: visible;
  overflow-x: hidden;

  // 自定义滚动条（当父容器限制高度时生效）
  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: $bg-color-hover;
  }

  &::-webkit-scrollbar-thumb {
    background: $color-border;
    border-radius: 4px;

    &:hover {
      background: $color-text-tertiary;
    }
  }
}

// ============================================
// Schedule Grid (时间槽网格)
// ============================================
.schedule-grid {
  display: grid;
  grid-template-columns: 60px repeat(7, 1fr);
  gap: 0;
  background-color: white;
}

// ============================================
// Time Column (时间列)
// ============================================
.time-column {
  border-right: 1px solid $color-border;
  background-color: $bg-color-hover;

  .time-slot {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: $color-text-tertiary;
    border-top: 1px solid $color-border;

    &:first-child {
      border-top: none;
    }
  }
}

// ============================================
// Day Column (滚动区域内的日列 - 只包含时间槽)
// ============================================
.day-column {
  border-right: 1px solid $color-border;
  position: relative;

  &:last-child {
    border-right: none;
  }

  &.is-today {
    background-color: rgba($color-primary, 0.02);
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
  }
}
</style>
