FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock README.md openenv.yaml ./
COPY support_ops_env ./support_ops_env
COPY scripts ./scripts
COPY inference.py ./inference.py

RUN pip install --no-cache-dir --upgrade pip uv && \
    uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "support_ops_env.server.app:app", "--host", "0.0.0.0", "--port", "7860"]
