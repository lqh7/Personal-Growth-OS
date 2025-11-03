<template>
  <div class="dashboard-view">
    <!-- Header -->
    <div class="dashboard-header">
      <div class="header-left">
        <h1 class="page-title">工作台</h1>
        <p class="page-subtitle">{{ currentDate }} · {{ greeting }}</p>
      </div>
    </div>

    <!-- Statistics Cards -->
    <div class="stats-grid">
      <div
        v-for="stat in stats"
        :key="stat.key"
        class="stat-card"
        :class="stat.key"
        @click="handleStatClick(stat.key)"
      >
        <div class="stat-icon">{{ stat.icon }}</div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
        <div class="stat-trend" :class="stat.trend">
          {{ stat.trendText }}
        </div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="content-grid">
      <!-- Week Schedule -->
      <div class="schedule-section card">
        <div class="section-header">
          <h3 class="section-title">本周日程</h3>
          <el-button text type="primary" @click="router.push('/tasks')">查看更多</el-button>
        </div>
        <WeekSchedule
          :tasks="calendarTasks"
          @task-click="handleTaskClick"
          @task-complete="handleTaskComplete"
          @task-snooze="handleTaskSnooze"
          @slot-click="handleSlotClick"
          @task-drop="handleTaskDrop"
        />
      </div>

      <!-- Floating Tasks -->
      <div class="floating-tasks-section card">
        <div class="section-header">
          <h3 class="section-title">
            悬浮任务
            <el-tooltip content="已延后的任务将在这里显示" placement="top">
              <el-icon class="info-icon"><InfoFilled /></el-icon>
            </el-tooltip>
          </h3>
          <span class="task-count">{{ floatingTasks.length }}</span>
        </div>
        <div class="task-list">
          <div
            v-for="task in floatingTasks"
            :key="task.id"
            class="floating-task-item"
            draggable="true"
            @dragstart="handleDragStart(task, $event)"
            @click="handleTaskClick(task.id)"
          >
            <div class="task-checkbox">
              <el-checkbox v-model="task.completed" @change="handleTaskComplete(task)" />
            </div>
            <div class="task-main">
              <div class="task-title">{{ task.title }}</div>
              <div class="task-meta">
                <span class="task-project" v-if="task.project">
                  <el-tag size="small" :color="task.project.color">
                    {{ task.project.name }}
                  </el-tag>
                </span>
                <span class="task-snooze">
                  <el-icon><Clock /></el-icon>
                  延后至 {{ formatSnoozeTime(task.snoozeUntil) }}
                </span>
              </div>
            </div>
          </div>
          <div v-if="floatingTasks.length === 0" class="empty-state">
            <el-icon><SuccessFilled /></el-icon>
            <p>太棒了！没有延后的任务</p>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="activity-section card">
        <div class="section-header">
          <h3 class="section-title">最近动态</h3>
          <el-button text type="primary">查看全部</el-button>
        </div>
        <div class="activity-list">
          <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
            <div class="activity-icon" :class="activity.type">
              {{ getActivityIcon(activity.type) }}
            </div>
            <div class="activity-content">
              <div class="activity-title">{{ activity.title }}</div>
              <div class="activity-time">{{ formatActivityTime(activity.timestamp) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Clock,
  InfoFilled,
  SuccessFilled
} from '@element-plus/icons-vue'
import WeekSchedule from '@/components/schedule/WeekSchedule.vue'
import { useTaskStore } from '@/stores/taskStore'
import { useProjectStore } from '@/stores/projectStore'
import { useTaskAdapter, type ViewTask } from '@/composables/useTaskAdapter'

// ============================================
// Types
// ============================================
interface Stat {
  key: string
  icon: string
  label: string
  value: number
  trend: 'up' | 'down' | 'neutral'
  trendText: string
}

interface FloatingTask {
  id: string
  title: string
  completed: boolean
  snoozeUntil: Date
  project?: {
    name: string
    color: string
  }
}

interface Activity {
  id: string
  type: 'task_created' | 'task_completed' | 'note_created' | 'review_generated'
  title: string
  timestamp: Date
}

// ============================================
// Stores
// ============================================
const router = useRouter()
const taskStore = useTaskStore()
const projectStore = useProjectStore()
const { toViewTask, toApiTask } = useTaskAdapter()

// ============================================
// Lifecycle
// ============================================
onMounted(async () => {
  await loadTasks()
})

async function loadTasks() {
  try {
    await Promise.all([
      taskStore.fetchTasks(),
      projectStore.fetchProjects()
    ])
  } catch (error) {
    ElMessage.error('加载任务失败')
  }
}

// ============================================
// State - Mock Data (Activities only - stats are computed)
// ============================================

// Computed stats from task store
const stats = computed<Stat[]>(() => {
  const now = new Date()
  const weekStart = new Date(now)
  weekStart.setDate(now.getDate() - now.getDay() + 1) // Monday
  weekStart.setHours(0, 0, 0, 0)

  const pendingCount = taskStore.tasks.filter(t => t.status === 'pending').length
  const overdueCount = taskStore.tasks.filter(t => {
    if (t.status === 'completed' || !t.due_date) return false
    return new Date(t.due_date) < now
  }).length
  const weekCompletedCount = taskStore.tasks.filter(t => {
    if (t.status !== 'completed' || !t.completed_at) return false
    return new Date(t.completed_at) >= weekStart
  }).length
  const weekTotalCount = taskStore.tasks.filter(t => {
    if (!t.created_at) return false
    return new Date(t.created_at) >= weekStart
  }).length
  const inProgressCount = taskStore.tasks.filter(t => t.status === 'in_progress').length

  const completionRate = weekTotalCount > 0 ? Math.round((weekCompletedCount / weekTotalCount) * 100) : 0

  return [
    {
      key: 'pending',
      icon: '📋',
      label: '待办任务',
      value: pendingCount,
      trend: 'neutral',
      trendText: `进行中 ${inProgressCount}`
    },
    {
      key: 'overdue',
      icon: '⚠️',
      label: '逾期任务',
      value: overdueCount,
      trend: overdueCount > 0 ? 'down' : 'neutral',
      trendText: overdueCount > 0 ? '需要关注' : '无逾期'
    },
    {
      key: 'completed',
      icon: '✅',
      label: '本周完成',
      value: weekCompletedCount,
      trend: 'up',
      trendText: `完成率 ${completionRate}%`
    },
    {
      key: 'week_total',
      icon: '📊',
      label: '本周总计',
      value: weekTotalCount,
      trend: 'neutral',
      trendText: `进行中 ${inProgressCount}`
    }
  ]
})

// Floating tasks - tasks that are snoozed
const floatingTasks = computed<FloatingTask[]>(() => {
  const now = new Date()
  return taskStore.tasks
    .filter(task => task.snooze_until && new Date(task.snooze_until) > now && task.status !== 'completed')
    .map(task => {
      const viewTask = toViewTask(task)
      return {
        id: viewTask.id,
        title: viewTask.title,
        completed: viewTask.completed,
        snoozeUntil: viewTask.snoozeUntil!,
        project: viewTask.project
      }
    })
})

const recentActivities = ref<Activity[]>([])

// Calendar tasks - all active tasks (completed/snoozed excluded)
const calendarTasks = computed(() => {
  const now = new Date()
  return taskStore.tasks
    .filter(task => {
      // Exclude completed tasks
      if (task.status === 'completed') return false
      // Exclude snoozed tasks (they appear in floating tasks)
      if (task.snooze_until && new Date(task.snooze_until) > now) return false
      // Include ALL active tasks (with or without start_time)
      return true
    })
    .map(task => toViewTask(task))
})

// ============================================
// Computed
// ============================================
const currentDate = computed(() => {
  const now = new Date()
  return now.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了，注意休息'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  if (hour < 22) return '晚上好'
  return '夜深了，注意休息'
})

// ============================================
// Methods
// ============================================
function handleStatClick(key: string) {
  ElMessage.info(`点击了统计卡片: ${key}`)
  router.push('/tasks')
}

function handleTaskClick(taskId: string) {
  ElMessage.info(`点击了任务: ${taskId}`)
}

async function handleTaskComplete(task: FloatingTask) {
  try {
    const newStatus = task.completed ? 'completed' : 'pending'
    await taskStore.updateTask(Number(task.id), { status: newStatus })
    if (task.completed) {
      ElMessage.success(`任务"${task.title}"已完成！`)
    } else {
      ElMessage.success('任务已恢复')
    }
  } catch (error) {
    ElMessage.error('更新任务状态失败')
  }
}

function formatSnoozeTime(date: Date): string {
  const now = new Date()
  const diff = date.getTime() - now.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}天后`
  if (hours > 0) return `${hours}小时后`
  return '即将到来'
}

function formatActivityTime(date: Date): string {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days}天前`
  if (hours > 0) return `${hours}小时前`
  if (minutes > 0) return `${minutes}分钟前`
  return '刚刚'
}

function getActivityIcon(type: Activity['type']): string {
  const icons: Record<Activity['type'], string> = {
    task_created: '➕',
    task_completed: '✅',
    note_created: '📝',
    review_generated: '📊'
  }
  return icons[type] || '•'
}

function handleTaskSnooze(taskId: string) {
  ElMessage.info(`延后任务: ${taskId}`)
}

function handleSlotClick(date: Date, hour: number) {
  ElMessage.info(`点击了时间槽: ${date.toLocaleDateString()} ${hour}:00`)
}

function handleDragStart(task: FloatingTask, event: DragEvent) {
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('taskId', task.id)
  }
}

async function handleTaskDrop(taskId: string, date: Date, hour: number) {
  try {
    // Create start time with correct date and hour
    // IMPORTANT: Use date's year/month/day to avoid date jumping bug
    const startTime = new Date(
      date.getFullYear(),
      date.getMonth(),
      date.getDate(),
      hour,
      0,
      0,
      0
    )

    // Set end time (default to 1 hour after start)
    const endTime = new Date(
      date.getFullYear(),
      date.getMonth(),
      date.getDate(),
      hour + 1,
      0,
      0,
      0
    )

    // Update task: set start_time, end_time, and clear snooze
    await taskStore.updateTask(Number(taskId), {
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      snooze_until: null
    })

    ElMessage.success(`任务已安排到 ${date.toLocaleDateString('zh-CN')} ${hour}:00`)
    await loadTasks() // Reload tasks to reflect changes
  } catch (error) {
    ElMessage.error('更新任务时间失败')
  }
}
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';
@import '@/assets/styles/mixins.scss';

.dashboard-view {
  max-width: 1400px;
  margin: 0 auto;
}

// ============================================
// Header
// ============================================
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: $spacing-xl;

  .header-left {
    .page-title {
      font-size: $font-size-xxl;
      font-weight: 600;
      color: $color-text-primary;
      margin: 0 0 $spacing-xs 0;
    }

    .page-subtitle {
      font-size: $font-size-sm;
      color: $color-text-secondary;
      margin: 0;
    }
  }

  .header-right {
    display: flex;
    gap: $spacing-md;
  }
}

// ============================================
// Statistics Grid
// ============================================
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: $spacing-lg;
  margin-bottom: $spacing-xl;
}

.stat-card {
  @include card-base;
  display: flex;
  align-items: center;
  gap: $spacing-lg;
  padding: $spacing-lg;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    transform: translateY(-2px);
    box-shadow: $shadow-lg;
  }

  .stat-icon {
    font-size: 36px;
    line-height: 1;
  }

  .stat-content {
    flex: 1;

    .stat-value {
      font-size: $font-size-xxl;
      font-weight: 600;
      color: $color-text-primary;
      line-height: 1.2;
    }

    .stat-label {
      font-size: $font-size-sm;
      color: $color-text-secondary;
      margin-top: $spacing-xs;
    }
  }

  .stat-trend {
    font-size: $font-size-xs;
    padding: $spacing-xs $spacing-sm;
    border-radius: $radius-sm;
    white-space: nowrap;

    &.up {
      background-color: rgba(102, 126, 234, 0.1);
      color: $color-primary;
    }

    &.down {
      background-color: rgba(245, 108, 108, 0.1);
      color: $color-danger;
    }

    &.neutral {
      background-color: $bg-color-hover;
      color: $color-text-secondary;
    }
  }

  // 不同卡片的渐变效果
  &.pending {
    border-left: 4px solid $color-primary;
  }

  &.overdue {
    border-left: 4px solid $color-danger;
  }

  &.completed {
    border-left: 4px solid $color-success;
  }

  &.week_total {
    border-left: 4px solid $color-info;
  }
}

// ============================================
// Content Grid
// ============================================
.content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: $spacing-lg;

  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
}

.card {
  @include card-base;
  padding: $spacing-lg;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-lg;

  .section-title {
    font-size: $font-size-lg;
    font-weight: 600;
    color: $color-text-primary;
    margin: 0;
    display: flex;
    align-items: center;
    gap: $spacing-xs;

    .info-icon {
      font-size: $font-size-md;
      color: $color-text-tertiary;
      cursor: help;
    }
  }
}

// ============================================
// Schedule Section
// ============================================
.schedule-section {
  grid-column: 1 / -1;
}

// ============================================
// Floating Tasks
// ============================================
.floating-tasks-section {
  .section-title {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
  }

  .task-count {
    background-color: $color-primary;
    color: white;
    font-size: $font-size-xs;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: $radius-round;
    min-width: 20px;
    text-align: center;
  }
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.floating-task-item {
  display: flex;
  gap: $spacing-md;
  padding: $spacing-md;
  background-color: $bg-color-hover;
  border-radius: $radius-md;
  cursor: move;
  transition: all $transition-fast;

  &:hover {
    background-color: darken($bg-color-hover, 2%);
    transform: translateX(4px);
  }

  &:active {
    cursor: grabbing;
    opacity: 0.7;
  }

  .task-checkbox {
    flex-shrink: 0;
  }

  .task-main {
    flex: 1;
    min-width: 0;

    .task-title {
      font-size: $font-size-sm;
      color: $color-text-primary;
      margin-bottom: $spacing-xs;
      @include text-ellipsis;
    }

    .task-meta {
      display: flex;
      align-items: center;
      gap: $spacing-md;
      font-size: $font-size-xs;
      color: $color-text-secondary;

      .task-snooze {
        display: flex;
        align-items: center;
        gap: $spacing-xs;
      }
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $spacing-xl;
  color: $color-text-tertiary;

  .el-icon {
    font-size: 48px;
    margin-bottom: $spacing-md;
    color: $color-success;
  }

  p {
    margin: 0;
    font-size: $font-size-sm;
  }
}

// ============================================
// Activity
// ============================================
.activity-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.activity-item {
  display: flex;
  gap: $spacing-md;
  padding: $spacing-md;
  border-radius: $radius-md;
  transition: background-color $transition-fast;

  &:hover {
    background-color: $bg-color-hover;
  }

  .activity-icon {
    flex-shrink: 0;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-md;
    font-size: 16px;

    &.task_created {
      background-color: rgba(102, 126, 234, 0.1);
    }

    &.task_completed {
      background-color: rgba(103, 194, 58, 0.1);
    }

    &.note_created {
      background-color: rgba(240, 147, 251, 0.1);
    }

    &.review_generated {
      background-color: rgba(250, 173, 20, 0.1);
    }
  }

  .activity-content {
    flex: 1;
    min-width: 0;

    .activity-title {
      font-size: $font-size-sm;
      color: $color-text-primary;
      margin-bottom: $spacing-xs;
      @include text-ellipsis;
    }

    .activity-time {
      font-size: $font-size-xs;
      color: $color-text-tertiary;
    }
  }
}
</style>
