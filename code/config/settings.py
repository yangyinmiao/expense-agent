"""
统一配置管理
所有环境变量从这里读取，业务代码不直接用 os.getenv
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv(
        "OPENAI_BASE_URL", "https://goods.fatrabbits.shop:12788/v1"
    )
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

    # 数据库
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://expense:changeme@localhost:5432/expense_agent"
    )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # MinIO
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ROOT_USER: str = os.getenv("MINIO_ROOT_USER", "minioadmin")
    MINIO_ROOT_PASSWORD: str = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))


settings = Settings()
