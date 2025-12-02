<template>
  <div class="messages-container" ref="containerRef">
    <!-- Empty state -->
    <div v-if="messages.length === 0" class="empty-state">
      <el-empty description="开始新对话">
        <template #image>
          <el-icon :size="80" color="#909399">
            <ChatDotRound />
          </el-icon>
        </template>
        <template #description>
          <p>输入消息开始与AI助手对话</p>
          <p class="hint-text">AI助手可以帮助您分解任务、检索知识库等</p>
        </template>
      </el-empty>
    </div>

    <!-- Message list -->
    <div v-else class="messages-list">
      <MessageItem
        v-for="(message, index) in messages"
        :key="`msg-${index}`"
        :message="message"
      />

      <!-- Loading indicator (when streaming) -->
      <div v-if="isStreaming" class="loading-indicator">
        <div class="loading-dots">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
        <span class="loading-text">AI正在思考...</span>
      </div>
    </div>

    <!-- Scroll to bottom button -->
    <transition name="fade">
      <div
        v-if="showScrollButton"
        class="scroll-to-bottom"
        @click="scrollToBottom(true)"
      >
        <el-button :icon="ArrowDown" circle />
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ChatDotRound, ArrowDown } from '@element-plus/icons-vue'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chatStore'
import MessageItem from './MessageItem.vue'

/**
 * Store
 */
const chatStore = useChatStore()
const { messages, isStreaming } = storeToRefs(chatStore)

/**
 * Refs
 */
const containerRef = ref<HTMLElement | null>(null)
const showScrollButton = ref(false)

/**
 * Auto-scroll to bottom when new messages arrive
 */
watch(
  () => messages.value.length,
  async () => {
    await nextTick()
    scrollToBottom(false)
  }
)

/**
 * Auto-scroll when streaming updates content
 */
watch(
  () => messages.value[messages.value.length - 1]?.content,
  async () => {
    if (isStreaming.value) {
      await nextTick()
      scrollToBottom(false)
    }
  }
)

/**
 * Scroll to bottom with optional smooth animation
 */
function scrollToBottom(smooth: boolean = true) {
  if (!containerRef.value) return

  containerRef.value.scrollTo({
    top: containerRef.value.scrollHeight,
    behavior: smooth ? 'smooth' : 'auto',
  })
}

/**
 * Handle scroll event to show/hide scroll button
 */
function handleScroll() {
  if (!containerRef.value) return

  const { scrollTop, scrollHeight, clientHeight } = containerRef.value
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight

  // Show button if more than 200px from bottom
  showScrollButton.value = distanceFromBottom > 200
}

/**
 * Lifecycle
 */
onMounted(() => {
  if (containerRef.value) {
    containerRef.value.addEventListener('scroll', handleScroll)
  }
})

onUnmounted(() => {
  if (containerRef.value) {
    containerRef.value.removeEventListener('scroll', handleScroll)
  }
})
</script>

<style scoped lang="scss">
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600&family=Inter:wght@400&display=swap');

.messages-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  background: #FFFFFF;

  // Minimal custom scrollbar
  &::-webkit-scrollbar {
    width: 4px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background: #D6D3D1;
    border-radius: 2px;

    &:hover {
      background: #A8A29E;
    }
  }
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 80px 48px;

  :deep(.el-empty) {
    .el-empty__image {
      margin-bottom: 32px;

      .el-icon {
        color: #D6D3D1 !important;
        opacity: 0.4;
        animation: float 4s ease-in-out infinite;
      }
    }

    .el-empty__description {
      p {
        font-family: 'Inter', sans-serif;
        font-size: 15px;
        line-height: 1.6;
        color: #78716C;
        margin: 8px 0;

        &:first-child {
          font-family: 'Crimson Pro', serif;
          font-size: 18px;
          font-weight: 600;
          color: #2D2D2D;
          letter-spacing: -0.02em;
          margin-bottom: 12px;
        }
      }

      .hint-text {
        margin-top: 16px;
        font-size: 13px;
        color: #A8A29E;
        font-style: italic;
      }
    }
  }

  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-12px); }
  }
}

.messages-list {
  display: flex;
  flex-direction: column;
  padding: 24px 0;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 32px 48px;
  color: #78716C;
  opacity: 0;
  animation: fadeIn 0.4s ease-out forwards;

  @keyframes fadeIn {
    to { opacity: 1; }
  }

  .loading-dots {
    display: flex;
    gap: 6px;

    .dot {
      width: 6px;
      height: 6px;
      background: linear-gradient(135deg, #8B7355 0%, #A8A29E 100%);
      border-radius: 50%;
      animation: gentlePulse 1.6s infinite ease-in-out both;

      &:nth-child(1) {
        animation-delay: -0.32s;
      }

      &:nth-child(2) {
        animation-delay: -0.16s;
      }
    }
  }

  .loading-text {
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 400;
    font-style: italic;
    letter-spacing: 0.01em;
  }
}

@keyframes gentlePulse {
  0%, 80%, 100% {
    transform: scale(0.3);
    opacity: 0.3;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.scroll-to-bottom {
  position: absolute;
  bottom: 32px;
  right: 32px;
  z-index: 10;

  :deep(.el-button) {
    background: #FFFFFF;
    border: 1.5px solid #E7E5E4;
    color: #57534E;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      background: #FAFAF9;
      border-color: #8B7355;
      color: #2D2D2D;
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }

    &:active {
      transform: translateY(-1px);
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
