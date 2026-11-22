<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# DB upgrade verification: api / opengauss (api-jdk25-opengauss)

## 业务一致性（同一 jar、同一端点清单）

| 指标 | 结果 |
|---|---|
| status_match | 0 |
| exact | 0 |
| semantic | 0 |
| nondet | 0 |
| diff / fails | None / 0 |

## 资源占用与性能（old -> new）

| 指标 | old | new |
|---|---|---|
| DB version |  |  |
| DB CPU | 0.66% | 0.00% |
| DB memory | 356.5MiB / 15.61GiB | 0B / 0B |
| app startup_ms | 5423 | 3608 |
| app startup RSS(MB) | 323.1 | 285.5 |
| app steady RSS(MB) | None | None |
| app avg latency(ms) | None | None |
| app status_fail | 0 | 0 |

迁移方式: `FAILED:pg_dump; fallback to gs_dump in container`

