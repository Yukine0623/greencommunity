<template>
  <button
    :class="['btn', type]"
    :disabled="disabled"
    @click="handleClick"
  >
    <slot />
  </button>
</template>

<script setup>
const props = defineProps({
  type: String,
  disabled: Boolean
})

const emit = defineEmits(['click'])

const handleClick = () => {
  if (props.disabled) return
  emit('click')
}
</script>