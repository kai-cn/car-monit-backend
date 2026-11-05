"""扫出 Java 侧所有 @RestController/@Controller，与 docs/01-baseline/02-endpoints.md 的前缀对照，
找出基线清单漏掉的控制器（/oss 就是这么露出来的）。"""
import pathlib
import re

root = pathlib.Path(r'D:/work/IdeaProjects/car-monit-backend-new')
skip = ('car-monit-go', 'car-monit-py', 'target', 'node_modules')
controllers = []
for path in root.rglob('*.java'):
    text_path = path.as_posix()
    if any(part in text_path for part in skip):
        continue
    if '/src/main/java/' not in text_path:
        continue
    text = path.read_text(encoding='utf-8', errors='replace')
    if '@RestController' not in text and '@Controller' not in text:
        continue
    match = re.search(r'@RequestMapping\s*\(\s*(?:value\s*=\s*)?\{?\s*"([^"]+)"', text)
    prefix = match.group(1) if match else '(none)'
    methods = len(re.findall(r'@(Get|Post|Put|Delete|Patch|Request)Mapping', text))
    controllers.append((prefix, methods, text_path.split('/src/main/java/')[-1]))

baseline = pathlib.Path('docs/01-baseline/02-endpoints.md').read_text(encoding='utf-8')
print('控制器总数', len(controllers))
missing = []
for prefix, methods, rel in controllers:
    if prefix == '(none)':
        continue
    if ('`' + prefix) not in baseline:
        missing.append((prefix, methods, rel))
print('基线里找不到前缀的控制器:', len(missing))
for prefix, methods, rel in sorted(missing):
    print('  %-24s %2d 条  %s' % (prefix, methods, rel))
