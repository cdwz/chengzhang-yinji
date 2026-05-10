/**
 * 图像压缩工具
 * 用于上传前自动压缩照片，减少网络传输和存储空间
 */

export interface CompressOptions {
  maxWidth?: number;      // 最长边，默认 1920
  maxHeight?: number;     // 最大高度，默认 2560 (A4比例)
  quality?: number;       // 压缩质量 0-1，默认 0.8
  mimeType?: string;      // 输出格式，默认 image/jpeg
}

const DEFAULT_OPTIONS: Required<CompressOptions> = {
  maxWidth: 1920,
  maxHeight: 2560,  // A4比例 (210:297 ≈ 1:1.414)
  quality: 0.8,
  mimeType: 'image/jpeg'
}

/**
 * 压缩图像文件
 * @param file 原始图像文件
 * @param options 压缩选项
 * @returns 压缩后的文件
 */
export async function compressImage(
  file: File,
  options?: CompressOptions
): Promise<File> {
  const opts = { ...DEFAULT_OPTIONS, ...options }
  
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    
    img.onload = () => {
      URL.revokeObjectURL(url)
      
      // 计算压缩后的尺寸
      let { width, height } = img
      const ratio = width / height
      
      // 按最长边缩放
      if (width > opts.maxWidth || height > opts.maxHeight) {
        if (ratio > opts.maxWidth / opts.maxHeight) {
          // 宽度为主
          width = opts.maxWidth
          height = Math.round(width / ratio)
        } else {
          // 高度为主
          height = opts.maxHeight
          width = Math.round(height * ratio)
        }
      }
      
      // 创建 Canvas 进行压缩
      const canvas = document.createElement('canvas')
      canvas.width = width
      canvas.height = height
      
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        reject(new Error('无法创建 Canvas 上下文'))
        return
      }
      
      // 使用高质量缩放
      ctx.imageSmoothingEnabled = true
      ctx.imageSmoothingQuality = 'high'
      
      // 绘制图像
      ctx.drawImage(img, 0, 0, width, height)
      
      // 转换为 Blob
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            reject(new Error('图像压缩失败'))
            return
          }
          
          // 创建新文件，保留原文件名
          const compressedFile = new File([blob], file.name.replace(/\.[^/.]+$/, '.jpg'), {
            type: opts.mimeType,
            lastModified: Date.now()
          })
          
          resolve(compressedFile)
        },
        opts.mimeType,
        opts.quality
      )
    }
    
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('图像加载失败'))
    }
    
    img.src = url
  })
}

/**
 * 批量压缩图像
 * @param files 图像文件数组
 * @param options 压缩选项
 * @param onProgress 进度回调
 * @returns 压缩后的文件数组
 */
export async function compressImages(
  files: File[],
  options?: CompressOptions,
  onProgress?: (current: number, total: number) => void
): Promise<File[]> {
  const results: File[] = []
  
  for (let i = 0; i < files.length; i++) {
    try {
      const compressed = await compressImage(files[i], options)
      results.push(compressed)
      onProgress?.(i + 1, files.length)
    } catch (error) {
      console.error(`压缩第 ${i + 1} 张图片失败:`, error)
      // 压缩失败时使用原图
      results.push(files[i])
    }
  }
  
  return results
}

/**
 * 获取图像尺寸信息
 * @param file 图像文件
 * @returns 宽度和高度
 */
export async function getImageDimensions(file: File): Promise<{ width: number; height: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image()
    const url = URL.createObjectURL(file)
    
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve({ width: img.width, height: img.height })
    }
    
    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('无法加载图像'))
    }
    
    img.src = url
  })
}

/**
 * 检查文件是否为图像
 * @param file 文件
 * @returns 是否为图像
 */
export function isImageFile(file: File): boolean {
  return file.type.startsWith('image/')
}
