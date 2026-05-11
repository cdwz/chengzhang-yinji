<template>
  <div class="dimension-settings">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>评价维度设置</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon> 添加维度
          </el-button>
        </div>
      </template>
      
      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        系统已为班级创建6个默认评价维度，您可以根据需要添加、修改或禁用维度。
      </el-alert>
      
      <el-table :data="dimensions" v-loading="loading" row-key="id">
        <el-table-column prop="sort_order" label="排序" width="80">
          <template #default>
            <el-icon class="drag-handle" style="cursor: move"><Rank /></el-icon>
          </template>
        </el-table-column>
        
        <el-table-column prop="name" label="维度名称" min-width="150" />
        
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)">
              {{ getTypeName(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="subject" label="适用科目" width="120">
          <template #default="{ row }">
            <span v-if="row.subject">{{ row.subject }}</span>
            <span v-else style="color: #999">通用</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-switch 
              v-model="row.is_active" 
              @change="handleStatusChange(row)"
              :loading="row.statusLoading"
            />
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="editDimension(row)">编辑</el-button>
            <el-button link type="danger" @click="deleteDimension(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 添加/编辑维度对话框 -->
    <el-dialog 
      v-model="showAddDialog" 
      :title="editingDimension ? '编辑维度' : '添加维度'"
      width="500px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="维度名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入维度名称" maxlength="100" />
        </el-form-item>
        
        <el-form-item label="评价类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择评价类型" style="width: 100%">
            <el-option label="星级评价" value="star" />
            <el-option label="等级评价" value="grade" />
            <el-option label="是/否" value="boolean" />
            <el-option label="分数" value="score" />
            <el-option label="文字评语" value="text" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="适用科目">
          <el-select v-model="form.subject" placeholder="通用" clearable style="width: 100%">
            <el-option label="通用" value="" />
            <el-option label="语文" value="语文" />
            <el-option label="数学" value="数学" />
            <el-option label="英语" value="英语" />
            <el-option label="科学" value="科学" />
            <el-option label="美术" value="美术" />
            <el-option label="音乐" value="音乐" />
            <el-option label="体育" value="体育" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="类型说明">
          <div class="type-desc">
            <p><strong>星级评价：</strong>1-5颗星，适合日常行为评价</p>
            <p><strong>等级评价：</strong>A/B/C/D等级，适合学业评价</p>
            <p><strong>是/否：</strong>二元选择，适合达标类评价</p>
            <p><strong>分数：</strong>0-100分，适合量化评价</p>
            <p><strong>文字评语：</strong>自由文本，适合个性化评价</p>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ editingDimension ? '保存' : '添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Rank } from '@element-plus/icons-vue'
import { 
  getDimensions, 
  createDimension, 
  updateDimension, 
  deleteDimension as deleteDimensionApi 
} from '@/api/dimensions'
import type { EvaluationDimension, DimensionCreate, DimensionUpdate } from '@/api/dimensions'

const route = useRoute()
const classId = route.params.classId as string || route.params.id as string

const loading = ref(false)
const submitting = ref(false)
const dimensions = ref<EvaluationDimension[]>([])
const showAddDialog = ref(false)
const editingDimension = ref<EvaluationDimension | null>(null)
const formRef = ref<FormInstance>()

const form = reactive<DimensionCreate & { subject?: string }>({
  name: '',
  type: 'star',
  subject: ''
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入维度名称', trigger: 'blur' },
    { max: 100, message: '维度名称最多100个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择评价类型', trigger: 'change' }
  ]
}

onMounted(() => {
  loadDimensions()
})

async function loadDimensions() {
  loading.value = true
  try {
    dimensions.value = await getDimensions(classId)
  } catch (error) {
    console.error('加载维度失败', error)
  } finally {
    loading.value = false
  }
}

function getTypeName(type: string) {
  const typeMap: Record<string, string> = {
    star: '星级',
    grade: '等级',
    boolean: '是/否',
    score: '分数',
    text: '文字'
  }
  return typeMap[type] || type
}

function getTypeTagType(type: string) {
  const tagMap: Record<string, string> = {
    star: 'warning',
    grade: 'success',
    boolean: 'info',
    score: 'primary',
    text: ''
  }
  return tagMap[type] || ''
}

function editDimension(dimension: EvaluationDimension) {
  editingDimension.value = dimension
  form.name = dimension.name
  form.type = dimension.type
  form.subject = dimension.subject || ''
  showAddDialog.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      if (editingDimension.value) {
        // 更新
        const updateData: DimensionUpdate = {
          name: form.name,
          type: form.type,
          subject: form.subject || undefined
        }
        await updateDimension(editingDimension.value.id, updateData)
        ElMessage.success('更新成功')
      } else {
        // 创建
        await createDimension(classId, {
          name: form.name,
          type: form.type,
          subject: form.subject || undefined
        })
        ElMessage.success('添加成功')
      }
      
      showAddDialog.value = false
      resetForm()
      loadDimensions()
    } catch (error: any) {
      ElMessage.error(error?.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

async function handleStatusChange(dimension: EvaluationDimension & { statusLoading?: boolean }) {
  dimension.statusLoading = true
  try {
    await updateDimension(dimension.id, { is_active: dimension.is_active })
    ElMessage.success(dimension.is_active ? '已启用' : '已禁用')
  } catch (error: any) {
    dimension.is_active = !dimension.is_active // 恢复原状态
    ElMessage.error(error?.message || '操作失败')
  } finally {
    dimension.statusLoading = false
  }
}

async function deleteDimension(dimension: EvaluationDimension) {
  try {
    await ElMessageBox.confirm(
      `确定要删除维度"${dimension.name}"吗？删除后无法恢复。`,
      '删除确认',
      { type: 'warning' }
    )
    
    await deleteDimensionApi(dimension.id)
    ElMessage.success('删除成功')
    loadDimensions()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error?.message || '删除失败')
    }
  }
}

function resetForm() {
  form.name = ''
  form.type = 'star'
  form.subject = ''
  editingDimension.value = null
  formRef.value?.resetFields()
}
</script>

<style scoped lang="scss">
.dimension-settings {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .drag-handle {
    color: #999;
    cursor: move;
    
    &:hover {
      color: #409eff;
    }
  }
  
  .type-desc {
    font-size: 12px;
    color: #666;
    line-height: 1.8;
    
    p {
      margin: 0;
    }
    
    strong {
      color: #333;
    }
  }
}
</style>
