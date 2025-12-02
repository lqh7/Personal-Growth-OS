/**
 * Settings Store - LLM Configuration Management
 *
 * Manages LLM provider settings with backend API (.env file) persistence
 * Supports OpenAI, Claude (Anthropic), and Ollama providers
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/client'

// ============================================================================
// Types
// ============================================================================

export type LLMProvider = 'openai' | 'claude' | 'ollama'

export interface LLMSettings {
  // Provider selection
  llmProvider: LLMProvider

  // OpenAI settings
  openaiApiKey: string
  openaiBaseUrl: string
  openaiModel: string

  // Anthropic (Claude) settings
  anthropicApiKey: string
  anthropicBaseUrl: string
  anthropicModel: string

  // Ollama settings
  ollamaApiKey: string
  ollamaBaseUrl: string
  ollamaModel: string

  // Common settings
  temperature: number
}

// ============================================================================
// Constants
// ============================================================================

const STORAGE_KEY = 'personal-growth-os-settings'

const DEFAULT_SETTINGS: LLMSettings = {
  llmProvider: 'openai',
  openaiApiKey: '',
  openaiBaseUrl: '',
  openaiModel: 'gpt-4',
  anthropicApiKey: '',
  anthropicBaseUrl: '',
  anthropicModel: 'claude-3-sonnet-20240229',
  ollamaApiKey: '',
  ollamaBaseUrl: 'http://localhost:11434',
  ollamaModel: 'llama2',
  temperature: 0.7,
}

// ============================================================================
// Store Definition
// ============================================================================

export const useSettingsStore = defineStore('settings', () => {
  // ============================================================================
  // State
  // ============================================================================

  const llmProvider = ref<LLMProvider>(DEFAULT_SETTINGS.llmProvider)

  // OpenAI
  const openaiApiKey = ref(DEFAULT_SETTINGS.openaiApiKey)
  const openaiBaseUrl = ref(DEFAULT_SETTINGS.openaiBaseUrl)
  const openaiModel = ref(DEFAULT_SETTINGS.openaiModel)

  // Anthropic
  const anthropicApiKey = ref(DEFAULT_SETTINGS.anthropicApiKey)
  const anthropicBaseUrl = ref(DEFAULT_SETTINGS.anthropicBaseUrl)
  const anthropicModel = ref(DEFAULT_SETTINGS.anthropicModel)

  // Ollama
  const ollamaApiKey = ref(DEFAULT_SETTINGS.ollamaApiKey)
  const ollamaBaseUrl = ref(DEFAULT_SETTINGS.ollamaBaseUrl)
  const ollamaModel = ref(DEFAULT_SETTINGS.ollamaModel)

  // Common
  const temperature = ref(DEFAULT_SETTINGS.temperature)

  // ============================================================================
  // Actions
  // ============================================================================

  /**
   * Load settings from backend API (.env file)
   */
  async function loadSettings() {
    try {
      const response = await api.get('/settings/')
      const settings = response.data

      // Apply loaded settings (snake_case from API -> camelCase)
      llmProvider.value = settings.llm_provider || DEFAULT_SETTINGS.llmProvider
      openaiApiKey.value = settings.openai_api_key || DEFAULT_SETTINGS.openaiApiKey
      openaiBaseUrl.value = settings.openai_api_base || DEFAULT_SETTINGS.openaiBaseUrl
      openaiModel.value = settings.openai_model || DEFAULT_SETTINGS.openaiModel
      anthropicApiKey.value = settings.anthropic_api_key || DEFAULT_SETTINGS.anthropicApiKey
      anthropicBaseUrl.value = settings.anthropic_api_base || DEFAULT_SETTINGS.anthropicBaseUrl
      anthropicModel.value = settings.anthropic_model || DEFAULT_SETTINGS.anthropicModel
      ollamaApiKey.value = settings.ollama_api_key || DEFAULT_SETTINGS.ollamaApiKey
      ollamaBaseUrl.value = settings.ollama_base_url || DEFAULT_SETTINGS.ollamaBaseUrl
      ollamaModel.value = settings.ollama_model || DEFAULT_SETTINGS.ollamaModel
      temperature.value = settings.temperature ?? DEFAULT_SETTINGS.temperature

      console.log('[SettingsStore] Settings loaded from backend API')
    } catch (error) {
      console.error('[SettingsStore] Failed to load settings:', error)
    }
  }

  /**
   * Save settings to backend API (.env file)
   */
  async function saveSettings() {
    try {
      // Build update payload (camelCase -> snake_case)
      const updates = {
        llm_provider: llmProvider.value,
        openai_api_key: openaiApiKey.value,
        openai_api_base: openaiBaseUrl.value,
        openai_model: openaiModel.value,
        anthropic_api_key: anthropicApiKey.value,
        anthropic_api_base: anthropicBaseUrl.value,
        anthropic_model: anthropicModel.value,
        ollama_api_key: ollamaApiKey.value,
        ollama_base_url: ollamaBaseUrl.value,
        ollama_model: ollamaModel.value,
        temperature: temperature.value,
      }

      await api.put('/settings/', updates)
      console.log('[SettingsStore] Settings saved to backend API (.env file)')

      return { success: true }
    } catch (error) {
      console.error('[SettingsStore] Failed to save settings:', error)
      return { success: false, error }
    }
  }

  /**
   * Reset settings to default values and save to backend
   */
  async function resetSettings() {
    llmProvider.value = DEFAULT_SETTINGS.llmProvider
    openaiApiKey.value = DEFAULT_SETTINGS.openaiApiKey
    openaiBaseUrl.value = DEFAULT_SETTINGS.openaiBaseUrl
    openaiModel.value = DEFAULT_SETTINGS.openaiModel
    anthropicApiKey.value = DEFAULT_SETTINGS.anthropicApiKey
    anthropicBaseUrl.value = DEFAULT_SETTINGS.anthropicBaseUrl
    anthropicModel.value = DEFAULT_SETTINGS.anthropicModel
    ollamaApiKey.value = DEFAULT_SETTINGS.ollamaApiKey
    ollamaBaseUrl.value = DEFAULT_SETTINGS.ollamaBaseUrl
    ollamaModel.value = DEFAULT_SETTINGS.ollamaModel
    temperature.value = DEFAULT_SETTINGS.temperature

    await saveSettings()
    console.log('[SettingsStore] Settings reset to default')
  }

  // ============================================================================
  // Initialization
  // ============================================================================

  // Load settings on initialization
  loadSettings()

  // ============================================================================
  // Return
  // ============================================================================

  return {
    // State
    llmProvider,
    openaiApiKey,
    openaiBaseUrl,
    openaiModel,
    anthropicApiKey,
    anthropicBaseUrl,
    anthropicModel,
    ollamaApiKey,
    ollamaBaseUrl,
    ollamaModel,
    temperature,

    // Actions
    loadSettings,
    saveSettings,
    resetSettings,
  }
})
