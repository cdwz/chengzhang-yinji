<template>
  <div class="parent-tasks">
    <!-- 班级信息卡片 -->
    <div class="class-info-card" v-if="studentInfo">
      <div class="class-name">{{ displayClassName }}</div>
      <div class="student-info">
        <span class="student-name">{{ studentInfo.name }}</span>
      </div>
    </div>
    
    <!-- 任务标签页 -->
    <van-tabs v-model:active="activeTab" sticky>
      <van-tab :title="`待完成 (${pendingTasks.length})`">
        <div class="task-cards">
          <div v-for="task in pendingTasks" :key="task.id" class="task-card">
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
                type="primary" 
                size="small" 
                block 
                @click="goToTask(task.id)"
              >
                拍照记录
              </van-button>
            </div>
          </div>
          
          <van-empty v-if="!loading && pendingTasks.length === 0" description="暂无待完成任务" />
        </div>
      </van-tab>
      
      <van-tab :title="`已完成 (${completedTasks.length})`">
        <div class="task-cards">
          <div v-for="task in completedTasks" :key="task.id" class="task-card completed">
            <div class="task-card-header">
              <span class="task-card-title">{{ task.title }}</span>
              <van-tag type="success">已提交</van-tag>
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
                type="default" 
                size="small" 
                block 
                @click="goToTask(task.id)"
              >
                查看详情
              </van-button>
            </div>
          </div>
          
          <van-empty v-if="!loading && completedTasks.length === 0" description="暂无已完成任务" />
        </div>
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { http } from '@/utils/request'
import type { Task } from '@/api/types'

const router = useRouter()
const loading = ref(false)
const tasks = ref<Task[]>([])
const studentInfo = ref<any>(null)
const submissionMap = ref<Map<string, { submitted: boolean; hasAnnotation: boolean }>>(new Map())
const activeTab = ref(0)

// 计算班级显示名称：优先昵称，否则显示"年级+班级"
const displayClassName = computed(() => {
  if (!studentInfo.value) return ''
  // 优先显示班级自定义昵称
  if (studentInfo.value.class_nickname) {
    return studentInfo.value.class_nickname
  }
  // 否则显示"年级+班级"
  const grade = studentInfo.value.grade_name || ''
  const className = studentInfo.value.class_name || ''
  return `${grade}${className}`
})

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
    const map = new Map<string, { submitted: boolean; hasAnnotation: boolean }>()
    for (const sub of submissions) {
      map.set(sub.task_id, { 
        submitted: true, 
        hasAnnotation: sub.has_teacher_annotation || false 
      })
    }
    submissionMap.value = map
  } catch (error) {
    console.error('加载任务列表失败', error)
  } finally {
    loading.value = false
  }
}

// 检查是否是周末
const isWeekend = computed(() => {
  const today = new Date()
  const day = today.getDay() // 0=周日, 1=周一, ..., 6=周六
  return day === 0 || day === 6 // 周六或周日
})

// 检查是否是节假日
const isHoliday = computed(() => {
  const today = new Date()
  const year = today.getFullYear()
  const month = today.getMonth() + 1
  const day = today.getDate()
  
  // 简单的节假日列表（示例）
  const holidays = [
    `${year}-01-01`, // 元旦
    `${year}-02-10`, // 春节（示例日期，实际每年不同）
    `${year}-02-11`,
    `${year}-02-12`,
    `${year}-04-04`, // 清明节（示例）
    `${year}-05-01`, // 劳动节
    `${year}-06-10`, // 端午节（示例）
    `${year}-09-17`, // 中秋节（示例）
    `${year}-10-01`, // 国庆节
    `${year}-10-02`,
    `${year}-10-03`,
  ]
  
  const todayStr = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`
  return holidays.includes(todayStr)
})

// 待完成任务：未提交的任务
const pendingTasks = computed(() => {
  return tasks.value.filter(task => {
    // 检查是否已提交
    if (submissionMap.value.has(task.id)) return false
    
    // 检查周末过滤
    if (isWeekend.value && task.weekend_required === false) {
      return false
    }
    
    // 检查节假日过滤
    if (isHoliday.value && task.holiday_required === false) {
      return false
    }
    
    return true
  })
})

// 已完成任务：已提交且已批改的任务
const completedTasks = computed(() => {
  return tasks.value.filter(task => {
    const subInfo = submissionMap.value.get(task.id)
    return subInfo && subInfo.submitted
  })
})

function goToTask(id: string) {
  router.push(`/parent/tasks/${id}`)
}
</script>

<style scoped lang="scss">
.parent-tasks {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 60px;
  
  .class-info-card {
    background: linear-gradient(135deg, #1677ff 0%, #40a9ff 100%);
    color: white;
    padding: 20px;
    margin-bottom: 12px;
    
    .class-name {
      font-size: 18px;
      font-weight: 500;
      margin-bottom: 8px;
    }
    
    .student-info {
      display: flex;
      gap: 12px;
      font-size: 14px;
      opacity: 0.9;
    }
  }
  
  :deep(.van-tabs__wrap) {
    background: #fff;
  }
  
  .task-cards {
    padding: 12px;
    
    .task-card {
      background: white;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 12px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
      
      &.completed {
        opacity: 0.8;
      }
      
      .task-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        
        .task-card-title {
          font-size: 16px;
          font-weight: 500;
          color: #333;
        }
      }
      
      .task-card-content {
        font-size: 14px;
        color: #666;
        line-height: 1.5;
        margin-bottom: 12px;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
      
      .task-card-footer {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        color: #999;
        margin-bottom: 12px;
      }
      
      .task-card-actions {
        :deep(.van-button) {
          border-radius: 4px;
        }
      }
    }
  }
}
</style>
