/**
 * 聊天状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { chatApi } from '@/api'

export const useChatStore = defineStore('chat', () => {
  // ========== State ==========
  
  /** 当前会话 ID */
  const sessionId = ref(localStorage.getItem('session_id') || null)
  
  /** 消息列表 */
  const messages = ref([])
  
  /** 是否正在加载 */
  const loading = ref(false)
  
  /** 当前 Agent 执行状态 */
  const agentState = ref({
    phase: null,  // 'planning' | 'executing' | 'reasoning' | 'done'
    currentSkill: null,
    currentTool: null,
    steps: [],
  })
  
  /** 调试信息 */
  const debugInfo = ref(null)

  // ========== Getters ==========
  
  const hasMessages = computed(() => messages.value.length > 0)
  
  const lastMessage = computed(() => {
    return messages.value[messages.value.length - 1] || null
  })

  // ========== Actions ==========
  
  /**
   * 发送消息
   */
  async function sendMessage(content) {
    if (!content.trim() || loading.value) return
    
    // 添加用户消息
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date().toISOString(),
    }
    messages.value.push(userMessage)
    
    // 开始加载
    loading.value = true
    agentState.value = {
      phase: 'planning',
      currentSkill: null,
      currentTool: null,
      steps: [],
    }
    
    try {
      // 调用 API
      const response = await chatApi.send(content, sessionId.value)
      
      // 更新会话 ID
      if (response.session_id) {
        sessionId.value = response.session_id
        localStorage.setItem('session_id', response.session_id)
      }
      
      // 解析 Agent 执行步骤
      parseAgentSteps(response)
      
      // 添加助手消息
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.reply,
        timestamp: new Date().toISOString(),
        structuredData: response.structured_data,
        sources: response.sources,
        debugInfo: response.debug_info,
      }
      messages.value.push(assistantMessage)
      
      // 保存调试信息
      debugInfo.value = response.debug_info
      
      // 更新状态为完成
      agentState.value.phase = 'done'
      
    } catch (error) {
      console.error('Send message error:', error)
      
      // 添加错误消息
      messages.value.push({
        id: Date.now() + 1,
        role: 'assistant',
        content: '抱歉，处理您的请求时出现了问题。请稍后再试。',
        timestamp: new Date().toISOString(),
        isError: true,
      })
      
      agentState.value.phase = 'error'
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 解析 Agent 执行步骤（模拟，实际需要后端支持）
   */
  function parseAgentSteps(response) {
    const steps = []
    
    // 规划阶段
    steps.push({
      type: 'planner',
      title: '任务规划',
      status: 'completed',
      data: {
        intent: response.debug_info?.intent || 'general',
      },
    })
    
    // 技能调用
    if (response.sources?.length > 0) {
      steps.push({
        type: 'skill',
        title: '技能调用',
        status: 'completed',
        data: {
          skills: response.sources,
        },
      })
    }
    
    // 结构化数据
    if (response.structured_data?.length > 0) {
      for (const data of response.structured_data) {
        steps.push({
          type: 'mcp',
          title: `MCP 工具: ${data.type}`,
          status: 'completed',
          data: data.data,
        })
      }
    }
    
    agentState.value.steps = steps
  }
  
  /**
   * 清空消息
   */
  function clearMessages() {
    messages.value = []
    agentState.value = {
      phase: null,
      currentSkill: null,
      currentTool: null,
      steps: [],
    }
    debugInfo.value = null
  }
  
  /**
   * 新建会话
   */
  async function newSession() {
    clearMessages()
    sessionId.value = null
    localStorage.removeItem('session_id')
  }
  
  /**
   * 切换会话
   */
  async function switchSession(newSessionId) {
    sessionId.value = newSessionId
    localStorage.setItem('session_id', newSessionId)
    clearMessages()
    // 可以在这里加载历史消息
  }

  return {
    // State
    sessionId,
    messages,
    loading,
    agentState,
    debugInfo,
    // Getters
    hasMessages,
    lastMessage,
    // Actions
    sendMessage,
    clearMessages,
    newSession,
    switchSession,
  }
})
