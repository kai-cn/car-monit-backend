# Python 3.12 迁移版镜像。
# 依赖均有 manylinux wheel（PyMySQL / bcrypt / Pillow / psutil），因此不需要编译工具链。
FROM python:3.12-slim

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
