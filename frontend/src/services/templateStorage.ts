/**
 * localStorage-based template management service
 * Templates are stored per-user in browser localStorage
 */

export interface LocalTemplate {
  id: string  // UUID
  name: string
  description?: string
  content_template: string
  icon?: string
  category?: string
  created_at: string
  updated_at: string
  is_builtin: boolean  // Flag for predefined templates
}

const STORAGE_KEY = 'personal_growth_os_templates'
const BUILTIN_TEMPLATES_KEY = 'personal_growth_os_builtin_templates_initialized'

// Default built-in templates
const BUILTIN_TEMPLATES: Omit<LocalTemplate, 'id' | 'created_at' | 'updated_at'>[] = [
  {
    name: '每日日记',
    description: '记录每天的想法和事件',
    content_template: `# {title}

**日期**: {date}
**时间**: {time}

## 今日总结


## 收获与感悟


## 明日计划

`,
    icon: '📅',
    category: '生活',
    is_builtin: true
  },
  {
    name: '会议纪要',
    description: '会议记录模板',
    content_template: `# {title}

**日期**: {date}
**时间**: {time}

## 参会人员


## 会议议题


## 讨论要点


## 决策事项


## 行动项

`,
    icon: '📋',
    category: '工作',
    is_builtin: true
  },
  {
    name: '学习笔记',
    description: '学习新知识时使用',
    content_template: `# {title}

**日期**: {date}
**来源**:

## 核心概念


## 重点内容


## 个人理解


## 实践应用

`,
    icon: '📚',
    category: '学习',
    is_builtin: true
  },
  {
    name: '问题追踪',
    description: '记录和追踪问题',
    content_template: `# {title}

**日期**: {date}
**状态**: 待解决

## 问题描述


## 尝试方案


## 解决方案


## 经验总结

`,
    icon: '🐛',
    category: '工作',
    is_builtin: true
  },
  {
    name: '空白笔记',
    description: '从空白开始',
    content_template: `# {title}

`,
    icon: '📝',
    category: '其他',
    is_builtin: true
  }
]

class TemplateStorageService {
  // Initialize built-in templates on first use
  initializeBuiltinTemplates(): void {
    const initialized = localStorage.getItem(BUILTIN_TEMPLATES_KEY)
    if (!initialized) {
      const existing = this.getAllTemplates()
      const now = new Date().toISOString()

      const builtins = BUILTIN_TEMPLATES.map(t => ({
        ...t,
        id: this.generateUUID(),
        created_at: now,
        updated_at: now
      }))

      const merged = [...builtins, ...existing]
      this.saveTemplates(merged)
      localStorage.setItem(BUILTIN_TEMPLATES_KEY, 'true')
    }
  }

  // Generate UUID (simple version)
  private generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0
      const v = c == 'x' ? r : (r & 0x3 | 0x8)
      return v.toString(16)
    })
  }

  // Get all templates
  getAllTemplates(): LocalTemplate[] {
    const data = localStorage.getItem(STORAGE_KEY)
    if (!data) return []
    try {
      return JSON.parse(data)
    } catch {
      return []
    }
  }

  // Get template by ID
  getTemplate(id: string): LocalTemplate | null {
    const templates = this.getAllTemplates()
    return templates.find(t => t.id === id) || null
  }

  // Get templates by category
  getTemplatesByCategory(category: string | null): LocalTemplate[] {
    const templates = this.getAllTemplates()
    if (category === null) return templates
    return templates.filter(t => t.category === category)
  }

  // Get all unique categories
  getCategories(): string[] {
    const templates = this.getAllTemplates()
    const categories = new Set(templates.map(t => t.category).filter(Boolean) as string[])
    return Array.from(categories).sort()
  }

  // Create new template
  createTemplate(data: Omit<LocalTemplate, 'id' | 'created_at' | 'updated_at'>): LocalTemplate {
    const templates = this.getAllTemplates()
    const now = new Date().toISOString()

    const newTemplate: LocalTemplate = {
      ...data,
      id: this.generateUUID(),
      created_at: now,
      updated_at: now
    }

    templates.push(newTemplate)
    this.saveTemplates(templates)
    return newTemplate
  }

  // Update template
  updateTemplate(id: string, updates: Partial<Omit<LocalTemplate, 'id' | 'created_at' | 'updated_at' | 'is_builtin'>>): LocalTemplate | null {
    const templates = this.getAllTemplates()
    const index = templates.findIndex(t => t.id === id)

    if (index === -1) return null

    // Prevent editing built-in templates
    if (templates[index].is_builtin) {
      throw new Error('Cannot edit built-in templates. Create a copy instead.')
    }

    templates[index] = {
      ...templates[index],
      ...updates,
      updated_at: new Date().toISOString()
    }

    this.saveTemplates(templates)
    return templates[index]
  }

  // Delete template
  deleteTemplate(id: string): boolean {
    const templates = this.getAllTemplates()
    const template = templates.find(t => t.id === id)

    // Prevent deleting built-in templates
    if (template?.is_builtin) {
      throw new Error('Cannot delete built-in templates')
    }

    const filtered = templates.filter(t => t.id !== id)
    if (filtered.length === templates.length) return false

    this.saveTemplates(filtered)
    return true
  }

  // Duplicate template (useful for customizing built-ins)
  duplicateTemplate(id: string, newName?: string): LocalTemplate | null {
    const template = this.getTemplate(id)
    if (!template) return null

    return this.createTemplate({
      name: newName || `${template.name} (副本)`,
      description: template.description,
      content_template: template.content_template,
      icon: template.icon,
      category: template.category,
      is_builtin: false
    })
  }

  // Render template with placeholders
  renderTemplate(id: string, title?: string): { content: string; template_name: string; suggested_title: string } | null {
    const template = this.getTemplate(id)
    if (!template) return null

    const now = new Date()
    const replacements: Record<string, string> = {
      '{date}': now.toISOString().split('T')[0],
      '{time}': now.toTimeString().slice(0, 5),
      '{title}': title || '未命名笔记'
    }

    let content = template.content_template
    for (const [placeholder, value] of Object.entries(replacements)) {
      content = content.replaceAll(placeholder, value)
    }

    return {
      content,
      template_name: template.name,
      suggested_title: title || `${template.name} - ${replacements['{date}']}`
    }
  }

  // Export templates (for backup)
  exportTemplates(): string {
    return JSON.stringify(this.getAllTemplates(), null, 2)
  }

  // Import templates (from backup)
  importTemplates(jsonData: string, merge: boolean = true): boolean {
    try {
      const imported = JSON.parse(jsonData) as LocalTemplate[]

      if (merge) {
        const existing = this.getAllTemplates()
        const existingIds = new Set(existing.map(t => t.id))
        const newTemplates = imported.filter(t => !existingIds.has(t.id))
        this.saveTemplates([...existing, ...newTemplates])
      } else {
        this.saveTemplates(imported)
      }

      return true
    } catch {
      return false
    }
  }

  // Private: Save templates to localStorage
  private saveTemplates(templates: LocalTemplate[]): void {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(templates))
  }
}

export const templateStorage = new TemplateStorageService()
