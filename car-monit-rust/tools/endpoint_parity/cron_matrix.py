# -*- coding: utf-8 -*-
"""cron 表达式接受度矩阵：Java(Quartz CronExpression.isValidExpression) vs Rust。

对每条表达式：POST /monitor/job 建任务（用不触发的组避免影响调度），比较两端 msg；
建成功的再读 GET /monitor/job/{id} 比较 nextValidTime（低频表达式要求逐字一致，
高频表达式只比较“是否同一天/同一小时”）。最后删除两端建出来的行。

用法（两端已启动）：
    PARITY_USER=admin PARITY_PASSWORD=xxx python -m tools.endpoint_parity.cron_matrix
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

#: (表达式, 说明)；说明只给人看，不参与比较。
CASES = [
    ('0 0 2 * * ?', '每天 2 点'),
    ('0 0/5 * * * ?', '每 5 分钟'),
    ('0 0 2 ? * MON-FRI', '工作日'),
    ('0 0 2 ? * 2#1', '每月第 1 个周一'),
    ('0 0 2 ? * 6L', '每月最后一个周五'),
    ('0 0 2 L * ?', '每月最后一天'),
    ('0 0 2 LW * ?', '每月最后一个工作日'),
    ('0 0 2 L-3 * ?', '月末倒数第 3 天'),
    ('0 0 2 15W * ?', '最接近 15 号的工作日'),
    ('0 0 2 ? * L', 'DOW 的 L'),
    ('0 0 2 ? * SAT', '星期名'),
    ('0 0 2 ? * sat', '小写星期名'),
    ('0 0 2 ? * 7', 'SAT=7'),
    ('0 0 2 ? * 1', 'SUN=1'),
    ('0 0 2 ? * 0', 'DOW=0'),
    ('0 0 2 ? * 1-5', 'DOW 区间'),
    ('0 0 2 ? * 1,3,5', 'DOW 列表'),
    ('0 0 2 ? * 1/2', 'DOW 步长'),
    ('0 0 2 1/1 * ?', 'DOM 步长'),
    ('0 0 2 1 1 ? 2099', '7 段：带年'),
    ('0 0 2 1 1 ? *', '7 段：年=*'),
    ('0 0 2 1 1 ? 1969', '年早于 1970'),
    ('0 0 2 1 1 ? 2400', '年晚于 2299'),
    ('0 0 2 * 1-12 ?', '月份区间'),
    ('0 0 2 ? JAN ?', '月份名'),
    ('0 0 2 ? jan ?', '小写月份名'),
    ('*/0 * * * * ?', '步长 0'),
    ('0 0 2 ? * 7W', 'W 出现在 DOW'),
    ('0 0 2 ? * 5#2,6#3', '两个 #'),
    ('0 0 2 ? * 3#0', '#0'),
    ('0 0 2 ? * 3#6', '#6'),
    ('0 0 2 ? * 2-6L', '区间后接 L'),
    ('0 0 2 ? * 1LW', 'LW 前带序号'),
    ('0 0 2 0 * ?', 'DOM=0'),
    ('0 0 2 32 * ?', 'DOM=32'),
    ('0 0 2 L-31 * ?', 'L-31'),
    ('0 0 25 * * ?', '小时 25'),
    ('60 0 2 * * ?', '秒 60'),
    ('0 60 2 * * ?', '分 60'),
    ('0 0 2 * 13 ?', '月份 13'),
    ('0 0 2 * * 8', 'DOW=8'),
    ('? 0 2 * * ?', '秒位用 ?'),
    ('0 0 2 * ? 1', '月份位用 ?'),
    ('bogus', '纯垃圾'),
    ('', '空串'),
    ('   ', '只有空格'),
    ('0 0 2 * *', '只有 6 段'),
    ('0 0 2 * * ? 2099 2100', '8 段'),
    ('0  0  2 * * ?', '多个空格'),
    (' 0 0 2 * * ? ', '前后空格'),
    ('0 0 2 * * ?x', '尾部垃圾'),
    ('0 0 2 1W,3 * ?', '列表里混 W'),
    ('0 0 2 LW,1 * ?', '列表里混 LW'),
    ('0 0 2 ? * 5#2,6', '# 后再接值'),
    ('0 0 2 ? * 5,6#2', '值后再接 #'),
    ('0 0 2 ? * ?', '日月周双 ?'),
    ('0 0 2 * * *', '日月周都指定'),
    ('0 0 2 ? * *', 'DOM=? DOW=*'),
    ('0 0 2 * 1 ?', 'DOM=* MONTH=1 DOW=?'),
]


def normalize(msg):
    """两端共用同一张表，报错里嵌的自增 job_id 必然不同，归一后再比。"""
    if not isinstance(msg, str):
        return msg
    return re.sub(r'TASK_CLASS_NAME\d+', 'TASK_CLASS_NAME{id}', msg)


def post_cron(base: str, token: str, index: int, expr: str) -> dict:
    """建任务 -> 读 nextValidTime -> 删任务，返回可比较的结果。"""
    name = 'parity-cron-%d' % index
    body = {
        'jobName': name, 'jobGroup': 'DEFAULT',
        'invokeTarget': 'ryTask.ryNoParams', 'cronExpression': expr,
        'misfirePolicy': '3', 'concurrent': '1',
        # Java: insertJob 会先把 status 改成 PAUSE("1")，所以这里故意传 "0" 验证覆盖行为。
        'status': '0',
    }
    _, _, raw = http('POST', base + '/monitor/job', token=token, body=body, timeout=60)
    try:
        created = json.loads(raw)
    except Exception:
        return {'msg': 'NON-JSON %s' % raw[:80].decode('utf-8', 'replace')}
    out = {'msg': normalize(created.get('msg'))}
    _, _, raw = http('GET', base + '/monitor/job/list?jobName=' + name, token=token, timeout=60)
    rows = (json.loads(raw) or {}).get('rows') or []
    if rows:
        # 「永不触发」的行两端都会留在库里（Java 的 SchedulerException 是 checked 异常，
        # @Transactional 默认不回滚），所以无论 msg 是什么都要按名字清干净。
        out['next'] = rows[0].get('nextValidTime')
        out['stored'] = rows[0].get('cronExpression')
        out['status'] = rows[0].get('status')
        out['misfire'] = rows[0].get('misfirePolicy')
        for row in rows:
            http('DELETE', base + '/monitor/job/%s' % row['jobId'], token=token, timeout=60)
    return out


def same(a: dict, b: dict) -> bool:
    if a.get('msg') != b.get('msg'):
        return False
    x, y = a.get('next'), b.get('next')
    if (x is None) != (y is None):
        return False
    if x is None:
        return True
    # 两端取“现在”的时刻差了几十毫秒，高频表达式可能跨一个触发点，放宽到同日同时。
    if x == y:
        return True
    return x[:13] == y[:13]


def main() -> int:
    tj, sj, _ = login(JAVA)
    tr, sr, _ = login(RUST)
    if not tj or not tr:
        print('登录失败', sj, sr)
        return 2
    bad = 0
    for index, (expr, note) in enumerate(CASES):
        started = time.time()
        a = post_cron(JAVA, tj, index, expr)
        b = post_cron(RUST, tr, index, expr)
        ok = same(a, b)
        bad += 0 if ok else 1
        tag = '==' if ok else '!='
        print('%s %-24r java=%-46s rust=%-46s %s' % (
            tag, expr, json.dumps(a, ensure_ascii=False),
            json.dumps(b, ensure_ascii=False), note))
        if time.time() - started < 0.2:
            time.sleep(0.2)
    print('\n不一致 %d / %d' % (bad, len(CASES)))
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
