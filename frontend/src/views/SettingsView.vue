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
            <div style="display: flex; gap: 8px;">
              <el-input
                v-model="formData.openaiModel"
                placeholder="gpt-4, gpt-4o, gpt-3.5-turbo..."
                clearable
                style="flex: 1;"
              />
              <el-button
                @click="handleTestLLM"
                :loading="testingLLM"
                :disabled="testingLLM"
              >
                {{ testingLLM ? '测试中...' : '🔍 测试连接' }}
              </el-button>
            </div>
            <span class="form-hint">
              常用模型: gpt-4, gpt-4o, gpt-4-turbo, gpt-3.5-turbo,gpt-4.1-mini
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
            <div style="display: flex; gap: 8px;">
              <el-input
                v-model="formData.anthropicModel"
                placeholder="claude-3-5-sonnet-20240620, claude-3-opus..."
                clearable
                style="flex: 1;"
              />
              <el-button
                @click="handleTestLLM"
                :loading="testingLLM"
                :disabled="testingLLM"
              >
                {{ testingLLM ? '测试中...' : '🔍 测试连接' }}
              </el-button>
            </div>
            <span class="form-hint">
              常用模型: claude-3-5-sonnet-20240620, claude-3-opus-20240229, claude-3-sonnet-20240229
            </span>
          </el-form-item>
        </div>

        <!-- Ollama Settings -->
        <div v-if="formData.llmProvider === 'ollama'" class="provider-section">
          <h3 class="section-title">Ollama 配置</h3>

          <el-form-item label="API Key (可选)">
            <el-input
              v-model="formData.ollamaApiKey"
              type="password"
              placeholder="可选，某些 Ollama 部署需要"
              show-password
              clearable
            />
            <span class="form-hint">如果 Ollama 服务启用了认证，请填写 API Key</span>
          </el-form-item>

          <el-form-item label="Base URL">
            <el-input
              v-model="formData.ollamaBaseUrl"
              placeholder="http://localhost:11434"
              clearable
            />
            <span class="form-hint">Ollama 服务地址</span>
          </el-form-item>

          <el-form-item label="Model">
            <div style="display: flex; gap: 8px;">
              <el-input
                v-model="formData.ollamaModel"
                placeholder="llama2, mistral, ..."
                clearable
                style="flex: 1;"
              />
              <el-button
                @click="handleTestLLM"
                :loading="testingLLM"
                :disabled="testingLLM"
              >
                {{ testingLLM ? '测试中...' : '🔍 测试连接' }}
              </el-button>
            </div>
            <!-- <span class="form-hint">已安装的 Ollama 模型名称</span> -->
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

        <el-divider />

        <!-- DingTalk Notification Settings -->
        <div class="dingtalk-section">
          <h3 class="section-title">钉钉通知配置</h3>

          <el-form-item label="启用任务提醒">
            <el-switch
              v-model="formData.enableTaskReminder"
              active-text="开启"
              inactive-text="关闭"
            />
            <span class="form-hint">
              开启后将在任务开始前10分钟发送钉钉提醒
            </span>
          </el-form-item>

          <el-form-item label="Webhook URL">
            <el-input
              v-model="formData.dingtalkWebhook"
              placeholder="https://oapi.dingtalk.com/robot/send?access_token=..."
              clearable
              :disabled="!formData.enableTaskReminder"
            />
            <span class="form-hint">
              钉钉群机器人的 Webhook 地址
              <a href="https://open.dingtalk.com/document/group/custom-robot-access" target="_blank">如何获取?</a>
            </span>
          </el-form-item>

          <el-form-item label="加签密钥 (可选)">
            <div style="display: flex; gap: 8px;">
              <el-input
                v-model="formData.dingtalkSecret"
                type="password"
                placeholder="SEC..."
                show-password
                clearable
                :disabled="!formData.enableTaskReminder"
                style="flex: 1;"
              />
              <el-button
                @click="handleTestDingTalk"
                :loading="testingDingTalk"
                :disabled="!formData.enableTaskReminder || testingDingTalk"
              >
                {{ testingDingTalk ? '发送中...' : '📱 测试通知' }}
              </el-button>
            </div>
            <span class="form-hint">
              如果钉钉机器人启用了"加签"安全设置,请填写此密钥
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
          <li>点击"测试连接"/"测试通知"验证配置是否正确</li>
          <li>修改配置后会立即生效，无需重启服务</li>
          <li>API Key 敏感信息，请妥善保管</li>
        </ul>
      </el-alert>

      <!-- Action Buttons -->
      <div class="actions-bar">
        <el-button @click="handleReset">重置为默认值</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ saving ? '保存中...' : '💾 保存配置' }}
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
import { validateLLMConfig } from '@/utils/llmValidator'

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
  ollamaApiKey,
  ollamaBaseUrl,
  ollamaModel,
  temperature,
} = storeToRefs(settingsStore)

// ============================================================================
// State
// ============================================================================
const saving = ref(false)
const testingLLM = ref(false)
const testingDingTalk = ref(false)

// Form data (copy from store)
const formData = reactive({
  llmProvider: llmProvider.value,
  openaiApiKey: openaiApiKey.value,
  openaiBaseUrl: openaiBaseUrl.value,
  openaiModel: openaiModel.value,
  anthropicApiKey: anthropicApiKey.value,
  anthropicBaseUrl: anthropicBaseUrl.value,
  anthropicModel: anthropicModel.value,
  ollamaApiKey: ollamaApiKey.value,
  ollamaBaseUrl: ollamaBaseUrl.value,
  ollamaModel: ollamaModel.value,
  temperature: temperature.value,
  // DingTalk settings
  enableTaskReminder: true,
  dingtalkWebhook: '',
  dingtalkSecret: '',
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
  formData.ollamaApiKey = ollamaApiKey.value
  formData.ollamaBaseUrl = ollamaBaseUrl.value
  formData.ollamaModel = ollamaModel.value
  formData.temperature = temperature.value

  // Load DingTalk settings from backend
  const response = await fetch('http://localhost:8000/api/settings/')
  const data = await response.json()
  formData.enableTaskReminder = data.enable_task_reminder ?? true
  formData.dingtalkWebhook = data.dingtalk_webhook || ''
  formData.dingtalkSecret = data.dingtalk_secret || ''
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
    console.log('[SettingsView] Starting save...')

    // 构建保存数据 - 只包含当前选中的provider
    const saveData: any = {
      llm_provider: formData.llmProvider,  // 必须发送（决定LangGraph使用哪个LLM）
      temperature: formData.temperature,    // 通用配置
      dingtalk_webhook: formData.dingtalkWebhook,
      dingtalk_secret: formData.dingtalkSecret,
      enable_task_reminder: formData.enableTaskReminder,
    }

    // 根据选中的provider，只发送对应配置
    // 未发送的配置会保留在.env中不被覆盖
    if (formData.llmProvider === 'openai') {
      saveData.openai_api_key = formData.openaiApiKey
      saveData.openai_api_base = formData.openaiBaseUrl
      saveData.openai_model = formData.openaiModel
      // 不发送 Claude 和 Ollama 的配置 → 后端不更新它们
    } else if (formData.llmProvider === 'claude') {
      saveData.anthropic_api_key = formData.anthropicApiKey
      saveData.anthropic_api_base = formData.anthropicBaseUrl
      saveData.anthropic_model = formData.anthropicModel
      // 不发送 OpenAI 和 Ollama 的配置
    } else if (formData.llmProvider === 'ollama') {
      saveData.ollama_api_key = formData.ollamaApiKey
      saveData.ollama_base_url = formData.ollamaBaseUrl
      saveData.ollama_model = formData.ollamaModel
      // 不发送 OpenAI 和 Claude 的配置
    }

    console.log('[SettingsView] Save data:', saveData)

    const response = await fetch('http://localhost:8000/api/settings/', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(saveData)
    })

    console.log('[SettingsView] API response:', response.ok)

    if (response.ok) {
      ElMessage.success(`配置保存成功！当前使用: ${formData.llmProvider.toUpperCase()}`)
    } else {
      ElMessage.error('保存失败，请检查后端服务')
    }
  } catch (error) {
    console.error('[SettingsView] Save error:', error)
    ElMessage.error('配置保存失败')
  } finally {
    saving.value = false
  }
}

/**
 * Test LLM connection
 */
async function handleTestLLM() {
  testingLLM.value = true

  try {
    // 使用表单当前值进行测试（不保存）
    const result = await validateLLMConfig(formData.llmProvider, {
      openaiApiKey: formData.openaiApiKey,
      openaiModel: formData.openaiModel,
      openaiBaseUrl: formData.openaiBaseUrl,
      anthropicApiKey: formData.anthropicApiKey,
      anthropicModel: formData.anthropicModel,
      anthropicBaseUrl: formData.anthropicBaseUrl,
      ollamaApiKey: formData.ollamaApiKey,
      ollamaModel: formData.ollamaModel,
      ollamaBaseUrl: formData.ollamaBaseUrl,
    })

    if (result.valid) {
      ElMessage.success({
        message: `✅ 连接成功！已测试模型: ${result.modelTested}`,
        duration: 3000
      })
    } else {
      ElMessage.error({
        message: `❌ 连接失败: ${result.errorMessage}`,
        duration: 5000
      })
    }
  } catch (error) {
    console.error('[SettingsView] Test LLM error:', error)
    ElMessage.error('测试请求失败')
  } finally {
    testingLLM.value = false
  }
}

/**
 * Test DingTalk notification
 */
async function handleTestDingTalk() {
  // 前端验证：必须启用且填写webhook
  if (!formData.enableTaskReminder) {
    ElMessage.warning('请先启用任务提醒')
    return
  }

  if (!formData.dingtalkWebhook) {
    ElMessage.warning('请先填写 Webhook URL')
    return
  }

  testingDingTalk.value = true

  try {
    // 调用后端新增的测试API
    const response = await fetch('http://localhost:8000/api/settings/test-dingtalk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        webhook: formData.dingtalkWebhook,
        secret: formData.dingtalkSecret || ''
      })
    })

    const result = await response.json()

    if (response.ok && result.success) {
      ElMessage.success({
        message: '📱 测试消息已发送，请在钉钉群查看',
        duration: 3000
      })
    } else {
      ElMessage.error({
        message: `❌ 发送失败: ${result.error || '未知错误'}`,
        duration: 5000
      })
    }
  } catch (error) {
    console.error('[SettingsView] Test DingTalk error:', error)
    ElMessage.error('测试请求失败')
  } finally {
    testingDingTalk.value = false
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
    formData.ollamaApiKey = ollamaApiKey.value
    formData.ollamaBaseUrl = ollamaBaseUrl.value
    formData.ollamaModel = ollamaModel.value
    formData.temperature = temperature.value
    formData.enableTaskReminder = true
    formData.dingtalkWebhook = ''
    formData.dingtalkSecret = ''

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
.common-section,
.dingtalk-section {
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
