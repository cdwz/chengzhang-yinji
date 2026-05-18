<template>
  <div class="task-detail">
    <!-- 任务信息 -->
    <van-cell-group inset class="task-info">
      <van-cell :title="task?.title" :label="task?.subject" title-class="task-title" />
      <van-cell title="任务日期" :value="task?.task_date" />
      <van-cell title="建议时长" :value="task?.suggested_duration ? `${task.suggested_duration}分钟` : '无限制'" />
      <van-cell title="任务性质">
        <template #value>
          <van-tag type="primary">选做</van-tag>
        </template>
      </van-cell>
      <van-cell v-if="task?.content" title="任务内容">
        <template #label>
          <div class="task-content">{{ task.content }}</div>
        </template>
      </van-cell>
    </van-cell-group>

    <!-- 提交记录 -->
    <div class="section-title">学习记录</div>
    
    <van-cell-group v-if="submission" inset>
      <van-cell title="提交时间" :value="formatTime(submission.submitted_at)" />
      <van-cell v-if="submission.feedback" title="家长留言">
        <template #label>
          <div class="feedback-text">{{ submission.feedback }}</div>
        </template>
      </van-cell>
    </van-cell-group>

    <!-- 操作区域 -->
    <div class="section-title">{{ submission ? '提交记录' : '任务上传' }}</div>
    
    <div class="image-section">
      <!-- 教师批改状态提示 -->
      <div v-if="submission?.has_teacher_annotation" class="annotation-notice">
        <van-notice-bar
          color="#1989fa"
          background="#ecf9ff"
          left-icon="info-o"
        >
          教师已批改，无法修改
        </van-notice-bar>
      </div>
      
      <!-- 按钮区域 -->
      <div class="upload-actions">
        <!-- 未提交：显示任务上传按钮 -->
        <van-button 
          v-if="!submission"
          type="primary" 
          size="large" 
          icon="edit"
          @click="goToSubmit"
          block
        >
          任务上传
        </van-button>
        
        <!-- 已提交或已批改：显示查看记录按钮 -->
        <van-button 
          v-else
          type="default" 
          size="large" 
          icon="eye-o"
          @click="showSubmissionDetail"
          block
        >
          查看记录
        </van-button>
        
        <p v-if="!submission" class="upload-tip">点击上传作业照片，支持拍照或从相册选择</p>
        <p v-else class="upload-tip">点击查看已提交的任务记录</p>
      </div>
      
      <!-- 已提交照片预览 -->
      <div v-if="submissionImages.length > 0" class="image-preview">
        <div class="preview-header">
          <span>已提交照片</span>
          <span v-if="submission?.has_teacher_annotation" class="annotation-badge">
            <van-icon name="success" /> 已批改
          </span>
        </div>
        <van-grid :column-num="3" :gutter="8">
          <van-grid-item v-for="(img, index) in submissionImages" :key="index">
            <van-image :src="img" fit="cover" @click="previewImage(img)" />
          </van-grid-item>
        </van-grid>
      </div>
    </div>
    
    <!-- 查看记录详情弹窗 -->
    <van-popup v-model:show="showDetailPopup" position="bottom" :style="{ height: '80%' }">
      <div class="detail-popup">
        <van-nav-bar title="提交记录详情" left-text="关闭" @click-left="showDetailPopup = false" />
        
        <div class="detail-content">
          <div class="detail-section">
            <div class="detail-label">提交时间</div>
            <div class="detail-value">{{ submission ? formatTime(submission.submitted_at) : '' }}</div>
          </div>
          
          <div class="detail-section" v-if="submission?.feedback">
            <div class="detail-label">家长留言</div>
            <div class="detail-value">{{ submission.feedback }}</div>
          </div>
          
          <div class="detail-section">
            <div class="detail-label">提交照片</div>
            <div class="detail-images">
              <van-image 
                v-for="(img, index) in submissionImages" 
                :key="index"
                :src="img" 
                fit="contain"
                @click="previewImage(img)"
              />
            </div>
          </div>
          
          <!-- 教师批注展示 -->
          <div class="detail-section" v-if="submission?.annotations && submission.annotations.length > 0">
            <div class="detail-label">教师批注</div>
            <div class="annotations-list">
              <div v-for="(annotation, index) in submission.annotations" :key="index" class="annotation-item">
                <van-image 
                  v-if="annotation.annotation_url" 
                  :src="getFileUrl(annotation.annotation_url)" 
                  fit="contain"
                  @click="previewImage(getFileUrl(annotation.annotation_url))"
                />
                <div class="annotation-comment" v-if="annotation.comment">
                  {{ annotation.comment }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showFailToast, showImagePreview } from 'vant'
import { http, getFileUrl } from '@/utils/request'
import type { Task, TaskSubmission } from '@/api/types'

const route = useRoute()
const router = useRouter()

// 状态
const task = ref<Task | null>(null)
const submission = ref<TaskSubmission | null>(null)
const showDetailPopup = ref(false)

// 计算属性：处理 submission.images 的类型
const submissionImages = computed(() => {
  if (!submission.value?.images) return []
  const images = submission.value.images
  // 如果是字符串数组，转换为完整URL
  if (images.length > 0 && typeof images[0] === 'string') {
    return (images as string[]).map(url => getFileUrl(url))
  }
  // 如果是对象数组，转换image_url
  return (images as any[]).map(img => getFileUrl(img.image_url))
})

// 跳转到提交页面
const goToSubmit = () => {
  const taskId = route.params.id as string
  router.push(`/parent/tasks/${taskId}/submit`)
}

// 显示提交详情
const showSubmissionDetail = () => {
  showDetailPopup.value = true
}

// 加载任务详情
const loadTask = async () => {
  const taskId = route.params.id as string
  try {
    const res = await http.get<Task>(`/tasks/${taskId}`)
    task.value = res
  } catch (error) {
    showFailToast('获取任务详情失败')
    router.back()
  }
}

// 加载已提交记录
const loadSubmission = async () => {
  const taskId = route.params.id as string
  try {
    const res = await http.get<TaskSubmission[]>(`/tasks/${taskId}/submissions`)
    if (res && res.length > 0) {
      submission.value = res[0]
    }
  } catch (error) {
    console.error('加载提交记录失败', error)
  }
}

// 预览图片
const previewImage = (url: string) => {
  showImagePreview([url])
}

// 格式化时间
const formatTime = (time: string) => {
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 初始化
onMounted(async () => {
  await loadTask()
  await loadSubmission()
})
</script>

<style scoped lang="scss">
.task-detail {
  padding: 12px;
  padding-bottom: 80px;
  
  .task-info {
    margin-bottom: 12px;
    
    .task-title {
      font-size: 18px;
      font-weight: 500;
    }
    
    .task-content {
      margin-top: 8px;
      line-height: 1.6;
      color: #606266;
    }
  }
  
  .section-title {
    padding: 12px;
    font-size: 14px;
    font-weight: 500;
    color: #969799;
  }
  
  .image-section {
    padding: 12px;
    background: #fff;
    border-radius: 8px;
    
    .annotation-notice {
      margin-bottom: 12px;
    }
    
    .upload-actions {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      
      .upload-tip {
        font-size: 12px;
        color: #969799;
        margin: 0;
        margin-top: 8px;
      }
    }
    
    .image-preview {
      margin-top: 16px;
      
      .preview-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 12px;
        color: #333;
        
        .annotation-badge {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
          color: #07c160;
        }
      }
    }
  }
  
  .feedback-text {
    margin-top: 4px;
    line-height: 1.5;
    color: #606266;
  }
}

.detail-popup {
  height: 100%;
  display: flex;
  flex-direction: column;
  
  .detail-content {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
  }
  
  .detail-section {
    margin-bottom: 20px;
    
    .detail-label {
      font-size: 14px;
      color: #969799;
      margin-bottom: 8px;
    }
    
    .detail-value {
      font-size: 15px;
      color: #333;
      line-height: 1.6;
    }
    
    .detail-images {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      
      .van-image {
        width: calc(50% - 4px);
        border-radius: 8px;
        overflow: hidden;
      }
    }
  }
  
  .annotations-list {
    .annotation-item {
      margin-bottom: 16px;
      
      .van-image {
        width: 100%;
        border-radius: 8px;
        overflow: hidden;
      }
      
      .annotation-comment {
        margin-top: 8px;
        padding: 12px;
        background: #f7f8fa;
        border-radius: 8px;
        font-size: 14px;
        line-height: 1.6;
      }
    }
  }
}
</style>
