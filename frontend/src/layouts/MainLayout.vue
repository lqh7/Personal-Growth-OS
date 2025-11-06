<template>
  <div class="main-layout">
    <!-- 左侧边栏 -->
    <Sidebar />

    <!-- 主内容区域容器（Main + Chat） -->
    <div class="content-container">
      <!-- 中间主内容区 -->
      <main class="main-content" :style="{ flex: `0 0 ${mainContentWidthPercent}%` }">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>

      <!-- 拖拽调整宽度的分隔线 -->
      <div class="resize-divider" @mousedown="startResize"></div>

      <!-- 右侧AI Chat面板 -->
      <div class="chat-panel-container" :style="{ flex: `0 0 ${uiStore.chatPanelWidthPercent}%` }">
        <ChatPanel />
      </div>
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
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUiStore } from '@/stores/uiStore'
import Sidebar from '@/components/layout/Sidebar.vue'
import ChatPanel from '@/components/layout/ChatPanel.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'

// ============================================
// Stores & Router
// ============================================
const uiStore = useUiStore()
const router = useRouter()

// ============================================
// State
// ============================================
const showShortcutsHelp = ref(false)

// ============================================
// Computed
// ============================================
const mainContentWidthPercent = computed(() => {
  return 100 - uiStore.chatPanelWidthPercent
})

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
    key: '?',
    description: '显示快捷键帮助',
    handler: () => {
      showShortcutsHelp.value = true
    }
  }
])

// ============================================
// Methods - 拖拽调整Chat面板宽度
// ============================================
function startResize(e: MouseEvent) {
  e.preventDefault()

  const contentContainer = (e.target as HTMLElement).parentElement
  if (!contentContainer) return

  const containerWidth = contentContainer.offsetWidth
  const startX = e.clientX
  const startChatPercent = uiStore.chatPanelWidthPercent

  function onMouseMove(e: MouseEvent) {
    const deltaX = e.clientX - startX
    const deltaPercent = (deltaX / containerWidth) * 100
    const newChatPercent = startChatPercent - deltaPercent // 减号因为向左拖动增加Chat宽度

    uiStore.setChatPanelWidthPercent(newChatPercent)
  }

  function onMouseUp() {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}
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
  overflow-y: auto;
  overflow-x: hidden; // 防止横向溢出
  padding: $spacing-xl;
  min-width: 0; // 允许flex收缩
  @include custom-scrollbar;
}

// 拖拽分隔线
.resize-divider {
  width: 4px;
  cursor: ew-resize;
  background-color: transparent;
  transition: background-color $transition-fast;
  flex-shrink: 0;
  position: relative;

  &:hover {
    background-color: $color-primary;
  }

  // 增加可点击区域
  &::before {
    content: '';
    position: absolute;
    left: -4px;
    right: -4px;
    top: 0;
    bottom: 0;
  }
}

.chat-panel-container {
  min-width: 0; // 允许flex收缩
  overflow: hidden;
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
