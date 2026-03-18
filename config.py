"""
配置管理模块
优先从环境变量读取，其次从 .env 文件，最后使用默认值
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# 加载 .env 文件（若存在）
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    

@dataclass
class Settings:
    # ── QQ Bot 鉴权 ──────────────────────────────
    APP_ID: str = field(default_factory=lambda: os.getenv("QQ_APP_ID", ""))
    APP_SECRET: str = field(default_factory=lambda: os.getenv("QQ_APP_SECRET", ""))

    # ── 运行模式 ─────────────────────────────────
    SANDBOX: bool = field(default_factory=lambda: os.getenv("QQ_SANDBOX", "true").lower() == "true")

    # ── 回复前缀（可选） ──────────────────────────
    REPLY_PREFIX: str = field(default_factory=lambda: os.getenv("REPLY_PREFIX", ""))

    # ── 日志等级 ─────────────────────────────────
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


settings = Settings()
