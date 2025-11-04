<template>
  <div
    class="connector-line"
    :class="[`connector-${line.type}`, `position-${line.position}`]"
    :style="{ borderColor: line.color }"
  ></div>
</template>

<script setup lang="ts">
interface ConnectorLineData {
  type: 'enter' | 'exit'
  color: string
  position: 'top' | 'bottom'
}

interface Props {
  line: ConnectorLineData
}

defineProps<Props>()
</script>

<style scoped lang="scss">
.connector-line {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 2px;
  border-left: 2px dashed;
  z-index: 5;
  pointer-events: none;

  // Enter connector (from previous segment into aggregation)
  &.connector-enter {
    &.position-top {
      top: -10px;
      height: 10px;
    }

    &.position-bottom {
      bottom: -10px;
      height: 10px;
    }
  }

  // Exit connector (from aggregation to next segment)
  &.connector-exit {
    &.position-top {
      top: -10px;
      height: 10px;
    }

    &.position-bottom {
      bottom: -10px;
      height: 10px;
    }
  }
}
</style>
