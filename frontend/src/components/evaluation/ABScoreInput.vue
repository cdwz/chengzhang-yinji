<template>
  <div class="ab-score-input">
    <div class="ab-row">
      <span class="ab-label">A卷</span>
      <van-stepper v-model="aVal" :min="0" :max="aMax" input-width="60px" @change="calc" />
      <span class="ab-max">/ {{ aMax }}</span>
    </div>
    <div class="ab-row">
      <span class="ab-label">B卷</span>
      <van-stepper v-model="bVal" :min="0" :max="bMax" input-width="60px" @change="calc" />
      <span class="ab-max">/ {{ bMax }}</span>
    </div>
    <div class="ab-total">
      总分：<b>{{ aVal + bVal }}</b> / {{ total }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue: string
  total: number
  aMax: number
  bMax: number
}>()
const emit = defineEmits<{ 'update:modelValue': [v: string] }>()

const aVal = ref(0)
const bVal = ref(0)

// 解析初始值
watch(() => props.modelValue, v => {
  if (v && v.includes('/')) {
    const [a, b] = v.split('/').map(Number)
    aVal.value = a || 0
    bVal.value = b || 0
  }
}, { immediate: true })

function calc() {
  emit('update:modelValue', `${aVal.value}/${bVal.value}`)
}
</script>

<style scoped>
.ab-score-input { display: flex; flex-direction: column; gap: 8px; }
.ab-row { display: flex; align-items: center; gap: 8px; }
.ab-label { width: 36px; font-weight: 500; }
.ab-max { color: #909399; font-size: 13px; }
.ab-total { padding-top: 4px; font-size: 14px; }
.ab-total b { color: #3e7dc9; font-size: 18px; }
</style>
