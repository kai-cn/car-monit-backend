#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本地假 S3（MinIO 语义的最小子集），并且**自己验签**。

存在的理由：真实的 MinIO（172.30.100.102:9002）不在这个网络里，而 C++ 侧新写的 SigV4
签名不能只靠"和自己的实现再对一遍"来证明。这里的验签用的是 Python 标准库
hmac/hashlib 的第二套独立实现：它从**收到的请求**里重建规范请求（路径按收到的原始字节、
SignedHeaders 按 Authorization 里声明的那份），算出的签名和客户端给的对不上就返 403。
所以 PUT/GET/DELETE 能走通，就同时证明了签名的结构与传输的细节都是对的。

记录每一笔操作到 stdout（由调用方重定向到 logs/fake_s3.log），供 verify 脚本断言。

用法：python scripts/fake_s3.py <port> <accessKey> <secretKey>
"""
import hashlib
import hmac
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9123
AK = sys.argv[2] if len(sys.argv) > 2 else "jtwl_access_key"
SK = sys.argv[3] if len(sys.argv) > 3 else "minio.prod"

STORE = {}
LOCK = threading.Lock()
HITS = []


def h(key, msg):
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def signature(headers, method, uri_path, signed_list):
    amz_date = headers.get("x-amz-date", "")
    date_stamp = amz_date[:8]
    canonical_headers = "".join(
        "%s:%s\n" % (k, re.sub(r"\s+", " ", headers[k]).strip())
        for k in signed_list)
    payload = headers.get("x-amz-content-sha256", "")
    # 规范请求里"首部块"与"SignedHeaders"之间必须有一个空行：
    # 首部块自带结尾 \n，再补一个 \n，然后才是 SignedHeaders 与负载哈希
    cr = "%s\n%s\n%s\n%s\n%s\n%s" % (method, uri_path, "", canonical_headers,
                                     ";".join(signed_list), payload)
    scope = "%s/us-east-1/s3/aws4_request" % date_stamp
    sts = "\n".join(["AWS4-HMAC-SHA256", amz_date, scope,
                     hashlib.sha256(cr.encode()).hexdigest()])
    k = h(("AWS4" + SK).encode(), date_stamp)
    k = h(k, "us-east-1")
    k = h(k, "s3")
    k = h(k, "aws4_request")
    return hmac.new(k, sts.encode(), hashlib.sha256).hexdigest(), cr


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # 静音默认访问日志
        pass

    def _hdrs(self):
        return {k.lower(): v for k, v in self.headers.items()}

    def _reply(self, code, body=b"", ctype="application/xml", extra=None):
        self.send_response(code)
        if body:
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _err(self, code, s3code, msg):
        body = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?><Error><Code>%s</Code>"
                "<Message>%s</Message><Resource>%s</Resource></Error>"
                % (s3code, msg, self.path)).encode("utf-8")
        self._reply(code, body)

    def _check(self, body):
        hs = self._hdrs()
        auth = hs.get("authorization", "")
        m = re.match(r"AWS4-HMAC-SHA256 Credential=([^/]+)/([\d]{8})/([^/]+)/s3/aws4_request, "
                     r"SignedHeaders=([^,]+), Signature=([0-9a-f]{64})", auth)
        if not m:
            return "no-auth"
        cred_ak, _date, region, signed, want = m.groups()
        if cred_ak != AK:
            return "bad-ak"
        if region != "us-east-1":
            return "bad-region"
        got, _cr = signature(hs, self.command, self.path, signed.split(";"))
        if got != want:
            return "sig-mismatch"
        # 负载哈希也要对得上，否则 body 与签名不一致
        if hs.get("x-amz-content-sha256") != hashlib.sha256(body).hexdigest():
            return "payload-mismatch"
        return None

    def do_PUT(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0) or 0))
        bad = self._check(body)
        with LOCK:
            if bad:
                HITS.append("PUT reject %s %s" % (self.path, bad))
                self._err(403, "SignatureDoesNotMatch", bad)
                return
            key = self.path.lstrip("/")
            STORE[key] = (body, self._hdrs().get("content-type", ""))
            HITS.append("PUT ok %s len=%d ct=%s" % (key, len(body),
                                                    self._hdrs().get("content-type", "")))
        self._reply(200, b"", "application/xml",
                    {"ETag": '"%s"' % hashlib.md5(body).hexdigest()})

    def do_GET(self):
        bad = self._check(b"")
        with LOCK:
            if bad:
                HITS.append("GET reject %s %s" % (self.path, bad))
                self._err(403, "SignatureDoesNotMatch", bad)
                return
            obj = STORE.get(self.path.lstrip("/"))
            if obj is None:
                HITS.append("GET miss %s" % self.path)
                self._err(404, "NoSuchKey", "The specified key does not exist.")
                return
            body, ct = obj
            HITS.append("GET ok %s len=%d" % (self.path.lstrip("/"), len(body)))
        self._reply(200, body, ct or "application/octet-stream")

    def do_DELETE(self):
        bad = self._check(b"")
        with LOCK:
            if bad:
                HITS.append("DEL reject %s %s" % (self.path, bad))
                self._err(403, "SignatureDoesNotMatch", bad)
                return
            existed = STORE.pop(self.path.lstrip("/"), None) is not None
            HITS.append("DEL %s %s" % ("ok" if existed else "gone", self.path.lstrip("/")))
        self._reply(204)


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print("fake-s3 listening on %d (ak=%s)" % (PORT, AK), flush=True)
    srv.serve_forever()
