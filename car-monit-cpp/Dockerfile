# 多阶段构建：仅依赖系统 OpenSSL / zlib / pthread，无需联网拉第三方库
FROM ubuntu:22.04 AS build

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake libssl-dev zlib1g-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . .
RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build -j"$(nproc)" \
    && ./build/carmonit_tests

FROM ubuntu:22.04
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        libssl3 zlib1g curl tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

WORKDIR /app
COPY --from=build /src/build/car-monit-cpp /app/car-monit-cpp
COPY config /app/config

ENV CM_CONFIG_DIR=/app/config
EXPOSE 9989
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:9989/health || exit 1

ENTRYPOINT ["/app/car-monit-cpp", "--config", "/app/config"]
