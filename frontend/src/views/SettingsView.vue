<template>
  <div class="settings-view">
    <div class="settings-container">
      <!-- Header -->
      <div class="settings-header">
        <h1>设置</h1>
        <p class="subtitle">配置 LLM 模型参数</p>
      </div>

      <!-- Settings Form -->
      <el-form :model="formData" label-width="140px" label-position="left">
        <!-- Provider Selection -->
        <el-form-item label="LLM Provider">
          <el-radio-group v-model="formData.llmProvider">
            <el-radio label="openai">OpenAI</el-radio>
            <el-radio label="claude">Claude (Anthropic)</el-radio>
            <el-radio label="ollama">Ollama</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-divider />

        <!-- OpenAI Settings -->
        <div v-if="formData.llmProvider === 'openai'" class="provider-section">
          <h3 class="section-title">OpenAI 配置</h3>

          <el-form-item label="API Key">
            <el-input
              v-model="formData.openaiApiKey"
              type="password"
              placeholder="sk-..."
              show-password
              clearable
            />
            <span class="form-hint">
              从 <a href="https://platform.openai.com/api-keys" target="_blank">OpenAI Platform</a> 获取 API Key
            </span>
          </el-form-item>

          <el-form-item label="Base URL">
            <el-input
              v-model="formData.openaiBaseUrl"
              placeholder="https://api.openai.com/v1 (可选)"
              clearable
            />
            <span class="form-hint">自定义 API 端点（可选，如使用代理）</span>
          </el-form-item>

          <el-form-item label="Model">
            <el-input
              v-model="formData.openaiModel"
              placeholder="gpt-4, gpt-4o, gpt-3.5-turbo..."
              clearable
            />
            <span class="form-hint">
              常用模型: gpt-4, gpt-4o, gpt-4-turbo, gpt-3.5-turbo
            </span>
          </el-form-item>
        </div>

        <!-- Claude Settings -->
        <div v-if="formData.llmProvider === 'claude'" class="provider-section">
          <h3 class="section-title">Claude 配置</h3>

          <el-form-item label="API Key">
            <el-input
              v-model="formData.anthropicApiKey"
              type="password"
              placeholder="sk-ant-..."
              show-password
              clearable
            />
            <span class="form-hint">
              从 <a href="https://console.anthropic.com/" target="_blank">Anthropic Console</a> 获取 API Key
            </span>
          </el-form-item>

          <el-form-item label="Base URL">
            <el-input
              v-model="formData.anthropicBaseUrl"
              placeholder="https://api.anthropic.com (可选)"
              clearable
            />
            <span class="form-hint">自定义 API 端点（可选）</span>
          </el-form-item>

          <el-form-item label="Model">
            <el-input
              v-model="formData.anthropicModel"
              placeholder="claude-3-5-sonnet-20240620, claude-3-opus..."
              clearable
            />
            <span class="form-hint">
              常用模型: claude-3-5-sonnet-20240620, claude-3-opus-20240229, claude-3-sonnet-20240229
            </span>
          </el-form-item>
        </div>

        <!-- Ollama Settings -->
        <div v-if="formData.llmProvider === 'ollama'" class="provider-section">
          <h3 class="section-title">Ollama 配置</h3>

          <el-form-item label="Base URL">
            <el-input
              v-model="formData.ollamaBaseUrl"
              placeholder="http://localhost:11434"
              clearable
            />
            <span class="form-hint">Ollama 服务地址</span>
          </el-form-item>

          <el-form-item label="Model">
            <el-input
              v-model="formData.ollamaModel"
              placeholder="llama2, mistral, ..."
              clearable
            />
            <span class="form-hint">已安装的 Ollama 模型名称</span>
          </el-form-item>
        </div>

        <el-divider />

        <!-- Common Settings -->
        <div class="common-section">
          <h3 class="section-title">通用配置</h3>

          <el-form-item label="Temperature">
            <div class="temperature-control">
              <el-slider
                v-model="formData.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                :show-tooltip="true"
                style="flex: 1; margin-right: 20px"
              />
              <el-input-number
                v-model="formData.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                :precision="1"
                style="width: 120px"
              />
            </div>
            <span class="form-hint">
              控制生成结果的随机性。0 = 确定性，2 = 最随机
            </span>
          </el-form-item>
        </div>
      </el-form>

      <!-- Warning Alert -->
      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-top: 24px"
      >
        <template #title>
          <strong>注意事项</strong>
        </template>
        <ul style="margin: 8px 0 0 0; padding-left: 20px">
          <li>配置会保存到后端 <code>.env</code> 文件</li>
          <li>修改配置后会立即生效，无需重启服务</li>
          <li>API Key 敏感信息，请妥善保管</li>
        </ul>
      </el-alert>

      <!-- Action Buttons -->
      <div class="actions-bar">
        <el-button @click="handleReset">重置为默认值</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          保存配置
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useSettingsStore } from '@/stores/settingsStore'
import { storeToRefs } from 'pinia'

// ============================================================================
// Store
// ============================================================================
const settingsStore = useSettingsStore()
const {
  llmProvider,
  openaiApiKey,
  openaiBaseUrl,
  openaiModel,
  anthropicApiKey,
  anthropicBaseUrl,
  anthropicModel,
  ollamaBaseUrl,
  ollamaModel,
  temperature,
} = storeToRefs(settingsStore)

// ============================================================================
// State
// ============================================================================
const saving = ref(false)

// Form data (copy from store)
const formData = reactive({
  llmProvider: llmProvider.value,
  openaiApiKey: openaiApiKey.value,
  openaiBaseUrl: openaiBaseUrl.value,
  openaiModel: openaiModel.value,
  anthropicApiKey: anthropicApiKey.value,
  anthropicBaseUrl: anthropicBaseUrl.value,
  anthropicModel: anthropicModel.value,
  ollamaBaseUrl: ollamaBaseUrl.value,
  ollamaModel: ollamaModel.value,
  temperature: temperature.value,
})

// ============================================================================
// Lifecycle
// ============================================================================
onMounted(async () => {
  // Reload settings from backend on mount
  await settingsStore.loadSettings()

  // Update form data
  formData.llmProvider = llmProvider.value
  formData.openaiApiKey = openaiApiKey.value
  formData.openaiBaseUrl = openaiBaseUrl.value
  formData.openaiModel = openaiModel.value
  formData.anthropicApiKey = anthropicApiKey.value
  formData.anthropicBaseUrl = anthropicBaseUrl.value
  formData.anthropicModel = anthropicModel.value
  formData.ollamaBaseUrl = ollamaBaseUrl.value
  formData.ollamaModel = ollamaModel.value
  formData.temperature = temperature.value
})

// ============================================================================
// Methods
// ============================================================================

/**
 * Save settings
 */
async function handleSave() {
  saving.value = true

  try {
    console.log('[SettingsView] handleSave() called with formData:', formData)

    // Update store from form data
    llmProvider.value = formData.llmProvider
    openaiApiKey.value = formData.openaiApiKey
    openaiBaseUrl.value = formData.openaiBaseUrl
    openaiModel.value = formData.openaiModel
    anthropicApiKey.value = formData.anthropicApiKey
    anthropicBaseUrl.value = formData.anthropicBaseUrl
    anthropicModel.value = formData.anthropicModel
    ollamaBaseUrl.value = formData.ollamaBaseUrl
    ollamaModel.value = formData.ollamaModel
    temperature.value = formData.temperature

    console.log('[SettingsView] Calling settingsStore.saveSettings()...')

    // Save to backend
    const result = await settingsStore.saveSettings()

    console.log('[SettingsView] saveSettings() result:', result)

    if (result.success) {
      ElMessage.success('配置保存成功！已立即生效。')
    } else {
      ElMessage.error('配置保存失败，请检查后端服务是否正常运行')
    }
  } catch (error) {
    console.error('[SettingsView] Save error:', error)
    ElMessage.error('配置保存失败')
  } finally {
    saving.value = false
  }
}

/**
 * Reset settings to default
 */
async function handleReset() {
  try {
    await ElMessageBox.confirm(
      '确定要重置所有配置为默认值吗？此操作不可撤销。',
      '重置配置',
      {
        confirmButtonText: '重置',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    await settingsStore.resetSettings()

    // Update form data
    formData.llmProvider = llmProvider.value
    formData.openaiApiKey = openaiApiKey.value
    formData.openaiBaseUrl = openaiBaseUrl.value
    formData.openaiModel = openaiModel.value
    formData.anthropicApiKey = anthropicApiKey.value
    formData.anthropicBaseUrl = anthropicBaseUrl.value
    formData.anthropicModel = anthropicModel.value
    formData.ollamaBaseUrl = ollamaBaseUrl.value
    formData.ollamaModel = ollamaModel.value
    formData.temperature = temperature.value

    ElMessage.success('配置已重置为默认值')
  } catch (error) {
    // User canceled
  }
}
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';
@import '@/assets/styles/mixins.scss';

.settings-view {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  @include custom-scrollbar;
}

.settings-container {
  max-width: 800px;
  margin: 0 auto;
  padding: $spacing-xl;
}

.settings-header {
  margin-bottom: $spacing-xl;

  h1 {
    font-size: $font-size-xxl;
    font-weight: 600;
    color: $color-text-primary;
    margin: 0 0 $spacing-sm 0;
  }

  .subtitle {
    font-size: $font-size-sm;
    color: $color-text-secondary;
    margin: 0;
  }
}

.section-title {
  font-size: $font-size-lg;
  font-weight: 600;
  color: $color-text-primary;
  margin: 0 0 $spacing-lg 0;
}

.provider-section,
.common-section {
  margin-bottom: $spacing-lg;
}

.form-hint {
  display: block;
  font-size: $font-size-xs;
  color: $color-text-secondary;
  margin-top: $spacing-xs;

  a {
    color: $color-primary;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  code {
    font-family: 'Monaco', 'Courier New', monospace;
    font-size: $font-size-xs;
    padding: 2px 6px;
    background-color: $bg-color-hover;
    border-radius: $radius-sm;
  }
}

.temperature-control {
  display: flex;
  align-items: center;
  width: 100%;
}

.actions-bar {
  display: flex;
  justify-content: flex-end;
  gap: $spacing-md;
  margin-top: $spacing-xl;
  padding-top: $spacing-xl;
  border-top: 1px solid $color-border;
}
</style>
