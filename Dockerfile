FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src ./src
COPY main.py README.md ./

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "src/main.py"]
