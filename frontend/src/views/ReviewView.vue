<template>
  <div class="review-view">
    <!-- Header -->
    <div class="view-header">
      <div class="header-left">
        <h1 class="page-title">数据复盘</h1>
        <div class="header-stats">
          <span class="stat-item">{{ selectedPeriod }}</span>
          <span class="stat-divider">·</span>
          <span class="stat-item">{{ formatDateRange() }}</span>
        </div>
      </div>
      <div class="header-actions">
        <el-select v-model="selectedPeriod" style="width: 120px" @change="loadReviewData">
          <el-option label="本周" value="week" />
          <el-option label="本月" value="month" />
          <el-option label="本季度" value="quarter" />
          <el-option label="本年" value="year" />
        </el-select>
        <el-button type="primary" @click="handleGenerateReport">
          <el-icon><DocumentCopy /></el-icon>
          生成报告
        </el-button>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="summary-cards">
      <div
        v-for="card in summaryCards"
        :key="card.key"
        class="summary-card"
        :class="card.key"
      >
        <div class="card-icon">{{ card.icon }}</div>
        <div class="card-content">
          <div class="card-value">{{ card.value }}</div>
          <div class="card-label">{{ card.label }}</div>
        </div>
        <div class="card-trend" :class="card.trendType">
          <el-icon v-if="card.trendType === 'up'"><TrendCharts /></el-icon>
          <el-icon v-else-if="card.trendType === 'down'"><Bottom /></el-icon>
          <span>{{ card.trendText }}</span>
        </div>
      </div>
    </div>

    <!-- Charts Grid -->
    <div class="charts-grid">
      <!-- Task Completion Trend -->
      <div class="chart-card full-width">
        <div class="chart-header">
          <h3 class="chart-title">
            <el-icon><TrendCharts /></el-icon>
            任务完成趋势
          </h3>
          <el-radio-group v-model="completionChartType" size="small">
            <el-radio-button value="line">折线图</el-radio-button>
            <el-radio-button value="bar">柱状图</el-radio-button>
          </el-radio-group>
        </div>
        <div ref="completionChartRef" class="chart-container"></div>
      </div>

      <!-- Priority Distribution -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">
            <el-icon><PieChart /></el-icon>
            优先级分布
          </h3>
        </div>
        <div ref="priorityChartRef" class="chart-container"></div>
      </div>

      <!-- Procrastination Analysis -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">
            <el-icon><Warning /></el-icon>
            拖延分析
          </h3>
        </div>
        <div ref="procrastinationChartRef" class="chart-container"></div>
      </div>

      <!-- Knowledge Growth -->
      <div class="chart-card full-width">
        <div class="chart-header">
          <h3 class="chart-title">
            <el-icon><Reading /></el-icon>
            知识增长路径
          </h3>
        </div>
        <div ref="knowledgeChartRef" class="chart-container"></div>
      </div>

      <!-- Time Distribution -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">
            <el-icon><Clock /></el-icon>
            时间分布
          </h3>
        </div>
        <div ref="timeDistributionChartRef" class="chart-container"></div>
      </div>

      <!-- Project Progress -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">
            <el-icon><Folder /></el-icon>
            项目进度
          </h3>
        </div>
        <div ref="projectProgressChartRef" class="chart-container"></div>
      </div>
    </div>

    <!-- Insights Section -->
    <div class="insights-section">
      <div class="section-header">
        <h2 class="section-title">
          <el-icon><MagicStick /></el-icon>
          智能洞察
        </h2>
      </div>
      <div class="insights-grid">
        <div
          v-for="insight in insights"
          :key="insight.id"
          class="insight-card"
          :class="insight.type"
        >
          <div class="insight-icon">{{ insight.icon }}</div>
          <div class="insight-content">
            <h4 class="insight-title">{{ insight.title }}</h4>
            <p class="insight-description">{{ insight.description }}</p>
            <div v-if="insight.suggestion" class="insight-suggestion">
              <el-icon><Promotion /></el-icon>
              <span>{{ insight.suggestion }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DocumentCopy,
  TrendCharts,
  Bottom,
  PieChart,
  Warning,
  Reading,
  Clock,
  Folder,
  MagicStick,
  Promotion
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import type { ECharts } from 'echarts'

// ============================================
// Types
// ============================================
interface SummaryCard {
  key: string
  icon: string
  label: string
  value: string | number
  trendType: 'up' | 'down' | 'neutral'
  trendText: string
}

interface Insight {
  id: string
  type: 'positive' | 'warning' | 'info'
  icon: string
  title: string
  description: string
  suggestion?: string
}

// ============================================
// State
// ============================================
const selectedPeriod = ref('week')
const completionChartType = ref('line')

// Chart refs
const completionChartRef = ref<HTMLElement>()
const priorityChartRef = ref<HTMLElement>()
const procrastinationChartRef = ref<HTMLElement>()
const knowledgeChartRef = ref<HTMLElement>()
const timeDistributionChartRef = ref<HTMLElement>()
const projectProgressChartRef = ref<HTMLElement>()

// Chart instances
let completionChart: ECharts | null = null
let priorityChart: ECharts | null = null
let procrastinationChart: ECharts | null = null
let knowledgeChart: ECharts | null = null
let timeDistributionChart: ECharts | null = null
let projectProgressChart: ECharts | null = null

// Data will be loaded from API
const summaryCards = ref<SummaryCard[]>([])

const insights = ref<Insight[]>([])

// ============================================
// Methods
// ============================================
function formatDateRange(): string {
  const now = new Date()
  if (selectedPeriod.value === 'week') {
    const weekStart = new Date(now)
    weekStart.setDate(now.getDate() - now.getDay() + 1)
    const weekEnd = new Date(weekStart)
    weekEnd.setDate(weekStart.getDate() + 6)
    return `${formatDate(weekStart)} - ${formatDate(weekEnd)}`
  } else if (selectedPeriod.value === 'month') {
    return `${now.getFullYear()}年${now.getMonth() + 1}月`
  } else if (selectedPeriod.value === 'quarter') {
    const quarter = Math.floor(now.getMonth() / 3) + 1
    return `${now.getFullYear()}年 Q${quarter}`
  } else {
    return `${now.getFullYear()}年`
  }
}

function formatDate(date: Date): string {
  return `${date.getMonth() + 1}/${date.getDate()}`
}

function loadReviewData() {
  // Mock: Load data based on selected period
  ElMessage.success(`已切换到${selectedPeriod.value === 'week' ? '本周' : selectedPeriod.value === 'month' ? '本月' : selectedPeriod.value === 'quarter' ? '本季度' : '本年'}数据`)

  // Reinitialize charts with new data
  nextTick(() => {
    initCompletionChart()
    initPriorityChart()
    initProcrastinationChart()
    initKnowledgeChart()
    initTimeDistributionChart()
    initProjectProgressChart()
  })
}

function handleGenerateReport() {
  ElMessage.success('正在生成复盘报告...')
}

function initCompletionChart() {
  if (!completionChartRef.value) return

  if (completionChart) {
    completionChart.dispose()
  }

  completionChart = echarts.init(completionChartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['已完成', '未完成', '完成率'],
      top: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    },
    yAxis: [
      {
        type: 'value',
        name: '任务数'
      },
      {
        type: 'value',
        name: '完成率 (%)',
        max: 100
      }
    ],
    series: [
      {
        name: '已完成',
        type: completionChartType.value,
        data: [5, 7, 6, 8, 5, 3, 4],
        itemStyle: {
          color: '#67c23a'
        }
      },
      {
        name: '未完成',
        type: completionChartType.value,
        data: [2, 1, 2, 0, 2, 3, 2],
        itemStyle: {
          color: '#f56c6c'
        }
      },
      {
        name: '完成率',
        type: 'line',
        yAxisIndex: 1,
        data: [71, 88, 75, 100, 71, 50, 67],
        itemStyle: {
          color: '#409eff'
        },
        smooth: true
      }
    ]
  }

  completionChart.setOption(option)
}

function initPriorityChart() {
  if (!priorityChartRef.value) return

  if (priorityChart) {
    priorityChart.dispose()
  }

  priorityChart = echarts.init(priorityChartRef.value)

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        label: {
          show: true,
          formatter: '{b}\n{d}%'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: [
          { value: 8, name: '高优先级', itemStyle: { color: '#f56c6c' } },
          { value: 15, name: '中优先级', itemStyle: { color: '#e6a23c' } },
          { value: 12, name: '低优先级', itemStyle: { color: '#409eff' } }
        ]
      }
    ]
  }

  priorityChart.setOption(option)
}

function initProcrastinationChart() {
  if (!procrastinationChartRef.value) return

  if (procrastinationChart) {
    procrastinationChart.dispose()
  }

  procrastinationChart = echarts.init(procrastinationChartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '平均延后天数'
    },
    yAxis: {
      type: 'category',
      data: ['文档编写', '代码review', '会议准备', '学习任务', '日常事务']
    },
    series: [
      {
        type: 'bar',
        data: [
          { value: 3.5, itemStyle: { color: '#f56c6c' } },
          { value: 2.1, itemStyle: { color: '#e6a23c' } },
          { value: 1.8, itemStyle: { color: '#e6a23c' } },
          { value: 0.9, itemStyle: { color: '#67c23a' } },
          { value: 0.5, itemStyle: { color: '#67c23a' } }
        ]
      }
    ]
  }

  procrastinationChart.setOption(option)
}

function initKnowledgeChart() {
  if (!knowledgeChartRef.value) return

  if (knowledgeChart) {
    knowledgeChart.dispose()
  }

  knowledgeChart = echarts.init(knowledgeChartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['前端开发', '系统设计', '产品思维', '个人成长'],
      top: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['第1周', '第2周', '第3周', '第4周']
    },
    yAxis: {
      type: 'value',
      name: '笔记数量'
    },
    series: [
      {
        name: '前端开发',
        type: 'line',
        stack: 'Total',
        areaStyle: {},
        emphasis: {
          focus: 'series'
        },
        data: [3, 5, 6, 8],
        itemStyle: { color: '#667eea' }
      },
      {
        name: '系统设计',
        type: 'line',
        stack: 'Total',
        areaStyle: {},
        emphasis: {
          focus: 'series'
        },
        data: [2, 3, 4, 4],
        itemStyle: { color: '#f093fb' }
      },
      {
        name: '产品思维',
        type: 'line',
        stack: 'Total',
        areaStyle: {},
        emphasis: {
          focus: 'series'
        },
        data: [1, 2, 2, 3],
        itemStyle: { color: '#4facfe' }
      },
      {
        name: '个人成长',
        type: 'line',
        stack: 'Total',
        areaStyle: {},
        emphasis: {
          focus: 'series'
        },
        data: [1, 1, 2, 2],
        itemStyle: { color: '#43e97b' }
      }
    ]
  }

  knowledgeChart.setOption(option)
}

function initTimeDistributionChart() {
  if (!timeDistributionChartRef.value) return

  if (timeDistributionChart) {
    timeDistributionChart.dispose()
  }

  timeDistributionChart = echarts.init(timeDistributionChartRef.value)

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}h ({d}%)'
    },
    series: [
      {
        type: 'pie',
        radius: '60%',
        data: [
          { value: 12, name: '工作任务', itemStyle: { color: '#667eea' } },
          { value: 6, name: '学习充电', itemStyle: { color: '#f093fb' } },
          { value: 4, name: '个人项目', itemStyle: { color: '#4facfe' } },
          { value: 2, name: '健康管理', itemStyle: { color: '#43e97b' } }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }

  timeDistributionChart.setOption(option)
}

function initProjectProgressChart() {
  if (!projectProgressChartRef.value) return

  if (projectProgressChart) {
    projectProgressChart.dispose()
  }

  projectProgressChart = echarts.init(projectProgressChartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      max: 100
    },
    yAxis: {
      type: 'category',
      data: ['工作项目', '个人学习', '健康管理', '副业探索']
    },
    series: [
      {
        type: 'bar',
        data: [
          { value: 75, itemStyle: { color: '#67c23a' } },
          { value: 60, itemStyle: { color: '#409eff' } },
          { value: 45, itemStyle: { color: '#e6a23c' } },
          { value: 20, itemStyle: { color: '#909399' } }
        ],
        label: {
          show: true,
          position: 'right',
          formatter: '{c}%'
        }
      }
    ]
  }

  projectProgressChart.setOption(option)
}

// ============================================
// Lifecycle
// ============================================
onMounted(() => {
  nextTick(() => {
    initCompletionChart()
    initPriorityChart()
    initProcrastinationChart()
    initKnowledgeChart()
    initTimeDistributionChart()
    initProjectProgressChart()
  })

  // Handle window resize
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)

  // Dispose all charts
  completionChart?.dispose()
  priorityChart?.dispose()
  procrastinationChart?.dispose()
  knowledgeChart?.dispose()
  timeDistributionChart?.dispose()
  projectProgressChart?.dispose()
})

function handleResize() {
  completionChart?.resize()
  priorityChart?.resize()
  procrastinationChart?.resize()
  knowledgeChart?.resize()
  timeDistributionChart?.resize()
  projectProgressChart?.resize()
}

// Watch chart type change
import { watch } from 'vue'
watch(completionChartType, () => {
  initCompletionChart()
})
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';
@import '@/assets/styles/mixins.scss';

.review-view {
  max-width: 1600px;
  margin: 0 auto;
}

// ============================================
// Header
// ============================================
.view-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: $spacing-xl;

  .header-left {
    .page-title {
      font-size: $font-size-xxl;
      font-weight: 600;
      color: $color-text-primary;
      margin: 0 0 $spacing-sm 0;
    }

    .header-stats {
      display: flex;
      align-items: center;
      gap: $spacing-md;
      font-size: $font-size-sm;
      color: $color-text-secondary;

      .stat-divider {
        color: $color-text-tertiary;
      }
    }
  }

  .header-actions {
    display: flex;
    gap: $spacing-md;
  }
}

// ============================================
// Summary Cards
// ============================================
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: $spacing-lg;
  margin-bottom: $spacing-xl;
}

.summary-card {
  @include card-base;
  display: flex;
  align-items: center;
  gap: $spacing-lg;
  padding: $spacing-lg;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    transform: translateY(-2px);
    box-shadow: $shadow-lg;
  }

  .card-icon {
    font-size: 36px;
    line-height: 1;
  }

  .card-content {
    flex: 1;

    .card-value {
      font-size: $font-size-xxl;
      font-weight: 600;
      color: $color-text-primary;
      line-height: 1.2;
    }

    .card-label {
      font-size: $font-size-sm;
      color: $color-text-secondary;
      margin-top: $spacing-xs;
    }
  }

  .card-trend {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    font-size: $font-size-xs;
    padding: $spacing-xs $spacing-sm;
    border-radius: $radius-sm;
    white-space: nowrap;

    &.up {
      background-color: rgba(103, 194, 58, 0.1);
      color: $color-success;
    }

    &.down {
      background-color: rgba(245, 108, 108, 0.1);
      color: $color-danger;
    }

    &.neutral {
      background-color: $bg-color-hover;
      color: $color-text-secondary;
    }
  }

  // Card specific colors
  &.completed {
    border-left: 4px solid $color-success;
  }

  &.completion_rate {
    border-left: 4px solid $color-primary;
  }

  &.notes_created {
    border-left: 4px solid $color-warning;
  }

  &.focus_time {
    border-left: 4px solid $color-info;
  }
}

// ============================================
// Charts Grid
// ============================================
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $spacing-lg;
  margin-bottom: $spacing-xl;
}

.chart-card {
  @include card-base;
  padding: $spacing-lg;

  &.full-width {
    grid-column: 1 / -1;
  }

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-lg;

    .chart-title {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      margin: 0;
      font-size: $font-size-lg;
      font-weight: 600;
      color: $color-text-primary;
    }
  }

  .chart-container {
    width: 100%;
    height: 300px;
  }
}

// ============================================
// Insights Section
// ============================================
.insights-section {
  .section-header {
    margin-bottom: $spacing-lg;

    .section-title {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      font-size: $font-size-xl;
      font-weight: 600;
      color: $color-text-primary;
      margin: 0;
    }
  }
}

.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: $spacing-lg;
}

.insight-card {
  @include card-base;
  display: flex;
  gap: $spacing-lg;
  padding: $spacing-lg;
  transition: all $transition-fast;

  &:hover {
    transform: translateY(-2px);
    box-shadow: $shadow-lg;
  }

  .insight-icon {
    font-size: 32px;
    line-height: 1;
    flex-shrink: 0;
  }

  .insight-content {
    flex: 1;

    .insight-title {
      font-size: $font-size-md;
      font-weight: 600;
      color: $color-text-primary;
      margin: 0 0 $spacing-sm 0;
    }

    .insight-description {
      font-size: $font-size-sm;
      color: $color-text-regular;
      line-height: 1.6;
      margin: 0 0 $spacing-md 0;
    }

    .insight-suggestion {
      display: flex;
      align-items: flex-start;
      gap: $spacing-xs;
      padding: $spacing-sm;
      background-color: $bg-color-hover;
      border-radius: $radius-sm;
      font-size: $font-size-xs;
      color: $color-text-secondary;
      line-height: 1.5;
    }
  }

  // Type-specific styling
  &.positive {
    border-left: 4px solid $color-success;
  }

  &.warning {
    border-left: 4px solid $color-warning;
  }

  &.info {
    border-left: 4px solid $color-primary;
  }
}
</style>
