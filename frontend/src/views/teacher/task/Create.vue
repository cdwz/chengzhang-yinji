<template>
  <div class="create-task">
    <el-card>
      <template #header>
        <span>发布学习任务</span>
      </template>
      
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="班级" prop="class_id">
          <el-select v-model="form.class_id" placeholder="选择班级" @change="onClassChange">
            <el-option
              v-for="cls in classes"
              :key="cls.id"
              :label="cls.name"
              :value="cls.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="科目" prop="subject">
          <el-select v-model="form.subject" placeholder="选择科目">
            <el-option
              v-for="sub in availableSubjects"
              :key="sub"
              :label="sub"
              :value="sub"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入任务标题" maxlength="200" show-word-limit />
        </el-form-item>
        
        <el-form-item label="任务内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="5"
            placeholder="请输入任务内容（支持富文本）"
          />
          <div v-if="complianceWarning" class="compliance-warning">
            {{ complianceWarning }}
          </div>
        </el-form-item>
        
        <el-form-item label="发布对象">
          <el-radio-group v-model="form.target_type" @change="onTargetTypeChange">
            <el-radio value="all">全班</el-radio>
            <el-radio value="groups">按学习小组</el-radio>
            <el-radio value="students">按学生个人</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- 按小组多选 -->
        <el-form-item v-if="form.target_type === 'groups'" label="选择小组">
          <el-checkbox-group v-model="form.target_ids">
            <el-checkbox
              v-for="group in studyGroups"
              :key="group.id"
              :label="group.name"
              :value="group.id"
            />
          </el-checkbox-group>
          <div v-if="studyGroups.length === 0" class="empty-hint">暂无学习小组</div>
        </el-form-item>
        
        <!-- 按学生搜索选择 -->
        <el-form-item v-if="form.target_type === 'students'" label="选择学生">
          <el-select
            v-model="form.target_ids"
            multiple
            filterable
            remote
            :remote-method="searchStudents"
            :loading="searchLoading"
            placeholder="输入姓名或学号搜索"
            style="width: 100%"
          >
            <el-option
              v-for="s in studentOptions"
              :key="s.id"
              :label="`${s.name}${s.student_number ? ' (' + s.student_number + ')' : ''}`"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="建议时长">
          <el-input-number
            v-model="form.suggested_duration"
            :min="1"
            :max="60"
            placeholder="分钟"
          />
          <span style="margin-left: 8px; color: #909399;">分钟</span>
        </el-form-item>
        
        <el-form-item label="任务日期" prop="task_date">
          <el-date-picker
            v-model="form.task_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled-date="disablePastDates"
          />
        </el-form-item>
        
        <el-form-item>
          <el-alert
            title="所有任务均为【选做】，建议时长每日总计不超过60分钟"
            type="info"
            :closable="false"
            show-icon
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading">
            发布任务
          </el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { http } from '@/utils/request'
import { checkCompliance } from '@/utils/compliance'
import { createTask } from '@/api/tasks'
import { getClasses } from '@/api/schools'
import type { Class, Student, StudyGroup } from '@/api/types'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const classes = ref<Class[]>([])
const studyGroups = ref<StudyGroup[]>([])
const studentOptions = ref<Student[]>([])
const searchLoading = ref(false)

const form = reactive({
  class_id: '',
  subject: '',
  title: '',
  content: '',
  suggested_duration: 30,
  task_date: new Date().toISOString().split('T')[0],
  target_type: 'all' as 'all' | 'groups' | 'students',
  target_ids: [] as string[]
})

const rules = {
  class_id: [{ required: true, message: '请选择班级', trigger: 'change' }],
  subject: [{ required: true, message: '请选择科目', trigger: 'change' }],
  title: [{ required: true, message: '请输入任务标题', trigger: 'blur' }],
  task_date: [{ required: true, message: '请选择日期', trigger: 'change' }]
}

// 可用科目列表（根据班级subjects动态加载）
const availableSubjects = computed(() => {
  const cls = classes.value.find(c => c.id === form.class_id)
  return cls?.subjects || ['语文', '数学', '英语']
})

const complianceWarning = computed(() => {
  if (!form.content) return ''
  const result = checkCompliance(form.content)
  if (!result.valid) {
    return `检测到不合规词汇：${result.violations.join('、')}。请使用合规表述。`
  }
  return ''
})

// 禁用过去日期
const disablePastDates = (date: Date) => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date < today
}

// 班级变更时加载小组和学生
const onClassChange = async (classId: string) => {
  form.target_ids = []
  form.target_type = 'all'
  await loadStudyGroups(classId)
  await loadAllStudents(classId)
}

// 加载学习小组
const loadStudyGroups = async (classId: string) => {
  try {
    const res = await http.get<StudyGroup[]>(`/schools/classes/${classId}/groups`)
    studyGroups.value = res || []
  } catch (error) {
    studyGroups.value = []
  }
}

// 加载全部学生（用于初始选项）
const loadAllStudents = async (classId: string) => {
  try {
    const res = await http.get<{ items: Student[] }>('/students', { class_id: classId, page_size: 100 })
    studentOptions.value = res?.items || []
  } catch (error) {
    studentOptions.value = []
  }
}

// 搜索学生（远程搜索）
const searchStudents = async (query: string) => {
  if (!query || !form.class_id) return
  searchLoading.value = true
  try {
    const res = await http.get<{ items: Student[] }>('/students', {
      class_id: form.class_id,
      search: query,
      page_size: 20
    })
    studentOptions.value = res?.items || []
  } catch (error) {
    console.error('搜索学生失败', error)
  } finally {
    searchLoading.value = false
  }
}

// 发布对象类型切换
const onTargetTypeChange = () => {
  form.target_ids = []
}

onMounted(() => {
  loadClasses()
})

async function loadClasses() {
  try {
    classes.value = await getClasses()
  } catch (error) {
    console.error('加载班级列表失败', error)
  }
}

async function handleSubmit() {
  const valid = await formRef.value?.validate()
  if (!valid) return
  
  if (complianceWarning.value) {
    ElMessage.warning('请修改不合规内容后再提交')
    return
  }
  
  // 校验发布对象
  if (form.target_type === 'groups' && form.target_ids.length === 0) {
    ElMessage.warning('请选择至少一个学习小组')
    return
  }
  if (form.target_type === 'students' && form.target_ids.length === 0) {
    ElMessage.warning('请选择至少一个学生')
    return
  }
  
  loading.value = true
  try {
    await createTask({
      class_id: form.class_id,
      subject: form.subject,
      title: form.title,
      content: form.content || undefined,
      suggested_duration: form.suggested_duration || undefined,
      task_date: form.task_date,
      target_type: form.target_type,
      target_ids: form.target_type !== 'all' ? form.target_ids : undefined
    })
    ElMessage.success('任务发布成功')
    router.push('/teacher/tasks')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || '发布失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.create-task {
  max-width: 800px;
  margin: 0 auto;
  
  .compliance-warning {
    color: #e6a23c;
    font-size: 12px;
    margin-top: 4px;
  }
  
  .empty-hint {
    color: #909399;
    font-size: 12px;
  }
}
</style>
