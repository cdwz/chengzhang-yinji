<template>
  <div class="star-input">
    <span
      v-for="n in 5"
      :key="n"
      class="star"
      :class="{ active: n <= modelValue }"
      @click="$emit('update:modelValue', n === modelValue ? 0 : n)"
    >★</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{ modelValue: number }>()
defineEmits<{ 'update:modelValue': [v: number] }>()
</script>

<style scoped>
.star-input { display: flex; gap: 8px; }
.star { font-size: 28px; color: #dcdfe6; cursor: pointer; transition: color .15s; user-select: none; }
.star.active { color: #f7ba2a; }
</style>
