FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    AZURE_OPENAI_API_KEY="" \
    AZURE_OPENAI_ENDPOINT="" \
    AZURE_OPENAI_DEPLOYMENT="" \
    AZURE_OPENAI_API_VERSION="" \
    OPENAI_API_KEY=""

WORKDIR /app

COPY pyproject.toml uv.lock README.md requirements.txt openenv.yaml ./
COPY support_ops_env ./support_ops_env
COPY scripts ./scripts
COPY tests ./tests

RUN pip install --no-cache-dir --upgrade pip uv && \
    uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 7860

CMD ["python", "-m", "support_ops_env.server"]
