<template>
  <div class="review-view">
    <el-alert
      title="复盘功能开发中"
      type="info"
      description="复盘仪表盘将在后续版本中实现。敬请期待！"
      show-icon
      :closable="false"
    />

    <div class="placeholder-content">
      <h3>计划功能</h3>
      <ul>
        <li>任务完成统计和趋势分析</li>
        <li>拖延模式识别</li>
        <li>知识增长路径可视化</li>
        <li>个性化洞察和建议</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
// Review view - placeholder for future implementation
</script>

<style scoped>
.review-view {
  max-width: 1200px;
  margin: 0 auto;
}

.placeholder-content {
  background: #fff;
  padding: 40px;
  border-radius: 8px;
  margin-top: 24px;
}

.placeholder-content h3 {
  color: #303133;
  margin-bottom: 20px;
}

.placeholder-content ul {
  color: #606266;
  line-height: 2;
}
</style>
