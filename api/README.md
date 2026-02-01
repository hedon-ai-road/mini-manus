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

### PyTest

Run all the tests

```sh
pytest
```

Run specify folder tests

```sh
pytest <folder>
```

Run specify test file

```sh
pytest <file>
```

Run specify test function

```sh
pytest <file>::<function>
```

Run specify class tests

```sh
pytest <file>::<class>
```

Run specify method tests

```sh
pytest <file>::<class>::<method>
```

Show standard output and verbose output

```sh
pytest -s -v
```

### Uvicorn

Run the FastAPI server with hot reload

```sh
uvicorn app.main:app --reload --lifespan on --port 9527
```
