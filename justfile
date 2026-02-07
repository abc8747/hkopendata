fmt:
    uv run --python 3.10 ruff check src tests
    uv run --python 3.10 ruff format --check src tests
    uv run --python 3.10 mypy src tests
