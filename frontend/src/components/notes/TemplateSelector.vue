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
        :class="{ 'selected': selectedTemplate?.id === template.id }"
        @click="selectTemplate(template)"
      >
        <div class="template-icon">{{ template.icon || '📝' }}</div>
        <div class="template-info">
          <h4 class="template-name">{{ template.name }}</h4>
          <p class="template-description">{{ template.description || '无描述' }}</p>
        </div>
        <el-icon v-if="selectedTemplate?.id === template.id" class="check-icon">
          <CircleCheck />
        </el-icon>
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
import { ElMessage } from 'element-plus'
import { CircleCheck } from '@element-plus/icons-vue'
import type { Template, TemplateRenderResponse } from '@/types'
import apiClient from '@/api/client'

const emit = defineEmits<{
  (e: 'select', rendered: TemplateRenderResponse): void
  (e: 'cancel'): void
}>()

const templates = ref<Template[]>([])
const categories = ref<string[]>([])
const selectedCategory = ref<string | null>(null)
const selectedTemplate = ref<Template | null>(null)
const loading = ref(false)

const filteredTemplates = computed(() => {
  if (selectedCategory.value === null) {
    return templates.value
  }
  return templates.value.filter(t => t.category === selectedCategory.value)
})

onMounted(async () => {
  await Promise.all([
    fetchTemplates(),
    fetchCategories()
  ])
})

async function fetchTemplates() {
  try {
    loading.value = true
    const response = await apiClient.get('/templates/')
    templates.value = response.data
  } catch (error) {
    console.error('Failed to fetch templates:', error)
    ElMessage.error('加载模板失败')
  } finally {
    loading.value = false
  }
}

async function fetchCategories() {
  try {
    const response = await apiClient.get('/templates/categories')
    categories.value = response.data
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  }
}

function selectTemplate(template: Template) {
  selectedTemplate.value = template
}

async function handleConfirm() {
  if (!selectedTemplate.value) return

  try {
    loading.value = true
    const response = await apiClient.post<TemplateRenderResponse>(
      `/templates/${selectedTemplate.value.id}/render`,
      null,
      {
        params: {
          title: `新笔记 - ${selectedTemplate.value.name}`
        }
      }
    )
    emit('select', response.data)
  } catch (error) {
    console.error('Failed to render template:', error)
    ElMessage.error('渲染模板失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';

.template-selector {
  padding: $spacing-lg;
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

.category-filter {
  display: flex;
  gap: $spacing-sm;
  margin-bottom: $spacing-lg;
  flex-wrap: wrap;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: $spacing-md;
  flex: 1;
  margin-bottom: $spacing-lg;
}

.template-card {
  position: relative;
  border: 2px solid $color-border;
  border-radius: $radius-md;
  padding: $spacing-lg;
  cursor: pointer;
  transition: all $transition-base;
  background: white;

  &:hover {
    border-color: $color-primary;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  &.selected {
    border-color: $color-primary;
    background: linear-gradient(135deg, #f5f7fa 0%, #f0f2ff 100%);
  }

  .template-icon {
    font-size: 48px;
    text-align: center;
    margin-bottom: $spacing-md;
  }

  .template-info {
    .template-name {
      font-size: $font-size-lg;
      font-weight: 600;
      color: $color-text-primary;
      margin: 0 0 $spacing-sm 0;
      text-align: center;
    }

    .template-description {
      font-size: $font-size-sm;
      color: $color-text-secondary;
      margin: 0;
      text-align: center;
      line-height: 1.5;
      min-height: 3em;
    }
  }

  .check-icon {
    position: absolute;
    top: $spacing-md;
    right: $spacing-md;
    font-size: 24px;
    color: $color-primary;
  }
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: $spacing-md;
  padding-top: $spacing-lg;
  border-top: 1px solid $color-border;
}
</style>
