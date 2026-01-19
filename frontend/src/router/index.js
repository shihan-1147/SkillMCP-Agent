/**
 * 路由配置
 */
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Console',
    component: () => import('@/views/ConsoleView.vue'),
    meta: { title: 'Agent Console' }
  },
  {
    path: '/debug',
    name: 'Debug',
    component: () => import('@/views/DebugView.vue'),
    meta: { title: '调试面板' }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  document.title = `${to.meta.title || 'Console'} | SkillMCP Agent`
  next()
})

export default router
