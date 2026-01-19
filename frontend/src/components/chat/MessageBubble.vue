<template>
  <div class="message-bubble" :class="[message.role, { error: message.isError }]">
    <!-- 头像 -->
    <div class="avatar">
      <el-avatar :size="36" :style="avatarStyle">
        {{ message.role === 'user' ? '我' : '🤖' }}
      </el-avatar>
    </div>

    <!-- 消息内容 -->
    <div class="content-wrapper">
      <div class="meta">
        <span class="role-name">{{ message.role === 'user' ? '用户' : 'Agent' }}</span>
        <span class="time">{{ formatTime(message.timestamp) }}</span>
      </div>

      <!-- 消息正文 -->
      <div class="content" v-html="renderContent"></div>

      <!-- 结构化数据卡片 -->
      <div v-if="message.structuredData?.length" class="structured-data">
        <StructuredCard
          v-for="(data, index) in message.structuredData"
          :key="index"
          :type="data.type"
          :data="data.data"
        />
      </div>

      <!-- 来源标签 -->
      <div v-if="message.sources?.length" class="sources">
        <el-tag
          v-for="source in message.sources"
          :key="source"
          size="small"
          type="info"
        >
          {{ source }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import StructuredCard from './StructuredCard.vue'

const props = defineProps({
  message: {
    type: Object,
    required: true,
  },
})

// 头像样式
const avatarStyle = computed(() => {
  return props.message.role === 'user'
    ? { background: '#409eff' }
    : { background: '#67c23a' }
})

// 渲染 Markdown 内容
const renderContent = computed(() => {
  if (props.message.role === 'user') {
    return props.message.content
  }
  return marked.parse(props.message.content || '')
})

// 格式化时间
function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style lang="scss" scoped>
.message-bubble {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  
  &.user {
    flex-direction: row-reverse;
    
    .content-wrapper {
      align-items: flex-end;
    }
    
    .content {
      background: #409eff;
      color: white;
      border-radius: 16px 4px 16px 16px;
    }
    
    .meta {
      flex-direction: row-reverse;
    }
  }
  
  &.assistant {
    .content {
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 4px 16px 16px 16px;
    }
  }
  
  &.error {
    .content {
      background: #fef0f0;
      border-color: #fde2e2;
      color: #f56c6c;
    }
  }
}

.avatar {
  flex-shrink: 0;
}

.content-wrapper {
  display: flex;
  flex-direction: column;
  max-width: 70%;
  min-width: 120px;
}

.meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 12px;
  color: var(--text-secondary);
  
  .role-name {
    font-weight: 500;
  }
}

.content {
  padding: 12px 16px;
  line-height: 1.6;
  word-break: break-word;
  
  :deep(p) {
    margin: 0;
    
    &:not(:last-child) {
      margin-bottom: 8px;
    }
  }
  
  :deep(ul), :deep(ol) {
    margin: 8px 0;
    padding-left: 20px;
  }
  
  :deep(code) {
    background: rgba(0, 0, 0, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 13px;
  }
  
  :deep(pre) {
    margin: 8px 0;
    padding: 12px;
    background: #1e1e1e;
    border-radius: 8px;
    overflow-x: auto;
    
    code {
      background: transparent;
      padding: 0;
      color: #d4d4d4;
    }
  }
}

.structured-data {
  margin-top: 12px;
}

.sources {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
</style>
