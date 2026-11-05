"""从 Java 控制器源码里抽出 @PathVariable 的类型清单，再用非法值对拍双端。

Java 侧 `@PathVariable Long jobId` 遇到 '1x' 会在进控制器之前失败，由
GlobalExceptionHandler 回 `{"msg":"请求参数类型不匹配，参数[jobId]要求类型为：'java.lang.Long'，但输入值为：'1x'","code":500}`；
Rust 侧若用 `Path<String>` + 宽松转换，就会把 '1x' 当 1 查出数据（或回一段英文 400 文案）。

只探测只读端点（GET / 导出），写端点靠清单静态核对——否则可能真的删改数据。

    python -m tools.endpoint_parity.pathvar_matrix              # 对拍 GET
    python -m tools.endpoint_parity.pathvar_matrix --inventory   # 只打印 Java 清单
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from client import JAVA_BASE, RUST_BASE, http, login  # noqa: E402

JAVA_SRC_ROOTS = [
    # 控制器不止在 ruoyi-admin：quartz / generator 各自的模块里也有。
    Path(item)
    for item in os.environ.get(
        'PARITY_JAVA_SRC',
        r'D:/work/IdeaProjects/car-monit-backend-new',
    ).split(os.pathsep)
]
SKIP_PARTS = ('car-monit-go', 'car-monit-py', 'target', 'node_modules', r'\test')


def controller_files(roots=JAVA_SRC_ROOTS):
    for root in roots:
        for path in sorted(root.rglob('*.java')):
            text = str(path)
            if any(part in text for part in SKIP_PARTS):
                continue
            if 'src' + os.sep + 'main' not in text:
                continue
            yield path

# @GetMapping / @PostMapping / @RequestMapping(value = "/x", method = RequestMethod.GET)
MAPPING_RE = re.compile(
    r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*(\(\s*(?:value\s*=\s*)?'
    r'(?:\{\s*)?"(?P<path>[^"]*)"(?P<more>[^)]*)?\)?)?'
)
CLASS_MAPPING_RE = re.compile(r'@RequestMapping\s*\(\s*(?:value\s*=\s*)?"(?P<path>[^"]*)"')
PATH_VARIABLE_RE = re.compile(
    r'@PathVariable\s*(?:\(\s*(?:value\s*=\s*)?"(?P<explicit>[^"]*)"[^)]*\))?\s+'
    r'(?P<type>[A-Za-z_][\w.<>\[\]]*(?:\s*\[\s*\])?)\s+(?P<name>\w+)'
)
NUMERIC = {
    'Long': 'java.lang.Long',
    'long': 'java.lang.Long',
    'Integer': 'java.lang.Integer',
    'int': 'java.lang.Integer',
}
BAD_VALUE = '1x'


def array_of(type_name):
    """Java 数组类型的 getName()，如 [Ljava.lang.Long;。"""
    return '[L%s;' % type_name


def parse_controllers():
    """返回 [(method, path_pattern, [(param_name, required_type_name)])]，只含数字类型路径变量。"""
    out = []
    for path in controller_files():
        text = path.read_text(encoding='utf-8', errors='replace')
        if '@PathVariable' not in text:
            continue
        base = ''
        head = text.split('public class', 1)[0]
        match = CLASS_MAPPING_RE.search(head)
        if match:
            base = match.group('path').rstrip('/')
        # 逐个方法块：@XxxMapping 与其后的方法签名。
        for match in MAPPING_RE.finditer(text):
            verb = match.group(1).upper()
            sub = match.group('path')
            more = match.group('more') or ''
            if verb == 'REQUEST':
                method_match = re.search(r'RequestMethod\.(\w+)', more)
                if not method_match:
                    continue
                verb = method_match.group(1).upper()
            elif verb == 'REQUESTMAPPING':
                continue
            start = match.end()
            brace = text.find('{', start)
            signature = text[start:brace if brace > 0 else start + 800]
            params = []
            for pv in PATH_VARIABLE_RE.finditer(signature):
                raw_type = pv.group('type').strip()
                name = pv.group('explicit') or pv.group('name')
                element = raw_type.replace('[ ]', '[]').replace(' ', '')
                if element.endswith('[]'):
                    inner = element[:-2]
                    required = array_of(NUMERIC.get(inner, inner))
                    if inner not in NUMERIC:
                        continue
                elif element in NUMERIC:
                    required = NUMERIC[element]
                else:
                    continue
                params.append((name, required))
            if not params:
                continue
            full = (base + sub) if sub.startswith('/') or not sub else base + '/' + sub
            out.append((verb, full.rstrip('/') or '/', params))
    return out


def fill_pattern(pattern, bad_position=None):
    """把 {var} 换成样例值；bad_position 指定第几个变量用坏值（这里统一用坏值）。
    与 compare.py 的样例表分开：这里只关心路径变量的类型转换，值一律给非法的。"""
    return re.sub(r'\{[^}]*\}', BAD_VALUE, pattern)


def probe(base, token, method, path):
    status, headers, body = http(method, base + path, token=token, timeout=60)
    text = (body or b'').decode('utf-8', 'replace')
    try:
        payload = json.loads(text)
        code = payload.get('code')
        msg = payload.get('msg')
    except Exception:
        code = None
        msg = text[:120]
    return status, code, msg


def core(msg):
    if not isinstance(msg, str):
        return msg
    return re.sub(r'\s+', ' ', msg)[:150]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', action='store_true', help='只打印 Java 的数字路径变量清单')
    parser.add_argument('--java-base', default=JAVA_BASE)
    parser.add_argument('--rust-base', default=RUST_BASE)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    entries = parse_controllers()
    total = sum(len(params) for _, _, params in entries)
    print('Java 控制器里的数字路径变量端点：%d 个（变量 %d 个）' % (len(entries), total))
    for verb, pattern, params in entries:
        print('  %-6s %-46s %s' % (verb, pattern, params))
    if args.inventory:
        return

    tj = login(args.java_base)[0]
    tr = login(args.rust_base)[0]
    ok = warn = fail = skip = 0
    for verb, pattern, params in entries:
        if verb != 'GET':
            skip += 1
            continue
        path = fill_pattern(pattern)
        sj, cj, mj = probe(args.java_base, tj, verb, path)
        sr, cr, mr = probe(args.rust_base, tr, verb, path)
        same = (sj == sr and cj == cr and core(mj) == core(mr))
        if same:
            ok += 1
            if args.verbose:
                print('OK   %-6s %s' % (verb, path))
            continue
        # Java 的类型不匹配文案是基准；两端都报错但文案不同算 WARN，Rust 返回数据算 FAIL。
        java_is_mismatch = isinstance(mj, str) and '请求参数类型不匹配' in mj
        rust_is_mismatch = isinstance(mr, str) and '请求参数类型不匹配' in mr
        if java_is_mismatch and rust_is_mismatch:
            warn += 1
            tag = 'WARN'
        else:
            fail += 1
            tag = 'FAIL'
        print('%s %-6s %s' % (tag, verb, path))
        print('     java status=%s code=%s msg=%s' % (sj, cj, core(mj)))
        print('     rust status=%s code=%s msg=%s' % (sr, cr, core(mr)))
    print('\n=== SUMMARY === 端点 OK=%d WARN=%d FAIL=%d 未探测(非 GET)=%d' % (ok, warn, fail, skip))
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main() or 0)
