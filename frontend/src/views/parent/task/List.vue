<template>
  <div class="parent-tasks">
    <!-- 班级信息卡片 -->
    <div class="class-info-card" v-if="studentInfo">
      <div class="class-name">{{ studentInfo.class_name }}</div>
      <div class="student-info">
        <span class="student-name">{{ studentInfo.name }}</span>
        <span class="grade-name">{{ studentInfo.grade_name }}</span>
      </div>
    </div>
    
    <div class="task-cards">
      <div v-for="task in tasks" :key="task.id" class="task-card">
        <div class="task-card-header">
          <span class="task-card-title">{{ task.title }}</span>
          <van-tag type="primary">选做</van-tag>
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
          <van-button 
            :type="isSubmitted(task.id) ? 'default' : 'primary'" 
            size="small" 
            block 
            @click="goToTask(task.id)"
          >
            {{ isSubmitted(task.id) ? '已提交 ✓' : '拍照记录' }}
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
const studentInfo = ref<any>(null)
const submissionMap = ref<Map<string, boolean>>(new Map())

onMounted(() => {
  loadStudentInfo()
  loadTasks()
})

async function loadStudentInfo() {
  try {
    const data = await http.get<any[]>('/students/my')
    if (data && data.length > 0) {
      studentInfo.value = data[0]
    }
  } catch (error) {
    console.error('加载学生信息失败', error)
  }
}

async function loadTasks() {
  loading.value = true
  try {
    // 加载任务列表
    const res = await http.get<Task[]>('/tasks')
    tasks.value = res
    
    // 加载已提交记录
    const submissions = await http.get<any[]>('/tasks/my-submissions')
    const map = new Map<string, boolean>()
    for (const sub of submissions) {
      map.set(sub.task_id, true)
    }
    submissionMap.value = map
  } catch (error) {
    console.error('加载任务列表失败', error)
  } finally {
    loading.value = false
  }
}

function isSubmitted(taskId: string): boolean {
  return submissionMap.value.has(taskId)
}

function goToTask(id: string) {
  router.push(`/parent/tasks/${id}`)
}
</script>

<style scoped lang="scss">
.parent-tasks {
  .class-info-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
    color: #fff;
    
    .class-name {
      font-size: 20px;
      font-weight: 600;
      margin-bottom: 4px;
    }
    
    .student-info {
      font-size: 14px;
      opacity: 0.9;
      
      .student-name {
        margin-right: 8px;
      }
      
      .grade-name {
        opacity: 0.8;
      }
    }
  }
  
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
