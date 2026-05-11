<template>
  <div class="class-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>我的班级</span>
          <div class="header-actions">
            <el-button @click="showGradeDialog = true">
              <el-icon><Plus /></el-icon> 创建年级
            </el-button>
            <el-button type="primary" @click="showCreateDialog = true">
              <el-icon><Plus /></el-icon> 创建班级
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 未关联学校提示 -->
      <el-alert
        v-if="!schoolLoaded && !loading"
        title="未关联学校"
        type="warning"
        description="您的账号尚未关联学校，无法管理班级。请联系管理员将您添加到学校。"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />
      
      <!-- 空状态提示 -->
      <el-alert
        v-if="!loading && grades.length === 0"
        title="请先创建年级"
        type="info"
        description="点击「创建年级」按钮，为本校添加年级信息（如：一年级、二年级...）"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />
      
      <el-table :data="classes" v-loading="loading">
        <el-table-column prop="name" label="班级名称" />
        <el-table-column prop="grade.name" label="年级" />
        <el-table-column prop="student_count" label="学生数" width="100" />
        <el-table-column prop="invite_code" label="邀请码" width="120">
          <template #default="{ row }">
            <el-tooltip content="家长使用此邀请码绑定学生" placement="top">
              <el-tag style="cursor: pointer" @click="copyInviteCode(row.invite_code)">
                {{ row.invite_code }}
              </el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="350">
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
            <el-button link type="primary" @click="goStudyGroups(row.id)">
              小组管理
            </el-button>
            <el-button link type="warning" @click="openEditDialog(row)">
              编辑
            </el-button>
            <el-button link type="danger" @click="confirmDeleteClass(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-empty v-if="!loading && classes.length === 0 && grades.length > 0" description="暂无班级，请点击「创建班级」" />
    </el-card>
    
    <!-- 创建年级对话框 -->
    <el-dialog v-model="showGradeDialog" title="创建年级" width="500px">
      <el-form :model="gradeForm" label-width="80px">
        <el-form-item label="年级名称" required>
          <el-input v-model="gradeForm.name" placeholder="如：一年级、二年级" />
        </el-form-item>
        <el-form-item label="学年" required>
          <el-date-picker
            v-model="gradeForm.year"
            type="year"
            placeholder="选择学年"
            format="YYYY"
            value-format="YYYY"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showGradeDialog = false">取消</el-button>
        <el-button type="primary" @click="createGrade" :loading="creatingGrade">确定</el-button>
      </template>
    </el-dialog>
    
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
          <el-input v-model="createForm.name" placeholder="如：1班、2班" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createClass" :loading="creating">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 导入学生对话框 -->
    <el-dialog v-model="showImport" title="导入学生" width="550px">
      <div class="import-tips">
        <p>\uD83D\uDCCB 支持 Excel (.xlsx) 和 CSV 格式文件</p>
        <p>\uD83D\uDCDD 模板包含列：<b>姓名</b>（必填）、<b>学号</b>（必填）、家长手机号（选填）、组名（选填，不存在自动创建）</p>
      </div>
      
      <div class="template-download">
        <el-link type="primary" @click="downloadTemplate">
          <el-icon><Download /></el-icon> 下载导入模板 (.csv)
        </el-link>
      </div>
      
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.xls,.csv"
        :on-change="handleFileChange"
        drag
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
      </el-upload>
      <template #footer>
        <el-button @click="showImport = false">取消</el-button>
        <el-button type="primary" @click="importStudents" :loading="importing">导入</el-button>
      </template>
    </el-dialog>
    
    <!-- 编辑班级对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑班级" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="班级名称" required>
          <el-input v-model="editForm.name" placeholder="如：1班、2班" />
        </el-form-item>
        <el-form-item label="所属年级">
          <el-select v-model="editForm.grade_id" placeholder="选择年级" style="width: 100%">
            <el-option
              v-for="grade in grades"
              :key="grade.id"
              :label="grade.name"
              :value="grade.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="saveEditClass" :loading="savingEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, UploadFilled } from '@element-plus/icons-vue'
import { getClasses, createClass as createClassApi, getGrades, createGrade as createGradeApi, getMySchool, updateClass as updateClassApi, deleteClass as deleteClassApi } from '@/api/schools'
import { importStudents as importStudentsApi } from '@/api/students'
import type { Class, Grade } from '@/api/types'
import type { UploadFile } from 'element-plus'

const router = useRouter()

const loading = ref(false)
const creating = ref(false)
const creatingGrade = ref(false)
const importing = ref(false)
const deletingClass = ref(false)
const classes = ref<Class[]>([])
const grades = ref<Grade[]>([])
const schoolId = ref<string>('')
const schoolName = ref<string>('')
const schoolLoaded = ref(false)
const showGradeDialog = ref(false)
const showCreateDialog = ref(false)
const showImport = ref(false)
const showEditDialog = ref(false)
const savingEdit = ref(false)
const currentClass = ref<Class | null>(null)
const uploadFile = ref<File | null>(null)

const editForm = reactive({
  id: '',
  name: '',
  grade_id: ''
})

const gradeForm = reactive({
  name: '',
  year: new Date().getFullYear().toString()
})

const createForm = reactive({
  grade_id: '',
  name: ''
})

onMounted(async () => {
  await loadSchool()
  await loadGrades()
  await loadClasses()
})

async function loadSchool() {
  try {
    const school = await getMySchool()
    schoolId.value = school.id
    schoolName.value = school.name || ''
    schoolLoaded.value = true
  } catch (error) {
    console.error('获取学校信息失败', error)
    schoolLoaded.value = false
    ElMessage.warning('请先关联学校，请联系管理员添加学校归属')
  }
}

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
  if (!schoolId.value) return
  try {
    grades.value = await getGrades(schoolId.value)
  } catch (error) {
    console.error('加载年级列表失败', error)
  }
}

async function createGrade() {
  if (!gradeForm.name || !gradeForm.year) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  if (!schoolId.value) {
    ElMessage.error('未获取到学校信息')
    return
  }
  
  creatingGrade.value = true
  try {
    await createGradeApi(schoolId.value, {
      name: gradeForm.name,
      year: parseInt(gradeForm.year)
    })
    ElMessage.success('年级创建成功')
    showGradeDialog.value = false
    gradeForm.name = ''
    loadGrades()
  } catch (error: any) {
    ElMessage.error(error?.message || '创建失败')
  } finally {
    creatingGrade.value = false
  }
}

function viewDetail(id: string) {
  router.push(`/teacher/classes/${id}`)
}

function copyInviteCode(code: string) {
  navigator.clipboard.writeText(code)
  ElMessage.success('邀请码已复制，可分享给家长绑定学生')
}

function goStudyGroups(classId: string) {
  router.push(`/teacher/classes/${classId}/groups`)
}

function showImportDialog(cls: Class) {
  currentClass.value = cls
  uploadFile.value = null
  showImport.value = true
}

function handleFileChange(file: UploadFile) {
  uploadFile.value = file.raw || null
}

function downloadTemplate() {
  // 生成CSV模板（UTF-8 BOM，Excel可直接打开）
  const headers = ['姓名', '学号', '家长手机号', '组名']
  const sampleRow1 = ['张三', '2025001', '13800000001', '第一组']
  const sampleRow2 = ['李四', '2025002', '', '第一组']
  const sampleRow3 = ['王五', '2025003', '', '']
  
  const bom = '\uFEFF'
  const lines = [headers.join(','), sampleRow1.join(','), sampleRow2.join(','), sampleRow3.join(',')]
  const csvContent = bom + lines.join('\n')
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = '学生导入模板.csv'
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('模板已下载，可用Excel打开编辑')
}

async function createClass() {
  if (!createForm.grade_id || !createForm.name) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  creating.value = true
  try {
    await createClassApi(createForm)
    ElMessage.success('班级创建成功')
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

// 编辑班级
function openEditDialog(cls: Class) {
  editForm.id = cls.id
  editForm.name = cls.name
  editForm.grade_id = cls.grade?.id || ''
  showEditDialog.value = true
}

async function saveEditClass() {
  if (!editForm.name.trim()) {
    ElMessage.warning('班级名称不能为空')
    return
  }
  
  savingEdit.value = true
  try {
    await updateClassApi(editForm.id, {
      name: editForm.name,
      grade_id: editForm.grade_id || undefined
    })
    ElMessage.success('班级修改成功')
    showEditDialog.value = false
    loadClasses()
  } catch (error: any) {
    ElMessage.error(error?.message || '修改失败')
  } finally {
    savingEdit.value = false
  }
}

// 删除班级
async function confirmDeleteClass(cls: Class) {
  const count = cls.student_count || 0
  const message = count > 0
    ? `该班级下有 ${count} 名学生，删除后所有数据（任务、评价、小组等）将无法恢复，请确认是否需要删除？`
    : '删除后无法恢复，请确认是否需要删除？'

  try {
    await ElMessageBox.confirm(
      message,
      `删除「${cls.name}」`,
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' }
    )
    
    deletingClass.value = true
    await deleteClassApi(cls.id)
    ElMessage.success('班级已删除')
    loadClasses()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error?.message || '删除失败')
    }
  } finally {
    deletingClass.value = false
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
  
  .header-actions {
    display: flex;
    gap: 8px;
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
  
  .template-download {
    margin-bottom: 16px;
  }
}
</style>
