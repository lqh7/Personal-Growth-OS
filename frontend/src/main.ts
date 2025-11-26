import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { templateStorage } from './services/templateStorage'

// 导入全局样式
import '@/assets/styles/global.scss'
// 导入Element Plus主题覆盖样式
import '@/assets/styles/element-theme.scss'

// Initialize built-in templates on app startup
templateStorage.initializeBuiltinTemplates()

const app = createApp(App)

// Register Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
