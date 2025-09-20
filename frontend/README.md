# Telegram消息转发机器人 - React前端

一个现代化的React前端界面，用于管理Telegram消息转发机器人。

## 🚀 技术栈

- **React 18** + **TypeScript** - 现代化前端框架
- **Vite** - 快速构建工具
- **Ant Design** - 企业级UI组件库
- **Zustand** - 轻量级状态管理
- **React Query** - 服务端状态管理
- **React Router v6** - 路由管理
- **ECharts** - 数据可视化
- **Axios** - HTTP客户端

## 📁 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── components/        # 可复用组件
│   │   ├── common/       # 通用组件
│   │   ├── forms/        # 表单组件
│   │   └── charts/       # 图表组件
│   ├── pages/            # 页面组件
│   │   ├── Dashboard/    # 仪表板
│   │   ├── Rules/        # 转发规则管理
│   │   ├── Logs/         # 消息日志
│   │   ├── Settings/     # 系统设置
│   │   └── Chats/        # 聊天管理
│   ├── services/         # API服务
│   ├── stores/           # 状态管理
│   ├── types/            # TypeScript类型
│   ├── utils/            # 工具函数
│   └── hooks/            # 自定义Hooks
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## 🛠️ 开发命令

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview

# 代码检查
npm run lint
```

## 🔧 配置说明

### 环境变量
创建 `.env.local` 文件：
```
VITE_API_URL=http://localhost:9393
VITE_DEV_TOOLS=true
```

### API代理
开发环境下，Vite会自动代理 `/api` 请求到后端服务器（默认 `http://localhost:9393`）。

## 🎨 主要功能

### 1. 仪表板 (Dashboard)
- 实时系统状态监控
- 消息转发统计图表
- 最近日志和活跃规则
- 关键指标展示

### 2. 转发规则管理 (Rules)
- 规则列表和搜索
- 规则创建和编辑
- 关键词过滤设置
- 正则替换配置
- 批量操作

### 3. 消息日志 (Logs)
- 分页日志列表
- 高级筛选功能
- 日志导出
- 统计分析

### 4. 聊天管理 (Chats)
- 聊天列表展示
- 聊天选择器
- 实时数据刷新

### 5. 系统设置 (Settings)
- Telegram配置
- 代理设置
- 系统参数
- 主题切换

## 🔄 状态管理

### Zustand Stores
- `useAppStore` - 全局应用状态（主题、用户信息等）
- `useRulesStore` - 规则管理状态

### React Query
- 服务端数据缓存和同步
- 自动重试和错误处理
- 实时数据更新

## 🎯 API集成

所有API调用都通过 `services/` 目录下的服务模块进行：
- `api.ts` - 基础API客户端
- `rules.ts` - 规则相关API
- `logs.ts` - 日志相关API
- `system.ts` - 系统管理API

## 🎨 主题系统

支持浅色/深色/自动三种主题模式：
- 基于CSS变量的主题切换
- 保留原有毛玻璃效果
- 响应式设计

## 🔒 类型安全

完整的TypeScript类型定义：
- API接口类型
- 组件Props类型
- 状态管理类型
- 路由参数类型

## 📱 响应式设计

- 移动端优先设计
- 多断点适配
- 侧边栏自适应折叠
- 表格横向滚动

## 🚀 部署说明

### 开发环境
1. 启动后端服务：`python web_app.py`
2. 启动前端开发服务器：`npm run dev`
3. 访问：`http://localhost:3000`

### 生产环境
1. 构建前端：`npm run build`
2. 后端会自动服务构建后的文件
3. 访问：`http://localhost:9393/app`

## 🔧 开发工具

- **ESLint** - 代码质量检查
- **Prettier** - 代码格式化
- **TypeScript** - 类型检查
- **React DevTools** - React调试
- **React Query DevTools** - 状态调试

## 📝 注意事项

1. **API兼容性**：前端API调用与后端完全兼容
2. **数据流向**：使用React Query管理服务端状态
3. **错误处理**：全局错误边界和API错误处理
4. **性能优化**：代码分割、懒加载、虚拟滚动
5. **安全性**：CSRF保护、XSS防护、API权限验证