# 11-results 云端对比实测结果（backend 侧）

> 2026-11-17。方法/坑点见 `11-cloud-parity-verification.md`。

## 1. backend native vs JVM（Linux，RuoYi）

| 分支 | JVM jar | native | 结论 |
| --- | --- | --- | --- |
| jdk25 | ✅ 2 端点，12327 ms / 740.1 MB | ❌ 启动 rc=1 | 见下坑点 1 |
| jdk21 | ✅ 2 端点 | ❌ build-only（探针跳过） | Boot4 native 需 JDK25 |
| jdk17 | ✅ 2 端点，12326 ms / 776.6 MB | ❌ build-only | 同上 |

### 坑点 1：backend native 启动 `masterDataSource: null` NPE
- 现象：jdk25 native 二进制启动即 rc=1，日志
  `BeanCreationException: Error creating bean with name 'masterDataSource': null` →
  `NullPointerException`。
- 定性：native image 下 Druid 动态数据源的环境变量绑定（`SPRING__DATASOURCE__DRUID__MASTER__*`）
  未被 AOT 正确处理，属 **backend native 化未完成的真实待办**（RuoYi 的 Druid + 动态数据源是
  native 化的难点）。非本验收误判，如实记录。
- JVM 基线同一配置下正常，说明配置本身正确，问题在 native 运行时。

### 坑点 2：backend 端点几乎全需认证
RuoYi 仅 `/captchaImage`（随机验证码 → NONDET）、`/` 免认证 GET；
native-vs-jvm 的接口对比只能覆盖这 2 个，故 backend 侧重**启动时间/RSS/延迟**，
79 端点全接口对比由 **api 侧**完成。

## 2. 跨语言 — Java8 vs Go/Python/Rust（backend master，run 44006210631）

| 变体 | 启动 | 峰值 RSS | 探针端点 | 结论 |
| --- | --- | --- | --- | --- |
| Java8（基线） | 903 ms | 134.4 MB | 2 | — |
| **Go** | **302 ms** | **15.3 MB** | 2 | 启动快 3×、内存省 8.8×，资源最优 |
| Rust | 启动失败 rc=1（68768ms） | 10.7 MB | 0 | 需排查启动配置/DB 连接 |
| Python | 依赖/配置失败 | — | 0 | 需排查 requirements 与环境变量 |
| C# / Kotlin / C++ | — | — | — | **仓库内无 HTTP 服务，无法对比** |

- Go 的 2 端点判 `MISSING`：Go 侧 `/captchaImage`、`/` 路径/前缀与 Java8 基线未匹配，
  需对齐路由或 context-path 才能做接口等价判定（如实记录，非 native 问题）。

## 3. 结论
1. backend native（jdk25）构建成功但**启动失败**（Druid 数据源 native 绑定），是后端 native 化的
   真实阻塞点；JVM 基线在三分支均正常启动。
2. 跨语言中 **Go 资源表现最优**（15.3MB vs Java8 134MB），启动 3× 快。
3. Java8/Go 都能起在云 runner 上，证明跨语言 harness 可用；Rust/Python 需进一步调配。
