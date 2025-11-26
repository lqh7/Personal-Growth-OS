<template>
  <el-popover
    :width="400"
    trigger="hover"
    placement="top"
  >
    <template #reference>
      <el-tag
        :type="tagType"
        :effect="toolCall.tool_call_error ? 'dark' : 'light'"
        size="small"
        class="tool-badge"
      >
        <el-icon :size="14" style="margin-right: 4px">
          <component :is="toolIcon" />
        </el-icon>
        {{ toolCall.tool_name }}
        <span v-if="executionTime" class="execution-time">
          ({{ executionTime }}ms)
        </span>
      </el-tag>
    </template>

    <!-- Popover content -->
    <div class="tool-details">
      <div class="detail-header">
        <el-icon :size="18" :color="iconColor">
          <component :is="toolIcon" />
        </el-icon>
        <span class="tool-title">{{ toolCall.tool_name }}</span>
      </div>

      <el-divider style="margin: 12px 0" />

      <!-- Tool arguments -->
      <div v-if="hasArguments" class="detail-section">
        <div class="section-label">参数:</div>
        <pre class="code-block">{{ formatJSON(toolCall.tool_args) }}</pre>
      </div>

      <!-- Tool result -->
      <div v-if="toolCall.content" class="detail-section">
        <div class="section-label">结果:</div>
        <div class="result-content">{{ toolCall.content }}</div>
      </div>

      <!-- Execution metrics -->
      <div v-if="executionTime" class="detail-section">
        <div class="section-label">执行时间:</div>
        <div class="metric-value">{{ executionTime }} 毫秒</div>
      </div>

      <!-- Error indicator -->
      <div v-if="toolCall.tool_call_error" class="detail-section error">
        <el-alert
          type="error"
          :closable="false"
          show-icon
          title="工具执行失败"
        />
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Tools, Check, Close, Loading } from '@element-plus/icons-vue'
import type { ToolCall } from '@/types/chat'

/**
 * Props
 */
interface Props {
  toolCall: ToolCall
}

const props = defineProps<Props>()

/**
 * Tag type based on status
 */
const tagType = computed(() => {
  if (props.toolCall.tool_call_error) return 'danger'
  if (props.toolCall.content) return 'success'
  return 'info'
})

/**
 * Icon based on status
 */
const toolIcon = computed(() => {
  if (props.toolCall.tool_call_error) return Close
  if (props.toolCall.content) return Check
  return Tools
})

/**
 * Icon color
 */
const iconColor = computed(() => {
  if (props.toolCall.tool_call_error) return '#f56c6c'
  if (props.toolCall.content) return '#67c23a'
  return '#909399'
})

/**
 * Execution time in milliseconds
 */
const executionTime = computed(() => {
  return props.toolCall.metrics?.time
    ? Math.round(props.toolCall.metrics.time)
    : null
})

/**
 * Check if tool has arguments
 */
const hasArguments = computed(() => {
  return (
    props.toolCall.tool_args &&
    Object.keys(props.toolCall.tool_args).length > 0
  )
})

/**
 * Format JSON for display
 */
function formatJSON(obj: Record<string, unknown>): string {
  return JSON.stringify(obj, null, 2)
}
</script>

<style scoped lang="scss">
.tool-badge {
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .execution-time {
    margin-left: 4px;
    font-size: 11px;
    opacity: 0.8;
  }
}

.tool-details {
  .detail-header {
    display: flex;
    align-items: center;
    gap: 8px;

    .tool-title {
      font-weight: 600;
      font-size: 15px;
      color: #303133;
    }
  }

  .detail-section {
    margin-bottom: 12px;

    &:last-child {
      margin-bottom: 0;
    }

    &.error {
      margin-top: 12px;
    }

    .section-label {
      font-size: 13px;
      font-weight: 600;
      color: #606266;
      margin-bottom: 6px;
    }

    .code-block {
      background-color: #f5f7fa;
      padding: 8px 12px;
      border-radius: 4px;
      font-size: 12px;
      font-family: 'Consolas', 'Monaco', monospace;
      color: #606266;
      overflow-x: auto;
      max-height: 200px;
      margin: 0;
    }

    .result-content {
      font-size: 13px;
      color: #606266;
      line-height: 1.6;
      max-height: 150px;
      overflow-y: auto;
    }

    .metric-value {
      font-size: 13px;
      color: #409eff;
      font-weight: 600;
    }
  }
}
</style>
