<template>
  <div class="class-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>我的班级</span>
          <el-button type="primary" @click="showCreateDialog = true">
            创建班级
          </el-button>
        </div>
      </template>
      
      <el-table :data="classes" v-loading="loading">
        <el-table-column prop="name" label="班级名称" />
        <el-table-column prop="grade.name" label="年级" />
        <el-table-column prop="student_count" label="学生数" />
        <el-table-column prop="invite_code" label="邀请码" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row.id)">
              详情
            </el-button>
            <el-button link type="primary" @click="copyInviteCode(row.invite_code)">
              复制邀请码
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 创建班级对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建班级" width="500px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="年级">
          <el-select v-model="createForm.grade_id" placeholder="选择年级">
            <el-option
              v-for="grade in grades"
              :key="grade.id"
              :label="grade.name"
              :value="grade.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="班级名称">
          <el-input v-model="createForm.name" placeholder="如：一年级1班" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createClass">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { http } from '@/utils/request'
import type { Class, Grade } from '@/api/types'

const router = useRouter()

const loading = ref(false)
const classes = ref<Class[]>([])
const grades = ref<Grade[]>([])
const showCreateDialog = ref(false)

const createForm = reactive({
  grade_id: '',
  name: ''
})

onMounted(() => {
  loadClasses()
  loadGrades()
})

async function loadClasses() {
  loading.value = true
  try {
    // 这里需要根据实际API调整
    const res = await http.get<Class[]>('/schools/classes')
    classes.value = res
  } catch (error) {
    console.error('加载班级列表失败', error)
  } finally {
    loading.value = false
  }
}

async function loadGrades() {
  try {
    const res = await http.get<Grade[]>('/schools/grades')
    grades.value = res
  } catch (error) {
    console.error('加载年级列表失败', error)
  }
}

function viewDetail(id: string) {
  router.push(`/teacher/classes/${id}`)
}

function copyInviteCode(code: string) {
  navigator.clipboard.writeText(code)
  ElMessage.success('邀请码已复制')
}

async function createClass() {
  if (!createForm.grade_id || !createForm.name) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  try {
    await http.post('/schools/classes', createForm)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    loadClasses()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}
</script>

<style scoped lang="scss">
.class-list {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}
</style>
