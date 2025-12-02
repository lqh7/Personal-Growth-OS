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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap');

.chat-input-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 32px 24px;
  background: linear-gradient(to top, #FFFFFF 0%, #FAFAF9 100%);
  border-top: 1px solid #E7E5E4;
}

.chat-textarea {
  :deep(.el-textarea__inner) {
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    line-height: 1.65;
    padding: 14px 16px;
    border-radius: 10px;
    border: 1.5px solid #E7E5E4;
    background: #FFFFFF;
    color: #2D2D2D;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    letter-spacing: -0.011em;

    &::placeholder {
      color: #A8A29E;
      font-style: italic;
    }

    &:hover {
      border-color: #D6D3D1;
    }

    &:focus {
      border-color: #8B7355;
      box-shadow: 0 0 0 3px rgba(139, 115, 85, 0.08);
      outline: none;
    }

    &:disabled {
      background-color: #FAFAF9;
      border-color: #E7E5E4;
      cursor: not-allowed;
      opacity: 0.6;
    }
  }
}

.actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 4px;
}

.input-hints {
  .hint-text {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 400;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    color: #A8A29E;

    &.disabled {
      color: #D6D3D1;
      font-style: italic;
    }
  }
}

.input-actions {
  display: flex;
  gap: 10px;

  :deep(.el-button--primary) {
    background: linear-gradient(135deg, #2D2D2D 0%, #3F3F3F 100%);
    border: none;
    color: #FFFFFF;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: -0.01em;
    padding: 10px 24px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      background: linear-gradient(135deg, #3F3F3F 0%, #525252 100%);
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    &:active {
      transform: translateY(0);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
    }

    &.is-disabled {
      background: #E7E5E4;
      color: #A8A29E;
      box-shadow: none;
      cursor: not-allowed;

      &:hover {
        transform: none;
      }
    }

    &.is-loading {
      background: #D6D3D1;

      .el-icon {
        color: #78716C;
      }
    }
  }
}
</style>
