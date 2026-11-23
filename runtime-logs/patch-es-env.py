#!/usr/bin/env python3
"""Patch api Elasticsearch host defaults for WSL/CI compatibility."""
from pathlib import Path
p=Path('/home/dev/IdeaProjects/car-monit-api/pro-business-api/src/main/resources/application.yml')
raw=p.read_bytes(); crlf=b'\r\n' in raw
t=raw.decode('utf-8',errors='replace')
t=t.replace('  host: localhost\n  port: 9200\n  scheme: http', '  host: ${ELASTICSEARCH_HOST:localhost}\n  port: ${ELASTICSEARCH_PORT:9200}\n  scheme: http')
data=(t.replace('\r\n','\n').replace('\n','\r\n') if crlf else t).encode('utf-8')
p.write_bytes(data)
print('OK',p)
