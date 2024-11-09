FROM python:3.9-slim

WORKDIR /app

COPY . /app

# 持久化
VOLUME ["/app/file"]

RUN pip install --no-cache-dir fastapi httpx pydantic cryptography uvicorn

# 端口
EXPOSE 12987

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "12987"]