/**
 * API 服务层
 * 
 * 前端只通过此模块与后端通信
 * 不直接访问 MCP / 向量库 / LLM
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000, // Agent 可能需要较长时间
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token
    const token = localStorage.getItem('api_token')
    if (token) {
      config.headers['X-API-Key'] = token
    }
    
    // 调试模式
    if (localStorage.getItem('debug_mode') === 'true') {
      config.headers['X-Debug'] = 'true'
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

/**
 * 聊天 API
 */
export const chatApi = {
  /**
   * 发送消息
   * @param {string} message - 用户消息
   * @param {string} sessionId - 会话 ID
   * @returns {Promise<ChatResponse>}
   */
  async send(message, sessionId = null) {
    return api.post('/chat', {
      message,
      session_id: sessionId,
      stream: false,
    })
  },

  /**
   * 流式发送消息
   * @param {string} message - 用户消息
   * @param {string} sessionId - 会话 ID
   * @param {Function} onToken - 收到 token 的回调
   * @param {Function} onDone - 完成回调
   */
  async sendStream(message, sessionId, onToken, onDone) {
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        stream: true,
      }),
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const text = decoder.decode(value)
      const lines = text.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (data.event === 'token') {
              onToken(data.data, data.index)
            } else if (data.event === 'done') {
              onDone(data)
            } else if (data.event === 'error') {
              throw new Error(data.message)
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
  },

  /**
   * 获取会话信息
   * @param {string} sessionId - 会话 ID
   */
  async getSession(sessionId) {
    return api.get(`/chat/session/${sessionId}`)
  },

  /**
   * 删除会话
   * @param {string} sessionId - 会话 ID
   */
  async deleteSession(sessionId) {
    return api.delete(`/chat/session/${sessionId}`)
  },

  /**
   * 列出所有会话
   */
  async listSessions() {
    return api.get('/chat/sessions')
  },
}

/**
 * 健康检查 API
 */
export const healthApi = {
  /**
   * 健康检查
   */
  async check() {
    return api.get('/health')
  },

  /**
   * 就绪检查
   */
  async ready() {
    return api.get('/health/ready')
  },
}

export default api
