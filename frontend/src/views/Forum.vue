<template>
  <div class="forum-layout-wrapper">
    <div class="forum-content">
      <header class="forum-header">
        <div class="search-wrapper">
          <span class="search-icon">🔍</span>
          <input v-model="keyword" placeholder="搜索帖子标题..." />
        </div>

        <div class="tabs-pill">
          <button :class="{ active: tab === 'all' }" @click="tab = 'all'">所有帖子</button>
          <button :class="{ active: tab === 'mine' }" @click="tab = 'mine'">我的帖子</button>
        </div>
      </header>

      <section class="glass-card announcement-board">
        <div class="board-header">
          <h3>社区公告</h3>
        </div>

        <div v-if="isAdmin" class="announcement-editor">
          <input
            v-model="announcementForm.title"
            class="announcement-title-input"
            placeholder="公告标题"
            maxlength="100"
          />
          <textarea
            v-model="announcementForm.content"
            class="announcement-content-input"
            placeholder="请输入公告内容..."
            maxlength="1000"
          />
          <button class="btn-submit-announcement" @click="publishAnnouncement">发布公告</button>
        </div>

        <div v-if="announcements.length > 0" class="announcement-list">
          <article
            v-for="item in announcements"
            :key="item.id"
            class="announcement-item"
          >
            <div class="announcement-title-row">
              <h4>{{ item.title }}</h4>
              <span class="announcement-time">{{ item.created_at }}</span>
            </div>
            <p class="announcement-content">{{ item.content }}</p>
            <p class="announcement-meta">发布人：{{ item.author }}</p>
          </article>
        </div>
        <div v-else class="announcement-empty">暂无公告</div>
      </section>

      <main class="forum-main">
        <div v-if="filteredPosts.length === 0" class="empty-state">
          <p>📭 暂无相关帖子，快来抢沙发吧！</p>
        </div>

        <div class="post-grid">
          <div class="glass-card post-card" v-for="post in filteredPosts" :key="post.id">
            <div class="post-main">
              <h3 class="post-title">{{ post.title }}</h3>
              <div class="post-meta">
                <span class="author">👤 {{ post.author }}</span>
                <span class="time" v-if="post.created_at">🕒 {{ post.created_at }}</span>
              </div>
              <p class="post-content-preview">{{ post.content }}</p>
            </div>

            <div class="post-footer">
              <span :class="['status-badge', post.status]">
                {{ formatStatus(post.status) }}
              </span>
              <div class="actions">
                <button v-if="tab === 'mine' && post.status === 'rejected'" class="btn-edit" @click="handleEditClick(post)">修改</button>
                <button class="btn-detail" @click="openDetailModal(post)">详情</button>
              </div>
            </div>
          </div>
        </div>
      </main>

      <button class="fab-post-btn" title="发布新话题" @click="openPostModal">
        <span class="plus-icon">+</span>
      </button>

      <Transition name="fade">
        <div v-if="showPostModal" class="modal-overlay" @click.self="closePostModal">
          <div class="modal-content glass-card post-modal">
            <button class="close-x" @click="closePostModal">×</button>
            <div class="modal-header">
              <h2>{{ isEditing ? '修改我的话题' : '发布新话题' }}</h2>
              <span class="tip">内容需经管理员审核</span>
            </div>
            <div class="post-form">
              <input v-model="title" class="input-title" placeholder="起个响亮的标题..." />
              <textarea v-model="content" class="input-content" placeholder="分享你的新鲜事..."></textarea>
              <div class="form-footer">
                <button class="btn-submit" @click="submitPost">
                  <span>🚀</span> {{ isEditing ? '保存修改' : '立即提交' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>

      <DetailModal
        :visible="showDetailModal"
        :title="currentPost.title || '帖子详情'"
        :rows="detailRows"
        @close="closeDetailModal"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useUserStore } from '@/store/user'
import DetailModal from '@/components/DetailModal.vue'

const userStore = useUserStore()
const username = computed(() => userStore.username)
const isAdmin = computed(() => userStore.role === 'admin')

// 数据状态
const posts = ref([])
const announcements = ref([])
const keyword = ref('')
const tab = ref('all')
const title = ref('')
const content = ref('')
const announcementForm = ref({
  title: '',
  content: ''
})

// 弹窗状态
const showPostModal = ref(false)
const showDetailModal = ref(false)
const isEditing = ref(false)
const editingPostId = ref(null)
const currentPost = ref({})

// 获取数据
const fetchPosts = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/posts/', {
      params: { username: username.value }
    })
    posts.value = res.data.posts
  } catch (err) {
    console.error("加载帖子失败", err)
  }
}
const fetchAnnouncements = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/announcements/')
    announcements.value = res.data.announcements || []
  } catch (err) {
    console.error('加载公告失败', err)
    announcements.value = []
  }
}
const fetchUserInfo = async () => {
  if (!username.value) return
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/user_info/', {
      username: username.value
    })
    if (res.data?.role) {
      userStore.role = res.data.role
      userStore.points = res.data.points || 0
    }
  } catch (err) {
    console.error('获取用户角色失败', err)
  }
}
const publishAnnouncement = async () => {
  if (!announcementForm.value.title.trim() || !announcementForm.value.content.trim()) {
    return alert('请填写公告标题和内容')
  }

  try {
    const res = await axios.post('http://127.0.0.1:8000/api/create_announcement/', {
      username: username.value,
      title: announcementForm.value.title,
      content: announcementForm.value.content
    })
    if (res.data.code === 200) {
      announcementForm.value.title = ''
      announcementForm.value.content = ''
      fetchAnnouncements()
      alert('公告发布成功')
      return
    }
    alert(res.data.message || '公告发布失败')
  } catch (err) {
    alert(err.response?.data?.message || '公告发布失败，请稍后重试')
  }
}

// 统一的提交逻辑（包含新增和修改）
const submitPost = async () => {
  if(!title.value || !content.value) return alert('请填写完整内容')
  
  try {
    if (isEditing.value) {
      // 执行修改逻辑
      await axios.post('http://127.0.0.1:8000/api/update_post/', {
        id: editingPostId.value,
        title: title.value,
        content: content.value
      })
      alert('修改成功，已重新提交审核')
    } else {
      // 执行发布逻辑
      await axios.post('http://127.0.0.1:8000/api/create_post/', {
        title: title.value,
        content: content.value,
        author: username.value
      })
      alert('发布成功，请等待管理员审核')
    }
    closePostModal()
    await fetchPosts()
  } catch (err) {
    alert('操作失败，请检查网络或后端接口')
  }
}

// 修改按钮点击处理
const handleEditClick = (post) => {
  isEditing.value = true
  editingPostId.value = post.id
  title.value = post.title
  content.value = post.content
  showPostModal.value = true
}

// 弹窗开关控制
const openPostModal = () => {
  isEditing.value = false
  title.value = ''
  content.value = ''
  showPostModal.value = true
}
const closePostModal = () => { showPostModal.value = false }

const openDetailModal = (post) => {
  currentPost.value = post
  showDetailModal.value = true
}
const closeDetailModal = () => { showDetailModal.value = false }
const detailRows = computed(() => {
  return [
    { label: '作者', value: currentPost.value.author },
    {
      label: '状态',
      value: formatStatus(currentPost.value.status),
      badge: true,
      badgeType: currentPost.value.status || 'default'
    },
    {
      label: '发布时间',
      value: currentPost.value.created_at,
      visible: currentPost.value.status !== 'rejected'
    },
    {
      label: '拒绝理由',
      value: currentPost.value.reject_reason,
      visible: currentPost.value.status === 'rejected',
      multiline: true
    },
    { label: '帖子内容', value: currentPost.value.content, multiline: true }
  ]
})

// 格式化函数 (修复报错的关键)
const formatStatus = (status) => {
  const map = { pending: '审核中', approved: '已发布', rejected: '被退回' }
  return map[status] || status
}

// 过滤逻辑
const filteredPosts = computed(() => {
  return posts.value
    .filter(post => {
      if (tab.value === 'all') return post.status === 'approved'
      if (tab.value === 'mine') return post.author === username.value
      return true
    })
    .filter(post => post.title.includes(keyword.value))
})

onMounted(async () => {
  await fetchUserInfo()
  fetchPosts()
  fetchAnnouncements()
})
</script>

<style scoped>
/* --- 全局布局 --- */
.forum-layout-wrapper { display: flex; min-height: 100vh; background-color: #f8fafc; }
.forum-content { flex: 1; margin-left: 260px; padding: 40px; max-width: 1400px; position: relative; }

/* --- 顶部导航 --- */
.forum-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
.search-wrapper { position: relative; flex: 1; max-width: 400px; }
.search-wrapper input { width: 100%; padding: 12px 40px; border-radius: 25px; border: 1px solid #e2e8f0; outline: none; transition: all 0.3s; }
.search-wrapper input:focus { border-color: #3182ce; box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1); }
.search-icon { position: absolute; left: 15px; top: 12px; opacity: 0.4; }
.tabs-pill { display: flex; background: #edf2f7; padding: 4px; border-radius: 30px; }
.tabs-pill button { padding: 8px 20px; border: none; background: transparent; border-radius: 25px; cursor: pointer; font-weight: 600; color: #718096; transition: all 0.3s; }
.tabs-pill button.active { background: white; color: #3182ce; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }

/* --- 公告板块 --- */
.announcement-board {
  background: white;
  border-radius: 20px;
  padding: 24px;
  border: 1px solid rgba(0, 0, 0, 0.02);
  margin-bottom: 28px;
}

.board-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.board-header h3 {
  margin: 0;
  font-size: 20px;
  color: #2d3748;
}

.announcement-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 18px;
}

.announcement-title-input,
.announcement-content-input {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px 12px;
  outline: none;
  transition: all 0.2s;
}

.announcement-content-input {
  min-height: 90px;
  resize: vertical;
}

.announcement-title-input:focus,
.announcement-content-input:focus {
  border-color: #3182ce;
  box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
}

.btn-submit-announcement {
  align-self: flex-end;
  background: #3182ce;
  color: white;
  border: none;
  border-radius: 10px;
  padding: 8px 16px;
  font-weight: 600;
  cursor: pointer;
}

.announcement-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.announcement-item {
  padding: 14px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #edf2f7;
}

.announcement-title-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 6px;
}

.announcement-title-row h4 {
  margin: 0;
  color: #1a365d;
}

.announcement-time {
  color: #718096;
  font-size: 12px;
  white-space: nowrap;
}

.announcement-content {
  margin: 0;
  color: #2d3748;
  white-space: pre-wrap;
  line-height: 1.7;
}

.announcement-meta {
  margin: 8px 0 0;
  color: #718096;
  font-size: 12px;
}

.announcement-empty {
  color: #a0aec0;
  padding: 8px 2px;
}

/* --- 帖子网格 --- */
.post-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 25px; }
.post-card { background: white; border-radius: 20px; padding: 25px; border: 1px solid rgba(0,0,0,0.02); transition: all 0.3s; display: flex; flex-direction: column; justify-content: space-between;}
.post-card:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.05); }
.post-title { font-size: 18px; color: #2d3748; margin-bottom: 8px; font-weight: 700; }
.post-meta { font-size: 13px; color: #a0aec0; margin-bottom: 15px; display: flex; gap: 15px; }
.post-content-preview { color: #4a5568; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 20px; }
.post-footer { display: flex; justify-content: space-between; align-items: center; padding-top: 15px; border-top: 1px solid #f7fafc; }

/* --- 状态标签 --- */
.status-badge { font-size: 11px; padding: 4px 10px; border-radius: 20px; font-weight: 700; }
.status-badge.pending { background: #fffbeb; color: #b7791f; }
.status-badge.approved { background: #f0fff4; color: #38a169; }
.status-badge.rejected { background: #fff5f5; color: #e53e3e; }

/* --- 发帖弹窗样式 --- */
.post-modal {
  width: 500px; 
  max-width: 90vw; 
  padding: 40px; 
  background: #ffffff; /* 🚀 核心修复：确保有白色背景 */
  border-radius: 28px; 
  box-shadow: 0 20px 50px rgba(0,0,0,0.15); 
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.5);
}

.modal-header h2 { font-size: 24px; color: #1a365d; text-align: center; margin-bottom: 20px; }
.form-footer { margin-top: 30px; display: flex; justify-content: center; }

/* --- 按钮系列 --- */
.btn-submit { 
  padding: 12px 60px; 
  background: #3182ce; 
  color: white; 
  border: none; 
  border-radius: 12px; 
  font-weight: 600; 
  cursor: pointer; 
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(49, 130, 206, 0.2);
}
.btn-submit:hover { background: #2b6cb0; transform: translateY(-2px); }

/* --- 发帖悬浮按钮 --- */
.fab-post-btn { position: fixed; right: 50px; bottom: 50px; width: 60px; height: 60px; background: #3182ce; color: white; border-radius: 50%; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 20px rgba(49,130,206,0.3); z-index: 100; transition: transform 0.3s;}
.fab-post-btn:hover { transform: scale(1.1); }
.plus-icon { font-size: 30px; }

/* --- 基础动画与遮罩 --- */
.modal-overlay { 
  position: fixed; 
  inset: 0; 
  background: rgba(0,0,0,0.4); 
  backdrop-filter: blur(8px); 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  z-index: 1000; 
}

.close-x { position: absolute; right: 25px; top: 25px; background: none; border: none; font-size: 24px; cursor: pointer; color: #a0aec0; transition: color 0.2s; }
.close-x:hover { color: #4a5568; }

.tip { font-size: 12px; color: #a0aec0; display: block; text-align: center; margin-bottom: 20px; margin-top: -10px; }

/* --- 表单输入样式 --- */
.input-title { width: 100%; font-size: 18px; font-weight: 700; border: none; border-bottom: 2px solid #edf2f7; padding: 10px 0; margin-bottom: 15px; outline: none; transition: border-color 0.3s; }
.input-title:focus { border-color: #3182ce; }
.input-content { width: 100%; min-height: 180px; border: 1px solid #edf2f7; border-radius: 15px; padding: 15px; resize: none; outline: none; background: #f8fafc; font-family: inherit; font-size: 15px; transition: border-color 0.3s; }
.input-content:focus { border-color: #3182ce; background: white; }

/* --- 其他 --- */
.empty-state { text-align: center; padding: 100px; color: #a0aec0; width: 100%; }
.btn-detail, .btn-edit { padding: 8px 18px; border-radius: 8px; border: 1px solid #e2e8f0; background: #f7fafc; cursor: pointer; font-size: 13px; transition: all 0.2s; font-weight: 600; color: #4a5568; }
.btn-detail:hover { border-color: #3182ce; color: #3182ce; background: white; }
.btn-edit { background: #fff5f5; color: #e53e3e; border: none; margin-right: 5px; }
.btn-edit:hover { background: #feb2b2; }

.fade-enter-active, .fade-leave-active { transition: all 0.3s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(20px); }
</style>
