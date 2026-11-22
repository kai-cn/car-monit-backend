# Java 全版本 JUnit/压测与 Java25 跨语言全量对拍报告

日期：2026-11-22

## 结论

- Java JUnit 全接口/压测：16/16 cloud run success。
- Java25 Boot4 crosslang：backend/api 两个 workflow success，baseline + python/go/cpp/rust 全部 job success。
- 本地复跑：JUnit 生成与 Java8 编译通过；workflow YAML 4/4；脚本注释 TOTAL_MISSING 0；stub 驱动 contract/load 均 rc=0。
- 跨语言对齐差异按 artifact 真实记录，未通过放宽断言隐藏；差异详见下表。

## Java JUnit run 明细

| app | jdk | branch | run | conclusion |
| --- | --- | --- | ---: | --- |
| backend | 8 | master | 44935658497 | success |
| backend | 8 | car-monit-backend-java-V3 | 44935681158 | success |
| backend | 8 | feat/backend-full-parity | 44935689795 | success |
| backend | 17 | car-monit-backend-jdk17 | 44935698618 | success |
| backend | 21 | car-monit-backend-jdk21 | 44935707508 | success |
| backend | 25 | car-monit-backend-jdk25 | 44935715571 | success |
| backend | 25 | feature-dbupgrade | 44935745038 | success |
| api | 8 | master | 44935762629 | success |
| api | 8 | car-monit-api-java-V3 | 44935825399 | success |
| api | 8 | car-monit-api-java-fix | 44935833675 | success |
| api | 17 | feature/springboot3-jdk17 | 44935842044 | success |
| api | 21 | feature/springboot3 | 44935850245 | success |
| api | 17 | car-monit-api-jdk17 | 44935860532 | success |
| api | 21 | car-monit-api-jdk21 | 44935880717 | success |
| api | 25 | car-monit-api-jdk25 | 44935895092 | success |
| api | 25 | feature-dbupgrade | 44935904207 | success |

## Java25 crosslang workflow

| app | run | conclusion |
| --- | ---: | --- |
| backend | 44983230639 | success |
| api | 44983238487 | success |

## 跨语言全接口对齐与压测

| app | lang | endpoints | status_match | exact | semantic | nondet | fails | rps(candidate/baseline) | p95(candidate/baseline) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| backend | python | 302 | 302 | 301 | 301 | 1 | 0 | 1309.10/15476.80 | 8/1 |
| backend | go | 302 | 297 | 292 | 292 | 1 | 9 | 37892.73/15476.80 | 1/1 |
| backend | cpp | 302 | 302 | 295 | 295 | 1 | 6 | 28246.50/15476.80 | 1/1 |
| backend | rust | 302 | 302 | 301 | 301 | 1 | 0 | 50321.43/15476.80 | 1/1 |
| api | python | 79 | 77 | 19 | 52 | 10 | 17 | 59.03/463.30 | 338/65 |
| api | go | 79 | 0 | 18 | 18 | 0 | 79 | 56154.17/463.30 | 1/65 |
| api | cpp | 79 | 75 | 31 | 41 | 9 | 29 | 403.40/463.30 | 61/65 |
| api | rust | 79 | 0 | 18 | 18 | 0 | 79 | 176167.93/463.30 | 0/65 |

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
