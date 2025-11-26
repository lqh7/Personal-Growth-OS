<template>
  <div class="main-layout">
    <!-- 左侧边栏 -->
    <Sidebar />

    <!-- 主内容区域容器（Main + Chat） -->
    <div class="content-container">
      <!-- AI助手触发按钮 (右上角固定) -->
      <div
        v-if="!chatStore.isChatPanelVisible"
        class="ai-trigger-btn"
        @click="chatStore.toggleChatPanel"
      >
        <el-tooltip content="打开AI助手" placement="left">
          <el-button :icon="ChatDotRound" circle size="large" type="primary" />
        </el-tooltip>
      </div>

      <!-- 中间主内容区 -->
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>

      <!-- 拖拽分隔线 (只在ChatPanel可见时显示) -->
      <div
        v-if="chatStore.isChatPanelVisible"
        class="resize-divider"
        @mousedown="startResize"
      ></div>

      <!-- 右侧AI Chat面板 -->
      <ChatPanel
        v-if="chatStore.isChatPanelVisible"
        :style="{ width: `${uiStore.chatPanelWidthPercent}%` }"
      />
    </div>

    <!-- Keyboard Shortcuts Help Dialog -->
    <el-dialog v-model="showShortcutsHelp" title="键盘快捷键" width="600px">
      <div class="shortcuts-help">
        <div class="shortcut-section">
          <h4>导航</h4>
          <div class="shortcut-item">
            <kbd>Ctrl/Cmd + 1</kbd>
            <span>工作台</span>
          </div>
          <div class="shortcut-item">
            <kbd>Ctrl/Cmd + 2</kbd>
            <span>任务管理</span>
          </div>
          <div class="shortcut-item">
            <kbd>Ctrl/Cmd + 3</kbd>
            <span>笔记管理</span>
          </div>
          <div class="shortcut-item">
            <kbd>Ctrl/Cmd + 4</kbd>
            <span>数据复盘</span>
          </div>
        </div>

        <div class="shortcut-section">
          <h4>操作</h4>
          <div class="shortcut-item">
            <kbd>Ctrl/Cmd + K</kbd>
            <span>快速创建任务</span>
          </div>
          <div class="shortcut-item">
            <kbd>Ctrl/Cmd + N</kbd>
            <span>创建笔记</span>
          </div>
          <div class="shortcut-item">
            <kbd>Ctrl/Cmd + /</kbd>
            <span>切换侧边栏</span>
          </div>
          <div class="shortcut-item">
            <kbd>?</kbd>
            <span>显示此帮助</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showShortcutsHelp = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUiStore } from '@/stores/uiStore'
import { useChatStore } from '@/stores/chatStore'
import { ChatDotRound } from '@element-plus/icons-vue'
import Sidebar from '@/components/layout/Sidebar.vue'
import ChatPanel from '@/components/chat/ChatPanel.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'

// ============================================
// Stores & Router
// ============================================
const uiStore = useUiStore()
const chatStore = useChatStore()
const router = useRouter()

// ============================================
// State
// ============================================
const showShortcutsHelp = ref(false)

// ============================================
// Resize Logic for ChatPanel Divider
// ============================================

/**
 * Start resizing ChatPanel width via draggable divider
 */
function startResize(event: MouseEvent) {
  event.preventDefault()

  const startX = event.clientX
  const startPercent = uiStore.chatPanelWidthPercent
  const contentContainer = (event.target as HTMLElement).parentElement

  if (!contentContainer) return

  const containerWidth = contentContainer.offsetWidth

  function onMouseMove(e: MouseEvent) {
    // Calculate delta in pixels
    const deltaX = startX - e.clientX // Reversed: dragging left increases chat width

    // Convert delta to percentage
    const deltaPercent = (deltaX / containerWidth) * 100

    // Calculate new percentage
    const newPercent = startPercent + deltaPercent

    // Update via uiStore (with built-in constraints: 25%-70%)
    uiStore.setChatPanelWidthPercent(newPercent)
  }

  function onMouseUp() {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
  document.body.style.cursor = 'ew-resize'
  document.body.style.userSelect = 'none'
}

// ============================================
// Keyboard Shortcuts
// ============================================
useKeyboardShortcuts([
  {
    key: '1',
    ctrl: true,
    description: '跳转到工作台',
    handler: () => router.push('/')
  },
  {
    key: '2',
    ctrl: true,
    description: '跳转到任务管理',
    handler: () => router.push('/tasks')
  },
  {
    key: '3',
    ctrl: true,
    description: '跳转到笔记管理',
    handler: () => router.push('/notes')
  },
  {
    key: '4',
    ctrl: true,
    description: '跳转到数据复盘',
    handler: () => router.push('/review')
  },
  {
    key: 'k',
    ctrl: true,
    description: '快速创建任务',
    handler: () => {
      if (router.currentRoute.value.path !== '/tasks') {
        router.push('/tasks')
      }
      // Emit event for task creation (handled in TasksView)
    }
  },
  {
    key: 'n',
    ctrl: true,
    description: '创建笔记',
    handler: () => {
      if (router.currentRoute.value.path !== '/notes') {
        router.push('/notes')
      }
      // Emit event for note creation (handled in NotesView)
    }
  },
  {
    key: '/',
    ctrl: true,
    description: '切换侧边栏',
    handler: () => uiStore.toggleSidebar()
  },
  {
    key: ',',
    ctrl: true,
    description: '打开设置',
    handler: () => router.push('/settings')
  },
  {
    key: '?',
    description: '显示快捷键帮助',
    handler: () => {
      showShortcutsHelp.value = true
    }
  }
])
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';
@import '@/assets/styles/mixins.scss';

.main-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background-color: $bg-color-page;
}

// 主内容区域容器（包含Main Content和Chat Panel）
.content-container {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
  min-width: 0; // 防止flex子元素溢出
}

.main-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: $spacing-xl;
  min-width: 600px; // 设计要求:主内容区最小宽度
  @include custom-scrollbar;

  // 添加内容区淡入动画
  animation: contentFadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);

  @keyframes contentFadeIn {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
}

// AI助手触发按钮 (右上角固定位置)
.ai-trigger-btn {
  position: fixed;
  top: $spacing-lg;
  right: $spacing-lg;
  z-index: 100;

  // 添加淡入动画
  animation: fadeIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);

  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: scale(0.8) rotate(-10deg);
    }
    to {
      opacity: 1;
      transform: scale(1) rotate(0deg);
    }
  }

  :deep(.el-button) {
    background: $color-primary-gradient;
    border: none;
    box-shadow: $shadow-md;
    transition: all $transition-base cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      transform: translateY(-2px) scale(1.05);
      box-shadow: $shadow-lg;
    }

    &:active {
      transform: translateY(0) scale(0.98);
    }
  }
}

// 拖拽分隔线
.resize-divider {
  width: 4px;
  background: transparent;
  cursor: ew-resize;
  transition: all $transition-base;
  flex-shrink: 0; // 不允许压缩
  position: relative;

  // 水墨笔触效果
  &::before {
    content: '';
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 2px;
    height: 40px;
    background: linear-gradient(180deg,
      transparent 0%,
      rgba(136, 179, 168, 0.3) 50%,
      transparent 100%);
    opacity: 0;
    transition: opacity $transition-base;
  }

  &:hover {
    background: linear-gradient(180deg,
      rgba(136, 179, 168, 0.1) 0%,
      rgba(136, 179, 168, 0.2) 50%,
      rgba(136, 179, 168, 0.1) 100%);

    &::before {
      opacity: 1;
    }
  }

  &:active {
    background: linear-gradient(180deg,
      rgba(136, 179, 168, 0.15) 0%,
      rgba(136, 179, 168, 0.3) 50%,
      rgba(136, 179, 168, 0.15) 100%);
  }
}

// 页面切换动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity $transition-fast;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// ============================================
// Keyboard Shortcuts Help
// ============================================
.shortcuts-help {
  display: flex;
  flex-direction: column;
  gap: $spacing-xl;

  .shortcut-section {
    h4 {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $color-text-primary;
      margin: 0 0 $spacing-md 0;
      border-bottom: 1px solid $color-border;
      padding-bottom: $spacing-sm;
    }

    .shortcut-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: $spacing-md 0;
      border-bottom: 1px solid $color-border;

      &:last-child {
        border-bottom: none;
      }

      kbd {
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: $font-size-xs;
        font-weight: 600;
        padding: $spacing-xs $spacing-sm;
        background-color: $bg-color-hover;
        border: 1px solid $color-border;
        border-radius: $radius-sm;
        box-shadow: 0 2px 0 rgba(0, 0, 0, 0.05);
        white-space: nowrap;
      }

      span {
        font-size: $font-size-sm;
        color: $color-text-regular;
      }
    }
  }
}
</style>
