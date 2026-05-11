<template>
  <div class="score-input">
    <div v-if="scoreType === '10'" class="score-buttons">
      <button v-for="n in 11" :key="n-1" class="score-btn" :class="{ active: modelValue === String(n-1) }"
        @click="$emit('update:modelValue', String(n-1))">{{ n-1 }}</button>
    </div>
    <div v-else-if="scoreType === '100'" class="score-buttons compact">
      <button v-for="n in [100,95,90,85,80,75,70,60,50,40,30,20,10,0]" :key="n" class="score-btn sm"
        :class="{ active: modelValue === String(n) }" @click="$emit('update:modelValue', String(n))">{{ n }}</button>
    </div>
    <div v-else class="score-custom">
      <van-stepper v-model="inputVal" :min="0" :max="maxScore" @change="onInput" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{ modelValue: string; scoreType: string; maxScore: number }>()
const emit = defineEmits<{ 'update:modelValue': [v: string] }>()

const inputVal = ref(Number(props.modelValue) || 0)
watch(() => props.modelValue, v => { inputVal.value = Number(v) || 0 })

function onInput(v: number | string) {
  emit('update:modelValue', String(v))
}
</script>

<style scoped>
.score-buttons { display: flex; flex-wrap: wrap; gap: 6px; }
.score-btn {
  min-width: 36px; height: 36px; border-radius: 6px; border: 1.5px solid #dcdfe6;
  background: #fff; font-size: 14px; cursor: pointer; transition: all .15s;
}
.score-btn.sm { min-width: 42px; font-size: 13px; }
.score-btn.active { background: #3e7dc9; color: #fff; border-color: #3e7dc9; }
.score-custom { display: flex; align-items: center; }
</style>
