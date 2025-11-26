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
.messages-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  background: #ffffff;

  // Custom scrollbar
  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: #f5f7fa;
  }

  &::-webkit-scrollbar-thumb {
    background: #dcdfe6;
    border-radius: 3px;

    &:hover {
      background: #c0c4cc;
    }
  }
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px;

  .hint-text {
    margin-top: 8px;
    font-size: 13px;
    color: #909399;
  }
}

.messages-list {
  display: flex;
  flex-direction: column;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  color: #909399;

  .loading-dots {
    display: flex;
    gap: 4px;

    .dot {
      width: 8px;
      height: 8px;
      background-color: #409eff;
      border-radius: 50%;
      animation: bounce 1.4s infinite ease-in-out both;

      &:nth-child(1) {
        animation-delay: -0.32s;
      }

      &:nth-child(2) {
        animation-delay: -0.16s;
      }
    }
  }

  .loading-text {
    font-size: 14px;
    font-style: italic;
  }
}

@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.scroll-to-bottom {
  position: absolute;
  bottom: 20px;
  right: 20px;
  z-index: 10;

  .el-button {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
