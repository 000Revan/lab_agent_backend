from pydantic import BaseModel, ConfigDict


# 用户返回响应
class UserResponse(BaseModel):
    """用户响应信息"""

    id: int
    username: str
    name: str
    role: str
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    status: int

    # 将对象转换成json
    model_config = ConfigDict(from_attributes=True)


class UserCreateRequest(BaseModel):
    """创建用户参数"""

    username: str
    password: str = "123"
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    role: str = "student"
    status: int = 1


class UserUpdateRequest(BaseModel):
    """用户信息修改参数"""

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    role: str | None = None
    status: int | None = None


class PasswordUpdateRequest(BaseModel):
    """修改密码请求参数"""

    old_password: str
    new_password: str
