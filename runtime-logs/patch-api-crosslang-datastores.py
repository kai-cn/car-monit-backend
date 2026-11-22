#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-api-crosslang-datastores.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Patch api crosslang workflow candidate datastores to api fixtures."""
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
