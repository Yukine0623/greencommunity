<template>
  <!-- 👇 管理员界面 -->
  <Admin v-if="isAdmin" />

  <!-- 👇 普通用户界面 -->
  <div v-else>
    <div v-if="!loggedIn">
      <h2>社区平台登录</h2>
      <input v-model="username" placeholder="用户名" />
      <input v-model="password" type="password" placeholder="密码" />
      <button @click="handleLogin">登录</button>
      <button @click="handleRegister">注册</button>

      <p>{{ message }}</p>
    </div>

    <div v-else>
      <h2>欢迎 {{ username }}</h2>

      <h3>申请成为邻里达人</h3>
      <input v-model="reason" placeholder="申请理由" />
      <button @click="handleApply">申请达人</button>

      <h3>发布帖子</h3>
      <input v-model="title" placeholder="标题" />
      <br />
      <textarea v-model="content" placeholder="内容"></textarea>
      <br />
      <button @click="handlePost">发布</button>

      <h3>帖子列表</h3>
      <ul>
        <li v-for="post in posts" :key="post.id">
          <strong>{{ post.title }}</strong> - {{ post.author }}
          <p>{{ post.content }}</p>
          <small>{{ post.created_at }}</small>
        </li>
      </ul>

      <button @click="logout">退出登录</button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import Admin from '/src/views/Admin.vue'

const username = ref('')
const password = ref('')
const message = ref('')
const loggedIn = ref(false)
const users = ref([])
const title = ref('')
const content = ref('')
const posts = ref([])
const reason = ref('')
const isAdmin = ref(false)

// 登录
const handleLogin = async () => {
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/login/', {
      username: username.value,
      password: password.value
    })

    message.value = res.data.message

    // 只有登录成功才存
    if (res.data.code === 200) {
      localStorage.setItem('username', username.value)

      loggedIn.value = true

      // 判断是不是管理员
      if (username.value === 'admin') {
        isAdmin.value = true
      }
    }

  } catch (err) {
    console.error(err)
    message.value = '请求失败'
  }
}

//注册
const handleRegister = async () => {
  console.log('登录函数触发了')
  
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

const fetchUsers = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/users/')
    if (res.data.code === 200) {
      users.value = res.data.users
    }
  } catch (err) {
    console.error(err)
  }
}

const handleLogout = () => {
  loggedIn.value = false
  username.value = ''
  password.value = ''
  users.value = []
  message.value = ''
}

//发帖
const handlePost = async () => {
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/post/create/', {
      title: title.value,
      content: content.value,
      author: username.value
    })

    if (res.data.code === 200) {
      fetchPosts()
      title.value = ''
      content.value = ''
    }
  } catch (err) {
    console.error(err)
  }
}

//获取帖子列表
const fetchPosts = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/post/list/')
    if (res.data.code === 200) {
      posts.value = res.data.posts
    }
  } catch (err) {
    console.error(err)
  }
}

//处理邻里达人审核申请
const handleApply = async () => {
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/apply/', {
      username: username.value,
      reason: reason.value
    })

    message.value = res.data.message
  } catch (err) {
    message.value = '申请失败'
  }
}
</script>