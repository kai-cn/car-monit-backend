# 交接：Python vs Java V3 全量接口对拍 workflow

> 记录时间：2026-11-20（会话内实时记录）
> 目标：用云 runner 对 Java V3 与 Python 迁移版做 302 个 GET 端点的认证态全量对拍

## 1. 已完成

### 1.1 凭据注入（运行时，不落盘）
* admin 口令通过 GitHub API 注入为仓库 Secret `CI_ADMIN_PASSWORD`
  （`set_repo_secret.py`，libsodium sealed box 加密；值不进仓库/文档/日志/记忆）。
* workflow 仅在 step 级 `env:` 引用 `secrets.CI_ADMIN_PASSWORD`；
  云日志实测显示 `CI_ADMIN_PASSWORD: ***`，符合安全要求。
* 已验证：seed 中 admin 的 bcrypt 哈希与注入口令匹配（`check_bcrypt.py` → `True`）；
  Java V3 登录在 `code` 为空时跳过验证码，可直接用 admin 登录。

### 1.2 资产（均已推送远端）
| 文件 | 分支 | 方式 |
|---|---|---|
| `.github/workflows/python-v3-full-parity.yml` | `master`（默认分支，才可 dispatch） | Contents API |
| `scripts/v3/ops/parity/full_parity_probe.py` | `car-monit-backend-java-V3` | Contents API |
| `scripts/v3/ops/parity/parity_login.py` | `car-monit-backend-java-V3` | Contents API |
| `scripts/v3/ops/parity/endpoints/backend-v3-get-full.txt`（302 个 GET） | `car-monit-backend-java-V3` | Contents API |

* 端点清单由 `extract_backend_endpoints.py` 从 Java V3 的 83 个 Controller 提取 515 个端点
  （GET 302 / POST 83 / DELETE 67 / PUT 63），再由 `gen_full_endpoints.py` 把路径变量样例化为 `1`。
* 探针 `full_parity_probe.py`：启动进程 → 等待端口 → 用 `CI_ADMIN_PASSWORD` 登录 →
  Bearer token 仅在内存 → 逐端点 GET + 二次稳定性校验 → 输出不含口令/令牌的 JSON。

## 2. 云 runner 运行结果（如实记录）

| run | 结果 | 说明 |
|---|---|---|
| `44718506273` | 被后续 dispatch 取消 | 缺少 `/home/ruoyi/logs` 预建，已在 workflow 修复 |
| `44718887047` | failure | `setup-java` 工具缓存 tar 瞬时故障（非代码问题） |
| `44719080019` | **failure** | Java V3 jar 构建成功（201MB）；但两个 probe 步骤失败，见 §3 |

日志证据：`D:\work\runtime-logs\v3full-run3.log`。

## 3. 阻断项（下个会话按序修复）

### 3.1 Java V3 probe：`process exited rc=1`
* 现象：`PROBE_DONE variant=java-v3 ready=False login=None ep=0 err=process exited rc=1`，
  Java 进程启动 1.5 秒即退出，未监听 19903。
* 已排除：Maven 构建成功（201MB fat jar）、DB seed 成功、log 目录已预建。
* 待查：从 artifact `python-v3-full-parity` 的 `out/java-v3.json.app.log` 看具体启动异常
  （本次因 artifact 下载 401 未取到；下个会话用带 auth 的 redirect opener 重试 `save_full_joblog.py` 同款逻辑）。
  常见原因：`java -jar` 的工作目录是仓库根，logback 相对路径或配置资源找不到；
  或需要 V3 特有环境变量（ES/Kafka 地址、内部 token）。

### 3.2 Python probe：`pip install -r requirements.txt` 失败
* 现象：`ERROR: file:///home/runner/work/car-monit-backend/car-monit-backend does not appear to be a Python project: neither 'setup.py' nor 'pyproject.toml' found.`
* 根因：`car-monit-py/requirements.txt` 第 9 行是 `-e .[test]`，
  workflow 在仓库根目录执行 `pip install -r candidate/car-monit-py/requirements.txt`，
  `-e .` 解析到仓库根（非 Python 项目）而非 `candidate/car-monit-py`。
* 修复：把安装命令改为先 `cd candidate/car-monit-py` 再 `pip install -r requirements.txt`，
  或使用 `requirements-runtime.txt`（若无 `-e .`）。

### 3.3 对比步骤未执行
* 因 §3.1/§3.2，两个 JSON 不完整（java ready=False、python 未生成），
  Compare 步骤被跳过。修复后应能看到 `java-v3-vs-python` 的 status_match/exact/semantic 报告。

## 4. 复用命令

```powershell
cd d:\work\runtime-logs
# 重新部署 workflow（改完后）
python push_files_api.py kai-cn/car-monit-backend master v3parity-stage '.github/workflows/python-v3-full-parity.yml'
# 重新部署探针（改完后，注意目标分支是 V3）
python push_files_api.py kai-cn/car-monit-backend car-monit-backend-java-V3 v3parity-stage 'scripts/v3/ops/parity/full_parity_probe.py'
# 触发（口令已注入 Secret，无需再传）
python dispatch-redacted.py kai-cn/car-monit-backend python-v3-full-parity.yml car-monit-backend-java-V3 max_endpoints=302
# 抓日志
python save_full_joblog.py kai-cn/car-monit-backend <job_id> <out.log>
```

## 5. 文档索引
* 两侧 `docs/V3-CLOUD-VERIFICATION.md` —— 先前云实测与 2 端点对拍结果
* 两侧 `docs/V3-ALIGNMENT-HANDOVER.md` —— Java V3 对齐交接
* 本文件：全量对拍 workflow 的专项交接
