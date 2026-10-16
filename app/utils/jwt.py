from datetime import datetime, timedelta

import jwt
from app.config import settings


# 创建token
def create_access_token(user_id: int) -> str:
    """创建JWT token"""
    # 设置过期时间
    expire = datetime.now() + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    # 包含的信息（用户id，过期时间）
    payload = {"user_id": user_id, "exp": expire}  # "exp"是固定key，不能写成别的

    # 创建token
    return jwt.encode(
        # 设施包含信息，jwt密钥，加密算法
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


# 解析Token
def decode_access_token(token: str) -> dict:
    """解析JWT token"""
    return jwt.decode(
        # token,jwt密钥，加密算法
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
