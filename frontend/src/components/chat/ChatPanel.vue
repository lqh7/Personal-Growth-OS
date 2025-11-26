<template>
  <div class="chat-panel">
    <!-- Header -->
    <div class="chat-header">
      <div class="header-left">
        <el-icon :size="20" color="#409eff">
          <ChatDotRound />
        </el-icon>
        <span class="header-title">AI助手</span>
        <el-tag v-if="currentTaskId" size="small" type="info">
          任务 #{{ currentTaskId }}
        </el-tag>
      </div>

      <div class="header-actions">
        <!-- New chat button -->
        <el-tooltip content="新建对话" placement="bottom">
          <el-button
            :icon="Plus"
            circle
            size="small"
            @click="handleNewChat"
          />
        </el-tooltip>

        <!-- Close button -->
        <el-tooltip content="关闭面板" placement="bottom">
          <el-button
            :icon="Close"
            circle
            size="small"
            @click="handleClose"
          />
        </el-tooltip>
      </div>
    </div>

    <!-- Messages area -->
    <Messages />

    <!-- Input area -->
    <ChatInput
      :disabled="isStreaming"
      @send="handleSendMessage"
    />
  </div>
</template>

<script setup lang="ts">
import { ChatDotRound, Plus, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chatStore'
import { useChatStream } from '@/composables/useChatStream'
import Messages from './Messages.vue'
import ChatInput from './ChatInput.vue'

/**
 * Store
 */
const chatStore = useChatStore()
const {
  isStreaming,
  currentTaskId,
  currentSessionId,
} = storeToRefs(chatStore)

/**
 * Composables
 */
const { streamChat } = useChatStream()

/**
 * Handle send message
 */
async function handleSendMessage(message: string) {
  // Add user message to store
  chatStore.addMessage({
    role: 'user',
    content: message,
    created_at: Date.now(),
    task_id: currentTaskId.value || undefined,
  })

  // Add placeholder assistant message
  chatStore.addMessage({
    role: 'assistant',
    content: '',
    created_at: Date.now(),
  })

  // Stream response from agent
  try {
    await streamChat('task-igniter', {
      message,
      task_id: currentTaskId.value || undefined,
      session_id: currentSessionId.value || undefined,
      stream: true,
    })
  } catch (error) {
    console.error('[ChatPanel] Stream error:', error)
    ElMessage.error('消息发送失败，请重试')
  }
}

/**
 * Handle new chat
 */
function handleNewChat() {
  chatStore.clearMessages()
  ElMessage.success('已开始新对话')
}

/**
 * Handle close panel
 */
function handleClose() {
  chatStore.hideChatPanel()
}
</script>

<style scoped lang="scss">
.chat-panel {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-left: 1px solid #e4e7ed;
  flex-shrink: 0; // 不允许压缩
  min-width: 350px; // 设计要求：最小350px
  overflow: hidden; // 防止内容溢出
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e4e7ed;
  background: #f5f7fa;
  flex-shrink: 0; // Header固定高度

  .header-left {
    display: flex;
    align-items: center;
    gap: 8px;

    .header-title {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }
  }

  .header-actions {
    display: flex;
    gap: 8px;
  }
}
</style>
