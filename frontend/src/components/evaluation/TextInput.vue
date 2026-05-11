<template>
  <div class="text-input">
    <van-field v-model="text" type="textarea" rows="2" placeholder="输入备注..." @update:model-value="$emit('update:modelValue', $event)" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{ modelValue: string }>()
defineEmits<{ 'update:modelValue': [v: string] }>()
const text = ref(props.modelValue || '')
watch(() => props.modelValue, v => { text.value = v || '' })
</script>

<style scoped>
.text-input { width: 100%; }
</style>
