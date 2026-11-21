import hashlib
import hmac

# AWS docs GET Object 例子的规范请求（逐字）
cr = "\n".join([
    "GET",
    "/test.txt",
    "",
    "host:examplebucket.s3.amazonaws.com",
    "range:bytes=0-9",
    "x-amz-content-sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "x-amz-date:20130524T000000Z",
    "",
    "host;range;x-amz-content-sha256;x-amz-date",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
])
sts = "\n".join([
    "AWS4-HMAC-SHA256",
    "20130524T000000Z",
    "20130524/us-east-1/s3/aws4_request",
    hashlib.sha256(cr.encode()).hexdigest(),
])


def h(key, msg):
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


k = h(("AWS4" + "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY").encode(), "20130524")
k = h(k, "us-east-1")
k = h(k, "s3")
k = h(k, "aws4_request")
sig = hmac.new(k, sts.encode(), hashlib.sha256).hexdigest()
print("canonicalRequestHash =", hashlib.sha256(cr.encode()).hexdigest())
print("signature            =", sig)
