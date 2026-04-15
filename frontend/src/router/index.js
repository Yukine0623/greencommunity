// import { createRouter, createWebHistory } from 'vue-router'

// import Login from '../views/Login.vue'
// import User from '../views/User.vue'
// import Admin from '../views/Admin.vue'
// import Forum from '../views/Forum.vue'
// import MyPosts from '../views/MyPosts.vue'

// // Layout
// import MainLayout from '../layout/MainLayout.vue'
// import AdminLayout from '../layout/AdminLayout.vue'

// const routes = [

//   // ✅ 登录页（无layout）
//   {
//     path: '/',
//     component: Login
//   },

//   // ✅ 用户端 layout
//   {
//     path: '/',
//     component: MainLayout,
//     children: [
//       {
//         path: 'user',
//         component: User
//       },
//       {
//         path: 'forum',
//         component: Forum
//       },
//       {
//         path:'/my-posts',
//         component: MyPosts
//       }
//     ]
//   },

//   // ✅ 管理员 layout
//   {
//     path: '/admin',
//     component: AdminLayout,
//     children: [
//       {
//         path: '',
//         component: Admin
//       }
//     ]
//   }

// ]

// // const routes = [
// //   {
// //     path: '/',
// //     component: Login
// //   },
// //   {
// //     path: '/user',
// //     component: User
// //   },
// //   {
// //     path: '/admin',
// //     component: Admin
// //   },
// //   {
// //     path: '/forum',
// //     component: Forum
// //   },
// //   {
// //     path: '/my-posts',
// //     component: MyPosts
// //   }
// // ]

// const router = createRouter({
//   history: createWebHistory(),
//   routes
// })

// /* 🔥 路由守卫（核心） */
// router.beforeEach((to, from, next) => {
//   const username = localStorage.getItem('username')
//   const role = localStorage.getItem('role')

//   // 1️⃣ 没登录 → 只能去登录页
//   if (!username && to.path !== '/') {
//     return next('/')
//   }

//   // 2️⃣ 访问 admin，但不是管理员
//   if (to.path === '/admin' && role !== 'admin') {
//     alert('没有权限访问管理员页面')
//     return next('/user')
//   }

//   // 3️⃣ 已登录访问登录页 → 重定向
//   if (to.path === '/' && username) {
//     if (role === 'admin') {
//       return next('/admin')
//     } else {
//       return next('/user')
//     }
//   }

//   next()
// })

// export default router

import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user' // 引入上面的 store

// 1. 导入页面组件
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import User from '@/views/User.vue'
import Forum from '@/views/Forum.vue'
import Admin from '@/views/Admin.vue'

// 2. 导入布局组件 (注意：如果你的文件夹叫 layout，请把下面的 s 去掉)
import MainLayout from '@/layout/MainLayout.vue'
import TaskMarket from '../views/TaskMarket.vue'
import MyTasks from '../views/MyTasks.vue'

const routes = [
  {
    path: '/',
    name: 'login',
    component: Login
  },
  {
    path: '/register',
    name: 'register',
    component: Register
  },
  {
    path: '/admin',
    name: 'admin',
    component: Admin
  },
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: 'user',
        name: 'user',
        component: User
      },
      {
        path: 'forum',
        name: 'forum',
        component: Forum
      },
      {
        path: 'tasks',
        name: 'tasks',
        component: TaskMarket
      },
      {
        path:'mytasks',
        name:'mytasks',
        component:MyTasks
      },

    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 3. 🚀 路由守卫：负责拦截逻辑
router.beforeEach((to, from, next) => {
  const userStore = useUserStore() // 在守卫内部获取 store 实例

  // 如果访问的不是登录页，且用户名为空（未登录）
  if (!['/', '/register'].includes(to.path) && !userStore.username) {
    console.warn('未登录，拦截并跳转到登录页')
    next('/')
  } else {
    next() // 放心通行
  }
})

export default router
