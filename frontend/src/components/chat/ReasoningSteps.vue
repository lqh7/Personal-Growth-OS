<template>
  <el-collapse v-model="activeSteps" class="reasoning-collapse">
    <el-collapse-item name="reasoning">
      <template #title>
        <div class="collapse-title">
          <el-icon :size="16" color="#409eff">
            <Operation />
          </el-icon>
          <span>推理过程 ({{ steps.length }}步)</span>
        </div>
      </template>

      <!-- Reasoning steps timeline -->
      <el-timeline class="reasoning-timeline">
        <el-timeline-item
          v-for="(step, index) in steps"
          :key="`step-${index}`"
          :icon="getStepIcon(step)"
          :type="getStepType(step)"
          :color="getStepColor(step)"
          :hollow="false"
        >
          <!-- Step header -->
          <div class="step-header">
            <span class="step-title">{{ step.title }}</span>
            <el-tag
              v-if="step.confidence !== undefined"
              :type="getConfidenceType(step.confidence)"
              size="small"
              effect="plain"
            >
              置信度: {{ (step.confidence * 100).toFixed(0) }}%
            </el-tag>
          </div>

          <!-- Step action -->
          <div v-if="step.action" class="step-section">
            <div class="section-label">执行动作:</div>
            <div class="section-content action">{{ step.action }}</div>
          </div>

          <!-- Step reasoning -->
          <div class="step-section">
            <div class="section-label">推理逻辑:</div>
            <div class="section-content reasoning">{{ step.reasoning }}</div>
          </div>

          <!-- Step result -->
          <div class="step-section">
            <div class="section-label">结果:</div>
            <div class="section-content result">{{ step.result }}</div>
          </div>

          <!-- Next action hint -->
          <div v-if="step.next_action" class="step-section">
            <div class="section-label">下一步:</div>
            <div class="section-content next-action">
              <el-icon :size="14" style="margin-right: 4px">
                <Right />
              </el-icon>
              {{ step.next_action }}
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
    </el-collapse-item>
  </el-collapse>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Operation, Right, CircleCheck, Warning, InfoFilled } from '@element-plus/icons-vue'
import type { ReasoningStep } from '@/types/chat'
import type { Component } from 'vue'

/**
 * Props
 */
interface Props {
  steps: ReasoningStep[]
}

const props = defineProps<Props>()

/**
 * Collapse state (default expanded)
 */
const activeSteps = ref(['reasoning'])

/**
 * Get step icon based on confidence
 */
function getStepIcon(step: ReasoningStep): Component {
  if (step.confidence === undefined) return InfoFilled

  if (step.confidence >= 0.8) return CircleCheck
  if (step.confidence >= 0.5) return InfoFilled
  return Warning
}

/**
 * Get step type for timeline
 */
function getStepType(step: ReasoningStep): string {
  if (step.confidence === undefined) return 'primary'

  if (step.confidence >= 0.8) return 'success'
  if (step.confidence >= 0.5) return 'primary'
  return 'warning'
}

/**
 * Get step color
 */
function getStepColor(step: ReasoningStep): string {
  if (step.confidence === undefined) return '#409eff'

  if (step.confidence >= 0.8) return '#67c23a'
  if (step.confidence >= 0.5) return '#409eff'
  return '#e6a23c'
}

/**
 * Get confidence tag type
 */
function getConfidenceType(confidence: number): string {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.5) return 'primary'
  return 'warning'
}
</script>

<style scoped lang="scss">
.reasoning-collapse {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #f9fafb;

  :deep(.el-collapse-item__header) {
    background: transparent;
    padding: 0 12px;
    border: none;
    font-weight: 600;
  }

  :deep(.el-collapse-item__content) {
    padding: 0 12px 12px 12px;
  }
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #303133;
}

.reasoning-timeline {
  padding-top: 8px;

  :deep(.el-timeline-item__wrapper) {
    padding-left: 24px;
  }

  :deep(.el-timeline-item__tail) {
    border-left: 2px dashed #dcdfe6;
  }
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  .step-title {
    font-size: 15px;
    font-weight: 600;
    color: #303133;
  }
}

.step-section {
  margin-bottom: 10px;

  &:last-child {
    margin-bottom: 0;
  }

  .section-label {
    font-size: 12px;
    font-weight: 600;
    color: #909399;
    margin-bottom: 4px;
  }

  .section-content {
    font-size: 13px;
    line-height: 1.6;
    color: #606266;
    padding: 6px 10px;
    border-radius: 4px;
    background: #ffffff;

    &.action {
      border-left: 3px solid #409eff;
    }

    &.reasoning {
      border-left: 3px solid #67c23a;
    }

    &.result {
      border-left: 3px solid #e6a23c;
    }

    &.next-action {
      display: flex;
      align-items: center;
      border-left: 3px solid #909399;
      font-style: italic;
    }
  }
}
</style>
