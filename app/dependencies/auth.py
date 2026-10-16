# 用户JWT验证
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import user
from app.common.exceptions import BusinessException
from app.database import get_db
from app.models.user import User
from app.utils.jwt import decode_access_token

# 自动获取token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """JWT token 鉴权验证合法性"""
    # 解析token
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已失效，请重新登录"
        )
    # 获取到用户ID
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="无效登录凭证"
        )
    # 从数据库根据用户ID查询用户信息
    # user = db.query(User).filter(User.id == user_id).first()
    stmt = select(User).where(User.id == user_id)
    user = db.scalar(stmt)
    if user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户被禁用"
        )
    return user


# 验证管理员权限
def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """判断JWT token 内角色是否为admin"""
    if current_user.role != "admin":
        raise BusinessException(code=403, message="无权限访问")
    return current_user
