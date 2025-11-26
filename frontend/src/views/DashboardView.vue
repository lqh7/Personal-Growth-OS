<template>
  <div class="dashboard-view page-view">
    <!-- Header -->
    <div class="dashboard-header page-header">
      <div class="header-left">
        <h1 class="page-title">工作台</h1>
        <p class="page-subtitle">{{ currentDate }} · {{ greeting }}</p>
      </div>
    </div>

    <!-- Statistics Cards -->
    <div class="stats-grid grid-stagger">
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
      <div class="schedule-section content-card">
        <div class="section-header">
          <h3 class="section-title">
            <el-icon><Calendar /></el-icon>
            本周日程
          </h3>
          <el-button text type="primary" @click="router.push('/tasks')">查看更多</el-button>
        </div>
        <WeekSchedule
          :tasks="calendarTasks"
          @task-click="handleTaskClick"
          @task-snooze="handleTaskSnooze"
          @slot-click="handleSlotClick"
        />
      </div>

      <!-- Snoozed Tasks (Floating Tasks) -->
      <div class="floating-tasks-section content-card">
        <div class="section-header">
          <h3 class="section-title">
            <el-icon><Clock /></el-icon>
            延后任务
          </h3>
          <span class="task-count">{{ floatingTasks.length }}</span>
        </div>
        <div class="task-list">
          <div
            v-for="task in floatingTasks"
            :key="task.id"
            class="floating-task-item"
          >
            <div class="task-main">
              <span class="task-title" @click="handleTaskClick(task.id)">{{ task.title }}</span>
              <div class="task-meta">
                <el-tag
                  v-if="task.project"
                  size="small"
                  class="project-tag"
                  :style="{ borderLeftColor: task.project.color }"
                >
                  {{ task.project.name }}
                </el-tag>
                <el-rate
                  v-model="task.priority"
                  disabled
                  :max="5"
                  size="small"
                />
              </div>
            </div>
            <span class="task-snooze">
              <el-icon><Clock /></el-icon>
              {{ task.snoozeText }}
            </span>
          </div>

          <!-- Empty State -->
          <div v-if="floatingTasks.length === 0" class="empty-state">
            <el-icon class="empty-icon"><InfoFilled /></el-icon>
            <p>暂无延后任务</p>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="activity-section content-card">
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
import { Clock, InfoFilled, SuccessFilled, Calendar } from '@element-plus/icons-vue'
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

interface Activity {
  id: string
  type: 'task_created' | 'task_completed' | 'note_created' | 'review_generated'
  title: string
  timestamp: Date
}

interface FloatingTask {
  id: string
  title: string
  priority: number
  snoozeUntil: Date
  snoozeText: string
  project?: {
    id: string
    name: string
    color: string
  }
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

const recentActivities = ref<Activity[]>([])

// Calendar tasks - all active tasks (exclude completed)
const calendarTasks = computed(() => {
  return taskStore.tasks
    .filter(task => task.status !== 'completed')
    .map(task => toViewTask(task))
})

// Floating tasks - snoozed tasks that are not yet due
const floatingTasks = computed<FloatingTask[]>(() => {
  const now = new Date()
  return taskStore.tasks
    .filter(task => {
      if (!task.snooze_until) return false
      if (task.status === 'completed') return false
      return new Date(task.snooze_until) > now
    })
    .map(task => ({
      id: String(task.id),
      title: task.title,
      priority: task.priority,
      snoozeUntil: new Date(task.snooze_until!),
      snoozeText: formatSnoozeTime(new Date(task.snooze_until!)),
      project: task.project_id ? {
        id: String(task.project_id),
        name: projectStore.projects.find(p => p.id === task.project_id)?.name || '',
        color: projectStore.projects.find(p => p.id === task.project_id)?.color || '#667eea'
      } : undefined
    }))
    .sort((a, b) => a.snoozeUntil.getTime() - b.snoozeUntil.getTime())
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

function formatSnoozeTime(date: Date): string {
  const now = new Date()
  const diff = date.getTime() - now.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(hours / 24)

  if (days > 1) return `${days}天后`
  if (days === 1) return '明天'
  if (hours > 0) return `${hours}小时后`
  return '即将开始'
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

  // 日程表完整显示，不需要滚动
  // 时间槽区域高度由内容决定 (13小时 × 60px = 780px)
}

// ============================================
// Floating Tasks Section
// ============================================
.floating-tasks-section {

  .section-header {
    .section-title {
      display: flex;
      align-items: center;
      gap: $spacing-xs;
    }

    .task-count {
      background-color: $color-warning;
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
    justify-content: space-between;
    align-items: center;
    padding: $spacing-md;
    border-bottom: 1px solid $color-border;
    transition: background-color $transition-fast;

    &:last-child {
      border-bottom: none;
    }

    &:hover {
      background-color: $bg-color-hover;
    }

    .task-main {
      flex: 1;
      min-width: 0;

      .task-title {
        display: block;
        font-size: $font-size-sm;
        font-weight: 500;
        color: $color-text-primary;
        margin-bottom: $spacing-xs;
        cursor: pointer;

        &:hover {
          color: $color-primary;
        }
      }

      .task-meta {
        display: flex;
        align-items: center;
        gap: $spacing-md;

        .project-tag {
          border: 1px solid $color-border;
          border-left-width: 3px;
          font-size: $font-size-xs;
          background-color: $bg-color-card;
          color: $color-text-primary;
          font-weight: 500;
        }
      }
    }

    .task-snooze {
      display: flex;
      align-items: center;
      gap: $spacing-xs;
      font-size: $font-size-xs;
      color: $color-text-secondary;
      white-space: nowrap;
      flex-shrink: 0;
      margin-left: $spacing-md;
    }
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: $spacing-xl;
    color: $color-text-tertiary;

    .empty-icon {
      font-size: 48px;
      margin-bottom: $spacing-md;
    }

    p {
      margin: 0;
      font-size: $font-size-sm;
    }
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
