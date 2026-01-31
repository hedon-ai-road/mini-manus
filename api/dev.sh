#!/bin/bash

# 激活虚拟环境
source .venv/bin/activate

# 启动 FastAPI 服务
uvicorn app.main:app --reload --lifespan on --port 9527