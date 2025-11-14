<template>
  <div
    :class="['task-card', `variant-${variant}`, { completed: task.completed }]"
    @click="handleClick"
  >
    <!-- Default Variant (Kanban Card) -->
    <template v-if="variant === 'default'">
      <div class="card-header">
        <el-checkbox
          v-model="task.completed"
          @click.stop
          @change="$emit('complete', task.id)"
        />
        <div class="card-priority">
          <el-rate
            v-model="task.priority"
            disabled
            :max="5"
            size="small"
            show-score
            score-template=""
          />
        </div>
        <el-dropdown trigger="click" @command="handleCommand">
          <span @click.stop>
            <el-icon class="more-icon"><MoreFilled /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-if="task.status === 'overdue'" command="complete">
                <el-icon><Check /></el-icon>
                已完成
              </el-dropdown-item>
              <el-dropdown-item v-if="!task.startTime && !task.endTime" command="schedule">
                <el-icon><Calendar /></el-icon>
                安排
              </el-dropdown-item>
              <el-dropdown-item v-if="task.startTime || task.endTime" command="snooze">
                <el-icon><Clock /></el-icon>
                延后
              </el-dropdown-item>
              <el-dropdown-item command="edit">
                <el-icon><Edit /></el-icon>
                编辑
              </el-dropdown-item>
              <el-dropdown-item command="delete" divided>
                <el-icon><Delete /></el-icon>
                删除
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <div class="card-content">
        <h4 class="card-title" :class="{ completed: task.completed }">
          {{ task.title }}
        </h4>
        <!-- 延后标签 -->
        <el-tag v-if="task.snoozeUntil" size="small" type="warning" class="snooze-tag">
          <el-icon><Clock /></el-icon>
          已延后至 {{ formatSnoozeDate(task.snoozeUntil) }}
        </el-tag>
        <p v-if="task.description" class="card-description">
          {{ task.description }}
        </p>
      </div>

      <div class="card-footer">
        <div class="footer-left">
          <el-tag
            v-if="task.project"
            size="small"
            class="project-tag"
            :style="{ borderLeftColor: task.project.color }"
          >
            {{ task.project.name }}
          </el-tag>
        </div>
        <div class="footer-right">
          <span v-if="task.endTime || task.startTime" class="due-date" :class="getDateClass(task.endTime || task.startTime)">
            <el-icon><Clock /></el-icon>
            {{ formatTaskDate(task.endTime || task.startTime) }}
          </span>
        </div>
      </div>
    </template>

    <!-- Compact Variant (List Item) -->
    <template v-else-if="variant === 'compact'">
      <div class="compact-content">
        <el-checkbox
          v-model="task.completed"
          @click.stop
          @change="$emit('complete', task.id)"
        />
        <div class="compact-main">
          <span class="compact-title" :class="{ completed: task.completed }">
            {{ task.title }}
          </span>
          <div class="compact-meta">
            <el-tag
              v-if="task.project"
              size="small"
              class="project-tag"
              :style="{ borderLeftColor: task.project.color }"
            >
              {{ task.project.name }}
            </el-tag>
            <el-rate v-model="task.priority" disabled :max="5" size="small" />
            <span v-if="task.endTime || task.startTime" class="due-date" :class="getDateClass(task.endTime || task.startTime)">
              {{ formatTaskDate(task.endTime || task.startTime) }}
            </span>
          </div>
        </div>
        <div class="compact-actions">
          <el-button size="small" text @click.stop="$emit('snooze', task.id)">
            <el-icon><Clock /></el-icon>
          </el-button>
          <el-button size="small" text type="danger" @click.stop="$emit('delete', task.id)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </template>

    <!-- Calendar Variant (Minimal Display) -->
    <template v-else-if="variant === 'calendar'">
      <div class="calendar-content">
        <div class="calendar-indicator" :style="{ backgroundColor: getPriorityColor(task.priority) }"></div>
        <div class="calendar-main">
          <span class="calendar-title" :class="{ completed: task.completed }">
            {{ task.title }}
          </span>
          <div v-if="task.project" class="calendar-project">
            <span class="project-dot" :style="{ backgroundColor: task.project.color }"></span>
            <span class="project-name">{{ task.project.name }}</span>
          </div>
        </div>
        <el-checkbox
          v-model="task.completed"
          size="small"
          @click.stop
          @change="$emit('complete', task.id)"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { MoreFilled, Clock, Edit, Delete, Calendar, Check } from '@element-plus/icons-vue'

// ============================================
// Props & Emits
// ============================================
interface Task {
  id: string
  title: string
  description?: string
  status: string
  priority: number
  dueDate?: Date
  startTime?: Date
  endTime?: Date
  snoozeUntil?: Date
  completed: boolean
  project?: {
    id: string
    name: string
    color: string
  }
}

interface Props {
  task: Task
  variant?: 'default' | 'compact' | 'calendar'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default'
})

const emit = defineEmits<{
  click: [id: string]
  complete: [id: string]
  snooze: [id: string]
  schedule: [id: string]
  delete: [id: string]
}>()

// ============================================
// Methods
// ============================================
function handleClick() {
  emit('click', props.task.id)
}

function handleCommand(command: string) {
  if (command === 'complete') {
    emit('complete', props.task.id)
  } else if (command === 'snooze') {
    emit('snooze', props.task.id)
  } else if (command === 'schedule') {
    emit('schedule', props.task.id)
  } else if (command === 'edit') {
    emit('click', props.task.id)
  } else if (command === 'delete') {
    emit('delete', props.task.id)
  }
}

function formatTaskDate(date: Date): string {
  const now = new Date()
  const diff = date.getTime() - now.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) return '今天'
  if (days === 1) return '明天'
  if (days < 0) return `已过期 ${Math.abs(days)} 天`
  if (days <= 7) return `${days} 天后`

  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

function getDateClass(date: Date): string {
  const now = new Date()
  const diff = date.getTime() - now.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days < 0) return 'overdue'
  if (days === 0) return 'today'
  if (days <= 2) return 'soon'
  return ''
}

function getPriorityColor(priority: number): string {
  if (priority >= 4) return '#f56c6c' // High - Red
  if (priority >= 2) return '#e6a23c' // Medium - Orange
  return '#909399' // Low - Gray
}

function formatSnoozeDate(date: Date): string {
  const now = new Date()
  const diff = date.getTime() - now.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(hours / 24)

  if (days > 1) return `${days}天后`
  if (days === 1) return '明天'
  if (hours > 0) return `${hours}小时后`
  return '即将开始'
}
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';
@import '@/assets/styles/mixins.scss';

.task-card {
  transition: all $transition-fast;

  &.completed {
    opacity: 0.7;
  }
}

// ============================================
// Default Variant (Kanban Card)
// ============================================
.variant-default {
  @include card-base;
  padding: $spacing-md;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  min-height: 180px;
  height: 100%;

  &:hover {
    @include hover-lift;
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    margin-bottom: $spacing-md;
    flex-shrink: 0;

    .card-priority {
      flex: 1;
      display: flex;
      justify-content: flex-end;
    }

    .more-icon {
      color: $color-text-tertiary;
      cursor: pointer;
      transition: color $transition-fast;

      &:hover {
        color: $color-text-primary;
      }
    }
  }

  .card-content {
    flex: 1;
    margin-bottom: $spacing-md;
    overflow: hidden;

    .card-title {
      font-size: $font-size-md;
      font-weight: 500;
      color: $color-text-primary;
      margin: 0 0 $spacing-xs 0;
      line-height: 1.4;
      @include text-ellipsis-multiline(2);

      &.completed {
        text-decoration: line-through;
        color: $color-text-tertiary;
      }
    }

    .card-description {
      font-size: $font-size-sm;
      color: $color-text-secondary;
      margin: 0;
      line-height: 1.5;
      @include text-ellipsis-multiline(2);
    }

    .snooze-tag {
      margin-top: $spacing-xs;
      margin-bottom: $spacing-xs;
      font-size: $font-size-xs;
      display: inline-flex;
      align-items: center;
      gap: 4px;

      .el-icon {
        font-size: 12px;
      }
    }
  }

  .card-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-shrink: 0;
    margin-top: auto;

    .footer-left {
      .project-tag {
        border: 1px solid $color-border;
        border-left-width: 3px;
        font-size: $font-size-xs;
        background-color: $bg-color-card;
        color: $color-text-primary;
        font-weight: 500;
      }
    }

    .footer-right {
      .due-date {
        display: flex;
        align-items: center;
        gap: $spacing-xs;
        font-size: $font-size-xs;
        color: $color-text-secondary;

        &.overdue {
          color: $color-danger;
          font-weight: 600;
        }

        &.today {
          color: $color-warning;
          font-weight: 600;
        }

        &.soon {
          color: $color-primary;
          font-weight: 500;
        }
      }
    }
  }
}

// ============================================
// Compact Variant (List Item)
// ============================================
.variant-compact {
  padding: $spacing-md;
  border-bottom: 1px solid $color-border;
  cursor: pointer;
  transition: background-color $transition-fast;

  &:hover {
    background-color: $bg-color-hover;
  }

  &:last-child {
    border-bottom: none;
  }

  .compact-content {
    display: flex;
    align-items: center;
    gap: $spacing-md;

    .compact-main {
      flex: 1;
      min-width: 0;

      .compact-title {
        display: block;
        font-size: $font-size-sm;
        font-weight: 500;
        color: $color-text-primary;
        margin-bottom: $spacing-xs;
        @include text-ellipsis;

        &.completed {
          text-decoration: line-through;
          color: $color-text-tertiary;
        }
      }

      .compact-meta {
        display: flex;
        align-items: center;
        gap: $spacing-md;
        font-size: $font-size-xs;

        .project-tag {
          border: 1px solid $color-border;
          border-left-width: 3px;
          background-color: $bg-color-card;
          color: $color-text-primary;
          font-weight: 500;
        }

        .due-date {
          color: $color-text-secondary;

          &.overdue {
            color: $color-danger;
            font-weight: 600;
          }

          &.today {
            color: $color-warning;
            font-weight: 600;
          }

          &.soon {
            color: $color-primary;
          }
        }
      }
    }

    .compact-actions {
      display: flex;
      gap: $spacing-xs;
      opacity: 0;
      transition: opacity $transition-fast;
    }
  }

  &:hover .compact-actions {
    opacity: 1;
  }
}

// ============================================
// Calendar Variant (Minimal)
// ============================================
.variant-calendar {
  padding: $spacing-xs $spacing-sm;
  background-color: $bg-color-card;
  border-radius: $radius-sm;
  border-left: 3px solid transparent;
  margin-bottom: $spacing-xs;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    background-color: $bg-color-hover;
    transform: translateX(2px);
  }

  .calendar-content {
    display: flex;
    align-items: center;
    gap: $spacing-sm;

    .calendar-indicator {
      width: 3px;
      height: 20px;
      border-radius: $radius-sm;
      flex-shrink: 0;
    }

    .calendar-main {
      flex: 1;
      min-width: 0;

      .calendar-title {
        display: block;
        font-size: $font-size-xs;
        color: $color-text-primary;
        margin-bottom: 2px;
        @include text-ellipsis;

        &.completed {
          text-decoration: line-through;
          color: $color-text-tertiary;
        }
      }

      .calendar-project {
        display: flex;
        align-items: center;
        gap: $spacing-xs;

        .project-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
        }

        .project-name {
          font-size: $font-size-xs;
          color: $color-text-tertiary;
          @include text-ellipsis;
        }
      }
    }
  }
}

// ============================================
// Responsive
// ============================================
@media (max-width: 768px) {
  .variant-default {
    .card-title {
      font-size: $font-size-sm;
    }

    .card-description {
      font-size: $font-size-xs;
    }
  }

  .variant-compact {
    .compact-meta {
      flex-wrap: wrap;
    }

    .compact-actions {
      opacity: 1; // Always show on mobile
    }
  }
}
</style>
