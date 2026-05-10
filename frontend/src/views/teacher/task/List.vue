<template>
  <div class="task-list">
    <!-- 统计概览 -->
    <TaskStats :class-id="selectedClassId" />

    <!-- 筛选栏 -->
    <van-cell-group inset class="filter-section">
      <van-field
        v-model="selectedDate"
        is-link
        readonly
        label="日期"
        placeholder="选择日期"
        @click="showDatePicker = true"
      />
      <van-field
        v-model="selectedClass"
        is-link
        readonly
        label="班级"
        placeholder="选择班级"
        @click="showClassPicker = true"
      />
    </van-cell-group>

    <!-- 任务列表 -->
    <div class="section-title">任务列表</div>
    
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="loadTasks"
      >
        <van-cell-group inset>
          <van-swipe-cell v-for="task in tasks" :key="task.id">
            <van-cell :title="task.title" :label="getTaskLabel(task)" is-link @click="viewTask(task)">
              <template #icon>
                <van-icon name="description" size="20" style="margin-right: 8px;" />
              </template>
              <template #value>
                <van-tag :type="getTaskTagType(task)">{{ task.subject }}</van-tag>
              </template>
            </van-cell>
            <template #right>
              <van-button square type="danger" text="删除" @click="deleteTask(task.id)" />
            </template>
          </van-swipe-cell>
        </van-cell-group>
      </van-list>
    </van-pull-refresh>

    <!-- 发布任务按钮 -->
    <van-floating-bubble
      icon="plus"
      @click="$router.push('/teacher/tasks/create')"
    />

    <!-- 日期选择器 -->
    <van-popup v-model:show="showDatePicker" position="bottom" round>
      <van-date-picker
        v-model="datePickerValue"
        title="选择日期"
        @confirm="onDateConfirm"
        @cancel="showDatePicker = false"
      />
    </van-popup>

    <!-- 班级选择器 -->
    <van-popup v-model:show="showClassPicker" position="bottom" round>
      <van-picker
        :columns="classColumns"
        title="选择班级"
        @confirm="onClassConfirm"
        @cancel="showClassPicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast, showFailToast, showConfirmDialog } from 'vant'
import { getTasks, deleteTask as deleteTaskApi } from '@/api/tasks'
import { getClasses } from '@/api/schools'
import type { Task, Class } from '@/api/types'
import TaskStats from '@/components/TaskStats.vue'

const router = useRouter()

// 状态
const loading = ref(false)
const refreshing = ref(false)
const finished = ref(false)
const tasks = ref<Task[]>([])
const classes = ref<Class[]>([])

// 筛选
const selectedDate = ref('')
const selectedClass = ref('')
const selectedClassId = ref('')
const showDatePicker = ref(false)
const showClassPicker = ref(false)
const datePickerValue = ref(['2024', '01', '01'])

// 班级选择器列
const classColumns = computed(() => {
  const cols = [{ text: '全部班级', value: '' }]
  classes.value.forEach(c => {
    cols.push({ text: c.name, value: c.id })
  })
  return cols
})

// 加载任务列表
const loadTasks = async () => {
  try {
    const params: any = {}
    if (selectedClassId.value) {
      params.class_id = selectedClassId.value
    }
    if (selectedDate.value) {
      params.task_date = selectedDate.value
    }
    
    const res = await getTasks(params)
    tasks.value = res
    finished.value = true
  } catch (error) {
    showFailToast('加载失败')
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

// 加载班级列表
const loadClasses = async () => {
  try {
    classes.value = await getClasses()
  } catch (error) {
    console.error('加载班级列表失败', error)
  }
}

// 下拉刷新
const onRefresh = () => {
  finished.value = false
  loadTasks()
}

// 查看任务详情
const viewTask = (task: Task) => {
  // 可以跳转到任务详情或统计页面
  router.push(`/teacher/tasks/${task.id}/stats`)
}

// 删除任务
const deleteTask = async (taskId: string) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: '删除后无法恢复，确定要删除这个任务吗？'
    })
    
    await deleteTaskApi(taskId)
    showSuccessToast('删除成功')
    tasks.value = tasks.value.filter(t => t.id !== taskId)
  } catch (error) {
    if (error !== 'cancel') {
      showFailToast('删除失败')
    }
  }
}

// 获取任务标签
const getTaskLabel = (task: Task) => {
  const parts = [task.task_date]
  if (task.suggested_duration) {
    parts.push(`${task.suggested_duration}分钟`)
  }
  if (task.group_name) {
    parts.push(task.group_name)
  }
  return parts.join(' · ')
}

// 获取标签类型
const getTaskTagType = (task: Task): 'default' | 'primary' | 'success' | 'warning' | 'danger' => {
  const types: Record<string, string> = {
    '语文': 'primary',
    '数学': 'success',
    '英语': 'warning',
    '科学': 'danger'
  }
  return (types[task.subject] as 'default' | 'primary' | 'success' | 'warning' | 'danger') || 'default'
}

// 日期确认
const onDateConfirm = ({ selectedValues }: any) => {
  selectedDate.value = selectedValues.join('-')
  showDatePicker.value = false
  loadTasks()
}

// 班级确认
const onClassConfirm = ({ selectedOptions }: any) => {
  const selected = selectedOptions[0]
  selectedClass.value = selected.text
  selectedClassId.value = selected.value
  showClassPicker.value = false
  loadTasks()
}

// 初始化
onMounted(async () => {
  await loadClasses()
  await loadTasks()
})
</script>

<style scoped lang="scss">
.task-list {
  padding: 12px;
  padding-bottom: 80px;
  
  .filter-section {
    margin: 12px 0;
  }
  
  .section-title {
    padding: 12px;
    font-size: 14px;
    font-weight: 500;
    color: #969799;
  }
  
  :deep(.van-floating-bubble) {
    background: linear-gradient(135deg, #3e7dc9 0%, #6db3f2 100%);
  }
}
</style>
