# mini-manus

## Useful commands

### Alembic

Create a new migration file

```sh
alembic revision --autogenerate -m "create xxx table"
```

Upgrade the database to the latest version

```sh
alembic upgrade head
```

Downgrade the database to the previous version

```sh
alembic downgrade -1
```
