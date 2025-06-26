<execution id="database-optimization">
  <constraint>
    ## 数据库优化的技术约束
    - **性能目标**：查询响应时间不超过100ms，吞吐量达到10000 QPS
    - **资源限制**：数据库服务器内存使用不超过80%，CPU使用率保持在70%以下
    - **可用性要求**：数据库可用性达到99.99%，故障恢复时间不超过30秒
    - **数据一致性**：ACID特性保证，分布式环境下保证最终一致性
  </constraint>

  <rule>
    ## 数据库优化强制规则
    - **索引策略**：所有查询字段必须有适当的索引，复合索引顺序必须优化
    - **查询规范**：禁止全表扫描，所有查询必须使用索引
    - **连接管理**：必须使用连接池，连接数不超过数据库最大连接数的80%
    - **事务控制**：事务必须尽可能短，避免长事务锁定资源
    - **监控告警**：必须设置完整的性能监控和告警机制
  </rule>

  <guideline>
    ## 数据库优化指导原则
    - **读写分离**：读操作和写操作分离，提高并发性能
    - **分库分表**：根据业务特点进行水平和垂直分割
    - **缓存策略**：合理使用多级缓存减少数据库压力
    - **批量操作**：优先使用批量操作减少网络开销
    - **定期维护**：定期进行数据库维护和性能调优
  </guideline>

  <process>
    ## 数据库优化完整流程
    
    ### Phase 1: 性能评估与分析 (1-2天)
    
    #### 1.1 基线性能测试
    ```python
    import time
    import psycopg2
    from contextlib import contextmanager
    import statistics
    
    class DatabasePerformanceAnalyzer:
        def __init__(self, connection_params):
            self.connection_params = connection_params
            self.metrics = []
        
        @contextmanager
        def get_connection(self):
            conn = psycopg2.connect(**self.connection_params)
            try:
                yield conn
            finally:
                conn.close()
        
        def measure_query_performance(self, query: str, params=None, iterations=100):
            execution_times = []
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for _ in range(iterations):
                    start_time = time.time()
                    cursor.execute(query, params)
                    cursor.fetchall()
                    end_time = time.time()
                    execution_times.append(end_time - start_time)
            
            metrics = {
                'query': query,
                'avg_time': statistics.mean(execution_times),
                'median_time': statistics.median(execution_times),
                'min_time': min(execution_times),
                'max_time': max(execution_times),
                'std_dev': statistics.stdev(execution_times)
            }
            
            self.metrics.append(metrics)
            return metrics
        
        def analyze_slow_queries(self):
            # 分析慢查询日志
            slow_queries = []
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT query, mean_time, calls, total_time
                    FROM pg_stat_statements
                    WHERE mean_time > 100  -- 超过100ms的查询
                    ORDER BY mean_time DESC
                    LIMIT 20
                """)
                slow_queries = cursor.fetchall()
            
            return slow_queries
    ```
    
    #### 1.2 索引分析
    ```python
    class IndexAnalyzer:
        def __init__(self, connection_params):
            self.connection_params = connection_params
        
        def analyze_missing_indexes(self):
            with psycopg2.connect(**self.connection_params) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT schemaname, tablename, attname, n_distinct, correlation
                    FROM pg_stats
                    WHERE schemaname = 'public'
                    AND n_distinct > 100  -- 高基数列
                    AND correlation < 0.1  -- 低相关性
                """)
                return cursor.fetchall()
        
        def analyze_unused_indexes(self):
            with psycopg2.connect(**self.connection_params) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
                    FROM pg_stat_user_indexes
                    WHERE idx_tup_read = 0 AND idx_tup_fetch = 0
                """)
                return cursor.fetchall()
        
        def suggest_composite_indexes(self):
            # 基于查询模式建议复合索引
            suggestions = []
            with psycopg2.connect(**self.connection_params) as conn:
                cursor = conn.cursor()
                # 分析WHERE子句中经常一起出现的列
                cursor.execute("""
                    SELECT query, calls
                    FROM pg_stat_statements
                    WHERE query LIKE '%WHERE%'
                    ORDER BY calls DESC
                    LIMIT 50
                """)
                queries = cursor.fetchall()
            
            # 解析查询模式并建议索引
            for query, calls in queries:
                # 简化的模式匹配，实际应用中需要更复杂的解析
                if 'AND' in query:
                    suggestions.append({
                        'query': query,
                        'calls': calls,
                        'suggestion': 'Consider composite index on frequently joined columns'
                    })
            
            return suggestions
    ```
    
    ### Phase 2: 关系型数据库优化 (3-5天)
    
    #### 2.1 PostgreSQL优化
    ```python
    class PostgreSQLOptimizer:
        def __init__(self, connection_params):
            self.connection_params = connection_params
        
        def optimize_configuration(self):
            # 优化PostgreSQL配置参数
            optimizations = {
                'shared_buffers': '256MB',  # 共享缓冲区
                'effective_cache_size': '1GB',  # 有效缓存大小
                'work_mem': '4MB',  # 工作内存
                'maintenance_work_mem': '64MB',  # 维护工作内存
                'checkpoint_completion_target': '0.9',  # 检查点完成目标
                'wal_buffers': '16MB',  # WAL缓冲区
                'default_statistics_target': '100'  # 统计信息目标
            }
            
            with psycopg2.connect(**self.connection_params) as conn:
                cursor = conn.cursor()
                for param, value in optimizations.items():
                    try:
                        cursor.execute(f"ALTER SYSTEM SET {param} = '{value}'")
                        print(f"Set {param} = {value}")
                    except Exception as e:
                        print(f"Failed to set {param}: {e}")
                
                cursor.execute("SELECT pg_reload_conf()")
                conn.commit()
        
        def create_optimized_indexes(self, table_name: str, columns: list):
            # 创建优化的索引
            with psycopg2.connect(**self.connection_params) as conn:
                cursor = conn.cursor()
                
                # 创建复合索引
                if len(columns) > 1:
                    index_name = f"idx_{table_name}_{'_'.join(columns)}"
                    columns_str = ', '.join(columns)
                    cursor.execute(f"""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name}
                        ON {table_name} ({columns_str})
                    """)
                
                # 创建部分索引（针对常见查询条件）
                for column in columns:
                    partial_index_name = f"idx_{table_name}_{column}_active"
                    cursor.execute(f"""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS {partial_index_name}
                        ON {table_name} ({column})
                        WHERE status = 'active'
                    """)
                
                conn.commit()
        
        def setup_partitioning(self, table_name: str, partition_column: str):
            # 设置表分区
            with psycopg2.connect(**self.connection_params) as conn:
                cursor = conn.cursor()
                
                # 创建分区表
                cursor.execute(f"""
                    CREATE TABLE {table_name}_partitioned (
                        LIKE {table_name} INCLUDING ALL
                    ) PARTITION BY RANGE ({partition_column})
                """)
                
                # 创建分区
                import datetime
                current_year = datetime.datetime.now().year
                for year in range(current_year - 2, current_year + 2):
                    partition_name = f"{table_name}_y{year}"
                    cursor.execute(f"""
                        CREATE TABLE {partition_name}
                        PARTITION OF {table_name}_partitioned
                        FOR VALUES FROM ('{year}-01-01') TO ('{year + 1}-01-01')
                    """)
                
                conn.commit()
    ```
    
    #### 2.2 MySQL优化
    ```python
    import mysql.connector
    
    class MySQLOptimizer:
        def __init__(self, connection_params):
            self.connection_params = connection_params
        
        def optimize_innodb_settings(self):
            # 优化InnoDB设置
            optimizations = {
                'innodb_buffer_pool_size': '1G',
                'innodb_log_file_size': '256M',
                'innodb_flush_log_at_trx_commit': '2',
                'innodb_file_per_table': 'ON',
                'innodb_buffer_pool_instances': '8'
            }
            
            with mysql.connector.connect(**self.connection_params) as conn:
                cursor = conn.cursor()
                for param, value in optimizations.items():
                    try:
                        cursor.execute(f"SET GLOBAL {param} = {value}")
                        print(f"Set {param} = {value}")
                    except Exception as e:
                        print(f"Failed to set {param}: {e}")
        
        def setup_read_write_splitting(self):
            # 配置读写分离
            class ReadWriteConnection:
                def __init__(self, master_config, slave_configs):
                    self.master_config = master_config
                    self.slave_configs = slave_configs
                    self.slave_index = 0
                
                def get_write_connection(self):
                    return mysql.connector.connect(**self.master_config)
                
                def get_read_connection(self):
                    # 轮询选择从库
                    config = self.slave_configs[self.slave_index]
                    self.slave_index = (self.slave_index + 1) % len(self.slave_configs)
                    return mysql.connector.connect(**config)
            
            return ReadWriteConnection
    ```
    
    ### Phase 3: NoSQL数据库优化 (2-3天)
    
    #### 3.1 MongoDB优化
    ```python
    from pymongo import MongoClient
    import pymongo
    
    class MongoDBOptimizer:
        def __init__(self, connection_string):
            self.client = MongoClient(connection_string)
        
        def create_optimized_indexes(self, database_name: str, collection_name: str):
            db = self.client[database_name]
            collection = db[collection_name]
            
            # 创建复合索引
            collection.create_index([
                ("user_id", pymongo.ASCENDING),
                ("created_at", pymongo.DESCENDING)
            ])
            
            # 创建文本索引
            collection.create_index([
                ("title", "text"),
                ("content", "text")
            ])
            
            # 创建稀疏索引
            collection.create_index(
                "optional_field",
                sparse=True
            )
        
        def setup_sharding(self, database_name: str, collection_name: str):
            # 配置分片
            admin_db = self.client.admin
            
            # 启用数据库分片
            admin_db.command("enableSharding", database_name)
            
            # 设置分片键
            admin_db.command({
                "shardCollection": f"{database_name}.{collection_name}",
                "key": {"user_id": "hashed"}
            })
        
        def optimize_aggregation_pipeline(self, pipeline):
            # 优化聚合管道
            optimized_pipeline = []
            
            # 将$match阶段尽早执行
            match_stages = [stage for stage in pipeline if '$match' in stage]
            other_stages = [stage for stage in pipeline if '$match' not in stage]
            
            optimized_pipeline.extend(match_stages)
            optimized_pipeline.extend(other_stages)
            
            return optimized_pipeline
    ```
    
    #### 3.2 Redis优化
    ```python
    import redis
    import json
    
    class RedisOptimizer:
        def __init__(self, connection_params):
            self.redis_client = redis.Redis(**connection_params)
        
        def setup_memory_optimization(self):
            # 内存优化配置
            config_updates = {
                'maxmemory-policy': 'allkeys-lru',
                'maxmemory': '2gb',
                'save': '900 1 300 10 60 10000',  # RDB持久化
                'appendonly': 'yes',  # AOF持久化
                'appendfsync': 'everysec'
            }
            
            for key, value in config_updates.items():
                self.redis_client.config_set(key, value)
        
        def implement_caching_strategy(self):
            # 实现多级缓存策略
            class MultiLevelCache:
                def __init__(self, redis_client):
                    self.redis = redis_client
                    self.local_cache = {}  # 本地缓存
                    self.cache_ttl = 3600  # 1小时TTL
                
                def get(self, key):
                    # 先检查本地缓存
                    if key in self.local_cache:
                        return self.local_cache[key]
                    
                    # 再检查Redis缓存
                    value = self.redis.get(key)
                    if value:
                        # 反序列化并存入本地缓存
                        deserialized_value = json.loads(value)
                        self.local_cache[key] = deserialized_value
                        return deserialized_value
                    
                    return None
                
                def set(self, key, value):
                    # 同时设置本地缓存和Redis缓存
                    self.local_cache[key] = value
                    serialized_value = json.dumps(value)
                    self.redis.setex(key, self.cache_ttl, serialized_value)
                
                def delete(self, key):
                    # 同时删除本地缓存和Redis缓存
                    self.local_cache.pop(key, None)
                    self.redis.delete(key)
            
            return MultiLevelCache(self.redis_client)
    ```
    
    ### Phase 4: 向量数据库优化 (2-3天)
    
    #### 4.1 Pinecone优化
    ```python
    import pinecone
    import numpy as np
    
    class PineconeOptimizer:
        def __init__(self, api_key, environment):
            pinecone.init(api_key=api_key, environment=environment)
        
        def create_optimized_index(self, index_name: str, dimension: int):
            # 创建优化的向量索引
            pinecone.create_index(
                name=index_name,
                dimension=dimension,
                metric='cosine',  # 或 'euclidean', 'dotproduct'
                pods=2,  # 增加pods提高性能
                replicas=1,
                pod_type='p1.x1'  # 选择合适的pod类型
            )
        
        def batch_upsert_optimization(self, index_name: str, vectors, batch_size=100):
            # 批量插入优化
            index = pinecone.Index(index_name)
            
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                index.upsert(vectors=batch)
        
        def query_optimization(self, index_name: str, query_vector, top_k=10):
            # 查询优化
            index = pinecone.Index(index_name)
            
            # 使用过滤器减少搜索空间
            results = index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter={"category": "active"}  # 添加过滤条件
            )
            
            return results
    ```
    
    #### 4.2 Weaviate优化
    ```python
    import weaviate
    
    class WeaviateOptimizer:
        def __init__(self, url):
            self.client = weaviate.Client(url)
        
        def create_optimized_schema(self, class_name: str):
            # 创建优化的schema
            schema = {
                "class": class_name,
                "description": f"Optimized {class_name} class",
                "vectorizer": "text2vec-openai",
                "moduleConfig": {
                    "text2vec-openai": {
                        "model": "ada",
                        "modelVersion": "002",
                        "type": "text"
                    }
                },
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "The content of the document",
                        "moduleConfig": {
                            "text2vec-openai": {
                                "skip": False,
                                "vectorizePropertyName": False
                            }
                        }
                    },
                    {
                        "name": "category",
                        "dataType": ["string"],
                        "description": "Category for filtering"
                    }
                ]
            }
            
            self.client.schema.create_class(schema)
        
        def batch_import_optimization(self, class_name: str, data_objects):
            # 批量导入优化
            with self.client.batch as batch:
                batch.batch_size = 100
                for obj in data_objects:
                    batch.add_data_object(
                        data_object=obj,
                        class_name=class_name
                    )
    ```
    
    ### Phase 5: 图数据库优化 (2-3天)
    
    #### 5.1 Neo4j优化
    ```python
    from neo4j import GraphDatabase
    
    class Neo4jOptimizer:
        def __init__(self, uri, user, password):
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
        def create_optimized_indexes(self):
            # 创建优化的索引
            with self.driver.session() as session:
                # 创建节点索引
                session.run("CREATE INDEX user_id_index FOR (u:User) ON (u.id)")
                session.run("CREATE INDEX product_name_index FOR (p:Product) ON (p.name)")
                
                # 创建复合索引
                session.run("""
                    CREATE INDEX user_location_index 
                    FOR (u:User) ON (u.city, u.country)
                """)
                
                # 创建全文索引
                session.run("""
                    CREATE FULLTEXT INDEX product_search 
                    FOR (p:Product) ON EACH [p.name, p.description]
                """)
        
        def optimize_cypher_queries(self):
            # Cypher查询优化示例
            optimized_queries = {
                # 使用索引提示
                "find_user_with_hint": """
                    MATCH (u:User)
                    USING INDEX u:User(id)
                    WHERE u.id = $user_id
                    RETURN u
                """,
                
                # 限制结果集大小
                "limited_results": """
                    MATCH (u:User)-[:PURCHASED]->(p:Product)
                    WHERE u.city = $city
                    RETURN u, p
                    LIMIT 1000
                """,
                
                # 使用WITH子句优化
                "optimized_with_clause": """
                    MATCH (u:User)
                    WHERE u.age > 25
                    WITH u
                    MATCH (u)-[:PURCHASED]->(p:Product)
                    WHERE p.price > 100
                    RETURN u.name, p.name
                """
            }
            
            return optimized_queries
        
        def setup_clustering(self):
            # 设置Neo4j集群配置
            cluster_config = {
                "dbms.mode": "CORE",
                "causal_clustering.minimum_core_cluster_size_at_formation": "3",
                "causal_clustering.minimum_core_cluster_size_at_runtime": "3",
                "causal_clustering.initial_discovery_members": "server1:5000,server2:5000,server3:5000"
            }
            
            return cluster_config
    ```
    
    ### Phase 6: 性能监控与维护 (持续进行)
    
    #### 6.1 监控系统
    ```python
    import psutil
    import time
    from prometheus_client import Gauge, Counter, start_http_server
    
    class DatabaseMonitor:
        def __init__(self):
            # Prometheus指标
            self.db_connections = Gauge('db_connections_active', 'Active database connections')
            self.query_duration = Gauge('db_query_duration_seconds', 'Database query duration')
            self.db_cpu_usage = Gauge('db_cpu_usage_percent', 'Database CPU usage')
            self.db_memory_usage = Gauge('db_memory_usage_percent', 'Database memory usage')
            
        def monitor_system_resources(self):
            while True:
                # 监控CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                self.db_cpu_usage.set(cpu_percent)
                
                # 监控内存使用率
                memory = psutil.virtual_memory()
                self.db_memory_usage.set(memory.percent)
                
                time.sleep(10)  # 每10秒监控一次
        
        def monitor_database_metrics(self, connection_params):
            with psycopg2.connect(**connection_params) as conn:
                cursor = conn.cursor()
                
                # 监控活跃连接数
                cursor.execute("""
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE state = 'active'
                """)
                active_connections = cursor.fetchone()[0]
                self.db_connections.set(active_connections)
                
                # 监控慢查询
                cursor.execute("""
                    SELECT count(*) FROM pg_stat_statements 
                    WHERE mean_time > 1000
                """)
                slow_queries = cursor.fetchone()[0]
                
                if slow_queries > 10:
                    print(f"Warning: {slow_queries} slow queries detected")
    ```
    
    #### 6.2 自动化维护
    ```python
    import schedule
    import subprocess
    
    class DatabaseMaintenance:
        def __init__(self, connection_params):
            self.connection_params = connection_params
        
        def vacuum_analyze(self):
            # 定期执行VACUUM ANALYZE
            with psycopg2.connect(**self.connection_params) as conn:
                conn.autocommit = True
                cursor = conn.cursor()
                cursor.execute("VACUUM ANALYZE")
                print("VACUUM ANALYZE completed")
        
        def update_statistics(self):
            # 更新表统计信息
            with psycopg2.connect(**self.connection_params) as conn:
                cursor = conn.cursor()
                cursor.execute("ANALYZE")
                conn.commit()
                print("Statistics updated")
        
        def backup_database(self):
            # 数据库备份
            backup_command = [
                "pg_dump",
                "-h", self.connection_params['host'],
                "-U", self.connection_params['user'],
                "-d", self.connection_params['database'],
                "-f", f"backup_{int(time.time())}.sql"
            ]
            
            subprocess.run(backup_command, check=True)
            print("Database backup completed")
        
        def schedule_maintenance(self):
            # 调度维护任务
            schedule.every().day.at("02:00").do(self.vacuum_analyze)
            schedule.every().hour.do(self.update_statistics)
            schedule.every().day.at("03:00").do(self.backup_database)
            
            while True:
                schedule.run_pending()
                time.sleep(60)
    ```
  </process>

  <criteria>
    ## 优化效果评估标准
    
    ### 性能指标
    - ✅ 查询响应时间减少50%以上
    - ✅ 数据库吞吐量提升3倍以上
    - ✅ CPU使用率降低到70%以下
    - ✅ 内存使用率控制在80%以下
    
    ### 可用性指标
    - ✅ 系统可用性达到99.99%
    - ✅ 故障恢复时间小于30秒
    - ✅ 数据零丢失
    - ✅ 备份恢复成功率100%
    
    ### 扩展性指标
    - ✅ 支持10倍数据量增长
    - ✅ 支持5倍并发用户增长
    - ✅ 水平扩展能力验证
    - ✅ 负载均衡效果良好
    
    ### 维护性指标
    - ✅ 监控覆盖率100%
    - ✅ 告警响应时间小于5分钟
    - ✅ 自动化维护任务执行成功率99%
    - ✅ 性能报告自动生成
  </criteria>
</execution>