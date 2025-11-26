<template>
  <el-collapse v-model="activePanel" class="references-collapse">
    <el-collapse-item name="references">
      <template #title>
        <div class="collapse-title">
          <el-icon :size="16" color="#67c23a">
            <Document />
          </el-icon>
          <span>知识引用 ({{ totalReferences }}条)</span>
          <el-tag v-if="hasSearchQuery" size="small" type="success" effect="plain">
            查询: {{ firstQuery }}
          </el-tag>
        </div>
      </template>

      <!-- Multiple reference queries -->
      <div v-for="(refData, queryIndex) in references" :key="`query-${queryIndex}`">
        <!-- Query header (if multiple queries) -->
        <div v-if="references.length > 1" class="query-header">
          <el-icon :size="14">
            <Search />
          </el-icon>
          <span class="query-text">查询: {{ refData.query }}</span>
          <el-tag size="small" type="info">{{ refData.references.length }}条结果</el-tag>
        </div>

        <!-- Reference cards -->
        <div class="reference-list">
          <el-card
            v-for="(ref, refIndex) in refData.references"
            :key="`ref-${queryIndex}-${refIndex}`"
            class="reference-card"
            shadow="hover"
          >
            <!-- Reference header -->
            <div class="ref-header">
              <div class="ref-info">
                <el-icon :size="16" color="#409eff">
                  <Notebook />
                </el-icon>
                <span class="ref-name">{{ ref.name }}</span>
              </div>

              <!-- Metadata tags -->
              <div class="ref-meta">
                <el-tag
                  v-if="ref.meta_data.note_title"
                  size="small"
                  type="primary"
                  effect="plain"
                >
                  {{ ref.meta_data.note_title }}
                </el-tag>
                <el-tag size="small" type="info" effect="plain">
                  分块 {{ ref.meta_data.chunk }}/{{ ref.meta_data.chunk_size }}
                </el-tag>
              </div>
            </div>

            <!-- Reference content -->
            <div class="ref-content">
              <p>{{ ref.content }}</p>
            </div>

            <!-- Footer actions -->
            <div class="ref-footer">
              <el-button
                v-if="ref.meta_data.note_id"
                size="small"
                text
                type="primary"
                @click="viewNote(ref.meta_data.note_id)"
              >
                <el-icon><Link /></el-icon>
                查看原笔记
              </el-button>
            </div>
          </el-card>
        </div>

        <!-- Query execution time -->
        <div v-if="refData.time" class="query-metrics">
          <el-icon :size="12">
            <Timer />
          </el-icon>
          <span>检索耗时: {{ refData.time.toFixed(2) }}ms</span>
        </div>

        <el-divider v-if="queryIndex < references.length - 1" />
      </div>
    </el-collapse-item>
  </el-collapse>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  Document,
  Search,
  Notebook,
  Link,
  Timer
} from '@element-plus/icons-vue'
import type { ReferenceData } from '@/types/chat'

/**
 * Props
 */
interface Props {
  references: ReferenceData[]
}

const props = defineProps<Props>()

/**
 * Router
 */
const router = useRouter()

/**
 * Collapse state (default expanded)
 */
const activePanel = ref(['references'])

/**
 * Total number of references across all queries
 */
const totalReferences = computed(() => {
  return props.references.reduce((sum, refData) => {
    return sum + refData.references.length
  }, 0)
})

/**
 * Check if has search query
 */
const hasSearchQuery = computed(() => {
  return props.references.length > 0 && props.references[0].query
})

/**
 * First query text (for display in title)
 */
const firstQuery = computed(() => {
  if (props.references.length === 0) return ''
  const query = props.references[0].query
  return query.length > 30 ? query.substring(0, 30) + '...' : query
})

/**
 * Navigate to note detail view
 */
function viewNote(noteId: number) {
  router.push({
    name: 'notes',
    query: { id: noteId }
  })
}
</script>

<style scoped lang="scss">
.references-collapse {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #f0f9ff;

  :deep(.el-collapse-item__header) {
    background: transparent;
    padding: 0 12px;
    border: none;
    font-weight: 600;
  }

  :deep(.el-collapse-item__content) {
    padding: 12px;
  }
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #303133;
  flex-wrap: wrap;
}

.query-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #ffffff;
  border-radius: 6px;
  border-left: 3px solid #67c23a;

  .query-text {
    font-size: 13px;
    font-weight: 600;
    color: #303133;
    flex: 1;
  }
}

.reference-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reference-card {
  :deep(.el-card__body) {
    padding: 12px;
  }

  .ref-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 10px;
    gap: 12px;

    .ref-info {
      display: flex;
      align-items: center;
      gap: 6px;
      flex: 1;
      min-width: 0;

      .ref-name {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }

    .ref-meta {
      display: flex;
      gap: 6px;
      flex-shrink: 0;
      flex-wrap: wrap;
    }
  }

  .ref-content {
    font-size: 13px;
    line-height: 1.6;
    color: #606266;
    background: #f9fafb;
    padding: 10px 12px;
    border-radius: 4px;
    border-left: 3px solid #67c23a;
    margin-bottom: 10px;

    p {
      margin: 0;
      display: -webkit-box;
      -webkit-line-clamp: 4;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
  }

  .ref-footer {
    display: flex;
    justify-content: flex-end;
  }
}

.query-metrics {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 12px;
  font-size: 12px;
  color: #909399;
  font-style: italic;
}
</style>
