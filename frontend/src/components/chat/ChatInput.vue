<template>
  <div class="chat-input-container">
    <!-- Input area -->
    <el-input
      v-model="inputText"
      type="textarea"
      :rows="inputRows"
      :placeholder="placeholder"
      :disabled="disabled"
      class="chat-textarea"
      @keydown="handleKeyDown"
      resize="none"
    />

    <!-- Actions bar -->
    <div class="actions-bar">
      <!-- Left side: hints -->
      <div class="input-hints">
        <span v-if="!disabled" class="hint-text">
          按 Enter 发送，Shift+Enter 换行
        </span>
        <span v-if="disabled" class="hint-text disabled">
          AI正在思考中...
        </span>
      </div>

      <!-- Right side: send button -->
      <div class="input-actions">
        <el-button
          type="primary"
          :icon="Promotion"
          :disabled="!canSend"
          :loading="disabled"
          @click="handleSend"
        >
          {{ disabled ? '发送中' : '发送' }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Promotion } from '@element-plus/icons-vue'

/**
 * Props
 */
interface Props {
  /**
   * Placeholder text
   */
  placeholder?: string

  /**
   * Whether input is disabled (e.g., during streaming)
   */
  disabled?: boolean

  /**
   * Minimum rows for textarea
   */
  minRows?: number

  /**
   * Maximum rows for textarea
   */
  maxRows?: number
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '输入消息...',
  disabled: false,
  minRows: 2,
  maxRows: 8,
})

/**
 * Emits
 */
const emit = defineEmits<{
  send: [message: string]
}>()

/**
 * State
 */
const inputText = ref('')

/**
 * Dynamic rows based on content
 */
const inputRows = computed(() => {
  const lines = inputText.value.split('\n').length
  return Math.max(props.minRows, Math.min(lines, props.maxRows))
})

/**
 * Can send when:
 * 1. Input is not empty (after trimming)
 * 2. Input is not disabled
 */
const canSend = computed(() => {
  return inputText.value.trim().length > 0 && !props.disabled
})

/**
 * Handle keyboard shortcuts
 */
function handleKeyDown(event: KeyboardEvent) {
  // Enter to send (without Shift)
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSend()
  }

  // Shift+Enter to add newline (default behavior, no action needed)
}

/**
 * Send message
 */
function handleSend() {
  if (!canSend.value) return

  const message = inputText.value.trim()
  if (message) {
    emit('send', message)
    inputText.value = '' // Clear input after sending
  }
}

/**
 * Expose methods for parent component
 */
defineExpose({
  focus: () => {
    // Focus logic can be implemented if needed
  },
  clear: () => {
    inputText.value = ''
  },
})
</script>

<style scoped lang="scss">
.chat-input-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 16px;
  background: #ffffff;
  border-top: 1px solid #e4e7ed;
}

.chat-textarea {
  :deep(.el-textarea__inner) {
    font-size: 14px;
    line-height: 1.6;
    padding: 8px 12px;
    border-radius: 8px;
    border-color: #dcdfe6;
    transition: border-color 0.3s;

    &:focus {
      border-color: #409eff;
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
    }

    &:disabled {
      background-color: #f5f7fa;
      cursor: not-allowed;
    }
  }
}

.actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-hints {
  .hint-text {
    font-size: 12px;
    color: #909399;

    &.disabled {
      color: #c0c4cc;
      font-style: italic;
    }
  }
}

.input-actions {
  display: flex;
  gap: 8px;
}
</style>
