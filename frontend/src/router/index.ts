import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes: RouteRecordRaw[] = [
  // 根路径重定向到登录页
  {
    path: '/',
    redirect: '/login'
  },
  // 公共路由
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { title: '注册' }
  },
  
  // 教师端
  {
    path: '/teacher',
    component: () => import('@/layouts/TeacherLayout.vue'),
    meta: { requiresAuth: true, roles: ['teacher', 'school_admin'] },
    children: [
      {
        path: '',
        redirect: '/teacher/classes'
      },
      {
        path: 'classes',
        name: 'TeacherClasses',
        component: () => import('@/views/teacher/class/List.vue'),
        meta: { title: '我的班级' }
      },
      {
        path: 'classes/:id',
        name: 'ClassDetail',
        component: () => import('@/views/teacher/class/Detail.vue'),
        meta: { title: '班级详情' }
      },
      {
        path: 'tasks',
        name: 'TeacherTasks',
        component: () => import('@/views/teacher/task/List.vue'),
        meta: { title: '学习任务' }
      },
      {
        path: 'tasks/create',
        name: 'CreateTask',
        component: () => import('@/views/teacher/task/Create.vue'),
        meta: { title: '发布任务' }
      },
      {
        path: 'evaluations',
        name: 'TeacherEvaluations',
        component: () => import('@/views/teacher/evaluation/Grid.vue'),
        meta: { title: '日常评价' }
      },
      {
        path: 'reports',
        name: 'TeacherReports',
        component: () => import('@/views/teacher/report/List.vue'),
        meta: { title: '数据分析' }
      }
    ]
  },
  
  // 家长端
  {
    path: '/parent',
    component: () => import('@/layouts/ParentLayout.vue'),
    meta: { requiresAuth: true, roles: ['parent'] },
    children: [
      {
        path: '',
        redirect: '/parent/tasks'
      },
      {
        path: 'tasks',
        name: 'ParentTasks',
        component: () => import('@/views/parent/task/List.vue'),
        meta: { title: '学习建议' }
      },
      {
        path: 'tasks/:id',
        name: 'ParentTaskDetail',
        component: () => import('@/views/parent/task/Detail.vue'),
        meta: { title: '任务详情' }
      },
      {
        path: 'evaluations',
        name: 'ParentEvaluations',
        component: () => import('@/views/parent/evaluation/Calendar.vue'),
        meta: { title: '评价记录' }
      },
      {
        path: 'growth',
        name: 'ParentGrowth',
        component: () => import('@/views/parent/growth/Index.vue'),
        meta: { title: '成长档案' }
      }
    ]
  },
  
  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 成长印记` : '成长印记'
  
  const userStore = useUserStore()
  
  // 需要认证的路由
  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
    
    // 角色检查
    const roles = to.meta.roles as string[] | undefined
    if (roles && !roles.includes(userStore.role)) {
      next({ name: 'NotFound' })
      return
    }
  }
  
  next()
})

export default router
