<template>
  <div class="annotation-canvas">
    <!-- 工具栏 -->
    <div class="toolbar" v-if="editable">
      <el-button-group>
        <el-button 
          :type="currentTool === 'select' ? 'primary' : 'default'"
          @click="setTool('select')"
        >
          <el-icon><Pointer /></el-icon> 选择
        </el-button>
        <el-button 
          :type="currentTool === 'pencil' ? 'primary' : 'default'"
          @click="setTool('pencil')"
        >
          <el-icon><Edit /></el-icon> 画笔
        </el-button>
        <el-button 
          :type="currentTool === 'arrow' ? 'primary' : 'default'"
          @click="setTool('arrow')"
        >
          <el-icon><TopRight /></el-icon> 箭头
        </el-button>
        <el-button 
          :type="currentTool === 'circle' ? 'primary' : 'default'"
          @click="setTool('circle')"
        >
          <el-icon><CircleCheck /></el-icon> 圆圈
        </el-button>
        <el-button 
          :type="currentTool === 'text' ? 'primary' : 'default'"
          @click="setTool('text')"
        >
          <el-icon><ChatDotSquare /></el-icon> 文字
        </el-button>
      </el-button-group>
      
      <div class="tool-options" v-if="currentTool === 'pencil'">
        <el-color-picker v-model="brushColor" size="small" />
        <el-slider v-model="brushWidth" :min="1" :max="20" :show-tooltip="false" style="width: 100px" />
      </div>
      
      <el-button-group>
        <el-button @click="undo" :disabled="!canUndo">
          <el-icon><RefreshLeft /></el-icon> 撤销
        </el-button>
        <el-button @click="clearCanvas" type="danger">
          <el-icon><Delete /></el-icon> 清空
        </el-button>
      </el-button-group>
    </div>
    
    <!-- 画布容器 -->
    <div class="canvas-container" ref="containerRef">
      <canvas ref="canvasRef"></canvas>
      <!-- 图片层 -->
      <img 
        v-if="imageUrl" 
        :src="imageUrl" 
        class="background-image"
        @load="initCanvas"
        ref="imageRef"
      />
    </div>
    
    <!-- 操作按钮 -->
    <div class="actions" v-if="editable">
      <el-button @click="$emit('cancel')">取消</el-button>
      <el-button type="primary" @click="saveAnnotation">保存批注</el-button>
    </div>
    
    <!-- 查看模式显示批注列表 -->
    <div class="annotations-list" v-if="!editable && annotations.length > 0">
      <h4>批注记录</h4>
      <div 
        v-for="annotation in annotations" 
        :key="annotation.id"
        class="annotation-item"
        :class="{ 'is-example': annotation.is_example }"
      >
        <div class="annotation-info">
          <span class="teacher">{{ annotation.teacher_name }}</span>
          <span class="time">{{ formatTime(annotation.created_at) }}</span>
          <el-tag v-if="annotation.is_example" type="success" size="small">典型例</el-tag>
        </div>
        <div class="annotation-actions">
          <el-button size="small" @click="viewAnnotation(annotation)">查看</el-button>
          <el-button 
            v-if="canSetExample" 
            size="small" 
            :type="annotation.is_example ? 'warning' : 'success'"
            @click="toggleExample(annotation)"
          >
            {{ annotation.is_example ? '取消典型' : '设为典型' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { Pointer, Edit, TopRight, CircleCheck, ChatDotSquare, RefreshLeft, Delete } from '@element-plus/icons-vue'
import * as fabric from 'fabric'
import { createAnnotation, setAsExample, getImageAnnotations } from '@/api/annotations'
import type { Annotation, AnnotationData } from '@/api/annotations'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  imageId: string
  imageUrl: string
  editable?: boolean
  canSetExample?: boolean
}>()

const emit = defineEmits<{
  (e: 'saved', annotation: Annotation): void
  (e: 'cancel'): void
}>()

// refs
const containerRef = ref<HTMLDivElement>()
const canvasRef = ref<HTMLCanvasElement>()
const imageRef = ref<HTMLImageElement>()

// state
const canvas = ref<fabric.Canvas>()
const currentTool = ref('select')
const brushColor = ref('#ff0000')
const brushWidth = ref(3)
const annotations = ref<Annotation[]>([])
const history = ref<any[]>([])

const canUndo = computed(() => history.value.length > 0)

// 初始化画布
function initCanvas() {
  if (!canvasRef.value || !imageRef.value) return
  
  const img = imageRef.value
  const width = img.naturalWidth
  const height = img.naturalHeight
  
  // 创建 Fabric 画布
  canvas.value = new fabric.Canvas(canvasRef.value, {
    width: Math.min(width, 800),
    height: Math.min(height, 600),
    selection: true
  })
  
  // 设置背景图片
  fabric.Image.fromURL(props.imageUrl, (img) => {
    canvas.value?.setBackgroundImage(img, () => {
      canvas.value?.renderAll()
    }, {
      scaleX: canvas.value!.width! / (img.width || 1),
      scaleY: canvas.value!.height! / (img.height || 1)
    })
  })
  
  // 设置自由绘制
  canvas.value.freeDrawingBrush = new fabric.PencilBrush(canvas.value)
  canvas.value.freeDrawingBrush.color = brushColor.value
  canvas.value.freeDrawingBrush.width = brushWidth.value
  
  // 监听对象添加
  canvas.value.on('object:added', () => {
    saveHistory()
  })
  
  // 加载已有批注
  loadAnnotations()
}

// 设置工具
function setTool(tool: string) {
  currentTool.value = tool
  if (!canvas.value) return
  
  switch (tool) {
    case 'select':
      canvas.value.isDrawingMode = false
      canvas.value.selection = true
      break
    case 'pencil':
      canvas.value.isDrawingMode = true
      canvas.value.freeDrawingBrush.color = brushColor.value
      canvas.value.freeDrawingBrush.width = brushWidth.value
      break
    case 'arrow':
      canvas.value.isDrawingMode = false
      canvas.value.selection = false
      enableArrowDrawing()
      break
    case 'circle':
      canvas.value.isDrawingMode = false
      canvas.value.selection = false
      enableCircleDrawing()
      break
    case 'text':
      canvas.value.isDrawingMode = false
      canvas.value.selection = false
      enableTextAdding()
      break
  }
}

// 启用箭头绘制
function enableArrowDrawing() {
  let startPoint: fabric.Point | null = null
  
  canvas.value?.on('mouse:down', (opt) => {
    startPoint = canvas.value!.getPointer(opt.e)
  })
  
  canvas.value?.on('mouse:up', (opt) => {
    if (!startPoint) return
    const endPoint = canvas.value!.getPointer(opt.e)
    
    // 创建箭头
    const line = new fabric.Line([
      startPoint.x, startPoint.y,
      endPoint.x, endPoint.y
    ], {
      stroke: '#ff0000',
      strokeWidth: 3
    })
    
    // 箭头头部
    const angle = Math.atan2(endPoint.y - startPoint.y, endPoint.x - startPoint.x)
    const arrowHead = new fabric.Triangle({
      left: endPoint.x,
      top: endPoint.y,
      width: 15,
      height: 15,
      fill: '#ff0000',
      angle: (angle * 180 / Math.PI) + 90
    })
    
    const group = new fabric.Group([line, arrowHead])
    canvas.value?.add(group)
    
    startPoint = null
  })
}

// 启用圆圈绘制
function enableCircleDrawing() {
  let startPoint: fabric.Point | null = null
  
  canvas.value?.on('mouse:down', (opt) => {
    startPoint = canvas.value!.getPointer(opt.e)
  })
  
  canvas.value?.on('mouse:up', (opt) => {
    if (!startPoint) return
    const endPoint = canvas.value!.getPointer(opt.e)
    
    const radius = Math.sqrt(
      Math.pow(endPoint.x - startPoint.x, 2) +
      Math.pow(endPoint.y - startPoint.y, 2)
    )
    
    const circle = new fabric.Circle({
      left: startPoint.x - radius,
      top: startPoint.y - radius,
      radius: radius,
      fill: 'transparent',
      stroke: '#ff0000',
      strokeWidth: 3
    })
    
    canvas.value?.add(circle)
    startPoint = null
  })
}

// 启用文字添加
function enableTextAdding() {
  canvas.value?.on('mouse:up', (opt) => {
    const pointer = canvas.value!.getPointer(opt.e)
    
    const text = new fabric.IText('点击输入文字', {
      left: pointer.x,
      top: pointer.y,
      fontSize: 16,
      fill: '#ff0000'
    })
    
    canvas.value?.add(text)
    canvas.value?.setActiveObject(text)
    text.enterEditing()
    
    // 移除监听，避免重复添加
    canvas.value?.off('mouse:up')
    setTool('select')
  })
}

// 保存历史
function saveHistory() {
  const json = canvas.value?.toJSON()
  history.value.push(json)
  if (history.value.length > 20) {
    history.value.shift()
  }
}

// 撤销
function undo() {
  if (history.value.length === 0 || !canvas.value) return
  
  history.value.pop()
  const previousState = history.value[history.value.length - 1]
  
  if (previousState) {
    canvas.value.loadFromJSON(previousState, () => {
      canvas.value?.renderAll()
    })
  }
}

// 清空画布
function clearCanvas() {
  if (!canvas.value) return
  
  canvas.value.getObjects().forEach(obj => {
    canvas.value?.remove(obj)
  })
  canvas.value.renderAll()
  history.value = []
}

// 加载已有批注
async function loadAnnotations() {
  try {
    const response = await getImageAnnotations(props.imageId)
    annotations.value = response.annotations
    
    // 如果只有一个批注，加载到画布
    if (response.annotations.length === 1) {
      const annotationData = response.annotations[0].annotation_data
      if (annotationData && annotationData.objects) {
        canvas.value?.loadFromJSON(annotationData, () => {
          canvas.value?.renderAll()
        })
      }
    }
  } catch (error) {
    console.error('加载批注失败', error)
  }
}

// 保存批注
async function saveAnnotation() {
  if (!canvas.value) return
  
  const annotationData = canvas.value.toJSON() as AnnotationData
  
  try {
    const annotation = await createAnnotation({
      image_id: props.imageId,
      annotation_data: annotationData
    })
    
    ElMessage.success('批注保存成功')
    emit('saved', annotation)
  } catch (error) {
    ElMessage.error('保存失败')
    console.error(error)
  }
}

// 查看批注
function viewAnnotation(annotation: Annotation) {
  if (!canvas.value) return
  
  const data = annotation.annotation_data
  if (data && data.objects) {
    canvas.value.loadFromJSON(data, () => {
      canvas.value?.renderAll()
    })
  }
}

// 切换典型例
async function toggleExample(annotation: Annotation) {
  try {
    const result = await setAsExample(annotation.id)
    annotation.is_example = result.is_example
    ElMessage.success(result.message)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 格式化时间
function formatTime(time: string) {
  return new Date(time).toLocaleString('zh-CN')
}

// 监听画笔颜色变化
watch(brushColor, (color) => {
  if (canvas.value?.freeDrawingBrush) {
    canvas.value.freeDrawingBrush.color = color
  }
})

// 监听画笔宽度变化
watch(brushWidth, (width) => {
  if (canvas.value?.freeDrawingBrush) {
    canvas.value.freeDrawingBrush.width = width
  }
})

onMounted(() => {
  // 图片加载后会调用 initCanvas
})
</script>

<style scoped>
.annotation-canvas {
  background: #f5f5f5;
  border-radius: 8px;
  overflow: hidden;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.tool-options {
  display: flex;
  align-items: center;
  gap: 8px;
}

.canvas-container {
  position: relative;
  min-height: 400px;
}

.background-image {
  display: none;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 12px;
  background: #fff;
  border-top: 1px solid #e0e0e0;
}

.annotations-list {
  padding: 12px;
  background: #fff;
  border-top: 1px solid #e0e0e0;
}

.annotations-list h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #333;
}

.annotation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 8px;
  background: #f9f9f9;
}

.annotation-item.is-example {
  background: #f0f9eb;
}

.annotation-info {
  display: flex;
  gap: 12px;
  align-items: center;
}

.teacher {
  font-weight: 500;
}

.time {
  color: #999;
  font-size: 12px;
}

.annotation-actions {
  display: flex;
  gap: 8px;
}
</style>
