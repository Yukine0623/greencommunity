<template>
  <div v-if="modelValue" class="overlay" @click.self="close">
    <div class="modal">
      <slot />
      <button @click="close">关闭</button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps(['modelValue'])
const emit = defineEmits(['update:modelValue'])

const close = () => {
  emit('update:modelValue', false)
}
</script>