# Python 3.15.2 迁移版镜像。
# Pillow 13 / orjson 3.13 提供 cp315 wheel；其余依赖也都有 manylinux wheel。
FROM python:3.15.2-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai

WORKDIR /app

COPY pyproject.toml README_PY.md ./
COPY app ./app
COPY config ./config
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN groupadd -r app && useradd -r -g app -u 10001 app \
 && mkdir -p /app/logs \
 && chown -R app:app /app

USER 10001
EXPOSE 9989
CMD ["python", "run.py"]
