# car-monit-go 本地质量门禁
# 用法：make help
SHELL := /bin/bash
GO ?= go
BIN_DIR := bin
SERVER := $(BIN_DIR)/carmonit-server
CONFIG ?= configs/config.yaml
GOLANGCI_LINT_VERSION ?= v2.1.6
BASE_URL ?= http://127.0.0.1:9989

# -buildvcs=false：worktree / CI 环境下 .git 状态可能不完整，避免 VCS stamping 失败。
GOFLAGS ?= -buildvcs=false

.PHONY: help
help: ## 列出所有目标
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

.PHONY: tidy
tidy: ## 整理依赖并确认 go.mod/go.sum 无漂移
	$(GO) mod tidy
	@git diff --exit-code -- go.mod go.sum || (echo "go.mod/go.sum 有未提交变化，请检查" && exit 1)

.PHONY: fmt
fmt: ## 写入 gofmt 格式
	gofmt -w $$(find . -name '*.go' -not -path './vendor/*')

.PHONY: fmt-check
fmt-check: ## 校验 gofmt（CI 用）
	@out=$$(gofmt -l $$(find . -name '*.go' -not -path './vendor/*')); \
	if [ -n "$$out" ]; then echo "以下文件未格式化："; echo "$$out"; exit 1; fi

.PHONY: build
build: ## 编译服务端到 bin/
	@mkdir -p $(BIN_DIR)
	$(GO) build $(GOFLAGS) -trimpath -o $(SERVER) ./cmd/server

.PHONY: vet
vet: ## go vet
	$(GO) vet ./...

.PHONY: test
test: ## 单元测试
	$(GO) test $(GOFLAGS) ./...

.PHONY: test-race
test-race: ## 竞态检测（本地/夜间任务）
	$(GO) test $(GOFLAGS) -race -count=1 ./...

.PHONY: cover
cover: ## 输出覆盖率
	$(GO) test $(GOFLAGS) -coverprofile=coverage.out ./...
	$(GO) tool cover -func=coverage.out | tail -1

.PHONY: lint
lint: ## golangci-lint（需自行安装 $(GOLANGCI_LINT_VERSION)）
	@command -v golangci-lint >/dev/null || (echo "未安装 golangci-lint，见 https://golangci-lint.run" && exit 1)
	golangci-lint run

.PHONY: check
check: fmt-check vet test build ## 提交前必须全绿

.PHONY: migrate
migrate: ## 应用数据库版本化迁移
	$(GO) run $(GOFLAGS) ./cmd/migrate -c $(CONFIG)

.PHONY: run
run: ## 本地启动
	$(GO) run $(GOFLAGS) ./cmd/server -c $(CONFIG)

.PHONY: parity-perms
parity-perms: ## 静态比对 Java 注解与 Go 注册的权限/操作日志
	python scripts/parity/check_perms.py \
		--java-root ../ruoyi-admin/src/main/java/com/ruoyi/web/controller \
		--go-root internal

.PHONY: parity-perms-runtime
parity-perms-runtime: ## 无权限账号运行时 403 + sys_oper_log 落行（需先启动服务并准备 noperm 账号）
	python scripts/parity/check_permissions_runtime.py --base-url $(BASE_URL)

.PHONY: docker
docker: ## 构建镜像
	docker build -t carmonit-go:local .

.PHONY: clean
clean: ## 清理构建产物
	rm -rf $(BIN_DIR) coverage.out
