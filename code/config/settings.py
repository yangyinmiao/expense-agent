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

    # 数据库（Phase 2 用）
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Redis（Phase 2 用）
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # OSS（Phase 2 用）
    OSS_BUCKET: str = os.getenv("OSS_BUCKET", "")
    OSS_ENDPOINT: str = os.getenv("OSS_ENDPOINT", "")


settings = Settings()
