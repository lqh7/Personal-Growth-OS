<template>
  <aside
    class="sidebar"
    :class="{ collapsed: uiStore.sidebarCollapsed }"
    :style="{ width: sidebarWidthPx }"
  >
    <!-- Logo和品牌 -->
    <div class="sidebar-header">
      <div class="logo-container">
        <el-icon class="logo-icon" :size="32"><Rocket /></el-icon>
        <transition name="fade">
          <div v-show="!uiStore.sidebarCollapsed" class="logo-text">
            <div class="brand-name">Personal Growth</div>
            <div class="brand-subtitle">OS</div>
          </div>
        </transition>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="nav-menu">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
      >
        <el-icon class="nav-icon" :size="20">
          <component :is="item.icon" />
        </el-icon>
        <transition name="fade">
          <span v-show="!uiStore.sidebarCollapsed" class="nav-label">{{ item.label }}</span>
        </transition>
      </router-link>
    </nav>

    <!-- 对话历史 - 直接在导航下方 -->
    <div class="conversation-section">
      <div v-show="!uiStore.sidebarCollapsed" class="section-header">
        <el-icon :size="16"><ChatLineRound /></el-icon>
        <span>对话记录</span>
      </div>

      <div class="conversation-list">
        <div
          v-for="conv in chatStore.conversations"
          :key="conv.id"
          class="conversation-item"
          :class="{ active: conv.isActive }"
          @click="chatStore.switchConversation(conv.id)"
        >
          <el-icon class="conv-icon" :size="18">
            <ChatDotRound />
          </el-icon>
          <transition name="fade">
            <div v-show="!uiStore.sidebarCollapsed" class="conv-content">
              <div class="conv-title">{{ conv.title }}</div>
              <div class="conv-time">{{ formatTime(conv.timestamp) }}</div>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <!-- 新建对话按钮 - 固定在底部 -->
    <div class="sidebar-footer">
      <el-button
        v-show="!uiStore.sidebarCollapsed"
        class="new-conversation-btn"
        type="primary"
        @click="chatStore.createConversation"
      >
        <el-icon><Plus /></el-icon>
        <span>新建对话</span>
      </el-button>

      <!-- 折叠按钮（已折叠时显示图标按钮） -->
      <el-button
        v-show="uiStore.sidebarCollapsed"
        class="collapsed-new-btn"
        type="primary"
        circle
        @click="chatStore.createConversation"
      >
        <el-icon><Plus /></el-icon>
      </el-button>
    </div>

    <!-- 折叠按钮 -->
    <div class="collapse-btn" @click="uiStore.toggleSidebar">
      <el-icon>
        <component :is="uiStore.sidebarCollapsed ? 'DArrowRight' : 'DArrowLeft'" />
      </el-icon>
    </div>

    <!-- 拖拽调整宽度 -->
    <div v-if="!uiStore.sidebarCollapsed" class="resize-handle" @mousedown="startResize"></div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUiStore } from '@/stores/uiStore'
import { useChatStore } from '@/stores/chatStore'
import {
  Rocket,
  HomeFilled,
  List,
  Document,
  DataAnalysis,
  ChatLineRound,
  ChatDotRound,
  Plus,
  DArrowLeft,
  DArrowRight
} from '@element-plus/icons-vue'

// ============================================
// Stores
// ============================================
const uiStore = useUiStore()
const chatStore = useChatStore()
const route = useRoute()

// ============================================
// Data
// ============================================
const navItems = [
  { path: '/dashboard', label: '工作台', icon: HomeFilled },
  { path: '/tasks', label: '任务', icon: List },
  { path: '/notes', label: '笔记', icon: Document },
  { path: '/review', label: '复盘', icon: DataAnalysis }
]

// ============================================
// Computed
// ============================================
const sidebarWidthPx = computed(() => {
  return uiStore.sidebarCollapsed ? '60px' : `${uiStore.sidebarWidth}px`
})

// ============================================
// Methods
// ============================================
function isActive(path: string) {
  return route.path === path
}

function formatTime(date: Date) {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days === 1) return '昨天'
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString()
}

function startResize(e: MouseEvent) {
  e.preventDefault()
  const startX = e.clientX
  const startWidth = uiStore.sidebarWidth

  function onMouseMove(e: MouseEvent) {
    const delta = e.clientX - startX
    const newWidth = startWidth + delta
    uiStore.setSidebarWidth(newWidth)
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

.sidebar {
  position: relative;
  height: 100vh;
  background-color: $bg-color-card;
  border-right: 1px solid $color-border;
  display: flex;
  flex-direction: column;
  transition: width $transition-base;
  overflow: hidden;

  // 折叠状态
  &.collapsed {
    .sidebar-header {
      justify-content: center;
    }

    .nav-item {
      justify-content: center;
      padding: $spacing-md;
    }

    .conversation-item {
      justify-content: center;
      padding: $spacing-sm;
    }
  }
}

// Logo区域
.sidebar-header {
  padding: $spacing-lg;
  border-bottom: 1px solid $color-border;
  flex-shrink: 0;

  .logo-container {
    display: flex;
    align-items: center;
    gap: $spacing-md;

    .logo-icon {
      color: $color-primary;
    }

    .logo-text {
      .brand-name {
        font-size: $font-size-md;
        font-weight: 600;
        color: $color-primary;
      }

      .brand-subtitle {
        font-size: $font-size-xs;
        color: $color-text-secondary;
        margin-top: 2px;
      }
    }
  }
}

// 导航菜单
.nav-menu {
  padding: $spacing-lg $spacing-md;
  flex-shrink: 0;

  .nav-item {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    padding: $spacing-md $spacing-lg;
    margin-bottom: $spacing-sm;
    border-radius: $radius-md;
    color: $color-text-regular;
    text-decoration: none;
    transition: all $transition-fast;
    cursor: pointer;

    .nav-icon {
      flex-shrink: 0;
    }

    .nav-label {
      font-size: $font-size-sm;
    }

    &:hover {
      background-color: rgba($color-primary, 0.1);
      color: $color-primary;
    }

    &.active {
      background-color: $color-primary;
      color: white;
    }
  }
}

// 对话历史区域 - 可滚动
.conversation-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: $spacing-md;
  border-top: 1px solid $color-border;

  .section-header {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    padding: $spacing-sm $spacing-md;
    font-size: $font-size-xs;
    color: $color-text-secondary;
    margin-bottom: $spacing-sm;
    flex-shrink: 0;
  }

  .conversation-list {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    @include custom-scrollbar;

    .conversation-item {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      padding: $spacing-md;
      margin-bottom: $spacing-sm;
      border-radius: $radius-md;
      cursor: pointer;
      transition: all $transition-fast;

      .conv-icon {
        flex-shrink: 0;
        color: $color-primary;
      }

      .conv-content {
        flex: 1;
        min-width: 0;

        .conv-title {
          font-size: $font-size-sm;
          color: $color-text-primary;
          @include text-ellipsis;
        }

        .conv-time {
          font-size: $font-size-xs;
          color: $color-text-secondary;
          margin-top: 2px;
        }
      }

      &:hover {
        background-color: rgba($color-primary, 0.05);
      }

      &.active {
        background-color: rgba($color-primary, 0.1);
        border-left: 3px solid $color-primary;
      }
    }
  }
}

// 底部固定区域 - 新建对话按钮
.sidebar-footer {
  padding: $spacing-md;
  border-top: 1px solid $color-border;
  background-color: $bg-color-card;
  flex-shrink: 0;

  .new-conversation-btn {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: $spacing-sm;
  }

  .collapsed-new-btn {
    width: 100%;
  }
}

// 折叠按钮
.collapse-btn {
  position: absolute;
  top: 50%;
  right: -12px;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  background-color: $bg-color-card;
  border: 1px solid $color-border;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all $transition-fast;
  z-index: 10;

  &:hover {
    background-color: $color-primary;
    color: white;
    border-color: $color-primary;
  }
}

// 拖拽调整宽度
.resize-handle {
  position: absolute;
  top: 0;
  right: 0;
  width: 4px;
  height: 100%;
  cursor: ew-resize;
  background-color: transparent;
  transition: background-color $transition-fast;

  &:hover {
    background-color: $color-primary;
  }
}

// 过渡动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity $transition-fast;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
