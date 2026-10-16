from sqlalchemy import or_, select, func
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.models.lab import Lab
from app.schemas.lab import LabCreateRequest, LabResponse, LabUpdateRequest


def get_lab_page_list(
    db: Session,
    page: int,
    page_size: int,
    keywords: str | None = None,
    status: int | None = None,
):
    """模糊查询实验室列表"""
    page = max(page, 1)
    page_size = max(page_size, 1)
    conditions = []
    if keywords and keywords.strip():
        like_keywords = f"%{keywords.strip()}%"
        conditions.append(
            or_(Lab.name.like(like_keywords), Lab.location.like(like_keywords))
        )
    if status is not None:
        conditions.append(Lab.status == status)
    total_stmt = select(func.count()).select_from(Lab)

    data_stmt = (
        select(Lab)
        .order_by(Lab.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    if conditions:
        total_stmt = total_stmt.where(*conditions)
        data_stmt = data_stmt.where(*conditions)

    total = db.scalar(total_stmt) or 0
    items = db.scalars(data_stmt).all()

    return PageResponse(
        list=[LabResponse.model_validate(item) for item in items],
        total=total,
    )
    # query = db.query(Lab)
    # if keywords:
    #     query = query.filter(
    #         or_(Lab.name.ilike(f"%{keywords}%"), Lab.location.ilike(f"%{keywords}%"))
    #     )
    # total = query.count()
    # items = (
    #     query.order_by(Lab.id.desc())
    #     .offset((page - 1) * page_size)
    #     .limit(page_size)
    #     .all()
    # )
    # return PageResponse(
    #     list=[LabResponse.model_validate(item) for item in items],
    #     total=total,
    # )


def get_lab(db: Session, lab_id: int):
    """获取实验室详情"""
    lab = db.scalar(select(Lab).where(Lab.id == lab_id))
    if not lab:
        raise BusinessException(message="实验室不存在")
    return LabResponse.model_validate(lab)


def create_lab(db: Session, data: LabCreateRequest):
    """管理员创建实验室"""
    # exists = db.query(Lab).filter(Lab.name == data.name).first()
    exists = db.scalar(select(Lab).where(Lab.name == data.name))
    if exists:
        raise BusinessException(message="实验室名称已存在")

    lab = Lab(**data.model_dump())
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def update_lab(db: Session, lab_id: int, data: LabUpdateRequest):
    """管理员修改实验室信息"""
    # lab = db.query(Lab).filter(Lab.id == lab_id).first()
    lab = db.scalar(select(Lab).where(Lab.id == lab_id))
    if not lab:
        raise BusinessException(message="实验室不存在")

    payload = data.model_dump(exclude_none=True)
    if "name" in payload:
        # exists = (
        #     db.query(Lab).filter(Lab.name == payload["name"], Lab.id != lab_id).first()
        # )
        exists = db.scalar(
            select(Lab).where(Lab.name == payload["name"], Lab.id != lab_id)
        )
        if exists:
            raise BusinessException(message="实验室名称已存在")

    for field, value in payload.items():
        setattr(lab, field, value)
    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def delete_lab(db: Session, lab_id: int):
    """管理员删除实验室"""
    # lab = db.query(Lab).filter(Lab.id == lab_id).first()
    lab = db.scalar(select(Lab).where(Lab.id == lab_id))
    if not lab:
        raise BusinessException(message="实验室不存在")
    db.delete(lab)
    db.commit()
