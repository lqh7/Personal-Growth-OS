<template>
  <div class="task-list">
    <el-empty v-if="tasks.length === 0" description="暂无任务" />
    <TaskCard
      v-for="task in tasks"
      :key="task.id"
      :task="task"
      @update="handleUpdate"
      @delete="handleDelete"
    />
  </div>
</template>

<script setup lang="ts">
import type { Task } from '@/types'
import TaskCard from './TaskCard.vue'

defineProps<{
  tasks: Task[]
}>()

const emit = defineEmits<{
  update: [taskId: number, updates: any]
  delete: [taskId: number]
}>()

function handleUpdate(taskId: number, updates: any) {
  emit('update', taskId, updates)
}

function handleDelete(taskId: number) {
  emit('delete', taskId)
}
</script>

<style scoped>
.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
