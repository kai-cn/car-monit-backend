<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# Java 全版本 JUnit/压测与 Java25 跨语言全量对拍报告

日期：2026-11-22

## 结论

- Java JUnit 全接口/压测：16/16 cloud run success。
- Java25 Boot4 crosslang：backend/api 两个 workflow success，baseline + python/go/cpp/rust baseline success；候选严格对拍 failure。
- 本地复跑：JUnit 生成与 Java8 编译通过；workflow YAML 4/4；脚本注释 TOTAL_MISSING 0；stub 驱动 contract/load 均 rc=0。
- 跨语言对齐差异按 artifact 真实记录，未通过放宽断言隐藏；差异详见下表。

## Java JUnit run 明细

| app | jdk | branch | run | conclusion |
| --- | --- | --- | ---: | --- |
| backend | 8 | master | 44993519137 | success |
| backend | 8 | car-monit-backend-java-V3 | 44993526377 | success |
| backend | 8 | feat/backend-full-parity | 44993534171 | success |
| backend | 17 | car-monit-backend-jdk17 | 44993542032 | success |
| backend | 21 | car-monit-backend-jdk21 | 44993549410 | success |
| backend | 25 | car-monit-backend-jdk25 | 44993556344 | success |
| backend | 25 | feature-dbupgrade | 44993563358 | success |
| api | 8 | master | 44993569427 | success |
| api | 8 | car-monit-api-java-V3 | 44993575886 | success |
| api | 8 | car-monit-api-java-fix | 44993583228 | success |
| api | 17 | feature/springboot3-jdk17 | 44993590020 | success |
| api | 21 | feature/springboot3 | 44993597379 | success |
| api | 17 | car-monit-api-jdk17 | 44993604632 | success |
| api | 21 | car-monit-api-jdk21 | 44993611914 | success |
| api | 25 | car-monit-api-jdk25 | 44993619858 | success |
| api | 25 | feature-dbupgrade | 44993628784 | success |

## Java25 crosslang workflow

| app | run | conclusion |
| --- | ---: | --- |
| backend | 44993639979 | success |
| api | 44993649569 | success |

## 跨语言全接口对齐与压测

| app | lang | endpoints | status_match | exact | semantic | nondet | fails | rps(candidate/baseline) | p95(candidate/baseline) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| backend | python | 302 | 302 | 301 | 301 | 1 | 0 | 940.37/15930.73 | 11/1 |
| backend | go | 302 | 297 | 292 | 292 | 1 | 9 | 47793.20/15930.73 | 1/1 |
| backend | cpp | 302 | 302 | 295 | 295 | 1 | 6 | 43496.17/15930.73 | 1/1 |
| backend | rust | 302 | 302 | 301 | 301 | 1 | 0 | 24513.07/15930.73 | 1/1 |
| api | python | 79 | 30 | 15 | 20 | 10 | 49 | 1.27/594.43 | 10060/50 |
| api | go | 79 | 62 | 6 | 36 | 6 | 37 | 2634.87/594.43 | 12/50 |
| api | cpp | 79 | 75 | 31 | 41 | 9 | 29 | 405.07/594.43 | 61/50 |
| api | rust | 79 | 72 | 30 | 49 | 9 | 21 | 5323.13/594.43 | 4/50 |

## 本机 WSL 重新编译打包与服务复测

- 重新编译打包：16/16 分支成功。
- WSL Docker 数据库：MySQL carmonitdb 与 Redis 可用。
- 本机服务契约：302 端点，失败 0。
- 本机服务压测：total=145354，ok=145354，errors=0，rps=9690.27，p95=1。

## 本地复跑

```text
api: {'generate_rc': 0, 'compile_rc': 0, 'generate': 'generated 79 endpoints -> D:\\work\\runtime-logs\\local-rerun-check\\api\\generated', 'compile': ''}
backend: {'generate_rc': 0, 'compile_rc': 0, 'generate': 'generated 302 endpoints -> D:\\work\\runtime-logs\\local-rerun-check\\backend\\generated', 'compile': ''}
workflow_yaml: {'D:\\work\\IdeaProjects\\car-monit-backend-new\\.github\\workflows\\java-junit-load-cloud.yml': 'OK', 'D:\\work\\IdeaProjects\\car-monit-backend-new\\.github\\workflows\\crosslang-full-parity-cloud.yml': 'OK', 'D:\\work\\IdeaProjects\\car-monit-api\\.github\\workflows\\java-junit-load-cloud.yml': 'OK', 'D:\\work\\IdeaProjects\\car-monit-api\\.github\\workflows\\crosslang-full-parity-cloud.yml': 'OK'}
script_comments: {'rc': 0, 'output': 'TOTAL_MISSING 0'}
java-junit-results.json: {'total': 16, 'success': 16}
crosslang-full-results.json: {'total': 2, 'success': 2}
native-crosslang-status.json: {'total': 11, 'success': 11}
java-upgrade-runs.json: {'total': 16, 'success': 16}
local junit smoke: contract_rc=0 load_rc=0 total=13727 errors=0
```
