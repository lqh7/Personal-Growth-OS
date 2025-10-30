<template>
  <div class="tasks-view">
    <!-- Header -->
    <div class="view-header">
      <div class="header-left">
        <h1 class="page-title">任务管理</h1>
        <div class="header-stats">
          <span class="stat-item">待办 {{ stats.pending }}</span>
          <span class="stat-divider">·</span>
          <span class="stat-item">进行中 {{ stats.inProgress }}</span>
          <span class="stat-divider">·</span>
          <span class="stat-item">已完成 {{ stats.completed }}</span>
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="handleQuickCreate">
          <el-icon><Plus /></el-icon>
          快速创建
        </el-button>
        <el-button type="primary" @click="showIgniteDialog = true">
          <el-icon><MagicStick /></el-icon>
          任务启动仪式
        </el-button>
      </div>
    </div>

    <!-- Filters -->
    <div class="filters-bar">
      <div class="filters-left">
        <el-select v-model="selectedProject" placeholder="所有项目" clearable @change="loadTasks">
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          >
            <span class="project-option">
              <span class="project-color" :style="{ backgroundColor: project.color }"></span>
              {{ project.name }}
            </span>
          </el-option>
        </el-select>

        <el-select v-model="selectedPriority" placeholder="所有优先级" clearable @change="loadTasks">
          <el-option label="🔥 高优先级 (4-5)" :value="'high'" />
          <el-option label="⭐ 中优先级 (2-3)" :value="'medium'" />
          <el-option label="📌 低优先级 (0-1)" :value="'low'" />
        </el-select>

        <el-input
          v-model="searchQuery"
          placeholder="搜索任务..."
          clearable
          @input="handleSearch"
          style="width: 240px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <div class="filters-right">
        <el-button-group>
          <el-button :type="viewMode === 'kanban' ? 'primary' : ''" @click="viewMode = 'kanban'">
            <el-icon><Grid /></el-icon>
            看板
          </el-button>
          <el-button :type="viewMode === 'list' ? 'primary' : ''" @click="viewMode = 'list'">
            <el-icon><List /></el-icon>
            列表
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- Kanban View -->
    <div v-if="viewMode === 'kanban'" class="kanban-view">
      <div
        v-for="column in kanbanColumns"
        :key="column.status"
        class="kanban-column"
        :class="column.status"
      >
        <div class="column-header">
          <div class="column-title">
            <span class="column-icon">{{ column.icon }}</span>
            <span class="column-label">{{ column.label }}</span>
            <span class="column-count">{{ column.tasks.length }}</span>
          </div>
          <el-dropdown trigger="click">
            <el-icon class="column-menu"><MoreFilled /></el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="sortColumn(column.status, 'priority')">
                  按优先级排序
                </el-dropdown-item>
                <el-dropdown-item @click="sortColumn(column.status, 'dueDate')">
                  按截止时间排序
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <div class="column-content">
          <div
            v-for="task in column.tasks"
            :key="task.id"
            class="kanban-task-wrapper"
          >
            <TaskCard
              :task="task"
              variant="default"
              @click="handleTaskClick(task.id)"
              @complete="handleTaskComplete(task.id)"
              @snooze="handleTaskSnooze(task.id)"
              @delete="handleTaskDelete(task.id)"
            />
          </div>

          <!-- Empty State -->
          <div v-if="column.tasks.length === 0" class="column-empty">
            <p>{{ column.emptyText }}</p>
          </div>

          <!-- Quick Add Button -->
          <el-button
            v-if="column.status !== 'completed'"
            class="quick-add-btn"
            text
            @click="handleQuickAddToColumn(column.status)"
          >
            <el-icon><Plus /></el-icon>
            添加任务
          </el-button>
        </div>
      </div>
    </div>

    <!-- List View -->
    <div v-else class="list-view">
      <el-table :data="filteredTasks" style="width: 100%">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="title" label="任务标题" min-width="200">
          <template #default="scope">
            <div class="task-title-cell" @click="handleTaskClick(scope.row.id)">
              <el-checkbox
                v-model="scope.row.completed"
                @change="handleTaskComplete(scope.row.id)"
                @click.stop
              />
              <span :class="{ 'task-completed': scope.row.completed }">
                {{ scope.row.title }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="project" label="项目" width="150">
          <template #default="scope">
            <el-tag v-if="scope.row.project" size="small" :color="scope.row.project.color">
              {{ scope.row.project.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="120">
          <template #default="scope">
            <el-rate v-model="scope.row.priority" disabled :max="5" size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="dueDate" label="截止时间" width="150">
          <template #default="scope">
            <span v-if="scope.row.dueDate" :class="getDueDateClass(scope.row.dueDate)">
              {{ formatDueDate(scope.row.dueDate) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button-group size="small">
              <el-button @click="handleTaskSnooze(scope.row.id)">延后</el-button>
              <el-button @click="handleTaskClick(scope.row.id)">编辑</el-button>
              <el-button type="danger" @click="handleTaskDelete(scope.row.id)">删除</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Task Ignition Dialog -->
    <el-dialog
      v-model="showIgniteDialog"
      title="任务启动仪式"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="ignite-dialog-content">
        <p class="dialog-hint">
          <el-icon><Bulb /></el-icon>
          描述你的任务，AI 将帮你分解为可执行的子任务
        </p>
        <el-input
          v-model="igniteForm.description"
          type="textarea"
          :rows="5"
          placeholder="例如：准备下周的项目演示&#10;&#10;AI 会自动：&#10;• 分解为具体子任务&#10;• 检索相关历史笔记&#10;• 推荐最小起步任务"
        />
      </div>
      <template #footer>
        <el-button @click="showIgniteDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleIgnite"
          :loading="igniting"
          :disabled="!igniteForm.description.trim()"
        >
          开始分解
        </el-button>
      </template>
    </el-dialog>

    <!-- Ignition Result Dialog -->
    <el-dialog
      v-model="showIgnitionResult"
      title="任务分解结果"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="ignitionResult" class="ignition-result">
        <!-- Main Task -->
        <div class="result-section">
          <h3 class="result-title">
            <span class="result-icon">📋</span>
            主任务
          </h3>
          <div class="main-task-preview">
            <h4>{{ ignitionResult.mainTask.title }}</h4>
            <p>{{ ignitionResult.mainTask.description }}</p>
            <div v-if="ignitionResult.mainTask.suggestedDueDate" class="suggested-due-date">
              <el-icon><Clock /></el-icon>
              建议截止时间：{{ formatDateTime(ignitionResult.mainTask.suggestedDueDate) }}
            </div>
          </div>
        </div>

        <!-- Subtasks -->
        <div class="result-section">
          <h3 class="result-title">
            <span class="result-icon">✅</span>
            子任务（{{ ignitionResult.subtasks.length }}）
          </h3>
          <div class="subtasks-list">
            <div
              v-for="(subtask, index) in ignitionResult.subtasks"
              :key="index"
              class="subtask-item"
            >
              <div class="subtask-order">{{ index + 1 }}</div>
              <div class="subtask-content">
                <div class="subtask-title">{{ subtask.title }}</div>
                <div class="subtask-description">{{ subtask.description }}</div>
                <div class="subtask-meta">
                  <span class="estimated-time">
                    <el-icon><Timer /></el-icon>
                    预计 {{ subtask.estimatedTime }} 分钟
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Related Notes -->
        <div v-if="ignitionResult.relatedNotes.length > 0" class="result-section">
          <h3 class="result-title">
            <span class="result-icon">📝</span>
            相关笔记（{{ ignitionResult.relatedNotes.length }}）
          </h3>
          <div class="related-notes-list">
            <div
              v-for="note in ignitionResult.relatedNotes"
              :key="note.id"
              class="related-note-item"
              @click="handleNoteClick(note.id)"
            >
              <div class="note-header">
                <span class="note-title">{{ note.title }}</span>
                <span class="relevance-score">
                  {{ Math.round(note.relevanceScore * 100) }}% 相关
                </span>
              </div>
              <div class="note-excerpt">{{ note.excerpt }}</div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="showIgnitionResult = false">稍后处理</el-button>
        <el-button type="primary" @click="handleConfirmIgnition">
          确认并创建任务
        </el-button>
      </template>
    </el-dialog>

    <!-- Snooze Dialog -->
    <el-dialog v-model="showSnoozeDialog" title="延后任务" width="400px">
      <div class="snooze-options">
        <el-button
          v-for="option in snoozeOptions"
          :key="option.value"
          class="snooze-option-btn"
          @click="confirmSnooze(option.value)"
        >
          <div class="snooze-label">{{ option.label }}</div>
          <div class="snooze-hint">{{ option.hint }}</div>
        </el-button>

        <el-date-picker
          v-model="customSnoozeDate"
          type="datetime"
          placeholder="选择自定义时间"
          style="width: 100%; margin-top: 12px"
        />
      </div>
      <template #footer>
        <el-button @click="showSnoozeDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="confirmSnooze('custom')"
          :disabled="!customSnoozeDate"
        >
          确认延后
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  MagicStick,
  Search,
  Grid,
  List,
  MoreFilled,
  Bulb,
  Clock,
  Timer
} from '@element-plus/icons-vue'
import TaskCard from '@/components/tasks/TaskCard.vue'

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
  snoozeUntil?: Date
  completed: boolean
  project?: {
    id: string
    name: string
    color: string
  }
}

interface KanbanColumn {
  status: string
  label: string
  icon: string
  tasks: Task[]
  emptyText: string
}

interface IgnitionResult {
  mainTask: {
    title: string
    description: string
    suggestedDueDate?: Date
  }
  subtasks: Array<{
    title: string
    description: string
    estimatedTime: number
    order: number
  }>
  relatedNotes: Array<{
    id: string
    title: string
    excerpt: string
    relevanceScore: number
  }>
}

// ============================================
// Router
// ============================================
const router = useRouter()

// ============================================
// State
// ============================================
const viewMode = ref<'kanban' | 'list'>('kanban')
const selectedProject = ref('')
const selectedPriority = ref('')
const searchQuery = ref('')

const showIgniteDialog = ref(false)
const showIgnitionResult = ref(false)
const showSnoozeDialog = ref(false)

const igniting = ref(false)
const currentSnoozeTaskId = ref<string | null>(null)
const customSnoozeDate = ref<Date | null>(null)

const igniteForm = ref({
  description: ''
})

const ignitionResult = ref<IgnitionResult | null>(null)

// Mock data
const projects = ref([
  { id: '1', name: '工作项目', color: '#667eea' },
  { id: '2', name: '个人学习', color: '#f093fb' },
  { id: '3', name: '健康管理', color: '#4facfe' }
])

const allTasks = ref<Task[]>([
  {
    id: '1',
    title: '完成前端详细设计文档',
    description: '包括组件设计、路由设计、状态管理等',
    status: 'in_progress',
    priority: 5,
    dueDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000),
    completed: false,
    project: projects.value[0]
  },
  {
    id: '2',
    title: '学习 LangGraph 基础',
    description: '了解节点、边、状态的概念',
    status: 'pending',
    priority: 4,
    dueDate: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000),
    completed: false,
    project: projects.value[1]
  },
  {
    id: '3',
    title: '每日晨跑 5km',
    status: 'completed',
    priority: 3,
    completed: true,
    project: projects.value[2]
  },
  {
    id: '4',
    title: '优化数据库查询性能',
    description: '添加索引，优化慢查询',
    status: 'pending',
    priority: 5,
    dueDate: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000),
    completed: false,
    project: projects.value[0]
  },
  {
    id: '5',
    title: '阅读《深度工作》第3章',
    status: 'in_progress',
    priority: 2,
    completed: false,
    project: projects.value[1]
  }
])

const snoozeOptions = [
  { label: '1小时后', value: '1h', hint: formatSnoozeHint(1, 'hours') },
  { label: '3小时后', value: '3h', hint: formatSnoozeHint(3, 'hours') },
  { label: '明天上午', value: 'tomorrow_morning', hint: '明天 9:00' },
  { label: '后天', value: 'day_after_tomorrow', hint: '后天 9:00' },
  { label: '下周一', value: 'next_monday', hint: '下周一 9:00' }
]

// ============================================
// Computed
// ============================================
const stats = computed(() => ({
  pending: allTasks.value.filter((t) => t.status === 'pending').length,
  inProgress: allTasks.value.filter((t) => t.status === 'in_progress').length,
  completed: allTasks.value.filter((t) => t.status === 'completed').length
}))

const filteredTasks = computed(() => {
  let tasks = allTasks.value

  if (selectedProject.value) {
    tasks = tasks.filter((t) => t.project?.id === selectedProject.value)
  }

  if (selectedPriority.value) {
    const priorityRanges = {
      high: [4, 5],
      medium: [2, 3],
      low: [0, 1]
    }
    const range = priorityRanges[selectedPriority.value as keyof typeof priorityRanges]
    tasks = tasks.filter((t) => t.priority >= range[0] && t.priority <= range[1])
  }

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    tasks = tasks.filter(
      (t) =>
        t.title.toLowerCase().includes(query) ||
        t.description?.toLowerCase().includes(query)
    )
  }

  return tasks
})

const kanbanColumns = computed<KanbanColumn[]>(() => [
  {
    status: 'pending',
    label: '待办',
    icon: '📋',
    tasks: filteredTasks.value.filter((t) => t.status === 'pending'),
    emptyText: '暂无待办任务'
  },
  {
    status: 'in_progress',
    label: '进行中',
    icon: '🚀',
    tasks: filteredTasks.value.filter((t) => t.status === 'in_progress'),
    emptyText: '暂无进行中的任务'
  },
  {
    status: 'completed',
    label: '已完成',
    icon: '✅',
    tasks: filteredTasks.value.filter((t) => t.status === 'completed'),
    emptyText: '还没有完成的任务'
  }
])

// ============================================
// Methods
// ============================================
function loadTasks() {
  // Mock: In real app, this would call API
  console.log('Loading tasks with filters:', {
    project: selectedProject.value,
    priority: selectedPriority.value,
    search: searchQuery.value
  })
}

function handleSearch() {
  // Mock: Debounced search
  console.log('Searching:', searchQuery.value)
}

function handleQuickCreate() {
  ElMessage.info('快速创建对话框（简化版）')
}

function handleQuickAddToColumn(status: string) {
  ElMessage.info(`添加任务到: ${status}`)
}

async function handleIgnite() {
  igniting.value = true

  // Mock AI response with delay
  await new Promise((resolve) => setTimeout(resolve, 1500))

  ignitionResult.value = {
    mainTask: {
      title: '准备下周的项目演示',
      description: '包含PPT制作、演示稿撰写、Demo准备等子任务',
      suggestedDueDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
    },
    subtasks: [
      {
        title: '回顾上次演示的PPT',
        description: '检查现有内容，确定可复用部分',
        estimatedTime: 30,
        order: 1
      },
      {
        title: '准备演示Demo',
        description: '确保所有功能正常运行',
        estimatedTime: 90,
        order: 2
      },
      {
        title: '撰写演示稿',
        description: '准备讲解要点和演示脚本',
        estimatedTime: 60,
        order: 3
      }
    ],
    relatedNotes: [
      {
        id: 'note1',
        title: '上次项目演示总结',
        excerpt: '上次演示中客户关注的重点是性能优化和用户体验...',
        relevanceScore: 0.92
      },
      {
        id: 'note2',
        title: '项目技术亮点整理',
        excerpt: 'AI驱动的任务分解、智能知识检索、可视化复盘...',
        relevanceScore: 0.85
      }
    ]
  }

  igniting.value = false
  showIgniteDialog.value = false
  showIgnitionResult.value = true
  ElMessage.success('任务分解完成！')
}

function handleConfirmIgnition() {
  ElMessage.success('任务已创建！')
  showIgnitionResult.value = false
  igniteForm.value.description = ''
  ignitionResult.value = null
  loadTasks()
}

function handleTaskClick(taskId: string) {
  ElMessage.info(`打开任务详情: ${taskId}`)
}

function handleTaskComplete(taskId: string) {
  const task = allTasks.value.find((t) => t.id === taskId)
  if (task) {
    task.completed = !task.completed
    task.status = task.completed ? 'completed' : 'pending'
    ElMessage.success(task.completed ? '任务已完成！' : '任务已恢复')
  }
}

function handleTaskSnooze(taskId: string) {
  currentSnoozeTaskId.value = taskId
  customSnoozeDate.value = null
  showSnoozeDialog.value = true
}

function confirmSnooze(option: string) {
  let snoozeUntil: Date

  if (option === 'custom') {
    if (!customSnoozeDate.value) return
    snoozeUntil = customSnoozeDate.value
  } else {
    snoozeUntil = calculateSnoozeTime(option)
  }

  const task = allTasks.value.find((t) => t.id === currentSnoozeTaskId.value)
  if (task) {
    task.snoozeUntil = snoozeUntil
    ElMessage.success(`任务已延后至 ${formatDateTime(snoozeUntil)}`)
  }

  showSnoozeDialog.value = false
}

function handleTaskDelete(taskId: string) {
  ElMessageBox.confirm('确定要删除这个任务吗？', '确认删除', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    const index = allTasks.value.findIndex((t) => t.id === taskId)
    if (index !== -1) {
      allTasks.value.splice(index, 1)
      ElMessage.success('任务已删除')
    }
  })
}

function handleNoteClick(noteId: string) {
  router.push(`/notes/${noteId}`)
}

function sortColumn(status: string, sortBy: string) {
  ElMessage.info(`排序: ${status} - ${sortBy}`)
}

function calculateSnoozeTime(option: string): Date {
  const now = new Date()
  const tomorrow = new Date(now)
  tomorrow.setDate(tomorrow.getDate() + 1)
  tomorrow.setHours(9, 0, 0, 0)

  switch (option) {
    case '1h':
      return new Date(now.getTime() + 60 * 60 * 1000)
    case '3h':
      return new Date(now.getTime() + 3 * 60 * 60 * 1000)
    case 'tomorrow_morning':
      return tomorrow
    case 'day_after_tomorrow':
      tomorrow.setDate(tomorrow.getDate() + 1)
      return tomorrow
    case 'next_monday':
      const nextMonday = new Date(now)
      nextMonday.setDate(now.getDate() + ((1 + 7 - now.getDay()) % 7 || 7))
      nextMonday.setHours(9, 0, 0, 0)
      return nextMonday
    default:
      return tomorrow
  }
}

function formatSnoozeHint(amount: number, unit: string): string {
  const time = new Date()
  if (unit === 'hours') {
    time.setHours(time.getHours() + amount)
  }
  return time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function formatDateTime(date: Date): string {
  return date.toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function formatDueDate(date: Date): string {
  const now = new Date()
  const diff = date.getTime() - now.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天'
  if (days === 1) return '明天'
  if (days < 0) return `逾期 ${Math.abs(days)} 天`
  return `${days} 天后`
}

function getDueDateClass(date: Date): string {
  const now = new Date()
  const diff = date.getTime() - now.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days < 0) return 'overdue'
  if (days === 0) return 'today'
  if (days <= 2) return 'soon'
  return ''
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';
@import '@/assets/styles/mixins.scss';

.tasks-view {
  max-width: 1600px;
  margin: 0 auto;
}

// ============================================
// Header
// ============================================
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: $spacing-xl;

  .header-left {
    .page-title {
      font-size: $font-size-xxl;
      font-weight: 600;
      color: $color-text-primary;
      margin: 0 0 $spacing-sm 0;
    }

    .header-stats {
      display: flex;
      align-items: center;
      gap: $spacing-md;
      font-size: $font-size-sm;
      color: $color-text-secondary;

      .stat-divider {
        color: $color-text-tertiary;
      }
    }
  }

  .header-actions {
    display: flex;
    gap: $spacing-md;
  }
}

// ============================================
// Filters
// ============================================
.filters-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-xl;
  padding: $spacing-lg;
  background-color: $bg-color-card;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;

  .filters-left {
    display: flex;
    gap: $spacing-md;
    flex: 1;
  }

  .filters-right {
    flex-shrink: 0;
  }
}

.project-option {
  display: flex;
  align-items: center;
  gap: $spacing-sm;

  .project-color {
    width: 12px;
    height: 12px;
    border-radius: $radius-sm;
  }
}

// ============================================
// Kanban View
// ============================================
.kanban-view {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: $spacing-lg;
  align-items: start;
}

.kanban-column {
  background-color: $bg-color-card;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  min-height: 500px;
  display: flex;
  flex-direction: column;

  .column-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: $spacing-lg;
    border-bottom: 1px solid $color-border;

    .column-title {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      font-weight: 600;
      color: $color-text-primary;

      .column-icon {
        font-size: 20px;
      }

      .column-count {
        background-color: $bg-color-hover;
        color: $color-text-secondary;
        font-size: $font-size-xs;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: $radius-round;
        min-width: 20px;
        text-align: center;
      }
    }

    .column-menu {
      cursor: pointer;
      color: $color-text-tertiary;
      transition: color $transition-fast;

      &:hover {
        color: $color-text-primary;
      }
    }
  }

  .column-content {
    flex: 1;
    padding: $spacing-md;
    overflow-y: auto;
    @include custom-scrollbar;
  }

  .kanban-task-wrapper {
    margin-bottom: $spacing-md;
  }

  .column-empty {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 200px;
    color: $color-text-tertiary;
    font-size: $font-size-sm;
  }

  .quick-add-btn {
    width: 100%;
    margin-top: $spacing-sm;
    border: 2px dashed $color-border;
    color: $color-text-secondary;

    &:hover {
      border-color: $color-primary;
      color: $color-primary;
    }
  }
}

// ============================================
// List View
// ============================================
.list-view {
  background-color: $bg-color-card;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;
  padding: $spacing-lg;
}

.task-title-cell {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  cursor: pointer;

  .task-completed {
    text-decoration: line-through;
    color: $color-text-tertiary;
  }
}

.overdue {
  color: $color-danger;
  font-weight: 600;
}

.today {
  color: $color-warning;
  font-weight: 600;
}

.soon {
  color: $color-primary;
}

// ============================================
// Ignite Dialog
// ============================================
.ignite-dialog-content {
  .dialog-hint {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    padding: $spacing-md;
    background-color: $bg-color-hover;
    border-radius: $radius-md;
    margin-bottom: $spacing-lg;
    font-size: $font-size-sm;
    color: $color-text-secondary;
  }
}

.ignition-result {
  .result-section {
    margin-bottom: $spacing-xl;

    &:last-child {
      margin-bottom: 0;
    }
  }

  .result-title {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    font-size: $font-size-lg;
    font-weight: 600;
    color: $color-text-primary;
    margin-bottom: $spacing-lg;

    .result-icon {
      font-size: 24px;
    }
  }

  .main-task-preview {
    padding: $spacing-lg;
    background-color: $bg-color-hover;
    border-radius: $radius-md;

    h4 {
      margin: 0 0 $spacing-sm 0;
      font-size: $font-size-md;
      color: $color-text-primary;
    }

    p {
      margin: 0 0 $spacing-md 0;
      color: $color-text-secondary;
      line-height: 1.6;
    }

    .suggested-due-date {
      display: flex;
      align-items: center;
      gap: $spacing-xs;
      font-size: $font-size-sm;
      color: $color-primary;
    }
  }

  .subtasks-list {
    display: flex;
    flex-direction: column;
    gap: $spacing-md;
  }

  .subtask-item {
    display: flex;
    gap: $spacing-md;
    padding: $spacing-md;
    background-color: $bg-color-hover;
    border-radius: $radius-md;

    .subtask-order {
      flex-shrink: 0;
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: $color-primary;
      color: white;
      font-weight: 600;
      border-radius: $radius-round;
    }

    .subtask-content {
      flex: 1;

      .subtask-title {
        font-size: $font-size-md;
        font-weight: 500;
        color: $color-text-primary;
        margin-bottom: $spacing-xs;
      }

      .subtask-description {
        font-size: $font-size-sm;
        color: $color-text-secondary;
        margin-bottom: $spacing-sm;
      }

      .subtask-meta {
        .estimated-time {
          display: inline-flex;
          align-items: center;
          gap: $spacing-xs;
          font-size: $font-size-xs;
          color: $color-text-tertiary;
        }
      }
    }
  }

  .related-notes-list {
    display: flex;
    flex-direction: column;
    gap: $spacing-sm;
  }

  .related-note-item {
    padding: $spacing-md;
    background-color: $bg-color-hover;
    border-radius: $radius-md;
    cursor: pointer;
    transition: all $transition-fast;

    &:hover {
      background-color: darken($bg-color-hover, 3%);
      transform: translateX(4px);
    }

    .note-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: $spacing-xs;

      .note-title {
        font-size: $font-size-sm;
        font-weight: 500;
        color: $color-text-primary;
      }

      .relevance-score {
        font-size: $font-size-xs;
        color: $color-primary;
        font-weight: 600;
      }
    }

    .note-excerpt {
      font-size: $font-size-xs;
      color: $color-text-secondary;
      line-height: 1.5;
      @include text-ellipsis-multiline(2);
    }
  }
}

// ============================================
// Snooze Dialog
// ============================================
.snooze-options {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
}

.snooze-option-btn {
  width: 100%;
  height: auto;
  padding: $spacing-md;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  border: 1px solid $color-border;
  border-radius: $radius-md;
  background-color: white;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    border-color: $color-primary;
    background-color: lighten($color-primary, 45%);
  }

  .snooze-label {
    font-size: $font-size-md;
    font-weight: 500;
    color: $color-text-primary;
    margin-bottom: $spacing-xs;
  }

  .snooze-hint {
    font-size: $font-size-xs;
    color: $color-text-tertiary;
  }
}
</style>
