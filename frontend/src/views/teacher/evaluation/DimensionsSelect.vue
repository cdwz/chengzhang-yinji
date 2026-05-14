<template>
  <div class="dimensions-select">
    <el-card>
      <template #header>
        <span>评价维度配置</span>
      </template>
      
      <el-form :model="form" label-width="100px">
        <el-form-item label="选择班级" required>
          <el-select v-model="form.class_id" placeholder="请选择班级" @change="onClassChange" style="width: 300px">
            <el-option
              v-for="cls in classes"
              :key="cls.id"
              :label="cls.name"
              :value="cls.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <div v-if="form.class_id" class="dimension-config">
        <el-divider />
        
        <div class="config-header">
          <h3>{{ currentClass?.name }} - 评价维度</h3>
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon> 添加维度
          </el-button>
        </div>
        
        <el-table :data="dimensions" v-loading="loading" style="width: 100%">
          <el-table-column prop="sort_order" label="序号" width="60" />
          <el-table-column prop="name" label="维度名称" />
          <el-table-column prop="subject" label="科目" width="100">
            <template #default="{ row }">{{ row.subject || '-' }}</template>
          </el-table-column>
          <el-table-column prop="type" label="类型" width="120">
            <template #default="{ row }">
              <el-tag :type="typeTagMap[row.type] || 'info'" size="small">{{ typeNameMap[row.type] || row.type }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="配置" width="160">
            <template #default="{ row }">
              <span v-if="row.type === 'score'">{{ row.config?.score_type === 'custom' ? `自定义${row.config.max_score}分` : `${row.config?.score_type || 100}分制` }}</span>
              <span v-else-if="row.type === 'ab_score'">A{{ row.config?.a_score ?? 100 }}/B{{ row.config?.b_score ?? 50 }}/总{{ row.config?.total ?? 150 }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button link type="primary" @click="openEditDialog(row)">编辑</el-button>
              <el-button link :type="row.is_active ? 'warning' : 'success'" @click="toggleActive(row)">{{ row.is_active ? '停用' : '启用' }}</el-button>
              <el-button link type="danger" @click="confirmDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <el-empty v-else description="请先选择班级" />
    </el-card>
    
    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editingId ? '编辑维度' : '添加维度'" width="520px">
      <el-form :model="dialogForm" label-width="90px">
        <el-form-item label="维度名称" required>
          <el-input v-model="dialogForm.name" placeholder="如：数学课堂定时" />
        </el-form-item>
        <el-form-item label="科目">
          <el-select v-model="dialogForm.subject" placeholder="选择科目" clearable style="width:100%">
            <el-option v-for="sub in classSubjects" :key="sub" :label="sub" :value="sub" />
          </el-select>
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="dialogForm.type" placeholder="选择类型" style="width:100%" :disabled="!!editingId" @change="onTypeChange">
            <el-option v-for="t in typeOptions" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </el-form-item>
        <!-- score类型配置 -->
        <el-form-item v-if="dialogForm.type === 'score'" label="分制">
          <el-radio-group v-model="dialogForm.config.score_type" @change="onScoreTypeChange">
            <el-radio value="10">10分制</el-radio>
            <el-radio value="100">100分制</el-radio>
            <el-radio value="custom">自定义</el-radio>
          </el-radio-group>
          <el-input-number v-if="dialogForm.config.score_type === 'custom'" v-model="dialogForm.config.max_score" :min="1" style="margin-left:12px" />
        </el-form-item>
        <!-- ab_score类型配置 -->
        <template v-if="dialogForm.type === 'ab_score'">
          <el-form-item label="总分">
            <el-input-number v-model="dialogForm.config.total" :min="1" />
          </el-form-item>
          <el-form-item label="A卷满分">
            <el-input-number v-model="dialogForm.config.a_score" :min="0" />
          </el-form-item>
          <el-form-item label="B卷满分">
            <el-input-number v-model="dialogForm.config.b_score" :min="0" />
          </el-form-item>
          <el-form-item label="">
            <span style="color:#909399;font-size:12px">A卷 + B卷 = {{ (dialogForm.config.a_score || 0) + (dialogForm.config.b_score || 0) }}（需等于总分 {{ dialogForm.config.total }}）</span>
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="saveDimension" :loading="saving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getClasses, getClass } from '@/api/schools'
import { getDimensions, createDimension, updateDimension, deleteDimension } from '@/api/dimensions'
import type { Class, EvaluationDimension } from '@/api/types'

const loading = ref(false)
const saving = ref(false)
const classes = ref<Class[]>([])
const dimensions = ref<EvaluationDimension[]>([])
const classSubjects = ref<string[]>(['语文', '数学', '英语'])
const showDialog = ref(false)
const editingId = ref('')

const form = reactive({
  class_id: ''
})

const dialogForm = reactive({
  name: '',
  subject: '',
  type: 'star' as string,
  config: {} as Record<string, any>
})

const currentClass = computed(() => {
  return classes.value.find(c => c.id === form.class_id)
})

const typeNameMap: Record<string, string> = {
  star: '星级', grade: '等第', score: '分值', ab_score: 'A/B卷', boolean: '是否完成', text: '文本备注'
}
const typeTagMap: Record<string, string> = {
  star: 'warning', grade: 'success', score: 'primary', ab_score: 'danger', boolean: 'info', text: 'info'
}
const typeOptions = [
  { label: '⭐ 星级（1-5星）', value: 'star' },
  { label: '📝 等第（A/B/C/D）', value: 'grade' },
  { label: '🔢 分值', value: 'score' },
  { label: '📄 A/B卷分值', value: 'ab_score' },
  { label: '✅ 是否完成', value: 'boolean' },
  { label: '💬 文本备注', value: 'text' },
]

async function loadClasses() {
  try {
    classes.value = await getClasses()
  } catch (error) {
    ElMessage.error('加载班级列表失败')
  }
}

function onClassChange(classId: string) {
  if (classId) {
    loadDimensions(classId)
    loadClassSubjects(classId)
  } else {
    dimensions.value = []
  }
}

async function loadDimensions(classId: string) {
  loading.value = true
  try {
    dimensions.value = await getDimensions(classId)
  } catch (error) {
    ElMessage.error('加载评价维度失败')
  } finally {
    loading.value = false
  }
}

async function loadClassSubjects(classId: string) {
  try {
    const cls = await getClass(classId)
    classSubjects.value = cls.subjects || ['语文', '数学', '英语']
  } catch (error) {
    classSubjects.value = ['语文', '数学', '英语']
  }
}

function resetDialogForm() {
  dialogForm.name = ''
  dialogForm.subject = ''
  dialogForm.type = 'star'
  dialogForm.config = {}
}

function onTypeChange(type: string) {
  if (type === 'score') {
    dialogForm.config = { score_type: '100', max_score: 100 }
  } else if (type === 'ab_score') {
    dialogForm.config = { total: 150, a_score: 100, b_score: 50 }
  } else {
    dialogForm.config = {}
  }
}

function onScoreTypeChange(val: string) {
  if (val === '10') dialogForm.config.max_score = 10
  else if (val === '100') dialogForm.config.max_score = 100
}

function openCreateDialog() {
  editingId.value = ''
  resetDialogForm()
  showDialog.value = true
}

function openEditDialog(dim: EvaluationDimension) {
  editingId.value = dim.id
  dialogForm.name = dim.name
  dialogForm.subject = dim.subject || ''
  dialogForm.type = dim.type
  dialogForm.config = dim.config ? { ...dim.config } : {}
  showDialog.value = true
}

async function saveDimension() {
  if (!dialogForm.name.trim()) {
    ElMessage.warning('请输入维度名称')
    return
  }
  
  // ab_score校验
  if (dialogForm.type === 'ab_score') {
    const a = dialogForm.config.a_score || 0
    const b = dialogForm.config.b_score || 0
    if (a + b !== dialogForm.config.total) {
      ElMessage.warning(`A卷${a} + B卷${b} ≠ 总分${dialogForm.config.total}`)
      return
    }
  }
  
  saving.value = true
  try {
    if (editingId.value) {
      await updateDimension(editingId.value, {
        name: dialogForm.name,
        subject: dialogForm.subject || undefined,
        config: dialogForm.config
      })
      ElMessage.success('更新成功')
    } else {
      await createDimension(form.class_id, {
        name: dialogForm.name,
        type: dialogForm.type as any,
        subject: dialogForm.subject || undefined,
        config: dialogForm.config
      })
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    loadDimensions(form.class_id)
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
  } finally {
    saving.value = false
  }
}

async function toggleActive(dim: EvaluationDimension) {
  try {
    await updateDimension(dim.id, { is_active: !dim.is_active })
    ElMessage.success(dim.is_active ? '已停用' : '已启用')
    loadDimensions(form.class_id)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

async function confirmDelete(dim: EvaluationDimension) {
  try {
    await ElMessageBox.confirm(
      `删除「${dim.name}」后，该维度下所有评价记录也将被删除且无法恢复，确认删除？`,
      '删除确认',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' }
    )
    await deleteDimension(dim.id)
    ElMessage.success('已删除')
    loadDimensions(form.class_id)
  } catch (e: any) {
    if (e !== 'cancel') ElMessage.error(e?.message || '删除失败')
  }
}

onMounted(() => {
  loadClasses()
})
</script>

<style scoped lang="scss">
.dimensions-select {
  padding: 20px;
  
  .dimension-config {
    margin-top: 20px;
    
    .config-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      
      h3 {
        margin: 0;
        font-size: 16px;
        color: #303133;
      }
    }
  }
}
</style>
