from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从 .env 读取的全局配置。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "家庭收支管理系统"
    APP_ENV: str = "development"

    # MySQL SQLAlchemy 连接串
    DATABASE_URL: str = "mysql+pymysql://root:change-me@localhost:3306/family_finance?charset=utf8mb4"
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # 允许访问 API 的前端地址
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # 导入文件大小上限（默认 10MB）
    IMPORT_MAX_FILE_SIZE: int = 10 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()