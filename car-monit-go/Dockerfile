# syntax=docker/dockerfile:1

# ---------- build ----------
FROM golang:1.27-alpine AS build
WORKDIR /src

# 依赖层单独缓存
COPY go.mod go.sum ./
RUN go mod download

COPY . .
# -buildvcs=false：镜像内不拷贝 .git，避免 VCS stamping 失败
# cmd/migrate 只在部分分支（如 car-monit-go-V2）存在，存在才构建，不假设它一定在。
RUN CGO_ENABLED=0 GOOS=linux go build -buildvcs=false -trimpath -ldflags "-s -w" \
    -o /out/carmonit-server ./cmd/server \
 && if [ -d ./cmd/migrate ]; then \
      CGO_ENABLED=0 GOOS=linux go build -buildvcs=false -trimpath -ldflags "-s -w" \
        -o /out/carmonit-migrate ./cmd/migrate; \
    fi

# ---------- runtime ----------
# distroless：无 shell、无包管理器，攻击面最小；需要时改成 alpine 便于排障。
FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /app

# 整个 /out 一起拷：migrate 不存在时也不会让 COPY 失败。
COPY --from=build /out/ /app/
# 代码生成器的 Velocity 模板与导入/下载模板属于运行期数据，随镜像分发。
COPY --from=build /src/configs/vm /app/configs/vm
COPY --from=build /src/configs/vmplus /app/configs/vmplus
COPY --from=build /src/configs/templates /app/configs/templates
COPY --from=build /src/configs/generator.yml /app/configs/generator.yml
# 配置文件不入镜像：运行时以单文件挂载到 /app/configs/config.yaml
#   docker run -v $PWD/configs/config.yaml:/app/configs/config.yaml:ro ...
# 单文件挂载不会遮蔽同目录下的 vm/vmplus/templates。
EXPOSE 9989
USER nonroot:nonroot
ENTRYPOINT ["/app/carmonit-server", "-c", "/app/configs/config.yaml"]
