// 全局用户状态
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    username: '',
    role: ''
  }),

  actions: {
    setUser(data) {
      this.username = data.username
      this.role = data.role
    }
  }
})