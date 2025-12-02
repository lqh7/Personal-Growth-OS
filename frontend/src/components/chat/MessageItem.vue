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
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600&family=Inter:wght@400;500&display=swap');

.message-item {
  display: flex;
  gap: 20px;
  padding: 32px 48px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 0;
  animation: fadeSlideIn 0.5s ease-out forwards;

  @keyframes fadeSlideIn {
    from {
      opacity: 0;
      transform: translateY(8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  &:hover {
    background-color: #FAFAF9;
  }

  &.has-error {
    background-color: #FEF2F2;
  }

  &.message-user {
    background: linear-gradient(to right, transparent, #F7F5F3 50%, transparent);

    .message-content {
      background: transparent;
      border: none;
    }
  }

  &.message-assistant {
    .message-content {
      background: transparent;
      border: none;
    }
  }

  &.message-system {
    opacity: 0.6;

    .message-content {
      background: transparent;
      border-left: 2px solid #E5E5E5;
      padding-left: 16px;
    }
  }
}

.message-avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;

  :deep(.el-avatar) {
    background: transparent;
    border: 1.5px solid #2D2D2D;
    color: #2D2D2D;
    font-weight: 500;
    font-size: 14px;
    transition: all 0.3s ease;

    &:hover {
      transform: scale(1.05);
      border-color: #8B7355;
    }
  }
}

.message-content {
  flex: 1;
  min-width: 0;
  max-width: 720px;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 16px;

  .role-name {
    font-family: 'Crimson Pro', serif;
    font-weight: 600;
    font-size: 15px;
    letter-spacing: -0.01em;
    color: #2D2D2D;
  }

  .message-time {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 400;
    letter-spacing: 0.02em;
    color: #A3A3A3;
    text-transform: uppercase;
  }
}

.message-text {
  font-family: 'Inter', sans-serif;
  font-size: 15px;
  line-height: 1.75;
  color: #3F3F3F;
  word-wrap: break-word;
  letter-spacing: -0.011em;

  // Markdown preview adjustments
  :deep(.md-preview) {
    background: transparent !important;
    padding: 0;
    color: #3F3F3F;
  }

  :deep(p) {
    margin: 0 0 20px 0;

    &:last-child {
      margin-bottom: 0;
    }
  }

  :deep(h1), :deep(h2), :deep(h3), :deep(h4) {
    font-family: 'Crimson Pro', serif;
    font-weight: 600;
    color: #2D2D2D;
    margin: 32px 0 16px 0;
    letter-spacing: -0.02em;
  }

  :deep(h1) { font-size: 28px; }
  :deep(h2) { font-size: 24px; }
  :deep(h3) { font-size: 20px; }
  :deep(h4) { font-size: 17px; }

  :deep(code) {
    background-color: #F5F3F0;
    color: #8B7355;
    padding: 3px 8px;
    border-radius: 4px;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
    font-size: 13.5px;
    font-weight: 500;
    letter-spacing: -0.02em;
  }

  :deep(pre) {
    background: linear-gradient(135deg, #FAFAF9 0%, #F5F3F0 100%);
    border: 1px solid #E7E5E4;
    padding: 20px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 24px 0;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

    code {
      background: transparent;
      color: #2D2D2D;
      padding: 0;
      font-size: 13px;
      line-height: 1.6;
    }
  }

  :deep(ul), :deep(ol) {
    margin: 16px 0;
    padding-left: 24px;

    li {
      margin: 8px 0;
      line-height: 1.75;
    }
  }

  :deep(blockquote) {
    border-left: 3px solid #D6D3D1;
    padding-left: 20px;
    margin: 24px 0;
    color: #57534E;
    font-style: italic;
  }
}

.message-error {
  margin-top: 20px;

  :deep(.el-alert) {
    background: #FEF2F2;
    border: 1px solid #FCA5A5;
    border-radius: 6px;
    font-size: 14px;
  }
}

.tool-calls {
  margin-top: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.reasoning-steps {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #E7E5E4;
}

.references {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #E7E5E4;
}
</style>
