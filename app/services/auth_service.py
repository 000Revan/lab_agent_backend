from os import name

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.common.exceptions import BusinessException
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserResponse
from app.utils.password import hash_password, verify_password
from app.utils.jwt import create_access_token
from app.schemas.auth import LoginRequest


def login(db: Session, data: LoginRequest):
    # 根据用户账号查询数据库
    # user = db.query(User).filter(User.username == data.username).first()
    user = db.scalar(select(User).where(User.username == data.username))
    # 判断账号与密码是否正确
    if not user or not verify_password(data.password, user.password):
        # return {"code": 400, "message": "账号或密码错误"}
        # return Response.error(code=400, message="账号或密码错误")
        raise BusinessException(code=400, message="账号或密码错误")
    # 验证账号状态
    if user.status != 1:
        # return {"code": 403, "message": "账号已被禁用"}
        # return Response.error(code=403, message="账号已被禁用")
        raise BusinessException(code=403, message="账号已被禁用")
    # 生成token
    token = create_access_token(user.id)
    # 返回信息
    return LoginResponse(token=token, user=UserResponse.model_validate(user))


def register(db: Session, data: RegisterRequest):
    # 根据用户账号查询数据库,是否重复
    # user = db.query(User).filter(User.username == data.username).first()
    user = db.scalar(select(User).where(User.username == data.username))
    if user:
        raise BusinessException(message="账号已存在")
    user_model = User(
        username=data.username,
        password=hash_password(data.password),
        name=data.name or data.username,
        role="student",
        status=1,
    )
    db.add(user_model)
    db.commit()
    db.refresh(user_model)
