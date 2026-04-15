<template>
  <aside class="admin-sidebar-wrapper">
    <div class="admin-profile">
      <div class="avatar-container">
        <div class="avatar-circle">
          {{ adminName?.charAt(0).toUpperCase() || 'A' }}
        </div>
      </div>
      <div class="admin-info">
        <span class="role-badge">超级管理员</span>
        <p class="welcome-text">您好，<span>{{ adminName || '管理员' }}</span></p>
      </div>
    </div>

    <nav class="nav-menu">
      <div class="menu-label">管理中心</div>
      
      <div 
        class="nav-item" 
        :class="{ active: currentActive === 'dashboard' }"
        @click="handleSwitch('dashboard')"
      >
        <span class="icon">📊</span> 运营仪表盘
      </div>

      <div 
        class="nav-item" 
        :class="{ active: currentActive === 'users' }"
        @click="handleSwitch('users')"
      >
        <span class="icon">👥</span> 用户管理
      </div>
      
      <div 
        class="nav-item nav-group"
        :class="{ active: isIdentityAuditActive }"
        @click="toggleIdentityAudit"
      >
        <span class="icon">📝</span> 社区身份审核
        <span class="chevron">{{ identityAuditOpen ? '▾' : '▸' }}</span>
      </div>
      <div v-if="identityAuditOpen" class="sub-menu">
        <div
          class="sub-nav-item"
          :class="{ active: currentActive === 'applyExpert' }"
          @click="handleSwitch('applyExpert')"
        >
          邻里达人审核
        </div>
        <div
          class="sub-nav-item"
          :class="{ active: currentActive === 'applyProvider' }"
          @click="handleSwitch('applyProvider')"
        >
          认证服务者审核
        </div>
      </div>

      <div
        class="nav-item nav-group"
        :class="{ active: isContentManageActive }"
        @click="toggleContentManage"
      >
        <span class="icon">📜</span> 社区内容管理
        <span class="chevron">{{ contentManageOpen ? '▾' : '▸' }}</span>
      </div>
      <div v-if="contentManageOpen" class="sub-menu">
        <div
          class="sub-nav-item"
          :class="{ active: currentActive === 'announcementManage' }"
          @click="handleSwitch('announcementManage')"
        >
          社区公告管理
        </div>
        <div
          class="sub-nav-item"
          :class="{ active: currentActive === 'postManage' }"
          @click="handleSwitch('postManage')"
        >
          社区帖子管理
        </div>
      </div>

      <div 
        class="nav-item" 
        :class="{ active: currentActive === 'taskAudit' }"
        @click="handleSwitch('taskAudit')"
      >
        <span class="icon">⚖️</span> 社区任务审核
      </div>

      <div class="nav-footer">
        <button class="logout-btn" @click="logout">
          退出系统
        </button>
      </div>
    </nav>
  </aside>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  adminName: String
})

const emit = defineEmits(['switchView'])
const router = useRouter()

// 🚀 核心：统一使用 currentActive 记录当前激活的菜单项
const currentActive = ref('dashboard')
const contentManageOpen = ref(false)
const identityAuditOpen = ref(false)
const isContentManageActive = computed(() => ['announcementManage', 'postManage'].includes(currentActive.value))
const isIdentityAuditActive = computed(() => ['applyExpert', 'applyProvider'].includes(currentActive.value))


const logout = () => {
  localStorage.removeItem('username')
  router.push('/')
}

const handleSwitch = (view) => {
  console.log('侧边栏点击了，发送的值是:', view) // 🚀 加这一行
  currentActive.value = view
  if (view === 'applyExpert' || view === 'applyProvider') {
    identityAuditOpen.value = true
  }
  if (view === 'announcementManage' || view === 'postManage') {
    contentManageOpen.value = true
  }
  emit('switchView', view)
}

const toggleContentManage = () => {
  contentManageOpen.value = !contentManageOpen.value
}
const toggleIdentityAudit = () => {
  identityAuditOpen.value = !identityAuditOpen.value
}
</script>

<style scoped>
/* 核心容器：深绿色毛玻璃 */
.admin-sidebar-wrapper {
  width: 260px;
  height: 100vh;
  background: rgba(6, 31, 26, 0.85);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
  color: white;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 管理员信息区 */
.admin-profile {
  padding: 40px 20px;
  text-align: center;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.avatar-circle {
  width: 65px;
  height: 65px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 50%;
  margin: 0 auto 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  font-weight: 800;
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.role-badge {
  background: rgba(16, 185, 129, 0.2);
  padding: 3px 12px;
  border-radius: 20px;
  font-size: 11px;
  color: #6ee7b7;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.welcome-text {
  margin-top: 12px;
  font-size: 15px;
  color: #d1fae5;
}

.welcome-text span {
  font-weight: 600;
  color: #10b981;
}

/* 导航菜单区 */
.nav-menu {
  flex: 1;
  min-height: 0;
  padding: 25px 15px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.menu-label {
  font-size: 12px;
  color: #34d399;
  opacity: 0.6;
  margin-left: 15px;
  margin-bottom: 10px;
  letter-spacing: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 14px 18px;
  color: #a7f3d0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
  font-size: 15px;
  border-left: 4px solid transparent; /* 预留边框位，防止抖动 */
}

.nav-group .chevron {
  margin-left: auto;
  opacity: 0.85;
}

.sub-menu {
  margin-top: -3px;
  margin-left: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sub-nav-item {
  padding: 10px 14px;
  border-radius: 10px;
  color: #a7f3d0;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.sub-nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.sub-nav-item.active {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  font-weight: 600;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  transform: translateX(5px);
}

/* 激活状态：翠绿色高亮 */
.nav-item.active {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  font-weight: 600;
  border-left: 4px solid #10b981;
}

.icon {
  margin-right: 12px;
  font-size: 18px;
}

/* 退出登录 */
.nav-footer {
  margin-top: auto;
  padding: 30px 20px;
}

.logout-btn {
  width: 100%;
  height: 45px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #ecfdf5;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.4);
  color: #f87171;
}
</style>
