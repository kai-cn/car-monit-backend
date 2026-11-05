# -*- coding: utf-8 -*-
"""sys_job 的 invokeTarget 行为矩阵：Java(Quartz + JobInvokeUtil) vs Rust。

对每个目标：建一个暂停任务 -> 立即执行 -> 读 sys_job_log -> 删任务，
比较两端 jobLog 的 status / jobMessage / exceptionInfo。

归一化口径（这些差异不是行为差异）：
  * `jobMessage` 里的耗时毫秒数（两端机器/任务快慢不同）；
  * `exceptionInfo` 只比**首行**（Java 写完整栈，Rust 无法复刻栈帧）；
  * 报错文案里嵌的自增 jobId（两端共用同一张表，号必然交错）。

用法（两端已启动）：
    PARITY_USER=admin PARITY_PASSWORD=xxx python -m tools.endpoint_parity.job_invoke_matrix
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client import http, login  # noqa: E402

JAVA = os.environ.get('PARITY_JAVA_BASE', 'http://127.0.0.1:9988')
RUST = os.environ.get('PARITY_RUST_BASE', 'http://127.0.0.1:9990')

# 2099 年才触发，跑批期间不会自己跑；同时验证「7 段 + ?」在两端都被接受。
CRON = '0 0 0 1 1 ? 2099'

TARGETS = [
    # 本仓库已迁移的任务
    'ryTask.ryNoParams()',
    'ryTask.ryParams(\'ry\')',
    'ryTask.ryMultipleParams(\'ry\', true, 2000L, 316.50D, 100)',
    'ryTask.ryNoParams',
    'partitionMaintenanceTask.createFuturePartitions()',
    'trackTask.syncHistoryTrackNoCar()',
    'orgTask.syncOrgInfo()',
    # 反射语义：未知 bean / 未知方法 / 类型不匹配
    'noSuchBean.foo()',
    'ryTask.noSuchMethod()',
    'ryTask.ryNoParams(abc)',
    'ryTask.ryParams(\'a,b\')',
    'ryTask.ryParams(1)',
    'ryTask.ryMultipleParams(\'ry\', TRUE, 2000L, 316.50D, 100)',
    'ryTask.ryParams(\'ry\', \'x\')',
    # 类全名形式：Java 走 Class.forName(...).newInstance()，新实例没有注入依赖
    'com.ruoyi.quartz.task.RyTask.ryNoParams()',
    'com.ruoyi.quartz.task.RyTask.ryParams(\'ry\')',
    'com.ruoyi.quartz.task.TrackTask.syncHistoryTrack()',
    'com.example.MissingBean.ryNoParams()',
    # 参数解析词表：Long/Double/Boolean/空串/小数
    'ryTask.ryParams()',
    'ryTask.ryParams(2000L)',
    'ryTask.ryParams(316.50D)',
    'ryTask.ryParams(true)',
    'ryTask.ryParams(\'\')',
    'ryTask.ryParams(1.5)',
    # 单参数带点的 bean 名（isValidClassName 数点 > 1 才算类名）
    'ry.Task.ryNoParams()',
]


def normalize(value):
    if not isinstance(value, str):
        return value
    value = re.sub(r'TASK_CLASS_NAME\d+', 'TASK_CLASS_NAME{id}', value)
    value = re.sub(r'总共耗时：\d+毫秒', '总共耗时：{ms}毫秒', value)
    return value


def first_line(value):
    if not isinstance(value, str):
        return value
    return normalize(value.splitlines()[0] if value.splitlines() else value)


def probe(base: str, token: str, index: int, target: str) -> dict:
    name = 'parity-job-%d' % index
    body = {
        'jobName': name, 'jobGroup': 'DEFAULT', 'invokeTarget': target,
        'cronExpression': CRON, 'misfirePolicy': '3', 'concurrent': '1', 'status': '1',
    }
    _, _, raw = http('POST', base + '/monitor/job', token=token, body=body, timeout=60)
    try:
        created = json.loads(raw)
    except Exception:
        return {'add': 'NON-JSON %s' % raw[:80].decode('utf-8', 'replace')}
    out = {'add': normalize(created.get('msg'))}
    _, _, raw = http('GET', base + '/monitor/job/list?jobName=' + name, token=token, timeout=60)
    rows = (json.loads(raw) or {}).get('rows') or []
    if not rows:
        # 建不出来：只需要 add 的报错文案一致（库里也没有行）。
        return out if created.get('code') != 200 else dict(out, list='查不到刚建的任务')
    job_id = rows[0]['jobId']
    _, _, raw = http('PUT', base + '/monitor/job/run', token=token,
                     body={'jobId': job_id, 'jobGroup': 'DEFAULT'}, timeout=120)
    try:
        out['run'] = normalize(json.loads(raw).get('msg'))
    except Exception:
        out['run'] = 'NON-JSON'
    time.sleep(2.5)
    _, _, raw = http('GET', base + '/monitor/jobLog/list?jobName=' + name, token=token, timeout=60)
    logs = (json.loads(raw) or {}).get('rows') or []
    if logs:
        row = logs[0]
        out['status'] = row.get('status')
        out['msg'] = normalize(row.get('jobMessage'))
        out['group'] = row.get('jobGroup')
        out['exc'] = first_line(row.get('exceptionInfo'))
    else:
        out['log'] = '无 jobLog 记录'
    # 清理：sys_job 与 sys_job_log 都按本次建的行删掉，失败也不影响结论。
    for row in logs:
        http('DELETE', base + '/monitor/jobLog/%s' % row['jobLogId'], token=token, timeout=60)
    http('DELETE', base + '/monitor/job/%s' % job_id, token=token, timeout=60)
    return out


def main() -> int:
    tj, sj, _ = login(JAVA)
    tr, sr, _ = login(RUST)
    if not tj or not tr:
        print('登录失败', sj, sr)
        return 2
    bad = 0
    for index, target in enumerate(TARGETS):
        a = probe(JAVA, tj, index, target)
        b = probe(RUST, tr, index, target)
        same = a == b
        bad += 0 if same else 1
        print(('==' if same else '!=') + '  ' + target)
        print('    java: ' + json.dumps(a, ensure_ascii=False))
        if not same:
            print('    rust: ' + json.dumps(b, ensure_ascii=False))
    print('\n不一致 %d / %d' % (bad, len(TARGETS)))
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
