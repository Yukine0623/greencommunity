<!-- <template>
  <div>
    <h2>社区平台登录</h2>

    <input v-model="username" placeholder="用户名" />
    <input v-model="password" type="password" placeholder="密码" />

    <button @click="handleLogin">登录</button>
    <button @click="handleRegister">注册</button>

    <p>{{ message }}</p>
  </div>
</template>

<script setup>
import { useUserStore } from '@/store/user'

import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'


const userStore = useUserStore()

const router = useRouter()

const username = ref('')
const password = ref('')
const message = ref('')

// 登录
const handleLogin = async () => {
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/login/', {
      username: username.value,
      password: password.value
    })

    message.value = res.data.message

    if (res.data.code === 200) {
      // localStorage.setItem('username', username.value)
      // localStorage.setItem('role', res.data.role)

      // ✅ 🔥 关键新增：写入 Pinia
      userStore.setUser({
        username: username.value,
        role: res.data.role
      })

      if (res.data.role === 'admin') {
        router.push('/admin')
      } else {
        router.push('/user')
      }
    }

  } catch (err) {
    message.value = '请求失败'
  }
}

// 注册
const handleRegister = async () => {
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/register/', {
      username: username.value,
      password: password.value
    })
    message.value = res.data.message
  } catch (err) {
    message.value = '注册失败'
  }
}




</script> -->

<template>
  <div class="login-container">
    <div class="login-card">
      <h2>社区平台</h2>
      <div class="form-group">
        <input v-model="username" placeholder="用户名" />
        <input v-model="password" type="password" placeholder="密码" @keyup.enter="handleLogin" />
      </div>
      <div class="button-group">
        <button class="btn-login" @click="handleLogin">登录</button>
        <button class="btn-register" @click="handleRegister">注册</button>
      </div>
      <p :class="['status-msg', isError ? 'error' : 'success']" v-if="message">{{ message }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const message = ref('')
const isError = ref(false)

const handleLogin = async () => {
  try {
    isError.value = false
    const res = await axios.post('http://127.0.0.1:8000/api/login/', {
      username: username.value,
      password: password.value
    })

    message.value = res.data.message

    if (res.data.code === 200) {
      userStore.setUserInfo({
        username: username.value,
        role: res.data.role,
        points: res.data.points || 0
      })
      
      // 根据角色跳转
      if (res.data.role === 'admin') {
        router.push('/admin')
      } else {
        router.push('/user')
      }
    } else {
      isError.value = true
    }
  } catch (err) {
    isError.value = true
    // 打印具体错误到控制台，方便排查是否是 CORS 或 404
    console.error('Login Error:', err)
    message.value = err.response?.data?.message || '网络请求失败，请检查后端服务'
  }
}

const handleRegister = async () => {
  try {
    isError.value = false
    const res = await axios.post('http://127.0.0.1:8000/api/register/', {
      username: username.value,
      password: password.value
    })
    message.value = res.data.message
  } catch (err) {
    isError.value = true
    message.value = '注册出错'
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  background: rgba(255, 255, 255, 0.9);
  padding: 2.5rem;
  border-radius: 15px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  width: 350px;
  text-align: center;
}
h2 { color: #333; margin-bottom: 1.5rem; font-weight: 600; }
.form-group { display: flex; flex-direction: column; gap: 15px; }
input {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  outline: none;
  transition: border 0.3s;
}
input:focus { border-color: #667eea; }
.button-group {
  margin-top: 20px;
  display: flex;
  gap: 10px;
}
button {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: opacity 0.3s;
}
.btn-login { background: #667eea; color: white; }
.btn-register { background: #eee; color: #555; }
button:hover { opacity: 0.9; }
.status-msg { margin-top: 15px; font-size: 14px; }
.error { color: #e74c3c; }
.success { color: #2ecc71; }
</style>
