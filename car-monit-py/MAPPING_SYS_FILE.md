# MAPPING_SYS_FILE.md — `sys_file` 切片（文件管理 / OSS）Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §36。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `uploadFilesPdf` → `upload_files_pdf`。
- 接口与实现（`ISysFileService` + `SysFileServiceImpl`）在 Python 里合并成一个类。
- 本切片**新增了一个基础设施件**：`ResponseSink`（`HttpServletResponse` 的最小替身，见 §3.8）。
  OSS 客户端 `OssTemplate` / `S3Object` 在 Phase 2 就已落地，本切片只是第一个真正用它的模块。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/system/SysFileController.java` | `app/api/system/sys_file_controller.py` | **新建**；**17 个映射，全部迁移**（本类没有 `export`） |
| `ruoyi-system/.../service/ISysFileService.java`<br>`ruoyi-system/.../service/impl/SysFileServiceImpl.java` | `app/system/service/sys_file_service.py` | **新建**；**24 个接口成员 + 1 个实现类私有方法**（`deleteSysFileByIdNew`）+ 4 个私有 `fileLog*`，全部迁移 |
| `ruoyi-system/.../mapper/SysFileMapper.java`<br>`ruoyi-system/.../resources/mapper/system/SysFileMapper.xml` | `app/system/mapper/sys_file_mapper.py` | **新建**；9 个方法 ↔ 9 条 statement，**严格 1:1** |
| `ruoyi-system/.../domain/SysFile.java` | `app/system/domain/sys_file.py` | **新建**；**不继承** `BaseEntity`，14 个自有字段 + 2 个临时字段 |
| `ruoyi-admin/.../RuoYiApplication.java`（`@SpringBootApplication` 扫描） | `app/main.py` | **改了一处**：`include_router(sys_file_router)` |

### 1.2 横切（本切片用到的部分）

| Java | Python | 说明 |
|---|---|---|
| `BaseController#startPage()` | `base_controller.start_page()` | `list` / `getNewCa` 调用 |
| `BaseController#getDataTable(List)` | `base_controller.get_data_table(rows)` | 只有 `list` |
| 无注解实体参数 `SysFile` | `bind_query_params(SysFile, request.query_params)` | 无 `@RequestBody` 即按 query string 绑定（`list` / `getNewCa`） |
| `@RequestBody SysFile` | 直接写成 FastAPI 的 pydantic 形参 | `edit` / `uploadFileId` / `updateCAFile`；**没有** `@Validated` |
| `@PathVariable Long[] ids` | `base_controller.parse_id_array(ids)` | `remove`；**注意不是** `parse_str_array`（§2.3） |
| `@RequestParam("files") MultipartFile[]` | `Annotated[List[UploadFile], File()]` | 部件名必须叫 `files`（§2.7） |
| `@RequestParam("bussNames") String[]` | `Annotated[List[str], Form(alias="bussNames")]` | `uploadSupplier`；原样保留驼峰别名 |
| `@PreAuthorize("@ss.hasPermi(...)")` | `@pre_authorize_permi(...)` | **只有 2 个端点有**，见 §2.2 |
| `@Log(title = "文件" / "文件管理", ...)` | **未迁移** | 不写 `sys_oper_log`，见 §36.2 |
| `SecurityUtils#getUserId()` | `security_utils.get_user_id()` | 四个审计列；写库前 `str(...)` |
| `IdUtil.simpleUUID()` | `uuid_utils.simple_uuid()` | OSS 上的 `fileName` 前缀（32 位、无连字符） |
| `SnowflakeIdWorker#nextId()` | `snowflake_id_worker.get_id_worker().next_id()` | `sys_file.id` 的主键 |
| `StringUtils.getUUID()` | `string_utils.get_uuid()` | 只有 `uploadFilesPdf` 的本地临时目录名用到 |
| `FileUtil.extName(...)` | `file_util.ext_name(...)` | 无后缀返回 `""`，入参 `null` 返回 `None` |
| `FileUtil.copy(is, os, 1024)` | `file_util.io_copy(src, dst)` | `getFile` 写响应流 |
| `CharsetUtil.convert(s, ISO_8859_1, UTF_8)` | `charset_util.convert(...)` | 微信上传的中文文件名还原 |
| `AmazonS3#getObject` / `putObject` / `deleteObject` | `OssTemplate.get_object` / `put_object` / `remove_object` | 四个都是**类级静态方法** |
| `sun.misc.BASE64Decoder` | `base64_utils.decode(...)` | 非法输入返回 `None`（Java 返回 `null`） |
| `HttpServletResponse` | `ResponseSink`（**本切片新增**） | 见 §3.8 |
| `Forest @GetRequest FileApi` | `app/system/service/forest/file_api.py` | `uploadByUrl` 的下载客户端（Phase 2 已落地） |
| `MockMultipartFile` | `multipart_file_util.convert_byte_to_multipart_file` | `uploadByUrl` 把 `byte[]` 包成"文件" |

### 1.3 测试

| 层 | Python 测试文件 | 函数数 → 用例数 | 覆盖点 |
|---|---|---|---|
| Mapper | `tests/test_sys_file_mapper.py` | 30 → **30** | 14 列投影 + `where`/11 个 `<if>` 的判据与**顺序** / `byId` **无** `del_flag` / `byIds` 的 `left join` + `createUserName` / insert 的 `useGeneratedKeys` 回写 / update 13 列传空串**清列** / 两条软删 + 一条**物理**删 / `updateCAFile` 写死 3001 / 分页 |
| Service | `tests/test_sys_file_service.py` | 64 → **84** | 4 个 `fileLog*` 变体的差异 / 白名单是**子串**匹配 / 先登记 vs 先 putObject 的**顺序** / `uploadByUrl` 单条失败**不中断** / pdf 非 pdf 分支 / `success(String)` 重载陷阱 / 5 个死方法 / `ResponseSink` 的异常路径 / base64 非法输入 |
| Controller | `tests/test_sys_file_controller.py` | 61 → **80** | 17 条路由与注册顺序 / **只有 2 个权限点** / `-111111` 魔数 / 被丢弃的 `AjaxResult.error` / 微信上传的 3 条规则 / 两条 `void` 下载路由的头与空 body / `parse_id_array` |

合计 **194** 条（30 + 84 + 80）。加上 Phase 3.14/3.15/3.16 的 332 条，全量从
**1955** 到 **2149**。

---

## 2. 控制器：17 个映射

### 2.1 端点逐条对照

| Java | Python | Method / Path | 权限 |
|---|---|---|---|
| `list` | `list_files` | GET `/system/file/list` | `base:sysflie:list` |
| `getInfoById` | `get_info_by_id` | GET `/system/file/getInfoById/{id}` | **无** |
| `getNewCa` | `get_new_ca` | GET `/system/file/getNewCa` | **无** |
| `getInfo` | `get_info` | GET `/system/file/{ids}` | **无** |
| `upload` | `upload` | POST `/system/file/upload` | **无** |
| `uploadByUrl` | `upload_by_url` | POST `/system/file/uploadByUrl` | **无** |
| `uploadSupplier` | `upload_supplier` | POST `/system/file/uploadSupplier` | **无** |
| `uploadPdf` | `upload_pdf` | POST `/system/file/uploadPdf` | **无** |
| `uploadFileId` | `upload_file_id` | POST `/system/file/uploadFileId` | **无** |
| `uploadFileEnc` | `upload_file_enc` | POST `/system/file/uploadFileEnc` | **无** |
| `updateCAFile` | `update_ca_file` | POST `/system/file/updateCAFile` | **无** |
| `upload`（重载，微信小程序） | `upload_wechat` | POST `/system/file/uploadFile` | **无** |
| `file` | `file` | GET `/system/file/{bucket}/{fileName}` | **无** |
| `fileview` | `file_view` | GET `/system/file/view/{bucket}/{fileName}` | **无** |
| `edit` | `edit` | PUT `/system/file` | **无** |
| `removeById` | `remove_by_id` | DELETE `/system/file/del/{id}` | **无** |
| `remove` | `remove` | DELETE `/system/file/{ids}` | `base:supplier:remove` |

Java 里 `upload` 是**两个同名重载**（一个 `MultipartFile[]`，一个 `HttpServletRequest`），
只看方法名会数成 16 个。Python 按路径拆成 `upload` / `upload_wechat`。

### 2.2 只有两个权限点，而且都"抄错"了

| 端点 | 权限串 | 备注 |
|---|---|---|
| `GET /list` | `base:sysflie:list` | **拼写是错的**（`sysflie`），但 `sys_menu.perms` 也是这么写的 |
| `DELETE /{ids}` | `base:supplier:remove` | 写的是**供应商**模块的权限点，不是 `system:file:remove` |

其余 15 个端点**登录即可**，走 `SecurityConfig` 的 `anyRequest().authenticated()`。

> **不要"顺手修正"**。改成 `base:sysfile:list` 会让文件列表**直接 403** ——
> 因为库里那条菜单的 `perms` 是 `base:sysflie:list`。
>
> `remove` 复用供应商的权限点也是 Java 原样：它本来就是为了删供应商附件而加的。

**回归用例** `tests/test_sys_file_controller.py::TestPermissions` —— 含一条反向用例：
只有 `base:sysflie:list` 能过 `list`，`base:sysfile:list` **反而 403**。

### 2.3 注册顺序（字面量必须在路径变量之前）

`/{ids}` 是**单段**、`/{bucket}/{fileName}` 是**双段**，两者都能吃掉未迁移的
`export` 之类的路径，所以字面量必须排在前面。Python 的实际注册顺序：

```
GET    /list                         ← 先
GET    /getInfoById/{id}
GET    /getNewCa
GET    /{ids}
POST   /upload
POST   /uploadByUrl
POST   /uploadSupplier
POST   /uploadPdf
POST   /uploadFileId
POST   /uploadFileEnc
POST   /updateCAFile
POST   /uploadFile
GET    /{bucket}/{fileName}
GET    /view/{bucket}/{fileName}
PUT    ""
DELETE /del/{id}
DELETE /{ids}
```

两条约束：

1. `/list` / `/getNewCa` 必须在 `/{ids}` 之前，否则被当成 `ids = "list"`；
2. `/getInfoById/{id}` 必须在 `/{bucket}/{fileName}` 之前，否则
   `id = "getInfoById"`、`fileName = "9"`。

`/view/{bucket}/{fileName}` 是三段，与双段规则不冲突，位置随意。

FastAPI 按**注册顺序**匹配（Spring 的 `AntPathMatcher` 是"更具体者优先"）；两者在本类上
结果一致，但这靠的是**顺序**，不是靠框架的偏好。

**回归用例** `tests/test_sys_file_controller.py::TestRouteTable`。

### 2.4 `-111111` 这个魔数

```java
@GetMapping(value = "/{ids}")
public AjaxResult getInfo(@PathVariable String ids) {
    ids = CommonUtil.deleteEnd(ids);
    if (CommonUtil.isBlank(ids)) { ids = "-111111"; }
    return AjaxResult.success(sysFileService.selectSysFileByIds(ids));
}
```

`-111111` 不是合法主键，`in ('-111111')` **必然查空** —— 目的只是**避免**
`in ()` 这种 SQL 语法错误。

`deleteEnd` 只删**一个**结尾逗号：

| 入参 | `delete_end` 之后 | 说明 |
|---|---|---|
| `"1,"` | `""` | 走 `-111111` |
| `"1,2,"` | `"1,2"` | 正常 |
| `"1,2,,"` | `"1,2,"` | 尾部仍有一个逗号 → `"1,2"` 之后还有空段 |
| `","` | `""` | 走 `-111111` |

Service 那边 `ids.split(",")` **不 trim、不过滤空串**，所以 `"1,2,"` 会切成
`["1", "2", ""]` → `in ('1','2','')`。照抄。

**回归用例** `tests/test_sys_file_controller.py::TestGetInfo`、
`tests/test_sys_file_service.py::TestQueries`。

### 2.5 `uploadFileId` 的 `AjaxResult.error` 被**丢弃**

```java
if (CommonUtil.isNull(sysFile.getId()).equals("")) {
    AjaxResult.error("主键不能为空");   // 没有 return，也没有 throw
}
```

返回值没人接、也不回给前端。所以 `id` 为空时**照样往下走**：

1. `base64_convert(entity.files)` 解出文件；
2. `uploadFileId(null, file)` → `fileLogId(file, name, null)`；
3. `deleteSysFileByIdNew(null)` 里的异常被自己的 `catch` 吞掉；
4. 插一条 `id = NULL` 的记录 → MySQL 自增补一个，`result_map["id"] = "null"`。

**不要补 `return`** —— 补了就变成"回一句 500 然后不落库"，是行为改变。

**回归用例** `tests/test_sys_file_controller.py::TestWrite::test_upload_file_id_without_an_id_still_proceeds`。

### 2.6 两条 `void` 下载路由

```java
@GetMapping("/{bucket}/{fileName}")
public void file(String bucket, String fileName, HttpServletResponse response) {
    sysFileService.getFile(bucket, fileName, response);
}
```

行为表：

| 场景 | HTTP | `Content-Type` | body |
|---|---|---|---|
| OSS 正常 | 200 | `application/octet-stream; charset=UTF-8` | 对象字节 |
| OSS 报错 / 文件不存在 | **200** | **不发**（Java 没走到 `setContentType`） | **空** |

即：**下载失败不是 404，是 200 + 空 body**。`get_file` 里的 `catch` 把异常全吞了
（Java 那边连 `log.error` 都被注释掉了）。

Python 侧用 `ResponseSink` 攒字节，再由 `_to_response()` 决定发不发 `Content-Type`。
`view/{bucket}/{fileName}` 是**完全相同的实现**（两套 URL 只是前端习惯不同）。

**回归用例** `tests/test_sys_file_controller.py::TestDownload`、
`tests/test_sys_file_service.py::TestRead`。

### 2.7 `uploadFile`（微信小程序）的三条照抄细节

```java
String original = CharsetUtil.convert(file.getOriginalFilename(), ISO_8859_1, UTF_8);
String ext = FileUtil.extName(original);
if (ext.indexOf("jpg") > -1 || ext.indexOf("jpeg") > -1
        || ext.indexOf("png") > -1 || ext.indexOf("gif") > -1) { } else { return error("上传失败,请上传照片格式的附件！"); }
if (file.getSize() > 1024 * 1024 * 15) { return error("上传失败,你上传的附件大于15M！"); }
```

| # | 细节 | 后果 |
|---|---|---|
| 1 | **没有** `toLowerCase()` | `.JPG` / `.Png` 一律被拒 |
| 2 | `indexOf` 是**子串**匹配，不是等值 | `.mjpg` / `.pngx` 也能过 |
| 3 | 两条失败文案**不同**，逗号是**半角** | 前端按键文案分支 |

`extName` 返回 `""`（无后缀）或 `null`（文件名为 `null`）时，`indexOf` 都不会命中 →
同样回"请上传照片格式"。Java 里 `null.indexOf(...)` 会 NPE，但 `getOriginalFilename()`
在 Spring 里不会是 `null`，所以这条分支实际不可达。

另：`getFile("file")` 是对**单个**部件的读取，所以 Python 声明成单个 `UploadFile`。

**回归用例** `tests/test_sys_file_controller.py::TestWechatUpload`。

### 2.8 两处"读起来像功能、实际是空的"代码

| 位置 | Java 实际行为 | Python 处理 |
|---|---|---|
| `uploadPdf` 的 `HttpServletResponse response` | `out = response.getOutputStream()` 的**下一行**就被 `out = new FileOutputStream(...)` 覆盖 → 响应一个字节都没写过 | 传 `None` 进去，service 明确忽略 |
| `uploadFileEnc` 的 service 方法体 | **整块被注释**，只剩空循环 → 永远 `success([])` | 照抄成空循环 |

**不要"修好"**：前者改了会往响应里写公文包（客户端解析会崩），后者是 CA 加密未启用。

**回归用例** `tests/test_sys_file_service.py::TestUploadPdf`、`TestDeadCode`。

---

## 3. Service：24 个方法（+ 5 个死方法）

### 3.1 方法对照

| Java | Python | 返回 |
|---|---|---|
| `selectSysFileByIds(String)` | `select_sys_file_by_ids(ids)` | `List[SysFile]` |
| `selectSysFileById(Long)` | `select_sys_file_by_id(id)` | `SysFile \| None` |
| `selectSysFileList(SysFile)` | `select_sys_file_list(entity)` | `List[SysFile]` |
| `saveSysFile(SysFile)` | `save_sys_file(entity)` | `AjaxResult` |
| `deleteSysFileByIds(Long[])` | `delete_sys_file_by_ids(ids)` | `AjaxResult` |
| `deleteSysFileById(Long)` | `delete_sys_file_by_id(id)` | `AjaxResult` |
| `uploadFile(MultipartFile)` | `upload_file(file)` | `AjaxResult` |
| `uploadFiles(MultipartFile[])` | `upload_files(files)` | `AjaxResult` |
| `uploadByUrl(List<UploadByUrlRo>)` | `upload_by_url(ro_list)` | `AjaxResult` |
| `uploadFilesUser(MultipartFile[], String)` | `upload_files_user(files, user_id)` | `AjaxResult` —— **无调用方** |
| `uploadSupplier(MultipartFile[], String[])` | `upload_supplier(files, buss_names)` | `AjaxResult` |
| `uploadFilesPdf(MultipartFile[], Response)` | `upload_files_pdf(files, response=None)` | `AjaxResult` |
| `uploadFileId(Long, MultipartFile)` | `upload_file_id(file_id, file)` | `AjaxResult` |
| `uploadFilesEnc(MultipartFile[])` | `upload_files_enc(files)` | `AjaxResult` —— **死方法** |
| `getFile(String, String, Response)` | `get_file(bucket, file_name, response)` | `None`（写 sink） |
| `getFile(String, String, OutputStream)` | `get_file_to_output_stream(...)` | `None` —— **无调用方** |
| `getFileToUrl(String, String, String)` | `get_file_to_url(...)` | `None` —— **无调用方** |
| `updateCAFile(SysFile)` | `update_ca_file(entity)` | `AjaxResult` |
| `getFileUrl(Long)` | `get_file_url(file_id)` | `None` —— **死方法** |
| `uploadBase64Picture(String, SysFile)` | `upload_base64_picture(...)` | `AjaxResult` —— 无控制器调用 |
| `uploadBase64Picture(String)` | `upload_base64_picture_rich_text(...)` | `str \| None` —— **死方法** |
| `uploadFile(InputStream, SysFile)` | `upload_file_from_stream(...)` | `int \| None` —— **死方法** |
| `getFileObject(Long)` | `get_file_object(sys_file_id)` | `S3Object \| None` —— 无控制器调用 |
| `getByteObject(Long)` | `get_byte_object(sys_file_id)` | `bytes \| None` —— 无控制器调用 |

四个私有"登记"方法：`fileLog` → `_file_log`、`fileSupplierLog` → `_file_supplier_log`、
`fileLogId` → `_file_log_id`、`fileLogUser` → `_file_log_user`。
实现类私有（不在接口里）的 `deleteSysFileByIdNew` → `delete_sys_file_by_id_new`。

### 3.2 三个同名重载怎么拆名

| Java 重载 | Python | 为什么这么拆 |
|---|---|---|
| `getFile(..., HttpServletResponse)` | `get_file` | 控制器唯一的调用点 |
| `getFile(..., OutputStream)` | `get_file_to_output_stream` | 按第二参数命名 |
| `uploadFile(MultipartFile)` | `upload_file` | 控制器唯一的调用点 |
| `uploadFile(InputStream, SysFile)` | `upload_file_from_stream` | 按第一参数命名 |
| `uploadBase64Picture(String, SysFile)` | `upload_base64_picture` | 带实体，是"主"重载 |
| `uploadBase64Picture(String)` | `upload_base64_picture_rich_text` | 富文本用，方法体已注释 |

与 `app/common/utils/file_upload_utils.py` 的拆名惯例一致：**最常用者占原名**。

### 3.3 `AjaxResult.success(String)` 与 `success(Object)` 的重载陷阱

```java
String fileId = String.valueOf(ajaxResult.get(DATA_TAG));
...
return AjaxResult.success(fileId);      // 挑中了 success(String msg)
```

`fileId` 是 `String`，Java 重载解析挑的是 `success(String msg)` —— **不是**
`success(Object data)`。于是"上传 base64 图片"返回的是：

```json
{"code": 200, "msg": "<文件id>"}
```

**没有 `data` 键**。Python 照抄成 `AjaxResult.success_message(file_id)`。

> 别"修正"成 `success_data`。`uploadBase64Picture(String richText)` 那半边读的就是
> `MSG_TAG`（虽然它整块被注释了），一旦有人把注释放开，契约就变了。

### 3.4 4 个 `fileLog*` 变体的差异（逐字照抄，别合并）

| 方法 | 写 `bussName` | 走 `saveSysFile` | 写 `del_flag` | 白名单 |
|---|---|---|---|---|
| `_file_log` | 否 | **是** | 是（`"0"`） | 17 个 |
| `_file_supplier_log` | **是** | **是** | 是（`"0"`） | 17 个 |
| `_file_log_id` | 否 | 否（**先物理删、再直插**） | 是（`"0"`） | 17 个 + 1 个死条目 |
| `_file_log_user` | 否 | 否（**直插**） | **否** | 17 个 |

三处坑：

1. **`_file_log_user` 不写 `del_flag`** → 插入的行 `del_flag` 是 `NULL`；而
   `selectSysFileList` 过滤 `del_flag = '0'`，所以这些记录**在列表里查不到**
   （按 id 仍能查到）。`uploadFilesUser` 目前无控制器调用，但行为照抄。
2. **`_SUPPORTED_EXTENSIONS_FOR_ID` 里有一条 `".ppt"`（带点）**，而 `ext` 已经
   `toLowerCase()` 且不含点 —— 这一条**永远匹配不上**。属于既有死代码，照留。
3. 四个变体里都有**重复的** `setCreateUser(...)`（复制粘贴残留），行为无差别。

白名单匹配是 `ext.indexOf(x) > -1` 的**子串**匹配，不是等值：
`ext = "doc"` 会命中 `"doc"`；`ext = "documentx"` 也会命中 `"doc"`。

不支持的扩展名 → `sysFile.id = -1`，**不写库、不 putObject**，但结果数组里仍有这一条
（`id` 为 `"-1"`）。

**回归用例** `tests/test_sys_file_service.py::TestWhitelist`。

### 3.5 `uploadFile` 与 `uploadFiles` 的**顺序相反**

| 方法 | 顺序 | 后果 |
|---|---|---|
| `upload_file`（单） | 先 `putObject`，**再** `fileLog` | 登记失败只留一个孤儿 OSS 对象 |
| `upload_files`（多） | 先 `fileLog`，**再** `putObject` | putObject 失败只留一条孤儿库记录 |

两个都照抄。`upload_file` 没有任何控制器调用，但按原则第 4 条保留。

另外：`upload_files` 遇到**任意一条**抛异常就 `return error(msg)`，
**前面已经成功的条目全部丢弃**（结果数组不再返回）；而 `upload_by_url` 是
**只记日志、继续下一条**。两者语义不同，不要统一。

**回归用例** `tests/test_sys_file_service.py::TestUploadFile` / `TestUploadFiles` / `TestUploadByUrl`。

### 3.6 `uploadFilesPdf`：只对 `pdf` 生效

```java
String ext = FileUtil.extName(file.getOriginalFilename());
if (ext != null && ext.equals("pdf")) { /* 登记 + putObject */ }
else { /* Word->PDF 转换整块被注释；只往本地临时目录写一个文件 */ }
```

三个要点：

1. 判据是 `equals("pdf")` —— **区分大小写**，`.PDF` 走 else 分支；
2. else 分支**不写库、不上传**，只把字节落到
   `{ruoyi.uploadPath}/{uuid}/{fileName}`，结果里**没有 `id` 键**；
3. `_pdf_name` / `_pdf_file_path` 两个变量算完就没人用（转换逻辑被注释），Python 照样算一遍。

`FileUtil.extName` 的 `null`（文件名本身就是 `null`）会让 `ext != null` 为假 → 也走 else。

**回归用例** `tests/test_sys_file_service.py::TestUploadPdf`。

### 3.7 五个死方法（方法体被注释）

| Python | Java 原样 | 返回值 |
|---|---|---|
| `upload_files_enc` | `for (MultipartFile f : files) { /* ... */ }` | 永远 `success([])` |
| `get_file_url` | 方法体注释 | 永远 `None` |
| `upload_base64_picture_rich_text` | 方法体注释，只剩 `if (StrUtil.isBlank(x)) return x;` | 空白原样返回，其余 `""` |
| `upload_file_from_stream` | 方法体注释 | 只返回**新生成的**雪花 id（不写库、不上传） |
| `get_file_to_output_stream` / `get_file_to_url` | **没**被注释，只是没人调用 | 正常实现 |

`upload_file_from_stream` 特别危险 —— 它"看起来成功"但什么都没做。别在别的模块里
拿它当上传入口。

**回归用例** `tests/test_sys_file_service.py::TestDeadCode`。

### 3.8 `ResponseSink`：`HttpServletResponse` 的最小替身

Java 直接往 servlet 的响应流里写字节；FastAPI 的 `Response` 是**不可变**的，所以需要
先攒后发：

```python
class ResponseSink:
    def set_content_type(self, content_type: str) -> None: ...
    def get_output_stream(self) -> BinaryIO: ...
    @property
    def body(self) -> bytes: ...
```

| 字段 | 语义 |
|---|---|
| `content_type` | `set_content_type` 之前是 `None`（= "Java 没设过"） |
| `body` | 攒下来的字节 |

控制器 `_to_response()` 据此决定**发不发** `Content-Type` 头：

```python
if sink.content_type is None:
    return Response(content=sink.body)          # 异常路径：无 Content-Type
return Response(content=sink.body, headers={"Content-Type": sink.content_type})
```

这样连"Java 的异常路径不带 `Content-Type`"都对齐了。别换成
`StreamingResponse` —— 它会在 try 之外抛错，破坏"异常吞掉"的语义。

### 3.9 base64 上传：`BytesIO(None)` 不会报错

```python
decoded = base64_utils.decode(base64_picture)
...
if decoded is None:
    raise ValueError("Base64 解码结果为空")
byte_array_input_stream = BytesIO(decoded)
```

**这是本切片修掉的唯一一个真实缺陷**。`sun.misc.BASE64Decoder.decodeBuffer`
遇到非法输入返回 `null`，Java 的 `new ByteArrayInputStream(null)` 抛 NPE → 落到
`catch` → `AjaxResult.error()`。而 CPython 的 `BytesIO(None)` **等价于空缓冲区**，
不会报错 —— 照直翻译的话，非法 base64 会被"成功"上传成一个 0 字节对象。

所以必须**显式判空**。见 §36.1。

**回归用例** `tests/test_sys_file_service.py::TestBase64Picture::test_a_malformed_base64_falls_into_the_error_branch`。

---

## 4. Mapper：9 条 statement

### 4.1 方法对照

| Java（XML `id`） | Python |
|---|---|
| `selectSysFileVo`（`<sql>`） | `SELECT_SYS_FILE_VO` 常量 |
| `selectSysFileByIds` | `select_sys_file_by_ids` |
| `selectSysFileById` | `select_sys_file_by_id` |
| `selectSysFileList` | `select_sys_file_list` |
| `insertSysFile` | `insert_sys_file` |
| `updateSysFile` | `update_sys_file` |
| `deleteSysFileById` | `delete_sys_file_by_id` |
| `deleteSysFileByIds` | `delete_sys_file_by_ids` |
| `deleteSysFileByIdNew` | `delete_sys_file_by_id_new` |
| `updateCAFile` | `update_ca_file` |

VO 的 14 列（顺序即 SQL 顺序）：
`t.id, t.file_name, t.bucket_name, t.original, t.type, t.file_size, t.buss_type,
t.buss_name, t.create_user, t.create_time, t.update_user, t.update_time, t.del_flag,
t.tenant_id`。

### 4.2 列表 SQL：硬编码 `where` + 11 个 `<if>`

XML 里**没有** `<where>` 标签，第一行就是 `where t.del_flag = '0'`，后面每个 `<if>` 自带
`and`。所以 Python 侧条件片段**不带**前导 `AND`，统一用 `"\nand "` 连接。

| 字段 | Java 判据 | `""` | `None` | 运算符 |
|---|---|---|---|---|
| `id` | `!= null and != ''` | **发出去**（数字比较，`''` 恒不成立） | 跳过 | `=` |
| `original` / `type` / `bussType` / `createUser` / `updateUser` | `!= null and != ''` | 跳过 | 跳过 | `=` |
| `fileName` / `bucketName` / `bussName` | `!= null and != ''` | 跳过 | 跳过 | `like concat('%', ?, '%')` |
| `fileSize` / `tenantId` | `!= null` | **发出去** | 跳过 | `=` |

> `id` 是 `Long`，`!= ''` 这一半在 OGNL 里对数字等价于"恒真"，所以**实际**只有
> "非 null"一个判据。Python 侧 `value == ""` 对 `int` 永远不成立，自然一致 ——
> 但**如果**有人用 `model_construct` 塞进 `""`，Python 会**跳过**而 Java 会**发出去**。
> 这个分支从 HTTP 不可达（pydantic 的 `BeforeValidator` 会把 `""` 归一成 `None`）。

`order by t.create_time desc,t.id` 是**自带**的 —— 不会追加客户端 `orderByColumn`，
前端点表头排序对这张表**不生效**（与 `sys_config` 相反）。

11 个条件的**顺序**也与 XML 逐条一致（`_LIST_CONDITIONS`），所以拼出的 SQL 与 MyBatis
的输出**逐字相同**，慢查询日志可以直接对比。

**回归用例** `tests/test_sys_file_mapper.py::TestSelectList`
（含 `test_the_conditions_keep_the_xml_order`）。

### 4.3 `selectSysFileByIds` 多带一个 `createUserName`

只有这一条 select 会：

```sql
left join sys_user t2 on t.create_user = t2.user_id and t2.del_flag = '0'
```

把 `t2.nick_name` 别名为 `createUserName`。于是：

- 按逗号串批量查能拿到"创建人姓名"，按 id 查 / 列表查拿不到（`null`）；
- `create_user` 是 **String** 而 `sys_user.user_id` 是 **bigint**，MySQL 会做隐式
  类型转换 —— 非数字的 `create_user` 被转成 `0` 而不是报错（照抄）。
- `<foreach>` 空数组会拼出 `in ()` → SQL 语法错（Java 同样）。

### 4.4 `selectSysFileById` **没有** `del_flag` 过滤

```sql
select <include refid="selectSysFileVo"/> from sys_file t where t.id = #{id}
```

与列表（始终带 `del_flag = '0'`）**不对称**：被软删除的记录仍能按 id 查到。
影响 `GET /system/file/getInfoById/{已删除的id}`：回整条记录而不是空信封。

**回归用例** `tests/test_sys_file_mapper.py::TestSelectById::test_there_is_no_del_flag_filter`。

### 4.5 `insert` / `update` 的列

| 语句 | 列数 | 判据 | 备注 |
|---|---|---|---|
| `insertSysFile` | **14**（`id` … `tenant_id`） | 全部 `!= null` | 有 `useGeneratedKeys`；`files` / `createUserName` **不在**列里 |
| `updateSysFile` | **13**（无 `id`） | 全部 `!= null` | 传 `""` 会**清列**；`id` 只出现在 `where` 里 |

`insertSysFile` 的 `useGeneratedKeys="true" keyProperty="id"` 在 XML 里有，但
**实际永不触发** —— service 在插入前已经赋了雪花 id。Python 仍然实现回写
（只在 `entity.id is None` 时），保持与 XML 同形。

`""` 的区别只体现在**列表查询**上，不体现在 insert/update。

**回归用例** `tests/test_sys_file_mapper.py::TestInsert` / `TestUpdate`。

### 4.6 两条软删 + 一条**物理**删

```sql
update sys_file set del_flag = '1' where id = :id            -- deleteSysFileById
update sys_file set del_flag = '1' where id in (:p0, :p1)    -- deleteSysFileByIds
delete from  sys_file  where id = :id                        -- deleteSysFileByIdNew
```

`deleteSysFileByIdNew` 是本模块**唯一**的硬删除，两个调用点：

1. `_file_log_id`（`uploadFileId` 的"先删后插"）—— 把已有 id 的记录物理删掉再插一条新的；
2. `delete_sys_file_by_id_new` ← `updateCAFile` 先删 `id = 3001`。

注意 XML 里 `delete from  sys_file  where` 是**双空格**（照抄，不影响语义）。

**回归用例** `tests/test_sys_file_mapper.py::TestDelete`。

### 4.7 `updateCAFile` 把主键写死成 3001

```sql
update sys_file set id = 3001 where id = #{id}
```

- `3001` 是**魔数**：CA 驱动程序固定占这个主键；
- `#{id}` 取的是**参数对象**的 `id`，不是 Mapper 接口方法声明的类型
  （接口写的是 `updateCAFile(SysFile)`，XML 的 `parameterType` 却写 `Long` ——
  既有不一致，不影响运行）；
- `update_ca_file` 返回的是 `AjaxResult.success("操作成功！", sysFile.getId())`，
  即**改之前**的那个 `id`，不是 `3001`。

**回归用例** `tests/test_sys_file_mapper.py::TestUpdate`、
`tests/test_sys_file_service.py::TestCa`。

---

## 5. 实体：`SysFile`（**不继承** `BaseEntity`）

### 5.1 14 个自有字段

| Java 字段 | Python | 类型 | 说明 |
|---|---|---|---|
| `id` | `id` | `JavaLong` → JSON **字符串** | 雪花 id |
| `fileName` | `file_name` | `Optional[str]` | OSS 上的 key（UUID + 后缀） |
| `bucketName` | `bucket_name` | `Optional[str]` | 桶名 |
| `original` | `original` | `Optional[str]` | 用户设备的原始文件名（可能是中文） |
| `type` | `type` | `Optional[str]` | 小写后缀 |
| `fileSize` | `file_size` | `JavaLong` | 字节数 |
| `bussType` | `buss_type` | `Optional[str]` | 业务类型 |
| `bussName` | `buss_name` | `Optional[str]` | 业务名称（供应商代理证有效期等） |
| `createUser` | `create_user` | `Optional[str]` | **String**，不是 `Long` |
| `createTime` | `create_time` | `Optional[datetime]` | `@JsonFormat(yyyy-MM-dd HH:mm:ss)` |
| `updateUser` | `update_user` | `Optional[str]` | **String** |
| `updateTime` | `update_time` | `Optional[datetime]` | 同上 |
| `delFlag` | `del_flag` | `Optional[str]` | `0` 存在 / `1` 删除 |
| `tenantId` | `tenant_id` | `JavaLong` | 所属租户 |

### 5.2 不继承 `BaseEntity` 的三个后果

1. **没有** `searchValue` / `remark` / `params` 三件套 —— 请求体里带 `params[beginTime]`
   不会被绑定（前端这张表本来也没有时间范围筛选）；
2. 审计列类型与 `BaseEntity` **相反**：`createUser` / `updateUser` 是 `String`，
   而 `BaseEntity.updateBy` 是 `Long`。service 里写的是
   `sysFile.setCreateUser(userId.toString())`，转换发生在**赋值那一刻**；
3. 时间字段的 `@JsonFormat` 得自己声明（没有基类可继承）。

### 5.3 `id` 序列化成**字符串**

```java
@JsonSerialize(using = ToStringSerializer.class)
private Long id;
```

19 位雪花 id 超过 JS 的 `Number.MAX_SAFE_INTEGER`（16 位），发数字会丢精度。
**这是线上契约**：响应里 `"id": "1234567890123456789"`。

Python 内部仍是 `int`（要参与 SQL 的 id 比较），只在 `field_serializer` 里转 `str`。

### 5.4 两个"临时字段"

| 字段 | 来源 | 落库？ |
|---|---|---|
| `files` | 前端把 base64 图片串放在这里（`uploadFileId` 读它） | **否** —— 14 个插入列里没有 |
| `createUserName` | 只由 `selectSysFileByIds` 的 `left join` 填 | **否** —— 列表 / 按 id 查都是 `null` |

两个都带 `@Excel`（`files` 的注解名还写成了 `"文件s"`），是 Excel 导出的列名。
`ExcelUtil` 尚未迁移，见 MIGRATION_PROGRESS §4。

### 5.5 `JavaLong` 的 `BeforeValidator`

`id` / `fileSize` / `tenantId` 三个 `Long` 字段都套了
`Annotated[Optional[int], BeforeValidator(_empty_string_as_none)]`：前端清空数字输入框时
发的是 `""`，Jackson 给 `null`，pydantic 默认会直接报错。

---

## 6. 未迁移 / 未对齐

| 项 | 原因 | 影响 |
|---|---|---|
| `@Log(title = "文件" / "文件管理", ...)` | 操作日志切面未迁移 | 10 个写操作不写 `sys_oper_log`（§36.2） |
| `@Transactional` | 见 COMPATIBILITY §28.3 | 每条 SQL 独立提交 |
| `@Validated` | Java 本来就没有 | 无差异：空 body 也接受 |
| Excel 列注解（`@Excel`） | `ExcelUtil` 未迁移 | 本类**没有** `export` 端点，所以当前无影响 |

> 与其它 7 个切片不同：本控制器**没有 `export`**，所以不受 `ExcelUtil` 缺口影响。
> `sys_file` 的 `@Excel` 注解只是实体上的"备用元数据"，没有对应端点。
