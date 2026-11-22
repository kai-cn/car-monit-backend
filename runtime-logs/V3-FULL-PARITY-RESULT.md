<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# Java V3 vs Python 全量接口对拍结果（云 runner 实测）

> run：`44755264319`（backend 仓库 `python-v3-full-parity.yml`，ref=master）
> job：`136353209943`，**completed success**（含 probe 质量门禁）
> 日志：`D:\work\runtime-logs\v3full-final.log`

## 1. 运行条件（凭据运行时注入）
* `CI_ADMIN_PASSWORD`：admin 口令，仅作仓库 Secret，step 级 env 注入；日志显示 `***`
* `EXPORT_DOWNLOAD_SECRET` / `JWT_SECRET` / `CI_EXPORT_SECRET`：Java V3 启动门禁与 Python 强度门禁
* `jdbc:p6spy:mysql://...`：与已验证的 auth-parity workflow 一致
* JDK 固定 `8.0.442`（8u514 tarball 在本 runner 解压失败）
* 两变体各自重置 DB seed，避免写端点互相污染

## 2. 探测结果
```
PROBE_DONE variant=java-v3 ready=True login=ok ep=302 err=None
PROBE_DONE variant=python  ready=True login=ok ep=302 err=None
COMPARE label=java-v3-vs-python endpoints=302 fails=84
Endpoints: 302 | status_match=301 | exact=164 | semantic=177 | nondet=41 | fails=84
```
* startup：Java 24027ms / Python 4003ms
* 平均延迟：Java 85.91ms / Python 24.04ms

## 3. 结论分类
| verdict | 数量 | 说明 |
|---|---|---|
| OK | 177 | 状态码+语义一致（其中 exact 164） |
| NONDET | 41 | 响应本身非确定（时间戳/验证码/导出文件名），非实现差异 |
| DIFF | 84 | **真实差异**，需按端点分析 |
| status_match | 301/302 | 仅 1 个端点状态码不一致 |

## 4. DIFF 端点（前 40 个，完整列表在云日志）
```
/base/cdc/config
/base/feeGantry/1, /export
/base/feeStationEnter/1, /list
/base/feerecords/1, /export, /list
/base/feestationexit/1, /export, /list
/base/fitting/1, /list
/base/geometry/syncAllGeometry
/base/provcapture/1, /list
/base/snapshotflow/1, /earliest-time, /export, /list
/base/stationcapture/1, /list
/base/vehicleweight/1, /list
/flow/messageinfo/export, /exportShrz, /list, /listxx, /listyb, /listyj
/getInfo
/manager/aduitfree/exportIncomeDetailList, /exportIncomeStatics
/manager/bigScreen/carAudit, /export/download/1, /export/status/1, /sectionList
/manager/carinfo/export
/manager/cartrackinfo/listByCarId
/manager/carwarning/export
...
```

## 5. 修复过程中通过云日志定位并解决的问题（未下载 artifact）
1. `setup-java` 8u514 tarball 解压失败 → 固定 `8.0.442`
2. Java 启动失败 `缺少导出下载签名密钥` → 注入 `EXPORT_DOWNLOAD_SECRET`
3. Python `pip install -r` 的 `-e .` 解析到仓库根 → 先 `cd candidate/car-monit-py`
4. Python 密钥强度门禁 → 用高熵 Secret 注入 `TOKEN__SECRET`/`HENGDA__SECRET`
5. workflow "假成功"（probe rc=1 但步骤绿）→ 新增 Gate probe quality 步骤
6. workflow 只在默认分支可 dispatch → 同步部署到 master 与 V3 分支

## 6. 下一步
* 对 84 个 DIFF 端点逐一分类：真实业务差异 vs seed 数据差异 vs 路径参数样例不当
* 尤其关注 `/getInfo`（权限集合）、`/base/cdc/config`（51578 vs 402 bytes）、
  `/manager/bigScreen/export/status/1`（V3 新端点）
* 写端点（POST/PUT/DELETE）对拍需两变体各自独立 DB，尚未覆盖
