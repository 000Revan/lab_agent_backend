from annotated_types import T
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# 后端项目根路径
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    LLM_API_KEY: str
    LLM_MODEL: str
    LLM_BASE_URL: str

    SKIP_KB_WARMUP: bool = False

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8"
    )


settings = Settings()

# 文件保存 文件夹路径
UPLOAD_DIR = BASE_DIR / "uploads"
# 确保 文件保存 文件夹存在
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# 文件上传最大大小
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100M

# 文件允许上传类型
ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
}
