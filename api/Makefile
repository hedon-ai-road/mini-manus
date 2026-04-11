.PHONY: migrate, run-dev

migrate:
# 用法:
# make migrate msg="some message"
	alembic revision --autogenerate -m "$(msg)"
	alembic upgrade head

run-dev:
	uvicorn app.main:app --reload --lifespan on --port 9527

