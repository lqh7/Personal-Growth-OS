<template>
  <div class="template-selector">
    <!-- Category Filter -->
    <div class="category-filter">
      <el-button
        :type="selectedCategory === null ? 'primary' : ''"
        size="small"
        @click="selectedCategory = null"
      >
        全部
      </el-button>
      <el-button
        v-for="cat in categories"
        :key="cat"
        :type="selectedCategory === cat ? 'primary' : ''"
        size="small"
        @click="selectedCategory = cat"
      >
        {{ cat }}
      </el-button>
    </div>

    <!-- Template Grid -->
    <div class="template-grid">
      <div
        v-for="template in filteredTemplates"
        :key="template.id"
        class="template-card"
        :class="{ 'selected': selectedTemplate?.id === template.id, 'builtin': template.is_builtin }"
        @click="selectTemplate(template)"
      >
        <div class="template-icon">{{ template.icon || '📝' }}</div>
        <div class="template-info">
          <h4 class="template-name">
            {{ template.name }}
            <el-tag v-if="template.is_builtin" size="small" type="info">内置</el-tag>
          </h4>
          <p class="template-description">{{ template.description || '无描述' }}</p>
        </div>
        <el-icon v-if="selectedTemplate?.id === template.id" class="check-icon">
          <CircleCheck />
        </el-icon>

        <!-- Template Actions (only for custom templates) -->
        <div v-if="!template.is_builtin" class="template-actions" @click.stop>
          <el-button
            size="small"
            circle
            @click="handleDuplicate(template)"
            title="复制"
          >
            <el-icon><DocumentCopy /></el-icon>
          </el-button>
          <el-button
            size="small"
            circle
            type="danger"
            @click="handleDelete(template)"
            title="删除"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
        <!-- 内置模板不显示任何操作按钮，用户直接选择使用即可 -->
      </div>
    </div>

    <!-- Empty State -->
    <el-empty
      v-if="filteredTemplates.length === 0"
      description="暂无模板"
    />

    <!-- Action Buttons -->
    <div class="action-buttons">
      <el-button @click="emit('cancel')">取消</el-button>
      <el-button
        type="primary"
        :disabled="!selectedTemplate"
        @click="handleConfirm"
      >
        使用模板
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CircleCheck, DocumentCopy, Delete } from '@element-plus/icons-vue'
import type { TemplateRenderResponse } from '@/types'
import type { LocalTemplate } from '@/services/templateStorage'
import { templateStorage } from '@/services/templateStorage'

const emit = defineEmits<{
  (e: 'select', rendered: TemplateRenderResponse): void
  (e: 'cancel'): void
}>()

const templates = ref<LocalTemplate[]>([])
const categories = ref<string[]>([])
const selectedCategory = ref<string | null>(null)
const selectedTemplate = ref<LocalTemplate | null>(null)

const filteredTemplates = computed(() => {
  if (selectedCategory.value === null) {
    return templates.value
  }
  return templates.value.filter(t => t.category === selectedCategory.value)
})

onMounted(() => {
  loadTemplates()
  loadCategories()
})

function loadTemplates() {
  templates.value = templateStorage.getAllTemplates()
}

function loadCategories() {
  categories.value = templateStorage.getCategories()
}

function selectTemplate(template: LocalTemplate) {
  selectedTemplate.value = template
}

async function handleConfirm() {
  if (!selectedTemplate.value) return

  try {
    const rendered = templateStorage.renderTemplate(selectedTemplate.value.id)
    if (!rendered) {
      ElMessage.error('模板渲染失败')
      return
    }

    emit('select', rendered)
  } catch (error) {
    console.error('Failed to render template:', error)
    ElMessage.error('模板渲染失败')
  }
}

async function handleDuplicate(template: LocalTemplate) {
  try {
    const newName = await ElMessageBox.prompt('请输入新模板名称', '复制模板', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: `${template.name} (副本)`,
      inputValidator: (value) => {
        if (!value || value.trim().length === 0) {
          return '模板名称不能为空'
        }
        return true
      }
    })

    const duplicated = templateStorage.duplicateTemplate(template.id, newName.value)
    if (duplicated) {
      loadTemplates()
      loadCategories()
      ElMessage.success('模板复制成功')
    } else {
      ElMessage.error('模板复制失败')
    }
  } catch (error) {
    // User cancelled
  }
}

async function handleDelete(template: LocalTemplate) {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板 "${template.name}" 吗？此操作不可恢复。`,
      '删除模板',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const success = templateStorage.deleteTemplate(template.id)
    if (success) {
      if (selectedTemplate.value?.id === template.id) {
        selectedTemplate.value = null
      }
      loadTemplates()
      loadCategories()
      ElMessage.success('模板已删除')
    } else {
      ElMessage.error('模板删除失败')
    }
  } catch (error) {
    // User cancelled
  }
}
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';

.template-selector {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
}

.category-filter {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  max-height: 500px;
  overflow-y: auto;
}

.template-card {
  position: relative;
  border: 2px solid $color-border;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;

  &:hover {
    border-color: $color-primary;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

    .template-actions {
      opacity: 1;
    }
  }

  &.selected {
    border-color: $color-primary;
    background-color: rgba($color-primary, 0.05);
  }

  &.builtin {
    background-color: rgba($color-info, 0.02);
  }
}

.template-icon {
  font-size: 36px;
  margin-bottom: 8px;
}

.template-info {
  flex: 1;
}

.template-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: $color-text-primary;
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-description {
  margin: 0;
  font-size: 13px;
  color: $color-text-secondary;
  line-height: 1.5;
}

.check-icon {
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 24px;
  color: $color-success;
}

.template-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;

  .template-card.builtin & {
    opacity: 0.7;
  }

  .template-card:hover & {
    opacity: 1;
  }
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid $color-border;
}
</style>
