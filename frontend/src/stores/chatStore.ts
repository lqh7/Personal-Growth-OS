import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// ============================================
// Types
// ============================================
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  actions?: MessageAction[]
  metadata?: {
    relatedTasks?: string[]
    relatedNotes?: string[]
    confidence?: number
  }
}

export interface MessageAction {
  type: 'create_task' | 'create_note' | 'navigate' | 'search'
  label: string
  payload: any
}

export interface Conversation {
  id: string
  title: string
  customTitle?: string // 用户自定义标题（如果设置了则使用这个）
  lastMessage: string
  timestamp: Date
  isActive: boolean
  context: 'dashboard' | 'task' | 'note' | 'review'
  messages?: Message[] // 存储该对话的历史消息（实际项目中应从后端加载）
}

// ============================================
// Store
// ============================================
export const useChatStore = defineStore('chat', () => {
  // ============================================
  // State
  // ============================================
  const conversations = ref<Conversation[]>([
    {
      id: '1',
      title: '今天的任务',
      lastMessage: '我来帮你规划一下今天的任务',
      timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5分钟前
      isActive: true,
      context: 'dashboard',
      messages: [
        {
          id: '1-1',
          role: 'user',
          content: '今天的任务',
          timestamp: new Date(Date.now() - 10 * 60 * 1000)
        },
        {
          id: '1-2',
          role: 'assistant',
          content: '我来帮你规划一下今天的任务。你今天想完成什么呢？',
          timestamp: new Date(Date.now() - 5 * 60 * 1000)
        }
      ]
    },
    {
      id: '2',
      title: '笔记整理',
      lastMessage: '找到了3条相关笔记',
      timestamp: new Date(Date.now() - 60 * 60 * 1000), // 1小时前
      isActive: false,
      context: 'note',
      messages: [
        {
          id: '2-1',
          role: 'user',
          content: '帮我整理一下笔记',
          timestamp: new Date(Date.now() - 70 * 60 * 1000)
        },
        {
          id: '2-2',
          role: 'assistant',
          content: '找到了3条相关笔记，让我帮你分类整理一下。',
          timestamp: new Date(Date.now() - 60 * 60 * 1000)
        }
      ]
    }
  ])

  const currentConversationId = ref<string | null>('1')

  // 初始化messages为第一个对话的历史消息
  const messages = ref<Message[]>(
    conversations.value[0]?.messages || [
      {
        id: '1',
        role: 'assistant',
        content: '你好！我是你的AI助手。你今天想完成什么任务呢？',
        timestamp: new Date(Date.now() - 10 * 60 * 1000),
        actions: [
          {
            type: 'create_task',
            label: '创建任务',
            payload: {}
          }
        ]
      }
    ]
  )
  const loading = ref(false)

  // ============================================
  // Getters
  // ============================================
  const currentConversation = computed(() => {
    return conversations.value.find((c) => c.id === currentConversationId.value) || null
  })

  const currentMessages = computed(() => {
    return messages.value
  })

  // ============================================
  // Actions
  // ============================================

  /**
   * 发送消息（模拟AI回复）
   * @param content - 用户消息内容
   */
  async function sendMessage(content: string) {
    // 添加用户消息
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    }
    messages.value.push(userMessage)

    // 如果是新对话的第一条消息，自动设置标题
    if (currentConversation.value) {
      const isNewConversation = currentConversation.value.title === '新对话' && !currentConversation.value.customTitle
      if (isNewConversation) {
        // 使用用户第一句话作为标题，过长则截断
        const maxTitleLength = 20
        currentConversation.value.title = content.length > maxTitleLength
          ? content.substring(0, maxTitleLength) + '...'
          : content
      }
    }

    // 模拟AI思考
    loading.value = true
    await new Promise((resolve) => setTimeout(resolve, 800))

    // 模拟AI回复
    const aiMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: generateMockResponse(content),
      timestamp: new Date(),
      actions: generateMockActions(content)
    }
    messages.value.push(aiMessage)
    loading.value = false

    // 更新对话列表
    if (currentConversation.value) {
      currentConversation.value.lastMessage = content
      currentConversation.value.timestamp = new Date()
    }
  }

  /**
   * 切换对话
   * @param id - 对话ID
   */
  function switchConversation(id: string) {
    // 保存当前对话的消息到conversation
    if (currentConversation.value && messages.value.length > 0) {
      currentConversation.value.messages = [...messages.value]
    }

    currentConversationId.value = id
    // 标记当前对话为激活
    conversations.value.forEach((c) => {
      c.isActive = c.id === id
    })

    // 加载新对话的历史消息
    const targetConv = conversations.value.find((c) => c.id === id)
    if (targetConv?.messages && targetConv.messages.length > 0) {
      // 从conversation中恢复历史消息
      messages.value = [...targetConv.messages]
    } else {
      // TODO: 实际项目中这里应该调用后端API加载消息历史
      // await loadMessagesFromBackend(id)

      // 暂时显示欢迎消息
      messages.value = [
        {
          id: Date.now().toString(),
          role: 'assistant',
          content: '你好！有什么我可以帮助你的吗？',
          timestamp: new Date()
        }
      ]
    }
  }

  /**
   * 创建新对话
   */
  function createConversation() {
    const newConv: Conversation = {
      id: Date.now().toString(),
      title: '新对话',
      lastMessage: '',
      timestamp: new Date(),
      isActive: false,
      context: 'dashboard'
    }
    conversations.value.unshift(newConv)
    switchConversation(newConv.id)
  }

  /**
   * 更新对话标题
   * @param conversationId - 对话ID
   * @param newTitle - 新标题
   */
  function updateConversationTitle(conversationId: string, newTitle: string) {
    const conversation = conversations.value.find((c) => c.id === conversationId)
    if (conversation) {
      conversation.customTitle = newTitle
      conversation.title = newTitle
    }
  }

  /**
   * 删除对话
   * @param conversationId - 对话ID
   */
  function deleteConversation(conversationId: string) {
    const index = conversations.value.findIndex((c) => c.id === conversationId)
    if (index === -1) return

    const wasActive = conversations.value[index].isActive

    // 删除对话
    conversations.value.splice(index, 1)

    // 如果删除的是当前活跃对话，切换到第一个对话
    if (wasActive && conversations.value.length > 0) {
      switchConversation(conversations.value[0].id)
    } else if (conversations.value.length === 0) {
      // 如果没有对话了，清空消息
      messages.value = []
      currentConversationId.value = null
    }
  }

  // ============================================
  // Helper Functions (Mock)
  // ============================================

  /**
   * 生成模拟AI回复
   */
  function generateMockResponse(userInput: string): string {
    const lowerInput = userInput.toLowerCase()

    if (lowerInput.includes('任务') || lowerInput.includes('task')) {
      return '好的，我来帮你分析这个任务。\n\n根据你的描述，我建议将它分解为以下子任务：\n1. 准备工作\n2. 执行核心步骤\n3. 检查和总结\n\n是否需要我帮你创建这些任务？'
    }

    if (lowerInput.includes('笔记') || lowerInput.includes('note')) {
      return '我找到了3条与此相关的笔记：\n• 上次项目总结\n• 技术要点记录\n• 相关资源链接\n\n你想查看哪一条？'
    }

    if (lowerInput.includes('复盘') || lowerInput.includes('review')) {
      return '让我看看你最近的工作情况...\n\n这周你完成了12个任务，平均完成率85%。\n周四的效率最高，建议将重要任务安排在周四。\n\n是否开始详细的复盘对话？'
    }

    return '我理解了你的需求。让我来帮你处理这个问题。你可以告诉我更多细节吗？'
  }

  /**
   * 生成模拟操作按钮
   */
  function generateMockActions(userInput: string): MessageAction[] {
    const lowerInput = userInput.toLowerCase()

    if (lowerInput.includes('任务')) {
      return [
        {
          type: 'create_task',
          label: '创建任务',
          payload: {}
        },
        {
          type: 'navigate',
          label: '查看所有任务',
          payload: { route: '/tasks' }
        }
      ]
    }

    if (lowerInput.includes('笔记')) {
      return [
        {
          type: 'search',
          label: '搜索笔记',
          payload: { query: userInput }
        },
        {
          type: 'create_note',
          label: '创建笔记',
          payload: {}
        }
      ]
    }

    return []
  }

  return {
    // State
    conversations,
    currentConversationId,
    messages,
    loading,

    // Getters
    currentConversation,
    currentMessages,

    // Actions
    sendMessage,
    switchConversation,
    createConversation,
    updateConversationTitle,
    deleteConversation
  }
})
