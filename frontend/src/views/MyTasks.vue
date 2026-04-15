<template>
  <div class="my-tasks-container">
    <header class="page-header glass-card">
      <div class="header-left">
        <h1>任务管理</h1>
        <p class="subtitle">追踪互助进度</p>
      </div>
      <div class="tab-group">
        <button :class="['tab-btn', { active: activeTab === 'posted' }]" @click="activeTab = 'posted'">📤 我发布的</button>
        <button
          v-if="canViewAcceptedTab"
          :class="['tab-btn', { active: activeTab === 'accepted' }]"
          @click="activeTab = 'accepted'"
        >
          📥 我接手的
        </button>
      </div>
    </header>

    <div class="filter-bar glass-card">
      <div class="filter-item">
        <label>状态：</label>
        <select v-model="statusFilter">
          <option value="all">全部</option>
          <option value="auditing">审核中</option>
          <option value="rejected">被驳回</option>
          <option value="pending">招募中</option>
          <option value="accepted">进行中</option>
          <option value="submitted">待确认</option>
          <option value="terminating_pending_peer">待对方确认终止</option>
          <option value="terminating_admin_review">待管理员终止审核</option>
          <option value="terminated">已终止</option>
          <option value="finished">已完成</option>
        </select>
      </div>
      <div class="search-mini">
        <input v-model="miniSearch" placeholder="搜索标题..." />
      </div>
    </div>

    <main class="task-grid" v-if="filteredDisplayTasks.length > 0">
      <div v-for="task in filteredDisplayTasks" :key="task.id" class="task-card glass-card">
        <div class="card-body">
          <div class="card-top">
            <span :class="['category-badge', task.category]">{{ formatCategory(task.category) }}</span>
            <span :class="['status-tag', task.status]">{{ formatStatus(task.status) }}</span>
          </div>
          <div class="title-row">
            <span class="points-badge">🪙 {{ task.reward_points || 0 }}</span>
            <h3 class="card-title">{{ task.title }}</h3>
          </div>
          <div class="task-meta">
            <p>👤 {{ activeTab === 'posted' ? '接单人：' + (task.worker || '暂无') : '发布人：' + task.creator }}</p>
            <p>🕒 {{ task.created_at }}</p>
            <p v-if="activeTab === 'accepted' && task.accepted_at">📥 接单时间：{{ task.accepted_at }}</p>
            <p v-if="task.status === 'terminating_pending_peer'">⚠️ 终止发起人：{{ task.terminate_requested_by || '未知' }}</p>
          </div>
        </div>

        <div class="card-footer">
          <div class="action-group">
            <button v-if="activeTab === 'posted' && task.status === 'submitted'" class="btn-blue" @click="handleConfirmFinish(task)">确认结项</button>
            <button v-if="activeTab === 'posted' && task.status === 'pending'" class="btn-ghost" @click="openQuoteManage(task)">报价管理</button>
            <button v-if="activeTab === 'posted' && task.status === 'finished' && task.worker && !task.reviewed_by_creator" class="btn-success" @click="openReviewModal(task)">评价服务</button>
            <button v-if="task.reviewed_by_creator" class="btn-ghost" @click="openReviewDetailModal(task)">
              {{ activeTab === 'accepted' ? '查看收到评价' : '查看评价' }}
            </button>
            <button v-if="activeTab === 'posted' && canEditTask(task)" class="btn-ghost" @click="openEditModal(task)">修改</button>
            <button v-if="activeTab === 'posted' && canDeleteTask(task)" class="btn-danger-lite" @click="handleDeleteTask(task)">删除</button>
            <button
              v-if="canRequestTerminate(task)"
              class="btn-warn"
              @click="handleRequestTerminate(task)"
            >
              终止任务
            </button>
            <button
              v-if="canRespondTerminate(task)"
              class="btn-success"
              @click="handleRespondTerminate(task, true)"
            >
              同意终止
            </button>
            <button
              v-if="canRespondTerminate(task)"
              class="btn-abandon"
              @click="handleRespondTerminate(task, false)"
            >
              拒绝终止
            </button>
            
            <template v-if="activeTab === 'accepted' && task.status === 'accepted'">
              <button class="btn-abandon" @click="openAbandonModal(task)">放弃任务</button>
              <button class="btn-blue" @click="openSubmitModal(task)">提交成果</button>
            </template>
            <button
              v-if="canOpenChat(task)"
              class="btn-chat"
              @click="openChatModal(task)"
            >
              聊天
            </button>
            
            <button class="btn-detail" @click="openDetail(task)">详情</button>
          </div>
        </div>
      </div>
    </main>

    <div v-else class="empty-state">📂 暂无任务记录</div>

    <Transition name="fade">
      <div v-if="showSubmitModal" class="modal-overlay" @click.self="showSubmitModal = false">
        <div class="modal-content glass-card mini-modal">
          <h3 class="modal-title">✅ 提交任务</h3>
          <div class="form-item">
            <label>成果描述</label>
            <textarea v-model="submitForm.desc" placeholder="请输入完成详情..." class="modal-textarea"></textarea>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showSubmitModal = false">取消</button>
            <button class="btn-blue" @click="confirmSubmit">确认提交</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
        <div class="modal-content glass-card task-modal">
          <button class="close-x" @click="showEditModal = false">×</button>
          <h3 class="modal-title">✏️ 修改任务</h3>
          <div class="post-form">
            <div class="form-item">
              <label>任务标题</label>
              <input v-model="editForm.title" maxlength="50" placeholder="简述你的需求 (50字以内)" />
            </div>
            <div class="form-item">
              <label>任务类型</label>
              <select v-model="editForm.category">
                <option value="errand">跑腿代购</option>
                <option value="repair">家电维修</option>
                <option value="pet">宠物照顾</option>
                <option value="other">其他互助</option>
              </select>
            </div>
            <div class="form-item">
              <label>详情描述</label>
              <textarea v-model="editForm.content" maxlength="1000" placeholder="请详细说明时间、地点、具体要求等..."></textarea>
            </div>
            <div class="form-item">
              <label>悬赏积分</label>
              <input v-model.number="editForm.reward_points" type="number" min="1" step="1" placeholder="请输入悬赏积分" />
              <small class="form-tip">保存后任务会自动下架，并重新进入管理员审核。</small>
            </div>
            <div class="form-item">
              <label>任务位置（可选）</label>
              <input v-model="editForm.community_zone" maxlength="50" placeholder="手动填写片区/地点（如：A区3栋附近）" />
              <div class="location-manual-grid">
                <input
                  v-model.number="editForm.latitude"
                  type="number"
                  step="0.000001"
                  min="-90"
                  max="90"
                  placeholder="手动填写纬度（可选）"
                />
                <input
                  v-model.number="editForm.longitude"
                  type="number"
                  step="0.000001"
                  min="-180"
                  max="180"
                  placeholder="手动填写经度（可选）"
                />
              </div>
              <div class="location-actions">
                <button class="btn-location" type="button" @click="handleGetEditLocation">获取当前位置</button>
                <button
                  v-if="editForm.latitude !== null || editForm.longitude !== null || editForm.community_zone"
                  class="btn-location-clear"
                  type="button"
                  @click="clearEditLocation"
                >
                  清除位置
                </button>
              </div>
            </div>
            <button class="btn-submit-task" @click="confirmEditTask">保存并重新提交审核</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="showAbandonModal" class="modal-overlay" @click.self="showAbandonModal = false">
        <div class="modal-content glass-card mini-modal">
          <h3 class="modal-title" style="color: #e53e3e;">⚠️ 放弃任务</h3>
          <div class="form-item">
            <label>放弃原因</label>
            <textarea v-model="abandonForm.reason" placeholder="请输入原因..." class="modal-textarea"></textarea>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showAbandonModal = false">取消</button>
            <button class="btn-danger" @click="confirmAbandon">确认放弃</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="showQuoteManageModal" class="modal-overlay" @click.self="showQuoteManageModal = false">
        <div class="modal-content glass-card mini-modal">
          <h3 class="modal-title">报价管理</h3>
          <p class="modal-subtitle">{{ quoteManageTask?.title || '' }}</p>
          <div v-if="quoteList.length === 0" class="empty-state" style="padding: 24px 8px;">暂无报价</div>
          <div v-else class="quote-list">
            <div class="quote-item" v-for="q in quoteList" :key="q.id">
              <div class="quote-main">
                <div class="quote-title">{{ q.quoter }} · 报价 {{ q.amount_points }} 积分</div>
                <div class="quote-message">{{ q.message || '暂无说明' }}</div>
                <div class="quote-meta">{{ q.created_at }} · {{ q.status }}</div>
              </div>
              <button v-if="q.status === 'pending'" class="btn-blue" @click="chooseQuote(q)">选择此报价</button>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showQuoteManageModal = false">关闭</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="showReviewModal" class="modal-overlay" @click.self="showReviewModal = false">
        <div class="modal-content glass-card mini-modal review-modal">
          <h3 class="modal-title">评价服务</h3>
          <p class="modal-subtitle">{{ reviewForm.taskTitle }}</p>
          <div class="form-item">
            <label>星级评分</label>
            <div class="star-rating">
              <button
                v-for="star in 5"
                :key="star"
                type="button"
                :class="['star-btn', { active: star <= reviewForm.rating }]"
                @click="reviewForm.rating = star"
              >
                ★
              </button>
              <span class="rating-text">{{ reviewForm.rating }} 分</span>
            </div>
          </div>
          <div class="form-item">
            <label>服务标签（可多选）</label>
            <div class="review-tags">
              <button
                v-for="tag in reviewTagOptions"
                :key="tag"
                type="button"
                :class="['tag-btn', { active: reviewForm.tags.includes(tag) }]"
                @click="toggleReviewTag(tag)"
              >
                {{ tag }}
              </button>
            </div>
          </div>
          <div class="form-item">
            <label>评价内容</label>
            <textarea v-model="reviewForm.comment" placeholder="写下你的服务评价..." class="modal-textarea"></textarea>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showReviewModal = false">取消</button>
            <button class="btn-blue" @click="submitReview">提交评价</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="showReviewDetailModal" class="modal-overlay" @click.self="showReviewDetailModal = false">
        <div class="modal-content glass-card mini-modal review-modal">
          <h3 class="modal-title">查看评价</h3>
          <p class="modal-subtitle">{{ reviewDetail.taskTitle }}</p>
          <p class="modal-subtitle">评价人：{{ reviewDetail.reviewer || '-' }} · 时间：{{ reviewDetail.created_at || '-' }}</p>
          <div class="form-item">
            <label>星级评分</label>
            <div class="star-rating readonly">
              <span
                v-for="star in 5"
                :key="`detail-${star}`"
                :class="['star-btn', 'readonly-star', { active: star <= (reviewDetail.rating || 0) }]"
              >
                ★
              </span>
              <span class="rating-text">{{ reviewDetail.rating || 0 }} 分</span>
            </div>
          </div>
          <div class="form-item">
            <label>服务标签</label>
            <div class="review-tags">
              <span
                v-for="tag in reviewDetail.tags"
                :key="`tag-${tag}`"
                class="tag-btn active readonly-tag"
              >
                {{ tag }}
              </span>
              <span v-if="!reviewDetail.tags || reviewDetail.tags.length === 0" class="modal-subtitle">未选择标签</span>
            </div>
          </div>
          <div class="form-item">
            <label>评价内容</label>
            <textarea :value="reviewDetail.comment || '暂无评价内容'" class="modal-textarea" readonly></textarea>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="showReviewDetailModal = false">关闭</button>
          </div>
        </div>
      </div>
    </Transition>

    <DetailModal
      :visible="showDetailModal && !!currentTask"
      title="📋 任务详情"
      :rows="detailRows"
      @close="closeDetail"
    />

    <Transition name="fade">
      <div v-if="showChatModal" class="modal-overlay" @click.self="closeChatModal">
        <div class="modal-content glass-card chat-modal">
          <div class="chat-header">
            <h3>💬 任务沟通</h3>
            <button class="detail-close" @click="closeChatModal">×</button>
          </div>
          <p class="chat-task-title">{{ chatTask?.title || '' }}</p>
          <div ref="chatListRef" class="chat-list">
            <div v-if="chatMessages.length === 0" class="chat-empty">暂无聊天记录，发一条消息开始沟通吧。</div>
            <div
              v-for="msg in chatMessages"
              :key="msg.id"
              :class="['chat-item', msg.sender === userStore.username ? 'self' : '']"
            >
              <div class="chat-meta">
                <span class="chat-sender">{{ msg.sender }}</span>
                <span class="chat-time">{{ msg.created_at }}</span>
              </div>
              <div class="chat-content">{{ msg.content }}</div>
            </div>
          </div>
          <div class="chat-input-row">
            <input
              v-model="chatInput"
              class="chat-input"
              maxlength="500"
              placeholder="输入消息，按 Enter 发送"
              @keyup.enter="sendChatMessage"
            />
            <button class="btn-blue" @click="sendChatMessage">发送</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useUserStore } from '@/store/user'
import axios from 'axios'
import DetailModal from '@/components/DetailModal.vue'

const userStore = useUserStore()
const activeTab = ref('posted')
const statusFilter = ref('all')
const miniSearch = ref('')
const postedTasks = ref([])
const acceptedTasks = ref([])
const showSubmitModal = ref(false)
const showAbandonModal = ref(false)
const showEditModal = ref(false)
const showDetailModal = ref(false)
const showChatModal = ref(false)
const showQuoteManageModal = ref(false)
const showReviewModal = ref(false)
const showReviewDetailModal = ref(false)
const currentTask = ref(null)
const submitForm = ref({ taskId: null, desc: '' })
const abandonForm = ref({ taskId: null, reason: '' })
const editForm = ref({
  task_id: null,
  title: '',
  category: 'other',
  reward_points: 1,
  content: '',
  community_zone: '',
  latitude: null,
  longitude: null
})
const chatTask = ref(null)
const chatMessages = ref([])
const chatInput = ref('')
const chatListRef = ref(null)
const lastChatId = ref(0)
let chatTimer = null
const quoteManageTask = ref(null)
const quoteList = ref([])
const reviewForm = ref({
  task_id: null,
  taskTitle: '',
  rating: 5,
  tags: [],
  comment: ''
})
const reviewDetail = ref({
  taskTitle: '',
  rating: 0,
  tags: [],
  comment: '',
  reviewer: '',
  created_at: ''
})
const reviewTagOptions = ['准时', '沟通顺畅', '专业', '态度好', '效率高', '细致认真', '价格合理', '值得推荐']

const userRole = computed(() => userStore.role === 'user' ? 'resident' : userStore.role)
const canViewAcceptedTab = computed(() => {
  if (userStore.role === 'admin') return true
  return userStore.isExpert || userStore.isProvider
})
const detailRows = computed(() => {
  if (!currentTask.value) return []

  return [
    { label: '任务标题', value: currentTask.value.title },
    { label: '任务分类', value: formatCategory(currentTask.value.category) },
    {
      label: '任务状态',
      value: formatStatus(currentTask.value.status),
      badge: true,
      badgeType: currentTask.value.status || 'default'
    },
    { label: '悬赏积分', value: currentTask.value.reward_points ?? 0 },
    { label: '任务位置', value: currentTask.value.community_zone || '未填写' },
    { label: '发布时间', value: currentTask.value.created_at },
    { label: '发布人', value: currentTask.value.creator },
    { label: '接单人', value: currentTask.value.worker, visible: userRole.value !== 'resident' },
    {
      label: '任务描述',
      value: currentTask.value.description || currentTask.value.content || '暂无描述',
      multiline: true,
      visible: userRole.value !== 'resident'
    },
    {
      label: '放弃原因',
      value: currentTask.value.abandon_reason,
      multiline: true,
      visible: userRole.value === 'admin'
    },
    {
      label: '成果描述',
      value: currentTask.value.submit_desc || currentTask.value.result_desc,
      multiline: true,
      visible: userRole.value === 'admin'
    },
    {
      label: '终止申请',
      value: currentTask.value.terminate_reason,
      multiline: true,
      visible: !!currentTask.value.terminate_reason
    },
    {
      label: '终止发起人',
      value: currentTask.value.terminate_requested_by,
      visible: !!currentTask.value.terminate_requested_by
    },
    {
      label: '终止审核说明',
      value: currentTask.value.terminate_reject_reason,
      multiline: true,
      visible: !!currentTask.value.terminate_reject_reason
    }
  ]
})

const openDetail = (task) => {
  currentTask.value = task
  showDetailModal.value = true
}

const closeDetail = () => {
  showDetailModal.value = false
  currentTask.value = null
}

const canEditTask = (task) => {
  return ['auditing', 'pending', 'rejected'].includes(task.status)
}
const canDeleteTask = (task) => {
  return ['auditing', 'pending', 'rejected', 'terminated'].includes(task.status)
}
const canRequestTerminate = (task) => {
  return task.status === 'accepted'
}
const canRespondTerminate = (task) => {
  if (task.status !== 'terminating_pending_peer') return false
  const me = userStore.username
  if (!me) return false
  const isParticipant = [task.creator, task.worker].filter(Boolean).includes(me)
  if (!isParticipant) return false
  // 正常情况：发起人不能自己同意/拒绝
  if (task.terminate_requested_by) return task.terminate_requested_by !== me
  // 兜底：若后端历史数据未写入发起人，仍允许继续推进流程，避免卡死
  return true
}

const fetchMyTasks = async () => {
  try {
    const res = await axios.get(`http://127.0.0.1:8000/api/my_tasks/?username=${userStore.username}`)
    postedTasks.value = res.data.posted || []
    acceptedTasks.value = res.data.accepted || []
  } catch (error) {
    console.error('获取我的任务失败:', error)
    postedTasks.value = []
    acceptedTasks.value = []
  }
}

const filteredDisplayTasks = computed(() => {
  const currentTab = canViewAcceptedTab.value ? activeTab.value : 'posted'
  let list = currentTab === 'posted' ? postedTasks.value : acceptedTasks.value
  if (statusFilter.value !== 'all') list = list.filter(t => t.status === statusFilter.value)
  if (miniSearch.value) list = list.filter(t => t.title.toLowerCase().includes(miniSearch.value.toLowerCase()))
  return list
})

watch(canViewAcceptedTab, (canView) => {
  if (!canView && activeTab.value === 'accepted') {
    activeTab.value = 'posted'
  }
}, { immediate: true })

const openSubmitModal = (task) => { submitForm.value = { taskId: task.id, desc: '' }; showSubmitModal.value = true; }
const confirmSubmit = async () => {
  if (!submitForm.value.desc) return alert('请填写描述')
  try {
    await axios.post('http://127.0.0.1:8000/api/submit_task/', submitForm.value)
    showSubmitModal.value = false
    fetchMyTasks()
  } catch (error) {
    console.error('提交成果失败:', error)
    alert('提交成果失败，请稍后重试')
  }
}

const openAbandonModal = (task) => { abandonForm.value = { taskId: task.id, reason: '' }; showAbandonModal.value = true; }
const confirmAbandon = async () => {
  if (!abandonForm.value.reason) return alert('请填写原因')
  try {
    await axios.post('http://127.0.0.1:8000/api/abandon_task/', abandonForm.value)
    showAbandonModal.value = false
    fetchMyTasks()
  } catch (error) {
    console.error('放弃任务失败:', error)
    alert('放弃任务失败，请稍后重试')
  }
}

const openEditModal = (task) => {
  editForm.value = {
    task_id: task.id,
    title: task.title || '',
    category: task.category || 'other',
    reward_points: Number(task.reward_points || 1),
    content: task.content || '',
    community_zone: task.community_zone || '',
    latitude: task.latitude ?? null,
    longitude: task.longitude ?? null
  }
  showEditModal.value = true
}

const handleGetEditLocation = () => {
  if (!navigator.geolocation) {
    alert('当前浏览器不支持定位')
    return
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      editForm.value.latitude = Number(pos.coords.latitude.toFixed(6))
      editForm.value.longitude = Number(pos.coords.longitude.toFixed(6))
    },
    () => {
      alert('定位失败，请检查浏览器定位权限')
    },
    { enableHighAccuracy: false, timeout: 8000, maximumAge: 300000 }
  )
}

const clearEditLocation = () => {
  editForm.value.community_zone = ''
  editForm.value.latitude = null
  editForm.value.longitude = null
}

const confirmEditTask = async () => {
  if (!editForm.value.title.trim() || !editForm.value.content.trim()) {
    alert('请填写任务标题和描述')
    return
  }
  if (!Number.isInteger(editForm.value.reward_points) || editForm.value.reward_points <= 0) {
    alert('悬赏积分必须是大于 0 的整数')
    return
  }

  try {
    const res = await axios.post('http://127.0.0.1:8000/api/update_task/', {
      username: userStore.username,
      ...editForm.value
    })
    if (res.data.code !== 200) {
      alert(res.data.message || '修改失败')
      return
    }
    showEditModal.value = false
    fetchMyTasks()
  } catch (error) {
    alert(error.response?.data?.message || '修改失败，请稍后重试')
  }
}

const handleDeleteTask = async (task) => {
  if (!confirm(`确认删除任务「${task.title}」吗？该操作不可恢复。`)) return
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/delete_task/', {
      username: userStore.username,
      task_id: task.id
    })
    if (res.data.code !== 200) {
      alert(res.data.message || '删除失败')
      return
    }
    fetchMyTasks()
  } catch (error) {
    alert(error.response?.data?.message || '删除失败，请稍后重试')
  }
}

const handleRequestTerminate = async (task) => {
  const reason = prompt('请输入终止原因（会提交给对方和管理员）')
  if (reason === null) return
  if (!reason.trim()) {
    alert('终止原因不能为空')
    return
  }
  if (!confirm('确认发起终止任务申请吗？')) return
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/request_terminate_task/', {
      username: userStore.username,
      task_id: task.id,
      reason: reason.trim()
    })
    if (res.data.code !== 200) {
      alert(res.data.message || '发起终止失败')
      return
    }
    fetchMyTasks()
  } catch (error) {
    alert(error.response?.data?.message || '发起终止失败，请稍后重试')
  }
}

const handleRespondTerminate = async (task, agree) => {
  if (!confirm(agree ? '确认同意终止该任务吗？' : '确认拒绝终止该任务吗？')) return
  let reason = ''
  if (!agree) {
    reason = prompt('请输入拒绝终止原因（可选）') || ''
  }
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/respond_terminate_task/', {
      username: userStore.username,
      task_id: task.id,
      agree,
      reason
    })
    if (res.data.code !== 200) {
      alert(res.data.message || '操作失败')
      return
    }
    fetchMyTasks()
  } catch (error) {
    alert(error.response?.data?.message || '操作失败，请稍后重试')
  }
}

const handleConfirmFinish = async (task) => {
  const raw = prompt(`请输入结算给接单者的积分（0-${task.reward_points}）`, String(task.reward_points))
  if (raw === null) return
  const workerPoints = Number(raw)
  if (!Number.isInteger(workerPoints) || workerPoints < 0 || workerPoints > Number(task.reward_points || 0)) {
    alert('请输入合法积分')
    return
  }
  const refundPoints = Number(task.reward_points || 0) - workerPoints
  if (!confirm(`确认结项？接单者获得 ${workerPoints} 积分，发单者退回 ${refundPoints} 积分。`)) return
  try {
    await axios.post('http://127.0.0.1:8000/api/finish_task_with_settlement/', {
      task_id: task.id,
      username: userStore.username,
      worker_points: workerPoints
    })
    fetchMyTasks()
  } catch (error) {
    console.error('确认结项失败:', error)
    alert('确认结项失败，请稍后重试')
  }
}
const openQuoteManage = async (task) => {
  quoteManageTask.value = task
  showQuoteManageModal.value = true
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/task_quote/list/', {
      params: { username: userStore.username, task_id: task.id }
    })
    quoteList.value = res.data.quotes || []
  } catch (error) {
    quoteList.value = []
    alert(error.response?.data?.message || '获取报价失败')
  }
}
const chooseQuote = async (quote) => {
  if (!quoteManageTask.value) return
  if (!confirm(`确认选择 ${quote.quoter} 的报价（${quote.amount_points} 积分）吗？`)) return
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/task_quote/choose/', {
      username: userStore.username,
      task_id: quoteManageTask.value.id,
      quote_id: quote.id
    })
    if (res.data.code !== 200) {
      alert(res.data.message || '选择报价失败')
      return
    }
    showQuoteManageModal.value = false
    fetchMyTasks()
  } catch (error) {
    alert(error.response?.data?.message || '选择报价失败')
  }
}
const openReviewModal = (task) => {
  reviewForm.value = {
    task_id: task.id,
    taskTitle: task.title,
    rating: 5,
    tags: [],
    comment: ''
  }
  showReviewModal.value = true
}
const toggleReviewTag = (tag) => {
  if (reviewForm.value.tags.includes(tag)) {
    reviewForm.value.tags = reviewForm.value.tags.filter((t) => t !== tag)
  } else {
    reviewForm.value.tags = [...reviewForm.value.tags, tag]
  }
}
const submitReview = async () => {
  if (!reviewForm.value.task_id) return
  if (!Number.isInteger(reviewForm.value.rating) || reviewForm.value.rating < 1 || reviewForm.value.rating > 5) {
    alert('评分必须是 1-5 的整数')
    return
  }
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/task_review/create/', {
      username: userStore.username,
      task_id: reviewForm.value.task_id,
      rating: reviewForm.value.rating,
      comment: reviewForm.value.comment,
      tags: reviewForm.value.tags
    })
    if (res.data.code !== 200) {
      alert(res.data.message || '评价失败')
      return
    }
    showReviewModal.value = false
    fetchMyTasks()
  } catch (error) {
    alert(error.response?.data?.message || '评价失败')
  }
}
const parseReviewTags = (tags) => {
  if (Array.isArray(tags)) return tags
  if (typeof tags === 'string') {
    return tags.split(',').map((t) => t.trim()).filter(Boolean)
  }
  return []
}
const openReviewDetailModal = (task) => {
  const review = task.review || {}
  reviewDetail.value = {
    taskTitle: task.title,
    rating: Number(review.rating || 0),
    tags: parseReviewTags(review.tags),
    comment: review.comment || '',
    reviewer: review.reviewer || '',
    created_at: review.created_at || ''
  }
  showReviewDetailModal.value = true
}
const canOpenChat = (task) => {
  return !!task.worker && ['accepted', 'submitted', 'intervention'].includes(task.status)
}
const scrollChatBottom = async () => {
  await nextTick()
  if (chatListRef.value) {
    chatListRef.value.scrollTop = chatListRef.value.scrollHeight
  }
}
const fetchTaskChatMessages = async ({ append = false } = {}) => {
  if (!chatTask.value?.id) return
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/chat/messages/', {
      params: {
        task_id: chatTask.value.id,
        username: userStore.username,
        after_id: append ? lastChatId.value : 0,
        limit: 100
      }
    })
    const incoming = res.data.messages || []
    if (!append) {
      chatMessages.value = incoming
    } else if (incoming.length > 0) {
      chatMessages.value = [...chatMessages.value, ...incoming]
    }
    if (chatMessages.value.length > 0) {
      lastChatId.value = chatMessages.value[chatMessages.value.length - 1].id
    }
    scrollChatBottom()
  } catch (error) {
    console.error('拉取任务聊天失败:', error)
  }
}
const startChatPolling = () => {
  stopChatPolling()
  chatTimer = setInterval(() => {
    fetchTaskChatMessages({ append: true })
  }, 2000)
}
const stopChatPolling = () => {
  if (chatTimer) {
    clearInterval(chatTimer)
    chatTimer = null
  }
}
const openChatModal = async (task) => {
  if (!canOpenChat(task)) {
    alert('任务已完成，聊天已关闭')
    return
  }
  chatTask.value = task
  chatMessages.value = []
  lastChatId.value = 0
  showChatModal.value = true
  await fetchTaskChatMessages({ append: false })
  startChatPolling()
}
const closeChatModal = () => {
  showChatModal.value = false
  stopChatPolling()
  chatTask.value = null
  chatMessages.value = []
  chatInput.value = ''
  lastChatId.value = 0
}
const sendChatMessage = async () => {
  if (!chatTask.value?.id || !chatInput.value.trim()) return
  if (!canOpenChat(chatTask.value)) {
    alert('任务已完成，无法继续发送消息')
    closeChatModal()
    return
  }
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/chat/send/', {
      task_id: chatTask.value.id,
      username: userStore.username,
      content: chatInput.value
    })
    if (res.data.code === 200) {
      chatInput.value = ''
      fetchTaskChatMessages({ append: true })
    } else {
      alert(res.data.message || '发送失败')
    }
  } catch (error) {
    alert(error.response?.data?.message || '发送失败，请稍后重试')
  }
}

const formatCategory = (cat) => {
  const map = { errand: '跑腿', repair: '维修', pet: '宠物', other: '其他' }
  return map[cat] || '互助'
}

const formatStatus = (s) => {
  const map = {
    auditing: '审核中',
    rejected: '被驳回',
    pending: '招募中',
    accepted: '进行中',
    submitted: '待确认',
    intervention: '仲裁中',
    terminating_pending_peer: '待对方确认终止',
    terminating_admin_review: '待管理员终止审核',
    terminated: '已终止',
    finished: '已完成'
  }
  return map[s] || s
}

onMounted(() => fetchMyTasks())
onUnmounted(() => stopChatPolling())
</script>

<style scoped>
.my-tasks-container { margin-left: 260px; padding: 40px; background: #f0f4f8; min-height: 100vh; }
.glass-card { background: white; border-radius: 20px; box-shadow: 0 8px 30px rgba(0,0,0,0.05); }

.page-header { display: flex; justify-content: space-between; align-items: center; padding: 25px 40px; margin-bottom: 20px; }
.tab-group { background: #edf2f7; padding: 5px; border-radius: 12px; display: flex; }
.tab-btn { padding: 10px 25px; border: none; background: none; border-radius: 8px; cursor: pointer; color: #718096; font-weight: 600; }
.tab-btn.active { background: white; color: #4299e1; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }

.filter-bar { display: flex; justify-content: space-between; padding: 15px 40px; margin-bottom: 30px; align-items: center; }
.filter-item select { padding: 8px 15px; border-radius: 10px; border: 1px solid #e2e8f0; outline: none; }
.search-mini input { padding: 8px 15px; border-radius: 20px; border: 1px solid #e2e8f0; width: 220px; }

.task-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 25px; }
.task-card { padding: 25px; display: flex; flex-direction: column; justify-content: space-between; }
.card-top { display: flex; justify-content: space-between; margin-bottom: 15px; }
.category-badge { padding: 4px 10px; border-radius: 6px; font-size: 12px; background: #ebf8ff; color: #3182ce; font-weight: 700; }
/* 🚀 状态标签颜色大幅优化：加深底色，提高对比度 */
.status-tag {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 20px;
  text-transform: uppercase;
}
/* 审核中：使用浅黄色底，深琥珀色字  */
.status-tag.auditing {
  background: #fef9c3 !important;
  color: #a16207 !important;
}
.status-tag.rejected {
  background: #fee2e2 !important;
  color: #991b1b !important;
}
/* 招募中：浅蓝 */
.status-tag.pending {
  background: #e0f2fe !important;
  color: #0369a1 !important;
}
/* 进行中：深蓝 */
.status-tag.accepted {
  background: #dbeafe !important;
  color: #1d4ed8 !important;
}
/* 待确认：紫 */
.status-tag.submitted {
  background: #ede9fe !important;
  color: #5b21b6 !important;
  border: 1px solid #ddd6fe;
}
.status-tag.intervention,
.status-tag.terminating_pending_peer {
  background: #fff7ed !important;
  color: #c2410c !important;
}
.status-tag.terminating_admin_review {
  background: #fef3c7 !important;
  color: #92400e !important;
}
.status-tag.terminated {
  background: #f1f5f9 !important;
  color: #475569 !important;
}

/* 已完成：与弹窗统一为绿色体系 */
.status-tag.finished {
  background: #d1fae5 !important;
  color: #065f46 !important;
}

.card-title { font-size: 19px; color: #2d3748; margin-bottom: 12px; }
.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.points-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px 10px;
  border-radius: 999px;
  background: #fff7ed;
  color: #c2410c;
  font-size: 12px;
  font-weight: 700;
}
.title-row .card-title { margin-bottom: 0; }
.task-meta { font-size: 14px; color: #718096; margin-bottom: 15px; line-height: 1.8; }

.card-footer { border-top: 1px solid #f1f5f9; padding-top: 15px; }
.action-group { display: flex; gap: 10px; justify-content: flex-end; }
.btn-blue { background: #4299e1; color: white; border: none; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-weight: 600; }
.btn-success { background: #10b981; color: white; border: none; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-weight: 600; }
.btn-chat { background: #eef2ff; color: #4338ca; border: 1px solid #c7d2fe; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-weight: 600; }
.btn-abandon { background: #fff5f5; color: #e53e3e; border: 1px solid #feb2b2; padding: 8px 18px; border-radius: 8px; cursor: pointer; }
.btn-warn { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-weight: 600; }
.btn-ghost { background: #f8fafc; color: #475569; border: 1px solid #cbd5e1; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-weight: 600; }
.btn-danger-lite { background: #fff1f2; color: #be123c; border: 1px solid #fecdd3; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-weight: 600; }
.btn-detail { background: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; padding: 8px 18px; border-radius: 8px; cursor: pointer; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 9999; padding: 16px; }
.mini-modal { width: 450px; padding: 35px; max-height: 90vh; overflow-y: auto; }
.task-modal {
  width: 520px;
  padding: 40px;
  position: relative;
  max-height: 90vh;
  overflow-y: auto;
}
.chat-modal { width: 640px; max-width: 94vw; padding: 24px; max-height: 90vh; overflow: hidden; display: flex; flex-direction: column; }
.chat-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.chat-header h3 { margin: 0; color: #2d3748; }
.detail-close { background: transparent; border: none; font-size: 26px; color: #718096; cursor: pointer; line-height: 1; }
.close-x { position: absolute; right: 25px; top: 25px; font-size: 24px; border: none; background: none; color: #cbd5e0; cursor: pointer; }
.chat-task-title { margin: 0 0 10px; color: #64748b; font-size: 14px; }
.chat-list { max-height: 320px; overflow-y: auto; border: 1px solid #e2e8f0; background: #f8fafc; border-radius: 12px; padding: 12px; }
.chat-empty { text-align: center; color: #94a3b8; padding: 24px 10px; }
.chat-item { margin-bottom: 10px; border: 1px solid #e2e8f0; border-radius: 10px; background: white; padding: 8px 10px; }
.chat-item.self { border-color: #bfdbfe; background: #eff6ff; }
.chat-meta { display: flex; justify-content: space-between; gap: 8px; margin-bottom: 4px; }
.chat-sender { font-size: 12px; font-weight: 700; color: #1e40af; }
.chat-time { font-size: 11px; color: #94a3b8; }
.chat-content { white-space: pre-wrap; line-height: 1.6; color: #334155; font-size: 14px; }
.chat-input-row { margin-top: 10px; display: flex; gap: 10px; }
.chat-input { flex: 1; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px; outline: none; }
.chat-input:focus { border-color: #4299e1; box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.12); }
.post-form .form-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 22px;
}
.post-form .form-item label {
  font-weight: 700;
  color: #4a5568;
  font-size: 14px;
  padding-left: 4px;
}
.post-form .form-item input,
.post-form .form-item select,
.post-form .form-item textarea {
  padding: 13px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  font-size: 14px;
  outline: none;
}
.post-form .form-item input:focus,
.post-form .form-item textarea:focus,
.post-form .form-item select:focus {
  border-color: #4299e1;
  background: white;
}
.post-form .form-item textarea {
  height: 130px;
  resize: none;
}
.form-tip { color: #718096; font-size: 12px; line-height: 1.5; }
.location-manual-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.location-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.btn-location,
.btn-location-clear {
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  background: white;
  color: #334155;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}
.btn-location-clear {
  border-color: #fecaca;
  color: #b91c1c;
  background: #fff1f2;
}
.btn-submit-task {
  width: 100%;
  padding: 15px;
  background: #4299e1;
  color: white;
  border: none;
  border-radius: 14px;
  font-weight: 700;
  font-size: 16px;
  cursor: pointer;
  margin-top: 10px;
  box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
}
.modal-textarea { width: 100%; height: 120px; padding: 12px; border-radius: 12px; border: 1px solid #e2e8f0; resize: none; outline: none; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; }
.btn-cancel { background: #edf2f7; color: #4a5568; border: none; padding: 10px 25px; border-radius: 10px; cursor: pointer; }
.btn-danger { background: #e53e3e; color: white; border: none; padding: 10px 25px; border-radius: 10px; cursor: pointer; }
.modal-subtitle { margin: -6px 0 10px; color: #64748b; font-size: 13px; }
.review-modal .form-item {
  margin-bottom: 18px;
  gap: 12px;
}
.review-modal label {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}
.review-modal .modal-textarea {
  min-height: 130px;
  line-height: 1.75;
}
.star-rating {
  display: flex;
  align-items: center;
  gap: 8px;
}
.star-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 30px;
  line-height: 1;
  color: #cbd5e1;
  padding: 0;
}
.star-rating.readonly .readonly-star {
  cursor: default;
}
.readonly-tag {
  cursor: default;
}
.star-btn.active {
  color: #f59e0b;
  text-shadow: 0 2px 4px rgba(245, 158, 11, 0.25);
}
.rating-text {
  margin-left: 4px;
  color: #475569;
  font-size: 14px;
  font-weight: 600;
}
.review-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.tag-btn {
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #334155;
  border-radius: 999px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.tag-btn.active {
  border-color: #60a5fa;
  background: #dbeafe;
  color: #1d4ed8;
  font-weight: 700;
}
.quote-list { display: flex; flex-direction: column; gap: 10px; max-height: 360px; overflow-y: auto; }
.quote-item {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.quote-main { min-width: 0; }
.quote-title { font-weight: 700; color: #1e293b; }
.quote-message { color: #475569; font-size: 13px; margin-top: 4px; }
.quote-meta { color: #94a3b8; font-size: 12px; margin-top: 4px; }

.empty-state { text-align: center; padding: 100px; color: #cbd5e0; }
.fade-enter-active, .fade-leave-active { transition: 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.95); }
</style>
