import asyncio
from contextlib import asynccontextmanager
from traceback import print_exc
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from app.config import UPLOAD_DIR, settings
from app.models.user import User
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.models.reservation import Reservation
from app.database import Base, engine
from app.api import api
from starlette.middleware.cors import CORSMiddleware
from app.common.exceptions import (
    BusinessException,
    bussiness_exception_hadler,
    http_exception_hadler,
    validation_exception_hadler,
    global_exception_hadler,
)
from app.services import kb_service, reservation_service

# 自动创建数据库和数据库表
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.SKIP_KB_WARMUP:
        try:
            await asyncio.to_thread(kb_service.warmup)
        except Exception:
            traceback.print_exc()

    task = asyncio.create_task(
        reservation_service.run_expire_scan()
    )  # 启动项目开启异步的扫描任务
    yield
    task.cancel()  # 关闭项目 同时取消异步任务
    await asyncio.gather(
        task, return_exceptions=True
    )  # 取消任务不再把CanceledError 抛给 lifespan


app = FastAPI(lifespan=lifespan)

# 跨域配置
origins = [
    "http://localhost:5100",
    "http://127.0.0.1:5100",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的前端源
    allow_credentials=True,  # 允许前端携带 Authorization token
    allow_methods=["*"],  # 允许所有请求方法 GET POST PUT DELETE OPTIONS
    allow_headers=["*"],  # 允许所有请求头(包括Authorization)
)

app.include_router(api)

# 注册自定义异常
app.add_exception_handler(BusinessException, bussiness_exception_hadler)
app.add_exception_handler(HTTPException, http_exception_hadler)
app.add_exception_handler(RequestValidationError, validation_exception_hadler)
# 全局异常兜底，必须放在最后注册
app.add_exception_handler(Exception, global_exception_hadler)


# 挂载静态文件访问目录  /uploads/xxx.jpg → uploads/xxx.jpg
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


# @app.on_event("startup")
# async def start_expir_scan():
#     asyncio.create_task(reservation_service.run_expire_scan())


@app.get("/")
def root():
    return {"message": "FastAPI工程正在运行中"}
