<template>
  <div class="task-list">
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
        v-model="selectedClassLabel"
        is-link
        readonly
        label="班级"
        placeholder="选择班级"
        @click="showClassPicker = true"
      />
      <van-field
        v-model="selectedSubject"
        is-link
        readonly
        label="科目"
        placeholder="全部科目"
        @click="showSubjectPicker = true"
      />
      <van-field
        v-model="selectedGroupLabel"
        is-link
        readonly
        label="组别"
        placeholder="全部组别"
        @click="showGroupPicker = true"
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
            <van-cell :title="task.title" :label="getTaskLabel(task)" is-link @click="viewSubmissions(task)">
              <template #icon>
                <van-tag :color="getSubjectColor(task.subject)" size="medium" style="margin-right: 8px;">
                  {{ task.subject }}
                </van-tag>
              </template>
              <template #value>
                <div class="task-stats">
                  <span class="stat-text">{{ task.submission_count }}/{{ task.total_student_count }}</span>
                  <van-progress
                    :percentage="task.total_student_count > 0 ? Math.round(task.submission_count / task.total_student_count * 100) : 0"
                    :stroke-width="4"
                    :show-pivot="false"
                    color="#3e7dc9"
                    style="width: 40px"
                  />
                </div>
              </template>
            </van-cell>
            <template #right>
              <van-button square type="primary" text="编辑" @click="editTask(task)" />
              <van-button square type="danger" text="删除" @click="deleteTask(task.id)" />
            </template>
          </van-swipe-cell>
        </van-cell-group>
        
        <van-empty v-if="!loading && tasks.length === 0" description="暂无任务" />
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

    <!-- 科目选择器 -->
    <van-popup v-model:show="showSubjectPicker" position="bottom" round>
      <van-picker
        :columns="subjectColumns"
        title="选择科目"
        @confirm="onSubjectConfirm"
        @cancel="showSubjectPicker = false"
      />
    </van-popup>

    <!-- 组别选择器 -->
    <van-popup v-model:show="showGroupPicker" position="bottom" round>
      <van-picker
        :columns="groupColumns"
        title="选择组别"
        @confirm="onGroupConfirm"
        @cancel="showGroupPicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast, showFailToast, showConfirmDialog } from 'vant'
import { getTasks, deleteTask as deleteTaskApi } from '@/api/tasks'
import { getClasses } from '@/api/schools'
import { http } from '@/utils/request'
import { SUBJECT_COLORS } from '@/constants'
import type { Task, Class, StudyGroup } from '@/api/types'

const router = useRouter()

// 状态
const loading = ref(false)
const refreshing = ref(false)
const finished = ref(false)
const tasks = ref<Task[]>([])
const classes = ref<Class[]>([])
const studyGroups = ref<StudyGroup[]>([])

// 筛选
const selectedDate = ref('')
const selectedClassLabel = ref('')
const selectedClassId = ref('')
const selectedSubject = ref('')
const selectedGroupLabel = ref('')
const selectedGroupId = ref('')

// 弹窗控制
const showDatePicker = ref(false)
const showClassPicker = ref(false)
const showSubjectPicker = ref(false)
const showGroupPicker = ref(false)
const datePickerValue = ref(['2024', '01', '01'])

// 可用科目列表
const availableSubjects = computed(() => {
  const cls = classes.value.find(c => c.id === selectedClassId.value)
  return cls?.subjects || ['语文', '数学', '英语']
})

// 班级选择器列
const classColumns = computed(() => {
  const cols = [{ text: '全部班级', value: '' }]
  classes.value.forEach(c => {
    cols.push({ text: c.name, value: c.id })
  })
  return cols
})

// 科目选择器列
const subjectColumns = computed(() => {
  const cols = [{ text: '全部科目', value: '' }]
  availableSubjects.value.forEach(s => {
    cols.push({ text: s, value: s })
  })
  return cols
})

// 组别选择器列
const groupColumns = computed(() => {
  const cols = [{ text: '全部组别', value: '' }]
  studyGroups.value.forEach(g => {
    cols.push({ text: g.name, value: g.id })
  })
  return cols
})

// 获取科目颜色
const getSubjectColor = (subject: string) => {
  return SUBJECT_COLORS[subject] || '#909399'
}

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
    if (selectedSubject.value) {
      params.subject = selectedSubject.value
    }
    if (selectedGroupId.value) {
      params.group_id = selectedGroupId.value
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
    if (classes.value.length > 0) {
      selectedClassId.value = classes.value[0].id
      selectedClassLabel.value = classes.value[0].name
      await loadStudyGroups()
      await loadTasks()
    }
  } catch (error) {
    console.error('加载班级列表失败', error)
  }
}

// 加载学习小组
const loadStudyGroups = async () => {
  if (!selectedClassId.value) return
  try {
    const res = await http.get<StudyGroup[]>(`/schools/classes/${selectedClassId.value}/groups`)
    studyGroups.value = res || []
  } catch (error) {
    studyGroups.value = []
  }
}

// 下拉刷新
const onRefresh = () => {
  finished.value = false
  loadTasks()
}

// 查看提交详情
const viewSubmissions = (task: Task) => {
  router.push(`/teacher/tasks/${task.id}/submissions`)
}

// 编辑任务
const editTask = (task: Task) => {
  router.push(`/teacher/tasks/create?edit=${task.id}`)
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
  // 发布对象
  if (task.target_names) {
    parts.push(task.target_names)
  } else if (task.group_name) {
    parts.push(task.group_name)
  }
  return parts.join(' · ')
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
  selectedClassLabel.value = selected.text
  selectedClassId.value = selected.value
  showClassPicker.value = false
  // 重置科目和组别
  selectedSubject.value = ''
  selectedGroupId.value = ''
  selectedGroupLabel.value = ''
  loadStudyGroups()
  loadTasks()
}

// 科目确认
const onSubjectConfirm = ({ selectedOptions }: any) => {
  const selected = selectedOptions[0]
  selectedSubject.value = selected.value
  showSubjectPicker.value = false
  loadTasks()
}

// 组别确认
const onGroupConfirm = ({ selectedOptions }: any) => {
  const selected = selectedOptions[0]
  selectedGroupLabel.value = selected.text
  selectedGroupId.value = selected.value
  showGroupPicker.value = false
  loadTasks()
}

// 初始化
onMounted(async () => {
  const today = new Date()
  datePickerValue.value = [
    String(today.getFullYear()),
    String(today.getMonth() + 1).padStart(2, '0'),
    String(today.getDate()).padStart(2, '0')
  ]
  await loadClasses()
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
  
  .task-stats {
    display: flex;
    align-items: center;
    gap: 4px;
    
    .stat-text {
      font-size: 12px;
      color: #3e7dc9;
      white-space: nowrap;
    }
  }
  
  :deep(.van-floating-bubble) {
    background: linear-gradient(135deg, #3e7dc9 0%, #6db3f2 100%);
  }
}
</style>
