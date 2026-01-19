<template>
  <div class="console-view">
    <!-- 顶部导航 -->
    <header class="console-header">
      <div class="header-left">
        <div class="logo">
          <el-icon :size="24"><Monitor /></el-icon>
          <span class="title">SkillMCP Agent Console</span>
        </div>
        <el-tag type="success" size="small">v0.1.0</el-tag>
      </div>
      
      <div class="header-right">
        <el-button text @click="showDebugPanel = !showDebugPanel">
          <el-icon><DataLine /></el-icon>
          调试面板
        </el-button>
        <el-button text @click="handleNewSession">
          <el-icon><Plus /></el-icon>
          新会话
        </el-button>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="console-main">
      <!-- 左侧：聊天区域 -->
      <section class="chat-section">
        <!-- 消息列表 -->
        <div class="message-list" ref="messageListRef">
          <!-- 欢迎提示 -->
          <div v-if="!chatStore.hasMessages" class="welcome-card">
            <div class="welcome-icon">🤖</div>
            <h2>欢迎使用 SkillMCP Agent</h2>
            <p>我可以帮你查询天气、火车票，或回答各种问题</p>
            <div class="quick-actions">
              <el-button 
                v-for="action in quickActions" 
                :key="action.text"
                round
                @click="handleQuickAction(action.text)"
              >
                {{ action.icon }} {{ action.text }}
              </el-button>
            </div>
          </div>

          <!-- 消息气泡 -->
          <MessageBubble
            v-for="msg in chatStore.messages"
            :key="msg.id"
            :message="msg"
          />

          <!-- 加载状态 -->
          <div v-if="chatStore.loading" class="loading-indicator">
            <AgentProgress :state="chatStore.agentState" />
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="input-area">
          <ChatInput @send="handleSend" :disabled="chatStore.loading" />
        </div>
      </section>

      <!-- 右侧：调试面板 -->
      <aside v-if="showDebugPanel" class="debug-section">
        <DebugPanel 
          :agentState="chatStore.agentState"
          :debugInfo="chatStore.debugInfo"
          :lastMessage="chatStore.lastMessage"
        />
      </aside>
    </main>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import AgentProgress from '@/components/debug/AgentProgress.vue'
import DebugPanel from '@/components/debug/DebugPanel.vue'

const chatStore = useChatStore()
const messageListRef = ref(null)
const showDebugPanel = ref(true)

// 快捷操作
const quickActions = [
  { icon: '🌤️', text: '北京今天天气怎么样？' },
  { icon: '🚄', text: '北京到上海的高铁' },
  { icon: '📚', text: '什么是 Agent？' },
]

// 发送消息
async function handleSend(content) {
  await chatStore.sendMessage(content)
  scrollToBottom()
}

// 快捷操作
function handleQuickAction(text) {
  handleSend(text)
}

// 新建会话
function handleNewSession() {
  chatStore.newSession()
}

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

// 监听消息变化，自动滚动
watch(() => chatStore.messages.length, () => {
  scrollToBottom()
})
</script>

<style lang="scss" scoped>
.console-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-color);
}

// 顶部导航
.console-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .logo {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .title {
        font-size: 18px;
        font-weight: 600;
        color: var(--text-primary);
      }
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

// 主内容区
.console-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

// 聊天区域
.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  
  .welcome-card {
    text-align: center;
    padding: 48px 24px;
    max-width: 500px;
    margin: 0 auto;
    
    .welcome-icon {
      font-size: 64px;
      margin-bottom: 16px;
    }
    
    h2 {
      font-size: 24px;
      margin-bottom: 8px;
      color: var(--text-primary);
    }
    
    p {
      color: var(--text-secondary);
      margin-bottom: 24px;
    }
    
    .quick-actions {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 12px;
    }
  }
  
  .loading-indicator {
    padding: 16px;
  }
}

.input-area {
  padding: 16px 24px 24px;
  background: var(--card-bg);
  border-top: 1px solid var(--border-color);
}

// 调试面板
.debug-section {
  width: 400px;
  border-left: 1px solid var(--border-color);
  background: var(--card-bg);
  overflow: hidden;
}
</style>
