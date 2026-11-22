# 最终 Java JUnit / 本机复测 / 跨语言严格对拍报告

## 结论

- Java JUnit 云验证：16/16 success。
- 本机重新编译打包：16/16 分支 rc=0。
- 本机管理员鉴权复测：302 端点、认证失败 0；压测 533 请求、传输错误 0。
- 跨语言 workflow：baseline 成功；严格门禁要求与 Java 返回一致，当前 backend/api workflow 结论为 failure，差异如实保留。
- 不得将 workflow failure 改写为 success；必须按端点报告修复多语言实现后再重跑。

## 最终 run

- backend run `45031566682`: `failure`
- api run `45031576935`: `failure`

## 跨语言严格对拍

| app | lang | endpoints | status_match | exact | semantic | nondet | fails |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| backend | python | 302 | 302 | 301 | 301 | 1 | 0 |
| backend | go | 302 | 297 | 166 | 182 | 40 | 80 |
| backend | cpp | 302 | 302 | 295 | 295 | 1 | 6 |
| backend | rust | 302 | 297 | 166 | 180 | 41 | 81 |
| api | python | 79 | 30 | 17 | 20 | 10 | 49 |
| api | go | 79 | 62 | 6 | 36 | 6 | 37 |
| api | cpp | 79 | 31 | 21 | 21 | 8 | 50 |
| api | rust | 79 | 72 | 51 | 52 | 4 | 23 |

## 本机证据

- 本机打包：`local-package-evidence/local-package-results.json`
- 本机鉴权契约：`wsl-retest-auth/junit-contract.json`
- 本机鉴权压测：`wsl-retest-auth/junit-load.json`
- 认证失败计数：0
