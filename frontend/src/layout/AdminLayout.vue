<template>
  <div class="container">
    <AdminSidebar />
    <div class="main">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import AdminSidebar from '@/components/AdminSidebar.vue'
</script>

<style>
.container {
  display: flex;
  height: 100vh;
}

.main {
  flex: 1;
  background: #f5f7fa;
  padding: 20px;
}
</style>