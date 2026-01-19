<template>
  <div class="agent-progress">
    <div class="progress-header">
      <el-icon class="loading-icon"><Loading /></el-icon>
      <span>Agent 正在处理...</span>
    </div>

    <div class="progress-steps">
      <!-- 规划阶段 -->
      <div class="step" :class="getStepClass('planning')">
        <div class="step-icon">
          <el-icon><Aim /></el-icon>
        </div>
        <div class="step-content">
          <div class="step-title">任务规划</div>
          <div class="step-desc">分析用户意图，制定执行计划</div>
        </div>
        <el-icon v-if="isStepCompleted('planning')" class="check"><Check /></el-icon>
      </div>

      <!-- 执行阶段 -->
      <div class="step" :class="getStepClass('executing')">
        <div class="step-icon">
          <el-icon><Operation /></el-icon>
        </div>
        <div class="step-content">
          <div class="step-title">技能调用</div>
          <div class="step-desc">
            {{ state.currentSkill ? `正在调用: ${state.currentSkill}` : '选择并调用合适的技能' }}
          </div>
        </div>
        <el-icon v-if="isStepCompleted('executing')" class="check"><Check /></el-icon>
      </div>

      <!-- MCP 工具 -->
      <div class="step" :class="getStepClass('mcp')">
        <div class="step-icon">
          <el-icon><Connection /></el-icon>
        </div>
        <div class="step-content">
          <div class="step-title">MCP 工具</div>
          <div class="step-desc">
            {{ state.currentTool ? `调用: ${state.currentTool}` : '通过 MCP 协议调用工具' }}
          </div>
        </div>
        <el-icon v-if="isStepCompleted('mcp')" class="check"><Check /></el-icon>
      </div>

      <!-- 推理阶段 -->
      <div class="step" :class="getStepClass('reasoning')">
        <div class="step-icon">
          <el-icon><MagicStick /></el-icon>
        </div>
        <div class="step-content">
          <div class="step-title">结果生成</div>
          <div class="step-desc">整合信息，生成回答</div>
        </div>
        <el-icon v-if="isStepCompleted('reasoning')" class="check"><Check /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  state: {
    type: Object,
    required: true,
  },
})

const phaseOrder = ['planning', 'executing', 'mcp', 'reasoning', 'done']

const currentPhaseIndex = computed(() => {
  return phaseOrder.indexOf(props.state.phase)
})

function getStepClass(phase) {
  const index = phaseOrder.indexOf(phase)
  if (index < currentPhaseIndex.value) return 'completed'
  if (index === currentPhaseIndex.value) return 'active'
  return 'pending'
}

function isStepCompleted(phase) {
  const index = phaseOrder.indexOf(phase)
  return index < currentPhaseIndex.value
}
</script>

<style lang="scss" scoped>
.agent-progress {
  background: var(--card-bg);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid var(--border-color);
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-weight: 500;
  color: var(--primary-color);
  
  .loading-icon {
    animation: rotate 1s linear infinite;
  }
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
  
  &.pending {
    opacity: 0.5;
    background: #f5f7fa;
  }
  
  &.active {
    background: #ecf5ff;
    border: 1px solid #409eff;
    
    .step-icon {
      background: #409eff;
      color: white;
    }
  }
  
  &.completed {
    background: #f0f9eb;
    
    .step-icon {
      background: #67c23a;
      color: white;
    }
  }
  
  .step-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #dcdfe6;
    color: #606266;
    flex-shrink: 0;
  }
  
  .step-content {
    flex: 1;
    min-width: 0;
    
    .step-title {
      font-weight: 500;
      font-size: 14px;
      margin-bottom: 2px;
    }
    
    .step-desc {
      font-size: 12px;
      color: var(--text-secondary);
    }
  }
  
  .check {
    color: #67c23a;
    font-size: 18px;
  }
}
</style>
