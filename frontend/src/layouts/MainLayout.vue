<template>
  <div class="main-layout">
    <!-- 左侧边栏 -->
    <Sidebar />

    <!-- 主内容区域容器（Main + Chat） -->
    <div class="content-container">
      <!-- 中间主内容区 -->
      <main class="main-content" :style="{ width: mainContentWidthPercent + '%' }">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>

      <!-- 拖拽调整宽度的分隔线 -->
      <div class="resize-divider" @mousedown="startResize"></div>

      <!-- 右侧AI Chat面板 -->
      <div class="chat-panel-container" :style="{ width: uiStore.chatPanelWidthPercent + '%' }">
        <ChatPanel />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUiStore } from '@/stores/uiStore'
import Sidebar from '@/components/layout/Sidebar.vue'
import ChatPanel from '@/components/layout/ChatPanel.vue'

// ============================================
// Stores
// ============================================
const uiStore = useUiStore()

// ============================================
// Computed
// ============================================
const mainContentWidthPercent = computed(() => {
  return 100 - uiStore.chatPanelWidthPercent
})

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
  padding: $spacing-xl;
  min-width: 600px; // 确保主内容区最小宽度
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
  min-width: 350px; // Chat面板最小宽度
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
</style>
