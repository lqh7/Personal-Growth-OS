<template>
  <div class="dashboard-view">
    <!-- Header -->
    <div class="dashboard-header">
      <div class="header-left">
        <h1 class="page-title">工作台</h1>
        <p class="page-subtitle">{{ currentDate }} · {{ greeting }}</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleQuickTask">
          <el-icon><Plus /></el-icon>
          快速创建任务
        </el-button>
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
      <!-- Week Calendar -->
      <div class="calendar-section card">
        <div class="section-header">
          <h3 class="section-title">本周日历</h3>
          <el-button text type="primary" @click="router.push('/tasks')">查看更多</el-button>
        </div>
        <WeekCalendar
          :tasks="calendarTasks"
          @task-click="handleTaskClick"
          @task-complete="handleTaskComplete"
          @task-snooze="handleTaskSnooze"
          @slot-click="handleSlotClick"
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
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus,
  Clock,
  InfoFilled,
  SuccessFilled
} from '@element-plus/icons-vue'
import WeekCalendar from '@/components/calendar/WeekCalendar.vue'

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
// Router
// ============================================
const router = useRouter()

// ============================================
// State - Mock Data
// ============================================
const stats = ref<Stat[]>([
  {
    key: 'pending',
    icon: '📋',
    label: '待办任务',
    value: 12,
    trend: 'up',
    trendText: '比昨天 +3'
  },
  {
    key: 'overdue',
    icon: '⚠️',
    label: '逾期任务',
    value: 3,
    trend: 'down',
    trendText: '比昨天 -1'
  },
  {
    key: 'completed',
    icon: '✅',
    label: '本周完成',
    value: 27,
    trend: 'up',
    trendText: '完成率 82%'
  },
  {
    key: 'week_total',
    icon: '📊',
    label: '本周总计',
    value: 42,
    trend: 'neutral',
    trendText: '进行中 12'
  }
])

const floatingTasks = ref<FloatingTask[]>([
  {
    id: '1',
    title: '准备季度总结PPT',
    completed: false,
    snoozeUntil: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2小时后
    project: {
      name: '工作项目',
      color: '#667eea'
    }
  },
  {
    id: '2',
    title: '阅读《深度工作》第3章',
    completed: false,
    snoozeUntil: new Date(Date.now() + 5 * 60 * 60 * 1000), // 5小时后
    project: {
      name: '个人学习',
      color: '#f093fb'
    }
  },
  {
    id: '3',
    title: '回复客户邮件',
    completed: false,
    snoozeUntil: new Date(Date.now() + 24 * 60 * 60 * 1000) // 明天
  }
])

const recentActivities = ref<Activity[]>([
  {
    id: '1',
    type: 'task_completed',
    title: '完成了任务"优化数据库查询性能"',
    timestamp: new Date(Date.now() - 30 * 60 * 1000) // 30分钟前
  },
  {
    id: '2',
    type: 'note_created',
    title: '创建了笔记"Vue 3 Composition API 最佳实践"',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000) // 2小时前
  },
  {
    id: '3',
    type: 'task_created',
    title: '创建了任务"准备下周的项目演示"',
    timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000) // 3小时前
  },
  {
    id: '4',
    type: 'review_generated',
    title: 'AI 生成了本周复盘报告',
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000) // 昨天
  }
])

// Mock calendar tasks with specific times
const calendarTasks = ref([
  {
    id: 'cal-1',
    title: '团队站会',
    description: '每日团队同步',
    status: 'completed' as const,
    priority: 3,
    dueDate: getDateForDayOfWeek(1), // Monday
    dueTime: '09:00',
    duration: 30,
    completed: true,
    project: {
      id: '1',
      name: '工作项目',
      color: '#667eea'
    }
  },
  {
    id: 'cal-2',
    title: '前端代码review',
    status: 'in_progress' as const,
    priority: 4,
    dueDate: getDateForDayOfWeek(1),
    dueTime: '14:00',
    duration: 60,
    completed: false,
    project: {
      id: '1',
      name: '工作项目',
      color: '#667eea'
    }
  },
  {
    id: 'cal-3',
    title: '学习LangGraph文档',
    status: 'pending' as const,
    priority: 2,
    dueDate: getDateForDayOfWeek(2), // Tuesday
    dueTime: '10:00',
    duration: 90,
    completed: false,
    project: {
      id: '2',
      name: '个人学习',
      color: '#f093fb'
    }
  },
  {
    id: 'cal-4',
    title: '准备项目演示PPT',
    status: 'pending' as const,
    priority: 5,
    dueDate: getDateForDayOfWeek(3), // Wednesday
    dueTime: '15:00',
    duration: 120,
    completed: false,
    project: {
      id: '1',
      name: '工作项目',
      color: '#667eea'
    }
  },
  {
    id: 'cal-5',
    title: '健身房锻炼',
    status: 'pending' as const,
    priority: 3,
    dueDate: getDateForDayOfWeek(4), // Thursday
    dueTime: '18:00',
    duration: 60,
    completed: false,
    project: {
      id: '3',
      name: '健康管理',
      color: '#4facfe'
    }
  },
  {
    id: 'cal-6',
    title: '周报总结',
    status: 'pending' as const,
    priority: 4,
    dueDate: getDateForDayOfWeek(5), // Friday
    dueTime: '16:00',
    duration: 30,
    completed: false,
    project: {
      id: '1',
      name: '工作项目',
      color: '#667eea'
    }
  },
  // Floating tasks (no time)
  {
    id: 'cal-7',
    title: '阅读产品需求文档',
    status: 'pending' as const,
    priority: 3,
    dueDate: new Date(),
    completed: false,
    project: {
      id: '1',
      name: '工作项目',
      color: '#667eea'
    }
  },
  {
    id: 'cal-8',
    title: '整理笔记',
    status: 'pending' as const,
    priority: 2,
    completed: false,
    project: {
      id: '2',
      name: '个人学习',
      color: '#f093fb'
    }
  }
])

// Helper function to get date for specific day of current week
function getDateForDayOfWeek(dayIndex: number): Date {
  const today = new Date()
  const currentDay = today.getDay()
  const monday = new Date(today)
  const diff = currentDay === 0 ? -6 : 1 - currentDay
  monday.setDate(today.getDate() + diff)

  const targetDate = new Date(monday)
  targetDate.setDate(monday.getDate() + dayIndex)
  return targetDate
}

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
function handleQuickTask() {
  ElMessage.success('跳转到任务创建页面（将在 TasksView 中实现）')
  router.push('/tasks')
}

function handleStatClick(key: string) {
  ElMessage.info(`点击了统计卡片: ${key}`)
  router.push('/tasks')
}

function handleTaskClick(taskId: string) {
  ElMessage.info(`点击了任务: ${taskId}`)
}

function handleTaskComplete(task: FloatingTask) {
  if (task.completed) {
    ElMessage.success(`任务"${task.title}"已完成！`)
    // 模拟延迟移除
    setTimeout(() => {
      const index = floatingTasks.value.findIndex((t) => t.id === task.id)
      if (index !== -1) {
        floatingTasks.value.splice(index, 1)
      }
    }, 500)
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
// Calendar Section
// ============================================
.calendar-section {
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
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    background-color: darken($bg-color-hover, 2%);
    transform: translateX(4px);
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
