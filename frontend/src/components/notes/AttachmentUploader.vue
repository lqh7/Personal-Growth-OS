<template>
  <div class="attachment-uploader">
    <el-upload
      ref="uploadRef"
      :action="uploadUrl"
      :data="uploadData"
      :on-success="handleSuccess"
      :on-error="handleError"
      :before-upload="beforeUpload"
      :file-list="fileList"
      :limit="10"
      :show-file-list="true"
      multiple
      drag
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        拖拽文件到此处或 <em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持图片、PDF、Office文档、文本文件等，单个文件最大50MB
        </div>
      </template>
    </el-upload>

    <!-- Attachment List -->
    <div v-if="attachments.length > 0" class="attachment-list">
      <h4>已上传附件 ({{ attachments.length }})</h4>
      <div v-for="att in attachments" :key="att.id" class="attachment-item">
        <el-icon class="file-icon">
          <component :is="getFileIcon(att.mimetype)" />
        </el-icon>
        <div class="attachment-info">
          <span class="filename">{{ att.filename }}</span>
          <span class="filesize">{{ formatFileSize(att.filesize) }}</span>
        </div>
        <div class="attachment-actions">
          <el-button
            size="small"
            type="primary"
            link
            @click="downloadAttachment(att)"
          >
            下载
          </el-button>
          <el-button
            size="small"
            type="danger"
            link
            @click="deleteAttachment(att.id)"
          >
            删除
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document, Picture, VideoCamera, Headset, FolderOpened } from '@element-plus/icons-vue'
import type { UploadFile, UploadInstance } from 'element-plus'
import type { Attachment } from '@/types'
import apiClient from '@/api/client'

interface Props {
  noteId: number
  attachments: Attachment[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:attachments', attachments: Attachment[]): void
  (e: 'upload-success', attachment: Attachment): void
  (e: 'delete-success', attachmentId: number): void
}>()

const uploadRef = ref<UploadInstance>()
const fileList = ref<UploadFile[]>([])

const uploadUrl = computed(() => {
  return `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/attachments/?note_id=${props.noteId}`
})

const uploadData = computed(() => ({
  note_id: props.noteId
}))

function beforeUpload(file: File) {
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    ElMessage.error(`文件 ${file.name} 超过50MB限制`)
    return false
  }

  const allowedTypes = [
    'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain', 'text/markdown', 'text/csv',
    'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
    'application/json'
  ]

  if (!allowedTypes.includes(file.type)) {
    ElMessage.error(`文件类型 ${file.type} 不支持`)
    return false
  }

  return true
}

function handleSuccess(response: Attachment) {
  ElMessage.success('文件上传成功')
  emit('upload-success', response)
  emit('update:attachments', [...props.attachments, response])
  fileList.value = []
}

function handleError(error: any) {
  console.error('Upload error:', error)
  ElMessage.error('文件上传失败')
}

async function downloadAttachment(attachment: Attachment) {
  try {
    const response = await apiClient.get(`/attachments/${attachment.id}/download`, {
      responseType: 'blob'
    })

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', attachment.filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Download error:', error)
    ElMessage.error('下载失败')
  }
}

async function deleteAttachment(attachmentId: number) {
  try {
    await apiClient.delete(`/attachments/${attachmentId}`)
    ElMessage.success('附件已删除')
    emit('delete-success', attachmentId)
    emit('update:attachments', props.attachments.filter(a => a.id !== attachmentId))
  } catch (error) {
    console.error('Delete error:', error)
    ElMessage.error('删除失败')
  }
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

function getFileIcon(mimetype: string) {
  if (mimetype.startsWith('image/')) return Picture
  if (mimetype.startsWith('video/')) return VideoCamera
  if (mimetype.startsWith('audio/')) return Headset
  if (mimetype.includes('pdf')) return Document
  if (mimetype.includes('zip') || mimetype.includes('rar') || mimetype.includes('7z')) return FolderOpened
  return Document
}
</script>

<style scoped lang="scss">
@import '@/assets/styles/variables.scss';

.attachment-uploader {
  :deep(.el-upload-dragger) {
    padding: $spacing-xl;
    border-radius: $radius-md;
    transition: all $transition-base;

    &:hover {
      border-color: $color-primary;
    }
  }

  .el-icon--upload {
    font-size: 48px;
    color: $color-text-tertiary;
    margin-bottom: $spacing-md;
  }

  .el-upload__text {
    color: $color-text-secondary;
    font-size: $font-size-md;

    em {
      color: $color-primary;
      font-style: normal;
    }
  }

  .el-upload__tip {
    margin-top: $spacing-sm;
    color: $color-text-tertiary;
    font-size: $font-size-xs;
  }
}

.attachment-list {
  margin-top: $spacing-xl;

  h4 {
    font-size: $font-size-md;
    font-weight: 600;
    color: $color-text-primary;
    margin-bottom: $spacing-md;
  }

  .attachment-item {
    display: flex;
    align-items: center;
    padding: $spacing-md;
    border: 1px solid $color-border;
    border-radius: $radius-md;
    margin-bottom: $spacing-sm;
    transition: all $transition-base;

    &:hover {
      background-color: #fafafa;
      border-color: $color-primary;
    }

    .file-icon {
      font-size: 24px;
      color: $color-primary;
      margin-right: $spacing-md;
      flex-shrink: 0;
    }

    .attachment-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 4px;

      .filename {
        font-size: $font-size-md;
        color: $color-text-primary;
        font-weight: 500;
      }

      .filesize {
        font-size: $font-size-xs;
        color: $color-text-tertiary;
      }
    }

    .attachment-actions {
      display: flex;
      gap: $spacing-sm;
      flex-shrink: 0;
    }
  }
}
</style>
