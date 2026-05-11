<template>
  <div class="boolean-input">
    <button class="bool-btn done" :class="{ active: modelValue === '完成' }" @click="$emit('update:modelValue', modelValue === '完成' ? '' : '完成')">✓ 完成</button>
    <button class="bool-btn undone" :class="{ active: modelValue === '未完成' }" @click="$emit('update:modelValue', modelValue === '未完成' ? '' : '未完成')">✗ 未完成</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ modelValue: string }>()
defineEmits<{ 'update:modelValue': [v: string] }>()
</script>

<style scoped>
.boolean-input { display: flex; gap: 12px; }
.bool-btn {
  flex: 1; height: 44px; border-radius: 8px; border: 2px solid #dcdfe6;
  background: #fff; font-size: 15px; cursor: pointer; transition: all .15s;
}
.bool-btn.done.active { background: #07c160; color: #fff; border-color: #07c160; }
.bool-btn.undone.active { background: #909399; color: #fff; border-color: #909399; }
</style>
