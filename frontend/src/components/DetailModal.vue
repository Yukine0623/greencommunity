<template>
  <Transition name="fade">
    <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-content glass-card detail-modal" :style="{ width, maxWidth }">
        <div class="detail-header">
          <h3 class="modal-title">{{ title }}</h3>
          <button class="detail-close" @click="$emit('close')">×</button>
        </div>

        <div class="detail-body">
        <div
          v-for="(row, index) in normalizedRows"
          :key="`${row.label}-${index}`"
          class="detail-row"
        >
          <span class="detail-label">{{ row.label }}</span>
          <span
            v-if="row.badge"
            :class="['detail-badge', `badge-${row.badgeType || 'default'}`]"
          >
            {{ formatValue(row.value) }}
          </span>
          <span
            v-else
            :class="['detail-value', row.multiline ? 'detail-multiline' : '']"
          >
            {{ formatValue(row.value) }}
          </span>
        </div>
      </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="$emit('close')">{{ closeText }}</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '详情'
  },
  rows: {
    type: Array,
    default: () => []
  },
  closeText: {
    type: String,
    default: '关闭'
  },
  width: {
    type: String,
    default: '620px'
  },
  maxWidth: {
    type: String,
    default: '92vw'
  }
})

defineEmits(['close'])

const normalizedRows = computed(() => {
  return props.rows.filter((row) => row && row.visible !== false)
})

const formatValue = (value) => {
  if (value === 0 || value === false) return String(value)
  if (value === null || value === undefined || value === '') return '暂无'
  return String(value)
}
</script>

<style scoped>
.glass-card {
  background: white;
  border-radius: 20px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 16px;
}

.detail-modal {
  padding: 30px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-title {
  margin: 0;
  color: #2d3748;
}

.detail-close {
  background: transparent;
  border: none;
  font-size: 28px;
  color: #718096;
  cursor: pointer;
  line-height: 1;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 64vh;
  overflow-y: auto;
}

.detail-row {
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 12px;
  align-items: start;
  padding: 12px 0;
  border-bottom: 1px solid #edf2f7;
}

.detail-label {
  color: #718096;
  font-weight: 600;
}

.detail-value {
  color: #2d3748;
  word-break: break-word;
}

.detail-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  min-width: 72px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.4;
}

.badge-default {
  background: #f1f5f9;
  color: #475569;
}

.badge-pending,
.badge-auditing {
  background: #fffbeb;
  color: #b45309;
}

.badge-approved,
.badge-finished {
  background: #f0fdf4;
  color: #15803d;
}

.badge-rejected {
  background: #fef2f2;
  color: #b91c1c;
}

.badge-accepted {
  background: #e0f2fe;
  color: #0369a1;
}

.badge-submitted,
.badge-intervention {
  background: #eef2ff;
  color: #4338ca;
}

.detail-multiline {
  white-space: pre-wrap;
  line-height: 1.7;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}

.btn-cancel {
  background: #edf2f7;
  color: #4a5568;
  border: none;
  padding: 10px 25px;
  border-radius: 10px;
  cursor: pointer;
}

.fade-enter-active,
.fade-leave-active {
  transition: 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
