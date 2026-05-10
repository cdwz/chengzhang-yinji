<template>
  <div class="task-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>学习任务</span>
          <el-button type="primary" @click="$router.push('/teacher/tasks/create')">
            发布任务
          </el-button>
        </div>
      </template>
      
      <el-table :data="tasks" v-loading="loading">
        <el-table-column prop="title" label="任务标题" />
        <el-table-column prop="subject" label="科目" width="100" />
        <el-table-column prop="task_date" label="日期" width="120" />
        <el-table-column prop="suggested_duration" label="建议时长" width="100">
          <template #default="{ row }">
            {{ row.suggested_duration ? `${row.suggested_duration}分钟` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_optional" label="性质" width="80">
          <template #default>
            <el-tag type="info" size="small">选做</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default>
            <el-button link type="primary">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { http } from '@/utils/request'
import type { Task } from '@/api/types'

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
</script>

<style scoped lang="scss">
.task-list {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
