.PHONY: migrate run-dev build-sandbox gen-req docker-up

migrate:
# 用法:
# make migrate msg="some message"
	alembic revision --autogenerate -m "$(msg)"
	alembic upgrade head

run-dev:
	uvicorn app.main:app --reload --lifespan on --port 9527

# 构建中控默认使用的沙箱镜像（与 core/config.py 的 sandbox_image 一致）
build-sandbox:
	docker build -f ../sandbox/.devops/Dockerfile -t mini-manus-sandbox:latest ../sandbox

# 从 uv.lock 重新生成 requirements.txt（依赖更新后执行）
gen-req:
	uv export --no-hashes > requirements.txt

# 构建并启动所有容器（自动刷新 requirements.txt）
docker-up: gen-req
	docker compose up -d --build
