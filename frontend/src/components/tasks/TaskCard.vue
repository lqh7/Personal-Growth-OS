<template>
  <el-card :class="['task-card', { highlighted: highlighted, simple: simple }]" shadow="hover">
    <div class="task-header">
      <div class="task-title-row">
        <el-checkbox
          v-if="!simple"
          :model-value="task.status === 'completed'"
          @change="toggleComplete"
        />
        <h4 class="task-title">{{ task.title }}</h4>
        <el-rate
          v-model="task.priority"
          :max="5"
          size="small"
          disabled
        />
      </div>
      <div v-if="!simple" class="task-actions">
        <el-dropdown @command="handleCommand">
          <el-button size="small" text>
            <el-icon><More /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="snooze">延后</el-dropdown-item>
              <el-dropdown-item command="edit">编辑</el-dropdown-item>
              <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <p v-if="task.description" class="task-description">{{ task.description }}</p>

    <div class="task-meta">
      <el-tag :type="statusTypeMap[task.status]" size="small">
        {{ statusTextMap[task.status] }}
      </el-tag>
      <span v-if="task.due_date" class="due-date">
        <el-icon><Clock /></el-icon>
        {{ formatDate(task.due_date) }}
      </span>
    </div>

    <!-- Subtasks -->
    <div v-if="task.subtasks && task.subtasks.length > 0" class="subtasks">
      <el-divider />
      <div v-for="subtask in task.subtasks" :key="subtask.id" class="subtask-item">
        <el-checkbox
          :model-value="subtask.status === 'completed'"
          @change="() => emit('update', subtask.id, { status: subtask.status === 'completed' ? 'pending' : 'completed' })"
        />
        <span>{{ subtask.title }}</span>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ElMessageBox } from 'element-plus'
import { More, Clock } from '@element-plus/icons-vue'
import type { Task } from '@/types'

const props = defineProps<{
  task: Task
  simple?: boolean
  highlighted?: boolean
}>()

const emit = defineEmits<{
  update: [taskId: number, updates: any]
  delete: [taskId: number]
}>()

const statusTypeMap: Record<string, any> = {
  pending: 'info',
  in_progress: 'warning',
  completed: 'success',
  cancelled: 'danger'
}

const statusTextMap: Record<string, string> = {
  pending: '待办',
  in_progress: '进行中',
  completed: '已完成',
  cancelled: '已取消'
}

function toggleComplete() {
  const newStatus = props.task.status === 'completed' ? 'pending' : 'completed'
  emit('update', props.task.id, { status: newStatus })
}

function handleCommand(command: string) {
  if (command === 'delete') {
    ElMessageBox.confirm('确定要删除这个任务吗？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      emit('delete', props.task.id)
    })
  } else if (command === 'snooze') {
    // TODO: Implement snooze dialog
    console.log('Snooze task:', props.task.id)
  } else if (command === 'edit') {
    // TODO: Implement edit dialog
    console.log('Edit task:', props.task.id)
  }
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.task-card {
  margin-bottom: 8px;
  transition: all 0.3s;
}

.task-card.highlighted {
  border: 2px solid #409eff;
  box-shadow: 0 0 10px rgba(64, 158, 255, 0.3);
}

.task-card.simple {
  margin-bottom: 12px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.task-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.task-title {
  margin: 0;
  font-size: 16px;
  flex: 1;
}

.task-description {
  margin: 12px 0;
  color: #606266;
  font-size: 14px;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}

.due-date {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #909399;
}

.subtasks {
  margin-top: 12px;
}

.subtask-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  font-size: 14px;
  color: #606266;
}
</style>
