<template>
  <div class="debug-panel">
    <div class="panel-header">
      <h3>🔍 调试面板</h3>
    </div>

    <el-scrollbar class="panel-content">
      <!-- Agent 状态 -->
      <el-collapse v-model="activeNames">
        <!-- 执行步骤 -->
        <el-collapse-item title="执行步骤" name="steps">
          <template #title>
            <div class="collapse-title">
              <el-icon><List /></el-icon>
              <span>执行步骤</span>
              <el-badge :value="agentState.steps?.length || 0" type="info" />
            </div>
          </template>
          
          <div v-if="agentState.steps?.length" class="step-list">
            <div 
              v-for="(step, index) in agentState.steps" 
              :key="index"
              class="step-item"
              :class="step.type"
            >
              <div class="step-header">
                <span class="step-type">{{ getStepIcon(step.type) }} {{ step.title }}</span>
                <el-tag size="small" :type="step.status === 'completed' ? 'success' : 'info'">
                  {{ step.status }}
                </el-tag>
              </div>
              <div v-if="step.data" class="step-data">
                <pre>{{ JSON.stringify(step.data, null, 2) }}</pre>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无执行步骤" :image-size="60" />
        </el-collapse-item>

        <!-- 结构化数据 -->
        <el-collapse-item title="结构化数据" name="structured">
          <template #title>
            <div class="collapse-title">
              <el-icon><Grid /></el-icon>
              <span>结构化数据</span>
            </div>
          </template>
          
          <div v-if="lastMessage?.structuredData?.length" class="data-list">
            <div 
              v-for="(data, index) in lastMessage.structuredData" 
              :key="index"
              class="data-item"
            >
              <div class="data-type">{{ data.type }}</div>
              <pre class="data-content">{{ JSON.stringify(data.data, null, 2) }}</pre>
            </div>
          </div>
          <el-empty v-else description="暂无结构化数据" :image-size="60" />
        </el-collapse-item>

        <!-- RAG 来源 -->
        <el-collapse-item title="RAG 来源" name="sources">
          <template #title>
            <div class="collapse-title">
              <el-icon><Document /></el-icon>
              <span>RAG 来源</span>
            </div>
          </template>
          
          <div v-if="lastMessage?.sources?.length" class="source-list">
            <el-tag 
              v-for="source in lastMessage.sources" 
              :key="source"
              effect="plain"
            >
              📄 {{ source }}
            </el-tag>
          </div>
          <el-empty v-else description="未使用 RAG 检索" :image-size="60" />
        </el-collapse-item>

        <!-- 调试信息 -->
        <el-collapse-item title="调试信息" name="debug">
          <template #title>
            <div class="collapse-title">
              <el-icon><DataLine /></el-icon>
              <span>调试信息</span>
            </div>
          </template>
          
          <div v-if="debugInfo" class="debug-info">
            <pre>{{ JSON.stringify(debugInfo, null, 2) }}</pre>
          </div>
          <el-empty v-else description="暂无调试信息" :image-size="60" />
        </el-collapse-item>

        <!-- 会话信息 -->
        <el-collapse-item title="会话信息" name="session">
          <template #title>
            <div class="collapse-title">
              <el-icon><ChatLineSquare /></el-icon>
              <span>会话信息</span>
            </div>
          </template>
          
          <div class="session-info">
            <div class="info-row">
              <span class="label">会话 ID:</span>
              <span class="value">{{ sessionId || '未创建' }}</span>
            </div>
            <div class="info-row">
              <span class="label">消息数:</span>
              <span class="value">{{ messageCount }}</span>
            </div>
            <div class="info-row">
              <span class="label">当前阶段:</span>
              <span class="value">{{ agentState.phase || '-' }}</span>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </el-scrollbar>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useChatStore } from '@/stores/chat'

const props = defineProps({
  agentState: {
    type: Object,
    default: () => ({}),
  },
  debugInfo: {
    type: Object,
    default: null,
  },
  lastMessage: {
    type: Object,
    default: null,
  },
})

const chatStore = useChatStore()
const activeNames = ref(['steps', 'structured'])

const sessionId = computed(() => chatStore.sessionId)
const messageCount = computed(() => chatStore.messages.length)

function getStepIcon(type) {
  const icons = {
    planner: '🎯',
    skill: '⚡',
    mcp: '🔧',
    rag: '📚',
    executor: '▶️',
  }
  return icons[type] || '📋'
}
</script>

<style lang="scss" scoped>
.debug-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
  
  h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
  }
}

.panel-content {
  flex: 1;
  
  :deep(.el-scrollbar__view) {
    padding: 12px;
  }
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .el-badge {
    margin-left: auto;
  }
}

// 步骤列表
.step-list {
  .step-item {
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 8px;
    
    &.planner { background: #f3e8ff; }
    &.skill { background: #dcfce7; }
    &.mcp { background: #fff7ed; }
    &.rag { background: #ecfeff; }
    
    .step-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      
      .step-type {
        font-weight: 500;
        font-size: 13px;
      }
    }
    
    .step-data {
      pre {
        margin: 0;
        padding: 8px;
        background: rgba(0, 0, 0, 0.05);
        border-radius: 4px;
        font-size: 11px;
        overflow-x: auto;
        max-height: 120px;
      }
    }
  }
}

// 数据列表
.data-list {
  .data-item {
    margin-bottom: 12px;
    
    .data-type {
      font-weight: 500;
      margin-bottom: 4px;
      text-transform: uppercase;
      font-size: 12px;
      color: var(--primary-color);
    }
    
    .data-content {
      margin: 0;
      padding: 8px;
      background: #f5f7fa;
      border-radius: 6px;
      font-size: 11px;
      max-height: 150px;
      overflow: auto;
    }
  }
}

// 来源列表
.source-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

// 调试信息
.debug-info {
  pre {
    margin: 0;
    padding: 12px;
    background: #1e1e1e;
    color: #d4d4d4;
    border-radius: 8px;
    font-size: 11px;
    max-height: 200px;
    overflow: auto;
  }
}

// 会话信息
.session-info {
  .info-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px dashed var(--border-color);
    font-size: 13px;
    
    &:last-child {
      border-bottom: none;
    }
    
    .label {
      color: var(--text-secondary);
    }
    
    .value {
      font-family: monospace;
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
}
</style>
