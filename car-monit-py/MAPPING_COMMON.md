# MAPPING_COMMON.md — `/common` + `/downTemplate` 切片 Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §38。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- 本切片是**公共服务包**（`com.ruoyi.web.controller.common` 去掉验证码），
  它是 §37 `ExcelUtil` 的下游：导出接口返回的文件名必须靠 `GET /common/download`
  才能变成文件。
- 这一片**没有** Service / Mapper / 实体：两个控制器都直接调工具类。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/common/CommonController.java` | `app/api/common/common_controller.py` | **新建**；4 个映射全部迁移 |
| `ruoyi-admin/.../web/controller/common/DownTemplateController.java` | `app/api/common/down_template_controller.py` | **新建**；1 个映射 |
| `ruoyi-common/.../utils/file/FileUtils.java` | `app/common/utils/file_utils.py` | **新建**；见 §3 |
| `ruoyi-common/.../utils/file/FileTypeUtils.java` | `app/common/utils/file_type_utils.py` | **新建**；见 §4 |
| `ruoyi-common/.../config/ServerConfig.java` | `app/framework/config/server_config.py` | **新建**；`getUrl()` / `getDomain()` |
| `ruoyi-common/.../utils/file/MimeTypeUtils.java` | `app/common/utils/mime_type_utils.py` | **未改动**（上传链路早已存在） |
| `ruoyi-common/.../utils/file/FileUploadUtils.java` | `app/common/utils/file_upload_utils.py` | **未改动**（上传链路早已存在） |
| `ruoyi-framework/.../config/SecurityConfig.java` | `app/framework/config/security_config.py` | **未改动**；`/common/download**` 与 `/common/download/resource**` 两条规则本来就在 |
| `ruoyi-admin/src/main/resources/templates/down/*.xlsx`（7 个） | `config/templates/down/*.xlsx`（7 个） | **字节级复制**；`config/` 是 classpath 的镜像，见 §6 |
| `com.ruoyi.common.utils.http.HttpUtils` 等 | **无对应物** | `CommonController` 没有用到（`resourceDownload` 的方法体是注释） |

### 1.2 被改动的已有文件（只有两处）

| 文件 | 改动 | 原因 |
|---|---|---|
| `app/system/service/sys_file_service.py` | `ResponseSink` 新增 `add_header` / `set_header` / `headers`，`get_output_stream()` 改为返回 `_CloseTolerantStream` | `FileUtils.writeBytes` 在 `finally` 里**关流**；不包一层，FastAPI 拿不到 body（见 §5.2） |
| `app/main.py` | `include_router(common_router)` + `include_router(down_template_router)` | 挂路由 |

`FileUtils` / `FileTypeUtils` / `ServerConfig` 是**新文件**，没有任何旧代码被改动。

### 1.3 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| 工具类 | `tests/test_file_utils.py` | **68** | `getFileType` 的大小写 / 白名单 / `URLEncoder` 的安全集 / `writeBytes` 的关流语义 / 文件名解析 / `getFileExtendName` 的大小写不对称 |
| CommonController | `tests/test_common_controller.py` | **25** | 4 条路由 / 3 条安全规则 / 缺参不是 400 / 文件不存在是 200 空 body / 上传四个额外键的顺序与拼接 |
| DownTemplateController | `tests/test_down_template_controller.py` | **30** | 1 条路由 / 登录即可 / 7 个 `type` 的原始字节 / 未知 `type` 的 200 空 body 无响应头 |

合计 **123** 条，全量 **2365 passed**（Phase 3.18 结束时是 2242）。

---

## 2. 控制器：5 个映射

### 2.1 `CommonController`（4 个）

| Java | Python | Method / Path | 权限 |
|---|---|---|---|
| `fileDownload(String fileName, Boolean delete, ...)` | `file_download(request, file_name, delete)` | GET `/common/download` | **`anonymous()`** |
| `uploadFile(MultipartFile file)` | `upload_file(request, file)` | POST `/common/upload` | 登录即可 |
| `uploadFiles(List<MultipartFile> files)` | `upload_files(request, files)` | POST `/common/uploads` | 登录即可 |
| `resourceDownload(String resource, ...)` | `resource_download(request, resource)` | GET `/common/download/resource` | `authenticated()` |

**一个 `@PreAuthorize` 都没有**（Java 源码里就没有），所以 Python 侧也没有装饰器。

### 2.2 `DownTemplateController`（1 个）

| Java | Python | Method / Path | 权限 |
|---|---|---|---|
| `downExcel(String type)` | `down_excel(type_)` | GET `/downTemplate/{type}` | 登录即可 |

`SecurityConfig` **没有** `/downTemplate/**` 规则，落到 `anyRequest().authenticated()`。

### 2.3 `/common/download/resource` **没有**被 `/common/download**` 遮蔽

这一点容易误判，因为两条规则长得像：

```
.antMatchers("/common/download**").anonymous()
.antMatchers("/common/download/resource**").authenticated()
```

`AntPathMatcher` 先按 `/` 切段：

| 模式 | 切出来 |
|---|---|
| `/common/download**` | `["common", "download**"]` |
| `/common/download/resource` | `["common", "download", "resource"]` |

第二段 `download**` 确实能匹配 `download`，但此时**路径还有剩余段、模式已经用完**，
`doMatch` 直接 `return false`。所以 `authenticated()` 那条**真的生效**。

> 这与 [COMPATIBILITY.md](COMPATIBILITY.md) §20 的"静态资源规则遮蔽 `denyAll`"**不是同一类问题**：
> 那是规则**排序**，这里是规则**形状**。

### 2.4 查询参数绑定

Spring 对**没有注解**的简单类型参数用 `RequestParamNamedValueInfo()`，其
`required` 默认是 **`false`** —— 所以 `fileName` / `delete` / `resource` 全是可选的：

| Java 形参 | query 参数名 | Python | 缺参时的行为 |
|---|---|---|---|
| `String fileName` | `fileName` | `file_name`（`Query(alias="fileName")`） | `checkAllowDownload(None)` → NPE → 被吞 → **200 空 body** |
| `Boolean delete` | `delete` | `delete` | 文件照下，随后 `if (delete)` 拆箱 NPE → 被吞 → **文件不删** |
| `String resource` | `resource` | `resource` | `checkAllowDownload(None)` → NPE → 被吞 → **200 空 body** |
| `MultipartFile file` | 部件名 `file` | `file: UploadFile` | `None` → NPE → `error(null)` → **code 500** |
| `List<MultipartFile> files` | 部件名 `files`（可重复） | `files: List[UploadFile]` | 空列表 → 循环 0 次 → `success` 里四个空串 |

`List<MultipartFile>` **没有 `@RequestParam`** 也能绑定，是
`MultipartResolutionDelegate.isMultipartArgument` 的功劳 —— 参数名就是部件名。

### 2.5 `delete` 的取值契约

走 Spring 的 `StringToBooleanConverter`：

| 真值 | 假值 |
|---|---|
| `true` / `on` / `yes` / `1` | `false` / `off` / `no` / `0` |

其它值（含空串）→ `MethodArgumentTypeMismatchException` → `code 500` +
`请求参数类型不匹配，参数[delete]要求类型为：'java.lang.Boolean'，但输入值为：'xxx'`。

Python 的 `_spring_boolean` 用 `ServiceException` 承载这个文案。**不能**用
`ValueError`：`@app.exception_handler(Exception)` 挂在 `ServerErrorMiddleware`，它在
响应发完之后会**重新抛**（见 [COMPATIBILITY.md](COMPATIBILITY.md) §25.3）。

### 2.6 注册顺序

FastAPI 按**注册顺序**匹配。本切片两条 GET 谁在前都不会互相吃掉（`/common/download`
是一段、`/common/download/resource` 是两段），但为了与 Java 源码声明顺序一致，
`fileDownload` 写在 `resourceDownload` 之前。

---

## 3. `FileUtils`（`com.ruoyi.common.utils.file.FileUtils`）

⚠ 与已有的 `app/common/utils/file_util.py`（**hutool** 的 `FileUtil`）**不是同一个类**。
两个文件并存是故意的：Java 里就是两个类。

### 3.1 重载改名表

| Java | Python | 说明 |
|---|---|---|
| `writeBytes(String filePath, OutputStream os)` | `write_bytes(file_path, output_stream)` | 1024 字节块；`finally` 关流 |
| `writeBytes(byte[] data, String filePath)` | `write_bytes_to_dir(data, dir_path)` | 返回 `/profile/upload/...` 相对 url |
| `writeImportBytes(byte[] data)` | `write_import_bytes(data)` | 写到 `ruoyi.import_path` |
| `deleteFile(String filePath)` | `delete_file(file_path)` | 目录返回 `False` |
| `isValidFilename(String)` | `is_valid_filename(file_name)` | `FILENAME_PATTERN` 全匹配 |
| `checkAllowDownload(String)` | `check_allow_download(resource)` | 见 §3.3 |
| `setFileDownloadHeader(HttpServletRequest, String, HttpServletResponse)` | `set_file_download_header(request, file_name, response)` | IE / Firefox / Chrome 三分支 |
| `setAttachmentResponseHeader(HttpServletResponse, String)` | `set_attachment_response_header(response, real_file_name)` | 三个响应头 |
| `percentEncode(String)` | `percent_encode(value)` | `URLEncoder` 之后 `+` → `%20` |
| `getFileExtendName(byte[])` | `get_file_extend_name(data)` | **小写** |
| `getName(String)` | `get_name(value)` | 两种分隔符都切 |
| `getNameNotSuffix(String)` | `get_name_not_suffix(value)` | 去路径 + 去最后一段后缀 |

### 3.2 `writeBytes` 在 `finally` 里关流

```java
try { ... } finally { IOUtils.closeQuietly(os); }
```

servlet 世界里"关流 = 提交响应"。所以**文件不存在**时：

1. `FileNotFoundException` 抛出；
2. `finally` 把响应流关掉 —— 响应头**已经发出去了**；
3. `CommonController` 的 `catch` 吞掉异常；
4. 客户端拿到 **HTTP 200 + 完整响应头 + 空 body**，**不是 404**。

Python 侧保留这个语义，靠 `_CloseTolerantStream`：`close()` 只置位，不碰
`BytesIO`，这样 FastAPI 在函数返回后仍能读到 body（见 §5.2）。

### 3.3 `checkAllowDownload` 的两道闸

```
1. contains(resource, "..")           -> false（防目录穿越，等价 Java 原样）
2. getFileType(resource) 在白名单里    -> 见下
```

`DEFAULT_ALLOWED_EXTENSION` 是 **22** 项：`bmp gif jpg jpeg png doc docx xls xlsx ppt
pptx html htm txt rar zip gz bz2 mp4 avi rmvb pdf`。

判据是 `FileTypeUtils.getFileType` —— 它内部 `toLowerCase()`，所以**不区分大小写**，
`A.PNG` 能过。这与**上传**那半边的 `MimeTypeUtils.getExtension`（`contains` 子串匹配、
区分大小写）**是两套不同规则**，别互相参照。

### 3.4 编码：`URLEncoder` 的安全字符集

`java.net.URLEncoder.encode` 的安全集是 `.-*_` + 字母数字：

| 字符 | Java `URLEncoder` | `urllib.parse.quote` |
|---|---|---|
| 空格 | `+` | `%20` |
| `~` | `%7E` | `~`（不编码） |
| `*` | `*`（不编码） | `%2A` |

所以 `url_encode` 是手写的，**不能**换成 `quote`。`percent_encode` = `url_encode`
之后把 `+` 换成 `%20`。

### 3.5 `getFileExtendName` 的大小写不对称

| 方法 | 返回 |
|---|---|
| `FileTypeUtils.getFileExtendName(byte[])` | **大写**：`"GIF"` / `"JPG"` / `"BMP"` / `"PNG"` |
| `FileUtils.getFileExtendName(byte[])` | **小写**：`"gif"` / `"jpg"` / `"bmp"` / `"png"` |

两个方法体**逐字相同**，只有大小写不同 —— Java 原样，别"顺手"统一。
两者都要求 `data.length >= 10`，否则 Java 抛 `ArrayIndexOutOfBoundsException`，
Python 抛 `IndexError`。

### 3.6 `setFileDownloadHeader` 的三个分支

| UA 特征 | 处理 |
|---|---|
| 含 `MSIE` | `fileName = URLEncoder.encode(fileName, "UTF-8")` 然后 `replaceAll("\\+", "%20")` |
| 含 `Firefox` | `MimeUtility.encodeText(fileName, "UTF-8", "B")`（Base64 编码词） |
| 含 `Chrome` | `new String(fileName.getBytes("UTF-8"), "ISO8859-1")` |

`request.getHeader("User-Agent")` 为 `null` 时，`agent.contains("MSIE")` 抛 NPE
（Python 是 `TypeError`）。本工程**没有调用点**，按迁移原则照搬。

---

## 4. `FileTypeUtils`（`com.ruoyi.common.utils.file.FileTypeUtils`）

| Java | Python | 说明 |
|---|---|---|
| `getFileType(String fileName)` | `get_file_type(file_name)` | `lastIndexOf(".")` 之后 `.toLowerCase()`；`null` → NPE → Python `AttributeError` |
| `getFileType(File file)` | `get_file_type_of_file(file)` | `file == null` → `""` |
| `getFileExtendName(byte[] photoByte)` | `get_file_extend_name(photo_byte)` | 大写，见 §3.5 |

`getFileType("a.b/c")` 返回 `"b/c"` —— 它只看**最后一个点**，不做目录判断，
与 `FileUploadUtils.getExtension`（会先 `substringAfterLast("/")`）**不同**。

---

## 5. 字节 ↔ 响应：`ResponseSink` 的三处扩展

`ResponseSink` 原本是 `sys_file` 切片的 `HttpServletResponse` 替身（`COMPATIBILITY.md`
§36）。`CommonController` 需要三样它原来没有的东西。

### 5.1 `addHeader` / `setHeader`

| Java | Python |
|---|---|
| `response.addHeader(name, value)` | `sink.add_header(name, value)`（追加） |
| `response.setHeader(name, value)` | `sink.set_header(name, value)`（先按**大小写不敏感**删除同名，再追加） |
| — | `sink.headers` 属性：合并成 `Dict[str, str]` |

`setAttachmentResponseHeader` 里两个方法都用到了：
`add_header("Access-Control-Expose-Headers", ...)` + `set_header("Content-disposition", ...)`。

### 5.2 `_CloseTolerantStream`

`FileUtils.write_bytes` 在 `finally` 里 `close()`。如果直接把 `BytesIO` 交出去，
`close()` 之后再读会抛 `ValueError: I/O operation on closed file`，FastAPI 就取不到 body。

`_CloseTolerantStream` 的处理：

| 方法 | 行为 |
|---|---|
| `write(data)` | 未关闭 → 转发给 `BytesIO`；已关闭 → 抛 `ValueError`（与真实流一致） |
| `close()` | **只置位**，不动 `BytesIO` |
| `__getattr__` | 其余全部转发（`getvalue` 等） |

`tests/test_file_utils.py::TestWriteBytes` 依赖"关流之后再写要报错"这个性质，
所以 `_closed` 标志是必需的，不能简写成"`close()` 什么都不做"。

### 5.3 `_to_response`

`ResponseSink` → `starlette.responses.Response`：

```
headers = dict(sink.headers)          # setHeader/addHeader 攒下来的
if sink.content_type is not None:
    headers["Content-Type"] = sink.content_type   # setContentType 单独一列
return Response(content=sink.body, headers=headers)
```

`Content-Type` 单独存是因为 servlet 的 `setContentType` 与 `setHeader("Content-Type")`
是同一个头，但 Java 代码里两种写法都出现过。

---

## 6. `DownTemplateController`：`type` → 模板

### 6.1 白名单

| `type` | 模板文件 |
|---|---|
| `goodsFkApplyDetail` | `importGoodsFkApplyDetail.xlsx` |
| `goodsRkApplyDetail` | `importGoodsRkApplyDetail.xlsx` |
| `planListDetail` | `importPlanListDetail.xlsx` |
| `importPsbz` | `importPsbz.xlsx` |
| `importSupplierAnnualScore` | `importSupplierAnnualScore.xlsx` |
| `carinfo` | `importCar.xlsx` |
| `carExcept` | `importCarExcept.xlsx` |
| 其它（含未知） | **`templates/down`（目录）** |

未知 `type` 时 `url` 停在初值 `"templates/down"` —— 那是个**目录**，读不到。
Python 侧 `resolve_template_path` 故意返回目录路径，让"读失败"发生在与 Java
完全相同的位置。

### 6.2 为什么直接返回模板原始字节

Java 走 easypoi：

```java
TemplateExportParams params = new TemplateExportParams(url, true);   // true = 扫描全部 sheet
return ExcelExportUtil.exportExcel(params, new HashMap<>());
```

**这 7 个模板里没有任何 `${...}` 占位符**（已逐格核对）。所以"渲染"等于"原样输出"。

Python 因此不走 openpyxl 重写，而是直接 `open(path, "rb").read()`。理由：

| | openpyxl 重写 | 原始字节 |
|---|---|---|
| 单元格值 | 一致 | 一致 |
| 数据校验（下拉框） | **可能丢失** | 保留 |
| 表单控件 / 批注 | **丢失** | 保留 |
| `importCarExcept.xlsx` 的"基础表请勿改动" sheet | 可能被改 | 保留（那张 sheet 就是给下拉框用的） |

### 6.3 成功与失败

| 场景 | 状态码 | body | 响应头 |
|---|---|---|---|
| 已知 `type` | 200 | 模板原始字节 | `Content-Type: application/octet-stream;charset=UTF-8`<br>`Content-Disposition: attachment` |
| 未知 `type` | 200 | **空** | **一个都没有** |

`Content-Disposition` 是写死的 `"attachment"`，**没有 `filename`** —— Java 原文如此。
浏览器会用 url 最后一段当文件名。

失败时没有任何响应头，是因为 `setContentType` / `setHeader` 都在 `try` 里、在异常点
**之后**。

---

## 7. 行号速查（改代码前先看这张表）

| 要改什么 | 去哪 |
|---|---|
| 4 个端点的路径 / 权限 | `app/api/common/common_controller.py` 顶部 docstring + `router` 声明 |
| `delete` 的真假值集合 | 同文件的 `_TRUE_LITERALS` / `_FALSE_LITERALS` |
| 下载白名单（22 项） | `app/common/utils/mime_type_utils.py::DEFAULT_ALLOWED_EXTENSION` |
| 下载大小写判据 | `file_type_utils.get_file_type`（`toLowerCase` 在这里） |
| 目录穿越拦截 | `file_utils.check_allow_download` 第一行 |
| 真实文件名（时间戳 + `_` 之后） | `common_controller.file_download` 里 `underscore = file_name.find("_")` 那段 |
| 响应头拼法（三个） | `file_utils.set_attachment_response_header` |
| 编码（`URLEncoder` 等价物） | `file_utils.url_encode` / `percent_encode` |
| 模板白名单 | `app/api/common/down_template_controller.py::TEMPLATE_BY_TYPE` |
| 模板文件本体 | `config/templates/down/` |
| 关流语义 | `app/system/service/sys_file_service.py::_CloseTolerantStream` |
| 路由是否挂上 | `app/main.py` 的两个 `include_router` |
| 安全规则 | `app/framework/config/security_config.py::AUTHORIZATION_RULES` |
| 行为差异说明 | [COMPATIBILITY.md](COMPATIBILITY.md) §38 |
| 导出接口怎么拿到文件 | [MAPPING_EXCEL_UTIL.md](MAPPING_EXCEL_UTIL.md) §2.1 |
