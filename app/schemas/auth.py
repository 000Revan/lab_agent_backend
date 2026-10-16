from pydantic import BaseModel, field_validator

from app.schemas.user import UserResponse


# 登录请求入参
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应参数"""

    token: str
    user: UserResponse


class RegisterRequest(BaseModel):
    """用户注册请求参数"""

    username: str
    password: str
    name: str | None = None

    @field_validator("username", "password")
    @classmethod
    def not_blank(cls, value: str):
        if not value.strip():
            raise ValueError("不能为空")
        return value


class RegisterResponse(BaseModel):
    """注册响应参数"""

    token: str
    user: UserResponse
