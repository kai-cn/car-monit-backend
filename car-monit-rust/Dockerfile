# Rust 迁移版镜像。
# 默认特性不需要 librdkafka（Cargo.toml 里 rdkafka 是 optional，只有 --features kafka 才引入），
# 所以构建阶段不用装 cmake / libssl-dev，直接用官方 rust 镜像。
FROM rust:1.90-bookworm AS build
WORKDIR /src
COPY . .
RUN cargo build --release --locked

# 运行阶段用 debian-slim：二进制动态链接 glibc，需要 ca-certificates（HTTPS）与 tzdata。
# 不用 distroless 的原因：本服务读取本地时区并写日志目录，slim 更容易排障。
FROM debian:bookworm-slim

ENV TZ=Asia/Shanghai \
    RUST_LOG=info

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates tzdata \
 && rm -rf /var/lib/apt/lists/* \
 && groupadd -r app && useradd -r -g app -u 10001 app \
 && mkdir -p /app/logs \
 && chown -R app:app /app

WORKDIR /app
COPY --from=build /src/target/release/car-monit-rust /app/car-monit-rust

USER 10001
EXPOSE 9989
ENTRYPOINT ["/app/car-monit-rust"]
