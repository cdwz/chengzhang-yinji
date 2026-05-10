<template>
  <van-popup
    v-model:show="visible"
    position="bottom"
    :style="{ height: '100%' }"
    teleport="body"
  >
    <div class="a4-camera-guide">
      <!-- 顶部工具栏 -->
      <div class="camera-header">
        <van-icon name="cross" size="24" @click="closeCamera" />
        <span class="title">拍照引导</span>
        <van-icon name="replay" size="24" @click="switchCamera" />
      </div>
      
      <!-- 相机预览区域 -->
      <div class="camera-preview" ref="previewRef">
        <video
          ref="videoRef"
          autoplay
          playsinline
          muted
          class="video-element"
        ></video>
        
        <!-- A4边框引导 -->
        <div class="a4-guide-overlay" :style="a4GuideStyle">
          <div class="a4-frame">
            <!-- 四个角标记 -->
            <div class="corner corner-tl"></div>
            <div class="corner corner-tr"></div>
            <div class="corner corner-bl"></div>
            <div class="corner corner-br"></div>
            
            <!-- 边框 -->
            <div class="frame-border"></div>
            
            <!-- 提示文字 -->
            <div class="guide-text">
              <van-icon name="info-o" />
              <span>请将作业放置在框内</span>
            </div>
          </div>
        </div>
        
        <!-- 倾斜警告 -->
        <transition name="fade">
          <div v-if="tiltWarning" class="tilt-warning">
            <van-icon name="warning-o" />
            <span>{{ tiltWarning }}</span>
          </div>
        </transition>
      </div>
      
      <!-- 拍照按钮区域 -->
      <div class="camera-footer">
        <div class="tip-text">
          <van-icon name="photo-o" />
          <span>建议将纸张平铺，垂直向下拍摄</span>
        </div>
        
        <div class="camera-actions">
          <!-- 相册选择 -->
          <van-uploader
            :show-upload="false"
            :after-read="handleSelectFromAlbum"
            accept="image/*"
          >
            <div class="action-btn album-btn">
              <van-icon name="photo" size="28" />
            </div>
          </van-uploader>
          
          <!-- 拍照按钮 -->
          <div class="capture-btn" @click="capturePhoto">
            <div class="capture-inner"></div>
          </div>
          
          <!-- 占位 -->
          <div class="action-btn placeholder"></div>
        </div>
      </div>
      
      <!-- Canvas (隐藏) -->
      <canvas ref="canvasRef" style="display: none;"></canvas>
    </div>
  </van-popup>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { showDialog, showConfirmDialog } from 'vant'
import { compressImage } from '@/utils/imageCompress'
import { detectFileTilt, type TiltResult } from '@/utils/imageTiltDetect'

// Props
interface Props {
  show: boolean
  maxCount?: number
  tiltThreshold?: number  // 倾斜阈值（度）
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
  maxCount: 9,
  tiltThreshold: 15
})

// Emits
const emit = defineEmits<{
  'update:show': [value: boolean]
  'capture': [file: File]
  'error': [message: string]
}>()

// Refs
const videoRef = ref<HTMLVideoElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const previewRef = ref<HTMLDivElement | null>(null)

// 状态
const visible = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})
const stream = ref<MediaStream | null>(null)
const facingMode = ref<'user' | 'environment'>('environment')  // 默认后置摄像头
const tiltWarning = ref<string>('')

// A4 边框样式（根据屏幕比例动态计算）
const a4GuideStyle = computed(() => {
  // A4 比例: 210:297 ≈ 1:1.414
  // 边距留 5%
  return {
    padding: '5%'
  }
})

// 启动相机
const startCamera = async () => {
  try {
    // 请求相机权限
    stream.value = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: facingMode.value,
        width: { ideal: 1920 },
        height: { ideal: 2560 }  // A4 比例
      },
      audio: false
    })
    
    if (videoRef.value) {
      videoRef.value.srcObject = stream.value
    }
  } catch (error: any) {
    console.error('启动相机失败:', error)
    
    let message = '无法启动相机'
    if (error.name === 'NotAllowedError') {
      message = '请允许访问相机权限'
    } else if (error.name === 'NotFoundError') {
      message = '未找到相机设备'
    }
    
    emit('error', message)
    showDialog({ message })
  }
}

// 停止相机
const stopCamera = () => {
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
    stream.value = null
  }
}

// 关闭相机
const closeCamera = () => {
  stopCamera()
  visible.value = false
}

// 切换前后摄像头
const switchCamera = async () => {
  stopCamera()
  facingMode.value = facingMode.value === 'user' ? 'environment' : 'user'
  await startCamera()
}

// 拍照
const capturePhoto = async () => {
  if (!videoRef.value || !canvasRef.value) return
  
  const video = videoRef.value
  const canvas = canvasRef.value
  
  // 设置 canvas 尺寸为视频尺寸
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  
  // 绘制视频帧到 canvas
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  
  // 转换为 Blob
  canvas.toBlob(
    async (blob) => {
      if (!blob) {
        emit('error', '拍照失败')
        return
      }
      
      // 创建文件
      const file = new File([blob], `photo_${Date.now()}.jpg`, {
        type: 'image/jpeg',
        lastModified: Date.now()
      })
      
      // 压缩图片
      try {
        const compressedFile = await compressImage(file)
        emit('capture', compressedFile)
      } catch (error) {
        console.error('压缩失败，使用原图:', error)
        emit('capture', file)
      }
    },
    'image/jpeg',
    0.9
  )
}

// 从相册选择
const handleSelectFromAlbum = async (file: any) => {
  if (!file || !file.file) return
  
  const selectedFile = file.file as File
  
  // 检测倾斜
  try {
    const result: TiltResult = await detectFileTilt(selectedFile)
    
    if (result.isTilted) {
      tiltWarning.value = `检测到照片倾斜约 ${result.angle}°，建议重新拍摄`
      
      // 显示确认对话框
      try {
        await showConfirmDialog({
          title: '照片倾斜提醒',
          message: `检测到照片倾斜约 ${Math.abs(result.angle)}°，可能影响识别效果。是否重新拍摄？`,
          confirmButtonText: '重新拍摄',
          cancelButtonText: '继续使用'
        })
        // 用户选择重新拍摄
        tiltWarning.value = ''
        return
      } catch {
        // 用户选择继续使用
        tiltWarning.value = ''
      }
    }
  } catch (error) {
    console.error('倾斜检测失败:', error)
  }
  
  // 压缩图片
  try {
    const compressedFile = await compressImage(selectedFile)
    emit('capture', compressedFile)
  } catch (error) {
    console.error('压缩失败，使用原图:', error)
    emit('capture', selectedFile)
  }
}

// 监听显示状态
watch(visible, (val) => {
  if (val) {
    startCamera()
  } else {
    stopCamera()
  }
})

// 组件销毁时停止相机
onBeforeUnmount(() => {
  stopCamera()
})
</script>

<style scoped lang="scss">
.a4-camera-guide {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #000;
}

.camera-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  
  .title {
    font-size: 16px;
    font-weight: 500;
  }
}

.camera-preview {
  flex: 1;
  position: relative;
  overflow: hidden;
  
  .video-element {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

.a4-guide-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.a4-frame {
  position: relative;
  width: 90%;
  aspect-ratio: 210 / 297;  // A4 比例
  max-height: 80%;
  
  .corner {
    position: absolute;
    width: 30px;
    height: 30px;
    border-color: #4CAF50;
    border-style: solid;
    
    &.corner-tl {
      top: 0;
      left: 0;
      border-width: 4px 0 0 4px;
      border-radius: 8px 0 0 0;
    }
    
    &.corner-tr {
      top: 0;
      right: 0;
      border-width: 4px 4px 0 0;
      border-radius: 0 8px 0 0;
    }
    
    &.corner-bl {
      bottom: 0;
      left: 0;
      border-width: 0 0 4px 4px;
      border-radius: 0 0 0 8px;
    }
    
    &.corner-br {
      bottom: 0;
      right: 0;
      border-width: 0 4px 4px 0;
      border-radius: 0 0 8px 0;
    }
  }
  
  .frame-border {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border: 2px dashed rgba(255, 255, 255, 0.5);
    border-radius: 4px;
  }
  
  .guide-text {
    position: absolute;
    bottom: -40px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    background: rgba(0, 0, 0, 0.6);
    border-radius: 20px;
    color: #fff;
    font-size: 13px;
    white-space: nowrap;
  }
}

.tilt-warning {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: rgba(255, 152, 0, 0.9);
  border-radius: 20px;
  color: #fff;
  font-size: 14px;
  
  .van-icon {
    font-size: 18px;
  }
}

.camera-footer {
  background: rgba(0, 0, 0, 0.8);
  padding: 16px;
  
  .tip-text {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    color: rgba(255, 255, 255, 0.7);
    font-size: 13px;
    margin-bottom: 16px;
  }
  
  .camera-actions {
    display: flex;
    align-items: center;
    justify-content: space-around;
    
    .action-btn {
      width: 50px;
      height: 50px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.2);
      color: #fff;
      
      &.placeholder {
        background: transparent;
      }
    }
    
    .capture-btn {
      width: 70px;
      height: 70px;
      border-radius: 50%;
      background: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .capture-inner {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: #4CAF50;
        transition: transform 0.1s;
      }
      
      &:active .capture-inner {
        transform: scale(0.9);
      }
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
