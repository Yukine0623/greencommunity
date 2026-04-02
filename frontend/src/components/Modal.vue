<template>
  <div v-if="modelValue" class="overlay" @click="handleClose">
    <div class="modal" @click.stop>
      
      <h3>{{ title }}</h3>

      <!-- 内容插槽 -->
      <div class="content">
        <slot />
      </div>

      <!-- 按钮 -->
      <div class="actions">
        <button @click="handleCancel">取消</button>
        <button @click="handleConfirm">确定</button>
      </div>

    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: Boolean,
  title: String
})

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const handleClose = () => {
  emit('update:modelValue', false)
}

const handleCancel = () => {
  emit('cancel')
  handleClose()
}

const handleConfirm = () => {
  emit('confirm')
  handleClose()
}
</script>

<style>
.overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);

  display: flex;
  justify-content: center;
  align-items: center;
}

.modal {
  background: white;
  padding: 20px;
  border-radius: 10px;
  width: 300px;
}

.actions {
  margin-top: 20px;
  text-align: right;
}
</style>