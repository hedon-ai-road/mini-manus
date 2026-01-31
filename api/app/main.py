import logging
from app.infrastructure.logging import setup_logging
from core.config import get_settings

from fastapi import FastAPI

# 1. 加载配置信息
settings = get_settings()

# 2. 初始化日志系统
setup_logging()
logger = logging.getLogger(__name__)
logger.info("测试~")

# 启动 fastapi
# 运行方式：uvicorn app.main:app --reload --port 9527
app = FastAPI()
