import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
  // ============================================
  // State
  // ============================================
  const sidebarCollapsed = ref(false)
  const sidebarWidth = ref(200) // 默认200px
  const chatPanelWidthPercent = ref(40) // 默认占主内容区域的40%
  const theme = ref<'light' | 'dark'>('light')

  // ============================================
  // Actions
  // ============================================

  /**
   * 切换侧边栏折叠状态
   */
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  /**
   * 设置侧边栏宽度
   * @param width - 新宽度（180-240px之间）
   */
  function setSidebarWidth(width: number) {
    // 限制宽度范围
    const minWidth = 180
    const maxWidth = 240
    sidebarWidth.value = Math.max(minWidth, Math.min(maxWidth, width))
  }

  /**
   * 设置Chat面板宽度百分比
   * @param percent - 新百分比（40%-60%之间）
   */
  function setChatPanelWidthPercent(percent: number) {
    // 限制百分比范围：40%-60%
    const minPercent = 40
    const maxPercent = 60
    chatPanelWidthPercent.value = Math.max(minPercent, Math.min(maxPercent, percent))
  }

  /**
   * 设置主题
   * @param newTheme - 'light' 或 'dark'
   */
  function setTheme(newTheme: 'light' | 'dark') {
    theme.value = newTheme
    // 未来可以在这里切换Element Plus主题
  }

  return {
    // State
    sidebarCollapsed,
    sidebarWidth,
    chatPanelWidthPercent,
    theme,

    // Actions
    toggleSidebar,
    setSidebarWidth,
    setChatPanelWidthPercent,
    setTheme
  }
})
