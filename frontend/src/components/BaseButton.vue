<template>
  <button class="btn" @click="$emit('click')">
    <slot />
  </button>
</template>