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
      <van-uploader
        v-model="imageList"
        multiple
        :max-count="9"
        :max-size="10 * 1024 * 1024"
        :after-read="handleAfterRead"
        @delete="handleDeleteImage"
      >
        <van-button type="primary" size="small" icon="photograph">拍照记录</van-button>
      </van-uploader>
      
      <div v-if="imageList.length > 0" class="image-preview">
        <van-grid :column-num="3" :gutter="8">
          <van-grid-item v-for="(img, index) in imageList" :key="index">
            <van-image :src="img.url || img.content" fit="cover" />
          </van-grid-item>
        </van-grid>
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showSuccessToast, showFailToast, showImagePreview } from 'vant'
import { http } from '@/utils/request'
import type { Task, TaskSubmission } from '@/api/types'

const route = useRoute()
const router = useRouter()

// 状态
const task = ref<Task | null>(null)
const submission = ref<TaskSubmission | null>(null)
const imageList = ref<any[]>([])
const feedback = ref('')
const submitting = ref(false)

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

// 处理图片选择
const handleAfterRead = (file: any) => {
  // 这里可以添加图片压缩逻辑
  console.log('Selected file:', file)
}

// 删除图片
const handleDeleteImage = (_file: any, index: number) => {
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

    showSuccessToast('提交成功')
    router.push('/parent/tasks')
  } catch (error: any) {
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
    
    .image-preview {
      margin-top: 12px;
    }
  }
  
  .submit-section {
    margin-top: 12px;
    padding: 12px;
    background: #fff;
    
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
