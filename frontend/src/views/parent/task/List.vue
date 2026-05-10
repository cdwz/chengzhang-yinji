<template>
  <div class="parent-tasks">
    <div class="task-cards">
      <div v-for="task in tasks" :key="task.id" class="task-card">
        <div class="task-card-header">
          <span class="task-card-title">{{ task.title }}</span>
          <van-tag type="primary" size="small">选做</van-tag>
        </div>
        <div class="task-card-content">
          {{ task.content || '暂无详细说明' }}
        </div>
        <div class="task-card-footer">
          <span>{{ task.subject }}</span>
          <span v-if="task.suggested_duration">
            建议时长：{{ task.suggested_duration }}分钟
          </span>
        </div>
        <div class="task-card-actions">
          <van-button type="primary" size="small" block @click="goToTask(task.id)">
            拍照记录
          </van-button>
        </div>
      </div>
      
      <van-empty v-if="!loading && tasks.length === 0" description="暂无学习建议" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { http } from '@/utils/request'
import type { Task } from '@/api/types'

const router = useRouter()
const loading = ref(false)
const tasks = ref<Task[]>([])

onMounted(() => {
  loadTasks()
})

async function loadTasks() {
  loading.value = true
  try {
    const res = await http.get<Task[]>('/tasks')
    tasks.value = res
  } catch (error) {
    console.error('加载任务列表失败', error)
  } finally {
    loading.value = false
  }
}

function goToTask(id: string) {
  router.push(`/parent/tasks/${id}`)
}
</script>

<style scoped lang="scss">
.parent-tasks {
  .task-cards {
    .task-card {
      background: #fff;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 12px;
      
      &-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }
      
      &-title {
        font-size: 16px;
        font-weight: 500;
        color: #303133;
      }
      
      &-content {
        color: #606266;
        font-size: 14px;
        line-height: 1.6;
        margin-bottom: 12px;
      }
      
      &-footer {
        display: flex;
        justify-content: space-between;
        color: #909399;
        font-size: 12px;
        margin-bottom: 12px;
      }
      
      &-actions {
        margin-top: 8px;
      }
    }
  }
}
</style>
