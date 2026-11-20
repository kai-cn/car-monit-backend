# 云 runner 实测 + Java V3 全量业务对比验收记录（backend 侧）

> 记录时间：2026-11-20（会话内实时记录）
> 触发方式：复用现有 Python workflow — backend `ci.yml` 的 `py` job；
> 跨语言对拍复用 backend master 的 `crosslang-parity-cloud.yml`（`langs=python`）
> 凭据：`D:\work\runtime-logs\gh_cred.py` 缓存 token；dispatch 经 `dispatch-redacted.py`

## 1. 云实测发现并修复的真实缺陷

| # | 现象 | 根因 | 修复 | 提交 |
|---|---|---|---|---|
| 1 | `test_quartz_tasks` FAIL：`全量同步完成，共同步 20 条数据` != `15 条数据` | 用例依赖 `datetime.now()` 落在 2026-10（earliest=2026-08-15 → 3 个月），云上 2026-11 变成 4 个月 | monkeypatch 冻结 `now=2026-10-20`，与 Java V3 审阅基线一致 | `ac960499` |

本地全量 pytest 也曾出现该失败但被误判为"时间依赖既有失败"；云 runner（Linux/UTF-8）
确认后已彻底修复。

## 2. 最终验收结果

| 项 | run / job | 结果 |
|---|---|---|
| backend `ci.yml` `py` job | run `44712980926` | **completed success**（Python 3.12 源码编译 + compileall + pytest + coverage 73% + wheel/sdist） |
| `crosslang-parity-cloud.yml` 整条 run | run `44713232995` | **completed success** |
| └ `baseline-java8` | job `136209979126` | success（Java 8 jar startup 16.5s / RSS 1711MB / ep=2） |
| └ `candidates (python)` | job `136210573835` | **success**，`COMPARE label=java8-vs-python endpoints=2 fails=0` |
| └ `candidates (go)` / `(rust)` | — | success |
| Python vs Java8 对拍报告 | artifact `crosslang-python` | `/` 200/200 OK；`/captchaImage` 200/200 NONDET（验证码非确定）；status_match=2 fails=0 |

日志证据：`D:\work\runtime-logs\bk-py-final.log`、`crosslang-baseline-v3.log`、
`crosslang-python-v3.log`。

## 3. 覆盖度边界（如实记录）

* 现有 `crosslang-parity-cloud.yml` 的 `endpoints/backend.txt` 仅 2 个免认证端点；
  本次 V3 对齐新增的 16 个端点（`/manager/bigScreen/export/**` 10 个、
  `/monitor/bigscreen/**` 6 个）需要权限，未被该 workflow 的 HTTP 对拍覆盖。
* 探针已扩展 `--headers-env`（从环境变量读 JSON 认证头，不落盘）并推送到 Java V3 分支
  （提交 `61462810`），下个会话可给 workflow 增加 token 注入以覆盖认证端点。
* backend `ci.yml` 同 run 的 `go` job failure 与本任务无关。

## 4. 文档索引

* `V3-ALIGNMENT-PLAN.md` / `V3-ALIGNMENT-HANDOVER.md` / `V3-ALIGNMENT-INDEX.md`
* `V3-CLOUD-VERIFICATION.md` —— 本文件
* api 侧：`car-monit-api-python/docs/V3-CLOUD-VERIFICATION.md`
