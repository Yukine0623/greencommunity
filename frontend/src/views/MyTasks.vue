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
          <option value="pending">招募中</option>
          <option value="accepted">进行中</option>
          <option value="submitted">待确认</option>
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
          </div>
        </div>

        <div class="card-footer">
          <div class="action-group">
            <button v-if="activeTab === 'posted' && task.status === 'submitted'" class="btn-blue" @click="handleConfirmFinish(task.id)">确认结项</button>
            
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
const showDetailModal = ref(false)
const showChatModal = ref(false)
const currentTask = ref(null)
const submitForm = ref({ taskId: null, desc: '' })
const abandonForm = ref({ taskId: null, reason: '' })
const chatTask = ref(null)
const chatMessages = ref([])
const chatInput = ref('')
const chatListRef = ref(null)
const lastChatId = ref(0)
let chatTimer = null

const userRole = computed(() => userStore.role === 'user' ? 'resident' : userStore.role)
const canViewAcceptedTab = computed(() => userRole.value !== 'resident')
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

const handleConfirmFinish = async (id) => {
  if (!confirm('确认该任务已完成？')) return
  try {
    await axios.post('http://127.0.0.1:8000/api/finish_task/', {
      task_id: id,
      username: userStore.username
    })
    fetchMyTasks()
  } catch (error) {
    console.error('确认结项失败:', error)
    alert('确认结项失败，请稍后重试')
  }
}
const canOpenChat = (task) => {
  return !!task.worker && ['accepted', 'submitted', 'finished', 'intervention'].includes(task.status)
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
  const map = { auditing: '审核中', pending: '招募中', accepted: '进行中', submitted: '待确认', finished: '已完成' }
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
  background: #fffbeb !important; /* 浅黄色背景 */
  color: #b45309 !important;      /* 深琥珀色文字 */
}
/* 招募中：与弹窗统一为黄色体系 */
.status-tag.pending {
  background: #fffbeb !important;
  color: #b45309 !important;
}
/* 进行中：使用浅蓝色底，深蓝色字 (符合主题) */
.status-tag.accepted {
  background: #e0f2fe !important;
  color: #0369a1 !important;
}
/* 待确认/已提交：与弹窗统一为靛蓝体系 */
.status-tag.submitted {
  background: #eef2ff !important;
  color: #4338ca !important;
  border: 1px solid #c7d2fe;
}

/* 已完成：与弹窗统一为绿色体系 */
.status-tag.finished {
  background: #f0fdf4 !important;
  color: #15803d !important;
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
.btn-chat { background: #eef2ff; color: #4338ca; border: 1px solid #c7d2fe; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-weight: 600; }
.btn-abandon { background: #fff5f5; color: #e53e3e; border: 1px solid #feb2b2; padding: 8px 18px; border-radius: 8px; cursor: pointer; }
.btn-detail { background: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; padding: 8px 18px; border-radius: 8px; cursor: pointer; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 9999; }
.mini-modal { width: 450px; padding: 35px; }
.chat-modal { width: 640px; max-width: 94vw; padding: 24px; }
.chat-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.chat-header h3 { margin: 0; color: #2d3748; }
.detail-close { background: transparent; border: none; font-size: 26px; color: #718096; cursor: pointer; line-height: 1; }
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
.modal-textarea { width: 100%; height: 120px; padding: 12px; border-radius: 12px; border: 1px solid #e2e8f0; resize: none; outline: none; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; }
.btn-cancel { background: #edf2f7; color: #4a5568; border: none; padding: 10px 25px; border-radius: 10px; cursor: pointer; }
.btn-danger { background: #e53e3e; color: white; border: none; padding: 10px 25px; border-radius: 10px; cursor: pointer; }

.empty-state { text-align: center; padding: 100px; color: #cbd5e0; }
.fade-enter-active, .fade-leave-active { transition: 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.95); }
</style>
