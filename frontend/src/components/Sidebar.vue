<template>
  <aside class="sidebar-wrapper">
    <div class="user-profile">
      <div class="avatar-container">
        <div class="avatar-circle">
          {{ userStore.username?.charAt(0).toUpperCase() || 'U' }}
        </div>
      </div>
      <div class="user-info">
        <span class="role-badge">
          {{ 
            userStore.role === 'admin' ? '管理员' : 
            userStore.isExpert && userStore.isProvider ? '邻里达人 / 认证服务者' :
            userStore.isExpert ? '邻里达人' :
            userStore.isProvider ? '认证服务者' : '普通用户' 
          }}
        </span>
        <p class="welcome-text">您好，<span>{{ userStore.username || '访客' }}</span></p>
        <p class="welcome-text">🪙 <span>{{ userStore.points || 0 }}</span></p>
      </div>
    </div>

    <nav class="nav-menu">
      <router-link to="/user" class="nav-item" active-class="active">
        <span class="icon">👤</span> 个人中心
      </router-link>

      <button
        :class="['nav-item', 'nav-group-trigger', isTaskRoute ? 'active' : '']"
        @click="toggleTaskCenter"
      >
        <span class="icon">🗂️</span>
        <span class="group-title">任务中心</span>
        <span class="chevron">{{ taskCenterOpen ? '▾' : '▸' }}</span>
      </button>

      <div v-if="taskCenterOpen" class="sub-menu">
        <router-link to="/tasks" class="sub-nav-item" active-class="active-sub">
          <span class="icon">🤝</span> 任务市场
        </router-link>
        <router-link to="/mytasks" class="sub-nav-item" active-class="active-sub">
          <span class="icon">📋</span> 我的任务
        </router-link>
        <router-link to="/providers" class="sub-nav-item" active-class="active-sub">
          <span class="icon">🧰</span> 认证服务者
        </router-link>
      </div>

      <router-link to="/forum" class="nav-item" active-class="active">
        <span class="icon">💬</span> 社区论坛
      </router-link>

      <router-link v-if="userStore.role === 'admin'" to="/admin" class="nav-item admin-link">
        <span class="icon">⚙️</span> 返回管理后台
      </router-link>
      
      <div class="nav-footer">
        <button class="logout-btn" @click="handleLogout">退出登录</button>
      </div>
    </nav>
  </aside>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useUserStore } from '@/store/user'
import { useRouter, useRoute } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()

const taskCenterOpen = ref(false)
const isTaskRoute = computed(() => ['/tasks', '/mytasks', '/providers'].includes(route.path))

watch(
  () => route.path,
  (path) => {
    if (path === '/tasks' || path === '/mytasks' || path === '/providers') {
      taskCenterOpen.value = true
    }
  },
  { immediate: true }
)

const toggleTaskCenter = () => {
  taskCenterOpen.value = !taskCenterOpen.value
}

const handleLogout = () => {
  if (confirm('确定要退出登录吗？')) {
    userStore.clearUserInfo()
    router.push('/')
  }
}
</script>

<style scoped>
/* 核心容器：深蓝毛玻璃 */
.sidebar-wrapper {
  width: 260px;
  height: 100vh;
  background: rgba(10, 25, 47, 0.85); 
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
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

/* 用户信息区：略微透亮的背景 */
.user-profile {
  padding: 40px 20px;
  text-align: center;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.avatar-circle {
  width: 65px;
  height: 65px;
  background: linear-gradient(135deg, #4299e1, #667eea);
  border-radius: 50%;
  margin: 0 auto 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 800;
  box-shadow: 0 4px 20px rgba(66, 153, 225, 0.3);
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.role-badge {
  background: rgba(102, 126, 234, 0.2);
  padding: 3px 12px;
  border-radius: 20px;
  font-size: 11px;
  color: #a0aec0;
  letter-spacing: 1px;
}

.welcome-text {
  margin-top: 12px;
  font-size: 15px;
  color: #cbd5e0;
}

.welcome-text span {
  font-weight: 600;
  color: #63b3ed;
}

/* 菜单列表 */
.nav-menu {
  flex: 1;
  min-height: 0;
  padding: 25px 15px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 14px 18px;
  text-decoration: none;
  color: #a0aec0;
  border-radius: 10px;
  transition: all 0.25s ease;
  font-size: 15px;
}

.nav-group-trigger {
  width: 100%;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.group-title {
  flex: 1;
}

.chevron {
  margin-left: auto;
  opacity: 0.8;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  transform: translateX(5px);
}

/* 激活状态：深蓝中的浅蓝亮起 */
.nav-item.active {
  background: rgba(66, 153, 225, 0.15);
  color: #63b3ed !important;
  font-weight: 600;
  border-left: 4px solid #4299e1;
}

.sub-menu {
  margin: -2px 0 6px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sub-nav-item {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  text-decoration: none;
  color: #a0aec0;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.25s ease;
}

.sub-nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.sub-nav-item.active-sub {
  background: rgba(66, 153, 225, 0.15);
  color: #63b3ed;
  font-weight: 600;
}

/* 特殊样式：返回管理后台按钮 */
.admin-link {
  margin-top: 10px;
  border: 1px dashed rgba(99, 179, 237, 0.3);
}

.icon {
  margin-right: 12px;
  font-size: 18px;
}

/* 底部退出 */
.nav-footer {
  margin-top: auto;
  padding: 30px 20px;
}

.logout-btn {
  width: 100%;
  padding: 12px;
  background: rgba(245, 101, 101, 0.1);
  border: 1px solid rgba(245, 101, 101, 0.3);
  color: #fc8181;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
}

.logout-btn:hover {
  background: #f56565;
  color: white;
  box-shadow: 0 4px 15px rgba(245, 101, 101, 0.4);
}
</style>
