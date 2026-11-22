#!/usr/bin/env python3
"""
@description 为关键生成脚本补函数级说明，并让生成的 Java 套件自带文件/类/方法 Javadoc。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python patch-production-function-docs.py
@dependencies 只改写 D:\\work\\runtime-logs 下的固定脚本，随后复制到两仓库 harness 目录。
"""
from pathlib import Path

BASE = Path(r'D:\work\runtime-logs')

gen = BASE / 'generate_junit_suite.py'
t = gen.read_text(encoding='utf-8')
t = t.replace(
    "CONTRACT = r'''package com.ruoyi.parity.generated;",
    """CONTRACT = r'''/**
 * @description 全接口 HTTP 契约套件，对每个端点做两次请求并记录可达性、状态码、字节数、延迟、正文片段与稳定性。
 * @author AI Assistant
 * @date 2026-11-22 23:45:04
 * @usage 由 generate_junit_suite.py 生成，通过 JUnit Platform Console 执行；OUT_DIR/BASE_URL/ENDPOINT_HEADERS 由环境变量注入。
 * @dependencies JDK 8+、JUnit 5 Platform Console；不依赖被测服务源码。
 */
package com.ruoyi.parity.generated;""", 1)
t = t.replace(
    "LOAD = r'''package com.ruoyi.parity.generated;",
    """LOAD = r'''/**
 * @description 有界并发端点压测套件，记录吞吐、延迟分位数、传输错误与业务状态码分布。
 * @author AI Assistant
 * @date 2026-11-22 23:45:04
 * @usage 由 generate_junit_suite.py 生成，通过 JUnit Platform Console 执行；LOAD_THREADS/LOAD_SECONDS/LOAD_WARMUP_SECONDS 控制压测规模。
 * @dependencies JDK 8+、JUnit 5 Platform Console；BASE_URL 指向被测服务。
 */
package com.ruoyi.parity.generated;""", 1)
t = t.replace(
    "/** Generated full-endpoint HTTP contract suite. No business code dependency. */\npublic class EndpointContractTest {",
    """/**
 * 全接口契约测试类，按端点清单动态生成测试；结果写入 junit-contract.json。
 */
public class EndpointContractTest {""", 1)
t = t.replace(
    "    @TestFactory\n    Stream<DynamicTest> allEndpoints() {",
    """    /**
     * 为每个端点生成一个动态测试。
     * @returns 动态测试流；每个测试记录一次可达性证据，不把业务 4xx/5xx 当作框架失败。
     * @sideEffect 向 RESULTS 线程安全列表写入端点结果。
     */
    @TestFactory
    Stream<DynamicTest> allEndpoints() {""", 1)
t = t.replace(
    "/** Generated bounded-concurrency load suite. */\npublic class EndpointLoadTest {",
    """/**
 * 有界并发压测类，按端点清单循环请求；结果写入 junit-load.json。
 */
public class EndpointLoadTest {""", 1)
t = t.replace(
    "    @Test\n    void runLoad() throws Exception {",
    """    /**
     * 执行限时压测并汇总吞吐、延迟分位数和业务状态码。
     * @throws InterruptedException 压测线程被中断时由 JUnit 标记为失败。
     * @sideEffect 写出 junit-load.json 报告文件。
     */
    @Test
    void runLoad() throws Exception {""", 1)
t = t.replace(
    "def java_array(paths):\n    items = []",
    """def java_array(paths: list[str]) -> str:
    \"\"\"
    将端点列表转换为 Java String 数组字面量。

    @param paths: 非空端点路径列表，顺序决定动态测试执行顺序。
    @returns 可直接嵌入 Java 源码的数组初始化表达式。
    \"\"\"
    items = []""", 1)
t = t.replace(
    "def main():\n    ap = argparse.ArgumentParser()",
    """def main() -> None:
    \"\"\"
    读取端点清单并生成契约/压测 Java 源码。

    @raises SystemExit: 端点清单为空时终止，避免生成空测试套件。
    @sideEffect 在输出目录写入 EndpointContractTest.java 与 EndpointLoadTest.java。
    \"\"\"
    ap = argparse.ArgumentParser()""", 1)
gen.write_text(t, encoding='utf-8')
print('patched', gen)

cl = BASE / 'compare_load.py'
t = cl.read_text(encoding='utf-8')
t = t.replace(
    "def main():\n    ap = argparse.ArgumentParser()",
    """def main() -> None:
    \"\"\"
    对比基线与候选的压测报告，并写出 JSON/Markdown 摘要。

    @sideEffect 写入 --out 指定的 JSON 与 --md 指定的 Markdown 文件。
    \"\"\"
    ap = argparse.ArgumentParser()""", 1)
cl.write_text(t, encoding='utf-8')
print('patched', cl)

pc = BASE / 'parity_compare.py'
t = pc.read_text(encoding='utf-8')
t = t.replace("def norm(x):", "def norm(x: object) -> object:", 1)
t = t.replace("def classify(body):", "def classify(body: str) -> tuple[str, object]:", 1)
t = t.replace("def main():", "def main() -> None:", 1)
t = t.replace("    def avg(es, f):", "    def avg(es: list[dict], f: str) -> float | None:", 1)
pc.write_text(t, encoding='utf-8')
print('patched', pc)
