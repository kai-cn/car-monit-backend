# MAPPING_SYS_DEPT.md — `sys_dept` 切片 Java ↔ Python 对照表

> 给熟悉 Java 的同事查表用。**第一列永远是 Java 的位置**，第二列是 Python 的对应物。
> 表里只写"叫什么、在哪、和 Java 哪里不一样"；为什么这么写，看对应文件的模块 docstring。
>
> 行为差异（客户端/运维需要知道的）不在本文件，见 [COMPATIBILITY.md](COMPATIBILITY.md) §27。

阅读约定：

- `# Migrated from:` 在每个 Python 文件第 1-4 行，指向它对应的 Java 文件；
  逐方法的对应写在 `# Java:` 行注释里，可直接全文搜索 `# Java:`。
- Python 用 `snake_case`，Java 用 `camelCase`。转换规则是机械的：
  `selectDeptList` → `select_dept_list`，`treeLeavel` → `tree_leavel`。
- 一个 Java 文件不一定对一个 Python 文件：接口与实现（`ISysDeptService` + `SysDeptServiceImpl`）
  在 Python 里合并成一个类，因为 Python 没有"接口"这个概念。
- **`treeLeavel` 的拼写（`Leavel` 而不是 `Level`）是刻意保留的**：它同时是列名和前端读的
  JSON 键，改了就断。

---

## 1. 文件级对照

### 1.1 主链路

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-admin/.../web/controller/system/SysDeptController.java` | `app/api/system/sys_dept_controller.py` | 11 个映射全部迁移 |
| `ruoyi-system/.../service/ISysDeptService.java`<br>`ruoyi-system/.../service/impl/SysDeptServiceImpl.java` | `app/system/service/sys_dept_service.py` | 接口 + 实现合并为 `SysDeptService`；16 个接口方法 + 6 个 `private` 辅助 |
| `ruoyi-system/.../mapper/SysDeptMapper.java`<br>`ruoyi-system/src/main/resources/mapper/system/SysDeptMapper.xml` | `app/system/mapper/sys_dept_mapper.py` | 接口 + XML 合并：16 条 statement 各变成一个模块级 SQL 常量 |
| `ruoyi-common/.../core/domain/entity/SysDept.java` | `app/common/core/domain/entity/sys_dept.py` | 27 个业务字段 + `BaseEntity`；含 `DEPT_CONSTRAINTS` |
| `ruoyi-common/.../core/domain/TreeSelect.java` | `app/common/core/domain/tree_select.py` | **新增**，`sys_dept` 是第一个用它的切片 |
| `ruoyi-common/.../utils/CommonUtil.java` | `app/common/utils/common_util.py` | 只用了 `isNull(Object)` |
| `ruoyi-common/.../core/domain/BaseEntity.java` | `app/common/core/domain/base_entity.py` | `createBy` / `updateBy` / `remark` / `params` ... |
| `ruoyi-common/.../constant/UserConstants.java` | `app/common/constant/user_constants.py` | `UNIQUE_OLD = "0"` / `NOT_UNIQUE_OLD = "1"` / `DEPT_NORMAL` / `DEPT_DISABLE` |
| `ruoyi-common/.../core/controller/BaseController.java` | `app/common/core/controller/base_controller.py` | 本切片用到 `bind_query_params` + `to_ajax` |
| `javax.validation.constraints.*`（`@NotBlank` / `@Size` / `@Email`） | `app/common/utils/bean_validation.py` | `@Email` 是本切片新增的第三个约束，见 §5 |

### 1.2 横切（本切片用到的部分）

| Java | Python | 说明 |
|---|---|---|
| `ruoyi-framework/.../web/service/PermissionService.java`（`@ss.hasPermi`） | `app/framework/web/service/permission_service.py` | `@pre_authorize_permi("...")` |
| `ruoyi-framework/.../aspectj/DataScopeAspect.java` | `app/framework/aspectj/data_scope_aspect.py` | 调了，但**不生效**，见 COMPATIBILITY §27.1 |
| `ruoyi-framework/.../aspectj/LogAspect.java` | **未迁移** | 因此不写 `sys_oper_log`，见 §27.2 |
| `ruoyi-common/.../utils/SecurityUtils.java` | `app/common/utils/security_utils.py` | `get_username()` / `get_tenant_id()` / `get_eps_id()` |
| `ruoyi-system/.../mapper/SysRoleMapper.java`（`selectRoleById`） | `app/system/mapper/sys_role_mapper.py` | 只为了读 `deptCheckStrictly` |
| `Hibernate Validator`（`MethodArgumentNotValidException`） | `bean_validation.validate()` + `RuntimeError` 处理器 | 见 §5 |
| `org.apache.commons.lang3.ArrayUtils.contains` | `app/common/utils/string_utils.split` | `excludeChild` 用 |

### 1.3 测试

| 层 | Python 测试文件 | 用例数 | 覆盖点 |
|---|---|---|---|
| Mapper | `tests/test_sys_dept_mapper.py` | 42 | 16 条 SQL 的拼装 / 14 个 `<if>` 顺序 / `<set>` 判据差异 / `${}` 拼接 / 投影 |
| Service | `tests/test_sys_dept_service.py` | 51 | `sub_code` 三级补零 / 建树 / `updateTenantId` 全表扫描 / `getQxSql` 降级 |
| Controller | `tests/test_sys_dept_controller.py` | 90 | 路由表 / 6 个权限点 / 校验先于权限 / `flag` 分支表 / 三道闸 |

合计 **183** 条；全量套件 **905 passed**。

Java 侧 **没有任何 `src/test`**，所以上表没有"Java 对应用例"列 ——
这些用例是照着 Java 源码逐行推导出来的，不是移植过来的。

---

## 2. 控制器：11 个映射逐条对照

前缀都是 `/system/dept`。`权限` 列是 `@PreAuthorize("@ss.hasPermi(...)")` 的值；
写 `登录` 表示**没有注解**，只要求通过认证。

| # | Java 方法 | Python 函数 | HTTP + 路径 | 权限 |
|---|---|---|---|---|
| 1 | `list(SysDept dept)` | `list_depts(dept: DeptParam)` | `GET /system/dept/list` | `system:dept:list` |
| 2 | `getList(SysDept dept)` | `get_list(dept: DeptParam)` | `GET /system/dept/getList` | **登录** |
| 3 | `excludeChild(Long deptId)` | `exclude_child(dept_id: int)` | `GET /system/dept/list/exclude/{deptId}` | `system:dept:list` |
| 4 | `getInfo(Long deptId)` | `get_info(dept_id: int)` | `GET /system/dept/{deptId}` | `system:dept:query` |
| 5 | `treeselect(SysDept dept)` | `treeselect(dept: DeptParam)` | `GET /system/dept/treeselect` | **登录** |
| 6 | `treeselectNew(SysDept dept)` | `treeselect_new(dept: DeptParam)` | `GET /system/dept/treeselectNew` | **登录** |
| 7 | `roleDeptTreeselect(Long roleId)` | `role_dept_treeselect(role_id: int)` | `GET /system/dept/roleDeptTreeselect/{roleId}` | **登录** |
| 8 | `add(SysDept dept)` | `add(dept: ValidDept)` | `POST /system/dept` | `system:dept:add` |
| 9 | `edit(SysDept dept)` | `edit(dept: ValidDept)` | `PUT /system/dept` | `system:dept:edit` |
| 10 | `remove(Long deptId)` | `remove(dept_id: int)` | `DELETE /system/dept/{deptId}` | `system:dept:remove` |
| 11 | `getCompanyList()` | `get_company_list()` | `GET /system/dept/getCompanyList` | **登录** |

### 2.1 `list` 与 `getList` 完全重复，但**不要合并**

两个方法的函数体一字不差（都 `return AjaxResult.success(deptService.selectDeptList(dept))`，
都**不分页**），区别只有 `getList` 没有 `@PreAuthorize`。权限差异是实质性的：
前端下拉框用 `getList`（普通用户要能取部门），列表页用 `list`（要权限点）。

### 2.2 形参绑定的两套写法

| Java 形参 | 绑定来源 | Python |
|---|---|---|
| `SysDept dept`（**无**注解） | query string | `DeptParam = Annotated[SysDept, Depends(_query_dept)]` |
| `@Validated @RequestBody SysDept dept` | JSON body | `ValidDept = Annotated[SysDept, Depends(_validated_dept)]` |
| `@PathVariable Long deptId` | 路径 | `dept_id: int`（FastAPI 直接转换） |
| `@PathVariable Long roleId` | 路径 | `role_id: int` |
| 无参数 | — | `get_company_list()` |

`remove` 的 Java 形参是**单个** `Long deptId`（不是 `Long[]`），与 `sys_post` 的
`remove(Long[] postIds)` 不同 —— 部门不支持批量删除，不要照抄 `parse_id_array`。

### 2.3 声明顺序：为什么六个字面量路径必须写在 `/{dept_id}` 之前

FastAPI **按注册顺序**匹配。`/system/dept/treeselect` 若排在 `/system/dept/{dept_id}` 之后，
会被当成 `dept_id = "treeselect"`，随后在 `int` 转换处炸掉（HTTP 422）。
Spring 的 `AntPathMatcher` 优先匹配字面量，所以两侧结果一致 —— 但 Python 侧必须靠
**书写顺序**保证。

顺序（文件里的实际顺序）：

```
/list            /getList          /list/exclude/{dept_id}
/treeselect      /treeselectNew    /roleDeptTreeselect/{role_id}
/getCompanyList  /{dept_id}        POST ""   PUT ""   DELETE /{dept_id}
```

`tests/test_sys_dept_controller.py::TestRouteTable::test_literal_paths_come_before_the_path_variable`
是这条约束的防回退阀。

### 2.4 `treeselectNew` 的 `flag` 分支表

Java 用 `CommonUtil.isNull(flag)` 先归一（`null` → `""`，并 `trim`），然后：

| `flag` | Java | Python | 效果 |
|---|---|---|---|
| `myDept` / `myDeptCg` | `dept.setTenantId(getTenantId())` | 同 | 本单位 |
| `sjzbDept` / `sjzbDeptCg` | `dept.setDataId(getTenantId() + "")` | 同 | 上级有资格的招标单位 |
| `isUint` | `dept.setIsUint("1")` | `UNIT_FLAG` | 只查单位 |
| `allDept` | 空分支 | `pass` | 查全部 |
| `onlyMyDept` | `dept.setDeptId(getEpsId())` | 同 | 自己所在部门 |
| **其他 / 空** | `dept.setDeptId(-1L)` | 同 | **查一个不存在的部门，结果是空列表** |

最后一行是最容易改错的：`else` 不是"查全部"，是"查不到"。前端不传 `flag` 时会拿到空树，
这是 Java 的现状（见 COMPATIBILITY §27.1 关于数据权限的讨论）。

### 2.5 `edit` 的三道闸，顺序不能换

```python
if _is_not_unique(check_dept_name_unique(dept)):                 # ① 同父下重名
    return AjaxResult.error_message(EDIT_DEPT_NAME_EXISTS)
elif _same_id(dept.parent_id, dept.dept_id):                      # ② 上级不能是自己
    return AjaxResult.error_message(EDIT_DEPT_SELF_PARENT)
elif DEPT_DISABLE == dept.status and select_normal_children_dept_by_id(...) > 0:
    return AjaxResult.error_message(EDIT_DEPT_HAS_ACTIVE_CHILD)   # ③ 停用前不能有未停用子部门
```

- ② 用的是 `dept.getParentId().equals(dept.getDeptId())`：**`parentId` 为 `null` 时 NPE**
  （落 500），所以前端保存时必须带 `parentId`。Python 的 `_same_id` 同样抛 `AttributeError`，
  不能写成 `left == right`（`None == None` 会变 `True`）。
- ③ 只在 `status == DEPT_DISABLE`（`"1"`）时才查子部门；`status` 为 `"0"` 时连查都不查。
- 文案里的感叹号是**全角** `！`，`remove` 的两条是**半角**逗号 `,`。

---

## 3. 服务层：`ISysDeptService` / `SysDeptServiceImpl`

16 个接口方法 + 6 个 `private` 辅助方法全部迁移。

| # | Java | Python | 备注 |
|---|---|---|---|
| 1 | `selectDeptList(SysDept dept)` | `select_dept_list` | 调 `apply_data_scope`，但 SQL 里没有片段（§27.1） |
| 2 | `selectDeptById(Long deptId)` | `select_dept_by_id` | 无行返回 `None` |
| 3 | `selectHeadOffice()` | `select_head_office` | 返回 `List`/`None`；**身份去重**，不是按 id |
| 4 | `selectDeptListByRoleId(Long roleId)` | `select_dept_list_by_role_id` | 先查角色拿 `deptCheckStrictly` |
| 5 | `selectNormalChildrenDeptById(Long deptId)` | `select_normal_children_dept_by_id` | 返回**原始计数** |
| 6 | `hasChildByDeptId(Long deptId)` | `has_child_by_dept_id` | `count > 0` → `bool` |
| 7 | `checkDeptExistUser(Long deptId)` | `check_dept_exist_user` | `count > 0` → `bool` |
| 8 | `checkDeptNameUnique(SysDept dept)` | `check_dept_name_unique` | 返回 `"0"`/`"1"` **字符串** |
| 9 | `buildDeptTree(List<SysDept> depts)` | `build_dept_tree` | 就地建树，见 §3.4 |
| 10 | `buildDeptTreeSelect(List<SysDept> depts)` | `build_dept_tree_select` | `TreeSelect.of_dept` 映射 |
| 11 | `insertDept(SysDept dept)` | `insert_dept` | 见 §3.1 |
| 12 | `updateDept(SysDept dept)` | `update_dept` | 前半段与 `insertDept` **逐字相同** |
| 13 | `updateDeptChildren(Long, String, String)` | `update_dept_children` | 改父级后重写后代 `ancestors` |
| 14 | `deleteDeptById(Long deptId)` | `delete_dept_by_id` | 逻辑删除（`del_flag = '2'`） |
| 15 | `getQxSql(String type)` | `get_qx_sql` | 见 §3.5；`type` 参数**完全没用** |
| 16 | `saveAll(List<SysDept> depts)` | `save_all` | 见 §3.6；**当前无调用方** |
| — | `private updateTenantId(String)` | `_update_tenant_id` | 见 §3.3 |
| — | `private updateParentDeptStatus(SysDept)` | `_update_parent_dept_status` | **无调用方**（Java 里那段是注释） |
| — | `private recursionFn(List, SysDept)` | `_recursion_fn` | 建树递归 |
| — | `private getChildList(List, SysDept)` | `_get_child_list` | `deptId` 为 `null` 时抛错（NPE） |
| — | `private hasChild(List, SysDept)` | `_has_child` | |
| — | `private getSqlDeptIds(List)` | `_get_sql_dept_ids` | 拼 `"1,2,3"`，末尾不带逗号 |

### 3.1 `sub_code` 的生成规则

```java
if (dept.getParentId() == 0) {
    dept.setTreeLeavel(1);  parentSubCode = "001";
} else {
    SysDept parentBO = deptMapper.selectDeptById(dept.getParentId());
    dept.setTreeLeavel(parentBO.getTreeLeavel() + 1);
    parentSubCode = parentBO.getSubCode();
}
boolean flag = true;
if (dept.getDeptId() != null) {
    SysDept tmpBO = deptMapper.selectDeptById(dept.getDeptId());
    if (tmpBO.getParentId().equals(dept.getParentId())) { flag = false; }
}
if (flag) {
    SysDept pbo = new SysDept(); pbo.setParentId(dept.getParentId());
    int counts = deptMapper.selectDeptList(pbo).size();
    dept.setSubCode(buildSubCode(dept.getParentId(), parentSubCode, counts));
}
```

补零规则（`counts` = 当前父节点下**已有的**子节点数）：

| `parentId` | `counts` | 结果 |
|---|---|---|
| `0` | 0 | `"001"` |
| `0` | 1 | `"002"` |
| 非 0 | `< 9` | `"001-00" + (counts+1)` → `001-009` |
| 非 0 | `< 99` | `"001-0" + (counts+1)` → `001-010` |
| 非 0 | `>= 99` | `"001-" + (counts+1)` → `001-100` |

**第 10 个子节点会从 `-009` 直接跳到 `-010`（三位数变四位口径），位数跳一次 —— Java 就是这样。**
父节点 `subCode` 为 `None` 时拼出来是 `"None-001"`（Java 是 `"null-001"`），照抄。

`flag == false`（父级没变）时**不重算** `subCode`，客户端传什么就存什么。

`counts` 用的是 `deptMapper.selectDeptList(pbo)`，**不是** `deptService.selectDeptList` ——
前者不过 `@DataScope`、也不走 Service 的任何额外逻辑。迁移时写成 `self.select_dept_list(pbo)`
会多套一层（目前无害，但只要哪天有人"修好" §27.1 就会数出不同的 `counts`）。

### 3.2 `insertDept` / `updateDept` 为什么不抽公共方法

前 50 行（父级解析、`treeLeavel`、`flag`、`subCode`、`isZbzg`）**逐字相同**，是 Java 的
复制粘贴。迁移时**故意保留两份**：抽成 `_prepare()` 之后，任何一处调整都会同时影响新增和
修改，而这两条路径的回归成本差一个量级。视图层如果将来要 diff 两段逻辑，重复反而是资产。

### 3.3 `updateTenantId(null)` 会扫全表

```java
List<SysDept> queryList = deptMapper.selectDeptList(queryBo);   // queryBo.deptSubCode = "001-"
```

XML 里那条 `<if test="deptSubCode != null and deptSubCode != ''">` 在参数为 `null` 时
**整段消失**，于是查的是 `where d.del_flag = '0'` —— 全表。
触发条件很常规：`updateDept` 在父级没变（`flag == false`）时不会重算 `subCode`，
而客户端又没把 `subCode` 回传。

Python 侧同样如此（`SysDept(dept_sub_code=None)` → mapper 不加条件），
`tests/test_sys_dept_service.py::TestUpdateDept::test_a_null_sub_code_refreshes_the_whole_table`
锁住了这个行为。**不要"顺手"加 `if dept_sub_code:` 的早退**，那会跳过整棵子树的 `tenant_id` 刷新。

### 3.4 `buildDeptTree` 的三个反直觉点

1. **一个根都没有时返回入参本身**（`if (returnList.isEmpty()) returnList = depts;`），
   不是返回空列表。此时列表是扁平的、每个节点的 `children` 还是 `[]`。
2. **`parentId == null` 算根节点**：判据是 `!tempList.contains(dept.getParentId())`，
   而 `tempList` 里装的是所有 `deptId`；`null` 只有在自己也是 `null` 时才会被包含。
3. **`deptId == null` 的节点进 `recursionFn` 会 NPE**（`t.getDeptId().longValue()`）。
   但只有它成为**根**才会走进递归 —— 如果 `tempList` 里已经有 `None`（它自己），
   `parentId = null` 就不算根，于是不炸。

`tests/test_sys_dept_service.py::TestBuildDeptTree` 把上面三点分别锁成用例。

### 3.5 `getQxSql` 的三级降级

```
① 是某个部门的分管领导（fgld_id = 当前用户）  ->  "t.eps_id in (1,2,3)"
② 否则是某个部门的负责人（leader_id = 当前用户） ->  "t.eps_id in (4,5)"
③ 都不是                                     ->  " t.create_by=123"   ← 注意前导空格
```

返回的是**拼好的 SQL 片段**（`userId` 直接字符串拼接），调用方自己塞进 `where` 里。
`type` 形参在 Java 里从头到尾没被读过，保留签名只为对齐接口。

当前**没有任何端点调用它**，但它属于"看起来没用、改了可能出事"的一类，按原则迁移。

### 3.6 `Set<SysDept>` 不是真的去重

`selectHeadOffice` 用 `Collectors.toSet()` 合并两组部门。`SysDept` **没有**重写
`equals` / `hashCode`，所以这是**身份哈希表**：同一个 `dept_id` 的两个实例不会被合并。

Python 用 `id()` 做键复刻同一语义，返回值用 `list` 承载（调用方只用 `if dept_set:`
和迭代）。顺序不确定这一点与 `HashSet` 一致，不要改成按 `dept_id` 排序 ——
那会动到前端"总公司排第一"的观感。

### 3.7 依赖注入

Java 是 `@Autowired` 两个字段（`deptMapper` / `roleMapper`）；Python 是构造函数两个可选
参数 + 模块级单例（`get_dept_service()` / `reset_dept_service()`）。
测试直接 `SysDeptService(fake_dept_mapper, fake_role_mapper)`。

---

## 4. Mapper 层

### 4.1 `SysDeptMapper`（16 条 statement + 1 个 `<sql>` + 1 个 `<resultMap>`）

| XML 片段 | Python | 备注 |
|---|---|---|
| `<sql id="selectDeptVo">` | `SELECT_DEPT_VO` | 7 行原生 SQL，逐字照抄（含制表符与行尾空格） |
| `selectDeptById` | `select_dept_by_id` | **不过滤** `del_flag` |
| `selectDeptList` | `select_dept_list` | 14 个 `<if>`，见 §4.2 |
| `selectDeptListByRoleId` | `select_dept_list_by_role_id` | `deptCheckStrictly` 决定是否加子查询 |
| `checkDeptExistUser` | `check_dept_exist_user` | `count(1)`，`del_flag = '0'` |
| `hasChildByDeptId` | `has_child_by_dept_id` | `count(1)` + `limit 1` |
| `selectChildrenDeptById` | `select_children_dept_by_id` | `select *` + `find_in_set`，见 §4.5 |
| `selectNormalChildrenDeptById` | `select_normal_children_dept_by_id` | `count(*)`，`status = 0` |
| `checkDeptNameUnique` | `check_dept_name_unique` | `dept_name` + `parent_id`，`limit 1`，**不过滤** `del_flag` |
| `selectTenantId` | `select_tenant_id` | `:sub_code like concat(d.sub_code, '%')` —— 参数在**左**边，找的是自己的祖先单位；`order by tree_leavel desc` 取最近的那个 |
| `updateDept` | `update_dept` | 动态 `<set>`，见 §4.3 |
| `updateDeptChildren` | `update_dept_children` | `<foreach>` + `case when` |
| `updateDeptStatus` | `update_dept_status` | `${ancestors}` 字符串拼接，见 §4.4 |
| `insertDept` | `insert_dept` | 动态列 + `sysdate()` + `lastrowid` 回写 |
| `updateTenantId` | `update_tenant_id` | `set` 和 `where` 用**同一个** `:tenant_id` |
| `deleteDeptById` | `delete_dept_by_id` | 名字叫 delete，SQL 是 `update ... del_flag = '2'` |
| `deleteDeptAll` | `delete_dept_all` | 只删 `create_by = '-9999'` 的种子数据 |
| `<resultMap id="SysDeptResult">` | `_DEPT_COLUMNS` (26 列) | `parent_name` / `update_by` / `update_time` / `remark` 无列源 |

### 4.2 `selectDeptList` 的 14 个 `<if>`

顺序固定（写错只是换结果集，不报错）：

```
parentId → deptName(like) → status → deptId → isZbzg → isUint → treeLeavel
→ subCode → deptJc → tenantId → leaderId → leader → fgldId → fgldName(like)
→ deptSubCode(前缀)
```

两个容易混的点：

- **判据是 OGNL 的 `x != null and x != ''`，不是 `isBlank`。** 项目里的
  `string_utils.is_not_empty()` 照抄的是 RuoYi 的 `StringUtils.isEmpty`，它**先 `trim`**，
  于是 `is_not_empty(" ")` 是 `False` —— 用它就会漏掉"只填一个空格"的条件。
  `_build_dept_list_sql` 因此用 `value is None or value == ""`。
- `deptSubCode` 是 `concat(#{deptSubCode}, '%')`，**前缀匹配**；其余 like 都是
  `concat('%', #{x}, '%')`。

另外 `treeLeavel = 0` 也会进条件（`0 != null` 且 `0 != ''`），别把 0 当"未设置"。

### 4.3 `insertDept` 与 `updateDept` 的列判据差异

两张表驱动建 SQL：`_INSERT_DEPT_COLUMNS` / `_UPDATE_DEPT_COLUMNS`，第三项
`require_text` 表示该列是否额外判 `!= ''`。

| 列 | insert | update | 结果 |
|---|---|---|---|
| `phone` / `email` | `require_text=True` | `False` | 传 `""` 时：insert 丢列，update 写空串 |
| `status` / `update_by` | 无此列 / `True` | `True` | update 时才会带 |
| `dept_name` / `ancestors` / `order_num` / `create_by` | `True` | — | 空串不写 |
| `parent_id` | 额外 `!= 0` | 同 | `0` 时**整列不出现** |
| 其余 | `False` | `False` | 只判 `null` |

`parent_id = 0` 被丢掉这件事很关键：新增顶级部门时 `parent_id` 靠**列默认值**落库
（表里是 `0`），不是显式写入。

`updateDept` 无条件带 `update_time = sysdate()`（不在 `<set>` 的动态列里），
所以只改 `tenant_id` 的那两次内部调用也会刷新时间 —— 与 Java 一致。

### 4.4 `updateDeptStatus` 的 `${ancestors}` 是字符串拼接

```python
ancestors = "null" if dept.ancestors is None else str(dept.ancestors)
sql = "update sys_dept\n\t    set " + ", ".join(sets) + f"\n\t    where dept_id in ({ancestors})"
```

`ancestors` 里装的是 `"0,100,101"` 这样的祖级串，**作为 SQL 文本**拼进 `in (...)`。
`None` 时拼的是字面量 `null`，于是 `where dept_id in (null)` —— 一行都改不到（不是报错）。

当前没有调用方（`updateParentDeptStatus` 是死代码），但 SQL 照抄。

### 4.5 投影：`selectDeptVo` 与 `select *` 的差别

`selectDeptVo` 只 select 26 列，`<resultMap>` 里的 `parent_name` / `update_by` /
`update_time` / `remark` **没有列源**，所以走它的语句这四项恒为 `None`
（`BaseEntity` 无 `@JsonInclude`，Jackson 会输出 `"updateBy": null`）。

`selectChildrenDeptById` 写的是 `select *`，MyBatis 的 `autoMappingBehavior=PARTIAL`
会把 `remark` / `update_by` / `update_time` 也陪进来 —— 所以它用
`_DEPT_SELECT_ALL_COLUMNS`（26 + 3 列）映射。两条语句的实体字段数不同，这是 Java 原样。

---

## 5. Bean Validation：`@NotBlank` / `@Size` / `@Email`

### 5.1 `SysDept` 的四个字段、六项约束

```java
@NotBlank(message = "部门名称不能为空")
@Size(min = 0, max = 30, message = "部门名称长度不能超过30个字符")
public String getDeptName() { return deptName; }

@NotBlank(message = "显示顺序不能为空")                       // 注意：没有 @Size
public String getOrderNum() { return orderNum; }

@Size(min = 0, max = 11, message = "联系电话长度不能超过11个字符")
public String getPhone() { return phone; }

@Email(message = "邮箱格式不正确")
@Size(min = 0, max = 50, message = "邮箱长度不能超过50个字符")
public String getEmail() { return email; }
```

`leader` / `bankName` / `account` / `socialCode` / `postalCode` / `address` 上
**没有任何注解**，可以随便空着 —— 不要看到别人有 `@Size` 就给它们也加一个。

`DEPT_CONSTRAINTS` 按源码顺序排列，因此"多字段同时违规"时报的是第一条
（空 body → `部门名称不能为空`）。

### 5.2 `@Email` 是放宽版，且**必须**保持放宽

Hibernate 的实现是 `Pattern.compile(".{0,64}@" + DOMAIN_PART_REGEX, CASE_INSENSITIVE)`
配 `matches()`：本地部分**不校验字符集**（`"a b@c.d"` 通过），`null` 与 `""` 也通过。

Python 的 `_EMAIL_PATTERN` 本地部分逐字照抄，域名部分略宽（允许标签以 `-` 开头、
不限制单标签 63 字符）。方向是**只多放过、不多拒绝**，详见 COMPATIBILITY §27.3。
写"标准邮箱正则"会拒绝 Java 接受的输入，那是真实的回归。

### 5.3 校验写成 `Depends` 的原因

Spring 的真实顺序是：

```
安全过滤器链(401) -> 路由 -> 反序列化 + 校验(500) -> @PreAuthorize(403) -> 方法体
```

`ValidDept` 是 `Annotated[SysDept, Depends(_validated_dept)]`，依赖在端点函数体之前解析，
正好补回 Spring 的位置。写成函数体第一行的话，"未登录 + 缺 deptName"会变成 403 而不是 500。

回归用例：`tests/test_sys_dept_controller.py::TestValidationRunsBeforePermission`（13 条）。

---

## 6. 实体字段：只列容易被改错的

| Java | Python | 类型 | 说明 |
|---|---|---|---|
| `Long deptId` | `dept_id` | `Optional[int]` | 主键，自增 |
| `Long parentId` | `parent_id` | `Optional[int]` | 顶级是 `0`；`null` 在 `insertDept` 里会被强制成 `0` |
| `String ancestors` | `ancestors` | `Optional[str]` | `"0,100,101"`；`excludeChild` / `updateDeptStatus` 都按字符串处理 |
| `String deptName` | `dept_name` | `Optional[str]` | `@NotBlank` + `@Size(max=30)` |
| `String orderNum` | `order_num` | `JavaString` | **varchar 列 + `String` 字段**，前端发数字要强转 |
| `Long tenantId` | `tenant_id` | `Optional[int]` | 由 `insertDept` / `updateTenantId` 维护 |
| `String isUint` | `is_uint` | `Optional[str]` | `"1"` 是单位；顶级节点一定是 `"1"` |
| `String isZbzg` | `is_zbzg` | `Optional[str]` | 非单位时被强制成 `"0"` |
| `Integer treeLeavel` | `tree_leavel` | `Optional[int]` | **拼写 `Leavel` 是原样**，同时是列名与 JSON 键 |
| `String subCode` | `sub_code` | `Optional[str]` | 见 §3.1 |
| `String deptSubCode` | `dept_sub_code` | `Optional[str]` | **只用于查询**（前缀匹配），不落库 |
| `String flag` | `flag` | `Optional[str]` | **只用于查询**（`treeselectNew`），不落库 |
| `String dataId` | `data_id` | `Optional[str]` | **只用于查询**（`sjzbDept`），是字符串 |
| `String delFlag` | `del_flag` | `Optional[str]` | `0` 存在 / `2` 删除 |
| `List<SysDept> children` | `children` | `List[SysDept] = []` | Java 初始化为 `new ArrayList<>()`，**无** `@JsonInclude`，所以空节点输出 `"children": []` |

`TreeSelect.children` 不一样：它带 `@JsonInclude(NON_EMPTY)`，**叶子节点不输出 `children` 键**。
`TreeSelect` 用 `_omit_when_empty = ("children",)` 复刻。

---

## 7. 逐行对照速查

```text
SysDeptController#list              -> sys_dept_controller.list_depts          (GET    /system/dept/list)
SysDeptController#getList           -> sys_dept_controller.get_list            (GET    /system/dept/getList)
SysDeptController#excludeChild      -> sys_dept_controller.exclude_child       (GET    /system/dept/list/exclude/{deptId})
SysDeptController#getInfo           -> sys_dept_controller.get_info            (GET    /system/dept/{deptId})
SysDeptController#treeselect        -> sys_dept_controller.treeselect          (GET    /system/dept/treeselect)
SysDeptController#treeselectNew     -> sys_dept_controller.treeselect_new      (GET    /system/dept/treeselectNew)
SysDeptController#roleDeptTreeselect-> sys_dept_controller.role_dept_treeselect(GET    /system/dept/roleDeptTreeselect/{roleId})
SysDeptController#add               -> sys_dept_controller.add                 (POST   /system/dept)
SysDeptController#edit              -> sys_dept_controller.edit                (PUT    /system/dept)
SysDeptController#remove            -> sys_dept_controller.remove              (DELETE /system/dept/{deptId})
SysDeptController#getCompanyList    -> sys_dept_controller.get_company_list    (GET    /system/dept/getCompanyList)

SysDeptServiceImpl#insertDept                 -> SysDeptService.insert_dept
SysDeptServiceImpl#updateDept                 -> SysDeptService.update_dept
SysDeptServiceImpl#buildDeptTree              -> SysDeptService.build_dept_tree
SysDeptServiceImpl#buildDeptTreeSelect        -> SysDeptService.build_dept_tree_select
SysDeptServiceImpl#checkDeptNameUnique        -> SysDeptService.check_dept_name_unique
SysDeptServiceImpl#selectHeadOffice           -> SysDeptService.select_head_office
SysDeptServiceImpl#updateDeptChildren         -> SysDeptService.update_dept_children
SysDeptServiceImpl#updateParentDeptStatus     -> SysDeptService._update_parent_dept_status
SysDeptServiceImpl#updateTenantId             -> SysDeptService._update_tenant_id
SysDeptServiceImpl#getQxSql                   -> SysDeptService.get_qx_sql
SysDeptServiceImpl#saveAll                    -> SysDeptService.save_all

SysDeptMapper.xml#selectDeptList           -> SysDeptMapper.select_dept_list
SysDeptMapper.xml#selectDeptById           -> SysDeptMapper.select_dept_by_id
SysDeptMapper.xml#insertDept               -> SysDeptMapper.insert_dept
SysDeptMapper.xml#updateDept               -> SysDeptMapper.update_dept
SysDeptMapper.xml#updateDeptStatus         -> SysDeptMapper.update_dept_status
SysDeptMapper.xml#selectChildrenDeptById   -> SysDeptMapper.select_children_dept_by_id
SysDeptMapper.xml#deleteDeptById           -> SysDeptMapper.delete_dept_by_id

TreeSelect(SysDept)                        -> TreeSelect.of_dept
TreeSelect(SysMenu)                        -> TreeSelect.of_menu
CommonUtil#isNull                          -> common_util.is_null
```
