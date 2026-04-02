<template>
  <div class="admin-layout-container">
    <AdminSidebar 
      :adminName="adminName"
      @switchView="switchView"
    />

    <div class="main-content">
      <header class="content-header">
        <div class="header-left">
          <h1>
            {{ 
              currentView === 'users' ? '用户管理系统' : 
              currentView === 'apply' ? '邻里达人资格审核' : 
              currentView === 'posts' ? '社区帖子审核' : '审核历史记录'
            }}
          </h1>
          <p class="subtitle">欢迎回来，超级管理员 {{ adminName }}</p>
        </div>
        <div class="header-right">
          <button class="btn-refresh" @click="refreshData">🔄 刷新数据</button>
        </div>
      </header>

      <div class="glass-card filter-bar">
        <div class="search-input">
          <span class="icon">🔍</span>
          <input v-model="searchName" placeholder="输入关键字搜索..." />
        </div>
        <div class="filter-select" v-if="currentView === 'users'">
          <select v-model="filterRole">
            <option value="">所有角色</option>
            <option value="user">普通用户</option>
            <option value="expert">邻里达人</option>
            <option value="admin">管理员</option>
          </select>
        </div>
      </div>

      <Transition name="fade" mode="out-in">
        
        <div class="glass-card table-card" v-if="currentView === 'users'" key="users">
          <div class="card-header">
            <h3>全部用户 ({{ filteredUsers.length }})</h3>
          </div>
          <div class="table-wrapper">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>用户名</th>
                  <th>角色</th>
                  <th>注册时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in paginatedUsers" :key="user.id">
                  <td class="id-col">#{{ user.id }}</td>
                  <td class="name-col">{{ user.username }}</td>
                  <td>
                    <span :class="['role-badge', user.role]">
                      {{ formatRole(user.role) }}
                    </span>
                  </td>
                  <td class="time-col">{{ user.created_at }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="pagination">
            <button class="page-btn" @click="currentPage--" :disabled="currentPage === 1">上一页</button>
            <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
            <button class="page-btn" @click="currentPage++" :disabled="currentPage === totalPages">下一页</button>
          </div>
        </div>

        <div class="glass-card table-card" v-else-if="currentView === 'apply'" key="apply">
          <div class="card-header">
            <h3>申请信息审核</h3>
          </div>
          <div class="table-wrapper">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>用户名</th>
                  <th>申请理由</th>
                  <th>当前状态</th>
                  <th style="text-align: center">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in filteredApplications" :key="item.id">
                  <td class="name-col">{{ item.username }}</td>
                  <td class="reason-col">{{ item.reason }}</td>
                  <td>
                    <span :class="['status-tag', item.status]">
                      {{ item.status === 'pending' ? '待审核' : (item.status === 'approved' ? '已通过' : '已拒绝') }}
                    </span>
                  </td>
                  <td class="action-cols">
                    <div class="action-btns" v-if="item.status === 'pending'">
                      <button class="btn-approve" @click="approve(item.username)">通过</button>
                      <button class="btn-reject" @click="openRejectModal(item.username)">拒绝</button>
                    </div>
                    <span class="processed-text" v-else>✅ 已处理</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="glass-card table-card" v-else-if="currentView === 'posts'" key="posts">
          <div class="card-header">
            <h3>社区待审核帖子 ({{ auditPosts.length }})</h3>
          </div>
          <div class="table-wrapper">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>作者</th>
                  <th>标题</th>
                  <th>内容预览</th>
                  <th>发布时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="post in auditPosts" :key="post.id">
                  <td class="name-col">{{ post.author }}</td>
                  <td class="title-col"><strong>{{ post.title }}</strong></td>
                  <td class="content-col">{{ post.content.substring(0, 20) }}...</td>
                  <td class="time-col">{{ post.created_at }}</td>
                  <td class="action-cols">
                    <div class="action-btns">
                      <button class="btn-detail" @click="openDetailModal(post)">详情</button>
                      <button class="btn-approve" @click="approvePost(post.id)">通过</button>
                      <button class="btn-reject" @click="openPostRejectModal(post.id)">拒绝</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="auditPosts.length === 0" style="text-align: center; padding: 40px; color: #9ca3af;">
            📭 暂时没有待审核的帖子
          </div>
        </div>

        <div class="glass-card table-card" v-else-if="currentView === 'history'" key="history">
          <div class="card-header">
            <h3>已处理帖子 ({{ auditHistory.length }})</h3>
          </div>
          <div class="table-wrapper">
            <table class="custom-table">
              <thead>
                <tr>
                  <th>标题</th>
                  <th>作者</th>
                  <th>状态</th>
                  <th>理由/备注</th>
                  <th>处理时间</th>
                  <th>操作</th> </tr>
              </thead>
              <tbody>
                <tr v-for="item in auditHistory" :key="item.id">
                  <td class="title-col"><strong>{{ item.title }}</strong></td>
                  <td>{{ item.author }}</td>
                  <td>
                    <span :class="['status-tag', item.status]">
                      {{ item.status === 'approved' ? '已通过' : '已拒绝' }}
                    </span>
                  </td>
                  <td class="reason-col">
                    {{ item.reject_reason || '--' }}
                  </td>
                  <td class="time-col">
                    {{ item.processed_at || item.updated_at || item.created_at || '--' }}
                  </td>
                  <td>
                    <button class="btn-detail" @click="openDetailModal(item)">详情</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="auditHistory.length === 0" style="text-align: center; padding: 40px; color: #9ca3af;">
            ☕️ 暂无审核历史记录
          </div>
        </div>
      </Transition>
    </div>

    <Transition name="fade">
      <div v-if="showRejectModal" class="modal-overlay" @click.self="closeModal">
        <div class="modal-content glass-card">
          <div class="modal-header">
            <h3>填写拒绝理由</h3>
            <p class="modal-subtitle">正在处理：{{ currentUser }}</p>
          </div>
          <textarea 
            v-model="rejectReason" 
            placeholder="请简述拒绝原因..."
            class="modal-textarea"
          ></textarea>
          <div class="modal-footer">
            <button class="btn-cancel" @click="closeModal">取消</button>
            <button class="btn-confirm" @click="confirmReject">确认提交</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="showDetailModal" class="modal-overlay" @click.self="closeDetailModal">
        <div class="modal-content glass-card detail-modal-box">
          <pre style="font-size: 10px; color: red; background: #eee;">{{ currentPostDetail }}</pre>
          <div class="detail-header">
            <h2 class="detail-title">{{ currentPostDetail.title }}</h2>
          </div>
          
          <div class="detail-body">
            <div class="detail-meta">
              <p class="meta-line">👤 <strong>发帖人：</strong>{{ currentPostDetail.author }}</p>
              <p class="meta-line">🕒 <strong>发布时间：</strong>{{ currentPostDetail.processed_at || currentPostDetail.created_at || '--' }}</p>
            </div>

            <div class="detail-content-text">
              {{ currentPostDetail.content }}
            </div>
          </div>

          <div class="detail-footer">
            <button class="btn-close-green" @click="closeDetailModal">关闭窗口</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import AdminSidebar from '../components/AdminSidebar.vue'
import { ref, onMounted, computed } from 'vue'
import { useUserStore } from '@/store/user'
import axios from 'axios'

const userStore = useUserStore()

// --- 响应式数据 ---
const adminName = computed(() => userStore.username)
const users = ref([])
const applications = ref([])
const auditPosts = ref([])
const auditHistory = ref([]) // 审核历史

const currentView = ref('users')
const searchName = ref('')
const filterRole = ref('')
const currentPage = ref(1)
const pageSize = 8

// --- 弹窗状态 ---
const showRejectModal = ref(false)
const showDetailModal = ref(false)
const rejectType = ref('')
const rejectReason = ref('')
const currentUser = ref('') // 存放用户名或帖子ID
const currentPostDetail = ref({})

// 🚀 新增：任务审核相关的状态
const auditTasks = ref([])
const showAuditModal = ref(false)
const selectedTask = ref({})
const auditReason = ref('')

// --- 核心方法 ---

// 视图切换
const switchView = (view) => {
  currentView.value = view
  currentPage.value = 1
  if (view === 'posts') fetchAuditPosts()
  if (view === 'history') fetchAuditHistory()
}

// 刷新所有数据
const refreshData = () => {
  fetchUsers()
  fetchApplications()
  if (currentView.value === 'posts') fetchAuditPosts()
  if (currentView.value === 'history') fetchAuditHistory()
}

// 数据抓取：待审核帖子
const fetchAuditPosts = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/all_pending_posts/')
    auditPosts.value = res.data.posts 
  } catch (err) { console.error("加载待审核帖子失败", err) }
}

// 数据抓取：审核历史
const fetchAuditHistory = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/audit_history/')
    auditHistory.value = res.data.history
  } catch (err) { console.error("加载历史记录失败", err) }
}

const fetchUsers = async () => {
  const res = await axios.get('http://127.0.0.1:8000/api/users/')
  users.value = res.data.users
}

const fetchApplications = async () => {
  const res = await axios.get('http://127.0.0.1:8000/api/applications/')
  applications.value = res.data.data
}

// --- 审批操作 ---

const approvePost = async (id) => {
  await axios.post('http://127.0.0.1:8000/api/review_post/', { id, action: 'approve' })
  refreshData() // 通过后刷新，帖子会进入历史记录
}

const approve = async (username) => {
  await axios.post('http://127.0.0.1:8000/api/approve/', { username })
  refreshData()
}

const confirmReject = async () => {
  if (!rejectReason.value) return alert('请输入理由')
  const url = rejectType.value === 'user' ? 'http://127.0.0.1:8000/api/reject/' : 'http://127.0.0.1:8000/api/review_post/'
  const data = rejectType.value === 'user' ? { username: currentUser.value, reason: rejectReason.value } : { id: currentUser.value, action: 'reject', reason: rejectReason.value }
  
  await axios.post(url, data)
  showRejectModal.value = false
  refreshData()
}

// --- 弹窗控制 ---
const openDetailModal = (post) => {
  currentPostDetail.value = post
  showDetailModal.value = true
}
const closeDetailModal = () => { showDetailModal.value = false }

const openRejectModal = (username) => {
  rejectType.value = 'user'; currentUser.value = username; rejectReason.value = ''; showRejectModal.value = true
}
const openPostRejectModal = (postId) => {
  rejectType.value = 'post'; currentUser.value = postId; rejectReason.value = ''; showRejectModal.value = true
}
const closeModal = () => { showRejectModal.value = false }

// --- 计算属性与格式化 ---
const filteredUsers = computed(() => {
  return users.value.filter(user => {
    const matchName = user.username.toLowerCase().includes(searchName.value.toLowerCase())
    const matchRole = filterRole.value ? user.role === filterRole.value : true
    return matchName && matchRole
  })
})
const paginatedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredUsers.value.slice(start, start + pageSize)
})
const totalPages = computed(() => Math.ceil(filteredUsers.value.length / pageSize) || 1)
const filteredApplications = computed(() => applications.value.filter(item => item.username.includes(searchName.value)))

const formatRole = (role) => {
  const map = { user: '普通用户', expert: '邻里达人', admin: '管理员' }
  return map[role] || role
}

// 获取待审核/待处理任务
const fetchAuditTasks = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/get_audit_tasks/')
    auditTasks.value = res.data.tasks
  } catch (err) {
    console.error("加载审核列表失败", err)
  }
}

// 监听切换，当切到 'taskAudit' 时自动刷新数据
watch(() => currentView.value, (newVal) => {
  if (newVal === 'taskAudit') {
    fetchAuditTasks()
  }
})

// 打开审批弹窗
const openAuditModal = (task) => {
  selectedTask.value = task
  auditReason.value = '' // 清空之前的理由
  showAuditModal.value = true
}

// 提交审批结果
const submitAudit = async (action) => {
  // 规则检查：初审拒绝 或 复审仲裁 时必须写理由
  const isIntervention = selectedTask.value.status === 'intervention'
  if ((action === 'reject' || isIntervention) && !auditReason.value.trim()) {
    return alert('为了公平公正，请务必填写理由/评语。')
  }

  try {
    await axios.post('http://127.0.0.1:8000/api/admin_handle_review/', {
      taskId: selectedTask.value.id,
      action: action,
      reason: auditReason.value
    })
    alert('处理成功！')
    showAuditModal.value = false
    fetchAuditTasks() // 刷新列表
  } catch (err) {
    alert('操作失败，请检查后端服务')
  }
}

const formatCategory = (cat) => {
  const map = { errand: '跑腿', repair: '维修', pet: '宠物', other: '其他' }
  return map[cat] || '互助'
}

onMounted(() => { 
  fetchUsers()
  fetchApplications() 
})
</script>

<style scoped>
/* --- 布局 --- */
.admin-layout-container { display: flex; min-height: 100vh; background-color: #f0f4f2; }
.main-content { flex: 1; margin-left: 260px; padding: 40px; max-width: 1400px; }

/* --- 头部 --- */
.content-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.content-header h1 { font-size: 28px; color: #064e3b; margin: 0; }
.subtitle { color: #6b7280; }

/* --- 过滤栏 --- */
.filter-bar { display: flex; gap: 20px; margin-bottom: 25px; padding: 15px 25px; align-items: center; }
.search-input input { width: 300px; padding: 10px 35px; border-radius: 10px; border: 1px solid #e5e7eb; outline: none; }

/* --- 表格卡片 --- */
.glass-card { background: white; border-radius: 20px; border: 1px solid rgba(16, 185, 129, 0.1); box-shadow: 0 10px 25px rgba(0,0,0,0.03); }
.table-card { padding: 25px; }
.custom-table { width: 100%; border-collapse: collapse; }
.custom-table th { text-align: left; padding: 12px; background: #f9fafb; color: #6b7280; font-size: 13px; }
.custom-table td { padding: 16px 12px; border-bottom: 1px solid #f3f4f6; font-size: 14px; }

/* --- 标签与按钮 --- */
.role-badge { padding: 4px 8px; border-radius: 6px; font-size: 12px; }
.role-badge.admin { background: #fff7ed; color: #d97706; }
.role-badge.expert { background: #ecfdf5; color: #059669; }
.role-badge.user { background: #eff6ff; color: #2563eb; }

.status-tag { padding: 4px 10px; border-radius: 20px; font-size: 12px; }
.status-tag.approved { background: #d1fae5; color: #065f46; }
.status-tag.rejected { background: #fee2e2; color: #991b1b; }
.status-tag.pending { background: #fef3c7; color: #92400e; }

.action-btns { display: flex; gap: 8px; }
.btn-detail { background: #f0f9ff; color: #0ea5e9; border: 1px solid #e0f2fe; padding: 6px 12px; border-radius: 6px; cursor: pointer; }
.btn-approve { background: #10b981; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; }
.btn-reject { background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; }
.btn-refresh { padding: 10px 18px; background: white; border: 1px solid #d1fae5; color: #059669; border-radius: 10px; cursor: pointer; }

/* --- 弹窗 --- */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; z-index: 2000;
}
.detail-modal-box { width: 550px; padding: 35px; background: white; border-radius: 24px; }
.detail-title { font-size: 24px; color: #064e3b; text-align: center; margin-bottom: 20px; }
.detail-content-text { font-size: 16px; line-height: 1.8; color: #1f2937; white-space: pre-wrap; min-height: 120px; }
.detail-footer { margin-top: 30px; display: flex; justify-content: center; }
.btn-close-green { padding: 12px 60px; background: #10b981 !important; color: white !important; border: none; border-radius: 12px; cursor: pointer; font-weight: 600; }

.modal-textarea { width: 100%; height: 100px; margin: 15px 0; padding: 10px; border-radius: 10px; border: 1px solid #ddd; resize: none; }

/* --- 分页 --- */
.pagination { display: flex; justify-content: center; align-items: center; gap: 15px; margin-top: 20px; }
.page-btn { padding: 5px 12px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer; }

/* --- 动画 --- */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s, transform 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(10px); }
</style>