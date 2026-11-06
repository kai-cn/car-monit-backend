"""快照 /oss 之外的业务表行数，用于证明 pathvar_matrix 的写端点探针没有改动数据。

    python tools/endpoint_parity/db_snapshot.py before
    python tools/endpoint_parity/db_snapshot.py after
    python tools/endpoint_parity/db_snapshot.py diff
"""
import subprocess
import sys
from pathlib import Path

TABLES = ['sys_user', 'sys_role', 'sys_config', 'sys_dict_data', 'sys_dict_type', 'sys_dept',
          'sys_menu', 'sys_notice', 'sys_post', 'sys_job', 'sys_job_log', 'sys_logininfor',
          'sys_oper_log', 'gen_table', 'gen_table_column', 'geometry', 'sys_file', 'sys_index_menu',
          'car_info', 'car_suspicious', 'car_white_info', 'car_warning_rule', 'car_except_record']
# 审计/日志类表本来就会被请求本身写入，不参与“没改动”的判定。
AUDIT = {'sys_oper_log', 'sys_logininfor', 'sys_job_log'}
# 快照写到 build/（已被 .gitignore 忽略），避免把临时产物提交进仓库。
PATH = Path(__file__).resolve().parent.parent.parent / 'build' / 'db_snapshot.txt'


def counts():
    out = {}
    for table in TABLES:
        result = subprocess.run(
            ['mysql', '-h', '127.0.0.1', '-P', '3307', '-uroot', '-proot', '-N', '-B', '--force',
             '-e', 'select count(*) from carmonitdb.%s' % table],
            capture_output=True, text=True)
        text = (result.stdout or '').strip()
        if text:
            out[table] = int(text)
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'before'
    if mode == 'diff':
        before = dict(
            (k, int(v)) for k, v in
            (line.split('\t') for line in PATH.read_text(encoding='utf-8').splitlines()))
        after = counts()
        changed = [(k, before[k], after[k]) for k in before
                   if k in after and after[k] != before[k] and k not in AUDIT]
        audit = [(k, before.get(k), after.get(k)) for k in after if k in AUDIT]
        print('业务表变动：', changed or '无')
        print('审计/日志表（请求本身会写）：', audit)
        return 1 if changed else 0
    snapshot = counts()
    PATH.write_text('\n'.join('%s\t%d' % kv for kv in sorted(snapshot.items())), encoding='utf-8')
    print('snapshot %s: %d 行 / %d 张表' % (mode, sum(snapshot.values()), len(snapshot)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
