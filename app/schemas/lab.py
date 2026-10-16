from pydantic import BaseModel, ConfigDict


class LabResponse(BaseModel):
    """实验室响应信息"""

    id: int
    name: str
    location: str | None = None
    capacity: int
    open_time: str | None = None
    close_time: str | None = None
    description: str | None = None
    img: str | None = None
    status: int

    model_config = ConfigDict(from_attributes=True)


class LabCreateRequest(BaseModel):
    """实验室创建信息"""

    name: str
    location: str | None = None
    capacity: int = 0
    open_time: str | None = None
    close_time: str | None = None
    description: str | None = None
    img: str | None = None
    status: int = 1


class LabUpdateRequest(BaseModel):
    """实验室信息修改"""

    name: str | None = None
    location: str | None = None
    capacity: int | None = None
    open_time: str | None = None
    close_time: str | None = None
    description: str | None = None
    img: str | None = None
    status: int | None = None
