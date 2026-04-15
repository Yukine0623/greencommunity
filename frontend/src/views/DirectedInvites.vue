<template>
  <div class="task-market-container">
    <template v-if="userStore.isProvider">
      <header class="market-header glass-card">
        <h1>定向邀约</h1>
        <p class="subtitle">仅展示定向邀请给你的认证服务任务</p>
        <div class="header-controls">
          <select v-model="selectedCategory" class="category-filter" @change="fetchTasks">
            <option value="all">全部类型</option>
            <option value="errand">跑腿代购</option>
            <option value="repair">家电维修</option>
            <option value="pet">宠物照顾</option>
            <option value="other">其他互助</option>
          </select>
          <select v-model="sortType" class="category-filter">
            <option value="created_desc">按发布时间（新到旧）</option>
            <option value="reward_desc">按积分（高到低）</option>
            <option value="distance_asc">按距离（近到远）</option>
          </select>
          <div class="search-bar">
            <span class="search-icon">🔍</span>
            <input v-model="searchQuery" placeholder="搜索任务标题..." />
          </div>
        </div>
      </header>

      <main class="task-grid" v-if="filteredTasks.length > 0">
        <div v-for="task in filteredTasks" :key="task.id" class="task-card glass-card">
          <div class="card-body">
            <div class="card-top">
              <span :class="['category-badge', task.category]">
                {{ formatCategory(task.category) }}
              </span>
              <span class="time-text">{{ task.created_at }}</span>
            </div>
            <div class="title-row">
              <span class="points-badge">🪙 {{ task.reward_points || 0 }}</span>
              <h3 class="card-title">{{ task.title }}</h3>
            </div>
            <p class="card-desc">{{ task.content }}</p>
            <p class="distance-line">🎯 {{ formatAssigneeType(task.assignee_type) }} · 定向邀约 {{ task.invited_provider }}</p>
            <p class="distance-line">
              <span v-if="task.distance_km !== null && task.distance_km !== undefined">📍 距你 {{ task.distance_km }} km</span>
              <span v-else>📍 距离未知</span>
              <span v-if="task.community_zone"> · {{ task.community_zone }}</span>
            </p>
          </div>

          <div class="card-footer">
            <div class="action-group">
              <button class="btn-accept" :disabled="!canAcceptTask(task)" @click="handleAccept(task.id)">
                {{ canAcceptTask(task) ? '接受任务' : '当前不可接单' }}
              </button>
              <button class="btn-quote" @click="openQuoteModal(task)">我要报价</button>
              <button class="btn-detail" @click="openDetail(task)">查看详情</button>
            </div>
          </div>
        </div>
      </main>

      <div v-else class="empty-state">
        <div class="empty-icon">📭</div>
        <p>当前没有定向邀请给你的任务</p>
      </div>
    </template>

    <div v-else class="empty-state glass-card no-auth">
      <div class="empty-icon">🔒</div>
      <p>该页面仅对认证服务者开放</p>
    </div>

    <DetailModal
      :visible="showDetailModal"
      :title="currentTask.title || '任务详情'"
      :rows="detailRows"
      @close="showDetailModal = false"
    />

    <Transition name="fade">
      <div v-if="showQuoteModal" class="modal-overlay" @click.self="showQuoteModal = false">
        <div class="modal-content glass-card mini-modal">
          <h3 class="modal-title">提交报价</h3>
          <p class="quote-task-title">{{ quoteForm.taskTitle }}</p>
          <div class="form-item">
            <label>报价积分</label>
            <input v-model.number="quoteForm.amount_points" type="number" min="0" step="1" placeholder="请输入报价积分" />
          </div>
          <div class="form-item">
            <label>报价说明</label>
            <textarea v-model="quoteForm.message" maxlength="255" placeholder="请输入你的服务说明（可选）"></textarea>
          </div>
          <div class="modal-footer">
            <button class="btn-detail" @click="showQuoteModal = false">取消</button>
            <button class="btn-accept" @click="submitQuote">提交报价</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/store/user'
import axios from 'axios'
import DetailModal from '@/components/DetailModal.vue'

const userStore = useUserStore()
const username = computed(() => userStore.username)

const tasks = ref([])
const showDetailModal = ref(false)
const showQuoteModal = ref(false)
const currentTask = ref({})
const searchQuery = ref('')
const selectedCategory = ref('all')
const sortType = ref('created_desc')
const userLocation = ref({ latitude: null, longitude: null })
const quoteForm = ref({
  task_id: null,
  taskTitle: '',
  amount_points: 0,
  message: ''
})

const getCurrentLocation = () => {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(false)
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        userLocation.value.latitude = Number(pos.coords.latitude.toFixed(6))
        userLocation.value.longitude = Number(pos.coords.longitude.toFixed(6))
        resolve(true)
      },
      () => resolve(false),
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 300000 }
    )
  })
}

const fetchTasks = async () => {
  if (!userStore.isProvider) return
  try {
    const params = {
      category: selectedCategory.value,
      username: username.value
    }
    if (userLocation.value.latitude && userLocation.value.longitude) {
      params.user_lat = userLocation.value.latitude
      params.user_lng = userLocation.value.longitude
    }
    const res = await axios.get('http://127.0.0.1:8000/api/get_tasks/', { params })
    tasks.value = res.data.tasks || []
  } catch (err) {
    console.error('加载定向邀约失败', err)
  }
}

const directedTasks = computed(() => {
  return tasks.value.filter((task) => {
    return task.invited_provider === username.value && task.creator !== username.value
  })
})

const filteredTasks = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  const list = directedTasks.value.filter((t) => (t.title || '').toLowerCase().includes(q))
  const sorted = [...list]

  if (sortType.value === 'reward_desc') {
    sorted.sort((a, b) => (b.reward_points || 0) - (a.reward_points || 0))
  } else if (sortType.value === 'distance_asc') {
    sorted.sort((a, b) => {
      const ad = a.distance_km
      const bd = b.distance_km
      if (ad == null && bd == null) return 0
      if (ad == null) return 1
      if (bd == null) return -1
      return ad - bd
    })
  } else {
    sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  }

  return sorted
})

const canAcceptTask = (task) => {
  if (!userStore.isProvider) return false
  if (task.invited_provider !== username.value) return false
  const assignee = task.assignee_type || 'any'
  if (assignee === 'expert') return false
  return true
}

const handleAccept = async (id) => {
  if (!confirm('确认要接受该任务吗？')) return
  try {
    await axios.post('http://127.0.0.1:8000/api/accept_task/', {
      task_id: id,
      username: username.value
    })
    alert('接单成功！')
    fetchTasks()
  } catch (err) {
    alert(err?.response?.data?.message || '接单失败')
  }
}

const openDetail = (task) => {
  currentTask.value = task
  showDetailModal.value = true
}
const openQuoteModal = (task) => {
  quoteForm.value = {
    task_id: task.id,
    taskTitle: task.title,
    amount_points: Number(task.reward_points || 0),
    message: ''
  }
  showQuoteModal.value = true
}
const submitQuote = async () => {
  if (!quoteForm.value.task_id) return
  if (!Number.isInteger(quoteForm.value.amount_points) || quoteForm.value.amount_points < 0) {
    alert('报价积分必须为大于等于 0 的整数')
    return
  }
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/task_quote/create/', {
      username: username.value,
      task_id: quoteForm.value.task_id,
      amount_points: quoteForm.value.amount_points,
      message: quoteForm.value.message
    })
    if (res.data.code !== 200) {
      alert(res.data.message || '报价失败')
      return
    }
    alert('报价成功')
    showQuoteModal.value = false
  } catch (error) {
    alert(error.response?.data?.message || '报价失败，请稍后重试')
  }
}

const detailRows = computed(() => {
  return [
    { label: '任务标题', value: currentTask.value.title },
    { label: '任务类型', value: formatCategory(currentTask.value.category) },
    { label: '发布人', value: currentTask.value.creator },
    { label: '悬赏积分', value: currentTask.value.reward_points ?? 0 },
    { label: '任务位置', value: currentTask.value.community_zone || '未填写' },
    { label: '接单对象', value: formatAssigneeType(currentTask.value.assignee_type) },
    { label: '定向邀约', value: currentTask.value.invited_provider || '无' },
    { label: '发布时间', value: currentTask.value.created_at },
    { label: '任务描述', value: currentTask.value.content, multiline: true }
  ]
})

const formatCategory = (cat) => {
  const map = { errand: '跑腿代购', repair: '家电维修', pet: '宠物照顾', other: '其他互助' }
  return map[cat] || '邻里互助'
}

const formatAssigneeType = (type) => {
  const map = { any: '不指定', expert: '仅邻里达人', provider: '仅认证服务者' }
  return map[type] || '不指定'
}

onMounted(async () => {
  await getCurrentLocation()
  fetchTasks()
})
</script>

<style scoped>
.task-market-container {
  margin-left: 260px;
  padding: 40px;
  min-height: 100vh;
  background-color: #f4f7f9;
}
.glass-card {
  background: white;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04);
}
.market-header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 14px;
  padding: 30px 45px;
  margin-bottom: 35px;
}
.market-header h1 { font-size: 32px; color: #111827; margin: 0; }
.subtitle { color: #6b7280; margin: 0; font-size: 16px; }
.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}
.search-bar {
  position: relative;
  width: 420px;
  flex: 0 0 420px;
}
.search-bar input {
  padding: 12px 20px 12px 45px;
  border-radius: 30px;
  border: 1px solid #e2e8f0;
  width: 100%;
  outline: none;
}
.search-icon { position: absolute; left: 18px; top: 12px; color: #a0aec0; }
.category-filter {
  border: 1px solid #e2e8f0;
  border-radius: 30px;
  padding: 11px 14px;
  background: white;
  color: #4a5568;
  outline: none;
}
.task-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 25px; }
.task-card { padding: 25px; transition: 0.3s; }
.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.category-badge { padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: 700; }
.category-badge.errand { background: #ebf8ff; color: #3182ce; }
.category-badge.repair { background: #edf2f7; color: #4a5568; }
.category-badge.pet { background: #fffaf0; color: #dd6b20; }
.category-badge.other { background: #f7fafc; color: #718096; }
.title-row { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
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
.card-title { font-size: 19px; color: #2d3748; margin: 0; }
.card-desc {
  color: #4a5568;
  font-size: 14px;
  line-height: 1.7;
  height: 72px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.distance-line { margin: 6px 0 0; color: #718096; font-size: 13px; }
.card-footer { border-top: 1px solid #f1f5f9; padding-top: 18px; margin-top: 10px; }
.action-group { display: flex; gap: 12px; justify-content: flex-end; }
.btn-accept { background: #4299e1; color: white; border: none; padding: 9px 22px; border-radius: 10px; cursor: pointer; font-weight: 600; }
.btn-accept:disabled { background: #94a3b8; cursor: not-allowed; }
.btn-quote { background: #edf2ff; color: #3730a3; border: 1px solid #c7d2fe; padding: 9px 18px; border-radius: 10px; cursor: pointer; font-weight: 600; }
.btn-detail { background: #f8fafc; border: 1px solid #e2e8f0; padding: 9px 22px; border-radius: 10px; color: #4a5568; cursor: pointer; }
.empty-state { text-align: center; padding: 100px; color: #64748b; font-size: 16px; }
.empty-icon { font-size: 28px; margin-bottom: 10px; }
.no-auth { margin-top: 40px; border: 1px dashed #cbd5e1; }
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(10, 25, 47, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2200;
  padding: 16px;
}
.modal-content {
  width: 520px;
  max-width: 100%;
  max-height: 88vh;
  overflow-y: auto;
  padding: 24px;
}
.mini-modal {
  width: 460px;
  max-height: 88vh;
  overflow-y: auto;
  padding: 28px;
}
.quote-task-title {
  margin: -8px 0 12px;
  color: #475569;
  font-size: 14px;
}
.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 14px;
}
.form-item input, .form-item textarea {
  border: 1px solid #dbe3eb;
  border-radius: 10px;
  padding: 10px;
}
.form-item textarea {
  min-height: 90px;
  resize: vertical;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.fade-enter-active, .fade-leave-active { transition: 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.95); }

@media (max-width: 1280px) {
  .header-controls { flex-wrap: wrap; }
  .search-bar { width: 100%; flex: 1 1 100%; margin-left: 0; }
}
@media (max-width: 1100px) {
  .task-grid { grid-template-columns: 1fr; }
}
</style>
