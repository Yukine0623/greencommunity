<template>
  <div class="register-container">
    <div class="register-card">
      <h2>创建账户</h2>
      <div class="form-group">
        <input v-model.trim="username" placeholder="用户名" maxlength="50" />
        <input v-model="password" type="password" placeholder="密码" maxlength="128" @keyup.enter="handleRegister" />
        <input v-model="confirmPassword" type="password" placeholder="确认密码" maxlength="128" @keyup.enter="handleRegister" />
      </div>
      <div class="button-group">
        <button class="btn-register" @click="handleRegister">提交注册</button>
        <button class="btn-back" @click="goLogin">返回登录</button>
      </div>
      <p :class="['status-msg', isError ? 'error' : 'success']" v-if="message">{{ message }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const message = ref('')
const isError = ref(false)

const handleRegister = async () => {
  if (!username.value || !password.value) {
    isError.value = true
    message.value = '请填写用户名和密码'
    return
  }
  if (password.value !== confirmPassword.value) {
    isError.value = true
    message.value = '两次输入的密码不一致'
    return
  }

  try {
    isError.value = false
    const res = await axios.post('http://127.0.0.1:8000/api/register/', {
      username: username.value,
      password: password.value
    })
    message.value = res.data.message || '注册成功'
    if (res.data.code === 200) {
      setTimeout(() => router.push('/'), 500)
    } else {
      isError.value = true
    }
  } catch (error) {
    isError.value = true
    message.value = error.response?.data?.message || '注册失败，请稍后重试'
  }
}

const goLogin = () => {
  router.push('/')
}
</script>

<style scoped>
.register-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.register-card {
  background: rgba(255, 255, 255, 0.92);
  padding: 2.5rem;
  border-radius: 15px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  width: 360px;
  text-align: center;
}
h2 { color: #111827; margin-bottom: 1.5rem; font-weight: 700; }
.form-group { display: flex; flex-direction: column; gap: 14px; }
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
  font-weight: 700;
  transition: opacity 0.3s;
}
.btn-register { background: #667eea; color: white; }
.btn-back { background: #eee; color: #555; }
button:hover { opacity: 0.9; }
.status-msg { margin-top: 15px; font-size: 14px; }
.error { color: #e74c3c; }
.success { color: #2ecc71; }
</style>
