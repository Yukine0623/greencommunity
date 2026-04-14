<template>
  <div class="admin-layout-container">
    <AdminSidebar :adminName="adminName" @switchView="switchView" />

    <div class="main-content">
      <header class="content-header">
        <div class="header-left">
          <h1>{{ viewTitle }}</h1>
          <p class="subtitle">工作愉快，{{ adminName }}。当前系统运行正常。</p>
        </div>
        <div class="header-right">
          <button class="btn-refresh" @click="refreshData">
            <span class="icon">🔄</span> 刷新实时数据
          </button>
        </div>
      </header>

      <div class="glass-card filter-bar">
        <div class="search-input">
          <span class="icon">🔍</span>
          <input v-model="searchName" :placeholder="searchPlaceholder" />
        </div>

        <div class="filter-group">
          <select v-if="currentView === 'users'" v-model="filterRole" class="custom-select">
            <option value="">所有角色</option>
            <option value="user">普通用户</option>
            <option value="expert">邻里达人</option>
            <option value="admin">管理员</option>
          </select>

          <select v-if="currentView === 'taskAudit'" v-model="taskTypeFilter" class="custom-select">
            <option value="all">全业务类型</option>
            <option value="initial">新建任务初审</option>
            <option value="dispute">争议仲裁复审</option>
          </select>

          <select v-if="['taskAudit', 'posts'].includes(currentView)" v-model="processStatusFilter" class="custom-select">
            <option value="all">🌐 全部状态</option>
            <option value="todo">⏳ 待处理</option>
            <option value="done">✅ 已归档</option>
          </select>
        </div>
      </div>

      <Transition name="fade-slide" mode="out-in">
        <div class="glass-card table-card" v-if="currentView === 'users'" key="users">
          <div class="card-header"><h3>活跃用户清单 ({{ filteredUsers.length }})</h3></div>
          <div class="table-wrapper">
            <table class="custom-table">
              <thead>
                <tr><th>用户标识</th><th>账户名</th><th>职能角色</th><th>积分</th><th>注册日期</th></tr>
              </thead>
              <tbody>
                <tr v-for="user in paginatedUsers" :key="user.id">
                  <td class="id-col">#{{ user.id }}</td>
                  <td class="name-col">{{ user.username }}</td>
                  <td><span :class="['role-badge', user.role]">{{ formatRole(user.role) }}</span></td>
                  <td><span class="points-text">🪙 {{ user.points || 0 }}</span></td>
                  <td class="time-col">{{ user.created_at }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="pagination">
            <button @click="currentPage--" :disabled="currentPage === 1">Prev</button>
            <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
            <button @click="currentPage++" :disabled="currentPage === totalPages">Next</button>
          </div>
        </div>

        <div class="glass-card table-card" v-else-if="currentView === 'apply'" key="apply">
          <div class="card-header"><h3>达人入驻申请</h3></div>
          <div class="table-wrapper">
            <table class="custom-table">
              <thead>
                <tr><th>申请人</th><th>资历描述</th><th>审核状态</th><th class="center">操作</th></tr>
              </thead>
              <tbody>
                <tr v-for="item in filteredApplications" :key="item.id">
                  <td class="name-col">{{ item.username }}</td>
                  <td class="reason-col">{{ item.reason }}</td>
                  <td><span :class="['status-pill', item.status]">{{ translateStatus(item.status) }}</span></td>
                  <td class="action-cols center">
                    <div v-if="item.status === 'pending'" class="action-btns">
                      <button class="btn-success" @click="approve(item.username)">核准</button>
                      <button class="btn-danger" @click="openRejectModal(item.username, 'user')">拒绝</button>
                    </div>
                    <span v-else class="processed-label">✅ 已处理</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="glass-card table-card" v-else-if="currentView === 'posts'" key="posts">
          <div class="card-header"><h3>内容审核日志</h3></div>
          <div class="table-wrapper">
            <table class="custom-table">
              <thead>
                <tr><th>内容概要</th><th>发布者</th><th>状态</th><th>反馈理由</th><th class="center">操作</th></tr>
              </thead>
              <tbody>
                <tr v-for="post in mixedFilteredPosts" :key="post.id">
                  <td class="title-col">
                    <strong>{{ post.title }}</strong>
                    <p class="excerpt">{{ post.content.substring(0, 15) }}...</p>
                  </td>
                  <td>{{ post.author }}</td>
                  <td><span :class="['status-pill', post.status]">{{ translateStatus(post.status) }}</span></td>
                  <td class="reason-col">{{ post.reject_reason || '--' }}</td>
                  <td class="action-cols center">
                    <div class="action-btns">
                      <button class="btn-ghost" @click="openDetailModal(post)">详情</button>
                      <template v-if="post.status === 'pending'">
                        <button class="btn-success" @click="approvePost(post.id)">准许</button>
                        <button class="btn-danger" @click="openPostRejectModal(post.id)">拦截</button>
                      </template>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="glass-card table-card" v-else-if="currentView === 'taskAudit'" key="tasks">
          <div class="card-header"><h3>互助任务管控中心</h3></div>
          <div class="table-wrapper">
            <table class="custom-table">
              <thead>
                <tr><th>任务信息</th><th>发布方</th><th>业务类型</th><th>流程环节</th><th class="center">管理操作</th></tr>
              </thead>
              <tbody>
                <tr v-for="task in mixedFilteredTasks" :key="task.id">
                  <td class="title-col">
                    <strong>{{ task.title }}</strong>
                    <span class="category-tag">{{ formatCategory(task.category) }}</span>
                  </td>
                  <td>{{ task.creator }}</td>
                  <td>{{ task.status === 'auditing' || task.status === 'pending' || task.status === 'rejected' ? '初核申请' : '争议仲裁' }}</td>
                  <td><span :class="['status-pill', task.status]">{{ translateStatus(task.status) }}</span></td>
                  <td class="action-cols center">
                    <button v-if="['auditing', 'intervention'].includes(task.status)" class="btn-primary" @click="openAuditModal(task)">
                      立即介入
                    </button>
                    <button v-else class="btn-ghost" @click="openAuditModal(task)">查看详情</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </Transition>
    </div>

    <Teleport to="body">
      
      <Transition name="zoom">
        <div v-if="showDetailModal" class="modal-overlay" @click.self="closeDetailModal">
          <div class="modal-card detail-view-card">
            <div class="modal-header">
              <div class="title-row">
                <span class="type-badge">内容详情</span>
                <h2 class="detail-title">{{ currentPostDetail.title }}</h2>
              </div>
              <div class="detail-meta">
                <span class="meta-item">👤 作者：<strong>{{ currentPostDetail.author }}</strong></span>
                <span class="meta-item">🕒 发布时间：{{ currentPostDetail.processed_at || currentPostDetail.created_at }}</span>
              </div>
            </div>
            <div class="modal-body">
              <div class="post-content-text">{{ currentPostDetail.content }}</div>
            </div>
            <div class="modal-footer">
              <button class="btn-close-styled" @click="closeDetailModal">已阅并关闭</button>
            </div>
          </div>
        </div>
      </Transition>

      <Transition name="zoom">
        <div v-if="showRejectModal" class="modal-overlay" @click.self="closeModal">
          <div class="modal-card reject-view">
            <div class="modal-header"><h3>请注明驳回理由</h3></div>
            <div class="modal-body">
              <textarea v-model="rejectReason" placeholder="该理由将向相关用户公示..." class="styled-textarea"></textarea>
            </div>
            <div class="modal-footer">
              <button class="btn-ghost" @click="closeModal">取消</button>
              <button class="btn-confirm-danger" @click="confirmReject">确认驳回</button>
            </div>
          </div>
        </div>
      </Transition>

      <Transition name="zoom">
        <div v-if="showAuditModal" class="modal-overlay" @click.self="showAuditModal = false">
          <div class="modal-card audit-view">
            <div class="modal-header"><h3>{{ selectedTask.status === 'auditing' ? '任务准入评估' : '互助仲裁裁定' }}</h3></div>
            <div class="modal-body">
              <div class="data-row"><strong>任务描述：</strong><p>{{ selectedTask.content }}</p></div>
              <div v-if="selectedTask.status === 'intervention'" class="data-row dispute">
                <strong>达人反馈：</strong><p>{{ selectedTask.result_desc || '未提供描述' }}</p>
              </div>
              <textarea v-model="auditReason" placeholder="请输入裁定依据..." class="styled-textarea" :readonly="isProcessed(selectedTask.status)"></textarea>
            </div>
            <div v-if="!isProcessed(selectedTask.status)" class="modal-footer">
              <button class="btn-danger" @click="submitAudit('reject')">驳回/判输</button>
              <button class="btn-success" @click="submitAudit('approve')">核准/判胜</button>
            </div>
            <div v-else class="modal-footer">
              <button class="btn-ghost" @click="showAuditModal = false">关闭视图</button>
            </div>
          </div>
        </div>
      </Transition>
      
    </Teleport>
  </div>
</template>

<script setup>
import AdminSidebar from '../components/AdminSidebar.vue'
import { ref, onMounted, computed, watch } from 'vue'
import { useUserStore } from '@/store/user'
import axios from 'axios'

const userStore = useUserStore()

// --- 状态定义 ---
const adminName = computed(() => userStore.username)
const currentView = ref('users')
const searchName = ref('')
const filterRole = ref('')
const currentPage = ref(1)
const pageSize = 8

const users = ref([])
const applications = ref([])
const auditPosts = ref([])
const auditHistory = ref([])
const auditTasks = ref([])

const taskTypeFilter = ref('all') 
const processStatusFilter = ref('all') 

const showRejectModal = ref(false)
const showDetailModal = ref(false)
const showAuditModal = ref(false)
const rejectType = ref('')
const rejectReason = ref('')
const currentUser = ref('')
const currentPostDetail = ref({})
const selectedTask = ref({})
const auditReason = ref('')

// --- 计算属性 ---
const viewTitle = computed(() => {
  const titles = { users: '用户管理系统', apply: '邻里达人入驻审核', posts: '社区内容安全管理', taskAudit: '任务调度与仲裁中心' }
  return titles[currentView.value]
})

const searchPlaceholder = computed(() => {
  if (currentView.value === 'users') return '搜索用户名...'
  if (currentView.value === 'posts') return '搜标题、内容或作者...'
  return '搜索关键词或发起人...'
})

// 🚀 1. 帖子混合过滤逻辑
const mixedFilteredPosts = computed(() => {
  const combined = [...auditPosts.value.map(p => ({...p, status: 'pending'})), ...auditHistory.value]
  return combined.filter(p => {
    const matchSearch = p.title.includes(searchName.value) || p.author.includes(searchName.value)
    
    // 状态过滤逻辑
    let matchStatus = true
    if (processStatusFilter.value === 'todo') matchStatus = p.status === 'pending'
    else if (processStatusFilter.value === 'done') matchStatus = p.status !== 'pending'
    
    return matchSearch && matchStatus
  })
})

// 🚀 2. 任务混合过滤逻辑
const mixedFilteredTasks = computed(() => {
  return auditTasks.value.filter(t => {
    const matchSearch = t.title.includes(searchName.value) || t.creator.includes(searchName.value);
    
    let matchType = true;
    const isInitial = ['auditing', 'pending', 'rejected'].includes(t.status);
    const isDispute = ['intervention', 'finished'].includes(t.status);
    if (taskTypeFilter.value === 'initial') matchType = isInitial;
    if (taskTypeFilter.value === 'dispute') matchType = isDispute;

    let matchStatus = true; 
    if (processStatusFilter.value === 'todo') matchStatus = ['auditing', 'intervention'].includes(t.status);
    else if (processStatusFilter.value === 'done') matchStatus = ['pending', 'rejected', 'finished'].includes(t.status);

    return matchSearch && matchType && matchStatus;
  }).sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at)); 
});

const filteredUsers = computed(() => users.value.filter(u => 
  u.username.toLowerCase().includes(searchName.value.toLowerCase()) && 
  (filterRole.value ? u.role === filterRole.value : true)
))

const paginatedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredUsers.value.slice(start, start + pageSize)
})

const totalPages = computed(() => Math.ceil(filteredUsers.value.length / pageSize) || 1)

const filteredApplications = computed(() => {
  if (!applications.value) return [];
  return applications.value.filter(item => item.username.toLowerCase().includes(searchName.value.toLowerCase()));
});

// --- API 方法 ---
const refreshData = () => {
  if (currentView.value === 'users') fetchUsers()
  if (currentView.value === 'apply') fetchApplications()
  if (currentView.value === 'posts') { fetchAuditPosts(); fetchAuditHistory() }
  if (currentView.value === 'taskAudit') fetchAuditTasks()
}

const fetchUsers = async () => { const res = await axios.get('http://127.0.0.1:8000/api/users/'); users.value = res.data.users }
const fetchApplications = async () => { const res = await axios.get('http://127.0.0.1:8000/api/applications/'); applications.value = res.data.data }
const fetchAuditPosts = async () => { const res = await axios.get('http://127.0.0.1:8000/api/all_pending_posts/'); auditPosts.value = res.data.posts }
const fetchAuditHistory = async () => { const res = await axios.get('http://127.0.0.1:8000/api/audit_history/'); auditHistory.value = res.data.history }
const fetchAuditTasks = async () => { const res = await axios.get('http://127.0.0.1:8000/api/get_audit_tasks/'); auditTasks.value = res.data.tasks }

const switchView = (view) => {
  currentView.value = view
  searchName.value = ''
  processStatusFilter.value = 'all' // 切换视图时重置状态
  refreshData()
}

// --- 审批逻辑 ---
const approvePost = async (id) => { await axios.post('http://127.0.0.1:8000/api/review_post/', { id, action: 'approve' }); refreshData() }
const approve = async (username) => { await axios.post('http://127.0.0.1:8000/api/approve/', { username }); refreshData() }

const confirmReject = async () => {
  if (!rejectReason.value.trim()) return alert('请填写驳回原因')
  const url = rejectType.value === 'user' ? '/api/reject/' : '/api/review_post/'
  const data = rejectType.value === 'user' ? { username: currentUser.value, reason: rejectReason.value } : { id: currentUser.value, action: 'reject', reason: rejectReason.value }
  await axios.post(`http://127.0.0.1:8000${url}`, data)
  showRejectModal.value = false
  refreshData()
}

const submitAudit = async (action) => {
  if (action === 'reject' && !auditReason.value.trim()) return alert('请填写理由')
  await axios.post('http://127.0.0.1:8000/api/admin_handle_review/', { taskId: selectedTask.value.id, action, reason: auditReason.value })
  showAuditModal.value = false
  fetchAuditTasks()
}

// --- UI 辅助 ---
const translateStatus = (s) => {
  const map = { pending: '待处理', approved: '准许', rejected: '驳回', auditing: '待初审', intervention: '仲裁中', finished: '已结案' }
  return map[s] || s
}
const formatRole = (r) => ({ user: '居民', expert: '达人', admin: '管理' }[r] || r)
const formatCategory = (c) => ({ errand: '跑腿', repair: '维修', pet: '宠物' }[c] || '互助')
const isProcessed = (s) => ['pending', 'rejected', 'finished'].includes(s)

const openDetailModal = (post) => { currentPostDetail.value = post; showDetailModal.value = true }
const closeDetailModal = () => { showDetailModal.value = false }
const openRejectModal = (id, type) => { rejectType.value = type; currentUser.value = id; rejectReason.value = ''; showRejectModal.value = true }
const openPostRejectModal = (id) => openRejectModal(id, 'post')
const closeModal = () => { showRejectModal.value = false }
const openAuditModal = (task) => { selectedTask.value = task; auditReason.value = task.audit_reason || task.intervention_decision || ''; showAuditModal.value = true }

onMounted(refreshData)
</script>

<style scoped>
/* 核心布局 */
.admin-layout-container { display: flex; min-height: 100vh; background: #f0f7f4; }
.main-content { flex: 1; margin-left: 260px; padding: 40px; }

/* 头部 */
.content-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; }
.content-header h1 { font-size: 28px; color: #1a4d38; font-weight: 700; }
.subtitle { color: #6b7c74; font-size: 14px; margin-top: 5px; }

/* 过滤栏 */
.glass-card { background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); border-radius: 24px; border: 1px solid rgba(255, 255, 255, 0.5); }
.filter-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px 25px; margin-bottom: 30px; }
.search-input { position: relative; flex: 1; max-width: 400px; }
.search-input input { width: 100%; padding: 12px 15px 12px 45px; border-radius: 14px; border: 1px solid #e2ece7; outline: none; }
.search-input .icon { position: absolute; left: 15px; top: 50%; transform: translateY(-50%); opacity: 0.5; }
.filter-group { display: flex; gap: 12px; }
.custom-select { padding: 10px 15px; border-radius: 12px; border: 1px solid #e2ece7; font-size: 14px; outline: none; cursor: pointer; }

/* 表格样式 */
.table-card { padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.02); }
.custom-table { width: 100%; border-collapse: collapse; }
.custom-table th { text-align: left; padding: 15px; color: #889891; border-bottom: 2px solid #f0f4f2; }
.custom-table td { padding: 20px 15px; border-bottom: 1px solid #f0f4f2; font-size: 14px; }
.excerpt { font-size: 12px; color: #94a3b8; margin-top: 4px; }

/* 标签与按钮 */
.status-pill, .role-badge { padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.status-pill.pending, .status-pill.auditing { background: #fffbeb; color: #b45309; }
.status-pill.approved, .status-pill.finished { background: #f0fdf4; color: #15803d; }
.status-pill.rejected { background: #fef2f2; color: #991b1b; }

.action-btns { display: flex; gap: 8px; }
.btn-success { background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 10px; cursor: pointer; }
.btn-danger { background: #ef4444; color: white; border: none; padding: 8px 16px; border-radius: 10px; cursor: pointer; }
.btn-ghost { background: #f3f4f6; color: #4b5563; border: none; padding: 8px 16px; border-radius: 10px; cursor: pointer; }
.btn-primary { background: #1a4d38; color: white; border: none; padding: 10px 20px; border-radius: 10px; cursor: pointer; }

/* ============================================================
   1. 全局遮罩层 (Modal Overlay)
   ============================================================ */
.modal-overlay {
  position: fixed !important;
  inset: 0;
  background: rgba(6, 31, 26, 0.45) !important; /* 深森林绿半透明 */
  backdrop-filter: blur(12px) !important;      /* 强力毛玻璃 */
  display: flex !important;
  align-items: center;
  justify-content: center;
  z-index: 9999 !important;
}

/* ============================================================
   2. 通用弹窗卡片基类 (Base Modal Card)
   ============================================================ */
.modal-card {
  background: #ffffff !important;
  border-radius: 28px !important;
  box-shadow: 0 25px 70px rgba(0, 0, 0, 0.2) !important;
  border: 1px solid rgba(255, 255, 255, 0.5);
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 防止内容溢出圆角 */
  transition: all 0.3s ease;
}

/* --- 变体 A：帖子详情弹窗 (略宽) --- */
.detail-view-card {
  width: 90%;
  max-width: 550px;
  padding: 40px;
}

/* --- 变体 B：任务审批弹窗 (精简紧致) --- */
.audit-view {
  width: 95%;
  max-width: 460px; /* 优化后的紧致宽度 */
  padding: 35px;
}

/* ============================================================
   3. 内容组件 (Components)
   ============================================================ */

/* 标题与标签 */
.type-badge {
  display: inline-block;
  background: #ecfdf5;
  color: #10b981;
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 6px;
  font-weight: 700;
  margin-bottom: 8px;
}

.detail-title {
  font-size: 26px;
  color: #064e3b;
  margin: 0;
  line-height: 1.3;
}

/* 元信息 (作者/时间) */
.detail-meta {
  margin-top: 12px;
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #889891;
  border-bottom: 1px solid #f0f4f2;
  padding-bottom: 15px;
}

/* 文本展示区域 (任务描述等) */
.data-row {
  margin-bottom: 15px;
  text-align: left;
}
.data-row strong {
  display: block;
  margin-bottom: 8px;
  color: #1a4d38;
  font-size: 15px;
}
.data-row p {
  background: #f8faf9;
  padding: 15px;
  border-radius: 14px;
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: #4a5568;
  border: 1px solid #edf2f0;
}

/* 滚动内容区 */
.modal-body {
  max-height: 350px;
  overflow-y: auto;
  padding: 10px 0;
}
.post-content-text {
  font-size: 16px;
  line-height: 1.8;
  color: #374151;
  white-space: pre-wrap;
}

/* ============================================================
   4. 表单与按钮 (Actions)
   ============================================================ */
.styled-textarea {
  width: 100%;
  min-height: 110px;
  padding: 15px;
  border-radius: 14px;
  border: 1px solid #e2ece7;
  font-size: 14px;
  outline-color: #10b981;
  margin: 10px 0;
}

.btn-close-styled {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 14px 70px;
  border-radius: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 10px;
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
  transition: all 0.3s ease;
}

.btn-close-styled:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 25px rgba(16, 185, 129, 0.4);
}

/* ============================================================
   5. 动画效果 (Transitions)
   ============================================================ */
/* 缩放弹入动画 */
.zoom-enter-active, 
.zoom-leave-active { 
  transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); 
}
.zoom-enter-from, 
.zoom-leave-to { 
  opacity: 0; 
  transform: scale(0.9) translateY(20px); 
}

/* 平滑切入动画 */
.fade-slide-enter-active { 
  transition: all 0.3s ease; 
}
.fade-slide-enter-from { 
  opacity: 0; 
  transform: translateY(15px); 
}
</style>