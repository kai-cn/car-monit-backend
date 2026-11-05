# -*- coding: utf-8 -*-
"""造导入夹具：把数据行追加进自带模板，生成可上传的 xlsx（不需要 openpyxl）。

用法：python -m tools.endpoint_parity.xlsx_fixture <输出路径> <行JSON...>

模板默认是 importCarExcept.xlsx，要换别的模板用环境变量 FX_TEMPLATE：
    FX_TEMPLATE=config/templates/down/importCar.xlsx python -m tools.endpoint_parity.xlsx_fixture ...
行JSON = [[colIndex, value], ...]，数字会自动写成 NUMERIC 单元格。
"""
import json
import os
import re
import shutil
import sys
import zipfile

TEMPLATE = os.environ.get('FX_TEMPLATE', 'config/templates/down/importCarExcept.xlsx')
LETTERS = [chr(ord('A') + i) for i in range(26)]


def col(index):
    return LETTERS[index]


def cell_xml(ref, value):
    if isinstance(value, (int, float)):
        return '<c r="%s"><v>%s</v></c>' % (ref, value)
    text = (value or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return '<c r="%s" t="inlineStr"><is><t>%s</t></is></c>' % (ref, text)


def main():
    out = sys.argv[1]
    rows = [json.loads(arg) for arg in sys.argv[2:]]
    shutil.copyfile(TEMPLATE, out)
    source = zipfile.ZipFile(TEMPLATE)
    sheet = source.read('xl/worksheets/sheet1.xml').decode('utf-8')
    source.close()

    existing = [int(num) for num in re.findall(r'<row r="(\d+)"', sheet)]
    next_row = max(existing) + 1 if existing else 1
    added = []
    for offset, cells in enumerate(rows):
        number = next_row + offset
        body = ''.join(cell_xml('%s%d' % (col(index), number), value) for index, value in cells)
        added.append('<row r="%d" spans="1:22">%s</row>' % (number, body))
    last = next_row + len(rows) - 1
    sheet = sheet.replace('</sheetData>', ''.join(added) + '</sheetData>')
    sheet = re.sub(r'<dimension ref="[^"]*"/>', '<dimension ref="A1:V%d"/>' % last, sheet)

    names = zipfile.ZipFile(out).namelist()
    temp = out + '.tmp'
    with zipfile.ZipFile(TEMPLATE) as reader, zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED) as writer:
        for entry in reader.infolist():
            payload = sheet.encode('utf-8') if entry.filename == 'xl/worksheets/sheet1.xml' else reader.read(entry.filename)
            writer.writestr(entry, payload)
    # zip 不能原地改，写完再换回去。
    import os

    os.replace(temp, out)
    assert 'xl/worksheets/sheet1.xml' in names
    sys.stderr.write('rows appended: %s..%s -> %s\n' % (next_row, last, out))


if __name__ == '__main__':
    main()
