"""
记忆管理服务 - 负责故事上下文记忆的存储和检索
"""
import time
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

import chromadb
from chromadb.config import Settings

from app.services.ai.base import BaseAIService, AIServiceError, AIRequest, AIResponse
from app.core.config import settings


@dataclass
class MemoryItem:
    """记忆项数据结构"""
    id: str
    content: str
    memory_type: str  # character, plot, setting, choice, emotion
    importance: float  # 0.0-1.0
    timestamp: datetime
    story_id: str
    chapter_id: Optional[str] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "timestamp": self.timestamp.isoformat(),
            "story_id": self.story_id,
            "chapter_id": self.chapter_id,
            "tags": self.tags,
            "metadata": self.metadata
        }


@dataclass
class MemoryQuery:
    """记忆查询请求"""
    story_id: str
    query_text: str
    memory_types: Optional[List[str]] = None
    min_importance: float = 0.0
    max_results: int = 10
    include_metadata: bool = True


@dataclass
class MemorySearchResult:
    """记忆搜索结果"""
    memory_item: MemoryItem
    similarity_score: float
    relevance_explanation: str


class MemoryManagerService(BaseAIService):
    """记忆管理服务"""
    
    def __init__(self):
        super().__init__()
        self._setup_chroma_client()
        self.logger.info("记忆管理服务初始化完成")
    
    def _setup_chroma_client(self):
        """设置ChromaDB客户端"""
        try:
            # 首先尝试HTTP客户端
            self.chroma_client = chromadb.HttpClient(
                host=settings.CHROMA_HOST,
                port=settings.CHROMA_PORT
            )

            # 测试连接
            self.chroma_client.heartbeat()

            # 获取或创建集合
            self.collection = self.chroma_client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"description": "AI互动小说故事记忆存储"}
            )

            self.logger.info(f"ChromaDB HTTP客户端初始化成功: {settings.CHROMA_COLLECTION_NAME}")

        except Exception as e:
            self.logger.warning(f"ChromaDB HTTP客户端初始化失败: {e}")

            # 尝试使用PersistentClient作为备选方案
            try:
                self.logger.info("尝试使用PersistentClient...")
                self.chroma_client = chromadb.PersistentClient(
                    path=settings.CHROMA_PERSIST_DIR
                )

                # 获取或创建集合
                self.collection = self.chroma_client.get_or_create_collection(
                    name=settings.CHROMA_COLLECTION_NAME,
                    metadata={"description": "AI互动小说故事记忆存储"}
                )

                self.logger.info(f"ChromaDB PersistentClient初始化成功: {settings.CHROMA_COLLECTION_NAME}")

            except Exception as e2:
                self.logger.error(f"ChromaDB PersistentClient也初始化失败: {e2}")
                self.chroma_client = None
                self.collection = None
    
    async def store_memory(self, memory_item: MemoryItem) -> bool:
        """存储记忆"""
        if not self.collection:
            raise AIServiceError("ChromaDB未初始化")
        
        try:
            # 生成向量
            embeddings = await self._get_embeddings([memory_item.content])
            if not embeddings:
                raise AIServiceError("向量生成失败")
            
            # 存储到ChromaDB
            self.collection.add(
                ids=[memory_item.id],
                embeddings=embeddings,
                documents=[memory_item.content],
                metadatas=[{
                    "memory_type": memory_item.memory_type,
                    "importance": memory_item.importance,
                    "timestamp": memory_item.timestamp.isoformat(),
                    "story_id": memory_item.story_id,
                    "chapter_id": memory_item.chapter_id or "",
                    "tags": json.dumps(memory_item.tags),
                    "metadata": json.dumps(memory_item.metadata)
                }]
            )
            
            self.logger.debug(f"记忆存储成功: {memory_item.id}")
            return True
            
        except Exception as e:
            self.logger.error(f"记忆存储失败: {e}")
            return False
    
    async def search_memories(self, query: MemoryQuery) -> List[MemorySearchResult]:
        """搜索记忆"""
        if not self.collection:
            raise AIServiceError("ChromaDB未初始化")
        
        try:
            # 生成查询向量
            query_embeddings = await self._get_embeddings([query.query_text])
            if not query_embeddings:
                raise AIServiceError("查询向量生成失败")
            
            # 构建过滤条件
            where_conditions = {"story_id": query.story_id}
            if query.memory_types:
                where_conditions["memory_type"] = {"$in": query.memory_types}
            if query.min_importance > 0:
                where_conditions["importance"] = {"$gte": query.min_importance}
            
            # 执行搜索
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=query.max_results,
                where=where_conditions,
                include=["documents", "metadatas", "distances"]
            )
            
            # 解析结果
            search_results = []
            if results["ids"] and results["ids"][0]:
                for i, memory_id in enumerate(results["ids"][0]):
                    metadata = results["metadatas"][0][i]
                    document = results["documents"][0][i]
                    distance = results["distances"][0][i]
                    
                    # 重构记忆项
                    memory_item = MemoryItem(
                        id=memory_id,
                        content=document,
                        memory_type=metadata["memory_type"],
                        importance=metadata["importance"],
                        timestamp=datetime.fromisoformat(metadata["timestamp"]),
                        story_id=metadata["story_id"],
                        chapter_id=metadata["chapter_id"] if metadata["chapter_id"] else None,
                        tags=json.loads(metadata.get("tags", "[]")),
                        metadata=json.loads(metadata.get("metadata", "{}"))
                    )
                    
                    # 计算相似度分数（距离转换为相似度）
                    similarity_score = max(0, 1 - distance)
                    
                    # 生成相关性解释
                    relevance_explanation = await self._generate_relevance_explanation(
                        query.query_text, document, similarity_score
                    )
                    
                    search_result = MemorySearchResult(
                        memory_item=memory_item,
                        similarity_score=similarity_score,
                        relevance_explanation=relevance_explanation
                    )
                    search_results.append(search_result)
            
            self.logger.debug(f"记忆搜索完成，找到{len(search_results)}条结果")
            return search_results
            
        except Exception as e:
            self.logger.error(f"记忆搜索失败: {e}")
            return []
    
    async def _generate_relevance_explanation(self, query: str, content: str, score: float) -> str:
        """生成相关性解释"""
        try:
            if score > 0.8:
                return "高度相关：内容与查询高度匹配"
            elif score > 0.6:
                return "中度相关：内容与查询部分匹配"
            elif score > 0.4:
                return "低度相关：内容与查询有一定关联"
            else:
                return "弱相关：内容与查询关联较弱"
        except:
            return "相关性未知"
    
    async def extract_memories_from_chapter(self, chapter_content: str, story_id: str, chapter_id: str) -> List[MemoryItem]:
        """从章节内容中提取记忆"""
        prompt = f"""
请从以下章节内容中提取重要的记忆信息，用于后续故事生成的参考。

章节内容：
{chapter_content}

请提取以下类型的记忆：
1. **角色信息** (character): 角色的外貌、性格、技能、关系等
2. **情节要点** (plot): 重要的事件、转折点、冲突等
3. **环境设定** (setting): 地点、时间、环境描述等
4. **选择结果** (choice): 用户选择及其后果
5. **情感状态** (emotion): 角色的情感变化、氛围等

输出格式：
```json
{{
    "memories": [
        {{
            "content": "记忆内容描述",
            "memory_type": "character/plot/setting/choice/emotion",
            "importance": 0.8,
            "tags": ["标签1", "标签2"],
            "metadata": {{"additional_info": "额外信息"}}
        }}
    ]
}}
```

请开始提取：
"""
        
        try:
            response = await self._call_gemini(prompt, max_tokens=1000, temperature=0.3)
            
            # 解析提取的记忆
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
                memories = parsed.get("memories", [])
                
                memory_items = []
                for memory_data in memories:
                    memory_item = MemoryItem(
                        id=str(uuid.uuid4()),
                        content=memory_data.get("content", ""),
                        memory_type=memory_data.get("memory_type", "plot"),
                        importance=memory_data.get("importance", 0.5),
                        timestamp=datetime.now(),
                        story_id=story_id,
                        chapter_id=chapter_id,
                        tags=memory_data.get("tags", []),
                        metadata=memory_data.get("metadata", {})
                    )
                    memory_items.append(memory_item)
                
                return memory_items
            
            return []
            
        except Exception as e:
            self.logger.error(f"记忆提取失败: {e}")
            return []
    
    async def get_story_context(self, story_id: str, max_memories: int = 20) -> Dict[str, Any]:
        """获取故事上下文"""
        try:
            # 搜索所有相关记忆
            query = MemoryQuery(
                story_id=story_id,
                query_text="故事上下文",
                max_results=max_memories
            )
            
            memories = await self.search_memories(query)
            
            # 按类型分组
            context = {
                "characters": [],
                "plot_points": [],
                "settings": [],
                "choices": [],
                "emotions": [],
                "summary": ""
            }
            
            for result in memories:
                memory = result.memory_item
                memory_type = memory.memory_type
                
                if memory_type == "character":
                    context["characters"].append(memory.content)
                elif memory_type == "plot":
                    context["plot_points"].append(memory.content)
                elif memory_type == "setting":
                    context["settings"].append(memory.content)
                elif memory_type == "choice":
                    context["choices"].append(memory.content)
                elif memory_type == "emotion":
                    context["emotions"].append(memory.content)
            
            # 生成上下文摘要
            context["summary"] = await self._generate_context_summary(memories)
            
            return context
            
        except Exception as e:
            self.logger.error(f"获取故事上下文失败: {e}")
            return {}
    
    async def _generate_context_summary(self, memories: List[MemorySearchResult]) -> str:
        """生成上下文摘要"""
        if not memories:
            return "暂无故事上下文"
        
        try:
            memory_contents = [result.memory_item.content for result in memories[:10]]  # 只用前10个
            combined_content = "\n".join(memory_contents)
            
            prompt = f"""
请为以下故事记忆生成一个简洁的上下文摘要（200字以内）：

{combined_content}

要求：
1. 概括主要角色和关系
2. 总结关键情节发展
3. 描述当前故事状态
4. 保持简洁明了

摘要：
"""
            
            summary = await self._call_gemini(prompt, max_tokens=300, temperature=0.3)
            return summary.strip()
            
        except Exception as e:
            self.logger.error(f"生成上下文摘要失败: {e}")
            return "上下文摘要生成失败"
    
    async def cleanup_old_memories(self, story_id: str, keep_count: int = 100) -> int:
        """清理旧记忆，保留最重要的记忆"""
        try:
            # 获取所有记忆
            query = MemoryQuery(
                story_id=story_id,
                query_text="",
                max_results=1000
            )
            
            memories = await self.search_memories(query)
            
            if len(memories) <= keep_count:
                return 0
            
            # 按重要性和时间排序
            memories.sort(key=lambda x: (x.memory_item.importance, x.memory_item.timestamp), reverse=True)
            
            # 删除多余的记忆
            to_delete = memories[keep_count:]
            deleted_count = 0
            
            for result in to_delete:
                try:
                    self.collection.delete(ids=[result.memory_item.id])
                    deleted_count += 1
                except Exception as e:
                    self.logger.error(f"删除记忆失败: {e}")
            
            self.logger.info(f"清理了{deleted_count}条旧记忆")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"记忆清理失败: {e}")
            return 0

    async def process(self, request: AIRequest) -> AIResponse:
        """处理AI请求 - 记忆管理服务的实现"""
        # 记忆管理服务不直接处理AI请求，这里提供一个基础实现
        raise NotImplementedError("记忆管理服务不支持通用AI请求处理")
