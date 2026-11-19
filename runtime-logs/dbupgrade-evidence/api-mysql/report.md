# DB upgrade verification: api / mysql (api-jdk25-mysql)

## 业务一致性（同一 jar、同一端点清单）

| 指标 | 结果 |
|---|---|
| status_match | 79 |
| exact | 20 |
| semantic | 20 |
| nondet | 59 |
| diff / fails | None / 0 |

## 资源占用与性能（old -> new）

| 指标 | old | new |
|---|---|---|
| DB version | 8.0.46 | 9.7.4 |
| DB CPU | 0.37% | None |
| DB memory | 370.9MiB / 15.33GiB | None |
| app startup_ms | 8720 | 7816 |
| app startup RSS(MB) | 501.8 | 540.8 |
| app steady RSS(MB) | 514.2 | 540.8 |
| app avg latency(ms) | 9.77 | 9.14 |
| app status_fail | 59 | 59 |

迁移方式: `mysqldump(mysql:8.0 -> plain SQL)`

