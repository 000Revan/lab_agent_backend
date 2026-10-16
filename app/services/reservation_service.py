import asyncio

from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from datetime import datetime
from app.common.exceptions import BusinessException
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.models.reservation import Reservation
from app.models.user import User
from app.common.response import PageResponse
from app.schemas.reservation import ReservationCreateRequest, ReservationResponse
from app.database import SessionLocal


def create_reservation(db: Session, current_user: User, data: ReservationCreateRequest):
    """创建预约"""
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    if data.date < current_date:
        raise BusinessException(message="预约日期不能小于当前日期")
    if data.end_time < data.start_time:
        raise BusinessException(message="预约的结束时间不能小于开始时间")
    if data.date == current_date and data.start_time < current_time:
        raise BusinessException(message="预约开始时间不能小于当前时间")

    lab = db.scalar(select(Lab).where(Lab.id == data.lab_id))
    if not lab:
        raise BusinessException(message="实验室不存在")
    if lab.status != 1:
        raise BusinessException(message="实验室已关闭")
    if lab.open_time and data.start_time < lab.open_time:
        raise BusinessException(message="预约开始时间不能早于实验室开放时间")
    if lab.close_time and data.end_time > lab.close_time:
        raise BusinessException(message="预约结束时间不能晚于实验室关闭时间")

    # equipment_id不为空，则表示这次是预约的实验室设备
    if data.equipment_id is not None:
        equipment = db.scalar(
            select(Equipment).where(Equipment.id == data.equipment_id)
        )
        if not equipment:
            raise BusinessException(message="预约的实验室设备不存在")
        if equipment.lab_id != data.lab_id:
            raise BusinessException(message="设备不属于当前实验室")
        if equipment.status != 1:
            raise BusinessException(message="实验室设备维护中...")

    # 实验室或者设备是否是可预约状态
    stmt = select(Reservation).where(
        Reservation.lab_id == data.lab_id,
        Reservation.date == data.date,
        Reservation.status.in_([0, 1]),  # 0 表示待审核，1 表示已通过不能预约
        Reservation.start_time < data.end_time,
        Reservation.end_time > data.start_time,
    )

    if data.equipment_id is not None:
        stmt = stmt.where(
            Reservation.equipment_id == data.equipment_id
        )  # 预约实验室设备
    else:
        stmt = stmt.where(Reservation.equipment_id.is_(None))  # 只预约实验室
    if db.scalar(stmt):
        raise BusinessException(message="该时段已预约")

    # 创建预约
    reservation = Reservation(
        user_id=current_user.id,
        lab_id=data.lab_id,
        equipment_id=data.equipment_id,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        remark=data.remark,
        status=0,
    )

    db.add(reservation)
    db.commit()
    # db.refresh(reservation)

    # return ReservationResponse.model_validate(reservation)


def get_reservation_page_list(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    status: int | None = None,
):
    """查询预约记录"""
    page = max(page, 1)
    page_size = max(page_size, 1)

    conditions = []

    if current_user.role != "admin":
        conditions.append(Reservation.user_id == current_user.id)

    if status is not None:
        conditions.append(Reservation.status == status)

    total_stmt = select(func.count()).select_from(Reservation)

    data_stmt = (
        select(Reservation)
        .options(
            selectinload(Reservation.user),
            selectinload(Reservation.lab),
            selectinload(Reservation.equipment),
        )
        .order_by(Reservation.id.desc())
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
        res = ReservationResponse.model_validate(item)
        res.user_name = item.user.name if item.user else None
        res.lab_name = item.lab.name if item.lab else None
        res.equipment_name = item.equipment.name if item.equipment else None
        res.type = "设备" if item.equipment_id else "实验室"
        result.append(res)

    return PageResponse(list=result, total=total)

    # query = db.query(Reservation)
    # if current_user.role != "admin":
    #     query = query.filter(Reservation.user_id == current_user.id)
    # if status is not None:
    #     query = query.filter(Reservation.status == status)
    # total = query.count()
    # items = (
    #     query.order_by(Reservation.id.desc())
    #     .offset((page - 1) * page_size)
    #     .limit(page_size)
    #     .all()
    # )
    # result = []
    # for item in items:
    #     res = ReservationResponse.model_validate(item)
    #     res.user_name = item.user.name if item.user else None
    #     res.lab_name = item.lab.name if item.lab else None
    #     res.equipment_name = item.equipment.name if item.equipment else None
    #     res.type = "设备" if item.equipment_id else "实验室"
    #     result.append(res)

    # return PageResponse(list=result, total=total)


def cancel_reservation(db: Session, current_user: User, reservation_id: int):
    """学生取消预约"""
    # item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    item = db.scalar(select(Reservation).where(Reservation.id == reservation_id))
    if not item:
        raise BusinessException(message="预约记录不存在")
    if item.user_id != current_user.id:
        raise BusinessException(message="无权限", code=403)
    if item.status != 0:
        raise BusinessException(message="当前状态无法取消")
    item.status = 3
    db.commit()


def audit_reservation(db: Session, reservation_id: int, status: int):
    """管理员审核预约"""
    if status not in [1, 2]:
        raise BusinessException(message="审核状态错误")
    # item = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    item = db.scalar(select(Reservation).where(Reservation.id == reservation_id))
    if not item:
        raise BusinessException(message="预约记录不存在")
    if item.status != 0:
        raise BusinessException(message="当前状态不支持审核")
    item.status = status
    db.commit()


def expire_pending_reservations():
    """批量取消过期的预约单"""
    db = SessionLocal()
    try:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M")
        items = db.scalars(select(Reservation).where(Reservation.status == 0))
        changed = False
        for item in items:
            if item.date < today or (item.date == today and item.end_time <= time):
                item.status = 3
                changed = True
        if changed:
            db.commit()
    finally:
        db.close()


async def run_expire_scan():
    "1分钟扫描一次"
    try:
        while True:
            await asyncio.to_thread(expire_pending_reservations())
            # print("异步任务正在执行中...")
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        return
