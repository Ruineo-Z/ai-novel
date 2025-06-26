<execution id="agent-development-workflow">
  <constraint>
    ## Agent开发的技术约束
    - **框架限制**：必须遵循CrewAI和LlamaIndex的API规范
    - **性能要求**：Agent响应时间不超过30秒，并发支持至少100个请求
    - **资源限制**：内存使用不超过8GB，CPU使用率保持在80%以下
    - **可靠性要求**：系统可用性达到99.9%，错误率低于0.1%
  </constraint>

  <rule>
    ## Agent开发强制规则
    - **角色定义清晰**：每个Agent必须有明确的角色定义和职责范围
    - **任务原子化**：Task必须是可独立执行的原子操作
    - **错误处理完整**：必须包含完整的异常处理和重试机制
    - **日志记录规范**：所有关键操作必须记录详细日志
    - **测试覆盖充分**：单元测试覆盖率不低于80%
  </rule>

  <guideline>
    ## Agent开发指导原则
    - **单一职责**：每个Agent专注于特定领域的任务
    - **松耦合设计**：Agent间通过标准接口通信，减少依赖
    - **可观测性**：提供充分的监控和调试信息
    - **可扩展性**：支持动态添加新的Agent和Task
    - **用户友好**：提供清晰的API文档和使用示例
  </guideline>

  <process>
    ## CrewAI Agent开发完整流程
    
    ### Phase 1: 需求分析与设计 (1-2天)
    
    #### 1.1 业务需求分析
    ```python
    # 需求分析模板
    class AgentRequirement:
        def __init__(self):
            self.business_goal = ""  # 业务目标
            self.user_scenarios = []  # 用户场景
            self.success_criteria = []  # 成功标准
            self.constraints = []  # 约束条件
    ```
    
    #### 1.2 Agent架构设计
    ```python
    from crewai import Agent, Task, Crew
    from typing import List, Dict, Any
    
    class AgentArchitecture:
        def __init__(self):
            self.agents: List[Agent] = []
            self.tasks: List[Task] = []
            self.workflows: Dict[str, Any] = {}
            self.dependencies: Dict[str, List[str]] = {}
    ```
    
    #### 1.3 数据流设计
    ```python
    # 数据流定义
    class DataFlow:
        def __init__(self):
            self.input_schema = {}  # 输入数据结构
            self.output_schema = {}  # 输出数据结构
            self.intermediate_data = {}  # 中间数据结构
            self.data_validation = {}  # 数据验证规则
    ```
    
    ### Phase 2: Agent实现 (3-5天)
    
    #### 2.1 基础Agent创建
    ```python
    from crewai import Agent
    from langchain.llms import OpenAI
    
    def create_base_agent(role: str, goal: str, backstory: str) -> Agent:
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            allow_delegation=False,
            llm=OpenAI(temperature=0.1)
        )
    
    # 示例：数据分析Agent
    data_analyst = create_base_agent(
        role="Senior Data Analyst",
        goal="Analyze data and provide actionable insights",
        backstory="Expert in statistical analysis and data visualization"
    )
    ```
    
    #### 2.2 专业化Agent开发
    ```python
    class SpecializedAgent:
        def __init__(self, agent_type: str):
            self.agent_type = agent_type
            self.tools = self._load_tools()
            self.memory = self._setup_memory()
            self.agent = self._create_agent()
        
        def _load_tools(self) -> List:
            # 根据Agent类型加载相应工具
            tool_mapping = {
                "researcher": ["search_tool", "web_scraper"],
                "writer": ["text_editor", "grammar_checker"],
                "analyst": ["data_processor", "chart_generator"]
            }
            return tool_mapping.get(self.agent_type, [])
        
        def _setup_memory(self):
            # 设置Agent记忆系统
            from crewai.memory import LongTermMemory
            return LongTermMemory()
        
        def _create_agent(self) -> Agent:
            return Agent(
                role=f"Specialized {self.agent_type.title()}",
                goal=f"Execute {self.agent_type} tasks efficiently",
                backstory=f"Expert {self.agent_type} with years of experience",
                tools=self.tools,
                memory=self.memory,
                verbose=True
            )
    ```
    
    #### 2.3 Task定义与实现
    ```python
    from crewai import Task
    
    class TaskBuilder:
        @staticmethod
        def create_research_task(topic: str, agent: Agent) -> Task:
            return Task(
                description=f"Research comprehensive information about {topic}",
                agent=agent,
                expected_output="Detailed research report with sources"
            )
        
        @staticmethod
        def create_analysis_task(data: str, agent: Agent) -> Task:
            return Task(
                description=f"Analyze the provided data: {data}",
                agent=agent,
                expected_output="Analysis report with insights and recommendations"
            )
        
        @staticmethod
        def create_writing_task(content: str, agent: Agent) -> Task:
            return Task(
                description=f"Write high-quality content based on: {content}",
                agent=agent,
                expected_output="Well-structured, engaging written content"
            )
    ```
    
    ### Phase 3: Crew组装与协调 (2-3天)
    
    #### 3.1 Crew创建
    ```python
    from crewai import Crew, Process
    
    class CrewManager:
        def __init__(self):
            self.agents = []
            self.tasks = []
            self.crew = None
        
        def add_agent(self, agent: Agent):
            self.agents.append(agent)
        
        def add_task(self, task: Task):
            self.tasks.append(task)
        
        def create_crew(self, process_type: Process = Process.sequential):
            self.crew = Crew(
                agents=self.agents,
                tasks=self.tasks,
                process=process_type,
                verbose=2
            )
            return self.crew
        
        def execute(self, inputs: Dict[str, Any] = None):
            if not self.crew:
                raise ValueError("Crew not created. Call create_crew() first.")
            return self.crew.kickoff(inputs=inputs)
    ```
    
    #### 3.2 工作流程编排
    ```python
    class WorkflowOrchestrator:
        def __init__(self):
            self.workflows = {}
        
        def define_sequential_workflow(self, name: str, tasks: List[Task]):
            self.workflows[name] = {
                "type": "sequential",
                "tasks": tasks,
                "process": Process.sequential
            }
        
        def define_parallel_workflow(self, name: str, tasks: List[Task]):
            self.workflows[name] = {
                "type": "parallel",
                "tasks": tasks,
                "process": Process.hierarchical
            }
        
        def execute_workflow(self, name: str, inputs: Dict[str, Any]):
            workflow = self.workflows.get(name)
            if not workflow:
                raise ValueError(f"Workflow {name} not found")
            
            crew = Crew(
                agents=[task.agent for task in workflow["tasks"]],
                tasks=workflow["tasks"],
                process=workflow["process"]
            )
            return crew.kickoff(inputs=inputs)
    ```
    
    ### Phase 4: LlamaIndex集成 (2-3天)
    
    #### 4.1 知识库构建
    ```python
    from llama_index import VectorStoreIndex, SimpleDirectoryReader
    from llama_index.storage.storage_context import StorageContext
    from llama_index.vector_stores import ChromaVectorStore
    
    class KnowledgeBaseManager:
        def __init__(self, persist_dir: str = "./storage"):
            self.persist_dir = persist_dir
            self.index = None
            self.query_engine = None
        
        def build_index_from_documents(self, doc_path: str):
            # 加载文档
            documents = SimpleDirectoryReader(doc_path).load_data()
            
            # 创建向量存储
            vector_store = ChromaVectorStore()
            storage_context = StorageContext.from_defaults(
                vector_store=vector_store
            )
            
            # 构建索引
            self.index = VectorStoreIndex.from_documents(
                documents,
                storage_context=storage_context
            )
            
            # 创建查询引擎
            self.query_engine = self.index.as_query_engine()
            
            return self.index
        
        def query_knowledge_base(self, query: str):
            if not self.query_engine:
                raise ValueError("Query engine not initialized")
            return self.query_engine.query(query)
    ```
    
    #### 4.2 Agent与知识库集成
    ```python
    class KnowledgeEnhancedAgent:
        def __init__(self, base_agent: Agent, knowledge_base: KnowledgeBaseManager):
            self.base_agent = base_agent
            self.knowledge_base = knowledge_base
        
        def enhanced_query(self, query: str):
            # 先从知识库检索相关信息
            knowledge_result = self.knowledge_base.query_knowledge_base(query)
            
            # 将知识库结果作为上下文传递给Agent
            enhanced_query = f"""
            Context from knowledge base: {knowledge_result}
            
            User query: {query}
            
            Please provide a comprehensive answer based on the context and your expertise.
            """
            
            # 使用Agent处理增强后的查询
            task = Task(
                description=enhanced_query,
                agent=self.base_agent,
                expected_output="Comprehensive answer with knowledge base context"
            )
            
            crew = Crew(agents=[self.base_agent], tasks=[task])
            return crew.kickoff()
    ```
    
    ### Phase 5: 测试与优化 (2-3天)
    
    #### 5.1 单元测试
    ```python
    import unittest
    from unittest.mock import Mock, patch
    
    class TestAgentDevelopment(unittest.TestCase):
        def setUp(self):
            self.agent = create_base_agent(
                "Test Agent", "Test Goal", "Test Backstory"
            )
        
        def test_agent_creation(self):
            self.assertIsNotNone(self.agent)
            self.assertEqual(self.agent.role, "Test Agent")
        
        def test_task_execution(self):
            task = Task(
                description="Test task",
                agent=self.agent,
                expected_output="Test output"
            )
            # Mock the execution
            with patch.object(task, 'execute') as mock_execute:
                mock_execute.return_value = "Test result"
                result = task.execute()
                self.assertEqual(result, "Test result")
        
        def test_crew_execution(self):
            task = Task(
                description="Test crew task",
                agent=self.agent,
                expected_output="Crew test output"
            )
            crew = Crew(agents=[self.agent], tasks=[task])
            # Test crew execution logic
            self.assertIsNotNone(crew)
    ```
    
    #### 5.2 性能测试
    ```python
    import time
    import concurrent.futures
    
    class PerformanceTest:
        def __init__(self, crew: Crew):
            self.crew = crew
        
        def test_response_time(self, inputs: Dict[str, Any]):
            start_time = time.time()
            result = self.crew.kickoff(inputs=inputs)
            end_time = time.time()
            
            response_time = end_time - start_time
            print(f"Response time: {response_time:.2f} seconds")
            return response_time, result
        
        def test_concurrent_execution(self, inputs_list: List[Dict[str, Any]]):
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for inputs in inputs_list:
                    future = executor.submit(self.crew.kickoff, inputs=inputs)
                    futures.append(future)
                
                results = []
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result(timeout=60)
                        results.append(result)
                    except Exception as e:
                        print(f"Error in concurrent execution: {e}")
                
                return results
    ```
    
    ### Phase 6: 部署与监控 (1-2天)
    
    #### 6.1 容器化部署
    ```dockerfile
    # Dockerfile
    FROM python:3.9-slim
    
    WORKDIR /app
    
    COPY requirements.txt .
    RUN pip install -r requirements.txt
    
    COPY . .
    
    EXPOSE 8000
    
    CMD ["python", "main.py"]
    ```
    
    #### 6.2 监控与日志
    ```python
    import logging
    from prometheus_client import Counter, Histogram, start_http_server
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Prometheus指标
    REQUEST_COUNT = Counter('agent_requests_total', 'Total agent requests')
    REQUEST_DURATION = Histogram('agent_request_duration_seconds', 'Agent request duration')
    
    class MonitoredCrew:
        def __init__(self, crew: Crew):
            self.crew = crew
        
        def execute_with_monitoring(self, inputs: Dict[str, Any]):
            REQUEST_COUNT.inc()
            
            with REQUEST_DURATION.time():
                try:
                    logger.info(f"Starting crew execution with inputs: {inputs}")
                    result = self.crew.kickoff(inputs=inputs)
                    logger.info(f"Crew execution completed successfully")
                    return result
                except Exception as e:
                    logger.error(f"Crew execution failed: {e}")
                    raise
    ```
  </process>

  <criteria>
    ## 开发质量标准
    
    ### 代码质量
    - ✅ 代码覆盖率 ≥ 80%
    - ✅ 代码复杂度 ≤ 10
    - ✅ 无严重安全漏洞
    - ✅ 符合PEP8编码规范
    
    ### 性能标准
    - ✅ 平均响应时间 ≤ 30秒
    - ✅ 并发处理能力 ≥ 100 QPS
    - ✅ 内存使用 ≤ 8GB
    - ✅ CPU使用率 ≤ 80%
    
    ### 可靠性标准
    - ✅ 系统可用性 ≥ 99.9%
    - ✅ 错误率 ≤ 0.1%
    - ✅ 故障恢复时间 ≤ 5分钟
    - ✅ 数据一致性保证
    
    ### 可维护性标准
    - ✅ 文档完整性 ≥ 90%
    - ✅ API文档自动生成
    - ✅ 日志记录完整
    - ✅ 监控指标齐全
  </criteria>
</execution>