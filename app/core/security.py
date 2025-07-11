"""
AI互动小说 - 安全认证模块
JWT认证、密码加密等安全功能
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Union, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer认证
security = HTTPBearer()


class SecurityManager:
    """安全管理器"""
    
    def __init__(self):
        self.pwd_context = pwd_context
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        try:
            return self.pwd_context.hash(password)
        except Exception as e:
            logger.error(f"密码哈希生成失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码处理失败"
            )
    
    def create_access_token(
        self, 
        data: dict, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌"""
        try:
            to_encode = data.copy()
            
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            
            return encoded_jwt
        except Exception as e:
            logger.error(f"JWT令牌创建失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="令牌创建失败"
            )
    
    def verify_token(self, token: str) -> Optional[dict]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            logger.warning(f"JWT令牌验证失败: {e}")
            return None
        except Exception as e:
            logger.error(f"令牌验证异常: {e}")
            return None
    
    def create_refresh_token(self, data: dict) -> str:
        """创建刷新令牌"""
        try:
            to_encode = data.copy()
            expire = datetime.utcnow() + timedelta(days=7)  # 刷新令牌7天有效
            to_encode.update({"exp": expire, "type": "refresh"})
            
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"刷新令牌创建失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="刷新令牌创建失败"
            )
    
    def validate_password_strength(self, password: str) -> bool:
        """验证密码强度"""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        return has_upper and has_lower and has_digit


# 全局安全管理器实例
security_manager = SecurityManager()


# 认证依赖函数
async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """获取当前用户令牌信息"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = security_manager.verify_token(token)
        
        if payload is None:
            raise credentials_exception
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        return {
            "user_id": user_id,
            "username": payload.get("username"),
            "exp": payload.get("exp"),
            "token_type": payload.get("type", "access")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"令牌验证异常: {e}")
        raise credentials_exception


async def get_current_user_id(
    token_data: dict = Depends(get_current_user_token)
) -> str:
    """获取当前用户ID"""
    return token_data["user_id"]


async def get_optional_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[str]:
    """获取可选的当前用户ID - 用于可选认证的端点"""
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = security_manager.verify_token(token)
        
        if payload is None:
            return None
        
        return payload.get("sub")
    except Exception:
        return None


# 权限验证装饰器
def require_permissions(*permissions: str):
    """权限验证装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 这里可以添加权限检查逻辑
            # 目前简化处理，后续可以扩展
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# API密钥验证
class APIKeyManager:
    """API密钥管理器"""
    
    def __init__(self):
        self.api_keys = set()  # 在实际应用中应该从数据库加载
    
    def generate_api_key(self, user_id: str) -> str:
        """生成API密钥"""
        import secrets
        api_key = f"ak_{secrets.token_urlsafe(32)}"
        self.api_keys.add(api_key)
        return api_key
    
    def validate_api_key(self, api_key: str) -> bool:
        """验证API密钥"""
        return api_key in self.api_keys
    
    def revoke_api_key(self, api_key: str) -> bool:
        """撤销API密钥"""
        if api_key in self.api_keys:
            self.api_keys.remove(api_key)
            return True
        return False


# 全局API密钥管理器
api_key_manager = APIKeyManager()


# 速率限制
class RateLimiter:
    """简单的速率限制器"""
    
    def __init__(self):
        self.requests = {}  # 存储请求计数
    
    def is_allowed(self, identifier: str, max_requests: int = None) -> bool:
        """检查是否允许请求"""
        if max_requests is None:
            max_requests = settings.MAX_REQUESTS_PER_MINUTE
        
        now = datetime.utcnow()
        minute_key = now.strftime("%Y-%m-%d-%H-%M")
        key = f"{identifier}:{minute_key}"
        
        current_count = self.requests.get(key, 0)
        
        if current_count >= max_requests:
            return False
        
        self.requests[key] = current_count + 1
        
        # 清理过期的计数
        self._cleanup_expired_counts()
        
        return True
    
    def _cleanup_expired_counts(self):
        """清理过期的计数"""
        now = datetime.utcnow()
        current_minute = now.strftime("%Y-%m-%d-%H-%M")
        
        # 保留当前分钟和前一分钟的数据
        prev_minute = (now - timedelta(minutes=1)).strftime("%Y-%m-%d-%H-%M")
        
        keys_to_remove = []
        for key in self.requests:
            if not (key.endswith(current_minute) or key.endswith(prev_minute)):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.requests[key]


# 全局速率限制器
rate_limiter = RateLimiter()


# 安全工具函数
def generate_secure_token(length: int = 32) -> str:
    """生成安全令牌"""
    import secrets
    return secrets.token_urlsafe(length)


def hash_data(data: str) -> str:
    """哈希数据"""
    import hashlib
    return hashlib.sha256(data.encode()).hexdigest()


def verify_hash(data: str, hash_value: str) -> bool:
    """验证哈希"""
    return hash_data(data) == hash_value


# 安全中间件相关
def get_client_ip(request) -> str:
    """获取客户端IP地址"""
    # 检查代理头部
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host


# 安全配置验证
def validate_security_config() -> bool:
    """验证安全配置"""
    try:
        # 检查密钥强度
        if len(settings.SECRET_KEY) < 32:
            logger.error("SECRET_KEY长度不足，至少需要32个字符")
            return False
        
        # 检查算法支持
        supported_algorithms = ["HS256", "HS384", "HS512"]
        if settings.ALGORITHM not in supported_algorithms:
            logger.error(f"不支持的JWT算法: {settings.ALGORITHM}")
            return False
        
        # 检查令牌过期时间
        if settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
            logger.error("访问令牌过期时间必须大于0")
            return False
        
        logger.info("安全配置验证通过")
        return True
        
    except Exception as e:
        logger.error(f"安全配置验证失败: {e}")
        return False


# 兼容函数 - 为CRUD模块提供
def get_password_hash(password: str) -> str:
    """获取密码哈希 - 兼容函数"""
    return security_manager.get_password_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码 - 兼容函数"""
    return security_manager.verify_password(plain_password, hashed_password)


# 初始化安全模块
def init_security():
    """初始化安全模块"""
    if not validate_security_config():
        raise RuntimeError("安全配置验证失败")

    logger.info("安全模块初始化完成")
