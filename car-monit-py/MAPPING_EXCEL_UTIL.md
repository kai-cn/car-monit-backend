# MAPPING_EXCEL_UTIL.md — `ExcelUtil` 切片 Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看
> [app/common/utils/poi/excel_util.py](app/common/utils/poi/excel_util.py) 的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §37。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Java 的 `exportExcel(List, String)` 与 `exportExcel(List, String, String)` 在 Python 里
  是两个方法名（`export_excel` / `export_excel_with_title`）—— Java 靠**重载**，
  Python 没有重载，所以**按参数个数改名**。这份文件里所有"同名不同参"都这么处理。
- `SXSSFWorkbook` 在 Python 里没有对应物，统一用 `openpyxl.Workbook`（内存版）。
  本项目最大导出量是用户表，几十行到几千行，内存版没有压力。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-common/.../utils/poi/ExcelUtil.java`（1797 行） | `app/common/utils/poi/excel_util.py`（1242 行） | **新建**；Python 去掉的是 POI 的样板（`CellStyle` 克隆、`Font`/`Fill`/`Border` 的 setter），逻辑逐行对应 |
| `ruoyi-common/.../annotation/Excel.java` | `app/common/annotation/excel.py` | **新建**；`@interface` → pydantic `dataclass`，26 个属性同名 `snake_case` |
| `ruoyi-common/.../annotation/Excels.java` | 同上：`Excels` 类型别名 | `@Excels({@Excel(..), @Excel(..)})` → 元组里两个并列项，靠 `target_attr` 区分 |
| `ruoyi-common/.../enums/ColumnType.java`<br>`.../enums/Type.java`<br>`.../enums/ExcelHandlerAdapter.java` | 同上：`ColumnType` / `Type` / `ExcelHandlerAdapter` | `__str__` 返回**常量名**，因为样式键是用 `toString()` 拼出来的 |
| `org.apache.poi.ss.usermodel.IndexedColors` | `IndexedColor`（同上文件） | 只保留用到的 5 个：`WHITE` / `BLACK` / `GREY_50_PERCENT` / `GREY_25_PERCENT` / `GREY_40_PERCENT` |
| `org.apache.poi.ss.usermodel.HorizontalAlignment` | `HorizontalAlignment` | 7 个常量同名 |
| `org.apache.poi.ss.usermodel.Workbook` / `SXSSFWorkbook(500)` | `openpyxl.Workbook` | 见 §5.1 |
| `WorkbookFactory.create(InputStream)` | `openpyxl.load_workbook` | **只认 xlsx**，见 §5.2 |
| `DictUtils.getDictLabel` | `DictUtils.get_dict_label_with_separator` | 已存在于 `app/common/utils/dict_util.py`，未改动 |
| `DateUtils.parseDateToStr` | `DateUtils.parse_date_to_str` | 已存在，未改动 |
| `Convert.toInt/toLong/toDouble/toStr/toBool` | `app/common/core/text/convert.py` 的同名函数 | 已存在，未改动 |

### 1.2 调用方（8 个 `export` + 2 个 `import`）

| 控制器 | 端点 | ExcelUtil 调用 |
|---|---|---|
| `SysUserController` | `GET /system/user/export` | `export_excel(rows, "用户数据")` |
| `SysUserController` | `GET /system/user/importTemplate` | `import_template_excel("用户数据")` |
| `SysUserController` | `POST /system/user/importData` | `import_excel(stream)` + `update_user` |
| `SysPostController` | `GET /system/post/export` | `export_excel(rows, "岗位数据")` |
| `SysRoleController` | `GET /system/role/export` | `export_excel(rows, "角色数据")` |
| `SysDictTypeController` | `GET /system/dict/type/export` | `export_excel(rows, "字典类型")` |
| `SysDictDataController` | `GET /system/dict/data/export` | `export_excel(rows, "字典数据")` |
| `SysConfigController` | `GET /system/config/export` | `export_excel(rows, "参数数据")` |
| `SysIndexMenuController` | `GET /system/indexmenu/export` | `export_excel(rows, "常用菜单")` |
| `SysUpgradeInfoController` | `GET /system/upgradeInfo/export` | `export_excel(rows, "升级信息")` |

`SysUpgradeInfo` **一个 `@Excel` 都没有** → 导出的是一张只有表头以外的空 sheet
（0 列）。这是 Java 原样，测试 `TestColumnTables::test_sys_upgrade_info_has_no_annotation_at_all`
把它钉住了。

### 1.3 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| ExcelUtil | `tests/test_excel_util.py` | **64** | 注解表（21 列 / 18 列 / 0 列）/ `getFields` 的 6 条判据 / 样式键 / `convertByExp` 的 7 种形态 / 文件名 / 落盘（11 条）/ 导入（8 条）/ `HttpServletResponse` 变体（3 条）/ 注解默认值 |

本切片新增 **64** 条，Phase 3.18 交付时全量 **2242 passed**（Phase 3.17 结束时是 2178）。

---

## 2. 入口方法对照

### 2.1 写文件（本项目 8 个 `export` 全走这条）

| Java | Python | 说明 |
|---|---|---|
| `exportExcel(List<T>, String sheetName)` | `export_excel(entities, sheet_name)` | 转调 `export_excel_with_title(..., "")` |
| `exportExcel(List<T>, String, String title)` | `export_excel_with_title(entities, sheet_name, title)` | `init` → `write_sheet` → 落盘 |
| `exportExcel()`（无参 **public**） | **私有** `_write_to_file()` | 返回值与上面完全相同，公开出去只会让调用点分不清；见 §2.3 |
| `importTemplateExcel(String sheetName)` | `import_template_excel(sheet_name)` | `Type.IMPORT` + 空 list |
| `importTemplateExcel(String, String title)` | `import_template_excel_with_title(sheet_name, title)` | 同上 + 标题行 |
| `encodingFilename(String)` | `encoding_filename(filename)` | `uuid4()_sheetName.xlsx` |
| `getAbsoluteFile(String)` | `get_absolute_file(filename)` | `{profile}/download/` + `mkdirs` |

### 2.2 写 `HttpServletResponse`（**本工程无调用点**，照搬）

| Java | Python |
|---|---|
| `exportExcel(HttpServletResponse, List<T>, String sheetName, String title)` | `export_excel_to_sink(sink, entities, sheet_name, title="")` |
| `importTemplateExcel(HttpServletResponse, String, String)` | `import_template_excel_to_sink(sink, sheet_name, title="")` |
| `exportExcel(HttpServletResponse)`（无参） | 私有 `_export_to_sink(sink)` |

`sink` 的鸭子类型是 `set_content_type(str)` + `get_output_stream()`，
现成的实现是 `app/system/service/sys_file_service.py::ResponseSink`。

**两条路的异常语义不同**，别合并：

| | 写文件 | 写流 |
|---|---|---|
| 失败 | 记日志 + 抛 `UtilException("导出Excel失败，请联系网站管理员！")` | **只**记日志 |
| 原因 | 调用方能 `catch` 后回 `AjaxResult.error(...)` | 响应头已经发出去了，抛异常也改不回来 |

### 2.3 为什么 `exportExcel()` 变私有

Java 的 `public AjaxResult exportExcel()` 是"已经 `init` 过、直接写"的内部入口，
外部唯一正确用法是通过另外两个重载。Python 没有重载，三者的**签名**会撞在一起
（`export_excel` 已占用两参版本），所以无参版改名为 `_write_to_file` 并降为私有 ——
**行为不变**，只是不再对调用方可见。

---

## 3. 读入口：`importExcel`

| Java | Python | 说明 |
|---|---|---|
| `importExcel(InputStream is)` | `import_excel(stream)` | `titleNum = 0`；异常包成 `UtilException`；`finally` 关流 |
| `importExcel(InputStream, int titleNum)` | `import_excel_with_title_num(stream, title_num)` | |
| `importExcel(String sheetName, InputStream, int)` | `import_excel_sheet(sheet_name, stream, title_num)` | 真正的实现 |
| `getCellValue(Row, int column)` | `get_cell_value(row, column)` | 见 §3.2 |

### 3.1 表头 → 字段的映射

```
cell_map  : 表头文字 -> 列号（空单元格记成 None -> 列号）
fields_map: 列号 -> (属性名, Excel)，键是 Excel.name（不是属性名！）
```

两个后果，都是 Java 原样：

1. **表头文字必须与 `@Excel(name=...)` 逐字相同**（含全角空格）。改一个字，那一列就
   静默丢失。
2. 表头里**重复**的同名列，后一个覆盖前一个 —— `cell_map` 是 `HashMap`，
   `put` 直接盖掉。

### 3.2 `getCellValue` 的类型判定顺序

| 单元格内容 | Java 结果 | Python 结果 |
|---|---|---|
| 空 | `""` | `""` |
| `boolean` | 原值 | `True` / `False` |
| 数字且是日期格式 | `Date`（Excel 1900 纪元） | `datetime`（`_EXCEL_EPOCH + timedelta(days=…)`） |
| `3.5` | `BigDecimal("3.5")` | `Decimal("3.5")` |
| `3.0` | `"3"`（`DecimalFormat("0")`） | `"3"` |
| 字符串 | 原值 | 原值 |
| 公式 | **`data_only=True` 取缓存值**，没缓存就是 `None` | 同左 |

`_EXCEL_EPOCH` 是 **1899-12-30** 而不是 12-31：POI 的 `DateUtil.getJavaDate` 已经把
1900-02-29（不存在的闰日）算进去了，基准因此往前挪一天。

### 3.3 按**声明类型**分派（`_convert_import_value`）

Java 用 `field.getType()`，Python 用 pydantic 的 `model_fields[name].annotation`
—— 两边拿到的都是**声明类型**，不是当前值的类型。

| Java 声明类型 | Python 声明类型 | 转换 |
|---|---|---|
| `String` | `Optional[str]` | `endsWith(".0")` 时砍掉（Excel 把 `3` 存成 `3.0`）；有 `dateFormat` 时先 `parseDateToStr` |
| `Integer` / `Long` | `Optional[int]` | 只有 `isNumeric` 才转，否则**保留原值**（可能留个 `""` 到实体里） |
| `Double` / `Float` | `Optional[float]` | `to_double` |
| `BigDecimal` | `Optional[Decimal]` | `to_big_decimal` |
| `Date` / `LocalDate` | `Optional[datetime/date]` | 字符串走 `DateUtils.parse_date`，数字走 Excel 纪元 |
| `Boolean` | `Optional[bool]` | `to_bool(...) or False` |
| 其它 | 其它 | 原值 |

`Integer` 与 `Long` 在 Python 里都是 `int`，统一用 `to_long`（值域更大）。本项目所有
带 `@Excel` 的整型字段在 Java 里都是 `Long`，所以没有"int 被放宽"的情形。

### 3.4 空行的判据

Java `isRowEmpty(Row)` 只在**整行都是 BLANK** 时返回 `true`。openpyxl 里"没有值"
就是 `None`，所以 `_is_row_empty` 是 `all(cell.value is None ...)`。

**空字符串 `""` 不算空行** —— 只要有一个单元格是 `""`，这一行就会生成一个实体。

---

## 4. 字段收集：`getFields()`

| Java | Python |
|---|---|
| `clazz.getSuperclass().getDeclaredFields()` + `clazz.getDeclaredFields()` | `_declared_excel_fields(clazz)`：按 `__mro__` 由基类到子类，每个类只取自己 `__dict__` 里的 `EXCEL_FIELDS` |
| `Stream.sorted(Comparator.comparing(Excel::sort))` | `fields.sort(key=lambda item: item[1].sort)`（Python 的 `sort` 也是**稳定**的） |
| `StringUtils.containsAny(excludeFields, field.getName())` | `name in excluded` |
| `containsAny(excludeFields, field.getName() + "." + targetAttr)` | `f"{name}.{attr.target_attr}" in excluded` |
| `attr.type() == Type.ALL \|\| attr.type() == type` | 同左 |

三个要点：

1. **`sort` 默认是 `Integer.MAX_VALUE`**（`UNSORTED`），所以没写 `sort` 的字段保持
   "父类字段在前、本类声明顺序在后"。Python 里是 `sys.maxsize`。
2. **`@Excels` 是摊平的**：一个字段两条注解 → 两条独立记录，同一个属性名。
   `hideColumn("dept")` 会同时排除两条；`hideColumn("dept.deptName")` 只排除其中一条。
3. **`getRowHeight()` 返回 twips**（`maxHeight * 20`，`short` 截断不四舍五入），
   而 openpyxl 的 `row_dimensions[i].height` 单位是**磅**，所以 `add_cell` 里要 `/20`。

---

## 5. 与 POI 的六处不等价

### 5.1 `SXSSFWorkbook(500)` → `Workbook`

POI 的流式工作簿把内存里超过 500 行的部分刷到临时文件；openpyxl 全程在内存。
**输出字节的语义等价**（都是 xlsx），差别只在内存占用与磁盘临时文件。
本项目最大导出量（用户表）远不到需要流式。

### 5.2 `WorkbookFactory.create` → `load_workbook`：**只认 xlsx**

| Java | Python |
|---|---|
| `.xls`（HSSF）、`.xlsx`（XSSF）都能读 | 只有 `.xlsx` / `.xlsm` |

`load_workbook` 读 `.xls` 抛 `InvalidFileException`，在 `import_excel` 里被包成
`UtilException`，前端拿到 `code 500`。前端的导入模板是从 `importTemplate`
（xlsx）下载的，所以正常流程不受影响；**手工另存为 `.xls` 再上传就会失败**。

### 5.3 `setDefaultColumnStyle` 没有对应物

Java 在子列表场景下调 `sheet.setDefaultColumnStyle(column, dataStyle)`。
openpyxl 没有"列默认样式"这个概念，等价效果由 `fill_excel_data` 里的 `add_cell`
逐格设置补齐。**子列表场景本身是休眠代码**（§6），所以这条差异只在纸面上。

### 5.4 `showDropDown` 语义**相反**

OOXML 的属性名是 `showDropDown`，但含义是"**隐藏**下拉箭头"：

| | 想让箭头显示 | 代码 |
|---|---|---|
| POI | `setSuppressDropDownArrow(false)` | 取反 |
| openpyxl | `validation.showDropDown = False` | 取反 |

`set_prompt_or_validation` 里写的是 `False`，注释里专门标了这一点 —— **别"顺手"改成 True**。

### 5.5 `DataFormat("@")` 的 `"General"` 反义

POI 的 `setDataFormat((short)49)` 是 `"@"`（文本）。openpyxl 的 `number_format`
直接接受字符串，`"General"` 是"常规"。两边字面量相同，**没有陷阱**，但别把
`"General"` 误当成 `"General"` 格式缺失。

### 5.6 列宽 / 行高的单位

| POI | 单位 | openpyxl |
|---|---|---|
| `setColumnWidth(col, w)` | `1/256` 个字符宽 | `width`（字符数），所以 `w / 256` |
| `setHeight(h)` | `1/20` 磅（twips） | `height`（磅），所以 `h / 20` |
| `setHeightInPoints(p)` | 磅 | `height`（磅），原值 |

`set_data_validation` 里两处宽度的算法**照抄 Java 的整数截断**：

```python
self.sheet.column_dimensions[letter].width = int((attr.width + 0.72) * 256) / 256
```

`int(...)` 在 `/256` **之前**，所以结果与 Java 的 `(int)((w+0.72)*256)/256.0` 一致，
而不是 `w + 0.72`。

---

## 6. 休眠代码（按迁移原则第 4 条照搬）

| Java 特性 | 本工程使用情况 | Python |
|---|---|---|
| `ColumnType.IMAGE`（读写图片、`addPicture`） | **零使用** | 导出时抛 `NotImplementedError`（被 `add_cell` 的 `except Exception` 吞掉，单元格留空）；导入时取 `""` |
| `ExcelHandlerAdapter` / `handler` / `args` | **零使用** | 完整迁了；默认值就是基类，`has_handler()` 用它判断 |
| `combo`（下拉框） | 只有 `SysUser` 的 `dept` 一处 | 完整迁了（含 >15 项走隐藏 sheet 的分支） |
| `prompt`（输入提示） | 两处 | 完整迁了 |
| `needMerge`（纵向合并） | **零使用** | 完整迁了 |
| `isStatistics`（合计行） | **零使用** | 完整迁了（`add_statistics_data` / `add_statistics_row`） |
| Collection 子列表（`subMethod` / `subFields`） | **零使用**（`_sub_fields` 永远是 `None`） | 完整迁了，`is_sub_list()` 永远 `False` |

`ColumnType.IMAGE` 的导出分支**不实现而是抛异常**，是为了让"将来有人给字段加上
`cellType = IMAGE`"时立刻炸出日志，而不是静默出一张没有图片的表。

---

## 7. 行号速查（改代码前先看这张表）

| 要改什么 | 去哪 |
|---|---|
| 样式键的拼法 | `_style_key_header` / `_style_key_data`（模块函数）+ 各枚举的 `__str__` |
| 表头 / 数据 / 合计三种基础样式 | `create_styles` |
| 字段收集与排序 | `get_fields` / `create_excel_field` / `_declared_excel_fields` |
| 单元格取值 / 格式化 / 统计 | `add_cell`（一个方法里 7 个 `elif`，顺序不能换） |
| 字符串强制成文本 | `_set_string`（防 `=A1` 变公式） |
| 列宽 / 提示 / 下拉 | `set_data_validation` / `set_prompt_or_validation` / `set_xssf_validation_with_hidden` |
| 落盘路径 | `get_absolute_file`（`ruoyi.download_path` + `mkdirs`） |
| 文件名 | `encoding_filename`（`uuid4()_sheetName.xlsx`） |
| 导入的表头匹配 | `import_excel_sheet` 里的 `cell_map` / `fields_map` |
| 导入的类型转换 | `_convert_import_value` |
| 实体的注解表 | 各实体的 `EXCEL_FIELDS`（`ClassVar`）+ `app/common/annotation/excel.py` 的 `Excel` |
| 行为差异说明 | [COMPATIBILITY.md](COMPATIBILITY.md) §37 |
| 客户端怎么拿到文件 | [MAPPING_COMMON.md](MAPPING_COMMON.md)（`GET /common/download`） |
