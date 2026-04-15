<template>
  <div class="task-market-container">
    <header class="market-header glass-card">
      <h1>任务市场</h1>
      <p class="subtitle">发现身边的邻里互助需求</p>
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
        <button class="btn-add-task-fab" @click="showModal = true" title="发布新任务">+</button>
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
          <p class="distance-line">
            <span v-if="task.distance_km !== null && task.distance_km !== undefined">📍 距你 {{ task.distance_km }} km</span>
            <span v-else>📍 距离未知</span>
            <span v-if="task.community_zone"> · {{ task.community_zone }}</span>
          </p>
        </div>

        <div class="card-footer">
          <div class="action-group">
            <template v-if="canAcceptTasks">
              <button class="btn-accept" @click="handleAccept(task.id)">接受任务</button>
            </template>
            <button class="btn-detail" @click="openDetail(task)">查看详情</button>
          </div>
        </div>
      </div>
    </main>

    <div v-else class="empty-state">
      <div class="empty-icon">🔍</div>
      <p>任务市场暂无匹配结果，或者正在加载中...</p>
      <button class="btn-post-first" @click="showModal = true">发布第一个任务</button>
    </div>

    <Transition name="fade">
      <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
        <div class="modal-content glass-card task-modal">
          <button class="close-x" @click="showModal = false">×</button>
          <h2 class="modal-title">🚀 发布新互助</h2>
          
          <div class="post-form">
            <div class="form-item">
              <label>任务标题</label>
              <input v-model="newTask.title" maxlength="20" placeholder="简述你的需求 (20字以内)" />
            </div>
            
            <div class="form-item">
              <label>任务类型</label>
              <select v-model="newTask.category">
                <option value="errand">跑腿代购</option>
                <option value="repair">家电维修</option>
                <option value="pet">宠物照顾</option>
                <option value="other">其他互助</option>
              </select>
            </div>
            
            <div class="form-item">
              <label>详情描述</label>
              <textarea v-model="newTask.content" maxlength="1000" placeholder="请详细说明时间、地点、具体要求等..."></textarea>
            </div>

            <div class="form-item">
              <label>悬赏积分</label>
              <input
                v-model.number="newTask.reward_points"
                type="number"
                min="1"
                step="1"
                placeholder="请输入悬赏积分"
              />
              <small class="form-tip">发布后会先冻结这部分积分，任务完成后发放给接单者。</small>
            </div>

            <div class="form-item">
              <label>任务位置（可选）</label>
              <input v-model="publishLocation.community_zone" maxlength="50" placeholder="手动填写片区/地点（如：A区3栋附近）" />
              <div class="location-manual-grid">
                <input
                  v-model.number="publishLocation.latitude"
                  type="number"
                  step="0.000001"
                  min="-90"
                  max="90"
                  placeholder="手动填写纬度（可选）"
                />
                <input
                  v-model.number="publishLocation.longitude"
                  type="number"
                  step="0.000001"
                  min="-180"
                  max="180"
                  placeholder="手动填写经度（可选）"
                />
              </div>
              <div class="location-actions">
                <button class="btn-location" type="button" @click="handleGetPublishLocation">获取当前位置</button>
                <button
                  v-if="publishLocation.latitude !== null || publishLocation.longitude !== null || publishLocation.community_zone"
                  class="btn-location-clear"
                  type="button"
                  @click="clearPublishLocation"
                >
                  清除位置
                </button>
              </div>
              <small class="form-tip">可不填写。填写后会用于任务距离计算与附近排序。</small>
              <small
                v-if="publishLocation.latitude !== null && publishLocation.longitude !== null"
                class="location-value"
              >
                已获取：{{ publishLocation.latitude }}, {{ publishLocation.longitude }}
              </small>
            </div>
            
            <button class="btn-submit-task" @click="submitTask">立即发布</button>
          </div>
        </div>
      </div>
    </Transition>

    <DetailModal
      :visible="showDetailModal"
      :title="currentTask.title || '任务详情'"
      :rows="detailRows"
      @close="showDetailModal = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/store/user'
import axios from 'axios'
import DetailModal from '@/components/DetailModal.vue'

const userStore = useUserStore()
const userRole = computed(() => userStore.role)
const username = computed(() => userStore.username)
const canAcceptTasks = computed(() => userStore.isExpert || userStore.isProvider)

// 状态管理
const tasks = ref([])
const showModal = ref(false)
const showDetailModal = ref(false)
const currentTask = ref({})
const searchQuery = ref('')
const selectedCategory = ref('all')
const sortType = ref('created_desc')
const userLocation = ref({
  latitude: null,
  longitude: null
})
const publishLocation = ref({
  community_zone: '',
  latitude: null,
  longitude: null
})
const newTask = ref({ title: '', category: 'errand', content: '', reward_points: 10 })

// 接口逻辑
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
const handleGetPublishLocation = () => {
  if (!navigator.geolocation) {
    alert('当前浏览器不支持定位')
    return
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      publishLocation.value.latitude = Number(pos.coords.latitude.toFixed(6))
      publishLocation.value.longitude = Number(pos.coords.longitude.toFixed(6))
    },
    () => {
      alert('定位失败，请检查浏览器定位权限')
    },
    { enableHighAccuracy: false, timeout: 8000, maximumAge: 300000 }
  )
}
const clearPublishLocation = () => {
  publishLocation.value.community_zone = ''
  publishLocation.value.latitude = null
  publishLocation.value.longitude = null
}

const fetchTasks = async () => {
  try {
    const params = {
      category: selectedCategory.value
    }
    if (userLocation.value.latitude && userLocation.value.longitude) {
      params.user_lat = userLocation.value.latitude
      params.user_lng = userLocation.value.longitude
    }
    const res = await axios.get('http://127.0.0.1:8000/api/get_tasks/', { params })
    tasks.value = res.data.tasks || []
  } catch (err) {
    console.error("加载数据失败", err)
  }
}

const submitTask = async () => {
  // 1. 基础校验
  if (!newTask.value.title || !newTask.value.content) {
    return alert('请完善任务标题和详情内容');
  }

  try {
    // 🚀 核心修复：必须把字段名改为 'username'，以匹配后端的 data.get('username')
    const res = await axios.post('http://127.0.0.1:8000/api/create_task/', {
      title: newTask.value.title,
      content: newTask.value.content,
      category: newTask.value.category,
      reward_points: Number(newTask.value.reward_points || 10),
      community_zone: publishLocation.value.community_zone || null,
      latitude: publishLocation.value.latitude,
      longitude: publishLocation.value.longitude,
      username: username.value  // 👈 重点：这里的 Key 必须叫 username
    });

    if (res?.data?.points !== undefined) {
      userStore.points = res.data.points
    }
    alert(res?.data?.message || '提交成功！任务已进入后台审核队列。');
    
    // 2. 关闭弹窗并重置表单
    showModal.value = false;
    newTask.value = { title: '', category: 'errand', content: '', reward_points: 10 };
    clearPublishLocation()
    
    // 3. 刷新列表（此时新任务在审核中，大厅列表依然不显示它是正常的）
    fetchTasks(); 
    
  } catch (err) {
    console.error('发布失败详情:', err);
    alert('发布失败，请检查登录状态或后端连接');
  }
};

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
    alert('接单失败')
  }
}

const openDetail = (task) => {
  currentTask.value = task
  showDetailModal.value = true
}
const detailRows = computed(() => {
  return [
    { label: '任务标题', value: currentTask.value.title },
    { label: '任务类型', value: formatCategory(currentTask.value.category) },
    { label: '发布人', value: currentTask.value.creator },
    { label: '悬赏积分', value: currentTask.value.reward_points ?? 0 },
    { label: '发布时间', value: currentTask.value.created_at },
    { label: '任务描述', value: currentTask.value.content, multiline: true }
  ]
})

onMounted(async () => {
  await getCurrentLocation()
  fetchTasks()
})

// 计算过滤
const filteredTasks = computed(() => {
  const list = tasks.value.filter(t =>
    t.title.toLowerCase().includes(searchQuery.value.toLowerCase())
  )

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

const formatCategory = (cat) => {
  const map = { errand: '跑腿代购', repair: '家电维修', pet: '宠物照顾', other: '其他互助' }
  return map[cat] || '邻里互助'
}
</script>

<style scoped>
/* 1. 核心布局修复 */
.task-market-container {
  margin-left: 260px; /* 避开侧边栏 */
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

/* 2. 头部风格 */
.market-header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 14px;
  padding: 30px 45px; margin-bottom: 35px;
}
.market-header h1 { font-size: 28px; color: #2d3748; margin: 0; }
.subtitle { color: #718096; margin: 0; font-size: 14px; }
.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.search-bar { position: relative; flex: 1; min-width: 260px; }
.search-bar input {
  padding: 12px 20px 12px 45px; border-radius: 30px; border: 1px solid #e2e8f0; width: 100%; outline: none; transition: 0.3s;
}
.search-bar input:focus { border-color: #4299e1; box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1); }
.search-icon { position: absolute; left: 18px; top: 12px; color: #a0aec0; }
.category-filter {
  border: 1px solid #e2e8f0;
  border-radius: 30px;
  padding: 11px 14px;
  background: white;
  color: #4a5568;
  outline: none;
}

.btn-add-task-fab {
  width: 52px; height: 52px; border-radius: 50%; background: #4299e1; color: white;
  border: none; font-size: 30px; cursor: pointer; margin-left: 15px;
  box-shadow: 0 4px 15px rgba(66, 153, 225, 0.3); transition: 0.3s;
}
.btn-add-task-fab:hover { transform: scale(1.1); background: #3182ce; }

/* 3. 任务卡片网格 */
.task-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 25px; }
.task-card { padding: 25px; transition: 0.3s; }
.task-card:hover { transform: translateY(-5px); box-shadow: 0 12px 40px rgba(0,0,0,0.06); }

.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.category-badge { padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: 700; }
.category-badge.errand { background: #ebf8ff; color: #3182ce; }
.category-badge.repair { background: #edf2f7; color: #4a5568; }
.category-badge.pet { background: #fffaf0; color: #dd6b20; }
.category-badge.other { background: #f7fafc; color: #718096; }

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
.card-desc {
  color: #4a5568; font-size: 14px; line-height: 1.7; height: 72px;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;
}
.distance-line {
  margin: 6px 0 0;
  color: #718096;
  font-size: 13px;
}

.card-footer { border-top: 1px solid #f1f5f9; padding-top: 18px; margin-top: 10px; }
.action-group { display: flex; gap: 12px; justify-content: flex-end; }
.btn-accept { background: #4299e1; color: white; border: none; padding: 9px 22px; border-radius: 10px; cursor: pointer; font-weight: 600; }
.btn-detail { background: #f8fafc; border: 1px solid #e2e8f0; padding: 9px 22px; border-radius: 10px; color: #4a5568; cursor: pointer; }

/* 4. 弹窗样式修正 (垂直布局) */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(10, 25, 47, 0.6);
  backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; z-index: 2000;
  padding: 16px;
}
.task-modal {
  width: 520px;
  padding: 40px;
  position: relative;
  max-height: 90vh;
  overflow-y: auto;
}
.modal-title { text-align: center; margin-bottom: 30px; color: #2d3748; }

.form-item {
  display: flex; flex-direction: column; /* 🚀 垂直排列关键 */
  gap: 10px; margin-bottom: 22px;
}
.form-item label { font-weight: 700; color: #4a5568; font-size: 14px; padding-left: 4px; }
.form-item input, .form-item select, .form-item textarea {
  padding: 13px; border-radius: 12px; border: 1px solid #e2e8f0; background: #f8fafc; font-size: 14px; outline: none;
}
.form-item input:focus, .form-item textarea:focus { border-color: #4299e1; background: white; }
.form-item textarea { height: 130px; resize: none; }
.form-tip { color: #718096; font-size: 12px; line-height: 1.5; }
.location-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.location-manual-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
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
.location-value {
  color: #0f766e;
  font-size: 12px;
}

.btn-submit-task {
  width: 100%; padding: 15px; background: #4299e1; color: white; border: none; border-radius: 14px;
  font-weight: 700; font-size: 16px; cursor: pointer; margin-top: 10px; box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
}

.close-x { position: absolute; right: 25px; top: 25px; font-size: 24px; border: none; background: none; color: #cbd5e0; cursor: pointer; }

.empty-state { text-align: center; padding: 120px; color: #cbd5e0; font-size: 16px; }
.btn-post-first { background: #4299e1; color: white; border: none; padding: 12px 30px; border-radius: 30px; margin-top: 20px; cursor: pointer; }

.fade-enter-active, .fade-leave-active { transition: 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.95); }
</style>
