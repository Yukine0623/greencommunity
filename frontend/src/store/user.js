// import { createRouter, createWebHistory } from 'vue-router'

// // 页面组件
// import Login from '@/views/Login.vue'
// import User from '@/views/User.vue'
// import Forum from '@/views/Forum.vue'
// import Admin from '@/views/Admin.vue'

// // 布局组件
// import MainLayout from '@/layout/MainLayout.vue'

// // pinia
// import { useUserStore } from '@/store/user'

// // 路由配置
// const routes = [
//   {
//     path: '/',
//     component: Login
//   },

//   {
//     path: '/admin',
//     component: Admin
//   },

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
//       }
//     ]
//   }
// ]

// // 创建路由实例
// const router = createRouter({
//   history: createWebHistory(),
//   routes
// })

// // 🚀 路由守卫（登录拦截）
// router.beforeEach((to, from, next) => {
//   const userStore = useUserStore()

//   // 没登录不能访问用户页/论坛/管理员
//   if (
//     to.path !== '/' &&
//     !userStore.username
//   ) {
//     next('/')  // 去登录页
//   } else {
//     next()
//   }
// })

// export default router

import { defineStore } from 'pinia'

// 这个文件只负责记住：用户是谁？有没有登录？
export const useUserStore = defineStore('user', {
  state: () => ({
    username: '', // 登录后存入用户名
    token: ''     // 登录后的身份令牌
  }),
  
  actions: {
    // 登录成功时调用这个方法存数据
    setUserInfo(name) {
      this.username = name
    },
    // 退出登录时清空
    clearUserInfo() {
      this.username = ''
      this.token = ''
    }
  }
})