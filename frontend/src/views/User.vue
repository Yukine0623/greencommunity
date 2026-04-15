<template>
  <div class="user-layout-container">
    <div class="main-content">
      <header class="content-header">
          <h1>个人中心</h1>
          <p class="subtitle">管理您的申请状态与历史记录</p>
      </header>

      <div class="content-body">
        
        <div class="top-cards-grid">
          <div class="glass-card user-info-card">
            <div class="card-header">
              <h3>基本信息</h3>
              <span class="role-badge">{{ roleText }}</span>
            </div>
            <div class="user-detail">
              <span class="label">当前登录：</span>
              <span class="value">{{ username }}</span>
            </div>
          </div>

          <div class="glass-card status-card">
            <div class="card-header">
              <h3>邻里达人申请状态</h3>
            </div>
            <div class="status-display">
              <p v-if="status === 'none'" class="status-text none">你还没有申请</p>
              
              <div v-if="status === 'pending'" class="status-box pending">
                <span class="icon">⏳</span>
                <p>审核中，请耐心等待管理员处理</p>
              </div>

              <div v-if="status === 'approved'" class="status-box approved">
                <span class="icon">🎉</span>
                <p>已通过，您现在是邻里达人</p>
              </div>

              <div v-if="status === 'rejected'" class="status-box rejected">
                <span class="icon">❌</span>
                <p>申请被拒绝，可以修改理由后重新申请</p>
              </div>
            </div>
          </div>
        </div>

        <div 
          class="glass-card apply-action-card"
          v-if="status === 'none' || status === 'rejected'"
        >
          <div class="card-header">
            <h3>申请成为邻里达人</h3>
          </div>
          <div class="apply-form">
            <input v-model="reason" placeholder="请输入您的申请理由..." />
            <button class="btn-primary" @click="handleApply">提交申请</button>
          </div>
        </div>

        <div 
          class="glass-card history-card"
          v-if="status === 'pending' || status === 'rejected'"
        >
          <div class="card-header">
            <h3>申请历史记录</h3>
          </div>
          <div class="table-wrapper">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>审核状态</th>
                  <th>提交时间</th>
                  <th>审核时间</th>
                  <th>拒绝理由</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in applicationHistory" :key="item.id">
                  <td>
                    <span :class="['status-tag', item.status]">
                      {{ formatStatus(item.status) }}
                    </span>
                  </td>
                  <td class="time-col">{{ item.created_at }}</td>
                  <td class="time-col">{{ item.reviewed_at || '-' }}</td>
                  <td class="reason-col">{{ item.reject_reason || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>

    </div>
  </div>
</template>

<script setup>
import Sidebar from '@/components/Sidebar.vue'
import { useUserStore } from '@/store/user'
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

const username = computed(() => userStore.username)
const role = computed(() => userStore.role)

const status = ref('')
const reason = ref('')
const applicationHistory = ref([])

const roleText = computed(() => {
  if (role.value === 'resident') return '普通用户'
  if (role.value === 'expert') return '邻里达人'
  if (role.value === 'admin') return '管理员'
  return '未知身份'
})

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/user_info/', {
      username: username.value
    })
    
    userStore.role = res.data.role
    userStore.points = res.data.points || 0
    
  } catch (error) {
    console.error("获取用户信息失败:", error)
  }
}

const fetchMyApplication = async () => {
  const res = await axios.post('http://127.0.0.1:8000/api/my_application/', {
    username: username.value
  })
  status.value = res.data.status
}

const handleApply = async () => {
  const res = await axios.post('http://127.0.0.1:8000/api/apply/', {
    username: username.value,
    reason: reason.value
  })
  alert(res.data.message)
  reason.value = ''
  await fetchMyApplication()
  await fetchApplicationHistory()
}

const logout = () => {
  localStorage.clear()
  router.push('/')
}

const fetchApplicationHistory = async () => {
  const res = await axios.post(
    'http://127.0.0.1:8000/api/my_application_history/',
    {
      username: username.value
    }
  )
  applicationHistory.value = res.data.data
}

const formatStatus = (status) => {
  if (status === 'pending') return '审核中'
  if (status === 'approved') return '已通过'
  if (status === 'rejected') return '已拒绝'
  return '未知状态'
}

onMounted(() => {
  fetchUserInfo()
  fetchMyApplication()
  fetchApplicationHistory()
})
</script>

<style scoped>
/* 使用 scoped，避免样式污染 */

/* 1. 整体布局：适配固定定位的 Sidebar */
.user-layout-container {
  display: flex;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  /* 🚀 关键：给左侧 Sidebar 腾出空间，请根据你 Sidebar 的实际宽度调整 */
  margin-left: 260px; 
  padding: 40px;
  background-color: #f8fafc; /* 冷灰色背景，衬托深色 Sidebar */
}

/* 2. 页面头部样式 */
.content-header {
  margin-bottom: 30px;
}
.content-header h1 {
  font-size: 32px;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
}
.subtitle {
  color: #718096;
  margin-top: 8px;
  font-size: 16px;
}

/* 3. 核心布局系统 */
.content-body {
  display: flex;
  flex-direction: column;
  gap: 25px; /* 卡片之间的间距 */
}

/* 上部两卡片并排 */
.top-cards-grid {
  display: grid;
  grid-template-columns: 1fr 1.5fr; /* 左右卡片比例 */
  gap: 25px;
}

/* 4. 通用“微光卡片”基类 (取代旧的 .card) */
.glass-card {
  background: white;
  border-radius: 20px;
  padding: 25px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.5);
  transition: all 0.3s ease;
}

.glass-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.06);
}

/* 卡片头部 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #edf2f7;
  padding-bottom: 15px;
  margin-bottom: 20px;
}

.card-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #2d3748;
  margin: 0;
  border: none; /* 去掉旧的蓝边 */
  padding: 0;
}

/* 5. 细节样式微调 */

/* 用户基本信息 */
.role-badge {
  background: #ebf8ff;
  color: #3182ce;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.user-detail {
  display: flex;
  align-items: center;
}
.user-detail .label { color: #718096; }
.user-detail .value {
  color: #1a202c;
  font-weight: 600;
  font-size: 16px;
}

/* 申请状态 */
.status-display p.none { color: #718096; font-style: italic; }

.status-box {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 15px;
  border-radius: 12px;
}

.status-box .icon { font-size: 20px; }
.status-box p { margin: 0; font-size: 14px; flex: 1; }

.pending { background-color: #fffbeb; color: #b7791f; border: 1px solid #fbd38d; }
.approved { background-color: #f0fff4; color: #2f855a; border: 1px solid #9ae6b4; }
.rejected { background-color: #fff5f5; color: #c53030; border: 1px solid #feb2b2; }

/* 申请表单 */
.apply-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

input {
  padding: 12px 15px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  outline: none;
  transition: all 0.2s;
}
input:focus {
  border-color: #63b3ed; /* 浅蓝高亮 */
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.15);
}

.btn-primary {
  padding: 12px;
  background-color: #3182ce;
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.btn-primary:hover { background-color: #2b6cb0; }

/* 历史记录表格 */
.table-wrapper {
  overflow-x: auto;
}

.custom-table {
  width: 100%;
  border-collapse: collapse;
}

.custom-table th {
  text-align: left;
  padding: 12px 15px;
  background-color: #f8fafc;
  color: #64748b;
  font-weight: 600;
  font-size: 13px;
}

.custom-table td {
  padding: 16px 15px;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
  font-size: 14px;
}

.custom-table tr:last-child td { border-bottom: none; }

/* 表格内的状态胶囊 */
.status-tag {
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}
.status-tag.pending { background: #ebf8ff; color: #3182ce; border: none; }
.status-tag.approved { background: #f0fff4; color: #38a169; border: none; }
.status-tag.rejected { background: #fff5f5; color: #e53e3e; border: none; }

.time-col { color: #64748b; font-size: 13px; }
.reason-col { color: #e53e3e; }
</style>
