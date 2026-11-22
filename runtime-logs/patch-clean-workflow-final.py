#!/usr/bin/env python3
"""
@description 修复干净跨语言 workflow 的数据库就绪顺序、JUnit jar 下载和 Go 构建入口。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python runtime-logs/patch-clean-workflow-final.py
@dependencies 修改两仓库 master 工作树中的 workflow。
"""
from pathlib import Path

PATHS = [Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml'),
         Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml')]

OLD_WAIT = '''          docker run -d --name my -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=carmonitdb -p 3306:3306 mysql:8.0 --default-authentication-plugin=mysql_native_password
          docker run -d --name rd -p 6379:6379 redis:7-alpine
          if [ '${{ inputs.app }}' = api ]; then'''
NEW_WAIT = '''          docker run -d --name my -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=carmonitdb -p 3306:3306 mysql:8.0 --default-authentication-plugin=mysql_native_password
          docker run -d --name rd -p 6379:6379 redis:7-alpine
          for i in $(seq 1 90); do docker exec my mysql -h127.0.0.1 -P3306 --protocol=TCP -uroot -proot -e 'select 1' >/dev/null 2>&1 && break; sleep 2; done
          for i in $(seq 1 30); do docker exec rd redis-cli ping >/dev/null 2>&1 && break; sleep 1; done
          if [ '${{ inputs.app }}' = api ]; then'''
OLD_AFTER = '''          fi
          for i in $(seq 1 90); do docker exec my mysql -h127.0.0.1 -P3306 --protocol=TCP -uroot -proot -e 'select 1' >/dev/null 2>&1 && break; sleep 2; done
          for i in $(seq 1 30); do docker exec rd redis-cli ping >/dev/null 2>&1 && break; sleep 1; done
'''
NEW_AFTER = '''          fi
'''

OLD_JUNIT = '''          sudo apt-get update -qq
          sudo apt-get install -y -qq junit-platform-console-standalone >/dev/null
          cp /usr/share/java/junit-platform-console-standalone.jar ../out/junit.jar
'''
NEW_JUNIT = '''          URL=https://repo.maven.apache.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.2/junit-platform-console-standalone-1.10.2.jar
          for i in 1 2 3 4; do
            curl -fsSL --retry 3 --retry-delay 5 -o ../out/junit.jar "$URL" && break
            sleep $((i*5))
          done
          test -s ../out/junit.jar
'''

OLD_GO = '''          if [ '${{ inputs.app }}' = api ]; then DIR=src/car-monit-api-go; BIN=bin/car-monit-api; CMD="./$BIN -config configs/config.yaml"; else DIR=src/car-monit-go; BIN=bin/car-monit-go; CMD="./$BIN -c configs/config.yaml"; fi
          cd "$DIR"
          go mod tidy
          go build -o "$BIN" ./cmd/server
          (cd src && go build -o "$BIN" ./cmd/server) 2>/dev/null || true
          if [ '${{ inputs.app }}' = api ]; then go build -o "$BIN" ./cmd/api; fi
          eval "$CMD" > "$GITHUB_WORKSPACE/app.log" 2>&1 &
'''
NEW_GO = '''          if [ '${{ inputs.app }}' = api ]; then DIR=src/car-monit-api-go; BIN=bin/car-monit-api; CMD="./$BIN -config configs/config.yaml"; PKG=./cmd/api; else DIR=src/car-monit-go; BIN=bin/car-monit-go; CMD="./$BIN -c configs/config.yaml"; PKG=./cmd/server; fi
          cd "$DIR"
          go mod tidy
          go build -o "$BIN" "$PKG"
          eval "$CMD" > "$GITHUB_WORKSPACE/app.log" 2>&1 &
'''

for p in PATHS:
    t = p.read_text(encoding='utf-8')
    assert OLD_WAIT in t and OLD_JUNIT in t and OLD_GO in t, p
    t = t.replace(OLD_WAIT, NEW_WAIT)
    t = t.replace(OLD_AFTER, NEW_AFTER)
    t = t.replace(OLD_JUNIT, NEW_JUNIT)
    t = t.replace(OLD_GO, NEW_GO)
    p.write_text(t, encoding='utf-8')
    print('PATCHED', p)
