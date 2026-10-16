from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import create_engine, DateTime
from app.config import settings
from datetime import datetime

# 创建数据库引擎
engine = create_engine(settings.DATABASE_URL)

# 数据库session会话连接工厂
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Base基类
class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(
        # 主键，自动递增
        primary_key=True,
        autoincrement=True,
        comment="主键ID",
        sort_order=-1,
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, comment="创建时间"
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )
