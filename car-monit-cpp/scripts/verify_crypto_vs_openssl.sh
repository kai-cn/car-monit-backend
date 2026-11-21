#!/usr/bin/env bash
# 内置 crypto 实现 与 OpenSSL CLI 的交叉验证。
#
# 为什么要这个脚本：car-monit-cpp 不依赖 OpenSSL（见 CMakeLists.txt 注释），
# 密码学是自己实现的。自研实现必须能证明“和行业标准库算出同一个结果”，
# 否则单测里那几个常量只是抄来的数字。car-monit-go 的差分脚本没有入库，
# 结果无法复现；这次把验证脚本放进仓库。
#
# 用法：bash scripts/verify_crypto_vs_openssl.sh [path-to-openssl]
set -euo pipefail

OPENSSL="${1:-openssl}"
command -v "$OPENSSL" >/dev/null 2>&1 || { echo "找不到 openssl：$OPENSSL"; exit 1; }
command -v g++ >/dev/null 2>&1 || { echo "找不到 g++"; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1. 编译探针（把三个 crypto 源文件单独编译，不依赖整个工程）
cat > "$TMP/probe.cpp" <<'CPP'
#include <cstdio>
#include <iostream>
#include <sstream>
#include <string>
#include "cm/common/utils/crypto/Base64.hpp"
#include "cm/common/utils/crypto/Digest.hpp"
#include "cm/common/utils/crypto/Rsa.hpp"
using namespace cm::crypto;
int main(int argc, char** argv) {
    std::string mode = argc > 1 ? argv[1] : "digest";
    std::stringstream ss;
    ss << std::cin.rdbuf();
    std::string in = ss.str();
    if (mode == "digest") {
        // 与 `openssl dgst -<alg>` 输出顺序一致，便于逐行比较
        std::printf("md5=%s\nsha1=%s\nsha256=%s\nsha512=%s\n", hex(md5(in)).c_str(),
                    hex(sha1(in)).c_str(), hex(sha256(in)).c_str(), hex(sha512(in)).c_str());
    } else if (mode == "hmac") {
        std::printf("sha1=%s\nsha256=%s\nsha512=%s\n", hex(hmacSha1(argv[2], in)).c_str(),
                    hex(hmacSha256(argv[2], in)).c_str(), hex(hmacSha512(argv[2], in)).c_str());
    } else if (mode == "b64") {
        std::printf("%s\n", base64Encode(in).c_str());
    } else if (mode == "rsaenc") {
        std::string pem = in, ct, err;
        if (!rsaOaepEncryptPem(pem, argv[2], ct, &err)) {
            std::fprintf(stderr, "%s\n", err.c_str());
            return 1;
        }
        std::printf("%s\n", base64Encode(ct).c_str());
    }
    return 0;
}
CPP
g++ -std=c++20 -O1 -Iinclude -o "$TMP/probe" "$TMP/probe.cpp" \
    src/cm/common/utils/crypto/Digest.cpp src/cm/common/utils/crypto/Base64.cpp \
    src/cm/common/utils/crypto/Rsa.cpp

fail=0
check() {  # check <desc> <expected> <actual>
    # Windows 版 openssl 输出行尾是 CRLF，用 bash 参数展开去掉 CR 再比
    exp=${2//$'\r'/}
    got=${3//$'\r'/}
    if [ "$exp" = "$got" ]; then
        printf '  ok   %s\n' "$1"
    else
        printf '  FAIL %s\n       openssl=%s\n       mine  =%s\n' "$1" "$exp" "$got"
        fail=$((fail + 1))
    fi
}

# 2. 摘要对拍（Windows 版 openssl 不支持 <(...) 进程替换，一律走临时文件）
odigest() {  # odigest <alg> <file>
    "$OPENSSL" dgst -"$1" -r "$2" | cut -d' ' -f1 | tr -d ''
}
echo "== 摘要（MD5/SHA-1/SHA-256/SHA-512）=="
for s in "" "a" "abc" "hello world" "car-monit-cpp 迁移校验" "01234567890123456789012345678901234567890123456789012345678901234567890123456789" "$(head -c 5000 /dev/urandom | base64)"; do
    printf '%s' "$s" > "$TMP/s.bin"
    mine=$(printf '%s' "$s" | "$TMP/probe" digest)
    ref=$(printf 'md5=%s
sha1=%s
sha256=%s
sha512=%s'         "$(odigest md5 "$TMP/s.bin")" "$(odigest sha1 "$TMP/s.bin")"         "$(odigest sha256 "$TMP/s.bin")" "$(odigest sha512 "$TMP/s.bin")")
    check "len=${#s}" "$ref" "$mine"
done

# 3. HMAC 对拍（含超长 key：key 长度大于分组大小时要先对 key 取哈希）
ohmac() {  # ohmac <alg> <key> <file>
    "$OPENSSL" dgst -"$2" -hmac "$1" -r "$3" 2>/dev/null | cut -d' ' -f1 | tr -d ''
}
echo "== HMAC =="
for key in "secret" "$(head -c 300 /dev/urandom | base64)"; do
    printf 'payload-text' > "$TMP/m.bin"
    mine=$(printf 'payload-text' | "$TMP/probe" hmac "$key")
    ref=$(printf 'sha1=%s
sha256=%s
sha512=%s'         "$(ohmac "$key" sha1 "$TMP/m.bin")" "$(ohmac "$key" sha256 "$TMP/m.bin")"         "$(ohmac "$key" sha512 "$TMP/m.bin")")
    check "key len=${#key}" "$ref" "$mine"
done

# 4. Base64 对拍
echo "== Base64 =="
for n in 0 1 2 3 4 5 6 17; do
    data=$(head -c $n /dev/urandom | base64)
    mine=$(printf '%s' "$data" | "$TMP/probe" b64)
    ref=$(printf '%s' "$data" | "$OPENSSL" base64 -A | tr -d '')
    check "n=$n" "$ref" "$mine"
done

# 5. RSA-OAEP(SHA-1)：我方加密 -> openssl 用私钥解密还原
echo "== RSA-OAEP(SHA-1) 端到端（openssl 私钥解密）=="
( cd "$TMP" && "$OPENSSL" genrsa -out priv.pem 2048 >/dev/null 2>&1     && "$OPENSSL" rsa -in priv.pem -pubout -out pub.pem >/dev/null 2>&1 )
plain='MySQL-pass-123'
for i in 1 2 3; do
    if "$TMP/probe" rsaenc "$plain" < "$TMP/pub.pem" > "$TMP/ct.b64" 2>/dev/null; then
        "$OPENSSL" base64 -d -A -in "$TMP/ct.b64" -out "$TMP/ct.bin"
        ctlen=$(wc -c < "$TMP/ct.bin" | tr -d ' ')
        got=$("$OPENSSL" pkeyutl -decrypt -inkey "$TMP/priv.pem" -in "$TMP/ct.bin"               -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha1 2>/dev/null | tr -d '' || true)
        if [ "$got" = "$plain" ] && [ "$ctlen" = "256" ]; then
            printf '  ok   run%s 密文 %s 字节，openssl 还原成功
' "$i" "$ctlen"
        else
            printf '  FAIL run%s ctlen=%s got=[%s]
' "$i" "$ctlen" "$got"
            fail=$((fail + 1))
        fi
    else
        printf '  FAIL run%s 加密失败
' "$i"
        fail=$((fail + 1))
    fi
done

echo
if [ "$fail" = "0" ]; then
    echo "crypto 与 OpenSSL 完全一致 ✅"
else
    echo "存在 $fail 处不一致 ❌"
    exit 1
fi
