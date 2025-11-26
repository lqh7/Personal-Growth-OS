<template>
  <div
    class="message-item"
    :class="[`message-${message.role}`, { 'has-error': message.streamingError }]"
  >
    <!-- Avatar -->
    <div class="message-avatar">
      <el-avatar :size="32" :style="avatarStyle">
        <component :is="avatarIcon" />
      </el-avatar>
    </div>

    <!-- Content -->
    <div class="message-content">
      <!-- Role header -->
      <div class="message-header">
        <span class="role-name">{{ roleName }}</span>
        <span class="message-time">{{ formatTime(message.created_at) }}</span>
      </div>

      <!-- Main content (Markdown) -->
      <div v-if="message.content" class="message-text">
        <MdPreview
          :model-value="message.content"
          :theme="'light'"
          :preview-theme="'github'"
          :code-theme="'github'"
        />
      </div>

      <!-- Error indicator -->
      <div v-if="message.streamingError" class="message-error">
        <el-alert type="error" :closable="false" show-icon>
          <template #title>
            {{ streamingErrorMessage || '消息处理出错' }}
          </template>
        </el-alert>
      </div>

      <!-- Tool calls -->
      <div v-if="message.tool_calls && message.tool_calls.length > 0" class="tool-calls">
        <ToolCallBadge
          v-for="(toolCall, index) in message.tool_calls"
          :key="`tool-${index}`"
          :tool-call="toolCall"
        />
      </div>

      <!-- Reasoning steps -->
      <div
        v-if="message.extra_data?.reasoning_steps && message.extra_data.reasoning_steps.length > 0"
        class="reasoning-steps"
      >
        <ReasoningSteps :steps="message.extra_data.reasoning_steps" />
      </div>

      <!-- References (RAG results) -->
      <div
        v-if="message.extra_data?.references && message.extra_data.references.length > 0"
        class="references"
      >
        <References :references="message.extra_data.references" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { User, ChatDotRound } from '@element-plus/icons-vue'
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/preview.css'
import type { ChatMessage } from '@/types/chat'
import ToolCallBadge from './ToolCallBadge.vue'
import ReasoningSteps from './ReasoningSteps.vue'
import References from './References.vue'
import { useChatStore } from '@/stores/chatStore'
import { storeToRefs } from 'pinia'

/**
 * Props
 */
interface Props {
  message: ChatMessage
}

const props = defineProps<Props>()

/**
 * Store
 */
const chatStore = useChatStore()
const { streamingErrorMessage } = storeToRefs(chatStore)

/**
 * Avatar icon based on role
 */
const avatarIcon = computed(() => {
  return props.message.role === 'user' ? User : ChatDotRound
})

/**
 * Avatar background style
 */
const avatarStyle = computed(() => {
  const colors = {
    user: { background: '#409eff', color: '#ffffff' },
    assistant: { background: '#67c23a', color: '#ffffff' },
    system: { background: '#909399', color: '#ffffff' },
  }
  return colors[props.message.role] || colors.system
})

/**
 * Role display name
 */
const roleName = computed(() => {
  const names = {
    user: '你',
    assistant: 'AI助手',
    system: '系统',
  }
  return names[props.message.role] || '未知'
})

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
    // Different day: show date + time
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }
}
</script>

<style scoped lang="scss">
.message-item {
  display: flex;
  gap: 12px;
  padding: 16px;
  transition: background-color 0.2s;

  &:hover {
    background-color: #f5f7fa;
  }

  &.has-error {
    background-color: #fef0f0;
  }

  &.message-user {
    .message-content {
      background-color: #ecf5ff;
      border-left: 3px solid #409eff;
    }
  }

  &.message-assistant {
    .message-content {
      background-color: #f0f9ff;
      border-left: 3px solid #67c23a;
    }
  }

  &.message-system {
    .message-content {
      background-color: #f4f4f5;
      border-left: 3px solid #909399;
    }
  }
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  min-width: 0;
  padding: 12px;
  border-radius: 8px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;

  .role-name {
    font-weight: 600;
    font-size: 14px;
    color: #303133;
  }

  .message-time {
    font-size: 12px;
    color: #909399;
  }
}

.message-text {
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
  word-wrap: break-word;

  // Markdown preview adjustments
  :deep(.md-preview) {
    background: transparent !important;
    padding: 0;
  }

  :deep(p) {
    margin: 0 0 8px 0;

    &:last-child {
      margin-bottom: 0;
    }
  }

  :deep(code) {
    background-color: rgba(0, 0, 0, 0.05);
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 13px;
  }

  :deep(pre) {
    background-color: #f6f8fa;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    margin: 8px 0;
  }
}

.message-error {
  margin-top: 12px;
}

.tool-calls {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.reasoning-steps {
  margin-top: 12px;
}

.references {
  margin-top: 12px;
}
</style>
