<template>
  <div class="chat-panel" :style="{ width: `${width}px` }">
    <!-- 头部 -->
    <div class="chat-header">
      <div class="header-title">
        <el-icon class="title-icon" :size="24">
          <ChatLineRound />
        </el-icon>
        <span class="title-text">AI 对话</span>
      </div>
      <div class="header-subtitle">{{ chatStore.currentConversation?.title || '新对话' }}</div>
    </div>

    <!-- 消息列表 -->
    <div class="message-list" ref="messageListRef">
      <div
        v-for="message in chatStore.currentMessages"
        :key="message.id"
        class="message-item"
        :class="message.role"
      >
        <div class="message-bubble">
          <div class="message-content" v-html="formatMessage(message.content)"></div>
          <div class="message-time">{{ formatTime(message.timestamp) }}</div>

          <!-- AI消息的操作按钮 -->
          <div v-if="message.role === 'assistant' && message.actions" class="message-actions">
            <el-button
              v-for="action in message.actions"
              :key="action.type"
              size="small"
              type="primary"
              text
              @click="handleAction(action)"
            >
              {{ action.label }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="chatStore.loading" class="message-item assistant">
        <div class="message-bubble loading">
          <el-icon class="is-loading">
            <Loading />
          </el-icon>
          <span>思考中...</span>
        </div>
      </div>
    </div>

    <!-- 输入框 -->
    <div class="chat-input">
      <el-input
        v-model="inputMessage"
        type="textarea"
        :rows="3"
        placeholder="输入消息... (Shift+Enter换行，Enter发送)"
        @keydown.enter.exact="handleSend"
      />
      <div class="input-footer">
        <el-button type="primary" @click="handleSend" :disabled="!inputMessage.trim()">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore, type MessageAction } from '@/stores/chatStore'
import { ElMessage } from 'element-plus'
import { Loading, ChatLineRound } from '@element-plus/icons-vue'

// ============================================
// Props
// ============================================
interface Props {
  width?: number
}

const props = withDefaults(defineProps<Props>(), {
  width: 450
})

// ============================================
// Stores & Router
// ============================================
const chatStore = useChatStore()
const router = useRouter()

// ============================================
// State
// ============================================
const inputMessage = ref('')
const messageListRef = ref<HTMLElement | null>(null)

// ============================================
// Methods
// ============================================
async function handleSend() {
  const message = inputMessage.value.trim()
  if (!message) return

  await chatStore.sendMessage(message)
  inputMessage.value = ''

  // 滚动到底部
  nextTick(() => {
    scrollToBottom()
  })
}

function formatMessage(content: string) {
  // 简单的换行处理
  return content.replace(/\n/g, '<br>')
}

function formatTime(date: Date) {
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function scrollToBottom() {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

function handleAction(action: MessageAction) {
  switch (action.type) {
    case 'create_task':
      ElMessage.success('跳转到任务创建页面')
      router.push('/tasks')
      break

    case 'create_note':
      ElMessage.success('跳转到笔记创建页面')
      router.push('/notes')
      break

    case 'navigate':
      if (action.payload?.route) {
        router.push(action.payload.route)
      }
      break

    case 'search':
      ElMessage.info(`搜索: ${action.payload?.query}`)
      break

    default:
      console.log('未处理的操作:', action)
  }
}

// ============================================
// Watch
// ============================================
watch(
  () => chatStore.currentMessages.length,
  () => {
    nextTick(() => {
      scrollToBottom()
    })
  }
)
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';
@import '@/assets/styles/mixins.scss';

.chat-panel {
  height: 100vh;
  background-color: $bg-color-card;
  border-left: 1px solid $color-border;
  display: flex;
  flex-direction: column;
}

// 头部
.chat-header {
  padding: $spacing-lg;
  border-bottom: 1px solid $color-border;

  .header-title {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    font-size: $font-size-lg;
    font-weight: 600;
    color: $color-text-primary;

    .title-icon {
      color: $color-primary;
    }
  }

  .header-subtitle {
    font-size: $font-size-xs;
    color: $color-text-secondary;
    margin-top: $spacing-xs;
  }
}

// 消息列表
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: $spacing-lg;
  @include custom-scrollbar;

  .message-item {
    margin-bottom: $spacing-lg;
    display: flex;

    // 用户消息 - 右对齐
    &.user {
      justify-content: flex-end;

      .message-bubble {
        background: $color-primary-gradient;
        color: white;
        border-radius: $radius-lg $radius-lg 0 $radius-lg;
      }
    }

    // AI消息 - 左对齐
    &.assistant {
      justify-content: flex-start;

      .message-bubble {
        background-color: #f0f2f5;
        color: $color-text-primary;
        border-radius: $radius-lg $radius-lg $radius-lg 0;

        &.loading {
          display: flex;
          align-items: center;
          gap: $spacing-sm;
          padding: $spacing-md $spacing-lg;
        }
      }
    }

    .message-bubble {
      max-width: 70%;
      padding: $spacing-md $spacing-lg;
      box-shadow: $shadow-sm;

      .message-content {
        font-size: $font-size-sm;
        line-height: 1.6;
        word-break: break-word;
      }

      .message-time {
        font-size: $font-size-xs;
        opacity: 0.7;
        margin-top: $spacing-xs;
      }

      .message-actions {
        display: flex;
        flex-wrap: wrap;
        gap: $spacing-sm;
        margin-top: $spacing-md;
        padding-top: $spacing-md;
        border-top: 1px solid rgba(0, 0, 0, 0.1);
      }
    }
  }
}

// 输入框
.chat-input {
  padding: $spacing-lg;
  border-top: 1px solid $color-border;

  .input-footer {
    display: flex;
    justify-content: flex-end;
    margin-top: $spacing-md;
  }
}
</style>
