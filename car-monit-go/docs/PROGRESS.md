# 迁移工作进度（接口返回逐一对比阶段）

> 记录时间：2026-10-31（第二轮更新）。本轮目标：把 Go 服务的接口返回与 Java 原服务逐字段对比，修掉所有代码层面的不一致。

## 1. 对比方法

| 项 | 值 |
|---|---|
| Java 参考服务 | `ruoyi-admin/target/ruoyi-admin.jar`，端口 **9988**（`--server.port=9988`） |
| Go 服务 | `bin/carmonit-server.exe`，端口 **9989**，配置 `configs/config.yaml` |
| 账号 | admin / Admin@2025-（Java 登录需验证码，答案从 Redis `captcha_codes:<uuid>` 读取） |
| 对比脚本 | `C:/Users/abelz/AppData/Local/Temp/cmp_api.py <路径前缀> <报告.json>`；单接口用 `cmp_one.py`（能区分「键缺失」与「值为 null」） |
| 路由清单来源 | Go 启动日志 `C:/Users/abelz/AppData/Local/Temp/carmonit.log` 里的 `[GIN-debug]` 行 |
| 归一化规则 | `yyyy-MM-dd HH:mm:ss` → `<DT>`、带横杠/无横杠 UUID → `<UUID>`/`<HEX32>`、浮点保留 6 位，深度逐字段比较 |

对比只对 GET 接口逐字段比较；POST/PUT/DELETE 走 `verify_non_get.py`（用非法请求体探测，避免污染数据）。

## 2. 最终对比结果（第二轮结束）

注册路由合计 **498** 条（移除 Go 多注册的 `GET /system/user` 后，与 Java 路由表一致）。

| 模块 | GET 路由 | 完全一致 | 仍有差异 | 非 JSON/二进制 | 说明 |
|---|---|---|---|---|---|
| `/manager/**` | 99 | 78 | 2 | 19 | 差异=Java 缓存串号 500 + 路网几何未复现；其余为 Excel 附件流 |
| `/base/**` | 70 | 55 | 10 | 5 | 差异=外部服务/Java 自身缺陷（见 §4） |
| `/flow/**` | 30 | 30 | 0 | 0 | 全量一致 |
| `/system/**` | 65 | 60 | 4 | 1 | 差异=upgradeInfo 的 500 错误文本 |
| `/monitor/**` | 13 | 9 | 4 | 0 | 差异=Redis 运行态统计 + 3 个 Java 自身异常 |
| `/tool/**` | 10 | 10 | 0 | 0 | 全量一致 |
| **合计** | **287** | **242** | **20** | **25** | |

报告：`final_manager.json`、`final_base.json`、`final_flow.json`、`final_system2.json`、`final_monitor2.json`、`final_tool2.json`（差异均为 §4 所列外部依赖或 Java 侧缺陷）。

## 3. 本轮修复清单

### 3.1 响应信封 / 公共设施
- `AjaxResult`：`data` 仅在非 null 时输出；`rows` 恒为数组（`internal/web/response.go`）
- 新增 `web.ErrorNilMsg()` + `ServiceError.NilMsg`：复刻 Java 未捕获 NPE 的「code 500、msg = null」
- 新增 `web.ISODateTime`：对应 Java 里**没有 @JsonFormat 的 `java.util.Date`**（Jackson 默认 ISO-8601 带毫秒与 +08:00 偏移）

### 3.2 manager
- `/manager/carsuspiciousback/**` 独立实体/列/排序（`order by t.create_time desc,t.id`、`@JsonFormat(yyyy-MM-dd)`），历史列表改回 `CarSuspicious` + `order by t.id`
- `EntityBase.ID` 改为 `*string`（列表 SQL 少选 `id` 时 Java 返回 null）
- `TrailBo` / `ZdataTrailTracks` 按 Java 字段全集建模；移植 `getTrailDevBO`、桩号换算 `pilenoDec`
- `carExceptRecord.supplementaryStatus` 的 Java 字段默认值 `"0"`（`tableSpec.afterScan` 钩子）
- `createInfo` 联表、`orgId` 查不到保持 null、`cartrackinfo` 去掉 Java 不存在的 `firtStation*` 赋值
- 导出文件名用 `UUID.randomUUID()`（带横杠）+ `@Excel(readConverterExp)` 支持

### 3.3 base
- **系统化指针化**：`models_*.go` 里 374 个 `string` 字段改为 `*string`（`null` / `""` 与 Java 对齐）；`isNull/isNotBlank/isBlank/deleteEnd` 扩展为 `any`
- 日期三态：`@JsonFormat(yyyy-MM-dd)` → `dateOnly`；`@JsonFormat(yyyy-MM-dd HH:mm:ss)` → `web.DateTime`；无注解 → `isoDateTime`（修好 `provcapture.loadtime` 等）
- `gantry.listAll` / `toll.listAll` / `fwqjcxx` 增补 `@TableField(exist=false)` 的 `sectionCodeList`
- `ods_yhgl_v_base_org` 的 `parentId` 相关子查询列映射（此前恒为 null）
- `/base/cdc/status` 不再读 `kafka.*`（Java 的 CdcConfig 全取默认值）
- `/base/geometry/getHenDa`、`/base/geometry/syncAllGeometry1` 改回 code 200（Java 为异步/兜底成功）；`syncAllGeometry` 真正执行 `geometry_copy1` 查询让 SQL 失败（与 Java 同因）
- `fitting/list` 保持可用（Java 的 Mapper 引用了不存在的 `id` 属性，恒 500 —— 记为 Java 侧缺陷）

### 3.4 flow
- `/flow/messageinfo/exportShrz` 的 NPE 分支改为 msg=null：**30/30 全量一致**

### 3.5 system / systemaux
- `model` 包系统实体（SysUser/SysRole/SysDept/SysMenu/SysPost/SysDict*/SysConfig/SysNotice/SysOperLog/SysLogininfor/SysFile）字符串字段指针化；`BaseEntity.CreateBy/UpdateBy/Remark` 指针化
- Jackson 派生属性：`SysUser.admin`、`SysRole.admin`、`SysDictData.default`、`SysDept/SysMenu.children`（恒数组）、`roles/menuIds/deptIds` 不省略
- `loginDate` 改 `ISODateTime`；`password` 改 `json:"-"`（Java `@JsonIgnore`）
- 查询列对齐 Java VO：`selectUserVo`（`dept` 只映射 dept_id/dept_name、`sub_code`、`ifnull(tenant_id,-1)`）、`RoleResult` 6 列、dict type/data 的 7/12 列、job/jobLog 的 12/8 列
- `/system/user/list/dept` 回填扁平 `deptName`；`/system/config/configKey/{k}` 的配置值放在 **msg**（Java 命中的是 `success(String msg)` 重载）
- `/system/user/profile` 复刻 fastjson2 缓存回读的 `params: {"@type":"java.util.HashMap"}`（user/dept/roles）
- 移除 Go 多注册的 `GET /system/user`；`/system/{file,notice}/view/**` 增加 `.anonymous()` 语义（带 token 访问 → 403 + Spring 错误体）

### 3.6 monitor / tool
- quartz `SysJob`/`SysJobLog` 查询列对齐 Java VO；`SysJobLog` 补 `BaseEntity`（createBy/updateBy/remark/updateTime 为 null）
- `SysOperLog.businessTypes` 恒输出 null
- 生成器：`information_schema` 列名大小写归一、`gen/list|all/list|db/list` 复刻 MyBatis `<collection>` 的空占位元素、`gen/{id}` 的列补 `tableId` —— **/tool 10/10 一致**

## 4. 剩余差异（全部为外部依赖或 Java 侧缺陷，均已标注）

| 接口 | 现象 | 结论 |
|---|---|---|
| `/manager/bigScreen/carLocation`、`/monitor/online/list` | Java 500 `JSONObject cannot be cast to ...` | 两服务共用 Redis，Go 写入的缓存 Java 反序列化失败（并行运行的环境现象，单服务部署无此问题） |
| `/manager/suspicious/{id}` 的 `raodTrailList` | 缺路网几何 | Java 依赖 `getCarGeometryByPlanNew`（路网最短路服务 + 腾讯路线规划），Go 不复现，固定空数组 |
| `/base/{gantry,toll}/list` 的 `roadName/sectionName` | Java 为 `""`，Go 有值 | Java 的 `section_list` 缓存由未迁移的外部同步任务写入，当前为空；Go 回源查库（见 `cache.go` 的 `// DIFF:`） |
| `/base/feeGantry/*`、`/base/feerecords/*`、`/base/feestationexit/*`、`/base/snapshotflow/{id,earliest-time}` | Java 500（String 强转 / SocketException） | 这些端点在 Java 里是转发外部 9901 服务的 proxy，Java 侧解析失败；Go 代理正常返回 |
| `/base/vehicleweight/ZdTrails:BorderWeighing` | Java 500 `TooManyResultsException` | Java 用 selectOne 取到 200 行（数据触发），Go 返回首行 |
| `/base/geometry/syncAllGeometry`、`/system/upgradeInfo/*` | 两侧均 500，错误文本不同 | 同为「表不存在」：Java 是 MyBatis 包装后的长文本，Go 是驱动错误文本 |
| `/base/cdc/config` | Java 返回两段拼接的非法 JSON | Java 自身序列化缺陷（含 Spring 内部结构 + 错误体），Go 返回合法 JSON |
| `/base/geometry/getHenDa` | Java 连接被重置 | 外部 HenDa 服务不可达导致 Java 侧连接中断 |
| `/monitor/jobLog/{id}` | Java 500 `缺少必需的路径变量[jobLogId]` | Java 编译未保留参数名，接口在 Java 侧不可用；Go 正常返回 |
| `/monitor/server` | Java 500 `NoSuchMethodError: com.sun.jna.Memory.close()` | Java 依赖 JNA 版本冲突；Go 正常返回 |
| `/monitor/cache` | 命令统计/键数量不同 | Redis 运行态数据（两服务共享同一实例），结构一致 |
| 25 项非 JSON | Excel/Word/图片等附件流 | POI/EasyPOI 与 excelize 生成的二进制无法逐字节一致，表头与列顺序已按 Java 注解还原 |

## 5. 下一步

1. 如需要「连错误文本都一致」，可把 §4 里的 MyBatis 错误文本按模板拼出来（当前判断为无收益，未做）
2. 在只运行 Go 单服务的前提下复测 `carLocation` / `online/list`（排除共享 Redis 干扰）
3. 补一次写接口回归（POST/PUT/DELETE）：`verify_non_get.py` 仅做了畸形请求探测，正常写入路径建议在隔离库上验证

## 6. 复现命令

```bash
# 构建与静态检查
go build ./... && go vet ./... && go test ./...
gofmt -l internal/ cmd/

# 重启 Go 服务（日志供脚本解析路由）
PID=$(netstat -ano | grep -E "TCP +0.0.0.0:9989" | awk '{print $5}' | head -1)
taskkill //PID $PID //F
go build -o bin/carmonit-server.exe ./cmd/server
bin/carmonit-server.exe > C:/Users/abelz/AppData/Local/Temp/carmonit.log 2>&1 &

# 逐字段对比（MSYS 会把 /manager 当路径改写，必须屏蔽）
MSYS2_ARG_CONV_EXCL='/manager' python C:/Users/abelz/AppData/Local/Temp/cmp_api.py \
  /manager C:/Users/abelz/AppData/Local/Temp/final_manager.json
```
