<execution>
  <constraint>
    ## AI互动小说项目约束
    - **技术栈限制**：必须使用Python + FastAPI + LlamaIndex + ChromaDB
    - **AI服务约束**：Gemini Pro作为主要生成服务，Jina AI作为embedding服务
    - **成本控制**：优先使用免费额度，月运营成本控制在$100以内
    - **部署要求**：支持本地开发和云端部署，ChromaDB本地持久化
    - **性能要求**：API响应时间<2秒，AI生成时间<10秒
  </constraint>

  <rule>
    ## 开发强制规则
    - **代码规范**：严格遵循PEP 8，使用type hints
    - **异步优先**：所有AI服务调用必须使用async/await
    - **错误处理**：每个AI调用必须有完整的异常处理和降级策略
    - **测试覆盖**：核心功能测试覆盖率必须>80%
    - **文档同步**：API变更必须同步更新FastAPI文档
    - **依赖管理**：使用requirements.txt，禁止手动编辑package文件
  </rule>

  <guideline>
    ## 开发指导原则
    - **AI优先设计**：将AI能力作为核心功能设计，而非附加功能
    - **模块化架构**：清晰的服务分层，便于测试和维护
    - **性能优化**：充分利用异步特性，优化AI服务调用
    - **用户体验**：AI生成过程的友好提示和错误处理
    - **可观测性**：完善的日志记录和性能监控
  </guideline>

  <process>
    ## AI互动小说开发标准流程
    
    ### Step 1: 环境搭建和基础配置 (1-2天)
    
    ```mermaid
    flowchart TD
        A[创建虚拟环境] --> B[安装依赖包]
        B --> C[配置环境变量]
        C --> D[初始化数据库]
        D --> E[测试基础连接]
    ```
    
    **关键任务**：
    - 创建Python虚拟环境
    - 安装LlamaIndex生态依赖
    - 配置Gemini和Jina AI密钥
    - 初始化PostgreSQL和ChromaDB
    - 验证所有服务连接正常
    
    ### Step 2: 数据模型和API基础 (2-3天)
    
    ```mermaid
    flowchart LR
        A[SQLAlchemy模型] --> B[Pydantic Schema]
        B --> C[FastAPI路由]
        C --> D[依赖注入]
        D --> E[基础CRUD]
    ```
    
    **数据模型设计**：
    ```python
    # 核心模型关系
    User 1:N Story 1:N Chapter 1:N Choice
    Story 1:1 StoryContext
    ```
    
    **API设计原则**：
    - RESTful风格的URL设计
    - 统一的响应格式
    - 完整的错误处理
    - 自动生成的API文档
    
    ### Step 3: LlamaIndex AI服务集成 (3-4天)
    
    ```mermaid
    flowchart TD
        A[LlamaIndex配置] --> B[Gemini LLM集成]
        B --> C[Jina Embedding集成]
        C --> D[ChromaDB向量存储]
        D --> E[AI服务封装]
        E --> F[错误处理和重试]
    ```
    
    **LlamaIndex配置示例**：
    ```python
    from llama_index.core import Settings
    from llama_index.llms.gemini import Gemini
    from llama_index.embeddings.jinaai import JinaEmbedding
    
    # 全局配置
    Settings.llm = Gemini(api_key=settings.GOOGLE_API_KEY)
    Settings.embed_model = JinaEmbedding(api_key=settings.JINA_API_KEY)
    ```
    
    **关键实现**：
    - AI服务的异步封装
    - 向量存储的CRUD操作
    - 智能记忆检索算法
    - 提示词模板管理
    
    ### Step 4: 业务逻辑开发 (1周)
    
    ```mermaid
    flowchart LR
        A[故事创建] --> B[主人公生成]
        B --> C[章节生成]
        C --> D[选择处理]
        D --> E[上下文更新]
    ```
    
    **核心业务流程**：
    1. **故事初始化**：主题选择 + 主人公设定
    2. **章节生成**：基于上下文和用户选择生成内容
    3. **记忆管理**：存储和检索故事记忆
    4. **选择处理**：3选项 + 自由输入的处理逻辑
    
    **关键服务类**：
    ```python
    class StoryService:
        async def create_story(self, story_data: StoryCreate) -> Story
        async def generate_chapter(self, story_id: str, user_choice: str) -> Chapter
        async def update_context(self, story_id: str, chapter: Chapter)
    
    class AIService:
        async def generate_content(self, prompt: str) -> str
        async def generate_protagonist(self, theme: str) -> dict
        async def suggest_choices(self, context: dict) -> List[dict]
    
    class VectorService:
        async def store_memory(self, story_id: str, content: str)
        async def search_memories(self, story_id: str, query: str) -> List[dict]
    ```
    
    ### Step 5: 测试和优化 (3-5天)
    
    ```mermaid
    flowchart TD
        A[单元测试] --> B[集成测试]
        B --> C[性能测试]
        C --> D[AI质量测试]
        D --> E[用户体验测试]
    ```
    
    **测试策略**：
    - **单元测试**：pytest + httpx异步测试
    - **AI服务测试**：Mock AI响应的测试
    - **性能测试**：并发用户的压力测试
    - **集成测试**：完整业务流程的端到端测试
    
    ### Step 6: 部署和监控 (2-3天)
    
    ```mermaid
    flowchart LR
        A[Docker容器化] --> B[环境配置]
        B --> C[数据库迁移]
        C --> D[服务部署]
        D --> E[监控设置]
    ```
    
    **部署清单**：
    - Docker镜像构建和优化
    - 环境变量和密钥管理
    - 数据库迁移和初始化
    - 负载均衡和反向代理
    - 日志收集和性能监控
    
    ## 质量保证流程
    
    ### 代码质量检查
    ```bash
    # 代码格式化
    black app/
    isort app/
    
    # 类型检查
    mypy app/
    
    # 代码质量
    flake8 app/
    pylint app/
    ```
    
    ### AI服务质量监控
    ```python
    # 关键指标监控
    - AI响应时间
    - Token使用量
    - 错误率统计
    - 用户满意度
    ```
  </process>

  <criteria>
    ## 开发质量评价标准
    
    ### 功能完整性标准
    - ✅ 支持4种主题故事生成
    - ✅ 主人公自定义和AI生成
    - ✅ 3选项 + 自由输入交互
    - ✅ 智能上下文管理
    - ✅ 故事记忆检索
    
    ### 技术质量标准
    - ✅ 代码覆盖率 > 80%
    - ✅ API响应时间 < 2秒
    - ✅ AI生成时间 < 10秒
    - ✅ 并发支持 > 50用户
    - ✅ 错误率 < 1%
    
    ### AI服务质量标准
    - ✅ 内容生成质量评分 > 4.0/5.0
    - ✅ 故事连贯性保持
    - ✅ 角色一致性维护
    - ✅ 用户选择影响体现
    
    ### 开发效率标准
    - ✅ 新功能开发周期 < 1周
    - ✅ Bug修复时间 < 1天
    - ✅ 部署流程自动化
    - ✅ 文档完整且同步
    
    ### 成本控制标准
    - ✅ 月度AI服务成本 < $50
    - ✅ 服务器成本 < $30
    - ✅ 存储成本 < $20
    - ✅ 总运营成本 < $100
  </criteria>
</execution>
