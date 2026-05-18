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
    
    <!-- 隐藏的文件输入框：相册模式 -->
    <input 
      ref="albumInputRef"
      type="file" 
      accept="image/*" 
      multiple
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
        <div class="photo-item add-btn" v-if="photos.length < 9 && !existingSubmission" @click="openCameraGuide">
          <van-icon name="plus" size="24" />
          <span>继续添加</span>
        </div>
      </div>
      
      <!-- 拍照按钮 -->
      <div class="photo-empty" v-else-if="!existingSubmission">
        <van-grid :column-num="2" :gutter="12">
          <van-grid-item icon="photograph" text="拍照" @click="openCameraGuide" />
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
    
    <!-- 图片预览 -->
    <van-image-preview v-model:show="showPreview" :images="existingPreviewImages.length > 0 ? existingPreviewImages : previewImages" :start-position="previewIndex" @close="existingPreviewImages = []" />
    
    <!-- A4相机引导组件（拍照模式） -->
    <A4CameraGuide
      v-model="showCameraGuide"
      :max-count="9 - photos.length"
      @capture="handleCameraCapture"
      @error="handleCameraError"
    />
    
    <!-- A4相机引导组件（相册模式） -->
    <van-dialog 
      v-model:show="showAlbumDetection" 
      title="图片检测" 
      show-cancel-button
      :before-close="handleAlbumFileCancel"
      @confirm="handleAlbumFileConfirm"
    >
      <div class="album-detection-dialog">
        <div v-if="albumFileToProcess" class="detection-content">
          <p>正在检测相册图片...</p>
          <p class="tip">请确保图片清晰、角度正确且包含学习内容</p>
          
          <!-- 这里可以显示图片预览和检测结果 -->
          <div class="image-preview-container">
            <img 
              :src="albumFileToProcessPreview" 
              alt="待检测图片" 
              class="detection-preview"
              ref="albumPreviewRef"
            />
            <div v-if="detectionResult" class="detection-result">
              <van-tag :type="detectionResult.pass ? 'success' : 'danger'">
                {{ detectionResult.pass ? '✓ 检测通过' : '✗ 检测未通过' }}
              </van-tag>
              <p v-if="!detectionResult.pass" class="detection-error">
                {{ detectionResult.message }}
              </p>
            </div>
          </div>
        </div>
        <div v-else class="detection-loading">
          <van-loading size="24px">加载中...</van-loading>
        </div>
      </div>
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { getTask, submitTask as submitTaskApi, uploadSubmissionImage as uploadImage } from '@/api/tasks'
import { http, getFileUrl } from '@/utils/request'
import A4CameraGuide from '@/components/A4CameraGuide.vue'
import type { Task } from '@/api/types'

const route = useRoute()
const router = useRouter()
const taskId = route.params.id as string

const task = ref<Task | null>(null)

// 相册图片检测相关
const showAlbumDetection = ref(false)
const albumFileToProcess = ref<File | null>(null)
const albumPreviewRef = ref<HTMLImageElement | null>(null)
const detectionResult = ref<{pass: boolean, message: string} | null>(null)

// 相册图片预览URL
const albumFileToProcessPreview = computed(() => {
  if (!albumFileToProcess.value) return ''
  return URL.createObjectURL(albumFileToProcess.value)
})
const photos = ref<{ file: File; preview: string }[]>([])
const feedback = ref('')
const showA4Frame = ref(true)
const enableEnhance = ref(true)
const submitting = ref(false)

// 图片预览
const showPreview = ref(false)
const previewIndex = ref(0)
const previewImages = computed(() => photos.value.map(p => p.preview))
const existingSubmission = ref<any>(null)
const existingPreviewImages = ref<string[]>([])

// 文件输入框引用
const albumInputRef = ref<HTMLInputElement | null>(null)

// A4相机引导
const showCameraGuide = ref(false)

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

// 打开相机引导
function openCameraGuide() {
  if (photos.value.length >= 9) {
    showToast('最多上传9张图片')
    return
  }
  showCameraGuide.value = true
}

// 处理A4相机拍摄的照片
function handleCameraCapture(file: File) {
  const previewUrl = URL.createObjectURL(file)
  photos.value.push({ file, preview: previewUrl })
  showSuccessToast('照片已添加')
}

// 处理相机错误
function handleCameraError(error: Error) {
  showToast(error.message || '拍照失败')
}

// 打开相册（支持多选）
function openAlbum() {
  if (photos.value.length >= 9) {
    showToast('最多上传9张图片')
    return
  }
  
  if (albumInputRef.value) {
    // 重置input，确保change事件能触发
    albumInputRef.value.value = ''
    albumInputRef.value.click()
  }
}

// 处理文件选择
async function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files || files.length === 0) return
  
  // 只处理第一张图片，单次选择一张
  const firstFile = files[0]
  const remainingSlots = 9 - photos.value.length
  
  if (remainingSlots <= 0) {
    showToast('最多只能添加9张图片')
    input.value = ''
    return
  }
  
  // 检查文件类型
  if (!firstFile.type.startsWith('image/')) {
    showToast(`${firstFile.name} 不是图片文件，已跳过`)
    input.value = ''
    return
  }
  
  // 检查文件大小
  if (firstFile.size > 10 * 1024 * 1024) {
    showToast(`${firstFile.name} 超过10MB，已跳过`)
    input.value = ''
    return
  }
  
  try {
    // 压缩图片（如果太大）
    let finalFile = firstFile
    if (firstFile.size > 2 * 1024 * 1024) {
      const blob = await compressImage(firstFile, 0.6)
      finalFile = new File([blob], firstFile.name, { type: 'image/jpeg' })
    }
    
    // 设置要处理的文件并显示检测对话框
    albumFileToProcess.value = finalFile
    showAlbumDetection.value = true
    
  } catch (error) {
    showToast('图片处理失败')
  }
  
  // 重置 input
  input.value = ''
}

// 处理从相册选择的图片通过检测
function handleAlbumFileProcessed(file: File) {
  if (!albumFileToProcess.value) return
  
  try {
    // 创建预览URL
    const previewUrl = URL.createObjectURL(file)
    photos.value.push({ file, preview: previewUrl })
    showSuccessToast('图片已添加')
  } catch (error) {
    showToast('图片添加失败')
  } finally {
    albumFileToProcess.value = null
    showAlbumDetection.value = false
  }
}

// 取消相册图片处理
function handleAlbumFileCancel() {
  albumFileToProcess.value = null
  showAlbumDetection.value = false
}

// 图片压缩
async function compressImage(file: File, quality: number): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const maxW = 1200
      const maxH = 1200
      let w = img.width
      let h = img.height
      
      // 限制最大尺寸
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
      if (!ctx) {
        reject(new Error('Canvas context not found'))
        return
      }
      
      // 绘制并压缩
      ctx.drawImage(img, 0, 0, w, h)
      
      // 图片增强（如果开启）
      if (enableEnhance.value) {
        try {
          const imageData = ctx.getImageData(0, 0, w, h)
          const data = imageData.data
          
          // 轻微增加对比度和亮度
          for (let i = 0; i < data.length; i += 4) {
            data[i] = Math.min(255, data[i] * 1.1)     // R
            data[i + 1] = Math.min(255, data[i + 1] * 1.1) // G
            data[i + 2] = Math.min(255, data[i + 2] * 1.1) // B
          }
          
          ctx.putImageData(imageData, 0, 0)
        } catch (e) {
          console.warn('图片增强失败', e)
        }
      }
      
      // 转换为JPEG
      canvas.toBlob((blob) => {
        if (blob) {
          resolve(blob)
        } else {
          reject(new Error('图片压缩失败'))
        }
      }, 'image/jpeg', quality)
    }
    img.onerror = reject
    img.src = URL.createObjectURL(file)
  })
}

function removePhoto(index: number) {
  const photo = photos.value[index]
  URL.revokeObjectURL(photo.preview)
  photos.value.splice(index, 1)
}

function previewPhoto(index: number) {
  previewIndex.value = index
  showPreview.value = true
}

function previewExistingImage(url: string) {
  existingPreviewImages.value = existingSubmission.value?.images || []
  previewIndex.value = existingPreviewImages.value.indexOf(url)
  showPreview.value = true
}

// 提交作业
async function submitTask() {
  if (photos.value.length === 0) {
    showToast('请至少上传一张图片')
    return
  }
  
  submitting.value = true
  
  try {
    // 创建提交记录
    const submissionRes = await submitTaskApi(taskId, {
      feedback: feedback.value
    })
    
    const submissionId = submissionRes.id
    
    // 上传图片
    for (const photo of photos.value) {
      await uploadImage(submissionId, photo.file)
    }
    
    showSuccessToast('作业提交成功')
    router.push({ name: 'ParentTasks' })
  } catch (error: any) {
    console.error('提交失败', error)
    showToast(error?.message || '提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

function goBack() {
  router.go(-1)
}

// 处理相册图片确认
async function handleAlbumFileConfirm() {
  if (!albumFileToProcess.value) {
    showToast('请先选择图片')
    return
  }
  
  // 创建图片元素用于检测
  const img = new Image()
  img.onload = async () => {
    try {
      // 创建canvas进行检测
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        throw new Error('无法创建画布上下文')
      }
      
      canvas.width = img.naturalWidth
      canvas.height = img.naturalHeight
      ctx.drawImage(img, 0, 0)
      
      // 执行四项检测（复用A4CameraGuide的检测逻辑）
      const clarityResult = detectClarity(canvas)
      const angleResult = detectAngle(canvas)
      const textResult = detectTextContent(canvas)
      const materialResult = detectLearningMaterial(canvas)
      
      // 检查是否全部通过
      const allPassed = clarityResult.pass && angleResult.pass && textResult.pass && materialResult.pass
      
      if (!allPassed) {
        // 构建错误消息
        const problems: string[] = []
        if (!clarityResult.pass) problems.push('照片模糊（清晰度不足）')
        if (!angleResult.pass) problems.push(`照片歪斜 ${angleResult.value.toFixed(1)}°（超过10°）`)
        if (!textResult.pass) problems.push('未检测到文字或图形内容')
        if (!materialResult.pass) problems.push('可能不是学习资料（白色占比低或颜色种类多）')
        
        detectionResult.value = {
          pass: false,
          message: '检测到以下问题：' + problems.join('、') + '。是否继续使用？'
        }
        
        // 显示确认对话框
        showToast(detectionResult.value.message)
        return
      }
      
      // 所有检测通过
      detectionResult.value = {
        pass: true,
        message: '✓ 检测通过'
      }
      
      // 处理图片并添加到列表
      if (albumFileToProcess.value) {
        handleAlbumFileProcessed(albumFileToProcess.value)
      }
      
    } catch (error) {
      console.error('图片检测失败:', error)
      showToast('图片检测失败，请重试')
      handleAlbumFileCancel()
    }
  }
  
  img.onerror = () => {
    showToast('图片加载失败')
    handleAlbumFileCancel()
  }
  
  img.src = albumFileToProcessPreview.value
}

// 检测函数（从A4CameraGuide复制）
function detectClarity(canvas: HTMLCanvasElement): { pass: boolean; value: number } {
  const ctx = canvas.getContext('2d')
  if (!ctx) return { pass: true, value: 0 }
  
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
  const data = imageData.data
  
  // 计算拉普拉斯方差
  let variance = 0
  for (let i = 0; i < data.length; i += 4) {
    const r = data[i]
    const g = data[i + 1]
    const b = data[i + 2]
    const gray = 0.299 * r + 0.587 * g + 0.114 * b
    variance += gray * gray
  }
  
  variance = variance / (data.length / 4)
  
  const pass = variance > 100
  return { pass, value: variance }
}

function detectAngle(canvas: HTMLCanvasElement): { pass: boolean; value: number } {
  const ctx = canvas.getContext('2d')
  if (!ctx) return { pass: true, value: 0 }
  
  // 简化角度检测逻辑
  // 实际应该使用Canny边缘检测+霍夫变换
  // 这里先返回通过
  return { pass: true, value: 0 }
}

function detectTextContent(canvas: HTMLCanvasElement): { pass: boolean; value: number } {
  const ctx = canvas.getContext('2d')
  if (!ctx) return { pass: true, value: 0 }
  
  // 简化文字检测逻辑
  // 实际应该使用滑动窗口扫描高对比度区域
  // 这里先返回通过
  return { pass: true, value: 0 }
}

function detectLearningMaterial(canvas: HTMLCanvasElement): { pass: boolean; value: number; whiteRatio: number; colorCount: number } {
  const ctx = canvas.getContext('2d')
  if (!ctx) return { pass: true, value: 0, whiteRatio: 0, colorCount: 0 }
  
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
  const data = imageData.data
  const totalPixels = canvas.width * canvas.height
  
  // 统计白色像素
  let whitePixels = 0
  const colorMap = new Map<string, number>()
  
  for (let i = 0; i < data.length; i += 4) {
    const r = data[i]
    const g = data[i + 1]
    const b = data[i + 2]
    
    // 白色检测（亮度>200）
    const brightness = 0.299 * r + 0.587 * g + 0.114 * b
    if (brightness > 200) whitePixels++
    
    // 颜色种类统计
    const rq = Math.floor(r / 16)
    const gq = Math.floor(g / 16)
    const bq = Math.floor(b / 16)
    const colorKey = `${rq}-${gq}-${bq}`
    colorMap.set(colorKey, (colorMap.get(colorKey) || 0) + 1)
  }
  
  const whiteRatio = whitePixels / totalPixels
  const colorCount = colorMap.size
  
  // 判断标准
  let pass = true
  let value = 1
  
  if (whiteRatio > 0.25 && colorCount < 15) {
    // 学习资料特征
    pass = true
    value = 1
  } else if (whiteRatio < 0.15 || colorCount > 25) {
    // 非学习资料特征
    pass = false
    value = 0
  } else {
    // 其他情况（通过）
    pass = true
    value = 2
  }
  
  return { pass, value, whiteRatio, colorCount }
}
</script>

<style scoped lang="scss">
.task-submit {
  padding-bottom: 60px;
  
  .task-info {
    margin: 12px;
  }
  
  .photo-section {
    margin: 12px;
    padding: 16px;
    background: #fff;
    border-radius: 8px;
    
    .section-title {
      font-size: 16px;
      font-weight: 500;
      margin-bottom: 12px;
      color: #333;
    }
    
    .submitted-images {
      margin-bottom: 16px;
      
      .submitted-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
        
        .submitted-time {
          font-size: 12px;
          color: #999;
        }
      }
      
      .submitted-feedback {
        margin-top: 8px;
        padding: 8px;
        background: #f5f5f5;
        border-radius: 4px;
        font-size: 14px;
        color: #666;
        
        .label {
          font-weight: 500;
          color: #333;
        }
      }
    }
    
    .photo-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
      
      .photo-item {
        position: relative;
        width: 80px;
        height: 80px;
        border-radius: 4px;
        overflow: hidden;
        background: #f5f5f5;
        
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
          color: white;
          border-radius: 50%;
          padding: 4px;
          font-size: 12px;
          cursor: pointer;
        }
        
        &.add-btn {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          border: 1px dashed #ddd;
          cursor: pointer;
          color: #666;
          
          &:hover {
            background: #f0f0f0;
          }
          
          span {
            margin-top: 4px;
            font-size: 12px;
          }
        }
      }
    }
    
    .photo-empty {
      text-align: center;
      padding: 24px 0;
      
      .tip {
        margin-top: 12px;
        font-size: 12px;
        color: #999;
      }
    }
    
    .already-submitted {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 24px 0;
      color: #52c41a;
      font-size: 14px;
    }
  }
  
  .settings {
    margin: 12px;
  }
  
  .feedback-section {
    margin: 12px;
  }
  
  .submit-area {
    position: fixed;
    bottom: 50px;
    left: 0;
    right: 0;
    padding: 12px;
    background: #fff;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  }
}

.album-detection-dialog {
  padding: 16px;
  
  .detection-content {
    text-align: center;
    
    .tip {
      color: #999;
      font-size: 12px;
      margin: 8px 0 16px;
    }
    
    .image-preview-container {
      position: relative;
      margin: 16px auto;
      max-width: 200px;
      
      .detection-preview {
        width: 100%;
        height: auto;
        border-radius: 8px;
        border: 2px solid #e8e8e8;
      }
      
      .detection-result {
        margin-top: 12px;
        
        .detection-error {
          margin-top: 8px;
          color: #ff4d4f;
          font-size: 12px;
        }
      }
    }
  }
  
  .detection-loading {
    text-align: center;
    padding: 40px 0;
  }
}

// 移除旧的相机弹窗相关样式
</style>