<template>
  <div class="my-tasks-container">
    <header class="page-header glass-card">
      <div class="header-left">
        <h1>任务管理</h1>
        <p class="subtitle">追踪互助进度</p>
      </div>
      <div class="tab-group">
        <button :class="['tab-btn', { active: activeTab === 'posted' }]" @click="activeTab = 'posted'">📤 我发布的</button>
        <button :class="['tab-btn', { active: activeTab === 'accepted' }]" @click="activeTab = 'accepted'">📥 我接手的</button>
      </div>
    </header>

    <div class="filter-bar glass-card">
      <div class="filter-item">
        <label>状态：</label>
        <select v-model="statusFilter">
          <option value="all">全部</option>
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
          <h3 class="card-title">{{ task.title }}</h3>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/store/user'
import axios from 'axios'

const userStore = useUserStore()
const activeTab = ref('posted')
const statusFilter = ref('all')
const miniSearch = ref('')
const postedTasks = ref([])
const acceptedTasks = ref([])
const showSubmitModal = ref(false)
const showAbandonModal = ref(false)
const submitForm = ref({ taskId: null, desc: '' })
const abandonForm = ref({ taskId: null, reason: '' })

const fetchMyTasks = async () => {
  const res = await axios.get(`http://127.0.0.1:8000/api/my_tasks/?username=${userStore.username}`)
  postedTasks.value = res.data.posted || []
  acceptedTasks.value = res.data.accepted || []
}

const filteredDisplayTasks = computed(() => {
  let list = activeTab.value === 'posted' ? postedTasks.value : acceptedTasks.value
  if (statusFilter.value !== 'all') list = list.filter(t => t.status === statusFilter.value)
  if (miniSearch.value) list = list.filter(t => t.title.toLowerCase().includes(miniSearch.value.toLowerCase()))
  return list
})

const openSubmitModal = (task) => { submitForm.value = { taskId: task.id, desc: '' }; showSubmitModal.value = true; }
const confirmSubmit = async () => {
  if (!submitForm.value.desc) return alert('请填写描述')
  await axios.post('http://127.0.0.1:8000/api/submit_task/', submitForm.value)
  showSubmitModal.value = false; fetchMyTasks()
}

const openAbandonModal = (task) => { abandonForm.value = { taskId: task.id, reason: '' }; showAbandonModal.value = true; }
const confirmAbandon = async () => {
  if (!abandonForm.value.reason) return alert('请填写原因')
  await axios.post('http://127.0.0.1:8000/api/abandon_task/', abandonForm.value)
  showAbandonModal.value = false; fetchMyTasks()
}

const handleConfirmFinish = async (id) => {
  if (confirm('确认该任务已完成？')) {
    await axios.post('http://127.0.0.1:8000/api/finish_task/', { task_id: id })
    fetchMyTasks()
  }
}

const formatCategory = (cat) => {
  const map = { errand: '跑腿', repair: '维修', pet: '宠物', other: '其他' }
  return map[cat] || '互助'
}

const formatStatus = (s) => {
  const map = { pending: '招募中', accepted: '进行中', submitted: '待确认', finished: '已完成' }
  return map[s] || s
}

onMounted(() => fetchMyTasks())
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
/* 招募中：使用浅红色底，深红色字 (醒目) */
.status-tag.pending {
  background: #fee2e2 !important; /* 明显的浅红 */
  color: #ef4444 !important;      /* 鲜艳的红 */
}
/* 进行中：使用浅蓝色底，深蓝色字 (符合主题) */
.status-tag.accepted {
  background: #e0f2fe !important; /* 明显的浅蓝 */
  color: #0284c7 !important;      /* 主题深蓝 */
}
/* 待确认/已提交：使用浅绿色底，深绿色字 (成功色) */
.status-tag.submitted {
  background: #dcfce7 !important; /* 明显的浅绿 */
  color: #16a34a !important;      /* 鲜绿 */
  border: 1px solid #bbf7d0;
}

/* 已完成：使用浅灰色底，深灰色字 (沉稳感) */
.status-tag.finished {
  background: #f1f5f9 !important; /* 灰蓝色底 */
  color: #475569 !important;      /* 深灰字 */
}

.card-title { font-size: 19px; color: #2d3748; margin-bottom: 12px; }
.task-meta { font-size: 14px; color: #718096; margin-bottom: 15px; line-height: 1.8; }

.card-footer { border-top: 1px solid #f1f5f9; padding-top: 15px; }
.action-group { display: flex; gap: 10px; justify-content: flex-end; }
.btn-blue { background: #4299e1; color: white; border: none; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-weight: 600; }
.btn-abandon { background: #fff5f5; color: #e53e3e; border: 1px solid #feb2b2; padding: 8px 18px; border-radius: 8px; cursor: pointer; }
.btn-detail { background: #f7fafc; color: #4a5568; border: 1px solid #e2e8f0; padding: 8px 18px; border-radius: 8px; }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 2000; }
.mini-modal { width: 450px; padding: 35px; }
.form-item { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.modal-textarea { width: 100%; height: 120px; padding: 12px; border-radius: 12px; border: 1px solid #e2e8f0; resize: none; outline: none; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; }
.btn-cancel { background: #edf2f7; color: #4a5568; border: none; padding: 10px 25px; border-radius: 10px; cursor: pointer; }
.btn-danger { background: #e53e3e; color: white; border: none; padding: 10px 25px; border-radius: 10px; cursor: pointer; }

.empty-state { text-align: center; padding: 100px; color: #cbd5e0; }
.fade-enter-active, .fade-leave-active { transition: 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.95); }
</style>