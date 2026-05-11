<template>
  <div class="message-page">
    <van-nav-bar title="消息通知">
      <template #right>
        <van-badge :content="unreadCount" v-if="unreadCount > 0">
          <van-icon name="bell" size="20" />
        </van-badge>
        <van-icon v-else name="bell" size="20" />
      </template>
    </van-nav-bar>
    
    <!-- 消息列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多消息了"
        @load="loadMessages"
      >
        <div 
          v-for="message in messages" 
          :key="message.id"
          class="message-item"
          :class="{ unread: !message.is_read }"
          @click="viewMessage(message)"
        >
          <div class="message-header">
            <span class="sender">{{ message.sender_name || '系统' }}</span>
            <span class="time">{{ formatTime(message.created_at) }}</span>
          </div>
          <div class="message-title">{{ message.title }}</div>
          <div class="message-content">{{ message.content }}</div>
          <div class="message-status">
            <van-tag v-if="!message.is_read" type="primary">未读</van-tag>
            <van-tag v-else type="default">已读</van-tag>
          </div>
        </div>
        
        <van-empty v-if="!loading && messages.length === 0" description="暂无消息" />
      </van-list>
    </van-pull-refresh>
    
    <!-- 消息详情弹窗 -->
    <van-popup v-model:show="showDetail" position="bottom" round style="height: 60%">
      <div class="message-detail" v-if="currentMessage">
        <div class="detail-header">
          <h3>{{ currentMessage.title }}</h3>
          <div class="meta">
            <span>{{ currentMessage.sender_name || '系统' }}</span>
            <span>{{ formatTime(currentMessage.created_at) }}</span>
          </div>
        </div>
        <div class="detail-content">
          {{ currentMessage.content }}
        </div>
        <div class="detail-actions">
          <van-button block type="primary" @click="closeDetail">确定</van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { showToast } from 'vant'
import { getMessages, getUnreadCount, markMessageRead } from '@/api/messages'
import type { Message } from '@/api/messages'

const messages = ref<Message[]>([])
const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)
const page = ref(1)
const unreadCount = ref(0)

const showDetail = ref(false)
const currentMessage = ref<Message | null>(null)

// 加载消息
async function loadMessages() {
  try {
    const response = await getMessages({
      page: page.value,
      page_size: 20
    })
    
    messages.value.push(...response.items)
    unreadCount.value = response.unread_count
    page.value++
    
    if (messages.value.length >= response.total) {
      finished.value = true
    }
  } catch (error) {
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

// 下拉刷新
async function onRefresh() {
  page.value = 1
  messages.value = []
  finished.value = false
  await loadMessages()
  refreshing.value = false
}

// 查看消息
async function viewMessage(message: Message) {
  currentMessage.value = message
  showDetail.value = true
  
  // 标记已读
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

// 格式化时间
function formatTime(time: string) {
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // 今天
  if (diff < 24 * 60 * 60 * 1000) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  // 昨天
  if (diff < 48 * 60 * 60 * 1000) {
    return '昨天'
  }
  // 其他
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

onMounted(() => {
  getUnreadCount().then(res => {
    unreadCount.value = res.unread_count
  })
})
</script>

<style scoped>
.message-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.message-item {
  background: #fff;
  padding: 16px;
  margin-bottom: 8px;
}

.message-item.unread {
  background: #e8f4ff;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.sender {
  font-weight: 500;
  color: #333;
}

.time {
  color: #999;
  font-size: 12px;
}

.message-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.message-content {
  font-size: 14px;
  color: #666;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.message-status {
  margin-top: 8px;
  text-align: right;
}

.message-detail {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.detail-header {
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 16px;
  margin-bottom: 16px;
}

.detail-header h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
}

.meta {
  display: flex;
  gap: 16px;
  color: #999;
  font-size: 14px;
}

.detail-content {
  flex: 1;
  font-size: 16px;
  line-height: 1.8;
  color: #333;
}

.detail-actions {
  padding-top: 16px;
}
</style>
