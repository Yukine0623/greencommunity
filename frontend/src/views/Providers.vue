<template>
  <div class="providers-container">
    <header class="providers-header glass-card">
      <h1>认证服务者大厅</h1>
      <p>浏览已通过认证的服务者，并可定向发送服务邀约</p>
      <div class="filters">
        <input v-model="keyword" placeholder="搜索服务者用户名..." />

        <div class="multi-select" @click.stop>
          <button class="multi-trigger" @click="directionPanelOpen = !directionPanelOpen">
            {{ selectedDirections.length ? `服务方向（${selectedDirections.length}）` : '全部服务方向' }}
          </button>
          <div v-if="directionPanelOpen" class="multi-panel">
            <label v-for="item in directionOptions" :key="`fd-${item}`" class="multi-option">
              <input
                type="checkbox"
                :checked="selectedDirections.includes(item)"
                @change="toggleDirectionFilter(item)"
              />
              <span>{{ item }}</span>
            </label>
            <button class="clear-btn" @click="selectedDirections = []">清空</button>
          </div>
        </div>

        <div class="multi-select" @click.stop>
          <button class="multi-trigger" @click="timePanelOpen = !timePanelOpen">
            {{ selectedTimes.length ? `服务时间（${selectedTimes.length}）` : '全部服务时间' }}
          </button>
          <div v-if="timePanelOpen" class="multi-panel">
            <label v-for="item in timeOptions" :key="`ft-${item}`" class="multi-option">
              <input
                type="checkbox"
                :checked="selectedTimes.includes(item)"
                @change="toggleTimeFilter(item)"
              />
              <span>{{ item }}</span>
            </label>
            <button class="clear-btn" @click="selectedTimes = []">清空</button>
          </div>
        </div>

        <div class="price-range-wrap">
          <span class="price-range-label">报价区间：</span>
          <div class="price-range-inputs">
            <input
              v-model.number="priceFilterMin"
              type="number"
              min="0"
              step="1"
              placeholder="最低价（元）"
            />
            <input
              v-model.number="priceFilterMax"
              type="number"
              min="0"
              step="1"
              placeholder="最高价（元）"
            />
          </div>
        </div>
      </div>
    </header>

    <section class="providers-grid" v-if="filteredProviders.length > 0">
      <article v-for="item in filteredProviders" :key="item.username" class="provider-card glass-card">
        <div class="provider-top">
          <div class="avatar">{{ item.avatar_text }}</div>
          <div>
            <h3>{{ item.username }}</h3>
            <p class="scope">{{ item.service_scope || '暂无服务范围描述' }}</p>
          </div>
        </div>
        <div class="tags-row">
          <span class="label">服务方向</span>
          <div class="tags">
            <span v-for="tag in item.service_directions" :key="`d-${item.username}-${tag}`" class="tag direction">{{ tag }}</span>
            <span v-if="!item.service_directions?.length" class="tag">暂无</span>
          </div>
        </div>
        <div class="tags-row">
          <span class="label">服务时间</span>
          <div class="tags">
            <span v-for="tag in item.service_times" :key="`t-${item.username}-${tag}`" class="tag time">{{ tag }}</span>
            <span v-if="!item.service_times?.length" class="tag">暂无</span>
          </div>
        </div>
        <p class="price">报价区间：{{ item.price_range || '面议' }}</p>
        <div class="actions">
          <button class="btn-ghost" @click="openDetailModal(item)">详情</button>
          <button class="btn-primary" @click="openInviteModal(item.username)">定向邀约</button>
        </div>
      </article>
    </section>
    <div v-else class="empty">暂无匹配的认证服务者</div>

    <Transition name="fade">
      <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
        <div class="modal-content glass-card">
          <h3>认证服务者详情</h3>
          <p class="sub">服务者：{{ selectedProvider?.username }}</p>
          <div class="detail-row">
            <span class="k">服务范围</span>
            <span class="v">{{ selectedProvider?.service_scope || '暂无' }}</span>
          </div>
          <div class="detail-row">
            <span class="k">服务方向</span>
            <span class="v">{{ (selectedProvider?.service_directions || []).join('、') || '暂无' }}</span>
          </div>
          <div class="detail-row">
            <span class="k">服务时间</span>
            <span class="v">{{ (selectedProvider?.service_times || []).join('、') || '暂无' }}</span>
          </div>
          <div class="detail-row">
            <span class="k">价格区间</span>
            <span class="v">{{ selectedProvider?.price_range || '面议' }}</span>
          </div>
          <div class="detail-row">
            <span class="k">简介</span>
            <span class="v">{{ selectedProvider?.provider_intro || '暂无简介' }}</span>
          </div>
          <div class="modal-footer">
            <button class="btn-ghost" @click="showDetailModal = false">关闭</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="showInviteModal" class="modal-overlay" @click.self="showInviteModal = false">
        <div class="modal-content glass-card">
          <h3>发送定向邀约</h3>
          <p class="sub">邀约对象：{{ inviteForm.invited_provider_username }}</p>
          <div class="form-item">
            <label>任务标题</label>
            <input v-model="inviteForm.title" maxlength="30" />
          </div>
          <div class="form-item">
            <label>任务分类</label>
            <select v-model="inviteForm.category">
              <option value="repair">家电维修</option>
              <option value="errand">跑腿代购</option>
              <option value="pet">宠物照顾</option>
              <option value="other">其他互助</option>
            </select>
          </div>
          <div class="form-item">
            <label>任务说明</label>
            <textarea v-model="inviteForm.content" maxlength="1000"></textarea>
          </div>
          <div class="form-item">
            <label>悬赏积分</label>
            <input v-model.number="inviteForm.reward_points" type="number" min="1" step="1" />
          </div>
          <div class="form-item">
            <label>任务位置（可选）</label>
            <input
              v-model="inviteForm.community_zone"
              type="text"
              maxlength="100"
              placeholder="例如：A区3号楼附近（可手动填写）"
            />
            <div class="location-manual-grid">
              <input
                v-model.number="inviteForm.latitude"
                type="number"
                step="0.000001"
                min="-90"
                max="90"
                placeholder="纬度（可选）"
              />
              <input
                v-model.number="inviteForm.longitude"
                type="number"
                step="0.000001"
                min="-180"
                max="180"
                placeholder="经度（可选）"
              />
            </div>
            <div class="location-actions">
              <button class="btn-location" type="button" @click="handleGetInviteLocation">获取当前位置</button>
              <button
                v-if="inviteForm.latitude !== null || inviteForm.longitude !== null || inviteForm.community_zone"
                class="btn-location-clear"
                type="button"
                @click="clearInviteLocation"
              >
                清除位置
              </button>
            </div>
            <p
              v-if="inviteForm.latitude !== null && inviteForm.longitude !== null"
              class="location-value"
            >
              已获取：{{ inviteForm.latitude }}, {{ inviteForm.longitude }}
            </p>
          </div>
          <div class="modal-footer">
            <button class="btn-ghost" @click="showInviteModal = false">取消</button>
            <button class="btn-primary" @click="submitInvite">发送邀约</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import axios from 'axios'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const providers = ref([])
const keyword = ref('')
const selectedDirections = ref([])
const selectedTimes = ref([])
const directionPanelOpen = ref(false)
const timePanelOpen = ref(false)
const showInviteModal = ref(false)
const showDetailModal = ref(false)
const selectedProvider = ref(null)
const priceFilterMin = ref(null)
const priceFilterMax = ref(null)
const directionOptions = ['家电维修', '管道疏通', '电路检修', '搬运服务', '保洁服务', '家居安装', '上门做饭', '宠物照护']
const timeOptions = ['0:00-8:00', '8:00-13:00', '13:00-18:00', '18:00-24:00']
const inviteForm = ref({
  title: '',
  category: 'repair',
  content: '',
  reward_points: 10,
  invited_provider_username: '',
  community_zone: '',
  latitude: null,
  longitude: null
})

const fetchProviders = async () => {
  const res = await axios.get('http://127.0.0.1:8000/api/providers/')
  providers.value = res.data.providers || []
}
const filteredProviders = computed(() => {
  const q = keyword.value.trim().toLowerCase()
  const toPriceValue = (raw) => {
    if (raw === '' || raw === null || raw === undefined) return null
    const n = Number(raw)
    if (!Number.isFinite(n) || n < 0) return null
    return n
  }
  const selectedMin = toPriceValue(priceFilterMin.value)
  const selectedMax = toPriceValue(priceFilterMax.value)
  const normalizedMin = selectedMin !== null && selectedMin >= 0 ? selectedMin : null
  const normalizedMax = selectedMax !== null && selectedMax >= 0 ? selectedMax : null
  return providers.value.filter((item) => {
    const hitKeyword = !q || (item.username || '').toLowerCase().includes(q)
    const hitDirection = selectedDirections.value.length === 0
      || selectedDirections.value.every((tag) => (item.service_directions || []).includes(tag))
    const hitTime = selectedTimes.value.length === 0
      || selectedTimes.value.every((tag) => (item.service_times || []).includes(tag))
    let hitPrice = true
    if (normalizedMin !== null || normalizedMax !== null) {
      const providerMin = Number(item.price_range_min)
      const providerMax = Number(item.price_range_max)
      if (!Number.isFinite(providerMin) || !Number.isFinite(providerMax)) {
        hitPrice = false
      } else {
        const rangeMin = normalizedMin !== null ? normalizedMin : 0
        const rangeMax = normalizedMax !== null ? normalizedMax : Number.MAX_SAFE_INTEGER
        const finalMin = Math.min(rangeMin, rangeMax)
        const finalMax = Math.max(rangeMin, rangeMax)
        hitPrice = !(providerMax < finalMin || providerMin > finalMax)
      }
    }
    return hitKeyword && hitDirection && hitTime && hitPrice
  })
})
const toggleDirectionFilter = (value) => {
  if (selectedDirections.value.includes(value)) {
    selectedDirections.value = selectedDirections.value.filter((item) => item !== value)
  } else {
    selectedDirections.value = [...selectedDirections.value, value]
  }
}
const toggleTimeFilter = (value) => {
  if (selectedTimes.value.includes(value)) {
    selectedTimes.value = selectedTimes.value.filter((item) => item !== value)
  } else {
    selectedTimes.value = [...selectedTimes.value, value]
  }
}
const handleOutsideClick = (event) => {
  const target = event.target
  if (!(target instanceof HTMLElement)) return
  if (!target.closest('.multi-select')) {
    directionPanelOpen.value = false
    timePanelOpen.value = false
  }
}

const openInviteModal = (username) => {
  inviteForm.value = {
    title: '',
    category: 'repair',
    content: '',
    reward_points: 10,
    invited_provider_username: username,
    community_zone: '',
    latitude: null,
    longitude: null
  }
  showInviteModal.value = true
}
const openDetailModal = (item) => {
  selectedProvider.value = item
  showDetailModal.value = true
}

const submitInvite = async () => {
  if (!inviteForm.value.title || !inviteForm.value.content) {
    alert('请填写任务标题和任务说明')
    return
  }
  const res = await axios.post('http://127.0.0.1:8000/api/create_task/', {
    username: userStore.username,
    title: inviteForm.value.title,
    category: inviteForm.value.category,
    content: inviteForm.value.content,
    reward_points: Number(inviteForm.value.reward_points || 10),
    assignee_type: 'provider',
    invited_provider_username: inviteForm.value.invited_provider_username,
    community_zone: inviteForm.value.community_zone,
    latitude: inviteForm.value.latitude,
    longitude: inviteForm.value.longitude
  })
  if (res.data.code !== 200) {
    alert(res.data.message || '发送邀约失败')
    return
  }
  if (res?.data?.points !== undefined) {
    userStore.points = res.data.points
  }
  alert(res.data.message || '邀约任务已提交审核')
  showInviteModal.value = false
}
const handleGetInviteLocation = () => {
  if (!navigator.geolocation) {
    alert('当前浏览器不支持定位')
    return
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      inviteForm.value.latitude = Number(pos.coords.latitude.toFixed(6))
      inviteForm.value.longitude = Number(pos.coords.longitude.toFixed(6))
      if (!inviteForm.value.community_zone?.trim()) {
        inviteForm.value.community_zone = '当前位置'
      }
    },
    () => {
      alert('定位失败，请检查浏览器定位权限')
    },
    { enableHighAccuracy: true, timeout: 8000 }
  )
}
const clearInviteLocation = () => {
  inviteForm.value.community_zone = ''
  inviteForm.value.latitude = null
  inviteForm.value.longitude = null
}

onMounted(() => {
  fetchProviders()
  document.addEventListener('click', handleOutsideClick)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutsideClick)
})
</script>

<style scoped>
.providers-container { margin-left: 260px; padding: 40px; min-height: 100vh; background: #f4f7f9; }
.glass-card { background: #fff; border-radius: 20px; border: 1px solid rgba(255,255,255,0.4); box-shadow: 0 8px 26px rgba(0,0,0,0.04); }
.providers-header { padding: 28px 32px; margin-bottom: 24px; }
.providers-header h1 { margin: 0 0 6px; font-size: 32px; color: #111827; }
.providers-header p { margin: 0 0 14px; color: #6b7280; font-size: 16px; }
.filters { display: flex; gap: 10px; flex-wrap: wrap; }
.filters input {
  height: 44px;
  box-sizing: border-box;
  padding: 10px 12px;
  border: 1px solid #dbe3eb;
  border-radius: 10px;
}
.price-range-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 44px;
  box-sizing: border-box;
  padding: 0 10px;
  border: 1px solid #dbe3eb;
  border-radius: 10px;
  background: #fff;
}
.price-range-label {
  color: #475569;
  font-size: 13px;
  white-space: nowrap;
}
.price-range-inputs {
  display: flex;
  gap: 8px;
}
.price-range-inputs input {
  width: 120px;
  height: 32px;
  box-sizing: border-box;
  padding: 6px 10px;
  border: 1px solid #dbe3eb;
  border-radius: 10px;
}
.multi-select { position: relative; }
.multi-trigger {
  border: 1px solid #dbe3eb;
  background: #fff;
  border-radius: 10px;
  height: 44px;
  box-sizing: border-box;
  padding: 10px 12px;
  color: #334155;
  cursor: pointer;
  min-width: 160px;
  text-align: left;
}
.multi-panel {
  position: absolute;
  top: 110%;
  left: 0;
  min-width: 220px;
  max-height: 240px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #dbe3eb;
  border-radius: 12px;
  box-shadow: 0 10px 26px rgba(0,0,0,0.1);
  padding: 8px;
  z-index: 30;
}
.multi-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  color: #334155;
  font-size: 13px;
}
.clear-btn {
  width: 100%;
  margin-top: 4px;
  border: 1px solid #dbe3eb;
  background: #f8fafc;
  border-radius: 8px;
  color: #475569;
  padding: 6px 8px;
  cursor: pointer;
}
.providers-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.provider-card { padding: 18px; display: flex; flex-direction: column; gap: 10px; }
.provider-top { display: flex; align-items: center; gap: 12px; }
.avatar { width: 46px; height: 46px; border-radius: 50%; background: linear-gradient(135deg, #60a5fa, #2563eb); color: #fff; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.provider-top h3 { margin: 0; color: #0f172a; }
.scope { margin: 4px 0 0; color: #64748b; font-size: 13px; }
.tags-row { display: flex; gap: 8px; align-items: flex-start; }
.label { min-width: 64px; color: #334155; font-size: 13px; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag { padding: 2px 9px; border-radius: 999px; font-size: 12px; background: #f1f5f9; color: #334155; }
.tag.direction { background: #e0f2fe; color: #075985; }
.tag.time { background: #ede9fe; color: #5b21b6; }
.price { margin: 4px 0 0; color: #0f172a; font-weight: 600; }
.actions { display: flex; justify-content: flex-end; margin-top: 4px; }
.btn-primary { border: none; background: #2563eb; color: #fff; border-radius: 10px; padding: 9px 14px; cursor: pointer; }
.btn-ghost { border: 1px solid #cbd5e1; background: #fff; color: #334155; border-radius: 10px; padding: 9px 14px; cursor: pointer; }
.empty { padding: 32px; text-align: center; color: #64748b; }
.modal-overlay { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.5); display: flex; align-items: center; justify-content: center; z-index: 2200; padding: 16px; }
.modal-content { width: 520px; max-width: 100%; max-height: 88vh; overflow-y: auto; padding: 24px; }
.modal-content h3 { margin: 0 0 4px; }
.sub { margin: 0 0 12px; color: #64748b; font-size: 13px; }
.form-item { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
.form-item input, .form-item select, .form-item textarea { border: 1px solid #dbe3eb; border-radius: 10px; padding: 10px; }
.form-item textarea { min-height: 90px; resize: vertical; }
.location-manual-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.location-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.btn-location,
.btn-location-clear {
  border: 1px solid #dbe3eb;
  background: #fff;
  color: #334155;
  border-radius: 10px;
  padding: 8px 12px;
  cursor: pointer;
}
.btn-location-clear {
  color: #7f1d1d;
  border-color: #fecaca;
  background: #fff5f5;
}
.location-value {
  margin: 0;
  color: #64748b;
  font-size: 12px;
}
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; }
.detail-row { display: flex; gap: 10px; margin-bottom: 10px; }
.detail-row .k { min-width: 72px; color: #64748b; font-size: 13px; }
.detail-row .v { color: #0f172a; font-size: 14px; line-height: 1.5; }
@media (max-width: 1100px) {
  .providers-grid { grid-template-columns: 1fr; }
  .location-manual-grid { grid-template-columns: 1fr; }
}
</style>
