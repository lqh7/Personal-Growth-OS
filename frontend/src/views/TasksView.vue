<template>
  <div class="tasks-view">
    <!-- Header with actions -->
    <div class="view-header">
      <el-button type="primary" @click="showIgniteDialog = true">
        <el-icon><MagicStick /></el-icon>
        任务启动仪式
      </el-button>
      <el-button @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        快速创建任务
      </el-button>
    </div>

    <!-- Task Filters -->
    <el-tabs v-model="activeTab" class="task-tabs">
      <el-tab-pane label="待办" name="pending">
        <TaskList :tasks="taskStore.pendingTasks" @update="handleUpdate" @delete="handleDelete" />
      </el-tab-pane>
      <el-tab-pane label="进行中" name="in_progress">
        <TaskList :tasks="taskStore.inProgressTasks" @update="handleUpdate" @delete="handleDelete" />
      </el-tab-pane>
      <el-tab-pane label="已完成" name="completed">
        <TaskList :tasks="taskStore.completedTasks" @update="handleUpdate" @delete="handleDelete" />
      </el-tab-pane>
    </el-tabs>

    <!-- Task Ignition Dialog -->
    <el-dialog
      v-model="showIgniteDialog"
      title="任务启动仪式 - AI 辅助分解"
      width="600px"
    >
      <el-form :model="ignitionForm">
        <el-form-item label="描述你的任务">
          <el-input
            v-model="ignitionForm.task_description"
            type="textarea"
            :rows="4"
            placeholder="例如：写一份年度总结报告"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showIgniteDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleIgnite"
          :loading="taskStore.loading"
        >
          开始分解
        </el-button>
      </template>
    </el-dialog>

    <!-- Quick Create Dialog -->
    <el-dialog v-model="showCreateDialog" title="快速创建任务" width="500px">
      <el-form :model="createForm">
        <el-form-item label="任务标题">
          <el-input v-model="createForm.title" placeholder="输入任务标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="优先级">
          <el-rate v-model="createForm.priority" :max="5" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="taskStore.loading">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- Ignition Result Dialog -->
    <el-dialog
      v-model="showIgnitionResult"
      title="任务分解结果"
      width="700px"
    >
      <div v-if="ignitionResult">
        <h4>主任务</h4>
        <TaskCard :task="ignitionResult.main_task" simple />

        <h4 style="margin-top: 20px">子任务</h4>
        <div v-for="subtask in ignitionResult.subtasks" :key="subtask.id">
          <TaskCard :task="subtask" simple />
        </div>

        <h4 style="margin-top: 20px">推荐起步任务</h4>
        <TaskCard :task="ignitionResult.minimum_viable_task" simple highlighted />

        <div v-if="ignitionResult.related_notes.length > 0" style="margin-top: 20px">
          <h4>相关笔记</h4>
          <el-tag
            v-for="note in ignitionResult.related_notes"
            :key="note.note_id"
            style="margin-right: 8px; margin-bottom: 8px"
          >
            {{ note.title }} ({{ (note.similarity_score * 100).toFixed(0) }}% 相关)
          </el-tag>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="showIgnitionResult = false">
          开始执行
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { MagicStick, Plus } from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/taskStore'
import TaskList from '@/components/tasks/TaskList.vue'
import TaskCard from '@/components/tasks/TaskCard.vue'
import type { TaskIgnitionResponse } from '@/types'

const taskStore = useTaskStore()

const activeTab = ref('pending')
const showIgniteDialog = ref(false)
const showCreateDialog = ref(false)
const showIgnitionResult = ref(false)
const ignitionResult = ref<TaskIgnitionResponse | null>(null)

const ignitionForm = ref({
  task_description: ''
})

const createForm = ref({
  title: '',
  description: '',
  priority: 3
})

onMounted(async () => {
  await taskStore.fetchTasks()
})

async function handleIgnite() {
  if (!ignitionForm.value.task_description) {
    ElMessage.warning('请输入任务描述')
    return
  }

  try {
    const result = await taskStore.igniteTask(ignitionForm.value)
    ignitionResult.value = result
    showIgniteDialog.value = false
    showIgnitionResult.value = true
    ElMessage.success('任务分解成功！')

    // Refresh task list
    await taskStore.fetchTasks()
  } catch (error) {
    ElMessage.error('任务分解失败')
  }
}

async function handleCreate() {
  if (!createForm.value.title) {
    ElMessage.warning('请输入任务标题')
    return
  }

  try {
    await taskStore.createTask(createForm.value)
    showCreateDialog.value = false
    createForm.value = { title: '', description: '', priority: 3 }
    ElMessage.success('任务创建成功')
  } catch (error) {
    ElMessage.error('任务创建失败')
  }
}

async function handleUpdate(taskId: number, updates: any) {
  try {
    await taskStore.updateTask(taskId, updates)
    ElMessage.success('任务更新成功')
  } catch (error) {
    ElMessage.error('任务更新失败')
  }
}

async function handleDelete(taskId: number) {
  try {
    await taskStore.deleteTask(taskId)
    ElMessage.success('任务删除成功')
  } catch (error) {
    ElMessage.error('任务删除失败')
  }
}
</script>

<style scoped>
.tasks-view {
  max-width: 1200px;
  margin: 0 auto;
}

.view-header {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.task-tabs {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}

h4 {
  color: #303133;
  margin: 10px 0;
}
</style>
