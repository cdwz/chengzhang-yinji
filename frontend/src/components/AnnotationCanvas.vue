<template>
  <div class="annotation-canvas">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="tool-group">
        <van-button 
          :type="currentTool === 'pencil' ? 'primary' : 'default'"
          size="small"
          @click="setTool('pencil')"
        >
          <van-icon name="edit" /> 画笔
        </van-button>
        <van-button 
          :type="currentTool === 'arrow' ? 'primary' : 'default'"
          size="small"
          @click="setTool('arrow')"
        >
          <van-icon name="share" /> 箭头
        </van-button>
        <van-button 
          :type="currentTool === 'circle' ? 'primary' : 'default'"
          size="small"
          @click="setTool('circle')"
        >
          <van-icon name="circle" /> 圆圈
        </van-button>
        <van-button 
          :type="currentTool === 'text' ? 'primary' : 'default'"
          size="small"
          @click="setTool('text')"
        >
          <van-icon name="comment-o" /> 文字
        </van-button>
      </div>
      
      <div class="tool-options" v-if="currentTool === 'pencil'">
        <span>颜色:</span>
        <input type="color" v-model="brushColor" />
        <span>粗细:</span>
        <van-slider v-model="brushWidth" :min="1" :max="10" style="width: 80px" />
      </div>
      
      <div class="tool-group">
        <van-button size="small" @click="undo" :disabled="history.length === 0">
          <van-icon name="replay" /> 撤销
        </van-button>
        <van-button size="small" type="danger" @click="clearCanvas">
          <van-icon name="delete-o" /> 清空
        </van-button>
      </div>
    </div>
    
    <!-- 画布容器 -->
    <div class="canvas-container" ref="containerRef">
      <img 
        v-if="imageUrl" 
        :src="imageUrl" 
        class="background-image"
        @load="initCanvas"
        ref="imageRef"
        crossorigin="anonymous"
      />
      <canvas 
        ref="canvasRef" 
        class="drawing-canvas"
        @mousedown="startDrawing"
        @mousemove="draw"
        @mouseup="stopDrawing"
        @touchstart="startDrawing"
        @touchmove="draw"
        @touchend="stopDrawing"
      ></canvas>
    </div>
    
    <!-- 操作按钮 -->
    <div class="actions">
      <van-button @click="$emit('cancel')">取消</van-button>
      <van-button type="primary" @click="saveAnnotation" :loading="saving">保存批注</van-button>
    </div>
    
    <!-- 文字输入弹窗 -->
    <van-dialog 
      v-model:show="showTextDialog" 
      title="添加文字" 
      show-cancel-button
      @confirm="addText"
    >
      <van-field v-model="textInput" placeholder="请输入文字" />
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { showToast, showSuccessToast } from 'vant'
import { createAnnotation } from '@/api/annotations'
import type { Annotation } from '@/api/annotations'

const props = defineProps<{
  imageId: string
  imageUrl: string
  editable?: boolean
  canSetExample?: boolean
  annotations?: Annotation[]
}>()

const emit = defineEmits<{
  (e: 'save', annotation: Annotation): void
  (e: 'cancel'): void
}>()

// refs
const containerRef = ref<HTMLDivElement>()
const canvasRef = ref<HTMLCanvasElement>()
const imageRef = ref<HTMLImageElement>()

// state
const ctx = ref<CanvasRenderingContext2D | null>(null)
const currentTool = ref('pencil')
const brushColor = ref('#ff0000')
const brushWidth = ref(3)
const isDrawing = ref(false)
const history = ref<ImageData[]>([])
const startPoint = ref({ x: 0, y: 0 })
const showTextDialog = ref(false)
const textInput = ref('')
const textPosition = ref({ x: 0, y: 0 })
const canvasSize = ref({ width: 800, height: 600 })

// 初始化画布
function initCanvas() {
  if (!canvasRef.value || !imageRef.value || !containerRef.value) return
  
  const img = imageRef.value
  const container = containerRef.value
  
  // 计算合适的画布尺寸
  const maxWidth = container.clientWidth - 20
  const maxHeight = 500
  
  let width = img.naturalWidth
  let height = img.naturalHeight
  
  // 缩放以适应容器
  if (width > maxWidth) {
    const ratio = maxWidth / width
    width = maxWidth
    height = height * ratio
  }
  if (height > maxHeight) {
    const ratio = maxHeight / height
    height = maxHeight
    width = width * ratio
  }
  
  canvasSize.value = { width, height }
  
  const canvas = canvasRef.value
  canvas.width = width
  canvas.height = height
  
  const context = canvas.getContext('2d')
  if (!context) return
  
  ctx.value = context
  
  // 绘制背景图片
  context.drawImage(img, 0, 0, width, height)
  
  // 保存初始状态
  saveHistory()
  
  console.log('画布初始化完成:', { width, height })
}

// 设置工具
function setTool(tool: string) {
  currentTool.value = tool
}

// 获取触摸/鼠标坐标
function getPoint(e: MouseEvent | TouchEvent): { x: number; y: number } {
  if (!canvasRef.value) return { x: 0, y: 0 }
  
  const rect = canvasRef.value.getBoundingClientRect()
  
  if ('touches' in e) {
    return {
      x: e.touches[0].clientX - rect.left,
      y: e.touches[0].clientY - rect.top
    }
  }
  
  return {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }
}

// 开始绘制
function startDrawing(e: MouseEvent | TouchEvent) {
  e.preventDefault()
  
  if (!ctx.value) return
  
  const point = getPoint(e)
  startPoint.value = point
  isDrawing.value = true
  
  if (currentTool.value === 'pencil') {
    ctx.value.beginPath()
    ctx.value.moveTo(point.x, point.y)
  } else if (currentTool.value === 'text') {
    textPosition.value = point
    showTextDialog.value = true
    isDrawing.value = false
  }
}

// 绘制中
function draw(e: MouseEvent | TouchEvent) {
  e.preventDefault()
  
  if (!isDrawing.value || !ctx.value) return
  
  const point = getPoint(e)
  
  if (currentTool.value === 'pencil') {
    ctx.value.lineTo(point.x, point.y)
    ctx.value.strokeStyle = brushColor.value
    ctx.value.lineWidth = brushWidth.value
    ctx.value.lineCap = 'round'
    ctx.value.lineJoin = 'round'
    ctx.value.stroke()
  }
}

// 结束绘制
function stopDrawing(e: MouseEvent | TouchEvent) {
  if (!isDrawing.value || !ctx.value) return
  
  const point = getPoint(e)
  
  if (currentTool.value === 'arrow') {
    drawArrow(startPoint.value, point)
  } else if (currentTool.value === 'circle') {
    drawCircle(startPoint.value, point)
  }
  
  isDrawing.value = false
  saveHistory()
}

// 绘制箭头
function drawArrow(start: { x: number; y: number }, end: { x: number; y: number }) {
  if (!ctx.value) return
  
  const headLength = 15
  const angle = Math.atan2(end.y - start.y, end.x - start.x)
  
  ctx.value.beginPath()
  ctx.value.moveTo(start.x, start.y)
  ctx.value.lineTo(end.x, end.y)
  ctx.value.strokeStyle = '#ff0000'
  ctx.value.lineWidth = 3
  ctx.value.stroke()
  
  // 箭头头部
  ctx.value.beginPath()
  ctx.value.moveTo(end.x, end.y)
  ctx.value.lineTo(
    end.x - headLength * Math.cos(angle - Math.PI / 6),
    end.y - headLength * Math.sin(angle - Math.PI / 6)
  )
  ctx.value.lineTo(
    end.x - headLength * Math.cos(angle + Math.PI / 6),
    end.y - headLength * Math.sin(angle + Math.PI / 6)
  )
  ctx.value.closePath()
  ctx.value.fillStyle = '#ff0000'
  ctx.value.fill()
}

// 绘制圆圈
function drawCircle(start: { x: number; y: number }, end: { x: number; y: number }) {
  if (!ctx.value) return
  
  const radius = Math.sqrt(
    Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2)
  )
  
  ctx.value.beginPath()
  ctx.value.arc(start.x, start.y, radius, 0, 2 * Math.PI)
  ctx.value.strokeStyle = '#ff0000'
  ctx.value.lineWidth = 3
  ctx.value.stroke()
}

// 添加文字
function addText() {
  if (!ctx.value || !textInput.value) return
  
  ctx.value.font = '16px sans-serif'
  ctx.value.fillStyle = '#ff0000'
  ctx.value.fillText(textInput.value, textPosition.value.x, textPosition.value.y)
  
  textInput.value = ''
  saveHistory()
}

// 保存历史
function saveHistory() {
  if (!ctx.value || !canvasRef.value) return
  
  const imageData = ctx.value.getImageData(0, 0, canvasRef.value.width, canvasRef.value.height)
  history.value.push(imageData)
  
  // 限制历史记录数量
  if (history.value.length > 20) {
    history.value.shift()
  }
}

// 撤销
function undo() {
  if (history.value.length <= 1 || !ctx.value || !canvasRef.value) return
  
  history.value.pop()
  const previousState = history.value[history.value.length - 1]
  
  if (previousState) {
    ctx.value.putImageData(previousState, 0, 0)
  }
}

// 清空画布
function clearCanvas() {
  if (!ctx.value || !canvasRef.value || !imageRef.value) return
  
  // 重新绘制背景图片
  ctx.value.drawImage(
    imageRef.value, 
    0, 0, 
    canvasSize.value.width, 
    canvasSize.value.height
  )
  
  history.value = []
  saveHistory()
}

// 保存批注
const saving = ref(false)

async function saveAnnotation() {
  if (!canvasRef.value || saving.value) return
  
  saving.value = true
  
  try {
    const dataUrl = canvasRef.value.toDataURL('image/png')
    
    // 调用保存API
    const annotation = await createAnnotation({
      image_id: props.imageId,
      annotation_data: {
        version: '1.0',
        objects: [],
        dataUrl: dataUrl
      } as any
    })
    
    showSuccessToast('批注保存成功')
    emit('save', annotation)
    return annotation  // 返回保存的结果
  } catch (error) {
    showToast('保存失败')
    console.error('批注保存失败:', error)
    throw error  // 抛出错误让外部处理
  } finally {
    saving.value = false
  }
}

// 暴露方法给父组件调用
defineExpose({
  saveAnnotation
})

onMounted(() => {
  // 图片加载后会调用 initCanvas
})
</script>

<style scoped>
.annotation-canvas {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.tool-group {
  display: flex;
  gap: 8px;
}

.tool-options {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.tool-options input[type="color"] {
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.canvas-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: auto;
  padding: 10px;
  min-height: 400px;
  background: #e8e8e8;
}

.background-image {
  display: none;
}

.drawing-canvas {
  border: 2px solid #ddd;
  background: #fff;
  cursor: crosshair;
  touch-action: none;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 12px;
  background: #fff;
  border-top: 1px solid #e0e0e0;
}
</style>
