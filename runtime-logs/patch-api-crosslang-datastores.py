#!/usr/bin/env python3
"""
@description 历史脚本 patch-api-crosslang-datastores.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python patch-api-crosslang-datastores.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Docker CLI 与已启动的守护进程；Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml')
t = p.read_text(encoding='utf-8')
old = '''          docker exec -i my mysql -h127.0.0.1 -P3306 --protocol=TCP -uroot -proot -D carmonitdb < harness/scripts/v3/ops/parity/sql/schema_carmonitdb.sql
          docker exec -i my mysql -h127.0.0.1 -P3306 --protocol=TCP -uroot -proot -D carmonitdb < harness/scripts/v3/ops/parity/sql/seed_carmonitdb.sql
'''
new = '''          docker run -d --name pg -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=RuoYi -p 5432:5432 postgres:16-alpine
          for i in $(seq 1 60); do docker exec pg pg_isready -U postgres -d RuoYi >/dev/null 2>&1 && break; sleep 2; done
          export PGPASSWORD=postgres
          psql -h 127.0.0.1 -U postgres -d RuoYi -v ON_ERROR_STOP=1 -f harness/scripts/v3/ops/parity/sql/schema_jl_data01.sql >/dev/null
          gunzip -c harness/scripts/v3/ops/parity/sql/seed_jl_data01.sql.gz > /tmp/seed.sql
          psql -h 127.0.0.1 -U postgres -d RuoYi -v ON_ERROR_STOP=1 -f /tmp/seed.sql >/dev/null
          for i in $(seq 1 10); do
            docker exec -i my mysql -h127.0.0.1 -P3306 --protocol=TCP -uroot -proot < harness/scripts/v3/ops/parity/sql/mysql_dict.sql && break
            echo "mysql dict load retry $i"; sleep 3
          done
'''
assert old in t
p.write_text(t.replace(old, new, 1), encoding='utf-8')
print('patched api candidate datastores')
