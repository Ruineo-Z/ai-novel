# Docker 数据库服务部署指南

## 概述

本项目使用 Docker 来管理所有数据库服务，包括：
- **PostgreSQL**: 主数据库
- **Redis**: 缓存和会话存储
- **ChromaDB**: 向量数据库（用于AI记忆存储）
- **pgAdmin**: PostgreSQL管理工具（可选）
- **Redis Commander**: Redis管理工具（可选）

## 快速开始

### 1. 前置要求

确保已安装以下软件：
- Docker (>= 20.10)
- Docker Compose (>= 2.0)

### 2. 启动核心服务

```bash
# 启动核心数据库服务
./scripts/docker-services.sh start

# 或者启动所有服务（包括管理工具）
./scripts/docker-services.sh start-all
```

### 3. 检查服务状态

```bash
# 查看服务状态
./scripts/docker-services.sh status

# 检查服务健康状态
./scripts/docker-services.sh health
```

### 4. 配置应用环境

复制Docker环境配置文件：
```bash
cp .env.docker .env
```

根据需要修改配置文件中的设置。

## 服务详情

### PostgreSQL 数据库

- **端口**: 5432
- **数据库名**: ai_novel
- **用户名**: ai_novel_user
- **密码**: ai_novel_password
- **连接URL**: `postgresql://ai_novel_user:ai_novel_password@localhost:5432/ai_novel`

### Redis 缓存

- **端口**: 6379
- **密码**: ai_novel_redis_password
- **连接URL**: `redis://:ai_novel_redis_password@localhost:6379/0`

### ChromaDB 向量数据库

- **端口**: 8000
- **API地址**: http://localhost:8000
- **健康检查**: http://localhost:8000/api/v1/heartbeat

### 管理工具

#### pgAdmin (PostgreSQL管理)
- **端口**: 5050
- **访问地址**: http://localhost:5050
- **用户名**: admin@ai-novel.com
- **密码**: admin_password

#### Redis Commander (Redis管理)
- **端口**: 8081
- **访问地址**: http://localhost:8081

## 常用命令

### 服务管理

```bash
# 启动核心服务
./scripts/docker-services.sh start

# 启动所有服务（包括管理工具）
./scripts/docker-services.sh start-all

# 停止所有服务
./scripts/docker-services.sh stop

# 重启服务
./scripts/docker-services.sh restart

# 查看服务状态
./scripts/docker-services.sh status

# 检查服务健康状态
./scripts/docker-services.sh health
```

### 日志查看

```bash
# 查看所有服务日志
./scripts/docker-services.sh logs

# 查看特定服务日志
./scripts/docker-services.sh logs postgres
./scripts/docker-services.sh logs redis
./scripts/docker-services.sh logs chromadb
```

### 数据管理

```bash
# 备份数据
./scripts/docker-services.sh backup

# 清理所有数据（谨慎使用）
./scripts/docker-services.sh clean
```

## 数据持久化

所有数据都通过Docker卷进行持久化：

- `postgres_data`: PostgreSQL数据
- `redis_data`: Redis数据
- `chromadb_data`: ChromaDB数据
- `pgadmin_data`: pgAdmin配置

即使容器被删除，数据也会保留。

## 网络配置

所有服务都在 `ai-novel-network` 网络中运行，可以通过服务名相互访问。

## 环境配置

### 开发环境

使用 `.env.docker` 配置文件，包含开发环境的默认设置。

### 生产环境

1. 修改密码和密钥
2. 调整资源限制
3. 配置备份策略
4. 启用SSL/TLS

## 故障排除

### 服务无法启动

1. 检查端口是否被占用：
   ```bash
   netstat -tulpn | grep -E ':(5432|6379|8000|5050|8081)'
   ```

2. 检查Docker服务状态：
   ```bash
   docker ps
   docker-compose --env-file .env.docker ps
   ```

3. 查看服务日志：
   ```bash
   ./scripts/docker-services.sh logs [service_name]
   ```

### 数据库连接失败

1. 确认服务已启动：
   ```bash
   ./scripts/docker-services.sh health
   ```

2. 检查网络连接：
   ```bash
   docker network ls
   docker network inspect ai-novel_ai-novel-network
   ```

3. 验证连接参数：
   ```bash
   # PostgreSQL
   docker-compose --env-file .env.docker exec postgres psql -U ai_novel_user -d ai_novel -c "SELECT 1;"
   
   # Redis
   docker-compose --env-file .env.docker exec redis redis-cli -a ai_novel_redis_password ping
   ```

### 性能优化

1. **PostgreSQL优化**：
   - 调整 `shared_buffers`
   - 配置 `work_mem`
   - 优化 `max_connections`

2. **Redis优化**：
   - 调整 `maxmemory`
   - 配置 `maxmemory-policy`
   - 启用持久化

3. **ChromaDB优化**：
   - 调整内存限制
   - 配置批处理大小

## 安全注意事项

1. **生产环境**：
   - 更改所有默认密码
   - 使用强密码
   - 限制网络访问
   - 启用SSL/TLS

2. **数据备份**：
   - 定期备份数据
   - 测试恢复流程
   - 异地存储备份

3. **监控**：
   - 监控服务状态
   - 设置告警
   - 记录访问日志

## 更多帮助

查看脚本帮助信息：
```bash
./scripts/docker-services.sh help
```

或查看Docker Compose配置：
```bash
cat docker-compose.yml
```
