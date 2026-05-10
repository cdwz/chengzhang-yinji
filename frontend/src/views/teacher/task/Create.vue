<template>
  <div class="create-task">
    <el-card>
      <template #header>
        <span>发布学习任务</span>
      </template>
      
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="班级" prop="class_id">
          <el-select v-model="form.class_id" placeholder="选择班级">
            <el-option
              v-for="cls in classes"
              :key="cls.id"
              :label="cls.name"
              :value="cls.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="科目" prop="subject">
          <el-input v-model="form.subject" placeholder="如：语文、数学" />
        </el-form-item>
        
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入任务标题" />
        </el-form-item>
        
        <el-form-item label="任务内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            placeholder="请输入任务内容"
          />
          <div v-if="complianceWarning" class="compliance-warning">
            {{ complianceWarning }}
          </div>
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
import type { Class } from '@/api/types'

const router = useRouter()
const formRef = ref()
const loading = ref(false)
const classes = ref<Class[]>([])

const form = reactive({
  class_id: '',
  subject: '',
  title: '',
  content: '',
  suggested_duration: 30,
  task_date: new Date().toISOString().split('T')[0]
})

const rules = {
  class_id: [{ required: true, message: '请选择班级', trigger: 'change' }],
  subject: [{ required: true, message: '请输入科目', trigger: 'blur' }],
  title: [{ required: true, message: '请输入任务标题', trigger: 'blur' }],
  task_date: [{ required: true, message: '请选择日期', trigger: 'change' }]
}

const complianceWarning = computed(() => {
  if (!form.content) return ''
  const result = checkCompliance(form.content)
  if (!result.valid) {
    return `检测到不合规词汇：${result.violations.join('、')}。请使用合规表述。`
  }
  return ''
})

onMounted(() => {
  loadClasses()
})

async function loadClasses() {
  try {
    const res = await http.get<Class[]>('/schools/classes')
    classes.value = res
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
  
  loading.value = true
  try {
    await http.post('/tasks', form)
    ElMessage.success('任务发布成功')
    router.push('/teacher/tasks')
  } catch (error) {
    ElMessage.error('发布失败')
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
}
</style>
