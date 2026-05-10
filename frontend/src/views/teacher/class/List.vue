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
        <el-table-column prop="student_count" label="学生数" width="100" />
        <el-table-column prop="invite_code" label="邀请码" width="120">
          <template #default="{ row }">
            <el-tag>{{ row.invite_code }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row.id)">
              详情
            </el-button>
            <el-button link type="primary" @click="copyInviteCode(row.invite_code)">
              复制邀请码
            </el-button>
            <el-button link type="primary" @click="showImportDialog(row)">
              导入学生
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="!loading && classes.length === 0" description="暂无班级，请先创建年级和班级" />
    </el-card>
    
    <!-- 创建班级对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建班级" width="500px">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="年级" required>
          <el-select v-model="createForm.grade_id" placeholder="选择年级" style="width: 100%">
            <el-option
              v-for="grade in grades"
              :key="grade.id"
              :label="grade.name"
              :value="grade.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="班级名称" required>
          <el-input v-model="createForm.name" placeholder="如：1班" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createClass" :loading="creating">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 导入学生对话框 -->
    <el-dialog v-model="showImport" title="导入学生" width="500px">
      <div class="import-tips">
        <p>支持 Excel (.xlsx) 和 CSV 格式文件</p>
        <p>文件需包含以下列：姓名、学号（可选）、性别（可选）</p>
      </div>
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.xls,.csv"
        :on-change="handleFileChange"
        drag
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
      </el-upload>
      <template #footer>
        <el-button @click="showImport = false">取消</el-button>
        <el-button type="primary" @click="importStudents" :loading="importing">导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { getClasses, createClass as createClassApi, getGrades } from '@/api/schools'
import { importStudents as importStudentsApi } from '@/api/students'
import type { Class, Grade } from '@/api/types'
import type { UploadFile } from 'element-plus'

const router = useRouter()

const loading = ref(false)
const creating = ref(false)
const importing = ref(false)
const classes = ref<Class[]>([])
const grades = ref<Grade[]>([])
const showCreateDialog = ref(false)
const showImport = ref(false)
const currentClass = ref<Class | null>(null)
const uploadFile = ref<File | null>(null)

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
    classes.value = await getClasses()
  } catch (error) {
    console.error('加载班级列表失败', error)
  } finally {
    loading.value = false
  }
}

async function loadGrades() {
  try {
    // 使用测试学校ID（实际项目中应从用户信息获取）
    const schoolId = '5f027ad4-d7c0-4570-a7fa-0a8ffa3b623b'
    grades.value = await getGrades(schoolId)
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

function showImportDialog(cls: Class) {
  currentClass.value = cls
  uploadFile.value = null
  showImport.value = true
}

function handleFileChange(file: UploadFile) {
  uploadFile.value = file.raw || null
}

async function createClass() {
  if (!createForm.grade_id || !createForm.name) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  creating.value = true
  try {
    await createClassApi(createForm)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    createForm.grade_id = ''
    createForm.name = ''
    loadClasses()
  } catch (error: any) {
    ElMessage.error(error?.message || '创建失败')
  } finally {
    creating.value = false
  }
}

async function importStudents() {
  if (!currentClass.value || !uploadFile.value) {
    ElMessage.warning('请选择要上传的文件')
    return
  }
  
  importing.value = true
  try {
    const formData = new FormData()
    formData.append('class_id', currentClass.value.id)
    formData.append('file', uploadFile.value)
    const result = await importStudentsApi(formData)
    ElMessage.success(result.message)
    showImport.value = false
    loadClasses()
  } catch (error: any) {
    ElMessage.error(error?.message || '导入失败')
  } finally {
    importing.value = false
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
  
  .import-tips {
    margin-bottom: 16px;
    padding: 12px;
    background: var(--el-fill-color-light);
    border-radius: 4px;
    font-size: 14px;
    color: var(--el-text-color-secondary);
    
    p {
      margin: 4px 0;
    }
  }
}
</style>
