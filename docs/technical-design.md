# AI互动小说项目技术设计文档

## 📋 项目概述

### 🎯 项目目标
构建一个AI驱动的互动式小说平台，用户可以选择主题、自定义主人公，通过选择或自由输入影响故事发展，享受完全自由的小说互动体验。

### 🔥 核心功能
1. **主题选择**：都市、科幻、修仙、武侠四大主题
2. **角色定制**：用户自定义或AI生成主人公信息
3. **智能选择**：每章节提供3个AI生成的选择选项
4. **自由输入**：用户可完全自定义故事走向
5. **上下文连贯**：基于历史内容和用户选择生成后续章节

## 🏗️ 技术架构

### 整体架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端应用层     │    │   API网关层     │    │   AI服务层      │
│                │    │                │    │                │
│ React + Next.js │◄──►│ Next.js API    │◄──►│ OpenAI GPT-4   │
│ TypeScript     │    │ Routes         │    │ Claude-3       │
│ TailwindCSS    │    │ 中间件层        │    │ 本地备用模型    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   状态管理层     │    │   业务逻辑层     │    │   数据存储层     │
│                │    │                │    │                │
│ Zustand        │    │ 故事生成服务     │    │ PostgreSQL     │
│ React Query    │    │ 上下文管理      │    │ Redis缓存      │
│ 本地缓存        │    │ 用户管理        │    │ Pinecone向量库  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 技术栈选择

#### 前端技术栈
- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript
- **样式**: TailwindCSS + Framer Motion
- **状态管理**: Zustand
- **数据获取**: React Query (TanStack Query)
- **表单处理**: React Hook Form + Zod

#### 后端技术栈
- **运行时**: Node.js
- **框架**: Next.js API Routes
- **ORM**: Prisma
- **数据库**: PostgreSQL (主库) + Redis (缓存)
- **向量数据库**: Pinecone (AI记忆存储)

#### AI服务
- **主要模型**: OpenAI GPT-4
- **备用模型**: Anthropic Claude-3
- **本地备用**: Ollama (可选)

## 📊 数据模型设计

### 核心实体关系
```
User (用户)
├── Story (故事) 1:N
│   ├── Chapter (章节) 1:N
│   │   └── Choice (选择) 1:N
│   └── StoryContext (故事上下文) 1:1
└── UserPreference (用户偏好) 1:N
```

### 数据库Schema
```sql
-- 用户表
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 故事表
CREATE TABLE stories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  title VARCHAR(255) NOT NULL,
  theme VARCHAR(50) NOT NULL,
  protagonist_info JSONB NOT NULL,
  current_chapter_id UUID,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 章节表
CREATE TABLE chapters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  story_id UUID REFERENCES stories(id),
  previous_chapter_id UUID REFERENCES chapters(id),
  chapter_number INTEGER NOT NULL,
  content TEXT NOT NULL,
  ai_prompt_used TEXT,
  choices_offered JSONB DEFAULT '[]',
  created_at TIMESTAMP DEFAULT NOW()
);

-- 选择表
CREATE TABLE choices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chapter_id UUID REFERENCES chapters(id),
  next_chapter_id UUID REFERENCES chapters(id),
  choice_text TEXT NOT NULL,
  user_input TEXT,
  is_custom BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 故事上下文表
CREATE TABLE story_contexts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  story_id UUID REFERENCES stories(id) UNIQUE,
  character_profiles JSONB DEFAULT '{}',
  world_building JSONB DEFAULT '{}',
  plot_threads JSONB DEFAULT '{}',
  user_preferences JSONB DEFAULT '{}',
  context_summary TEXT,
  updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🧠 AI上下文管理方案

### 上下文管理架构
```
用户选择 → 上下文聚合 → 记忆提取 → 提示词构建 → AI生成 → 内容验证 → 上下文更新
```

### 分层记忆管理
1. **短期记忆**: 最近3-5个章节的详细内容
2. **中期记忆**: 重要情节点和角色发展
3. **长期记忆**: 世界观设定、角色背景、核心冲突
4. **向量记忆**: 基于语义相似度的内容检索

### 上下文压缩策略
- **Token限制**: 控制在模型上下文窗口的80%以内
- **重要性评分**: 基于时间衰减、用户交互、情节重要性
- **智能摘要**: 对次要内容进行摘要压缩
- **动态调整**: 根据生成质量动态调整上下文策略

## 🔌 API接口设计

### 核心API端点

#### 故事管理
```typescript
GET    /api/stories           # 获取故事列表
POST   /api/stories           # 创建新故事
GET    /api/stories/[id]      # 获取故事详情
PUT    /api/stories/[id]      # 更新故事信息
DELETE /api/stories/[id]      # 删除故事
```

#### 章节生成
```typescript
POST   /api/chapters/generate # 生成新章节
GET    /api/chapters/[id]     # 获取章节详情
PUT    /api/chapters/[id]     # 更新章节内容
```

#### AI服务
```typescript
POST   /api/ai/generate-protagonist  # AI生成主人公
POST   /api/ai/suggest-choices      # AI建议选择选项
POST   /api/ai/validate-content     # 内容质量验证
```

### API响应格式
```typescript
interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: {
    timestamp: string;
    requestId: string;
    version: string;
  };
}
```

## 📁 项目结构

```
ai-novel/
├── src/
│   ├── app/                 # Next.js App Router
│   │   ├── (auth)/         # 认证页面
│   │   ├── story/          # 故事相关页面
│   │   ├── api/            # API路由
│   │   └── globals.css     # 全局样式
│   ├── components/         # React组件
│   │   ├── ui/            # 基础UI组件
│   │   ├── story/         # 故事相关组件
│   │   └── layout/        # 布局组件
│   ├── lib/               # 核心业务逻辑
│   │   ├── ai/           # AI服务
│   │   ├── database/     # 数据库操作
│   │   ├── services/     # 业务服务
│   │   ├── utils/        # 工具函数
│   │   └── types/        # TypeScript类型
│   ├── store/            # 状态管理
│   └── hooks/            # 自定义Hooks
├── prisma/               # 数据库Schema
├── docs/                 # 项目文档
├── tests/                # 测试文件
└── public/               # 静态资源
```

## 🚀 实施计划

### Phase 1: 基础架构 (1周)
- [ ] 项目初始化和环境配置
- [ ] 数据库设计和Prisma设置
- [ ] 基础UI组件开发
- [ ] 用户认证系统

### Phase 2: 核心功能 (2周)
- [ ] 故事创建和主题选择
- [ ] AI服务集成
- [ ] 章节生成和显示
- [ ] 基础上下文管理

### Phase 3: 高级功能 (2周)
- [ ] 智能选择生成
- [ ] 高级上下文管理
- [ ] 性能优化
- [ ] 用户体验优化

### Phase 4: 测试部署 (1周)
- [ ] 全面测试
- [ ] 性能调优
- [ ] 部署配置
- [ ] 监控设置

## 📈 性能优化策略

### 前端优化
- **代码分割**: 按路由和功能模块分割
- **图片优化**: Next.js Image组件自动优化
- **缓存策略**: React Query智能缓存
- **懒加载**: 组件和数据的懒加载

### 后端优化
- **数据库优化**: 索引优化、查询优化
- **缓存策略**: Redis多层缓存
- **API限流**: 防止滥用和过载
- **CDN加速**: 静态资源CDN分发

### AI服务优化
- **并发控制**: 限制同时进行的AI请求
- **响应缓存**: 相似请求结果缓存
- **降级策略**: 多模型备用方案
- **成本控制**: Token使用监控和优化

## 🔒 安全考虑

### 数据安全
- **用户数据加密**: 敏感信息加密存储
- **API安全**: JWT认证 + HTTPS
- **输入验证**: 严格的输入验证和清理
- **SQL注入防护**: Prisma ORM防护

### AI安全
- **内容过滤**: 不当内容检测和过滤
- **提示词注入防护**: 用户输入清理
- **使用监控**: AI服务使用监控
- **成本控制**: 防止恶意使用

## 📊 监控和分析

### 性能监控
- **应用性能**: Vercel Analytics
- **错误追踪**: Sentry
- **数据库监控**: Prisma监控
- **AI服务监控**: 自定义监控

### 用户分析
- **用户行为**: Google Analytics
- **故事数据**: 自定义分析
- **AI生成质量**: 用户反馈收集
- **系统使用**: 使用统计和趋势

---

*文档版本: v1.0*  
*最后更新: 2024-01-10*  
*作者: AI互动小说架构专家*
