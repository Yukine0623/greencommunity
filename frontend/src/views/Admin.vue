<template>
  <div class="admin-layout-container">
    <AdminSidebar :adminName="adminName" @switchView="switchView" />

    <div class="main-content">
      <header class="content-header">
        <div class="header-left">
          <h1>{{ viewTitle }}</h1>
          <p class="subtitle">工作愉快，{{ adminName }}。当前系统运行正常。</p>
        </div>
      </header>

      <div v-if="!['applyExpert', 'applyProvider', 'taskAudit'].includes(currentView)" class="glass-card filter-bar">
        <div class="search-input">
          <span class="icon">🔍</span>
          <input v-model="searchName" :placeholder="searchPlaceholder" />
        </div>

        <div class="filter-group">
          <select v-if="currentView === 'users'" v-model="filterRole" class="custom-select">
            <option value="">所有角色</option>
            <option value="resident">普通用户</option>
            <option value="user">普通用户（兼容旧数据）</option>
            <option value="expert">邻里达人</option>
            <option value="provider">认证服务者</option>
            <option value="admin">管理员</option>
          </select>

          <select v-if="currentView === 'postManage'" v-model="processStatusFilter" class="custom-select">
            <option value="all">全部</option>
            <option value="pending">待处理</option>
            <option value="approved">已通过</option>
            <option value="rejected">已拒绝</option>
          </select>
        </div>
      </div>

      <Transition name="fade-slide" mode="out-in">
        <div class="glass-card table-card" v-if="currentView === 'users'" key="users">
          <div class="card-header"><h3>活跃用户清单 ({{ filteredUsers.length }})</h3></div>
          <div class="table-wrapper">
            <table class="custom-table">
              <thead>
                <tr><th>用户标识</th><th>账户名</th><th>职能角色</th><th>积分</th><th>注册日期</th><th class="center">操作</th></tr>
              </thead>
              <tbody>
                <tr v-for="user in paginatedUsers" :key="user.id">
                  <td class="id-col">#{{ user.id }}</td>
                  <td class="name-col">{{ user.username }}</td>
                  <td><span :class="['role-badge', user.role]">{{ formatUserRole(user) }}</span></td>
                  <td><span class="points-text">🪙 {{ user.points || 0 }}</span></td>
                  <td class="time-col">{{ user.created_at }}</td>
                  <td class="center">
                    <button class="btn-ghost" @click="openPointsPrompt(user)">修改积分</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="pagination">
            <button @click="usersPage--" :disabled="usersPage === 1">上一页</button>
            <span class="page-info">{{ usersPage }} / {{ totalUsersPages }}</span>
            <button @click="usersPage++" :disabled="usersPage === totalUsersPages">下一页</button>
          </div>
        </div>

        <div class="glass-card table-card" v-else-if="currentView === 'applyExpert' || currentView === 'applyProvider'" key="identity-audit">
          <div class="card-header"><h3>{{ currentView === 'applyExpert' ? '邻里达人审核' : '认证服务者审核' }}</h3></div>

          <div class="audit-card">
            <div class="audit-card-header">
              <h4>待处理申请</h4>
              <div class="audit-card-controls pending-controls">
                <div class="search-input mini-search">
                  <span class="icon">🔍</span>
                  <input v-model="pendingSearchName" placeholder="搜索申请人..." />
                </div>
              </div>
            </div>
            <div class="table-wrapper">
              <table class="custom-table">
                <thead>
                  <tr><th>申请人</th><th>资历描述</th><th>服务范围</th><th>定价参考</th><th>提交时间</th><th class="center">操作</th></tr>
                </thead>
                <tbody>
                  <tr v-for="item in paginatedPendingApplications" :key="`pending-${item.id}`">
                    <td class="name-col">{{ item.username }}</td>
                    <td class="reason-col">{{ item.reason }}</td>
                    <td>{{ item.service_scope || '-' }}</td>
                    <td>{{ item.pricing_note || '-' }}</td>
                    <td>{{ item.created_at }}</td>
                    <td class="action-cols center">
                      <div class="action-btns">
                        <button class="btn-success" @click="approve(item)">通过</button>
                        <button class="btn-danger" @click="openRejectModal(item, 'user')">拒绝</button>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="pendingApplications.length === 0">
                    <td colspan="6" class="empty-row">暂无待处理申请</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="pagination">
              <button @click="pendingAppsPage--" :disabled="pendingAppsPage === 1">上一页</button>
              <span class="page-info">{{ pendingAppsPage }} / {{ totalPendingAppsPages }}</span>
              <button @click="pendingAppsPage++" :disabled="pendingAppsPage === totalPendingAppsPages">下一页</button>
            </div>
          </div>

          <div class="audit-card">
            <div class="audit-card-header">
              <h4>历史申请记录</h4>
              <div class="audit-card-controls history-controls">
                <div class="search-input mini-search">
                  <span class="icon">🔍</span>
                  <input v-model="historySearchName" placeholder="搜索申请人..." />
                </div>
                <select v-model="applyHistoryStatusFilter" class="custom-select history-status-select">
                  <option value="all">全部</option>
                  <option value="approved">通过</option>
                  <option value="rejected">拒绝</option>
                </select>
              </div>
            </div>
            <div class="table-wrapper">
              <table class="custom-table">
                <thead>
                  <tr><th>申请人</th><th>资历描述</th><th>服务范围</th><th>定价参考</th><th>状态</th><th>提交时间</th></tr>
                </thead>
                <tbody>
                  <tr v-for="item in paginatedHistoryApplications" :key="`history-${item.id}`">
                    <td class="name-col">{{ item.username }}</td>
                    <td class="reason-col">{{ item.reason }}</td>
                    <td>{{ item.service_scope || '-' }}</td>
                    <td>{{ item.pricing_note || '-' }}</td>
                    <td><span :class="['status-pill', item.status]">{{ translateStatus(item.status) }}</span></td>
                    <td>{{ item.created_at }}</td>
                  </tr>
                  <tr v-if="historyApplications.length === 0">
                    <td colspan="6" class="empty-row">暂无历史申请记录</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="pagination">
              <button @click="historyAppsPage--" :disabled="historyAppsPage === 1">上一页</button>
              <span class="page-info">{{ historyAppsPage }} / {{ totalHistoryAppsPages }}</span>
              <button @click="historyAppsPage++" :disabled="historyAppsPage === totalHistoryAppsPages">下一页</button>
            </div>
          </div>
        </div>

        <div class="glass-card table-card" v-else-if="currentView === 'announcementManage'" key="announcement-manage">
          <div class="card-header"><h3>社区公告管理</h3></div>
          <div class="announcement-admin-panel">
            <div class="announcement-admin-card">
              <h4 class="panel-title">发布公告</h4>
              <div class="announcement-form">
                <input
                  v-model="announcementForm.title"
                  class="announcement-input"
                  placeholder="公告标题"
                  maxlength="100"
                />
                <textarea
                  v-model="announcementForm.content"
                  class="announcement-textarea"
                  placeholder="公告内容"
                  maxlength="1000"
                />
                <div class="announcement-form-footer">
                  <button class="btn-primary" @click="publishAnnouncement">发布公告</button>
                </div>
              </div>
            </div>

            <div class="announcement-admin-card">
              <h4 class="panel-title">已发布公告</h4>
              <div class="announcement-list">
                <div
                  v-for="item in paginatedAnnouncements"
                  :key="item.id"
                  class="announcement-item"
                >
                  <div class="announcement-item-header">
                    <strong>{{ item.title }}</strong>
                    <span class="announcement-time">{{ item.created_at }}</span>
                  </div>
                  <p class="announcement-content">{{ item.content }}</p>
                  <div class="announcement-item-footer">
                    <span class="announcement-author">发布人：{{ item.author }}</span>
                    <button class="btn-danger" @click="deleteAnnouncement(item.id)">删除</button>
                  </div>
                </div>
                <div v-if="filteredAnnouncements.length === 0" class="announcement-empty">暂无公告</div>
              </div>
              <div class="pagination">
                <button @click="announcementsPage--" :disabled="announcementsPage === 1">上一页</button>
                <span class="page-info">{{ announcementsPage }} / {{ totalAnnouncementsPages }}</span>
                <button @click="announcementsPage++" :disabled="announcementsPage === totalAnnouncementsPages">下一页</button>
              </div>
            </div>
          </div>
        </div>

        <div class="glass-card table-card" v-else-if="currentView === 'postManage'" key="post-manage">
          <div class="card-header"><h3>社区帖子管理</h3></div>
          <div class="table-wrapper">
            <table class="custom-table">
              <thead>
                <tr><th>内容概要</th><th>发布者</th><th>状态</th><th>反馈理由</th><th class="center">操作</th></tr>
              </thead>
              <tbody>
                <tr v-for="post in paginatedMixedFilteredPosts" :key="post.id">
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
                        <button class="btn-success" @click="approvePost(post.id)">通过</button>
                        <button class="btn-danger" @click="openPostRejectModal(post.id)">拒绝</button>
                      </template>
                    </div>
                  </td>
                </tr>
                <tr v-if="mixedFilteredPosts.length === 0">
                  <td colspan="5" class="empty-row">暂无帖子数据</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="pagination">
            <button @click="postsPage--" :disabled="postsPage === 1">上一页</button>
            <span class="page-info">{{ postsPage }} / {{ totalPostsPages }}</span>
            <button @click="postsPage++" :disabled="postsPage === totalPostsPages">下一页</button>
          </div>
        </div>

        <div v-else-if="currentView === 'taskAudit'" key="tasks" class="task-audit-panels">
          <div class="glass-card table-card task-audit-card">
            <div class="task-card-header">
              <h3>任务初审区</h3>
              <div class="search-input mini-search task-mini-search">
                <span class="icon">🔍</span>
                <input v-model="initialTaskSearchName" placeholder="搜索任务标题或发布方..." />
              </div>
            </div>
            <div class="table-wrapper">
              <table class="custom-table">
                <thead>
                  <tr><th>任务信息</th><th>发布方</th><th>悬赏积分</th><th>状态</th><th class="center">管理操作</th></tr>
                </thead>
                <tbody>
                  <tr v-for="task in paginatedInitialAuditTasks" :key="`initial-${task.id}`">
                    <td class="title-col">
                      <strong>{{ task.title }}</strong>
                      <span class="category-tag">{{ formatCategory(task.category) }}</span>
                    </td>
                    <td>{{ task.creator }}</td>
                    <td>🪙 {{ task.reward_points || 0 }}</td>
                    <td><span :class="['status-pill', task.status]">{{ translateStatus(task.status) }}</span></td>
                    <td class="action-cols center">
                      <div class="action-btns">
                        <button class="btn-ghost" @click="openTaskDetailModal(task)">详情</button>
                        <button class="btn-primary" @click="openAuditModal(task)">立即介入</button>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="initialAuditTasks.length === 0">
                    <td colspan="5" class="empty-row">暂无待初审任务</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="pagination">
              <button @click="initialTasksPage--" :disabled="initialTasksPage === 1">上一页</button>
              <span class="page-info">{{ initialTasksPage }} / {{ totalInitialTasksPages }}</span>
              <button @click="initialTasksPage++" :disabled="initialTasksPage === totalInitialTasksPages">下一页</button>
            </div>
          </div>

          <div class="glass-card table-card task-audit-card">
            <div class="task-card-header">
              <h3>任务复审区</h3>
              <div class="search-input mini-search task-mini-search">
                <span class="icon">🔍</span>
                <input v-model="recheckTaskSearchName" placeholder="搜索任务标题/发布方/接单方..." />
              </div>
            </div>
            <div class="table-wrapper">
              <table class="custom-table">
                <thead>
                  <tr><th>任务信息</th><th>发布方</th><th>接单方</th><th>状态</th><th class="center">管理操作</th></tr>
                </thead>
                <tbody>
                  <tr v-for="task in paginatedRecheckAuditTasks" :key="`recheck-${task.id}`">
                    <td class="title-col">
                      <strong>{{ task.title }}</strong>
                      <span class="category-tag">{{ formatCategory(task.category) }}</span>
                    </td>
                    <td>{{ task.creator }}</td>
                    <td>{{ task.worker || '暂无' }}</td>
                    <td><span :class="['status-pill', task.status]">{{ translateStatus(task.status) }}</span></td>
                    <td class="action-cols center">
                      <div class="action-btns">
                        <button class="btn-ghost" @click="openTaskDetailModal(task)">详情</button>
                        <button class="btn-primary" @click="openAuditModal(task)">立即介入</button>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="recheckAuditTasks.length === 0">
                    <td colspan="5" class="empty-row">暂无待复审任务</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="pagination">
              <button @click="recheckTasksPage--" :disabled="recheckTasksPage === 1">上一页</button>
              <span class="page-info">{{ recheckTasksPage }} / {{ totalRecheckTasksPages }}</span>
              <button @click="recheckTasksPage++" :disabled="recheckTasksPage === totalRecheckTasksPages">下一页</button>
            </div>
          </div>

          <div class="glass-card table-card task-audit-card">
            <div class="task-card-header">
              <h3>任务终止审核区</h3>
              <div class="search-input mini-search task-mini-search">
                <span class="icon">🔍</span>
                <input v-model="terminationTaskSearchName" placeholder="搜索任务标题或终止发起方..." />
              </div>
            </div>
            <div class="table-wrapper">
              <table class="custom-table">
                <thead>
                  <tr><th>任务信息</th><th>发起终止方</th><th>接单方</th><th>状态</th><th class="center">管理操作</th></tr>
                </thead>
                <tbody>
                  <tr v-for="task in paginatedTerminationAuditTasks" :key="`termination-${task.id}`">
                    <td class="title-col">
                      <strong>{{ task.title }}</strong>
                      <span class="category-tag">{{ formatCategory(task.category) }}</span>
                    </td>
                    <td>{{ task.terminate_requested_by || '未知' }}</td>
                    <td>{{ task.worker || '暂无' }}</td>
                    <td><span :class="['status-pill', task.status]">{{ translateStatus(task.status) }}</span></td>
                    <td class="action-cols center">
                      <div class="action-btns">
                        <button class="btn-ghost" @click="openTaskDetailModal(task)">详情</button>
                        <button class="btn-primary" @click="openAuditModal(task)">立即介入</button>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="terminationAuditTasks.length === 0">
                    <td colspan="5" class="empty-row">暂无待终止审核任务</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="pagination">
              <button @click="terminationTasksPage--" :disabled="terminationTasksPage === 1">上一页</button>
              <span class="page-info">{{ terminationTasksPage }} / {{ totalTerminationTasksPages }}</span>
              <button @click="terminationTasksPage++" :disabled="terminationTasksPage === totalTerminationTasksPages">下一页</button>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <Teleport to="body">
      <DetailModal
        :visible="showDetailModal"
        :title="currentPostDetail.title || '内容详情'"
        :rows="postDetailRows"
        close-text="已阅并关闭"
        width="620px"
        @close="closeDetailModal"
      />
      <DetailModal
        :visible="showTaskDetailModal"
        :title="currentTaskDetail.title || '任务详情'"
        :rows="taskDetailRows"
        width="660px"
        @close="closeTaskDetailModal"
      />

      <Transition name="zoom">
        <div v-if="showRejectModal" class="modal-overlay" @click.self="closeModal">
          <div class="modal-card reject-view">
            <div class="modal-header"><h3>请注明拒绝理由</h3></div>
            <div class="modal-body">
              <textarea v-model="rejectReason" placeholder="该理由将向相关用户公示..." class="styled-textarea"></textarea>
            </div>
            <div class="modal-footer">
              <button class="btn-ghost" @click="closeModal">取消</button>
              <button class="btn-confirm-danger" @click="confirmReject">确认拒绝</button>
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
              <div v-if="selectedTask.status === 'terminating_admin_review'" class="data-row dispute">
                <strong>终止申请：</strong><p>{{ selectedTask.terminate_reason || '未填写' }}</p>
              </div>
              <textarea v-model="auditReason" placeholder="请输入裁定依据..." class="styled-textarea" :readonly="isProcessed(selectedTask.status)"></textarea>
              <div v-if="selectedTask.status === 'terminating_admin_review'" class="settlement-row">
                <div class="settlement-item">
                  <label>发单方积分</label>
                  <input v-model.number="terminationSettlement.creatorPoints" type="number" min="0" class="settlement-input" />
                </div>
                <div class="settlement-item">
                  <label>接单方积分</label>
                  <input v-model.number="terminationSettlement.workerPoints" type="number" min="0" class="settlement-input" />
                </div>
                <p class="settlement-hint">
                  分配合计：{{ (terminationSettlement.creatorPoints || 0) + (terminationSettlement.workerPoints || 0) }} / {{ selectedTask.reward_points || 0 }}
                </p>
              </div>
            </div>
            <div v-if="!isProcessed(selectedTask.status)" class="modal-footer">
              <button class="btn-danger" @click="submitAudit('reject')">拒绝/判输</button>
              <button class="btn-success" @click="submitAudit('approve')">通过/判胜</button>
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
import DetailModal from '@/components/DetailModal.vue'

const userStore = useUserStore()

// --- 状态定义 ---
const adminName = computed(() => userStore.username)
const currentView = ref('users')
const searchName = ref('')
const pendingSearchName = ref('')
const historySearchName = ref('')
const initialTaskSearchName = ref('')
const recheckTaskSearchName = ref('')
const terminationTaskSearchName = ref('')
const applyHistoryStatusFilter = ref('all')
const filterRole = ref('')
const pageSize = 5
const usersPage = ref(1)
const pendingAppsPage = ref(1)
const historyAppsPage = ref(1)
const announcementsPage = ref(1)
const postsPage = ref(1)
const initialTasksPage = ref(1)
const recheckTasksPage = ref(1)
const terminationTasksPage = ref(1)

const users = ref([])
const applications = ref([])
const auditPosts = ref([])
const auditHistory = ref([])
const auditTasks = ref([])
const adminAnnouncements = ref([])
const announcementForm = ref({
  title: '',
  content: ''
})

const processStatusFilter = ref('all') 

const showRejectModal = ref(false)
const showDetailModal = ref(false)
const showTaskDetailModal = ref(false)
const showAuditModal = ref(false)
const rejectType = ref('')
const rejectReason = ref('')
const currentUser = ref('')
const currentPostDetail = ref({})
const currentTaskDetail = ref({})
const selectedTask = ref({})
const auditReason = ref('')
const terminationSettlement = ref({
  creatorPoints: 0,
  workerPoints: 0
})

// --- 计算属性 ---
const viewTitle = computed(() => {
  const titles = {
    users: '用户管理系统',
    applyExpert: '社区身份审核 / 邻里达人',
    applyProvider: '社区身份审核 / 认证服务者',
    announcementManage: '社区内容管理 / 公告',
    postManage: '社区内容管理 / 帖子',
    taskAudit: '任务调度与仲裁中心'
  }
  return titles[currentView.value]
})

const searchPlaceholder = computed(() => {
  if (currentView.value === 'users') return '搜索用户名...'
  if (currentView.value === 'announcementManage') return '搜公告标题或发布人...'
  if (currentView.value === 'postManage') return '搜标题、内容或作者...'
  return '搜索关键词或发起人...'
})

const currentApplyType = computed(() => (currentView.value === 'applyProvider' ? 'provider' : 'expert'))

// 🚀 1. 帖子混合过滤逻辑
const mixedFilteredPosts = computed(() => {
  const combined = [...auditPosts.value.map(p => ({...p, status: 'pending'})), ...auditHistory.value]
  return combined.filter(p => {
    const matchSearch = p.title.includes(searchName.value) || p.author.includes(searchName.value)
    
    // 状态过滤逻辑
    let matchStatus = true
    if (processStatusFilter.value === 'pending') matchStatus = p.status === 'pending'
    else if (processStatusFilter.value === 'approved') matchStatus = p.status === 'approved'
    else if (processStatusFilter.value === 'rejected') matchStatus = p.status === 'rejected'
    
    return matchSearch && matchStatus
  })
})

const initialAuditTasks = computed(() => {
  const q = initialTaskSearchName.value.toLowerCase().trim()
  return auditTasks.value.filter((task) => {
    if (task.status !== 'auditing') return false
    if (!q) return true
    return `${task.title || ''} ${task.creator || ''}`.toLowerCase().includes(q)
  })
})

const recheckAuditTasks = computed(() => {
  const q = recheckTaskSearchName.value.toLowerCase().trim()
  return auditTasks.value.filter((task) => {
    if (task.status !== 'intervention') return false
    if (!q) return true
    return `${task.title || ''} ${task.creator || ''} ${task.worker || ''}`.toLowerCase().includes(q)
  })
})
const terminationAuditTasks = computed(() => {
  const q = terminationTaskSearchName.value.toLowerCase().trim()
  return auditTasks.value.filter((task) => {
    if (task.status !== 'terminating_admin_review') return false
    if (!q) return true
    return `${task.title || ''} ${task.terminate_requested_by || ''} ${task.worker || ''}`.toLowerCase().includes(q)
  })
})

const filteredUsers = computed(() => users.value.filter(u => 
  u.username.toLowerCase().includes(searchName.value.toLowerCase()) && 
  (filterRole.value
    ? (
      filterRole.value === 'expert' ? !!u.is_expert :
      filterRole.value === 'provider' ? !!u.is_provider :
      filterRole.value === 'resident' ? !u.is_expert && !u.is_provider && (u.role === 'resident' || u.role === 'user') :
      u.role === filterRole.value
    )
    : true)
))

const paginate = (items, page) => {
  const start = (page - 1) * pageSize
  return items.slice(start, start + pageSize)
}
const totalPagesOf = (items) => Math.max(1, Math.ceil(items.length / pageSize))

const paginatedUsers = computed(() => {
  return paginate(filteredUsers.value, usersPage.value)
})

const totalUsersPages = computed(() => totalPagesOf(filteredUsers.value))

const currentTypeApplications = computed(() => {
  return (applications.value || []).filter(item => item.apply_type === currentApplyType.value)
})
const pendingApplications = computed(() => {
  const q = pendingSearchName.value.toLowerCase().trim()
  return currentTypeApplications.value.filter(item =>
    item.status === 'pending' && item.username.toLowerCase().includes(q)
  )
})
const paginatedPendingApplications = computed(() => paginate(pendingApplications.value, pendingAppsPage.value))
const totalPendingAppsPages = computed(() => totalPagesOf(pendingApplications.value))

const historyApplications = computed(() => {
  const q = historySearchName.value.toLowerCase().trim()
  return currentTypeApplications.value.filter(item => {
    if (item.status === 'pending') return false
    if (applyHistoryStatusFilter.value !== 'all' && item.status !== applyHistoryStatusFilter.value) return false
    return item.username.toLowerCase().includes(q)
  })
})
const paginatedHistoryApplications = computed(() => paginate(historyApplications.value, historyAppsPage.value))
const totalHistoryAppsPages = computed(() => totalPagesOf(historyApplications.value))

const filteredAnnouncements = computed(() => {
  return adminAnnouncements.value.filter((item) => {
    return item.title.includes(searchName.value) || item.author.includes(searchName.value)
  })
})
const paginatedAnnouncements = computed(() => paginate(filteredAnnouncements.value, announcementsPage.value))
const totalAnnouncementsPages = computed(() => totalPagesOf(filteredAnnouncements.value))

const paginatedMixedFilteredPosts = computed(() => paginate(mixedFilteredPosts.value, postsPage.value))
const totalPostsPages = computed(() => totalPagesOf(mixedFilteredPosts.value))

const paginatedInitialAuditTasks = computed(() => paginate(initialAuditTasks.value, initialTasksPage.value))
const totalInitialTasksPages = computed(() => totalPagesOf(initialAuditTasks.value))

const paginatedRecheckAuditTasks = computed(() => paginate(recheckAuditTasks.value, recheckTasksPage.value))
const totalRecheckTasksPages = computed(() => totalPagesOf(recheckAuditTasks.value))

const paginatedTerminationAuditTasks = computed(() => paginate(terminationAuditTasks.value, terminationTasksPage.value))
const totalTerminationTasksPages = computed(() => totalPagesOf(terminationAuditTasks.value))
const postDetailRows = computed(() => {
  return [
    { label: '作者', value: currentPostDetail.value.author },
    {
      label: '状态',
      value: currentPostDetail.value.status ? translateStatus(currentPostDetail.value.status) : '--',
      badge: true,
      badgeType: currentPostDetail.value.status || 'default'
    },
    { label: '发布时间', value: currentPostDetail.value.processed_at || currentPostDetail.value.created_at },
    {
      label: '反馈理由',
      value: currentPostDetail.value.reject_reason || '--',
      visible: currentPostDetail.value.status === 'rejected' || !!currentPostDetail.value.reject_reason
    },
    { label: '内容详情', value: currentPostDetail.value.content, multiline: true }
  ]
})
const taskDetailRows = computed(() => {
  return [
    { label: '任务标题', value: currentTaskDetail.value.title },
    { label: '任务分类', value: formatCategory(currentTaskDetail.value.category) },
    { label: '发布方', value: currentTaskDetail.value.creator },
    { label: '接单方', value: currentTaskDetail.value.worker || '暂无' },
    { label: '悬赏积分', value: currentTaskDetail.value.reward_points || 0 },
    {
      label: '任务状态',
      value: currentTaskDetail.value.status ? translateStatus(currentTaskDetail.value.status) : '--',
      badge: true,
      badgeType: currentTaskDetail.value.status || 'default'
    },
    { label: '发布时间', value: currentTaskDetail.value.created_at },
    { label: '任务描述', value: currentTaskDetail.value.content, multiline: true },
    {
      label: '达人反馈',
      value: currentTaskDetail.value.result_desc,
      multiline: true,
      visible: !!currentTaskDetail.value.result_desc
    },
    {
      label: '终止发起人',
      value: currentTaskDetail.value.terminate_requested_by,
      visible: !!currentTaskDetail.value.terminate_requested_by
    },
    {
      label: '终止原因',
      value: currentTaskDetail.value.terminate_reason,
      multiline: true,
      visible: !!currentTaskDetail.value.terminate_reason
    }
  ]
})

const clampPage = (pageRef, totalRef) => {
  if (pageRef.value > totalRef.value) pageRef.value = totalRef.value
  if (pageRef.value < 1) pageRef.value = 1
}

watch(filteredUsers, () => {
  usersPage.value = 1
})
watch(totalUsersPages, () => clampPage(usersPage, totalUsersPages))

watch(pendingApplications, () => {
  pendingAppsPage.value = 1
})
watch(totalPendingAppsPages, () => clampPage(pendingAppsPage, totalPendingAppsPages))

watch(historyApplications, () => {
  historyAppsPage.value = 1
})
watch(totalHistoryAppsPages, () => clampPage(historyAppsPage, totalHistoryAppsPages))

watch(filteredAnnouncements, () => {
  announcementsPage.value = 1
})
watch(totalAnnouncementsPages, () => clampPage(announcementsPage, totalAnnouncementsPages))

watch(mixedFilteredPosts, () => {
  postsPage.value = 1
})
watch(totalPostsPages, () => clampPage(postsPage, totalPostsPages))

watch(initialAuditTasks, () => {
  initialTasksPage.value = 1
})
watch(totalInitialTasksPages, () => clampPage(initialTasksPage, totalInitialTasksPages))

watch(recheckAuditTasks, () => {
  recheckTasksPage.value = 1
})
watch(totalRecheckTasksPages, () => clampPage(recheckTasksPage, totalRecheckTasksPages))

watch(terminationAuditTasks, () => {
  terminationTasksPage.value = 1
})
watch(totalTerminationTasksPages, () => clampPage(terminationTasksPage, totalTerminationTasksPages))

// --- API 方法 ---
const refreshData = () => {
  if (currentView.value === 'users') fetchUsers()
  if (currentView.value === 'applyExpert' || currentView.value === 'applyProvider') fetchApplications()
  if (currentView.value === 'announcementManage') fetchAnnouncements()
  if (currentView.value === 'postManage') { fetchAuditPosts(); fetchAuditHistory() }
  if (currentView.value === 'taskAudit') fetchAuditTasks()
}

const fetchUsers = async () => { const res = await axios.get('http://127.0.0.1:8000/api/users/'); users.value = res.data.users }
const fetchApplications = async () => { const res = await axios.get('http://127.0.0.1:8000/api/applications/'); applications.value = res.data.data }
const fetchAuditPosts = async () => { const res = await axios.get('http://127.0.0.1:8000/api/all_pending_posts/'); auditPosts.value = res.data.posts }
const fetchAuditHistory = async () => { const res = await axios.get('http://127.0.0.1:8000/api/audit_history/'); auditHistory.value = res.data.history }
const fetchAuditTasks = async () => { const res = await axios.get('http://127.0.0.1:8000/api/get_audit_tasks/'); auditTasks.value = res.data.tasks }
const fetchAnnouncements = async () => {
  const res = await axios.get('http://127.0.0.1:8000/api/announcements/')
  adminAnnouncements.value = res.data.announcements || []
}

const switchView = (view) => {
  currentView.value = view
  searchName.value = ''
  pendingSearchName.value = ''
  historySearchName.value = ''
  initialTaskSearchName.value = ''
  recheckTaskSearchName.value = ''
  terminationTaskSearchName.value = ''
  usersPage.value = 1
  pendingAppsPage.value = 1
  historyAppsPage.value = 1
  announcementsPage.value = 1
  postsPage.value = 1
  initialTasksPage.value = 1
  recheckTasksPage.value = 1
  terminationTasksPage.value = 1
  applyHistoryStatusFilter.value = 'all'
  processStatusFilter.value = 'all' // 切换视图时重置状态
  refreshData()
}

// --- 审批逻辑 ---
const approvePost = async (id) => { await axios.post('http://127.0.0.1:8000/api/review_post/', { id, action: 'approve' }); refreshData() }
const approve = async (item) => {
  await axios.post('http://127.0.0.1:8000/api/approve/', {
    id: item.id,
    username: item.username,
    apply_type: item.apply_type
  })
  refreshData()
}
const publishAnnouncement = async () => {
  if (!announcementForm.value.title.trim() || !announcementForm.value.content.trim()) {
    alert('请填写公告标题和内容')
    return
  }
  const res = await axios.post('http://127.0.0.1:8000/api/create_announcement/', {
    username: adminName.value,
    title: announcementForm.value.title,
    content: announcementForm.value.content
  })
  if (res.data.code !== 200) {
    alert(res.data.message || '公告发布失败')
    return
  }
  announcementForm.value.title = ''
  announcementForm.value.content = ''
  fetchAnnouncements()
}
const deleteAnnouncement = async (id) => {
  if (!confirm('确认删除这条公告吗？')) return
  const res = await axios.post('http://127.0.0.1:8000/api/delete_announcement/', {
    username: adminName.value,
    id
  })
  if (res.data.code !== 200) {
    alert(res.data.message || '删除失败')
    return
  }
  fetchAnnouncements()
}
const openPointsPrompt = async (user) => {
  const input = prompt(`请输入 ${user.username} 的新积分（当前 ${user.points || 0}）`, user.points || 0)
  if (input === null) return
  const points = Number(input)
  if (!Number.isInteger(points) || points < 0) {
    alert('请输入大于等于 0 的整数')
    return
  }

  try {
    const res = await axios.post('http://127.0.0.1:8000/api/update_user_points/', {
      admin_username: adminName.value,
      user_id: user.id,
      points
    })
    if (res.data.code === 200) {
      fetchUsers()
      alert('积分修改成功')
    } else {
      alert(res.data.message || '积分修改失败')
    }
  } catch (error) {
    alert(error.response?.data?.message || '积分修改失败')
  }
}

const confirmReject = async () => {
  if (!rejectReason.value.trim()) return alert('请填写拒绝原因')
  const url = rejectType.value === 'user' ? '/api/reject/' : '/api/review_post/'
  const data = rejectType.value === 'user'
    ? {
      id: currentUser.value?.id,
      username: currentUser.value?.username,
      apply_type: currentUser.value?.apply_type,
      reason: rejectReason.value
    }
    : { id: currentUser.value, action: 'reject', reason: rejectReason.value }
  await axios.post(`http://127.0.0.1:8000${url}`, data)
  showRejectModal.value = false
  refreshData()
}

const submitAudit = async (action) => {
  if (action === 'reject' && !auditReason.value.trim()) return alert('请填写理由')
  const payload = { taskId: selectedTask.value.id, action, reason: auditReason.value }
  if (selectedTask.value.status === 'terminating_admin_review' && action === 'approve') {
    const creatorPoints = Number(terminationSettlement.value.creatorPoints)
    const workerPoints = Number(terminationSettlement.value.workerPoints)
    if (!Number.isInteger(creatorPoints) || !Number.isInteger(workerPoints) || creatorPoints < 0 || workerPoints < 0) {
      alert('请填写合法的积分分配')
      return
    }
    if (creatorPoints + workerPoints !== Number(selectedTask.value.reward_points || 0)) {
      alert(`积分分配总和必须等于悬赏积分 ${selectedTask.value.reward_points || 0}`)
      return
    }
    payload.creator_points = creatorPoints
    payload.worker_points = workerPoints
  }
  await axios.post('http://127.0.0.1:8000/api/admin_handle_review/', payload)
  showAuditModal.value = false
  fetchAuditTasks()
}

// --- UI 辅助 ---
const translateStatus = (s) => {
  const map = {
    pending: '待处理',
    approved: '通过',
    rejected: '拒绝',
    auditing: '待初审',
    accepted: '进行中',
    submitted: '待确认',
    intervention: '仲裁中',
    terminating_pending_peer: '待对方确认终止',
    terminating_admin_review: '待管理员终止审核',
    terminated: '已终止',
    finished: '已结案'
  }
  return map[s] || s
}
const formatRole = (r) => ({
  resident: '普通用户',
  user: '普通用户',
  expert: '邻里达人',
  provider: '认证服务者',
  admin: '管理员'
}[r] || r)
const formatUserRole = (u) => {
  if (!u) return '-'
  if (u.role === 'admin') return '管理员'
  if (u.is_expert && u.is_provider) return '邻里达人 / 认证服务者'
  if (u.is_expert) return '邻里达人'
  if (u.is_provider) return '认证服务者'
  return formatRole(u.role)
}
const formatApplyType = (t) => ({ expert: '邻里达人', provider: '认证服务者' }[t] || '邻里达人')
const formatCategory = (c) => ({ errand: '跑腿', repair: '维修', pet: '宠物' }[c] || '互助')
const isProcessed = (s) => ['pending', 'rejected', 'finished'].includes(s)

const openDetailModal = (post) => { currentPostDetail.value = post; showDetailModal.value = true }
const closeDetailModal = () => { showDetailModal.value = false }
const openTaskDetailModal = (task) => {
  currentTaskDetail.value = task
  showTaskDetailModal.value = true
}
const closeTaskDetailModal = () => { showTaskDetailModal.value = false }
const openRejectModal = (payload, type) => { rejectType.value = type; currentUser.value = payload; rejectReason.value = ''; showRejectModal.value = true }
const openPostRejectModal = (id) => openRejectModal(id, 'post')
const closeModal = () => { showRejectModal.value = false }
const openAuditModal = (task) => {
  selectedTask.value = task
  auditReason.value = task.audit_reason || task.intervention_decision || task.terminate_reject_reason || ''
  terminationSettlement.value = {
    creatorPoints: Number(task.terminate_creator_points ?? task.reward_points ?? 0),
    workerPoints: Number(task.terminate_worker_points ?? 0)
  }
  showAuditModal.value = true
}

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
.pagination {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}
.pagination button {
  border: 1px solid #d9e4de;
  background: #fff;
  color: #1a4d38;
  border-radius: 8px;
  padding: 6px 12px;
  cursor: pointer;
}
.pagination button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.page-info {
  color: #64748b;
  font-size: 13px;
}
.excerpt { font-size: 12px; color: #94a3b8; margin-top: 4px; }
.task-audit-panels {
  display: flex;
  flex-direction: column;
  gap: 22px;
}
.task-audit-card {
  overflow: hidden;
}
.task-card-header {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.task-card-header h3 {
  flex: 1 1 auto;
  min-width: 0;
  margin: 0;
  color: #1a4d38;
  font-size: 20px;
}
.task-mini-search {
  width: 320px !important;
  min-width: 320px;
  max-width: 320px !important;
  flex: 0 0 320px !important;
  margin-left: auto;
  margin-right: 16px;
  box-sizing: border-box;
}
.task-card-header .task-mini-search input {
  width: 100%;
  box-sizing: border-box;
}

@media (max-width: 1200px) {
  .task-card-header {
    flex-wrap: wrap;
  }
  .task-mini-search {
    width: 80% !important;
    min-width: 0;
    max-width: 320px !important;
    flex: 0 1 320px !important;
  }
}
.empty-row { text-align: center; color: #94a3b8; padding: 26px 0; }
.category-tag {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #ecfdf5;
  color: #059669;
  font-size: 12px;
}
.announcement-admin-panel {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.announcement-admin-card {
  border: 1px solid #e2ece7;
  border-radius: 16px;
  background: #f8faf9;
  padding: 16px;
}
.panel-title {
  margin: 0 0 10px;
  color: #1a4d38;
  font-size: 16px;
}
.announcement-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.announcement-input,
.announcement-textarea {
  border: 1px solid #d9e4de;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 14px;
  outline: none;
}
.announcement-textarea {
  min-height: 90px;
  resize: vertical;
}
.announcement-form-footer {
  display: flex;
  justify-content: flex-end;
}
.announcement-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.announcement-item {
  background: white;
  border: 1px solid #e2ece7;
  border-radius: 12px;
  padding: 10px 12px;
}
.announcement-item-header {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 4px;
}
.announcement-time {
  color: #94a3b8;
  font-size: 12px;
}
.announcement-content {
  margin: 0;
  color: #4a5568;
  line-height: 1.6;
  white-space: pre-wrap;
}
.announcement-item-footer {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.announcement-author {
  color: #94a3b8;
  font-size: 12px;
}
.announcement-empty {
  text-align: center;
  color: #94a3b8;
  padding: 8px 0;
}
.audit-card {
  border: 1px solid #e2ece7;
  border-radius: 16px;
  padding: 14px;
  background: #f8faf9;
  overflow: hidden;
}
.audit-card + .audit-card {
  margin-top: 16px;
}
.audit-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: nowrap;
  margin-bottom: 10px;
  gap: 12px;
}
.audit-card-header h4 {
  margin: 0;
  color: #1a4d38;
  font-size: 16px;
}
.audit-card-controls {
  margin-left: auto;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: nowrap;
}
.audit-card-controls .search-input {
  flex: 0 0 auto;
  max-width: none;
}
.pending-controls {
  width: auto;
  min-width: 0;
  flex: 0 0 auto;
  margin-right: 12px;
  box-sizing: border-box;
}
.history-controls {
  width: auto;
  min-width: 0;
  flex: 0 0 auto;
  margin-right: 12px;
}
.mini-search {
  width: 320px !important;
  min-width: 320px;
  max-width: 320px !important;
  flex: 0 0 320px !important;
  margin-right: 8px;
  box-sizing: border-box;
}
.mini-search input {
  width: 100%;
  padding: 10px 12px 10px 38px;
  box-sizing: border-box;
}
.mini-search .icon {
  left: 12px;
}
.history-status-select {
  width: 140px;
  min-width: 140px;
  justify-self: end;
  flex: 0 0 140px;
}

@media (max-width: 1200px) {
  .audit-card-header {
    flex-wrap: wrap;
  }
  .audit-card-controls {
    width: 100%;
    justify-content: flex-end;
    flex-wrap: wrap;
  }
  .pending-controls {
    width: auto;
    min-width: 0;
  }
  .history-controls {
    width: auto;
    min-width: 0;
    margin-right: 0;
  }
  .mini-search {
    width: 80% !important;
    max-width: 320px !important;
    min-width: 0;
    flex: 0 1 320px !important;
  }
  .history-status-select {
    width: 140px;
    min-width: 140px;
  }
}

/* 标签与按钮 */
.status-pill, .role-badge { padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
.type-pill { padding: 5px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.type-pill.expert { background: #eef2ff; color: #3730a3; }
.type-pill.provider { background: #ecfeff; color: #0f766e; }
.status-pill.auditing { background: #fef9c3; color: #a16207; }
.status-pill.pending { background: #e0f2fe; color: #0369a1; }
.status-pill.approved { background: #dcfce7; color: #166534; }
.status-pill.rejected { background: #fee2e2; color: #991b1b; }
.status-pill.accepted { background: #dbeafe; color: #1d4ed8; }
.status-pill.submitted { background: #ede9fe; color: #5b21b6; }
.status-pill.intervention { background: #ffedd5; color: #c2410c; }
.status-pill.terminating_pending_peer { background: #ffe4e6; color: #be123c; }
.status-pill.terminating_admin_review { background: #fef3c7; color: #92400e; }
.status-pill.finished { background: #d1fae5; color: #065f46; }
.status-pill.terminated { background: #e2e8f0; color: #334155; }

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
  padding: 16px;
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
  max-height: 90vh;
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
.settlement-row {
  margin-top: 10px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #e2ece7;
  background: #f8faf9;
}
.settlement-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
}
.settlement-item label {
  font-size: 13px;
  color: #1a4d38;
}
.settlement-input {
  border: 1px solid #d9e4de;
  border-radius: 10px;
  padding: 8px 10px;
  outline: none;
}
.settlement-hint {
  margin: 2px 0 0;
  font-size: 12px;
  color: #64748b;
}

/* 滚动内容区 */
.modal-body {
  max-height: 350px;
  overflow-y: auto;
  padding: 10px 0;
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
