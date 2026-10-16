from sqlalchemy import or_, select, func

from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.models.user import User
from app.schemas import file
from app.schemas.user import (
    PasswordUpdateRequest,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from sqlalchemy.orm import Session

from app.utils.password import hash_password, verify_password


def get_user_info(user: User) -> UserResponse:
    """获取用户信息"""
    return UserResponse.model_validate(user)


def update_user_info(data: UserUpdateRequest, user: User, db: Session):
    """修改用户信息"""
    # pydantic对象转成字典
    user_dict = data.model_dump(exclude_none=True, exclude={"role", "status"})
    for field, value in user_dict.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def update_user_password(data: PasswordUpdateRequest, user: User, db: Session):
    """修改用户密码"""
    if not verify_password(data.old_password, user.password):
        raise BusinessException(message="原密码错误")
    if data.old_password == data.new_password:
        raise BusinessException(message="新密码不能与原密码相同")
    user.password = hash_password(data.new_password)
    db.commit()


def get_user_page_list(
    db: Session, page: int, page_size: int, keywords: str | None = None
):
    """分页模糊查询用户列表"""
    page = max(page, 1)
    page_size = max(page_size, 1)
    conditions = []
    if keywords and keywords.strip():
        like_keywords = f"%{keywords.strip()}%"
        conditions.append(
            or_(User.username.like(like_keywords), User.name.like(like_keywords))
        )
    total_stmt = select(func.count()).select_from(User)

    data_stmt = (
        select(User)
        .order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    if conditions:
        total_stmt = total_stmt.where(*conditions)
        data_stmt = data_stmt.where(*conditions)

    total = db.scalar(total_stmt) or 0
    items = db.scalars(data_stmt).all()

    return PageResponse(
        list=[UserResponse.model_validate(item) for item in items],
        total=total,
    )
    # query = db.query(User)
    # if username:
    #     query = query.filter(User.username.like(f"%{username}%"))
    # total = query.count()
    # items = (
    #     query.offset((page - 1) * page_size)
    #     .limit(page_size)
    #     .order_by(User.id.desc())
    #     .all()
    # )
    # return PageResponse(
    #     list=[UserResponse.model_validate(item) for item in items], total=total
    # )


def create_user(db: Session, data: UserCreateRequest):
    """管理员新增用户接口"""
    exist = db.scalar(select(User).where(User.username == data.username))
    if exist:
        raise BusinessException(message="账号已存在")
    user = User(
        username=data.username,
        password=hash_password(data.password),
        name=data.name,
        email=data.email,
        phone=data.phone,
        avatar=data.avatar,
        role=data.role or "student",
        status=data.status if data.status is not None else 1,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


def update_user(db: Session, user_id: int, data: UserUpdateRequest):
    """管理员更新用户信息接口"""
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise BusinessException(message="账号不存在")

    payload = data.model_dump(exclude_none=True)
    for filed, value in payload.items():
        setattr(user, filed, value)
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


def delete_user(db: Session, user_id: int, current_user: User):
    """管理员删除用户"""
    if user_id == current_user.id:
        raise BusinessException(message="不能删除当前登录的账号")
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise BusinessException(message="用户不存在")
    db.delete(user)
    db.commit()
