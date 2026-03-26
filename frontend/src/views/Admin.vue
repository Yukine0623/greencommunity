<template>
  <div class="admin-container">

    <!-- 左侧菜单 -->
    <div class="sidebar">
      <p>您好，{{ adminName || '管理员' }}</p>
      <button @click="logout">退出登录</button>

      <ul>
        <h2>管理中心</h2>
        <li @click="switchView('users')">用户列表</li>
        <li @click="switchView('apply')">申请审核</li>
      </ul>
    </div>

    <!-- 右侧内容 -->
    <div class="main">

      <div class="header">
        <span>管理员后台</span>
      </div>

      <div class="filter-bar">
        <input v-model="searchName" placeholder="输入用户名搜索" />

        <select v-model="filterRole">
          <option value="">全部角色</option>
          <option value="user">普通用户</option>
          <option value="expert">邻里达人</option>
          <option value="admin">管理员</option>
        </select>
      </div>

      <!-- 用户列表 -->
      <div v-if="currentView === 'users'">
        <h3>用户列表</h3>
        <button @click="fetchUsers">刷新列表</button>

        <table class="user-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>用户名</th>
              <th>角色</th>
              <th>电话</th>
              <th>注册时间</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="user in paginatedUsers" :key="user.id">
              <td>{{ user.id }}</td>
              <td>{{ user.username }}</td>

              <!-- 角色优化显示 -->
              <td>
                <span :class="getRoleClass(user.role)">
                  {{ formatRole(user.role) }}
                </span>
              </td>

              <td>{{ user.phone || '暂无' }}</td>
              <td>{{ user.created_at }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 申请审核 -->
      <div v-if="currentView === 'apply'">
        <h3>邻里达人审核</h3>

        <!-- 搜索 -->
        <div style="margin-bottom: 10px;">
          <input v-model="searchName" placeholder="输入用户名" />
          <button @click="fetchApplications">查询</button>
        </div>

        <!-- 表格 -->
        <table>
          <thead>
            <tr>
              <th>用户名</th>
              <th>申请理由</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="item in filteredApplications" :key="item.id">
              <td>{{ item.username }}</td>
              <td>{{ item.reason }}</td>

              <td>
                <span class="pending" v-if="item.status === 'pending'">待审核</span>
                <span class="approved" v-else-if="item.status === 'approved'">已通过</span>
                <span class="rejected" v-else>已拒绝</span>
              </td>

              <td>
                <button 
                  v-if="item.status === 'pending'" 
                  @click="approve(item.username)">
                  通过
                </button>

                <button 
                  v-if="item.status === 'pending'" 
                  @click="reject(item.username)">
                  拒绝
                </button>

                <span v-else>已处理</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination">
          <button @click="currentPage--" :disabled="currentPage === 1">
            上一页
          </button>

          <span>第 {{ currentPage }} / {{ totalPages }} 页</span>

          <button @click="currentPage++" :disabled="currentPage === totalPages">
            下一页
          </button>
        </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'

const users = ref([])
const applications = ref([])
const adminName = ref('')
const currentView = ref('users')
// 搜索 & 筛选
const searchName = ref('')
const filterRole = ref('')

// 分页
const currentPage = ref(1)
const pageSize = 5

// 切换页面
const switchView = (view) => {
  currentView.value = view
}

// 申请列表
// 获取用户
const fetchUsers = async () => {
  const res = await axios.get('http://127.0.0.1:8000/api/users/')
  users.value = res.data.users
}

// 获取申请列表
const fetchApplications = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/applications/')
    applications.value = res.data.data
  } catch (err) {
    console.error(err)
  }
}

// 搜索过滤
const filteredApplications = computed(() => {
  if (!searchName.value) return applications.value
  return applications.value.filter(item =>
    item.username.includes(searchName.value)
  )
})

// 审核通过
const approve = async (username) => {
  await axios.post('http://127.0.0.1:8000/api/approve/', { username })
  fetchApplications()
  fetchUsers()
}

// 审核拒绝
const reject = async (username) => {
  await axios.post('http://127.0.0.1:8000/api/reject/', { username })
  fetchApplications()
}

// 页面切换自动加载
watch(currentView, (val) => {
  if (val === 'apply') {
    fetchApplications()
  }
})

// 登出
const logout = () => {
  localStorage.removeItem('username')
  location.reload()
}

// 初始化
onMounted(() => {
  fetchUsers()
  fetchApplications()
  adminName.value = localStorage.getItem('username')
})

// 用户列表
// 过滤逻辑
const filteredUsers = computed(() => {
  return users.value.filter(user => {
    const matchName = user.username.includes(searchName.value)
    const matchRole = filterRole.value
      ? user.role === filterRole.value
      : true

    return matchName && matchRole
  })
})

// 分页逻辑
const paginatedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return filteredUsers.value.slice(start, end)
})

// 总页数
const totalPages = computed(() => {
  return Math.ceil(filteredUsers.value.length / pageSize)
})

const formatRole = (role) => {
  if (role === 'user') return '普通用户'
  if (role === 'expert') return '邻里达人'
  if (role === 'admin') return '管理员'
  return role
}

const getRoleClass = (role) => {
  if (role === 'user') return 'role-user'
  if (role === 'expert') return 'role-expert'
  if (role === 'admin') return 'role-admin'
  return ''
}
</script>

<style>
.admin-container {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 200px;
  background: #2c3e50;
  color: white;
  padding: 20px;
}

.sidebar li {
  cursor: pointer;
  margin: 10px 0;
}

.main {
  flex: 1;
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

/* 表格 */
table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  border: 1px solid #ddd;
  padding: 8px;
}

th {
  background: #f5f5f5;
}

/* 状态颜色 */
.pending {
  color: orange;
}

.approved {
  color: green;
}

.rejected {
  color: red;
}

.user-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
  background: #fff;
}

.user-table th {
  background: #f5f7fa;
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.user-table td {
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.user-table tr:hover {
  background: #f9f9f9;
}

/* 角色标签 */
.role-user {
  color: #409eff;
}

.role-expert {
  color: #67c23a;
  font-weight: bold;
}

.role-admin {
  color: #e6a23c;
  font-weight: bold;
}
</style>