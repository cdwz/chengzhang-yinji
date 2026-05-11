<template>
  <div class="message-page">
    <el-page-header @back="goBack">
      <template #content>
        <span class="title">消息中心</span>
      </template>
      <template #extra>
        <el-badge :value="unreadCount" v-if="unreadCount > 0">
          <el-button @click="handleMarkAllRead">全部已读</el-button>
        </el-badge>
      </template>
    </el-page-header>
    
    <!-- 筛选 -->
    <div class="filter-bar">
      <el-radio-group v-model="filterRead" @change="handleFilter">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="false">未读</el-radio-button>
        <el-radio-button label="true">已读</el-radio-button>
      </el-radio-group>
    </div>
    
    <!-- 消息列表 -->
    <div class="message-list">
      <el-empty v-if="messages.length === 0 && !loading" description="暂无消息" />
      
      <div 
        v-for="message in messages" 
        :key="message.id"
        class="message-item"
        :class="{ unread: !message.is_read }"
        @click="viewMessage(message)"
      >
        <div class="message-header">
          <span class="sender">
            <el-avatar v-if="message.sender_name" :size="32">{{ message.sender_name[0] }}</el-avatar>
            <el-avatar v-else :size="32" style="background: #409EFF">系</el-avatar>
            <span class="name">{{ message.sender_name || '系统通知' }}</span>
          </span>
          <span class="time">{{ formatTime(message.created_at) }}</span>
        </div>
        <div class="message-title">{{ message.title }}</div>
        <div class="message-content">{{ message.content }}</div>
        <div class="message-footer">
          <el-tag v-if="!message.is_read" type="primary" size="small">未读</el-tag>
          <el-tag v-else type="info" size="small">已读</el-tag>
        </div>
      </div>
      
      <!-- 加载更多 -->
      <div class="load-more" v-if="hasMore">
        <el-button :loading="loading" @click="loadMore">加载更多</el-button>
      </div>
    </div>
    
    <!-- 消息详情对话框 -->
    <el-dialog v-model="showDetail" title="消息详情" width="500px">
      <div class="detail-content" v-if="currentMessage">
        <h3>{{ currentMessage.title }}</h3>
        <div class="meta">
          <span>发送者：{{ currentMessage.sender_name || '系统' }}</span>
          <span>时间：{{ formatTime(currentMessage.created_at) }}</span>
        </div>
        <div class="body">{{ currentMessage.content }}</div>
      </div>
      <template #footer>
        <el-button type="primary" @click="closeDetail">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getMessages, markMessageRead, markAllRead } from '@/api/messages'
import type { Message } from '@/api/messages'

const router = useRouter()

const messages = ref<Message[]>([])
const loading = ref(false)
const hasMore = ref(true)
const page = ref(1)
const unreadCount = ref(0)
const filterRead = ref('')

const showDetail = ref(false)
const currentMessage = ref<Message | null>(null)

// 加载消息
async function loadMessages() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: 20 }
    if (filterRead.value !== '') {
      params.is_read = filterRead.value === 'true'
    }
    
    const response = await getMessages(params)
    
    if (page.value === 1) {
      messages.value = response.items
    } else {
      messages.value.push(...response.items)
    }
    
    unreadCount.value = response.unread_count
    hasMore.value = messages.value.length < response.total
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

// 加载更多
function loadMore() {
  page.value++
  loadMessages()
}

// 筛选
function handleFilter() {
  page.value = 1
  messages.value = []
  loadMessages()
}

// 全部已读
async function handleMarkAllRead() {
  try {
    await markAllRead()
    ElMessage.success('已全部标记为已读')
    messages.value.forEach(m => m.is_read = true)
    unreadCount.value = 0
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 查看消息
async function viewMessage(message: Message) {
  currentMessage.value = message
  showDetail.value = true
  
  if (!message.is_read) {
    try {
      await markMessageRead(message.id)
      message.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (error) {
      console.error('标记已读失败', error)
    }
  }
}

// 关闭详情
function closeDetail() {
  showDetail.value = false
}

// 返回
function goBack() {
  router.back()
}

// 格式化时间
function formatTime(time: string) {
  const date = new Date(time)
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadMessages()
})
</script>

<style scoped>
.message-page {
  padding: 20px;
}

.title {
  font-size: 18px;
  font-weight: 500;
}

.filter-bar {
  margin: 20px 0;
}

.message-list {
  background: #fff;
  border-radius: 8px;
}

.message-item {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.2s;
}

.message-item:hover {
  background: #fafafa;
}

.message-item.unread {
  background: #e8f4ff;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.sender {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sender .name {
  font-weight: 500;
}

.time {
  color: #999;
  font-size: 12px;
}

.message-title {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.message-content {
  font-size: 14px;
  color: #666;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.message-footer {
  margin-top: 8px;
  text-align: right;
}

.load-more {
  text-align: center;
  padding: 20px;
}

.detail-content h3 {
  margin: 0 0 12px 0;
}

.detail-content .meta {
  color: #999;
  font-size: 14px;
  margin-bottom: 16px;
  display: flex;
  gap: 16px;
}

.detail-content .body {
  font-size: 15px;
  line-height: 1.8;
  color: #333;
}
</style>
