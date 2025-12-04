<template>
  <div class="session-list-container">
    <!-- Header -->
    <div class="list-header">
      <span class="header-title">对话历史</span>
      <el-button
        :icon="Refresh"
        circle
        size="small"
        @click="handleRefresh"
        :loading="isLoading"
      />
    </div>

    <!-- Loading state -->
    <div v-if="isLoading && sessions.length === 0" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- Empty state -->
    <div v-else-if="sessions.length === 0" class="empty-state">
      <el-empty description="暂无对话历史" :image-size="60" />
    </div>

    <!-- Session list -->
    <div v-else class="session-list">
      <div
        v-for="session in sessions"
        :key="session.session_id"
        class="session-item"
        :class="{ active: session.session_id === currentSessionId }"
        @click="handleSelectSession(session)"
      >
        <!-- Session info -->
        <div class="session-info">
          <div class="session-name">{{ session.session_name }}</div>
          <div class="session-meta">
            <span class="session-time">{{ formatTime(session.created_at) }}</span>
            <el-tag v-if="session.message_count" size="small" type="info">
              {{ session.message_count }}条消息
            </el-tag>
          </div>
        </div>

        <!-- Delete button -->
        <el-button
          :icon="Delete"
          circle
          size="small"
          type="danger"
          text
          @click.stop="handleDelete(session)"
        />
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Refresh, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chatStore'
import type { SessionEntry } from '@/types/chat'
import { getSessions, getSessionHistory, deleteSession } from '@/api/chat'

/**
 * Store
 */
const chatStore = useChatStore()
const { sessions, currentSessionId, isSessionsLoading } = storeToRefs(chatStore)

/**
 * Local state
 */
const isLoading = ref(false)

/**
 * Load sessions from API
 * 一次性加载所有会话列表（不分页）
 */
async function loadSessions() {
  try {
    isLoading.value = true
    chatStore.setSessionsLoading(true)

    // 一次性加载所有会话（limit设置足够大）
    const response = await getSessions(undefined, 100, 0)
    chatStore.setSessions(response.sessions)

  } catch (error) {
    console.error('[SessionList] Load sessions error:', error)
    ElMessage.error('加载对话历史失败')
  } finally {
    isLoading.value = false
    chatStore.setSessionsLoading(false)
  }
}

/**
 * Handle refresh
 */
async function handleRefresh() {
  await loadSessions()
}

/**
 * Handle select session
 */
async function handleSelectSession(session: SessionEntry) {
  try {
    // 1. 清空现有消息
    chatStore.clearMessages()

    // 2. 设置当前会话ID (clearMessages会清空，需要重新设置)
    chatStore.setCurrentSessionId(session.session_id)

    // 3. 加载会话历史消息
    const history = await getSessionHistory(session.session_id)

    // 4. 将历史消息添加到 messages 列表 (不是 sessions!)
    history.messages.forEach(msg => {
      chatStore.addMessage({
        role: msg.role as 'user' | 'assistant',
        content: msg.content,
        created_at: msg.created_at
      })
    })

    ElMessage.success('已加载对话历史')
  } catch (error) {
    console.error('[SessionList] Load session history error:', error)
    ElMessage.error('加载对话历史失败')
  }
}

/**
 * Handle delete session
 */
async function handleDelete(session: SessionEntry) {
  try {
    await ElMessageBox.confirm(
      `确定要删除对话 "${session.session_name}" 吗?`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await deleteSession(session.session_id)
    chatStore.removeSession(session.session_id)
    ElMessage.success('删除成功')

    // Refresh list
    await handleRefresh()

  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('[SessionList] Delete session error:', error)
      ElMessage.error('删除失败')
    }
  }
}

/**
 * Format timestamp
 */
function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  const now = new Date()

  // Check if same day
  const isSameDay =
    date.getDate() === now.getDate() &&
    date.getMonth() === now.getMonth() &&
    date.getFullYear() === now.getFullYear()

  if (isSameDay) {
    // Same day: show time only
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    })
  } else {
    // Different day: show date
    return date.toLocaleDateString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
    })
  }
}

/**
 * Lifecycle
 */
onMounted(() => {
  loadSessions()
})
</script>

<style scoped lang="scss">
.session-list-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;

  .header-title {
    font-size: 14px;
    font-weight: 600;
    color: #303133;
  }
}

.loading-state,
.empty-state {
  flex: 1;
  padding: 16px;
}

.session-list {
  flex: 1;
  overflow-y: auto;

  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-track {
    background: #f5f7fa;
  }

  &::-webkit-scrollbar-thumb {
    background: #dcdfe6;
    border-radius: 2px;

    &:hover {
      background: #c0c4cc;
    }
  }
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f2f5;
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover {
    background-color: #f5f7fa;

    .el-button {
      opacity: 1;
    }
  }

  &.active {
    background-color: #ecf5ff;
    border-left: 3px solid #409eff;
  }

  .session-info {
    flex: 1;
    min-width: 0;

    .session-name {
      font-size: 14px;
      font-weight: 500;
      color: #303133;
      margin-bottom: 4px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .session-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: #909399;

      .session-time {
        font-style: italic;
      }
    }
  }

  .el-button {
    opacity: 0;
    transition: opacity 0.2s;
  }
}
</style>
