#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实机验证：/system/file 的 9 个上传/下载端点（对象存储走 scripts/fake_s3.py）。

前置（两条命令）：
    python scripts/fake_s3.py 9123 jtwl_access_key minio.prod
    CM_SERVER_PORT=9992 ./build/car-monit-cpp.exe --config logs/cfg_fake
cfg_fake 是把 config/ 拷一份再追加 oss.endpoint=http://127.0.0.1:9123 得来的
（真实 MinIO 172.30.100.102:9002 不在这个网络里，见 COMPATIBILITY.md §5.4）。

fake_s3 会用 Python 标准库**独立重算 SigV4 签名**，对不上就 403，
所以下面每次成功的 PUT/GET/DELETE 都顺带证明了签名的正确性。

用法：python scripts/verify_sys_file.py [port] [token]
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9992
TOKEN = sys.argv[2] if len(sys.argv) > 2 else ""
BASE = "http://127.0.0.1:%d" % PORT
PROFILE = os.environ.get("CM_PROFILE", "D:/ruoyi/uploadPath")

ok = bad = 0
CREATED_IDS = []


def check(label, cond, detail=""):
    global ok, bad
    if cond:
        ok += 1
        print("PASS  " + label + ("  |  " + str(detail)[:160] if detail else ""))
    else:
        bad += 1
        print("FAIL  " + label + "  |  " + str(detail)[:360])


def req(path, method="GET", token=None, body=None, ctype=None):
    r = urllib.request.Request(BASE + path, method=method)
    t = TOKEN if token is None else token
    if t:
        r.add_header("Authorization", "Bearer " + t)
    data = body
    if isinstance(data, str):
        data = data.encode("utf-8")
    if data is not None and ctype:
        r.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(r, data=data, timeout=60) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def multipart(fields, files):
    """fields: [(name,value)]  files: [(name,filename,content)]"""
    b = "----qoderboundary42"
    out = b""
    for n, v in fields:
        out += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"\r\n\r\n%s\r\n"
                % (b, n, v)).encode("utf-8")
    for n, fn, content in files:
        out += ("--%s\r\nContent-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
                "Content-Type: application/octet-stream\r\n\r\n" % (b, n, fn)).encode("utf-8")
        out += content + b"\r\n"
    out += ("--%s--\r\n" % b).encode("utf-8")
    return out, "multipart/form-data; boundary=" + b


def upload(path, files, fields=None, extra_fields=None):
    body, ct = multipart(list(fields or []), files)
    st, hdr, raw = req(path, method="POST", body=body, ctype=ct)
    try:
        return st, json.loads(raw.decode("utf-8"))
    except Exception:
        return st, {"raw": raw[:200]}


def post_json(path, payload):
    st, _h, raw = req(path, method="POST", body=json.dumps(payload, ensure_ascii=False),
                      ctype="application/json;charset=UTF-8")
    try:
        return st, json.loads(raw.decode("utf-8"))
    except Exception:
        return st, {"raw": raw[:200]}


def mysql(sql):
    r = subprocess.run(["mysql", "-h", "127.0.0.1", "-P", "3307", "-uroot", "-proot",
                        "carmonitdb", "-N", "-B", "-e", sql], capture_output=True)
    out = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "replace"))
    return out.splitlines() if out else []


def track_rows():
    for i in mysql("select id from sys_file where original like 'qoder\\_%'"):
        CREATED_IDS.append(i)


# ---------------------------------------------------------------- 1) upload（白名单命中）
PDF = b"%PDF-1.4 qoder-sys-file-probe"
st, j = upload("/system/file/upload", [("files", "qoder_a.pdf", PDF)])
check("upload 200 + 信封 msg,code,data", st == 200 and list(j.keys()) == ["msg", "code", "data"]
      and j.get("code") == 200 and j.get("msg") == "操作成功", j)
d0 = (j.get("data") or [{}])[0]
check("map 的键序是 HashMap 桶序 bucketName,fileName,id,url",
      list(d0.keys()) == ["bucketName", "fileName", "id", "url"], list(d0.keys()))
check("桶固定为 oss.bucketName=developer", d0.get("bucketName") == "developer", d0)
key = d0.get("fileName", "")
check("对象名 = 32 位无横线 uuid + '.' + 原扩展名（保留大小写）",
      len(key.split(".")[0]) == 32 and key.endswith(".pdf"), key)
check("url = /system/file/developer/<key>",
      d0.get("url") == "/system/file/developer/" + key, d0.get("url"))
check("id 是字符串形态的雪花（19 位数字，不是 JSON number）",
      isinstance(d0.get("id"), str) and d0["id"].isdigit() and len(d0["id"]) >= 15, d0.get("id"))

st2, h2, b2 = req("/system/file/developer/" + urllib.parse.quote(key))
check("下载回来的字节与上传的一致（假 S3 独立验签通过 = SigV4 正确）",
      st2 == 200 and b2 == PDF, (st2, len(b2)))
check("下载 Content-Type 是 application/octet-stream; charset=UTF-8",
      h2.get("Content-Type") == "application/octet-stream; charset=UTF-8", h2.get("Content-Type"))
row = mysql("select file_name, type, original, file_size, del_flag from sys_file where id=%s" % d0["id"])
check("sys_file 落库：type 是小写扩展名、original 是原始名、del_flag=0",
      row and row[0].split("\t")[1:4] == ["pdf", "qoder_a.pdf", str(len(PDF))]
      and row[0].endswith("\t0"), row)

# ---------------------------------------------------------------- 2) upload（白名单不命中）
st3, j3 = upload("/system/file/upload", [("files", "qoder_b.exe", b"MZ\x90\x00")])
d3 = (j3.get("data") or [{}])[0]
check("扩展名不在白名单：仍然返回 map，但 id 是字符串 \"-1\"",
      d3.get("id") == "-1" and list(d3.keys()) == ["bucketName", "fileName", "id", "url"], d3)
st4, _h4, b4 = req("/system/file/" + urllib.parse.quote(d3["bucketName"]) + "/" +
                   urllib.parse.quote(d3["fileName"]))
check("未命中的文件没有 PUT，下载走 Java 的\"200 + 空 body\"",
      st4 == 200 and b4 == b"", (st4, len(b4)))
n = mysql("select count(1) from sys_file where id=%s" % "-1")
check("未命中不写库", n and n[0] == "0", n)

# ---------------------------------------------------------------- 3) upload 多文件 + PUT 失败留孤儿行
st5, j5 = upload("/system/file/upload", [("files", "qoder_c.pdf", b"x" * 10),
                                          ("files", "qoder_d.pdf", b"y" * 20)])
check("多文件返回两个 map", st5 == 200 and len(j5.get("data", [])) == 2, len(j5.get("data", [])))

# ---------------------------------------------------------------- 4) uploadPdf 的两个分支
st6, j6 = upload("/system/file/uploadPdf", [("files", "qoder_e.pdf", PDF),
                                             ("files", "qoder_f.docx", b"PK\x03\x04docx")])
data6 = j6.get("data", [])
check("uploadPdf：pdf 走桶（有 id 键）", len(data6) >= 1 and list(data6[0].keys()) ==
      ["bucketName", "fileName", "id", "url"], data6[:1])
check("uploadPdf：非 pdf 的 map 少一个 id 键（Word 转 PDF 整段在 Java 里被注释）",
      len(data6) >= 2 and list(data6[1].keys()) == ["bucketName", "fileName", "url"], data6[1:2])
found = []
for root, _dirs, fs in os.walk(PROFILE + "/upload"):
    for f in fs:
        if f.endswith(".docx") and f in data6[1]["fileName"]:
            found.append(os.path.join(root, f))
check("非 pdf 落到 profile/upload/<uuid>/<key>，字节原样",
      found and open(found[0], "rb").read() == b"PK\x03\x04docx", found)
st7, _h7, b7 = req("/system/file/developer/" + urllib.parse.quote(data6[0]["fileName"]))
check("pdf 那份确实进了桶", st7 == 200 and b7 == PDF, (st7, len(b7)))
# 大写 .PDF 走的是"非 PDF"分支：Java 的比较是 ext.equals("pdf")，不忽略大小写
st8, j8 = upload("/system/file/uploadPdf", [("files", "qoder_g.PDF", PDF)])
check("uploadPdf 的扩展名判断区分大小写：.PDF 也走本地分支（无 id 键）",
      (j8.get("data") or [{}])[0].get("id") is None, j8.get("data"))

# ---------------------------------------------------------------- 5) uploadSupplier
st9, j9 = upload("/system/file/uploadSupplier",
                [("files", "qoder_h.pdf", PDF), ("files", "qoder_i.pdf", PDF)],
                fields=[("bussNames", "合同"), ("bussNames", "发票")])
d9 = j9.get("data", [])
check("uploadSupplier：files 与 bussNames 按下标一一对应",
      st9 == 200 and len(d9) == 2 and all(x.get("id", "").isdigit() for x in d9), d9)
bn = mysql("select buss_name from sys_file where id in (%s,%s)" % (d9[0]["id"], d9[1]["id"]))
check("buss_name 被写进 sys_file（只有这条路径赋值）", sorted(x.split("\t")[0] for x in bn) ==
      sorted(["合同", "发票"]), bn)
st10, j10 = upload("/system/file/uploadSupplier", [("files", "qoder_j.pdf", PDF),
                                                    ("files", "qoder_k.pdf", PDF)],
                   fields=[("bussNames", "只有一个")])
check("bussNames 比 files 少：越界在 try 之外 ⇒ 整体 code:500 且没有 data",
      j10.get("code") == 500 and "out of bounds" in str(j10.get("msg")) and "data" not in j10, j10)

# ---------------------------------------------------------------- 6) uploadFileEnc
st11, j11 = upload("/system/file/uploadFileEnc", [("files", "qoder_l.pdf", PDF)])
check("uploadFileEnc 恒返回 data:[]（方法体在 Java 里全是注释，不加密不碰存储）",
      st11 == 200 and j11.get("code") == 200 and j11.get("data") == [], j11)
logrow = mysql("select title, business_type from sys_oper_log where oper_url like '%uploadFileEnc%'"
               " order by oper_time desc limit 1")
check("@Log 照样写 sys_oper_log（title=文件, businessType=INSERT=1）",
      logrow and logrow[0].split("\t")[0] == "文件" and logrow[0].split("\t")[1] == "1", logrow)

# ---------------------------------------------------------------- 7) uploadByUrl
st12, j12 = post_json("/system/file/uploadByUrl",
                      {"list": [{"fileName": "qoder_m.pdf", "url": ""},
                                {"fileName": "qoder_n", "url": "http://127.0.0.1:9123/developer/nope"},
                                {"fileName": "qoder_o", "url": "http://127.0.0.1:1/x"}]})
check("uploadByUrl：空 url 静默跳过、取不到也静默跳过 ⇒ 仍 200 且 data 变短",
      st12 == 200 and j12.get("code") == 200 and j12.get("data") == [], j12)

# ---------------------------------------------------------------- 8) uploadFileId
import base64 as b64
PNG = b"\x89PNG\r\n\x01\x00qoder-id-probe"
fid = "9%016d" % 12345
st13, j13 = post_json("/system/file/uploadFileId",
                      {"id": fid, "files": "data:image/png;base64," + b64.b64encode(PNG).decode()})
d13 = (j13.get("data") or [{}])[0]
check("uploadFileId：返回 list，且 id 回显的是请求里那个（不是生成的）",
      st13 == 200 and d13.get("id") == fid and list(d13.keys()) ==
      ["bucketName", "fileName", "id", "url"], d13)
row13 = mysql("select original, type from sys_file where id=%s" % fid)
check("original = <毫秒>.<MIME 子类型>（Java 的 (int)Math.random()*10000 恒为 0）",
      row13 and row13[0].split("\t")[0].split(".")[0].isdigit()
      and row13[0].split("\t")[0].endswith(".png") and row13[0].split("\t")[1] == "png", row13)
st14, _h14, b14 = req("/system/file/developer/" + urllib.parse.quote(d13["fileName"]))
check("uploadFileId 的字节进了桶", st14 == 200 and b14 == PNG, (st14, len(b14)))
# 再来一次同 id：先删旧行旧对象再插新的
st15, j15 = post_json("/system/file/uploadFileId",
                      {"id": fid, "files": "data:image/pdf;base64," + b64.b64encode(b"second").decode()})
cnt = mysql("select count(1) from sys_file where id=%s" % fid)
check("同 id 再传：客户端指定的主键被复用（库里面还是 1 行）", cnt == ["1"], cnt)
st16, _h16, b16 = req("/system/file/developer/" + urllib.parse.quote(d13["fileName"]))
check("旧对象被 removeObject 掉 ⇒ 下载回到\"200 + 空 body\"", b16 == b"", len(b16))
st17, j17 = post_json("/system/file/uploadFileId", {"files": "no-comma"})
check("base64 里没有逗号：Java 在控制器里就数组越界 ⇒ code:500",
      j17.get("code") == 500, j17)
st18, j18 = post_json("/system/file/uploadFileId",
                      {"files": "data:image/png;base64," + b64.b64encode(b"z").decode()})
check("缺 id：那个\"主键不能为空\"的 error 没有 return，真实路径是 NPE ⇒ code:500",
      j18.get("code") == 500 and "data" not in j18, j18)

# ---------------------------------------------------------------- 9) uploadFile（小程序）
st19, j19 = upload("/system/file/uploadFile", [("file", "qoder_p.JPG", b"\xff\xd8\xff")])
check("uploadFile 的扩展名判断**不**忽略大小写：.JPG 被拒",
      j19.get("code") == 500 and j19.get("msg") == "上传失败,请上传照片格式的附件！"
      and "data" not in j19, j19)
st20, j20 = upload("/system/file/uploadFile", [("file", "qoder_q.png", b"\x89PNG")])
check("uploadFile 走的是 uploadFiles：字段名单数 file，成功形态同 /upload",
      st20 == 200 and (j20.get("data") or [{}])[0].get("id", "").isdigit(), j20.get("data"))
st21, j21 = upload("/system/file/uploadFile", [("files", "qoder_r.png", b"\x89PNG")])
check("字段名写成复数 files：Java 取 req.getFile(\"file\") 拿到 null ⇒ NPE/code:500",
      j21.get("code") == 500, j21)

# ---------------------------------------------------------------- 10) 鉴权与 /view
st22, _h22, b22 = req("/system/file/developer/" + urllib.parse.quote(key), token="")
check("GET /{bucket}/{key} 无 token：HTTP 200 + body code 401（renderString 写死 200）",
      st22 == 200 and json.loads(b22.decode("utf-8")).get("code") == 401, b22[:90])
st23, _h23, b23 = req("/system/file/view/developer/" + urllib.parse.quote(key), token="")
check("/view 不带 token 能读（anonymous()）", st23 == 200 and b23 == PDF, (st23, len(b23)))
st24, _h24, b24 = req("/system/file/view/developer/" + urllib.parse.quote(key))
check("/view 带 token 反而被容器级拒绝 ⇒ HTTP 403", st24 == 403, (st24, b24[:80]))
st25, _h25, b25 = req("/system/file/developer/" + urllib.parse.quote("qoder-不存在"))
check("读不存在的 key：200 + 空 body，不是 404", st25 == 200 and b25 == b"", (st25, len(b25)))
st26, _h26, b26 = req("/system/file/anothersbucket/" + urllib.parse.quote(key))
check("bucket 直接来自 URL、不校验（跨桶读照样打出去）", st26 == 200, st26)

# ---------------------------------------------------------------- 善后
track_rows()
if fid:
    CREATED_IDS.append(fid)
if CREATED_IDS:
    mysql("delete from sys_file where id in (%s)" % ",".join(CREATED_IDS))
left = mysql("select count(1) from sys_file where original like 'qoder\\_%' or id=" + fid)
check("清理：本轮的 sys_file 行全部删除", left and left[0] == "0", left)

print("----")
print("SYS FILE: pass=%d fail=%d" % (ok, bad))
sys.exit(1 if bad else 0)
