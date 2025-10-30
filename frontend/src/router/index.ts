/**
 * Vue Router configuration
 */
import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: MainLayout,
      redirect: '/dashboard',
      children: [
        {
          path: '/dashboard',
          name: 'Dashboard',
          component: () => import('@/views/DashboardView.vue'),
          meta: { title: '工作台' }
        },
        {
          path: '/tasks',
          name: 'TasksView',
          component: () => import('@/views/TasksView.vue'),
          meta: { title: '任务' }
        },
        {
          path: '/notes',
          name: 'NotesView',
          component: () => import('@/views/NotesView.vue'),
          meta: { title: '笔记' }
        },
        {
          path: '/review',
          name: 'ReviewView',
          component: () => import('@/views/ReviewView.vue'),
          meta: { title: '复盘' }
        }
      ]
    }
  ]
})

export default router
