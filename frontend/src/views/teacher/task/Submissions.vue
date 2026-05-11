<template>
  <div class="submission-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>作业提交列表</span>
            <el-tag v-if="task">{{ task.title }}</el-tag>
          </div>
          <div class="header-actions">
            <el-button type="primary" @click="exportPDF" :loading="exporting">
              <el-icon><Download /></el-icon> 批量导出PDF
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 筛选 -->
      <div class="filters">
        <el-select v-model="filters.status" placeholder="提交状态" clearable style="width: 150px">
          <el-option label="全部" value="" />
          <el-option label="已提交" value="submitted" />
          <el-option label="未提交" value="pending" />
        </el-select>
        
        <el-input 
          v-model="filters.keyword" 
          placeholder="搜索学生姓名" 
          clearable
          style="width: 200px; margin-left: 12px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      
      <el-table :data="filteredSubmissions" v-loading="loading">
        <el-table-column prop="student_name" label="学生" width="120">
          <template #default="{ row }">
            <div class="student-info">
              <span>{{ row.student?.name }}</span>
              <el-tag v-if="row.student?.study_group" size="small" type="info">
                {{ row.student.study_group.name }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="提交状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.images?.length > 0" type="success">已提交</el-tag>
            <el-tag v-else type="info">未提交</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="作业图片" min-width="300">
          <template #default="{ row }">
            <div class="image-thumbnails" v-if="row.images?.length > 0">
              <el-image
                v-for="(img, idx) in row.images.slice(0, 5)"
                :key="idx"
                :src="img.thumbnail_url || img.image_url"
                :preview-src-list="row.images.map((i: any) => i.image_url)"
                :initial-index="idx"
                fit="cover"
                class="thumbnail"
              >
                <template #error>
                  <div class="image-error">
                    <el-icon><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
              <div v-if="row.images.length > 5" class="more-images">
                +{{ row.images.length - 5 }}
              </div>
            </div>
            <span v-else class="no-image">暂无提交</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="feedback" label="家长反馈" min-width="150">
          <template #default="{ row }">
            <span v-if="row.feedback">{{ row.feedback }}</span>
            <span v-else style="color: #999">-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="submitted_at" label="提交时间" width="160">
          <template #default="{ row }">
            <span v-if="row.submitted_at">{{ formatTime(row.submitted_at) }}</span>
            <span v-else style="color: #999">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="row.images?.length > 0"
              link 
              type="primary" 
              @click="annotateSubmission(row)"
            >
              批注
            </el-button>
            <el-button 
              v-if="row.annotations?.length > 0"
              link 
              type="success"
              @click="viewAnnotations(row)"
            >
              查看批注 ({{ row.annotations.length }})
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 批注对话框 -->
    <el-dialog v-model="showAnnotation" title="作业批注" width="90%" top="5vh">
      <div class="annotation-container">
        <div class="image-selector">
          <div 
            v-for="(img, idx) in currentSubmission?.images"
            :key="idx"
            class="image-thumb"
            :class="{ active: currentImageIndex === idx }"
            @click="currentImageIndex = idx"
          >
            <img :src="img.thumbnail_url || img.image_url" />
          </div>
        </div>
        
        <div class="annotation-workspace">
          <AnnotationCanvas
            v-if="currentSubmission && currentImageIndex !== null"
            :image-id="currentSubmission.images[currentImageIndex]?.id"
            :image-url="currentSubmission.images[currentImageIndex]?.image_url"
            :annotations="currentImageAnnotations"
            @save="handleAnnotationSave"
          />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Download, Search, Picture } from '@element-plus/icons-vue'
import { getSubmissions, getTask } from '@/api/tasks'
import AnnotationCanvas from '@/components/AnnotationCanvas.vue'
import type { Task, TaskSubmission } from '@/api/types'

const route = useRoute()
const taskId = route.params.taskId as string

const loading = ref(false)
const exporting = ref(false)
const task = ref<Task | null>(null)
const submissions = ref<TaskSubmission[]>([])
const showAnnotation = ref(false)
const currentSubmission = ref<TaskSubmission | null>(null)
const currentImageIndex = ref<number | null>(null)

const filters = reactive({
  status: '',
  keyword: ''
})

// 过滤后的提交列表
const filteredSubmissions = computed(() => {
  let result = submissions.value
  
  if (filters.keyword) {
    result = result.filter(s => 
      s.student?.name.includes(filters.keyword)
    )
  }
  
  if (filters.status) {
    if (filters.status === 'submitted') {
      result = result.filter(s => s.images?.length > 0)
    } else {
      result = result.filter(s => !s.images || s.images.length === 0)
    }
  }
  
  return result
})

// 当前图片的批注
const currentImageAnnotations = computed(() => {
  if (!currentSubmission.value || currentImageIndex.value === null) return []
  // TODO: 从批注API获取当前图片的批注
  return []
})

onMounted(() => {
  loadTask()
  loadSubmissions()
})

async function loadTask() {
  try {
    task.value = await getTask(taskId)
  } catch (error) {
    console.error('加载任务失败', error)
  }
}

async function loadSubmissions() {
  loading.value = true
  try {
    submissions.value = await getSubmissions({ task_id: taskId })
  } catch (error) {
    console.error('加载提交列表失败', error)
  } finally {
    loading.value = false
  }
}

function formatTime(time: string) {
  return new Date(time).toLocaleString('zh-CN')
}

function annotateSubmission(submission: TaskSubmission) {
  currentSubmission.value = submission
  currentImageIndex.value = submission.images?.length > 0 ? 0 : null
  showAnnotation.value = true
}

function viewAnnotations(submission: TaskSubmission) {
  currentSubmission.value = submission
  currentImageIndex.value = 0
  showAnnotation.value = true
}

function handleAnnotationSave(_annotations: any[]) {
  ElMessage.success('批注保存成功')
  loadSubmissions()
}

async function exportPDF() {
  exporting.value = true
  try {
    // TODO: 调用PDF导出API
    const submitted = submissions.value.filter(s => s.images?.length > 0)
    if (submitted.length === 0) {
      ElMessage.warning('暂无已提交的作业')
      return
    }
    
    // 前端生成PDF（简化版）
    ElMessage.info('PDF导出功能开发中，敬请期待')
    
    // 实际实现应该调用后端API:
    // const blob = await http.download(`/tasks/${taskId}/submissions/export-pdf`)
    // const url = URL.createObjectURL(blob)
    // const a = document.createElement('a')
    // a.href = url
    // a.download = `${task.value?.title}-作业提交.pdf`
    // a.click()
    // URL.revokeObjectURL(url)
  } catch (error: any) {
    ElMessage.error(error?.message || '导出失败')
  } finally {
    exporting.value = false
  }
}
</script>

<style scoped lang="scss">
.submission-list {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }
  }
  
  .filters {
    margin-bottom: 16px;
    display: flex;
    align-items: center;
  }
  
  .student-info {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  .image-thumbnails {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    
    .thumbnail {
      width: 60px;
      height: 60px;
      border-radius: 4px;
      cursor: pointer;
      
      :deep(img) {
        object-fit: cover;
      }
    }
    
    .image-error {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      height: 100%;
      background: #f5f5f5;
      color: #999;
    }
    
    .more-images {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 60px;
      height: 60px;
      background: #f5f5f5;
      border-radius: 4px;
      font-size: 14px;
      color: #666;
    }
  }
  
  .no-image {
    color: #999;
  }
  
  .annotation-container {
    display: flex;
    height: 70vh;
    
    .image-selector {
      width: 120px;
      overflow-y: auto;
      border-right: 1px solid #eee;
      padding: 8px;
      
      .image-thumb {
        width: 100px;
        height: 100px;
        margin-bottom: 8px;
        border-radius: 4px;
        overflow: hidden;
        cursor: pointer;
        border: 2px solid transparent;
        
        &.active {
          border-color: var(--el-color-primary);
        }
        
        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      }
    }
    
    .annotation-workspace {
      flex: 1;
      overflow: hidden;
    }
  }
}
</style>
