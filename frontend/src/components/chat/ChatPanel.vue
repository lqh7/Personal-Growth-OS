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
    await streamChat('orchestrator', {
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
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@600&family=Inter:wght@400;500&display=swap');

.chat-panel {
  display: flex;
  flex-direction: column;
  background: #FFFFFF;
  border-left: 1px solid #E7E5E4;
  flex-shrink: 0;
  min-width: 420px;
  overflow: hidden;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.04);
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  border-bottom: 1px solid #E7E5E4;
  background: linear-gradient(to bottom, #FAFAF9 0%, #FFFFFF 100%);
  flex-shrink: 0;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;

    .header-title {
      font-family: 'Crimson Pro', serif;
      font-size: 18px;
      font-weight: 600;
      letter-spacing: -0.02em;
      color: #2D2D2D;
    }

    :deep(.el-icon) {
      color: #8B7355 !important;
      transition: transform 0.3s ease;

      &:hover {
        transform: rotate(15deg) scale(1.1);
      }
    }

    :deep(.el-tag) {
      background: #F5F3F0;
      border: 1px solid #E7E5E4;
      color: #57534E;
      font-family: 'Inter', sans-serif;
      font-size: 11px;
      font-weight: 500;
      letter-spacing: 0.03em;
      text-transform: uppercase;
      padding: 4px 10px;
      border-radius: 12px;
    }
  }

  .header-actions {
    display: flex;
    gap: 8px;

    :deep(.el-button) {
      background: transparent;
      border: 1.5px solid #E7E5E4;
      color: #57534E;
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

      &:hover {
        background: #FAFAF9;
        border-color: #8B7355;
        color: #2D2D2D;
        transform: translateY(-1px);
      }

      &:active {
        transform: translateY(0);
      }
    }
  }
}
</style>
