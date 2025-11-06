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
          <span class="stat-item">已结束 {{ stats.completed }}</span>
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
          <el-button :type="viewMode === 'tree' ? 'primary' : ''" @click="viewMode = 'tree'">
            <el-icon><Fold /></el-icon>
            项目树
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
        </div>
      </div>
    </div>

    <!-- List View -->
    <div v-else-if="viewMode === 'list'" class="list-view">
      <!-- Batch Operations Toolbar (Always Visible) -->
      <div class="batch-toolbar">
        <span class="toolbar-info">
          <span v-if="selectedTasks.length > 0" class="selected-count">
            已选中 <strong>{{ selectedTasks.length }}</strong> 项
          </span>
          <span v-else class="toolbar-hint">批量操作</span>
        </span>
        <div class="toolbar-actions">
          <el-button
            :disabled="selectedTasks.length === 0"
            :type="selectedTasks.length > 0 ? 'success' : ''"
            size="small"
            @click="handleBatchComplete"
          >
            <el-icon><Check /></el-icon>
            完成
          </el-button>
          <el-button
            :disabled="selectedTasks.length === 0"
            size="small"
            @click="handleBatchSnooze"
          >
            <el-icon><Clock /></el-icon>
            延后
          </el-button>
          <el-button
            :disabled="selectedTasks.length === 0"
            type="danger"
            size="small"
            @click="handleBatchDelete"
          >
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
          <el-button
            v-if="selectedTasks.length > 0"
            text
            size="small"
            @click="clearSelection"
          >
            取消选择
          </el-button>
        </div>
      </div>

      <el-table :data="filteredTasks" style="width: 100%" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="title" label="任务标题" min-width="200">
          <template #default="scope">
            <div class="task-title-cell" @click="handleTaskClick(scope.row.id)">
              <span :class="{ 'task-completed': scope.row.completed }">
                {{ scope.row.title }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="project" label="项目" width="150">
          <template #default="scope">
            <el-tag
              v-if="scope.row.project"
              size="small"
              class="project-tag"
              :style="{ borderLeftColor: scope.row.project.color }"
            >
              {{ scope.row.project.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="120">
          <template #default="scope">
            <el-rate v-model="scope.row.priority" disabled :max="5" size="small" />
          </template>
        </el-table-column>
        <el-table-column prop="endTime" label="截止时间" width="150">
          <template #default="scope">
            <span
              v-if="scope.row.endTime"
              :class="getDueDateClass(scope.row.endTime)"
            >
              {{ formatDueDate(scope.row.endTime) }}
            </span>
            <span v-else class="no-due-date">-</span>
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

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 15, 20]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- Tree View -->
    <div v-else-if="viewMode === 'tree'" class="tree-view">
      <div
        v-for="project in projectTreeData"
        :key="project.id"
        class="project-tree-node"
      >
        <div class="project-header" @click="toggleProjectExpand(project.id)">
          <el-icon class="expand-icon" :class="{ 'is-expanded': project.expanded }">
            <ArrowRight />
          </el-icon>
          <span class="project-color-indicator" :style="{ backgroundColor: project.color }"></span>
          <span class="project-name">{{ project.name }}</span>
          <span class="project-task-count">{{ project.tasks.length }} 个任务</span>
          <div class="project-stats">
            <span class="stat pending">{{ project.stats.pending }} 待办</span>
            <span class="stat in-progress">{{ project.stats.inProgress }} 进行中</span>
            <span class="stat completed">{{ project.stats.completed }} 已完成</span>
          </div>
          <el-button
            size="small"
            text
            @click.stop="handleQuickAddToProject(project.id)"
          >
            <el-icon><Plus /></el-icon>
            添加任务
          </el-button>
        </div>

        <transition name="slide-down">
          <div v-show="project.expanded" class="project-tasks">
            <div
              v-for="task in project.tasks"
              :key="task.id"
              class="tree-task-item"
            >
              <el-checkbox
                v-model="task.completed"
                @change="handleTaskComplete(task.id)"
                @click.stop
              />
              <div class="task-content" @click="handleTaskClick(task.id)">
                <span class="task-title" :class="{ 'task-completed': task.completed }">
                  {{ task.title }}
                </span>
                <div class="task-meta">
                  <el-tag
                    v-if="task.status !== 'pending'"
                    size="small"
                    :type="task.status === 'completed' ? 'success' : task.status === 'in_progress' ? 'warning' : 'info'"
                  >
                    {{ getStatusLabel(task.status) }}
                  </el-tag>
                  <el-rate v-model="task.priority" disabled :max="5" size="small" />
                  <span v-if="task.dueDate" class="due-date" :class="getDueDateClass(task.dueDate)">
                    {{ formatDueDate(task.dueDate) }}
                  </span>
                </div>
              </div>
              <div class="task-actions">
                <el-button size="small" text @click.stop="handleTaskSnooze(task.id)">
                  <el-icon><Clock /></el-icon>
                </el-button>
                <el-button size="small" text @click.stop="handleTaskClick(task.id)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button size="small" text type="danger" @click.stop="handleTaskDelete(task.id)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            <div v-if="project.tasks.length === 0" class="empty-project">
              <el-icon><DocumentAdd /></el-icon>
              <p>该项目暂无任务</p>
            </div>
          </div>
        </transition>
      </div>

      <!-- Tasks without project -->
      <div v-if="tasksWithoutProject.length > 0" class="project-tree-node">
        <div class="project-header" @click="toggleProjectExpand('no-project')">
          <el-icon class="expand-icon" :class="{ 'is-expanded': noProjectExpanded }">
            <ArrowRight />
          </el-icon>
          <span class="project-name">未分配项目</span>
          <span class="project-task-count">{{ tasksWithoutProject.length }} 个任务</span>
        </div>

        <transition name="slide-down">
          <div v-show="noProjectExpanded" class="project-tasks">
            <div
              v-for="task in tasksWithoutProject"
              :key="task.id"
              class="tree-task-item"
            >
              <el-checkbox
                v-model="task.completed"
                @change="handleTaskComplete(task.id)"
                @click.stop
              />
              <div class="task-content" @click="handleTaskClick(task.id)">
                <span class="task-title" :class="{ 'task-completed': task.completed }">
                  {{ task.title }}
                </span>
                <div class="task-meta">
                  <el-tag
                    v-if="task.status !== 'pending'"
                    size="small"
                    :type="task.status === 'completed' ? 'success' : task.status === 'in_progress' ? 'warning' : 'info'"
                  >
                    {{ getStatusLabel(task.status) }}
                  </el-tag>
                  <el-rate v-model="task.priority" disabled :max="5" size="small" />
                  <span v-if="task.dueDate" class="due-date" :class="getDueDateClass(task.dueDate)">
                    {{ formatDueDate(task.dueDate) }}
                  </span>
                </div>
              </div>
              <div class="task-actions">
                <el-button size="small" text @click.stop="handleTaskSnooze(task.id)">
                  <el-icon><Clock /></el-icon>
                </el-button>
                <el-button size="small" text @click.stop="handleTaskClick(task.id)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button size="small" text type="danger" @click.stop="handleTaskDelete(task.id)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- Add Project Button at bottom of tree view -->
      <div class="add-project-section">
        <el-button
          class="add-project-btn"
          @click="showProjectDialog = true"
        >
          <el-icon><FolderAdd /></el-icon>
          <span>新建项目</span>
        </el-button>
      </div>
    </div>

    <!-- Project Creation/Edit Dialog -->
    <el-dialog
      v-model="showProjectDialog"
      :title="editingProject ? '编辑项目' : '新建项目'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="projectForm" label-width="80px">
        <el-form-item label="项目名称" required>
          <el-input v-model="projectForm.name" placeholder="请输入项目名称" />
        </el-form-item>

        <el-form-item label="项目描述">
          <el-input
            v-model="projectForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入项目描述（可选）"
          />
        </el-form-item>

        <el-form-item label="项目颜色">
          <el-color-picker v-model="projectForm.color" show-alpha />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="closeProjectDialog">取消</el-button>
        <el-button type="primary" @click="handleSaveProject">
          {{ editingProject ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Task Ignition Dialog -->
    <el-dialog
      v-model="showIgniteDialog"
      title="任务启动仪式"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="ignite-dialog-content">
        <p class="dialog-hint">
          <el-icon><InfoFilled /></el-icon>
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
    <el-dialog v-model="showSnoozeDialog" title="延后任务" width="460px">
      <div class="snooze-options">
        <div class="snooze-options-grid">
          <div
            v-for="option in snoozeOptions"
            :key="option.value"
            class="snooze-option-btn"
            @click="confirmSnooze(option.value)"
          >
            <div class="snooze-label">{{ option.label }}</div>
            <div class="snooze-hint">{{ option.hint }}</div>
          </div>
        </div>

        <el-divider>或选择自定义时间</el-divider>

        <el-date-picker
          v-model="customSnoozeDate"
          type="datetime"
          placeholder="选择自定义时间"
          style="width: 100%"
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

    <!-- Task Edit/Create Dialog -->
    <el-dialog
      v-model="showTaskDialog"
      :title="editingTask ? '编辑任务' : '创建任务'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="taskForm" label-width="80px">
        <el-form-item label="任务标题" required>
          <el-input v-model="taskForm.title" placeholder="请输入任务标题" />
        </el-form-item>

        <el-form-item label="任务描述">
          <el-input
            v-model="taskForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入任务描述（可选）"
          />
        </el-form-item>

        <el-form-item label="所属项目" required>
          <el-select v-model="taskForm.projectId" placeholder="选择项目" style="width: 100%">
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
        </el-form-item>

        <el-form-item label="优先级">
          <el-rate v-model="taskForm.priority" :max="5" show-text />
        </el-form-item>

        <el-form-item label="开始时间" required>
          <el-date-picker
            v-model="taskForm.startTime"
            type="datetime"
            placeholder="选择任务开始时间（必填）"
            style="width: 100%"
            :disabled-date="disablePastDates"
          />
        </el-form-item>

        <el-form-item label="结束时间">
          <el-date-picker
            v-model="taskForm.endTime"
            type="datetime"
            placeholder="选择任务结束时间（可选，默认1小时）"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="closeTaskDialog">取消</el-button>
        <el-button type="primary" @click="handleSaveTask">
          {{ editingTask ? '保存' : '创建' }}
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
  Fold,
  ArrowRight,
  Edit,
  Delete,
  DocumentAdd,
  MoreFilled,
  InfoFilled,
  Clock,
  Timer,
  FolderAdd,
  Check
} from '@element-plus/icons-vue'
import TaskCard from '@/components/tasks/TaskCard.vue'
import { useTaskStore } from '@/stores/taskStore'
import { useProjectStore } from '@/stores/projectStore'
import { useTaskAdapter, type ViewTask } from '@/composables/useTaskAdapter'

// ============================================
// Stores
// ============================================
const taskStore = useTaskStore()
const projectStore = useProjectStore()
const { toViewTask, toApiTask } = useTaskAdapter()

// ============================================
// Types
// ============================================
type Task = ViewTask

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
const viewMode = ref<'kanban' | 'list' | 'tree'>('kanban')
const selectedProject = ref('')
const selectedPriority = ref('')
const searchQuery = ref('')
const selectedTasks = ref<ViewTask[]>([]) // 批量选择的任务列表
let searchTimeout: number | null = null  // For debouncing search

// Pagination state
const pagination = ref({
  page: 1,
  pageSize: 15,
  total: 0
})

// Sorting state for each column
const columnSortConfig = ref<Record<string, { by: 'priority' | 'dueDate' | null; order: 'asc' | 'desc' }>>({
  pending: { by: null, order: 'desc' },
  in_progress: { by: null, order: 'desc' },
  finished: { by: null, order: 'desc' }
})

const showIgniteDialog = ref(false)
const showIgnitionResult = ref(false)
const showSnoozeDialog = ref(false)
const showTaskDialog = ref(false)
const showProjectDialog = ref(false)

const igniting = ref(false)
const currentSnoozeTaskId = ref<string | null>(null)
const noProjectExpanded = ref(true)
const customSnoozeDate = ref<Date | null>(null)
const editingTask = ref<Task | null>(null)
const editingProject = ref<any>(null)

const igniteForm = ref({
  description: ''
})

const ignitionResult = ref<IgnitionResult | null>(null)

const taskForm = ref({
  title: '',
  description: '',
  priority: 3,
  projectId: '',
  startTime: null as Date | null,
  endTime: null as Date | null
})

const projectForm = ref({
  name: '',
  description: '',
  color: '#667eea'
})

// Computed: Convert API tasks to View tasks
const allTasks = computed(() => {
  return taskStore.tasks.map(task => toViewTask(task))
})

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
  completed: allTasks.value.filter((t) => t.status === 'completed' || t.status === 'overdue').length
}))

// Helper function to sort tasks
function sortTasks(tasks: ViewTask[], sortBy: 'priority' | 'dueDate' | null, order: 'asc' | 'desc'): ViewTask[] {
  if (!sortBy) return tasks

  const sorted = [...tasks].sort((a, b) => {
    if (sortBy === 'priority') {
      // Higher priority number = higher priority (5 is highest)
      const diff = b.priority - a.priority
      return order === 'desc' ? diff : -diff
    } else if (sortBy === 'dueDate') {
      // Sort by due date (or start time if no due date)
      const dateA = a.dueDate || a.startTime
      const dateB = b.dueDate || b.startTime

      if (!dateA && !dateB) return 0
      if (!dateA) return 1  // No date goes to end
      if (!dateB) return -1

      const diff = dateA.getTime() - dateB.getTime()
      return order === 'asc' ? diff : -diff
    }
    return 0
  })

  return sorted
}

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

const kanbanColumns = computed<KanbanColumn[]>(() => {
  const pendingConfig = columnSortConfig.value.pending
  const inProgressConfig = columnSortConfig.value.in_progress
  const finishedConfig = columnSortConfig.value.finished

  return [
    {
      status: 'pending',
      label: '待办',
      icon: '📋',
      tasks: sortTasks(
        filteredTasks.value.filter((t) => t.status === 'pending'),
        pendingConfig.by,
        pendingConfig.order
      ),
      emptyText: '暂无待办任务'
    },
    {
      status: 'in_progress',
      label: '进行中',
      icon: '🚀',
      tasks: sortTasks(
        filteredTasks.value.filter((t) => t.status === 'in_progress'),
        inProgressConfig.by,
        inProgressConfig.order
      ),
      emptyText: '暂无进行中的任务'
    },
    {
      status: 'finished',
      label: '已结束',
      icon: '🏁',
      tasks: sortTasks(
        filteredTasks.value.filter((t) => t.status === 'completed' || t.status === 'overdue'),
        finishedConfig.by,
        finishedConfig.order
      ),
      emptyText: '还没有结束的任务'
    }
  ]
})

// Get projects from project store
const projects = computed(() => {
  return projectStore.projects.map(p => ({
    id: String(p.id),
    name: p.name,
    color: p.color,
    description: p.description,
    expanded: true
  }))
})

// Project tree data with expanded state
const projectTreeData = computed(() => {
  return projects.value.map(project => {
    const projectTasks = filteredTasks.value.filter(t => t.project?.id === project.id)
    return {
      ...project,
      tasks: projectTasks,
      expanded: project.expanded ?? true,
      stats: {
        pending: projectTasks.filter(t => t.status === 'pending').length,
        inProgress: projectTasks.filter(t => t.status === 'in_progress').length,
        completed: projectTasks.filter(t => t.status === 'completed').length
      }
    }
  })
})

// Tasks without project assignment
const tasksWithoutProject = computed(() => {
  return filteredTasks.value.filter(t => !t.project)
})

// ============================================
// Methods
// ============================================
async function loadTasks() {
  try {
    const [tasksResponse] = await Promise.all([
      taskStore.fetchTasks({
        page: pagination.value.page,
        pageSize: pagination.value.pageSize
      }),
      projectStore.fetchProjects()
    ])

    // Update pagination metadata from response
    if (tasksResponse && tasksResponse.pagination) {
      pagination.value.total = tasksResponse.pagination.total
    }
  } catch (error) {
    ElMessage.error('加载任务失败')
  }
}

// Disable past dates in date picker
function disablePastDates(date: Date) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date < today
}

function handleSearch() {
  // Clear existing timeout
  if (searchTimeout !== null) {
    clearTimeout(searchTimeout)
  }

  // Set new timeout for debounced search (300ms)
  searchTimeout = setTimeout(() => {
    // The search is done client-side via computed filteredTasks
    // Just reset to first page when searching
    pagination.value.page = 1
    searchTimeout = null
  }, 300) as unknown as number
}

function handleQuickCreate() {
  editingTask.value = null
  // Set default project to "未分配任务" (id: 1)
  const defaultProject = projects.value.find(p => p.name === '未分配任务')
  taskForm.value = {
    title: '',
    description: '',
    priority: 3,
    projectId: defaultProject?.id || '1',
    startTime: null,
    endTime: null
  }
  showTaskDialog.value = true
}

function handleQuickAddToColumn(status: string) {
  handleQuickCreate()
}

async function handleIgnite() {
  if (!igniteForm.value.description.trim()) {
    ElMessage.warning('请输入任务描述')
    return
  }

  igniting.value = true

  try {
    const response = await taskStore.igniteTask({
      task_description: igniteForm.value.description,
      project_id: igniteForm.value.projectId ? Number(igniteForm.value.projectId) : undefined
    })

    // Convert API response to view format
    ignitionResult.value = {
      mainTask: {
        title: response.main_task.title,
        description: response.main_task.description || '',
        suggestedDueDate: response.main_task.due_date ? new Date(response.main_task.due_date) : undefined
      },
      subtasks: response.subtasks.map(task => ({
        title: task.title,
        description: task.description || '',
        estimatedTime: 60, // Default 60 minutes
        order: 1
      })),
      relatedNotes: response.related_notes.map(note => ({
        id: String(note.note_id),
        title: note.title,
        excerpt: '',
        relevanceScore: note.similarity_score
      }))
    }

    igniting.value = false
    showIgniteDialog.value = false
    showIgnitionResult.value = true
    ElMessage.success('任务分解完成！')
  } catch (error) {
    igniting.value = false
    ElMessage.error('任务分解失败')
  }
}

function handleConfirmIgnition() {
  ElMessage.success('任务已创建！')
  showIgnitionResult.value = false
  igniteForm.value.description = ''
  ignitionResult.value = null
  loadTasks()
}

function handleTaskClick(taskId: string) {
  const task = allTasks.value.find((t) => t.id === taskId)
  if (task) {
    editingTask.value = task
    taskForm.value = {
      title: task.title,
      description: task.description || '',
      priority: task.priority,
      projectId: task.project?.id || '',
      startTime: task.startTime || null,
      endTime: task.endTime || null
    }
    showTaskDialog.value = true
  }
}

async function handleTaskComplete(taskId: string) {
  try {
    const task = allTasks.value.find((t) => t.id === taskId)
    if (task) {
      const newStatus = task.completed ? 'pending' : 'completed'
      await taskStore.updateTask(Number(taskId), { status: newStatus })
      ElMessage.success(newStatus === 'completed' ? '任务已完成！' : '任务已恢复')
    }
  } catch (error) {
    ElMessage.error('更新任务状态失败')
  }
}

function handleTaskSnooze(taskId: string) {
  currentSnoozeTaskId.value = taskId
  customSnoozeDate.value = null
  showSnoozeDialog.value = true
}

async function confirmSnooze(option: string) {
  let snoozeUntil: Date

  if (option === 'custom') {
    if (!customSnoozeDate.value) return
    snoozeUntil = customSnoozeDate.value
  } else {
    snoozeUntil = calculateSnoozeTime(option)
  }

  try {
    // 批量延后模式
    if (currentSnoozeTaskId.value === 'batch') {
      const promises = selectedTasks.value.map(task =>
        taskStore.snoozeTask(Number(task.id), snoozeUntil.toISOString())
      )
      await Promise.all(promises)
      ElMessage.success(`成功延后 ${selectedTasks.value.length} 个任务至 ${formatDateTime(snoozeUntil)}`)
      clearSelection()
    }
    // 单个任务延后模式
    else if (currentSnoozeTaskId.value) {
      await taskStore.snoozeTask(Number(currentSnoozeTaskId.value), snoozeUntil.toISOString())
      ElMessage.success(`任务已延后至 ${formatDateTime(snoozeUntil)}`)
    }
  } catch (error) {
    ElMessage.error('延后任务失败')
  }

  showSnoozeDialog.value = false
}

async function handleTaskDelete(taskId: string) {
  try {
    await ElMessageBox.confirm('确定要删除这个任务吗？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await taskStore.deleteTask(Number(taskId))
    ElMessage.success('任务已删除')

    // Smart refill after deletion
    await handleDeleteRefill(1)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除任务失败')
    }
  }
}

// ============================================
// Batch Operations
// ============================================
function handleSelectionChange(selection: ViewTask[]) {
  selectedTasks.value = selection
}

function clearSelection() {
  selectedTasks.value = []
}

async function handleBatchComplete() {
  if (selectedTasks.value.length === 0) {
    ElMessage.warning('请先选择要操作的任务')
    return
  }

  try {
    const promises = selectedTasks.value.map(task =>
      taskStore.updateTask(Number(task.id), { status: 'completed' })
    )
    await Promise.all(promises)
    ElMessage.success(`成功完成 ${selectedTasks.value.length} 个任务`)
    clearSelection()
  } catch (error) {
    ElMessage.error('批量完成任务失败')
  }
}

function handleBatchSnooze() {
  if (selectedTasks.value.length === 0) {
    ElMessage.warning('请先选择要操作的任务')
    return
  }

  // 使用现有的 snooze dialog，但标记为批量模式
  currentSnoozeTaskId.value = 'batch'
  customSnoozeDate.value = null
  showSnoozeDialog.value = true
}

async function handleBatchDelete() {
  if (selectedTasks.value.length === 0) {
    ElMessage.warning('请先选择要操作的任务')
    return
  }

  const deleteCount = selectedTasks.value.length

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${deleteCount} 个任务吗？`,
      '批量删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const promises = selectedTasks.value.map(task =>
      taskStore.deleteTask(Number(task.id))
    )
    await Promise.all(promises)
    ElMessage.success(`成功删除 ${deleteCount} 个任务`)
    clearSelection()

    // Smart refill after batch deletion
    await handleDeleteRefill(deleteCount)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除任务失败')
    }
  }
}

/**
 * Smart refill strategy after deletion
 * Automatically refills current page or navigates to previous page if empty
 */
async function handleDeleteRefill(deletedCount: number) {
  const currentPageItems = filteredTasks.value.length
  const remainingItems = currentPageItems - deletedCount

  // If current page will be empty after deletion
  if (remainingItems <= 0) {
    // If not on first page, go to previous page
    if (pagination.value.page > 1) {
      pagination.value.page -= 1
      await loadTasks()
    } else {
      // On first page, just reload to show whatever is left
      await loadTasks()
    }
  } else {
    // Current page still has items, reload to refill from next page
    await loadTasks()
  }
}

// ============================================
// Pagination Handlers
// ============================================
function handlePageChange(page: number) {
  pagination.value.page = page
  clearSelection() // Clear selection when changing pages
  loadTasks()
}

function handleSizeChange(pageSize: number) {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1 // Reset to first page
  clearSelection()
  loadTasks()
}

function handleNoteClick(noteId: string) {
  router.push(`/notes/${noteId}`)
}

function sortColumn(status: string, sortBy: 'priority' | 'dueDate') {
  const config = columnSortConfig.value[status]

  if (!config) return

  // If clicking the same sort field, toggle order
  if (config.by === sortBy) {
    config.order = config.order === 'desc' ? 'asc' : 'desc'
    ElMessage.info(`${sortBy === 'priority' ? '优先级' : '截止时间'}排序: ${config.order === 'desc' ? '降序' : '升序'}`)
  } else {
    // New sort field, default to desc
    config.by = sortBy
    config.order = 'desc'
    ElMessage.info(`按${sortBy === 'priority' ? '优先级' : '截止时间'}排序`)
  }
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

function getStatusLabel(status: string): string {
  const labels = {
    pending: '待办',
    in_progress: '进行中',
    completed: '已完成'
  }
  return labels[status as keyof typeof labels] || status
}

function toggleProjectExpand(projectId: string) {
  if (projectId === 'no-project') {
    noProjectExpanded.value = !noProjectExpanded.value
    return
  }

  const project = projects.value.find(p => p.id === projectId)
  if (project) {
    project.expanded = !project.expanded
  }
}

function handleQuickAddToProject(projectId: string) {
  editingTask.value = null
  taskForm.value = {
    title: '',
    description: '',
    priority: 3,
    projectId: projectId,
    startTime: null,
    endTime: null
  }
  showTaskDialog.value = true
}

async function handleSaveTask() {
  // 1. Validate title
  if (!taskForm.value.title.trim()) {
    ElMessage.warning('请输入任务标题')
    return
  }

  // 2. Validate project
  if (!taskForm.value.projectId) {
    ElMessage.warning('请选择所属项目')
    return
  }

  // 3. Validate start_time (required)
  if (!taskForm.value.startTime) {
    ElMessage.warning('请选择开始时间（必填）')
    return
  }

  // 4. Validate end_time > start_time
  if (taskForm.value.endTime && taskForm.value.startTime) {
    if (taskForm.value.endTime <= taskForm.value.startTime) {
      ElMessage.warning('结束时间必须晚于开始时间')
      return
    }
  }

  try {
    // 5. If no end_time, default to start_time + 1 hour
    let endTime = taskForm.value.endTime
    if (!endTime && taskForm.value.startTime) {
      endTime = new Date(taskForm.value.startTime)
      endTime.setHours(endTime.getHours() + 1)
    }

    const taskData = {
      title: taskForm.value.title,
      description: taskForm.value.description,
      priority: taskForm.value.priority,
      startTime: taskForm.value.startTime,
      endTime: endTime,
      project: taskForm.value.projectId ? {
        id: taskForm.value.projectId,
        name: '',
        color: ''
      } : undefined
    }

    const apiData = toApiTask(taskData)

    console.log('Saving task with data:', apiData)  // Debug log

    if (editingTask.value) {
      // 编辑现有任务
      await taskStore.updateTask(Number(editingTask.value.id), apiData)
      ElMessage.success('任务已更新')
    } else {
      // 创建新任务
      await taskStore.createTask(apiData)
      ElMessage.success('任务已创建')
    }

    showTaskDialog.value = false
    closeTaskDialog()
    await loadTasks()  // Reload tasks to show the new/updated task
  } catch (error: any) {
    console.error('Task save error:', error)
    const errorMessage = error.response?.data?.detail || error.message || '保存任务失败'
    ElMessage.error(`保存任务失败: ${errorMessage}`)
  }
}

function closeTaskDialog() {
  showTaskDialog.value = false
  editingTask.value = null
}

async function handleSaveProject() {
  if (!projectForm.value.name.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }

  try {
    if (editingProject.value) {
      // 编辑现有项目
      await projectStore.updateProject(Number(editingProject.value.id), {
        name: projectForm.value.name,
        description: projectForm.value.description,
        color: projectForm.value.color
      })
      ElMessage.success('项目已更新')
    } else {
      // 创建新项目
      await projectStore.createProject({
        name: projectForm.value.name,
        description: projectForm.value.description,
        color: projectForm.value.color
      })
      ElMessage.success('项目已创建')
    }

    showProjectDialog.value = false
    closeProjectDialog()
  } catch (error) {
    ElMessage.error('保存项目失败')
  }
}

function closeProjectDialog() {
  showProjectDialog.value = false
  editingProject.value = null
  projectForm.value = {
    name: '',
    description: '',
    color: '#667eea'
  }
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
  border-top: 3px solid transparent;

  &.pending {
    border-top-color: $color-primary;

    .column-header {
      background-color: rgba($color-primary, 0.05);
    }
  }

  &.in_progress {
    border-top-color: $color-warning;

    .column-header {
      background-color: rgba($color-warning, 0.05);
    }
  }

  &.completed {
    border-top-color: $color-success;

    .column-header {
      background-color: rgba($color-success, 0.05);
    }
  }

  .column-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: $spacing-lg;
    border-bottom: 1px solid $color-border;
    transition: background-color $transition-fast;

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

  .project-tag {
    border: 1px solid $color-border;
    border-left-width: 3px;
    font-size: $font-size-xs;
    background-color: $bg-color-card;
    color: $color-text-primary;
    font-weight: 500;
  }
}

// Batch Operations Toolbar (Always Visible)
.batch-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-md $spacing-lg;
  margin-bottom: $spacing-md;
  background-color: $bg-color-hover;
  border: 1px solid $color-border;
  border-radius: $radius-md;
  transition: all $transition-fast;

  .toolbar-info {
    font-size: $font-size-sm;
    color: $color-text-secondary;

    .selected-count {
      font-size: $font-size-md;
      color: $color-text-primary;

      strong {
        color: $color-primary;
        font-weight: 600;
        font-size: $font-size-lg;
      }
    }

    .toolbar-hint {
      font-weight: 500;
    }
  }

  .toolbar-actions {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
  }
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

.no-due-date {
  color: $color-text-tertiary;
  font-size: $font-size-sm;
}

// Pagination
.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: $spacing-lg;
  padding: $spacing-md 0;
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
  .snooze-options-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: $spacing-sm;
    margin-bottom: $spacing-md;
  }
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
    background-color: rgba($color-primary, 0.05);
  }

  .snooze-label {
    font-size: $font-size-md;
    font-weight: 500;
    color: $color-text-primary;
    margin-bottom: $spacing-xs;
  }

  .snooze-hint {
    font-size: $font-size-xs;
    color: $color-text-secondary;
  }
}

// ============================================
// Tree View
// ============================================
.tree-view {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.project-tree-node {
  @include card-base;
  overflow: hidden;

  .project-header {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    padding: $spacing-lg;
    background-color: $bg-color-hover;
    cursor: pointer;
    transition: background-color $transition-fast;

    &:hover {
      background-color: darken($bg-color-hover, 2%);
    }

    .expand-icon {
      font-size: $font-size-lg;
      color: $color-text-secondary;
      transition: transform $transition-fast;

      &.is-expanded {
        transform: rotate(90deg);
      }
    }

    .project-color-indicator {
      width: 4px;
      height: 24px;
      border-radius: $radius-sm;
    }

    .project-name {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $color-text-primary;
      flex: 1;
    }

    .project-task-count {
      font-size: $font-size-sm;
      color: $color-text-secondary;
      padding: $spacing-xs $spacing-sm;
      background-color: white;
      border-radius: $radius-sm;
    }

    .project-stats {
      display: flex;
      gap: $spacing-md;

      .stat {
        font-size: $font-size-xs;
        padding: $spacing-xs $spacing-sm;
        border-radius: $radius-sm;

        &.pending {
          background-color: rgba($color-primary, 0.1);
          color: $color-primary;
        }

        &.in-progress {
          background-color: rgba($color-warning, 0.1);
          color: $color-warning;
        }

        &.completed {
          background-color: rgba($color-success, 0.1);
          color: $color-success;
        }
      }
    }
  }

  .project-tasks {
    background-color: white;
  }

  .tree-task-item {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    padding: $spacing-md $spacing-lg;
    border-top: 1px solid $color-border;
    transition: background-color $transition-fast;

    &:hover {
      background-color: $bg-color-hover;
    }

    .task-content {
      flex: 1;
      cursor: pointer;
      min-width: 0;

      .task-title {
        font-size: $font-size-md;
        color: $color-text-primary;
        margin-bottom: $spacing-xs;
        @include text-ellipsis;

        &.task-completed {
          text-decoration: line-through;
          color: $color-text-tertiary;
        }
      }

      .task-meta {
        display: flex;
        align-items: center;
        gap: $spacing-md;
        font-size: $font-size-xs;
        color: $color-text-secondary;

        .due-date {
          &.overdue {
            color: $color-danger;
          }

          &.today {
            color: $color-warning;
          }

          &.soon {
            color: $color-primary;
          }
        }
      }
    }

    .task-actions {
      display: flex;
      gap: $spacing-xs;
      opacity: 0;
      transition: opacity $transition-fast;
    }

    &:hover .task-actions {
      opacity: 1;
    }
  }

  .empty-project {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: $spacing-xl;
    color: $color-text-tertiary;

    .el-icon {
      font-size: 48px;
      margin-bottom: $spacing-md;
    }

    p {
      margin: 0;
      font-size: $font-size-sm;
    }
  }
}

// Add Project Section
.add-project-section {
  padding: $spacing-lg;
  border-top: 1px solid $color-border;

  .add-project-btn {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: $spacing-sm;
    border: 2px dashed $color-border;
    color: $color-text-secondary;
    background-color: transparent;

    &:hover {
      border-color: $color-primary;
      color: $color-primary;
      background-color: rgba($color-primary, 0.05);
    }
  }
}

// Slide down transition for tree view
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
  max-height: 1000px;
  overflow: hidden;
}

.slide-down-enter-from,
.slide-down-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
