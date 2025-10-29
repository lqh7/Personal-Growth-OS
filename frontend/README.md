# Personal Growth OS - Frontend

Vue 3 + TypeScript + Element Plus frontend for Personal Growth OS.

## 技术栈

- **Vue 3** - Composition API
- **TypeScript** - 类型安全
- **Vite** - 快速构建工具
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Element Plus** - UI组件库
- **Axios** - HTTP客户端

## 开发环境设置

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

应用将在 `http://localhost:5173` 启动。

### 构建生产版本

```bash
npm run build
```

构建输出在 `dist/` 目录。

### 预览生产构建

```bash
npm run preview
```

## 项目结构

```
src/
├── api/              # API客户端和请求封装
│   └── client.ts     # Axios配置
├── components/       # Vue组件
│   ├── tasks/        # 任务相关组件
│   ├── notes/        # 笔记相关组件
│   └── common/       # 通用组件
├── layouts/          # 布局组件
│   └── MainLayout.vue
├── stores/           # Pinia状态管理
│   ├── taskStore.ts
│   └── noteStore.ts
├── views/            # 页面视图
│   ├── TasksView.vue
│   ├── NotesView.vue
│   └── ReviewView.vue
├── router/           # 路由配置
│   └── index.ts
├── types/            # TypeScript类型定义
│   └── index.ts
├── App.vue           # 根组件
├── main.ts           # 应用入口
└── style.css         # 全局样式
```

## 核心功能

### 任务管理 (`/tasks`)

- 任务列表（待办/进行中/已完成）
- 任务CRUD操作
- **任务启动仪式**: AI辅助任务分解
- 任务延后(Snooze)功能

### 笔记管理 (`/notes`)

- 笔记CRUD操作
- Markdown编辑器
- 标签系统
- **语义搜索**: RAG驱动的智能搜索
- 来源URL追踪

### 复盘分析 (`/review`)

- 占位页面（功能开发中）

## 状态管理

使用Pinia进行状态管理，主要包括：

### TaskStore
- `tasks` - 任务列表
- `fetchTasks()` - 获取任务
- `createTask()` - 创建任务
- `updateTask()` - 更新任务
- `deleteTask()` - 删除任务
- `snoozeTask()` - 延后任务
- `igniteTask()` - 任务启动仪式

### NoteStore
- `notes` - 笔记列表
- `tags` - 标签列表
- `fetchNotes()` - 获取笔记
- `createNote()` - 创建笔记
- `updateNote()` - 更新笔记
- `deleteNote()` - 删除笔记
- `searchNotesSemantic()` - 语义搜索

## API代理

开发环境下，Vite会自动代理 `/api` 请求到后端服务器（`http://localhost:8000`）。

配置见 `vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## 环境变量

创建 `.env.local` 文件配置本地环境变量（如果需要）。

## TypeScript配置

项目使用严格的TypeScript配置。所有类型定义在 `src/types/index.ts`。

## 开发建议

1. **组件开发**: 遵循Vue 3 Composition API最佳实践
2. **状态管理**: 使用Pinia stores而非组件内部状态
3. **类型安全**: 充分利用TypeScript类型系统
4. **代码风格**: 保持简洁，避免过度工程化

## 构建优化

- 使用Vite的快速HMR
- 组件懒加载（路由级别）
- Element Plus按需导入（已全量导入，后续可优化）

## 故障排除

### 端口冲突

如果5173端口被占用，Vite会自动尝试下一个可用端口。

### API请求失败

确保后端服务器正在运行（`http://localhost:8000`）。

### 依赖安装问题

尝试删除 `node_modules` 和 `package-lock.json`，然后重新安装：

```bash
rm -rf node_modules package-lock.json
npm install
```

## MVP版本说明

当前是最小可用原型版本，专注于核心功能。未来迭代将增加：

- 更丰富的Markdown编辑器
- 实时协作功能
- PWA支持
- 性能优化和代码分割
