from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from app.common.exceptions import BusinessException
from app.common.response import PageResponse
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.schemas.equipment import (
    EquipmentResponse,
    EquipmentCreateRequest,
    EquipmentUpdateRequest,
)
from sqlalchemy.orm import Session


def get_equipment_page_list(
    db: Session,
    page: int,
    page_size: int,
    keywords: str | None = None,
    lab_id: int | None = None,
):
    """分页模糊查询设备列表"""
    page = max(page, 1)
    page_size = max(page_size, 1)

    conditions = []

    if lab_id is not None:
        conditions.append(Equipment.lab_id == lab_id)

    if keywords and keywords.strip():
        conditions.append(Equipment.name.ilike(f"%{keywords.strip()}%"))

    total_stmt = select(func.count()).select_from(Equipment)

    data_stmt = (
        select(Equipment)
        .options(selectinload(Equipment.lab))
        .order_by(Equipment.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    if conditions:
        total_stmt = total_stmt.where(*conditions)
        data_stmt = data_stmt.where(*conditions)

    total = db.scalar(total_stmt) or 0
    items = db.scalars(data_stmt).all()

    result = []
    for item in items:
        res = EquipmentResponse.model_validate(item)
        res.lab_name = item.lab.name if item.lab else None
        result.append(res)

    return PageResponse(list=result, total=total)
    # query = db.query(Equipment)
    # if lab_id:
    #     query = query.filter(Equipment.lab_id == lab_id)
    # if keywords:
    #     query = query.filter(Equipment.name.ilike(f"%{keywords}%"))
    # total = query.count()
    # items = (
    #     query.order_by(Equipment.id.desc())
    #     .offset((page - 1) * page_size)
    #     .limit(page_size)
    #     .all()
    # )
    # result = []
    # for item in items:
    #     res = EquipmentResponse.model_validate(item)
    #     res.lab_name = item.lab.name if item.lab else None
    #     result.append(res)
    # return PageResponse(list=result, total=total)


def create_equipment(db: Session, data: EquipmentCreateRequest):
    """管理员新增设备"""
    # exist = db.query(Equipment).filter(Equipment.name == data.name).first()
    exist = db.scalar(
        select(Equipment).where(
            Equipment.lab_id == data.lab_id,
            Equipment.name == data.name,
        )
    )
    if exist:
        raise BusinessException(message="实验室设备已存在")
    equipment = Equipment(**data.model_dump())
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    res = EquipmentResponse.model_validate(equipment)
    res.lab_name = equipment.lab.name if equipment.lab else None
    return res


def update_equipment(db: Session, equipment_id: int, data: EquipmentUpdateRequest):
    """管理员更新设备"""
    # equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    equipment = db.scalar(select(Equipment).where(Equipment.id == equipment_id))
    if not equipment:
        raise BusinessException(message="实验室设备不存在")
    payload = data.model_dump(exclude_none=True)
    lab_id = payload.get("lab_id", equipment.lab_id)
    name = payload.get("name", equipment.name)
    # lab = db.query(Lab).filter(Lab.id == lab_id).first()
    lab = db.scalar(select(Lab).where(Lab.id == lab_id))
    if not lab:
        raise BusinessException(message="实验室不存在")
    # exist = (
    #     db.query(Equipment)
    #     .filter(
    #         Equipment.lab_id == lab_id,
    #         Equipment.name == name,
    #         Equipment.id != equipment.id,
    #     )
    #     .first()
    # )
    exist = db.scalar(
        select(Equipment).where(
            Equipment.lab_id == lab_id,
            Equipment.name == name,
            Equipment.id != equipment.id,
        )
    )
    if exist:
        raise BusinessException(message="同一个实验室不能存在同名的设备")

    for filed, value in payload.items():
        setattr(equipment, filed, value)

    db.commit()
    db.refresh(equipment)
    res = EquipmentResponse.model_validate(equipment)
    res.lab_name = equipment.lab.name if equipment.lab else None
    return EquipmentResponse.model_validate(res)


def delete_equipment(db: Session, equipment_id: int):
    """管理员删除设备"""
    # equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    equipment = db.scalar(select(Equipment).where(Equipment.id == equipment_id))
    if not equipment:
        raise BusinessException(message="实验室设备不存在")
    db.delete(equipment)
    db.commit()
