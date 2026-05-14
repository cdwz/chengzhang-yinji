<template>
  <div class="task-submit">
    <van-nav-bar title="提交作业" left-arrow @click-left="goBack" />
    
    <!-- 任务信息 -->
    <van-cell-group inset class="task-info">
      <van-cell :title="task?.title" :label="task?.subject">
        <template #value>
          <van-tag type="primary">选做</van-tag>
        </template>
      </van-cell>
      <van-cell v-if="task?.content" :title="task.content" />
      <van-cell v-if="task?.suggested_duration" title="建议时长" :value="task.suggested_duration + '分钟'" />
    </van-cell-group>
    
    <!-- 隐藏的文件输入框（备选方案） -->
    <input 
      ref="fileInputRef"
      type="file" 
      accept="image/*" 
      capture="environment"
      style="display: none"
      @change="handleFileSelect"
    />
    
    <!-- 拍照区域 -->
    <div class="photo-section">
      <div class="section-title">拍照上传</div>
      
      <!-- 已提交的图片 -->
      <div class="submitted-images" v-if="existingSubmission && existingSubmission.images?.length > 0">
        <div class="submitted-header">
          <van-tag type="success">已提交</van-tag>
          <span class="submitted-time">{{ new Date(existingSubmission.submitted_at).toLocaleString() }}</span>
        </div>
        <div class="photo-list">
          <div 
            v-for="(img, index) in existingSubmission.images" 
            :key="index"
            class="photo-item"
          >
            <img :src="img" @click="previewExistingImage(img)" />
          </div>
        </div>
        <div v-if="existingSubmission.feedback" class="submitted-feedback">
          <span class="label">家长反馈：</span>
          {{ existingSubmission.feedback }}
        </div>
      </div>
      
      <!-- 已拍照片列表 -->
      <div class="photo-list" v-if="photos.length > 0">
        <div 
          v-for="(photo, index) in photos" 
          :key="index"
          class="photo-item"
        >
          <img :src="photo.preview" @click="previewPhoto(index)" />
          <van-icon name="cross" class="remove-btn" @click="removePhoto(index)" />
        </div>
        
        <!-- 继续添加 -->
        <div class="photo-item add-btn" v-if="photos.length < 9 && !existingSubmission" @click="takePhoto">
          <van-icon name="plus" size="24" />
          <span>继续添加</span>
        </div>
      </div>
      
      <!-- 拍照按钮 -->
      <div class="photo-empty" v-else-if="!existingSubmission">
        <van-grid :column-num="2" :gutter="12">
          <van-grid-item icon="photograph" text="拍照" @click="openCamera" />
          <van-grid-item icon="photo-o" text="相册" @click="openAlbum" />
        </van-grid>
        <p class="tip">建议将作业平铺在桌面上拍摄</p>
      </div>
      
      <!-- 已提交提示 -->
      <div class="already-submitted" v-else>
        <van-icon name="checked" size="24" color="#52c41a" />
        <span>此任务已完成提交</span>
      </div>
    </div>
    
    <!-- A4引导框设置 -->
    <van-cell-group inset class="settings">
      <van-cell title="显示A4引导框" center>
        <template #right-icon>
          <van-switch v-model="showA4Frame" size="20" />
        </template>
      </van-cell>
      <van-cell title="图片增强" center>
        <template #right-icon>
          <van-switch v-model="enableEnhance" size="20" />
        </template>
      </van-cell>
    </van-cell-group>
    
    <!-- 家长反馈 -->
    <van-cell-group inset class="feedback-section">
      <van-field
        v-model="feedback"
        rows="2"
        autosize
        label="家长反馈"
        type="textarea"
        placeholder="选填：记录孩子在家的学习情况"
      />
    </van-cell-group>
    
    <!-- 提交按钮 -->
    <div class="submit-area" v-if="!existingSubmission">
      <van-button 
        type="primary" 
        block 
        :disabled="photos.length === 0"
        :loading="submitting"
        @click="submitTask"
      >
        提交作业
      </van-button>
    </div>
    
    <!-- 拍照弹窗 -->
    <van-popup v-model:show="showCamera" position="bottom" :style="{ height: '100%' }">
      <div class="camera-container">
        <!-- 摄像头预览 -->
        <div class="camera-preview" ref="previewRef">
          <!-- A4引导框 -->
          <div v-if="showA4Frame" class="a4-frame">
            <div class="corner tl"></div>
            <div class="corner tr"></div>
            <div class="corner bl"></div>
            <div class="corner br"></div>
          </div>
        </div>
        
        <!-- 相机控制 -->
        <div class="camera-controls">
          <van-button @click="closeCamera">取消</van-button>
          <van-button type="primary" @click="capturePhoto" :loading="capturing">
            <van-icon name="photograph" /> 拍照
          </van-button>
        </div>
      </div>
    </van-popup>
    
    <!-- 图片预览 -->
    <van-image-preview v-model:show="showPreview" :images="existingPreviewImages.length > 0 ? existingPreviewImages : previewImages" :start-position="previewIndex" @close="existingPreviewImages = []" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { getTask, submitTask as submitTaskApi, uploadSubmissionImage as uploadImage } from '@/api/tasks'
import { http, getFileUrl } from '@/utils/request'
import type { Task } from '@/api/types'

const route = useRoute()
const router = useRouter()
const taskId = route.params.id as string

const task = ref<Task | null>(null)
const photos = ref<{ file: File; preview: string }[]>([])
const feedback = ref('')
const showA4Frame = ref(true)
const enableEnhance = ref(true)
const submitting = ref(false)
const showCamera = ref(false)
const capturing = ref(false)
const previewRef = ref<HTMLDivElement>()
const stream = ref<MediaStream | null>(null)
const videoEl = ref<HTMLVideoElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

// 图片预览
const showPreview = ref(false)
const previewIndex = ref(0)
const previewImages = computed(() => photos.value.map(p => p.preview))
const existingSubmission = ref<any>(null)
const existingPreviewImages = ref<string[]>([])

onMounted(() => {
  loadTask()
  loadExistingSubmission()
})

async function loadTask() {
  try {
    task.value = await getTask(taskId)
  } catch (error) {
    showToast('加载任务失败')
  }
}

async function loadExistingSubmission() {
  try {
    const submissions = await http.get<any[]>('/tasks/my-submissions', { task_id: taskId })
    if (submissions && submissions.length > 0) {
      const sub = submissions[0]
      // 转换图片URL
      if (sub.images && Array.isArray(sub.images)) {
        sub.images = sub.images.map((img: string) => getFileUrl(img))
      }
      existingSubmission.value = sub
    }
  } catch (error) {
    console.error('加载提交记录失败', error)
  }
}

// 打开相机（直接使用 file input 相机模式，避免HTTP下getUserMedia不可用）
function openCamera() {
  if (photos.value.length >= 9) {
    showToast('最多上传9张图片')
    return
  }
  
  // 直接使用 file input（相机模式）
  if (fileInputRef.value) {
    fileInputRef.value.setAttribute('capture', 'environment')
    fileInputRef.value.removeAttribute('multiple')
    fileInputRef.value.click()
  }
}

// 打开相册（直接使用 file input，支持多选）
function openAlbum() {
  if (photos.value.length >= 9) {
    showToast('最多上传9张图片')
    return
  }
  
  if (fileInputRef.value) {
    fileInputRef.value.removeAttribute('capture')
    fileInputRef.value.setAttribute('multiple', 'true')
    fileInputRef.value.click()
  }
}

// 兼容旧的 takePhoto 方法（保持向后兼容）
async function takePhoto() {
  await openCamera()
}

function closeCamera() {
  // 停止摄像头
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
    stream.value = null
  }
  
  // 移除视频元素
  if (videoEl.value) {
    videoEl.value.remove()
    videoEl.value = null
  }
  
  showCamera.value = false
}

async function capturePhoto() {
  if (!videoEl.value || !previewRef.value) return
  
  capturing.value = true
  
  try {
    // 创建Canvas截图
    const canvas = document.createElement('canvas')
    const video = videoEl.value
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Canvas context not found')
    
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    
    // 图片增强
    if (enableEnhance.value) {
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
      const data = imageData.data
      
      // 增强对比度和亮度
      for (let i = 0; i < data.length; i += 4) {
        // 轻微增加对比度
        data[i] = Math.min(255, data[i] * 1.1)     // R
        data[i + 1] = Math.min(255, data[i + 1] * 1.1) // G
        data[i + 2] = Math.min(255, data[i + 2] * 1.1) // B
      }
      
      ctx.putImageData(imageData, 0, 0)
    }
    
    // 转换为Blob
    const blob = await new Promise<Blob>((resolve) => {
      canvas.toBlob((b) => resolve(b!), 'image/jpeg', 0.8)
    })
    
    // 压缩图片（如果太大）
    let finalBlob = blob
    if (blob.size > 2 * 1024 * 1024) { // 超过2MB压缩
      finalBlob = await compressImage(blob, 0.6)
    }
    
    // 创建预览URL
    const previewUrl = URL.createObjectURL(finalBlob)
    const file = new File([finalBlob], `photo_${Date.now()}.jpg`, { type: 'image/jpeg' })
    
    photos.value.push({ file, preview: previewUrl })
    
    closeCamera()
    showSuccessToast('拍照成功')
  } catch (error) {
    showToast('拍照失败')
  } finally {
    capturing.value = false
  }
}

// 图片压缩
async function compressImage(blob: Blob, quality: number): Promise<Blob> {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const maxW = 1920
      const maxH = 1080
      let w = img.width
      let h = img.height
      
      if (w > maxW) {
        h = h * (maxW / w)
        w = maxW
      }
      if (h > maxH) {
        w = w * (maxH / h)
        h = maxH
      }
      
      canvas.width = w
      canvas.height = h
      
      const ctx = canvas.getContext('2d')
      ctx?.drawImage(img, 0, 0, w, h)
      
      canvas.toBlob((b) => resolve(b!), 'image/jpeg', quality)
    }
    img.src = URL.createObjectURL(blob)
  })
}

function removePhoto(index: number) {
  const photo = photos.value[index]
  URL.revokeObjectURL(photo.preview)
  photos.value.splice(index, 1)
}

// 处理文件选择（相机/相册模式）
async function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files || files.length === 0) return
  
  // 支持多文件选择
  const fileArray = Array.from(files)
  const remainingSlots = 9 - photos.value.length
  const filesToProcess = fileArray.slice(0, remainingSlots)
  
  if (filesToProcess.length < fileArray.length) {
    showToast(`最多还能添加${remainingSlots}张图片`)
  }
  
  for (const file of filesToProcess) {
    // 检查文件类型
    if (!file.type.startsWith('image/')) {
      showToast(`${file.name} 不是图片文件，已跳过`)
      continue
    }
    
    // 检查文件大小
    if (file.size > 10 * 1024 * 1024) {
      showToast(`${file.name} 超过10MB，已跳过`)
      continue
    }
    
    try {
      // 压缩图片（如果太大）
      let finalFile = file
      if (file.size > 2 * 1024 * 1024) {
        const blob = await compressImage(file, 0.6)
        finalFile = new File([blob], file.name, { type: 'image/jpeg' })
      }
      
      // 创建预览URL
      const previewUrl = URL.createObjectURL(finalFile)
      photos.value.push({ file: finalFile, preview: previewUrl })
    } catch (error) {
      showToast(`${file.name} 添加失败`)
    }
  }
  
  if (filesToProcess.some(f => f.type.startsWith('image/'))) {
    showSuccessToast(`已添加${Math.min(filesToProcess.length, remainingSlots)}张图片`)
  }
  
  // 重置 input
  input.value = ''
}

function previewPhoto(index: number) {
  previewIndex.value = index
  showPreview.value = true
}

function previewExistingImage(url: string) {
  existingPreviewImages.value = existingSubmission.value?.images || []
  previewIndex.value = existingPreviewImages.value.indexOf(url)
  if (previewIndex.value < 0) previewIndex.value = 0
  showPreview.value = true
}

async function submitTask() {
  if (photos.value.length === 0) {
    showToast('请先拍照')
    return
  }
  
  submitting.value = true
  try {
    // 1. 创建提交记录
    const submission = await submitTaskApi(taskId, { feedback: feedback.value })
    
    // 2. 上传图片
    for (const photo of photos.value) {
      await uploadImage(submission.id, photo.file)
    }
    
    showSuccessToast('提交成功')
    router.back()
  } catch (error: any) {
    showToast(error?.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

function goBack() {
  router.back()
}
</script>

<style scoped lang="scss">
.task-submit {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 80px;
  
  .task-info {
    margin: 12px;
  }
  
  .photo-section {
    margin: 12px;
    
    .section-title {
      font-size: 14px;
      color: #333;
      margin-bottom: 12px;
    }
    
    .photo-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      
      .photo-item {
        width: calc(33.33% - 6px);
        aspect-ratio: 1;
        border-radius: 8px;
        overflow: hidden;
        position: relative;
        background: #fff;
        
        img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        
        .remove-btn {
          position: absolute;
          top: 4px;
          right: 4px;
          background: rgba(0, 0, 0, 0.5);
          color: #fff;
          border-radius: 50%;
          padding: 4px;
        }
        
        &.add-btn {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          border: 1px dashed #ddd;
          color: #999;
          
          span {
            font-size: 12px;
            margin-top: 4px;
          }
        }
      }
    }
    
    .photo-empty {
      background: #fff;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      
      .van-grid {
        margin: 0 auto;
        max-width: 280px;
      }
      
      .van-grid-item {
        :deep(.van-grid-item__content) {
          padding: 24px 12px;
          
          .van-grid-item__icon {
            font-size: 32px;
            color: #1989fa;
          }
          
          .van-grid-item__text {
            margin-top: 8px;
            color: #333;
          }
        }
      }
      
      .tip {
        font-size: 12px;
        color: #ccc;
        margin-top: 16px;
      }
    }
    
    .submitted-images {
      background: #f0f9eb;
      border-radius: 8px;
      padding: 12px;
      margin-bottom: 12px;
      
      .submitted-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
        
        .submitted-time {
          font-size: 12px;
          color: #909399;
        }
      }
      
      .photo-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        
        .photo-item {
          width: calc(33.33% - 6px);
          aspect-ratio: 1;
          border-radius: 8px;
          overflow: hidden;
          
          img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }
        }
      }
      
      .submitted-feedback {
        margin-top: 8px;
        font-size: 14px;
        color: #606266;
        
        .label {
          color: #909399;
        }
      }
    }
  }
  
  .settings, .feedback-section {
    margin: 12px;
  }
  
  .submit-area {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 12px;
    background: #fff;
  }
  
  .camera-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #000;
    
    .camera-preview {
      flex: 1;
      position: relative;
      
      .a4-frame {
        position: absolute;
        top: 10%;
        left: 5%;
        right: 5%;
        bottom: 20%;
        border: 2px dashed rgba(255, 255, 255, 0.5);
        pointer-events: none;
        
        .corner {
          position: absolute;
          width: 20px;
          height: 20px;
          border-color: #fff;
          border-style: solid;
          
          &.tl { top: -2px; left: -2px; border-width: 3px 0 0 3px; }
          &.tr { top: -2px; right: -2px; border-width: 3px 3px 0 0; }
          &.bl { bottom: -2px; left: -2px; border-width: 0 0 3px 3px; }
          &.br { bottom: -2px; right: -2px; border-width: 0 3px 3px 0; }
        }
      }
    }
    
    .camera-controls {
      padding: 20px;
      display: flex;
      justify-content: space-around;
    }
  }
}
</style>
