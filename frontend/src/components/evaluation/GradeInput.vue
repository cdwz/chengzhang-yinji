<template>
  <div class="grade-input">
    <button
      v-for="g in grades"
      :key="g"
      class="grade-btn"
      :class="{ active: modelValue === g, [g.toLowerCase()]: modelValue === g }"
      @click="$emit('update:modelValue', g === modelValue ? '' : g)"
    >{{ g }}</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ modelValue: string }>()
defineEmits<{ 'update:modelValue': [v: string] }>()
const grades = ['A', 'B', 'C', 'D']
</script>

<style scoped>
.grade-input { display: flex; gap: 10px; }
.grade-btn {
  width: 52px; height: 44px; border-radius: 8px; border: 2px solid #dcdfe6;
  background: #fff; font-size: 18px; font-weight: 600; cursor: pointer; transition: all .15s;
}
.grade-btn.active { border-color: transparent; color: #fff; }
.grade-btn.a { background: #07c160; }
.grade-btn.b { background: #3e7dc9; }
.grade-btn.c { background: #ff976a; }
.grade-btn.d { background: #ee0a24; }
</style>
