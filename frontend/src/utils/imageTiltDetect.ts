/**
 * 图像倾斜检测工具
 * 用于检测相册上传的照片是否倾斜，过歪时提示家长重新拍照
 */

export interface TiltResult {
  angle: number;         // 倾斜角度（度）
  isTilted: boolean;     // 是否过歪
  confidence: number;    // 检测置信度 0-1
  direction: 'left' | 'right' | 'none';  // 倾斜方向
}

// 倾斜阈值（度）
const TILT_THRESHOLD = 15
// 低置信度阈值
const LOW_CONFIDENCE_THRESHOLD = 0.3

/**
 * 检测图像倾斜
 * 使用边缘检测和霍夫变换检测图像中的主要线条角度
 * 
 * @param image 图像元素
 * @returns 倾斜检测结果
 */
export async function detectTilt(image: HTMLImageElement): Promise<TiltResult> {
  return new Promise((resolve) => {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    
    if (!ctx) {
      resolve({ angle: 0, isTilted: false, confidence: 0, direction: 'none' })
      return
    }
    
    // 缩小图像加速处理
    const maxSize = 400
    const scale = Math.min(maxSize / image.width, maxSize / image.height, 1)
    canvas.width = Math.round(image.width * scale)
    canvas.height = Math.round(image.height * scale)
    
    ctx.drawImage(image, 0, 0, canvas.width, canvas.height)
    
    // 获取图像数据
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const data = imageData.data
    
    // 转换为灰度并检测边缘
    const grayData = toGrayscale(data, canvas.width, canvas.height)
    const edges = detectEdges(grayData, canvas.width, canvas.height)
    
    // 使用简化的霍夫变换检测主要线条角度
    const angles = detectLines(edges, canvas.width, canvas.height)
    
    // 分析角度分布
    const result = analyzeAngles(angles)
    
    resolve(result)
  })
}

/**
 * RGB 转灰度
 */
function toGrayscale(data: Uint8ClampedArray, width: number, height: number): Uint8Array {
  const gray = new Uint8Array(width * height)
  
  for (let i = 0; i < width * height; i++) {
    const idx = i * 4
    // 使用加权平均
    gray[i] = Math.round(0.299 * data[idx] + 0.587 * data[idx + 1] + 0.114 * data[idx + 2])
  }
  
  return gray
}

/**
 * 简化的边缘检测（Sobel算子）
 */
function detectEdges(gray: Uint8Array, width: number, height: number): Uint8Array {
  const edges = new Uint8Array(width * height)
  
  // Sobel 卷积核
  const sobelX = [-1, 0, 1, -2, 0, 2, -1, 0, 1]
  const sobelY = [-1, -2, -1, 0, 0, 0, 1, 2, 1]
  
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      let gx = 0, gy = 0
      
      // 3x3 卷积
      for (let ky = -1; ky <= 1; ky++) {
        for (let kx = -1; kx <= 1; kx++) {
          const idx = (y + ky) * width + (x + kx)
          const kernelIdx = (ky + 1) * 3 + (kx + 1)
          gx += gray[idx] * sobelX[kernelIdx]
          gy += gray[idx] * sobelY[kernelIdx]
        }
      }
      
      // 梯度幅值
      const magnitude = Math.sqrt(gx * gx + gy * gy)
      edges[y * width + x] = magnitude > 50 ? 255 : 0
    }
  }
  
  return edges
}

/**
 * 简化的霍夫变换检测线条
 */
function detectLines(edges: Uint8Array, width: number, height: number): number[] {
  const angles: number[] = []
  
  // 角度直方图（-90 到 90 度）
  const angleHistogram = new Map<number, number>()
  
  // 遍历边缘点
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      if (edges[y * width + x] === 0) continue
      
      // 计算局部梯度方向
      let dx = 0, dy = 0
      for (let ky = -1; ky <= 1; ky++) {
        for (let kx = -1; kx <= 1; kx++) {
          dx += edges[(y + ky) * width + (x + kx)] * kx
          dy += edges[(y + ky) * width + (x + kx)] * ky
        }
      }
      
      if (dx === 0 && dy === 0) continue
      
      // 计算角度（度）
      let angle = Math.atan2(dy, dx) * (180 / Math.PI)
      
      // 只关注接近水平或垂直的线条（作业通常是水平放置的）
      // 将角度归一化到 -45 到 45 度范围
      if (angle > 45) angle -= 90
      if (angle < -45) angle += 90
      
      // 量化到 5 度间隔
      const quantizedAngle = Math.round(angle / 5) * 5
      angleHistogram.set(quantizedAngle, (angleHistogram.get(quantizedAngle) || 0) + 1)
    }
  }
  
  // 找出出现频率最高的角度
  let maxCount = 0
  
  for (const [, count] of angleHistogram) {
    if (count > maxCount) {
      maxCount = count
    }
  }
  
  // 收集主要角度（出现频率超过最大值50%的角度）
  const threshold = maxCount * 0.5
  for (const [angle, count] of angleHistogram) {
    if (count >= threshold) {
      angles.push(angle)
    }
  }
  
  return angles
}

/**
 * 分析角度分布，判断是否倾斜
 */
function analyzeAngles(angles: number[]): TiltResult {
  if (angles.length === 0) {
    return { angle: 0, isTilted: false, confidence: 0, direction: 'none' }
  }
  
  // 计算平均角度
  const avgAngle = angles.reduce((a, b) => a + b, 0) / angles.length
  
  // 计算角度方差
  const variance = angles.reduce((sum, a) => sum + Math.pow(a - avgAngle, 2), 0) / angles.length
  const stdDev = Math.sqrt(variance)
  
  // 置信度：角度越集中，置信度越高
  const confidence = Math.max(0, 1 - stdDev / 30)
  
  // 判断是否倾斜
  const absAngle = Math.abs(avgAngle)
  const isTilted = absAngle > TILT_THRESHOLD && confidence > LOW_CONFIDENCE_THRESHOLD
  
  // 判断倾斜方向
  let direction: 'left' | 'right' | 'none' = 'none'
  if (avgAngle > TILT_THRESHOLD) {
    direction = 'right'
  } else if (avgAngle < -TILT_THRESHOLD) {
    direction = 'left'
  }
  
  return {
    angle: Math.round(avgAngle * 10) / 10,
    isTilted,
    confidence: Math.round(confidence * 100) / 100,
    direction
  }
}

/**
 * 从文件创建图像元素
 */
export function createImageFromFile(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve(img)
    }
    
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('无法加载图像'))
    }
    
    img.src = url
  })
}

/**
 * 检测文件倾斜（便捷方法）
 */
export async function detectFileTilt(file: File): Promise<TiltResult> {
  try {
    const img = await createImageFromFile(file)
    return await detectTilt(img)
  } catch (error) {
    console.error('倾斜检测失败:', error)
    return { angle: 0, isTilted: false, confidence: 0, direction: 'none' }
  }
}
