/**
 * LLM Configuration Validator
 * Validates LLM API keys by making direct API calls from frontend
 */

export interface ValidationResult {
  valid: boolean
  errorMessage?: string
  modelTested?: string
}

/**
 * Validate OpenAI configuration
 */
export async function validateOpenAI(
  apiKey: string,
  model: string,
  baseUrl?: string
): Promise<ValidationResult> {
  const endpoint = baseUrl || 'https://api.openai.com/v1'
  const url = `${endpoint}/chat/completions`

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: model || 'gpt-4',
        messages: [{ role: 'user', content: 'Hello' }],
        max_tokens: 5
      }),
      signal: AbortSignal.timeout(10000) // 10s timeout
    })

    if (response.ok) {
      return {
        valid: true,
        modelTested: model
      }
    } else {
      const error = await response.json()
      return {
        valid: false,
        errorMessage: `OpenAI API 错误: ${error.error?.message || response.statusText}`
      }
    }
  } catch (error: any) {
    if (error.name === 'AbortError') {
      return {
        valid: false,
        errorMessage: 'API 请求超时 (10秒)，请检查网络或 API 端点'
      }
    }
    return {
      valid: false,
      errorMessage: `网络错误: ${error.message}`
    }
  }
}

/**
 * Validate Claude (Anthropic) configuration
 */
export async function validateClaude(
  apiKey: string,
  model: string,
  baseUrl?: string
): Promise<ValidationResult> {
  const endpoint = baseUrl || 'https://api.anthropic.com'
  const url = `${endpoint}/v1/messages`

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: model || 'claude-3-sonnet-20240229',
        messages: [{ role: 'user', content: 'Hello' }],
        max_tokens: 5
      }),
      signal: AbortSignal.timeout(10000)
    })

    if (response.ok) {
      return {
        valid: true,
        modelTested: model
      }
    } else {
      const error = await response.json()
      return {
        valid: false,
        errorMessage: `Claude API 错误: ${error.error?.message || response.statusText}`
      }
    }
  } catch (error: any) {
    if (error.name === 'AbortError') {
      return {
        valid: false,
        errorMessage: 'API 请求超时 (10秒)，请检查网络或 API 端点'
      }
    }
    return {
      valid: false,
      errorMessage: `网络错误: ${error.message}`
    }
  }
}

/**
 * Validate Ollama configuration
 */
export async function validateOllama(
  model: string,
  baseUrl?: string,
  apiKey?: string
): Promise<ValidationResult> {
  const endpoint = baseUrl || 'http://localhost:11434'
  const url = `${endpoint}/api/chat`

  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  }

  // Add Authorization header if API key is provided
  if (apiKey) {
    headers['Authorization'] = `Bearer ${apiKey}`
  }

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        model: model || 'llama2',
        messages: [{ role: 'user', content: 'Hello' }],
        stream: false
      }),
      signal: AbortSignal.timeout(10000)
    })

    if (response.ok) {
      return {
        valid: true,
        modelTested: model
      }
    } else {
      return {
        valid: false,
        errorMessage: `Ollama 错误: ${response.statusText}. 请确保 Ollama 服务正在运行且模型已安装。`
      }
    }
  } catch (error: any) {
    if (error.name === 'AbortError') {
      return {
        valid: false,
        errorMessage: 'Ollama 请求超时，请确保服务正在运行'
      }
    }
    return {
      valid: false,
      errorMessage: `无法连接到 Ollama (${endpoint}). 请检查服务是否运行。`
    }
  }
}

/**
 * Validate LLM configuration based on provider
 */
export async function validateLLMConfig(
  provider: 'openai' | 'claude' | 'ollama',
  config: {
    openaiApiKey?: string
    openaiModel?: string
    openaiBaseUrl?: string
    anthropicApiKey?: string
    anthropicModel?: string
    anthropicBaseUrl?: string
    ollamaApiKey?: string
    ollamaModel?: string
    ollamaBaseUrl?: string
  }
): Promise<ValidationResult> {
  switch (provider) {
    case 'openai':
      if (!config.openaiApiKey) {
        return { valid: false, errorMessage: 'OpenAI API Key 不能为空' }
      }
      return validateOpenAI(
        config.openaiApiKey,
        config.openaiModel || 'gpt-4',
        config.openaiBaseUrl
      )

    case 'claude':
      if (!config.anthropicApiKey) {
        return { valid: false, errorMessage: 'Claude API Key 不能为空' }
      }
      return validateClaude(
        config.anthropicApiKey,
        config.anthropicModel || 'claude-3-sonnet-20240229',
        config.anthropicBaseUrl
      )

    case 'ollama':
      return validateOllama(
        config.ollamaModel || 'llama2',
        config.ollamaBaseUrl,
        config.ollamaApiKey
      )

    default:
      return { valid: false, errorMessage: `不支持的 Provider: ${provider}` }
  }
}
