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

    <!-- 照片记录 -->
    <div class="section-title">照片记录</div>
    
    <div class="image-section">
      <!-- 主要拍照按钮（引导拍摄） -->
      <div class="photo-actions">
        <van-button 
          type="primary" 
          size="small" 
          icon="photograph"
          @click="openCameraGuide"
        >
          引导拍照
        </van-button>
        
        <span class="action-tip">推荐使用引导拍照，确保照片清晰</span>
      </div>
      
      <!-- 已选照片预览 -->
      <div v-if="imageList.length > 0" class="image-preview">
        <van-grid :column-num="3" :gutter="8">
          <van-grid-item v-for="(img, index) in imageList" :key="index">
            <div class="image-item">
              <van-image :src="img.url || img.content" fit="cover" />
              <van-icon 
                name="clear" 
                class="delete-icon" 
                @click="handleDeleteImage(index)"
              />
            </div>
          </van-grid-item>
        </van-grid>
        
        <!-- 添加更多照片 -->
        <div v-if="imageList.length < 9" class="add-more">
          <van-uploader
            :show-upload="true"
            :max-count="9 - imageList.length"
            :max-size="10 * 1024 * 1024"
            :after-read="handleSelectFromAlbum"
          >
            <van-button size="small" icon="plus">添加更多</van-button>
          </van-uploader>
        </div>
      </div>
      
      <!-- 相册选择（备选） -->
      <div v-if="imageList.length === 0" class="album-option">
        <span class="option-label">或从相册选择：</span>
        <van-uploader
          :show-upload="true"
          :max-count="9"
          :max-size="10 * 1024 * 1024"
          :after-read="handleSelectFromAlbum"
        >
          <van-button size="small" plain icon="photo-o">从相册选择</van-button>
        </van-uploader>
      </div>
    </div>

    <!-- 提交按钮 -->
    <div class="submit-section">
      <van-field
        v-model="feedback"
        rows="3"
        autosize
        type="textarea"
        placeholder="可以写写孩子的学习情况（可选）"
        show-word-limit
        maxlength="200"
      />
      
      <van-button
        type="primary"
        block
        :loading="submitting"
        :disabled="imageList.length === 0"
        @click="handleSubmit"
      >
        提交记录
      </van-button>
    </div>

    <!-- 提交历史 -->
    <div v-if="submission" class="section-title">已提交记录</div>
    <van-cell-group v-if="submission" inset class="submitted-images">
      <van-grid :column-num="3" :gutter="8">
        <van-grid-item v-for="(img, index) in submission.images" :key="index">
          <van-image :src="img" fit="cover" @click="previewImage(img)" />
        </van-grid-item>
      </van-grid>
    </van-cell-group>
    
    <!-- A4 相机引导组件 -->
    <A4CameraGuide
      v-model:show="showCameraGuide"
      :max-count="9 - imageList.length"
      @capture="handleCameraCapture"
      @error="handleCameraError"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showSuccessToast, showFailToast, showImagePreview, showConfirmDialog, showLoadingToast, closeToast } from 'vant'
import { http } from '@/utils/request'
import { compressImage } from '@/utils/imageCompress'
import { detectFileTilt, type TiltResult } from '@/utils/imageTiltDetect'
import A4CameraGuide from '@/components/A4CameraGuide.vue'
import type { Task, TaskSubmission } from '@/api/types'

const route = useRoute()
const router = useRouter()

// 状态
const task = ref<Task | null>(null)
const submission = ref<TaskSubmission | null>(null)
const imageList = ref<any[]>([])
const feedback = ref('')
const submitting = ref(false)
const showCameraGuide = ref(false)

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
    const res = await http.get<TaskSubmission[]>(`/tasks/submissions`, { task_id: taskId })
    if (res && res.length > 0) {
      submission.value = res[0]
    }
  } catch (error) {
    // 暂无提交记录，忽略错误
  }
}

// 打开相机引导
const openCameraGuide = () => {
  showCameraGuide.value = true
}

// 处理相机拍摄的照片
const handleCameraCapture = (file: File) => {
  // 照片已在 A4CameraGuide 中压缩，直接添加
  const imageUrl = URL.createObjectURL(file)
  imageList.value.push({
    file,
    url: imageUrl,
    content: imageUrl,
    isImage: true
  })
  
  showSuccessToast('照片已添加')
}

// 处理相机错误
const handleCameraError = (message: string) => {
  showFailToast(message)
}

// 处理从相册选择
const handleSelectFromAlbum = async (file: any) => {
  if (!file || !file.file) return
  
  // 支持多选
  const files = Array.isArray(file) ? file : [file]
  
  showLoadingToast({
    message: '处理中...',
    forbidClick: true,
    duration: 0
  })
  
  for (const f of files) {
    const selectedFile = f.file as File
    
    try {
      // 1. 检测倾斜
      const result: TiltResult = await detectFileTilt(selectedFile)
      
      if (result.isTilted) {
        closeToast()
        
        try {
          await showConfirmDialog({
            title: '照片倾斜提醒',
            message: `检测到照片倾斜约 ${Math.abs(result.angle)}°，可能影响识别效果。是否重新拍摄？`,
            confirmButtonText: '重新拍摄',
            cancelButtonText: '继续使用'
          })
          // 用户选择重新拍摄，跳过这张照片
          continue
        } catch {
          // 用户选择继续使用
        }
        
        showLoadingToast({
          message: '处理中...',
          forbidClick: true,
          duration: 0
        })
      }
      
      // 2. 压缩图片
      const compressedFile = await compressImage(selectedFile)
      
      // 3. 添加到列表
      const imageUrl = URL.createObjectURL(compressedFile)
      imageList.value.push({
        file: compressedFile,
        url: imageUrl,
        content: imageUrl,
        isImage: true
      })
      
    } catch (error) {
      console.error('处理照片失败:', error)
      // 压缩失败，使用原图
      const imageUrl = URL.createObjectURL(selectedFile)
      imageList.value.push({
        file: selectedFile,
        url: imageUrl,
        content: imageUrl,
        isImage: true
      })
    }
  }
  
  closeToast()
  showSuccessToast(`已添加 ${files.length} 张照片`)
}

// 删除图片
const handleDeleteImage = (index: number) => {
  // 释放 URL
  const img = imageList.value[index]
  if (img.url) {
    URL.revokeObjectURL(img.url)
  }
  imageList.value.splice(index, 1)
}

// 提交记录
const handleSubmit = async () => {
  if (imageList.value.length === 0) {
    showFailToast('请至少上传一张照片')
    return
  }

  const taskId = route.params.id as string
  submitting.value = true

  showLoadingToast({
    message: '提交中...',
    forbidClick: true,
    duration: 0
  })

  try {
    // 1. 创建提交记录
    const submitRes = await http.post<TaskSubmission>(`/tasks/${taskId}/submit`, {
      feedback: feedback.value
    })

    // 2. 上传图片
    for (const img of imageList.value) {
      const formData = new FormData()
      formData.append('file', img.file)
      
      await http.upload(`/tasks/submissions/${submitRes.id}/images`, formData)
    }

    closeToast()
    showSuccessToast('提交成功')
    router.push('/parent/tasks')
  } catch (error: any) {
    closeToast()
    showFailToast(error.response?.data?.detail || '提交失败')
  } finally {
    submitting.value = false
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
    
    .photo-actions {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      
      .action-tip {
        font-size: 12px;
        color: #969799;
      }
    }
    
    .image-preview {
      margin-top: 16px;
      
      .image-item {
        position: relative;
        
        .delete-icon {
          position: absolute;
          top: -6px;
          right: -6px;
          font-size: 20px;
          color: #ee0a24;
          background: #fff;
          border-radius: 50%;
        }
      }
      
      .add-more {
        margin-top: 12px;
        display: flex;
        justify-content: center;
      }
    }
    
    .album-option {
      margin-top: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 12px;
      
      .option-label {
        font-size: 13px;
        color: #969799;
      }
    }
  }
  
  .submit-section {
    margin-top: 12px;
    padding: 12px;
    background: #fff;
    border-radius: 8px;
    
    .van-button {
      margin-top: 12px;
    }
  }
  
  .submitted-images {
    padding: 12px;
  }
  
  .feedback-text {
    margin-top: 4px;
    line-height: 1.5;
    color: #606266;
  }
}
</style>
