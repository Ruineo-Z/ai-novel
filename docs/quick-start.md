# AI互动小说项目快速开始指南

## 🚀 立即开始

### 1. 项目初始化 (5分钟)

```bash
# 创建项目
npx create-next-app@latest ai-novel --typescript --tailwind --eslint --app
cd ai-novel

# 安装核心依赖
npm install prisma @prisma/client zustand @tanstack/react-query
npm install framer-motion react-hook-form @hookform/resolvers zod
npm install openai @anthropic-ai/sdk

# 安装UI组件
npm install @radix-ui/react-dialog @radix-ui/react-select
npm install @radix-ui/react-dropdown-menu @radix-ui/react-toast

# 开发依赖
npm install -D @types/node prisma
```

### 2. 环境配置 (3分钟)

创建 `.env.local` 文件：
```env
# 数据库
DATABASE_URL="postgresql://username:password@localhost:5432/ai_novel"
REDIS_URL="redis://localhost:6379"

# AI服务
OPENAI_API_KEY="your-openai-api-key"
ANTHROPIC_API_KEY="your-claude-api-key"

# 认证
NEXTAUTH_SECRET="your-secret-key"
NEXTAUTH_URL="http://localhost:3000"

# 向量数据库 (可选)
PINECONE_API_KEY="your-pinecone-key"
PINECONE_ENVIRONMENT="your-environment"
```

### 3. 数据库设置 (5分钟)

创建 `prisma/schema.prisma`：
```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        String   @id @default(cuid())
  email     String   @unique
  username  String   @unique
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  
  stories Story[]
  
  @@map("users")
}

model Story {
  id                String   @id @default(cuid())
  title             String
  theme             String
  protagonistInfo   Json
  currentChapterId  String?
  metadata          Json     @default("{}")
  createdAt         DateTime @default(now())
  updatedAt         DateTime @updatedAt
  
  userId   String
  user     User      @relation(fields: [userId], references: [id])
  chapters Chapter[]
  context  StoryContext?
  
  @@map("stories")
}

model Chapter {
  id                  String   @id @default(cuid())
  chapterNumber       Int
  content             String
  aiPromptUsed        String?
  choicesOffered      Json     @default("[]")
  previousChapterId   String?
  createdAt           DateTime @default(now())
  
  storyId         String
  story           Story     @relation(fields: [storyId], references: [id])
  previousChapter Chapter?  @relation("ChapterSequence", fields: [previousChapterId], references: [id])
  nextChapters    Chapter[] @relation("ChapterSequence")
  choices         Choice[]
  
  @@map("chapters")
}

model Choice {
  id             String   @id @default(cuid())
  choiceText     String
  userInput      String?
  isCustom       Boolean  @default(false)
  nextChapterId  String?
  createdAt      DateTime @default(now())
  
  chapterId   String
  chapter     Chapter  @relation(fields: [chapterId], references: [id])
  nextChapter Chapter? @relation("ChoiceToChapter", fields: [nextChapterId], references: [id])
  
  @@map("choices")
}

model StoryContext {
  id                   String   @id @default(cuid())
  characterProfiles    Json     @default("{}")
  worldBuilding        Json     @default("{}")
  plotThreads          Json     @default("{}")
  userPreferences      Json     @default("{}")
  contextSummary       String?
  updatedAt            DateTime @updatedAt
  
  storyId String @unique
  story   Story  @relation(fields: [storyId], references: [id])
  
  @@map("story_contexts")
}
```

运行数据库迁移：
```bash
npx prisma migrate dev --name init
npx prisma generate
```

## 🎯 核心功能实现

### 1. AI服务集成 (10分钟)

创建 `src/lib/ai/openai.ts`：
```typescript
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export interface GenerationRequest {
  theme: string;
  protagonist: any;
  context: string;
  userChoice: string;
}

export async function generateChapter(request: GenerationRequest): Promise<string> {
  const prompt = buildPrompt(request);
  
  const completion = await openai.chat.completions.create({
    model: "gpt-4",
    messages: [
      {
        role: "system",
        content: "你是一个专业的小说作家，擅长创作引人入胜的互动小说。"
      },
      {
        role: "user",
        content: prompt
      }
    ],
    max_tokens: 1500,
    temperature: 0.8,
  });

  return completion.choices[0]?.message?.content || '';
}

function buildPrompt(request: GenerationRequest): string {
  return `
# 小说生成任务

## 故事背景
主题：${request.theme}
主人公：${JSON.stringify(request.protagonist)}

## 当前情况
${request.context}

## 用户选择
${request.userChoice}

## 要求
1. 生成800-1200字的章节内容
2. 保持故事连贯性
3. 体现用户选择的影响
4. 在结尾提供3个不同的选择选项
5. 选择选项要有明显的差异和后果

请生成下一章节内容：
`;
}
```

### 2. 故事生成API (5分钟)

创建 `src/app/api/chapters/generate/route.ts`：
```typescript
import { NextRequest, NextResponse } from 'next/server';
import { generateChapter } from '@/lib/ai/openai';
import { prisma } from '@/lib/database/prisma';

export async function POST(request: NextRequest) {
  try {
    const { storyId, userChoice, isCustomChoice } = await request.json();
    
    // 获取故事上下文
    const story = await prisma.story.findUnique({
      where: { id: storyId },
      include: {
        chapters: {
          orderBy: { chapterNumber: 'desc' },
          take: 3
        },
        context: true
      }
    });

    if (!story) {
      return NextResponse.json({ error: 'Story not found' }, { status: 404 });
    }

    // 构建生成请求
    const generationRequest = {
      theme: story.theme,
      protagonist: story.protagonistInfo,
      context: buildContext(story),
      userChoice
    };

    // 生成新章节
    const content = await generateChapter(generationRequest);
    
    // 解析内容和选择
    const { chapterContent, choices } = parseGeneratedContent(content);
    
    // 保存到数据库
    const newChapter = await prisma.chapter.create({
      data: {
        storyId,
        chapterNumber: story.chapters.length + 1,
        content: chapterContent,
        choicesOffered: choices,
        previousChapterId: story.chapters[0]?.id
      }
    });

    // 更新故事当前章节
    await prisma.story.update({
      where: { id: storyId },
      data: { currentChapterId: newChapter.id }
    });

    return NextResponse.json({
      chapter: newChapter,
      choices
    });

  } catch (error) {
    console.error('Chapter generation error:', error);
    return NextResponse.json(
      { error: 'Failed to generate chapter' },
      { status: 500 }
    );
  }
}

function buildContext(story: any): string {
  const recentChapters = story.chapters
    .slice(0, 3)
    .map(ch => ch.content)
    .join('\n\n');
    
  return `最近章节内容：\n${recentChapters}`;
}

function parseGeneratedContent(content: string) {
  // 简单的内容解析逻辑
  const parts = content.split('选择：');
  const chapterContent = parts[0].trim();
  
  const choicesText = parts[1] || '';
  const choices = choicesText
    .split('\n')
    .filter(line => line.trim())
    .slice(0, 3)
    .map((choice, index) => ({
      id: `choice_${index}`,
      text: choice.replace(/^\d+\.?\s*/, '').trim()
    }));

  return { chapterContent, choices };
}
```

### 3. 前端故事阅读器 (10分钟)

创建 `src/components/story/StoryReader.tsx`：
```typescript
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Textarea } from '@/components/ui/Textarea';

interface StoryReaderProps {
  storyId: string;
  currentChapter: any;
  onChoiceSelect: (choice: string, isCustom: boolean) => void;
}

export function StoryReader({ storyId, currentChapter, onChoiceSelect }: StoryReaderProps) {
  const [customInput, setCustomInput] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleChoiceClick = async (choice: string) => {
    setIsGenerating(true);
    await onChoiceSelect(choice, false);
    setIsGenerating(false);
  };

  const handleCustomSubmit = async () => {
    if (!customInput.trim()) return;
    
    setIsGenerating(true);
    await onChoiceSelect(customInput, true);
    setCustomInput('');
    setShowCustomInput(false);
    setIsGenerating(false);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* 章节内容 */}
      <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
        <div className="prose prose-lg max-w-none">
          <h2 className="text-2xl font-bold mb-4">
            第 {currentChapter.chapterNumber} 章
          </h2>
          <div className="whitespace-pre-wrap leading-relaxed">
            {currentChapter.content}
          </div>
        </div>
      </div>

      {/* 选择区域 */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-4">你的选择：</h3>
        
        {/* 预设选择 */}
        <div className="space-y-3 mb-4">
          {currentChapter.choicesOffered?.map((choice: any, index: number) => (
            <Button
              key={choice.id}
              variant="outline"
              className="w-full text-left p-4 h-auto"
              onClick={() => handleChoiceClick(choice.text)}
              disabled={isGenerating}
            >
              <span className="font-medium text-blue-600 mr-2">
                {index + 1}.
              </span>
              {choice.text}
            </Button>
          ))}
        </div>

        {/* 自定义输入 */}
        {!showCustomInput ? (
          <Button
            variant="ghost"
            onClick={() => setShowCustomInput(true)}
            disabled={isGenerating}
            className="w-full"
          >
            💭 我有其他想法...
          </Button>
        ) : (
          <div className="space-y-3">
            <Textarea
              value={customInput}
              onChange={(e) => setCustomInput(e.target.value)}
              placeholder="描述你想要的故事发展..."
              className="min-h-[100px]"
            />
            <div className="flex gap-2">
              <Button
                onClick={handleCustomSubmit}
                disabled={!customInput.trim() || isGenerating}
                className="flex-1"
              >
                提交我的选择
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  setShowCustomInput(false);
                  setCustomInput('');
                }}
                disabled={isGenerating}
              >
                取消
              </Button>
            </div>
          </div>
        )}

        {isGenerating && (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-2">AI正在创作下一章节...</p>
          </div>
        )}
      </div>
    </div>
  );
}
```

## 🎉 运行项目

```bash
# 启动开发服务器
npm run dev

# 访问应用
open http://localhost:3000
```

## 📚 下一步

1. **完善UI组件**: 参考 `docs/technical-design.md` 完善所有组件
2. **添加用户认证**: 集成 NextAuth.js
3. **优化AI提示词**: 根据不同主题优化提示词模板
4. **添加缓存**: 实现Redis缓存提升性能
5. **部署上线**: 使用Vercel部署到生产环境

## 🔗 相关文档

- [完整技术设计文档](./technical-design.md)
- [详细实施计划](./implementation-plan.md)
- [API接口文档](./api.md)

---

*快速开始指南版本: v1.0*  
*预计搭建时间: 30分钟*
