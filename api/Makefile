.PHONY: migrate
migrate:
# 用法:
# make migrate msg="some message"
	alembic revision --autogenerate -m "$(msg)"
	alembic upgrade head



