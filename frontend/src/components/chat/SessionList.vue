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

    <!-- Load more button -->
    <div v-if="hasMore" class="load-more">
      <el-button
        text
        type="primary"
        :loading="isLoadingMore"
        @click="handleLoadMore"
      >
        加载更多
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
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
const isLoadingMore = ref(false)
const currentPage = ref(1)
const totalSessions = ref(0)
const pageSize = 20

/**
 * Computed
 */
const hasMore = computed(() => {
  return sessions.value.length < totalSessions.value
})

/**
 * Load sessions from API
 */
async function loadSessions(append: boolean = false) {
  try {
    if (append) {
      isLoadingMore.value = true
    } else {
      isLoading.value = true
      chatStore.setSessionsLoading(true)
    }

    const response = await getSessions(
      undefined, // agentId
      pageSize,
      (currentPage.value - 1) * pageSize
    )

    totalSessions.value = response.total

    if (append) {
      chatStore.setSessions([...sessions.value, ...response.sessions])
    } else {
      chatStore.setSessions(response.sessions)
    }

  } catch (error) {
    console.error('[SessionList] Load sessions error:', error)
    ElMessage.error('加载对话历史失败')
  } finally {
    isLoading.value = false
    isLoadingMore.value = false
    chatStore.setSessionsLoading(false)
  }
}

/**
 * Handle refresh
 */
async function handleRefresh() {
  currentPage.value = 1
  await loadSessions(false)
}

/**
 * Handle load more
 */
async function handleLoadMore() {
  currentPage.value++
  await loadSessions(true)
}

/**
 * Handle select session
 */
async function handleSelectSession(session: SessionEntry) {
  try {
    chatStore.setCurrentSessionId(session.session_id)

    // Load session history
    const history = await getSessionHistory(session.session_id)
    chatStore.setSessions(history.messages as any) // TODO: Fix type

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

.load-more {
  padding: 12px;
  text-align: center;
  border-top: 1px solid #e4e7ed;
}
</style>
