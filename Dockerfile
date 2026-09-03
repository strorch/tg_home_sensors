FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

COPY src ./src

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "--no-sync", "python", "-m", "src.main"]
