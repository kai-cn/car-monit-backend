"""功能更全的本地假 S3：给 /oss/** 的成功路径做双端对拍用。

真实 MinIO（`oss.endpoint=172.30.100.102:9002`）不在这个网络里，Java 侧的
`AmazonS3Client` 调用会一直挂着，`/oss/bucket`、`/oss/object/{b}/{o}` 这些端点的**成功形态**
因此没法直接看。这里补齐 AWS S3 REST 的最小响应集（ListAllMyBuckets / ListBucket /
HEAD bucket / PUT / GET / DELETE object），并且**不验签**（只关心 Java 与 Rust 拿到同样的
上游数据时出参是否一致）：

    python tools/endpoint_parity/fake_s3_full.py --port 9124
两端启动参数都带上：--oss.endpoint=http://127.0.0.1:9124

每次收到的请求会打到 stdout（方法、路径、查询串、Authorization 里的 Credential scope），
可以据此核对两端签名的区域与路径风格是否一致。
"""
import argparse
import hashlib
import re
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

CREATION = '2021-05-06T00:36:40.000Z'
LAST_MODIFIED = '2024-03-01T08:00:00.000Z'
BUCKETS = ['developer', 'parity-bucket']
OBJECTS = {
    'developer': [
        ('a/b.txt', b'parity-bytes', '"5c1a8f0deadbeef"', 'STANDARD'),
        ('a/c.log', b'log-bytes', '"0ffbeef1234567"', 'REDUCED_REDUNDANCY'),
    ]
}
LOCK = threading.Lock()

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--port', type=int, default=9124)
ARGS = parser.parse_args()


def note(line):
    print('%s %s' % (datetime.now(timezone.utc).strftime('%H:%M:%S'), line), flush=True)


def buckets_xml():
    entries = ''.join(
        '<Bucket><Name>%s</Name><CreationDate>%s</CreationDate></Bucket>' % (name, CREATION)
        for name in BUCKETS)
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<ListAllMyBucketsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
            '<Owner><ID>abc123</ID><DisplayName>parity</DisplayName></Owner>'
            '<Buckets>%s</Buckets></ListAllMyBucketsResult>' % entries).encode()


def list_objects_xml(bucket, prefix):
    rows = ''
    items = [item for item in OBJECTS.get(bucket, []) if item[0].startswith(prefix or '')]
    for key, body, etag, storage in items:
        rows += ('<Contents><Key>%s</Key><LastModified>%s</LastModified>'
                 '<ETag>%s</ETag><Size>%d</Size><StorageClass>%s</StorageClass>'
                 '<Owner><ID>abc123</ID><DisplayName>parity</DisplayName></Owner>'
                 '</Contents>') % (key, LAST_MODIFIED, etag, len(body), storage)
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
            '<Name>%s</Name><Prefix>%s</Prefix><KeyCount>%d</KeyCount><MaxKeys>1000</MaxKeys>'
            '<IsTruncated>false</IsTruncated>%s</ListBucketResult>'
            % (bucket, prefix or '', len(items), rows)).encode()


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def _reply(self, code, body=b'', ctype='application/xml', extra=None):
        self.send_response(code)
        self.send_header('Content-Length', str(len(body)))
        if body:
            self.send_header('Content-Type', ctype)
        self.send_header('x-amz-request-id', 'FAKEREQUEST')
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _err(self, code, s3code, message):
        body = ('<?xml version="1.0" encoding="UTF-8"?><Error><Code>%s</Code>'
                '<Message>%s</Message><Resource>%s</Resource><RequestId>FAKEREQUEST</RequestId>'
                '</Error>') % (s3code, message, self.path)
        self._reply(code, body.encode())

    def _record(self, method):
        parsed = urlparse(self.path)
        auth = self.headers.get('Authorization') or ''
        match = re.search(r'Credential=([^/]+)/(\d{8})/([^/]*)/s3/aws4_request', auth)
        scope = '-'.join(match.group(i) for i in (2, 3)) if match else 'no-auth'
        note('%s %s query=%s scope=%s sha256=%s host=%s' % (
            method, parsed.path, parsed.query, scope,
            self.headers.get('x-amz-content-sha256', '-')[:12],
            self.headers.get('Host', '-')))
        return parsed

    def do_GET(self):
        parsed = self._record('GET')
        query = parse_qs(parsed.query)
        parts = [p for p in parsed.path.split('/') if p]
        with LOCK:
            if not parts:
                return self._reply(200, buckets_xml())
            bucket = parts[0]
            if len(parts) == 1:
                return self._reply(200, list_objects_xml(bucket, (query.get('prefix') or [''])[0]))
            key = '/'.join(parts[1:])
            for name, body, etag, _storage in OBJECTS.get(bucket, []):
                if name == key:
                    return self._reply(200, body, 'text/plain', {
                        'ETag': etag,
                        'Last-Modified': 'Fri, 01 Mar 2024 08:00:00 GMT',
                    })
            return self._err(404, 'NoSuchKey', 'The specified key does not exist.')

    def do_HEAD(self):
        parsed = self._record('HEAD')
        parts = [p for p in parsed.path.split('/') if p]
        with LOCK:
            if not parts:
                return self._reply(200)
            bucket = parts[0]
            if bucket not in BUCKETS:
                return self._err(404)
            if len(parts) == 1:
                return self._reply(200)
            key = '/'.join(parts[1:])
            for name, body, etag, _storage in OBJECTS.get(bucket, []):
                if name == key:
                    return self._reply(200, b'', 'application/xml', {
                        'Content-Length': str(len(body)),
                        'ETag': etag,
                        'Last-Modified': 'Fri, 01 Mar 2024 08:00:00 GMT',
                    })
            return self._err(404)

    def do_PUT(self):
        parsed = self._record('PUT')
        length = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(length) if length else b''
        parts = [p for p in parsed.path.split('/') if p]
        with LOCK:
            if len(parts) >= 2:
                note('PUT store %s len=%d' % (parsed.path, len(body)))
                return self._reply(200, b'', 'application/xml',
                                   {'ETag': '"%s"' % hashlib.md5(body).hexdigest()})
            return self._reply(200, b'', 'application/xml',
                               {'Location': '/' + parts[0] if parts else '/'})

    def do_DELETE(self):
        self._record('DELETE')
        return self._reply(204)


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', ARGS.port), Handler)
    print('fake-s3-full on %d' % ARGS.port, flush=True)
    server.serve_forever()
