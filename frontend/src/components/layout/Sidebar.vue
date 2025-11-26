<template>
  <aside
    class="sidebar"
    :class="{ collapsed: uiStore.sidebarCollapsed }"
    :style="{ width: sidebarWidthPx }"
  >
    <!-- Logo和品牌 -->
    <div class="sidebar-header">
      <div class="logo-container">
        <el-icon class="logo-icon" :size="32"><ChatLineRound /></el-icon>
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
      <template v-for="item in navItems" :key="item.path">
        <!-- Action item (不是路由链接) -->
        <div
          v-if="item.isAction"
          class="nav-item action-item"
          @click="item.onClick"
        >
          <el-icon class="nav-icon" :size="20">
            <component :is="item.icon" />
          </el-icon>
          <transition name="fade">
            <span v-show="!uiStore.sidebarCollapsed" class="nav-label">{{ item.label }}</span>
          </transition>
        </div>

        <!-- Router link item -->
        <router-link
          v-else
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
      </template>
    </nav>

    <!-- 对话历史 - 使用新的SessionList组件 -->
    <div v-show="!uiStore.sidebarCollapsed" class="session-section">
      <SessionList />
    </div>

    <!-- 设置按钮 (底部固定) -->
    <router-link to="/settings" class="settings-btn" :class="{ active: isActive('/settings') }">
      <el-icon class="settings-icon" :size="20">
        <Setting />
      </el-icon>
      <transition name="fade">
        <span v-show="!uiStore.sidebarCollapsed" class="settings-label">设置</span>
      </transition>
    </router-link>

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
  HomeFilled,
  List,
  Document,
  DataAnalysis,
  ChatLineRound,
  DArrowLeft,
  DArrowRight,
  Setting
} from '@element-plus/icons-vue'
import SessionList from '@/components/chat/SessionList.vue'

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
  background: linear-gradient(180deg,
    rgba(253, 252, 248, 0.95) 0%,
    rgba(249, 247, 241, 0.98) 100%);
  backdrop-filter: blur(20px);
  border-right: 1px solid $color-border;
  box-shadow: $shadow-ink;
  display: flex;
  flex-direction: column;
  transition: width $transition-base;
  overflow: hidden;

  // 水墨边框装饰
  &::before {
    content: '';
    position: absolute;
    right: 0;
    top: 0;
    width: 2px;
    height: 100%;
    background: linear-gradient(180deg,
      rgba(136, 179, 168, 0.15) 0%,
      rgba(136, 179, 168, 0.25) 50%,
      rgba(136, 179, 168, 0.15) 100%);
    pointer-events: none;
  }

  // 折叠状态
  &.collapsed {
    .sidebar-header {
      justify-content: center;
    }

    .nav-item {
      justify-content: center;
      padding: $spacing-md;
    }
  }
}

// Logo区域
.sidebar-header {
  padding: $spacing-lg;
  border-bottom: 1px solid $color-border;
  flex-shrink: 0;
  position: relative;

  // 水墨晕染装饰
  &::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 10%;
    width: 80%;
    height: 2px;
    background: linear-gradient(90deg,
      transparent 0%,
      rgba(136, 179, 168, 0.3) 50%,
      transparent 100%);
  }

  .logo-container {
    display: flex;
    align-items: center;
    gap: $spacing-md;

    .logo-icon {
      color: $color-primary;
      filter: drop-shadow(0 2px 4px rgba(136, 179, 168, 0.2));
      transition: transform $transition-base;

      &:hover {
        transform: rotate(360deg) scale(1.1);
      }
    }

    .logo-text {
      .brand-name {
        font-family: $font-family-heading;
        font-size: $font-size-lg;
        font-weight: 600;
        background: $color-primary-gradient;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 1px;
      }

      .brand-subtitle {
        font-size: $font-size-xs;
        color: $color-text-secondary;
        margin-top: 2px;
        letter-spacing: 2px;
        font-weight: 300;
      }
    }
  }
}

// 导航菜单
.nav-menu {
  padding: $spacing-lg $spacing-md;
  flex-shrink: 0;

  .nav-item {
    position: relative;
    display: flex;
    align-items: center;
    gap: $spacing-md;
    padding: $spacing-md $spacing-lg;
    margin-bottom: $spacing-sm;
    border-radius: $radius-lg;
    color: $color-text-regular;
    text-decoration: none;
    transition: all $transition-base cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    overflow: hidden;

    // 水墨晕染效果（悬停时）
    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      background: radial-gradient(circle at center,
        rgba(136, 179, 168, 0.15) 0%,
        transparent 70%);
      opacity: 0;
      transform: scale(0.5);
      transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
      pointer-events: none;
    }

    .nav-icon {
      flex-shrink: 0;
      transition: transform $transition-base cubic-bezier(0.4, 0, 0.2, 1);
    }

    .nav-label {
      font-size: $font-size-sm;
      font-weight: 500;
      letter-spacing: 0.3px;
    }

    &:hover {
      background-color: rgba($color-primary, 0.08);
      color: $color-primary-dark;
      transform: translateX(4px);
      box-shadow: 0 2px 8px rgba(136, 179, 168, 0.12);

      &::before {
        opacity: 1;
        transform: scale(1);
      }

      .nav-icon {
        transform: scale(1.1);
      }
    }

    &.active {
      background: $color-primary-gradient;
      color: white;
      font-weight: 600;
      box-shadow: $shadow-md;

      &::before {
        display: none;
      }

      .nav-icon {
        transform: scale(1.05);
      }
    }
  }
}

// 会话历史区域 - 使用SessionList组件
.session-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

// 设置按钮 (底部固定)
.settings-btn {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md $spacing-lg;
  margin: 0 $spacing-md $spacing-md $spacing-md;
  border-radius: $radius-md;
  color: $color-text-regular;
  text-decoration: none;
  transition: all $transition-fast;
  cursor: pointer;
  flex-shrink: 0;

  .settings-icon {
    flex-shrink: 0;
  }

  .settings-label {
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

// 侧边栏折叠时设置按钮居中
.sidebar.collapsed .settings-btn {
  justify-content: center;
  padding: $spacing-md;
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
