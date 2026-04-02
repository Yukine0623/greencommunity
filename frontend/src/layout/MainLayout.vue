<template>
  <div class="container">
    <Sidebar />

    <div class="main">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import Sidebar from '@/components/Sidebar.vue'
</script>

<style>
.layout-container {
  display: flex;
  min-height: 100vh;
  background-color: #f5f7fa; /* 给右侧主背景一个浅灰色，衬托出侧边栏的深色 */
}

.main-content {
  flex: 1; /* 自动填充剩余空间 */
  
  /* 🚀 关键代码：必须等于 Sidebar 的宽度 */
  margin-left: 260px; 
  
  padding: 30px;
  box-sizing: border-box;
  transition: all 0.3s ease; /* 增加平滑过渡 */
}
</style>