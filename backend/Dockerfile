FROM python:3.12-slim

WORKDIR /app

# uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml README.md ./

# install dependencies
RUN uv sync --no-dev --no-install-project

# copy code
COPY app/ ./app/

# installing project
RUN uv sync --no-dev

EXPOSE 8000

# run uvicorn - use --reload flag via docker-compose for dev
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
