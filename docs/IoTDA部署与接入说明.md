# IoTDA 搭建、工作原理与用户端接入说明

> 适用范围：`car-monit-api` / `car-monit-backend` 的数据采集上游为华为 IoT 设备接入平台（IoTDA）。本文基于 `D:\IoTDAPak`（本环境挂载为 `/mnt/d/IoTDAPak`）中的安装指南、用户指南、LLD 规划表以及容器/虚拟机镜像包整理，供部署、联调和接入时参考。
>
> 文档版本对应关系：
>
> - `FC场景IoTDA安装指南.pdf`：文档版本 01，2025-06-16，116 页。
> - `IoT设备接入(IoTDA)25.3.0用户指南(forHCSOnline25.3.0)01(3).pdf`：IoTDA 25.3.0，文档版本 01，2025-04-30，344 页。
> - `1_IoT基于FusionCube底座部署 LLD (Copy).xlsx`：FusionCube 场景 LLD 规划模板（VLAN/IP、虚机、安全组、防火墙/NAT）。
> - 软件包版本：IoTDA 25.3.0（镜像包时间戳 20250426095439）；OPS/中间件包时间戳 20250429000337；K8s agent 1.27.13；OS 镜像为 Huawei Cloud EulerOS 2.0 64bit（qcow2）。

---

## 1. 结论摘要

1. IoTDA 是本地化部署的物联网接入平台，负责设备接入、物模型标准化、设备管理、规则流转与北向开放；`car-monit-api` 并不直接连接设备，而是消费 IoTDA 规则引擎转发到 Kafka 的数据。
2. FC（FusionCube）场景采用“FusionCube 虚拟化底座 + Kubernetes 业务集群”的两层结构。网络分为 Trust、DMZ、第三方应用三个 K8s 集群/区域，中间由防火墙、安全组和 VIP/EIP 隔离与暴露。
3. 部署顺序固定：LLD 规划 → 硬件安装 → 网络/路由/防火墙打通 → 服务器配置 → FusionCube（I 层）安装配置 → K8s/Ops/IoTDA 应用（业务层）安装 → 安装后配置 → 拨测验收。
4. 用户端分两类：
   - **设备侧**：MQTT(S)/CoAP(S)/HTTP 接入，使用“产品 + 设备 + 一机一密或 X.509 证书”鉴权，按系统 Topic 或自定义 Topic 上报属性/消息。
   - **应用侧**：通过 Console 或北向 REST API（`AK/SK` 换取 `X-Auth-Token`）管理设备，通过 Kafka / AMQP / HTTP 推送订阅设备数据。
5. 当前仓库实现与设计文档存在差距：设计文档规划 `device-raw-data` 原始流 + Flink + GaussDB + CDC，实际 Java 代码直接消费 `ods-rt-szdn-snapshot-flow`，消息信封为 `{operationType, data}`。对接时需以代码实际 topic/消息结构为准，或通过规则 SQL/适配层做转换。

---

## 2. 工作原理

### 2.1 分层与职责

用户指南“图 1-1 整体架构”自上而下分为：

| 层 | 内容 | 说明 |
|---|---|---|
| 应用层 | 智慧城市、园区、交通、工业互联等行业应用 | 通过 IoTDA 北向 API / 订阅推送获取监测数据 |
| 平台层 | IoT 平台：设备管理、应用管理、本地运维、账号管理、设备接入、数据管理、安全管理等 | 物模型定义 + 编解码插件把异构数据标准化；提供 RESTful API |
| 网络层 | 2G/3G/4G/5G/NB-IoT/LoRa/有线等 | 多网络接入 |
| 感知层 | 城市、园区、工业等终端设备，以及第三方子系统 | 直连、网关代理或子系统对接 |

平台核心能力：

- 设备接入：MQTT、MQTTS、CoAP、CoAPS、HTTP；Device SDK（C/Java/C#/Android/Python 等）；泛协议通过云网关或边缘协议驱动转换。
- 设备管理：生命周期、分组标签、批量操作、设备影子、子设备、软固件升级（OTA）、配置下发。
- 消息通信：属性上报、消息上报、命令下发（MQTT 同步、CoAP 异步/缓存）、消息下发、自定义 Topic 透传。
- 数据流转：规则引擎 + SQL 过滤，转发到 Kafka、ROMA MQS、HTTP 应用、MRS Kafka、OBS、InfluxDB、G100 等。
- 运维：监控报表、设备告警、消息跟踪、在线调试、EchoTest 拨测。

### 2.2 数据上行链路

```text
设备/网关
  │ MQTT(S) 1883/8883、CoAP(S) UDP 5683/5684、HTTP2 7443
  ▼
客户防火墙/NAT → DMZ LVS（浮动 IP）→ Trust 区 DeviceAccess（无状态接入）
  ▼
编解码插件（二进制/自定义格式 → 物模型标准 JSON）
  ▼
规则引擎（数据来源 + 触发事件 + SQL 过滤/字段改写）
  ▼
转发目标：第三方 Kafka / 云平台 Kafka / ROMA / AMQP / HTTP / OBS / InfluxDB ...
  ▼
应用服务（如 car-monit-api）消费、落库、检索、展示
```

- 属性上报：依赖产品模型，平台可解析、存快照、支持历史数据查询（用户指南说明最大可存 90 天）、可推送给订阅方。
- 消息上报：不依赖产品模型，平台不解析内容，适合直接转发到消息中间件。
- 原始数据上报：通过编解码插件转成标准 JSON；MQTT 也可用自定义 Topic 透传。
- 网关批量上报：网关一次上报多个子设备数据。

### 2.3 数据下行链路

- 应用调用北向 API，例如：
  - 同步命令：`POST /v5/iot/{project_id}/devices/{device_id}/commands`
  - 消息下发：`POST /v5/iot/{project_id}/devices/{device_id}/messages`
  - 异步命令（CoAP）：`POST /v5/iot/{project_id}/devices/{device_id}/async-commands`
- MQTT 命令下发 Topic：`$oc/devices/{device_id}/sys/commands/request_id={request_id}`；设备回复 Topic：`$oc/devices/{device_id}/sys/commands/response/request_id={request_id}`。
- MQTT 消息下发 Topic：`$oc/devices/{device_id}/sys/messages/down`。
- MQTT 命令/属性修改为同步机制（等待设备响应，超时失败）；消息下发为异步机制，支持立即下发和缓存下发（缓存消息 1 天未送达置为超时）。

### 2.4 鉴权与安全模型

| 方向 | 机制 |
|---|---|
| 设备 → 平台 | 一机一密（deviceId + deviceSecret）或 X.509 证书；基于 TLS 加密，设备侧 CA 证书从 Console“总览”下载；ClientId/username/password 在设备详情“MQTT 连接参数”中查看 |
| 应用 → 平台 | 在 Console 创建访问密钥（AK/SK），调用 API 时生成签名换取 `X-Auth-Token`，请求形如 `https://{Endpoint}/v5/iot/{project_id}/...` |
| AMQP 订阅 | `amqps://{address}:5671`，`username=accessKey={AK}|timestamp={13位毫秒}|`，`password={accessCode}`；时间戳与服务端相差需在 5 分钟内，单 AK 最多 32 个客户端并发建链 |
| Kafka 订阅 | 转发目标支持无鉴权（PAAS）、SASL PLAIN、SASL SCRAM-SHA-256/512 |
| 网络安全 | DMZ/Trust 分域、安全组白名单、仅暴露必要端口；非加密 MQTT/CoAP 端口默认关闭，需运维开通 |

---

## 3. 部署架构与规划

### 3.1 逻辑组网（来自安装指南图 1-3 与 LLD“2-1 整体组网图”）

```text
设备 / 华为云 / 本地运维 / APP
        │ 本地/Internet/Internet
        ▼
   客户防火墙（安全策略/VPN、NAT 映射）
        │
        ▼
   FusionCube 交换机
        ├── K8s 集群 1：第三方应用（untrust，APP 容器）
        ├── K8s 集群 2：DMZ（LVS + NGINX，南向接入与北向入口）
        └── K8s 集群 3：Trust（IoTDA、IOTA、DRIS、OPS、Stage）
```

要点：

- IoT 服务共用一个 K8s 集群，整体分 DMZ 和 Trust 区域，两区域之间流量过防火墙；第三方应用单独集群。
- 运维管理和业务同属 Trust 区域；服务间调用尽量同区域，若跨区域需开通对应安全组端口。
- 不同业务的 node 节点划分不同 IP 地址；不同 node 组容器不能飘移到其他节点组。
- LVS 浮动 IP 承接南向设备流量；NginxNorth 承接北向 REST/推送，NginxConsole 承接 Console/stage。

### 3.2 网络平面与端口

安装指南示例 VLAN（以项目 LLD 为准，可整体替换前三段 IP）：

| 平面 | VLAN 示例 | 网段示例 | 用途 |
|---|---|---|---|
| BMC | 300 | 172.16.0.128/25 | 服务器带外管理 |
| 管理面 | 301 | 172.16.1.0/24 | Infra 管理 |
| DMZ | 302 | 172.16.4.0/24 | LVS/NGINX 等 |
| Trust | 303 | 172.16.3.0/24 | IoTDA/OPS/Stage 等 |
| 存储 | 304 | 172.16.2.0/24 | 存储网络 |
| 容器网络 / Service 网络 | — | 172.16.5.0/23 / 172.16.7.0/24 | K8s Pod / ClusterIP |

注意：规划网段时**必须避开 172.17 网段**（Docker 默认网桥网段）。IPv6 场景需客户额外规划 Trust/DMZ 两个 IPv6 前缀（建议 /112），且不支持纯 IPv6 单独接入。

关键对外开放端口（详见 LLD“4-3 外部防火墙诉求”“4-2 虚机安全组规划”）：

| 端口 | 协议 | 用途 |
|---|---|---|
| 1883 / 8883 | TCP | 南向 MQTT / MQTTS（DNAT 到 LVS VIP） |
| 5683 / 5684 | UDP | 南向 CoAP / CoAPS（DNAT 到 LVS VIP） |
| 7443 | TCP | 南向 HTTP2 接入 |
| 443 | TCP | 北向 REST API / HTTP 推送、业务 Console |
| 5671 | TCP | AMQP 订阅推送 |
| 8443 / 80 | TCP | 运维面/Console（建议白名单） |
| 2081 | TCP | 跳板机（白名单：华为云 EIP + 客户本地接入段） |
| 8945 / 8946 / 8943 / 8989 | TCP | OTA 下载 / 边缘网关拉镜像 / 网关管理 / IT 数采配置 |
| 30000–32767 | TCP/UDP | K8s NodePort（如 Apollo 30070、Grafana/Kibana 临时 NodePort） |

### 3.3 版本与资源规格（LLD 示例）

- 版本配套：FusionCube 6.0.1（FCC）、FusionCompute 8.0.1SPH2、FusionStorage 8015；IoTDA 25.3.0；OS 镜像 HCE 2.0。
- 1000TPS 标准版示例（详见 LLD“4-1 虚机详细信息”）：
  - `iotda-master-0001~0003`：4C/16G，系统盘 200G，Trust 区；
  - `iotda-worker-0001~0007`：16C/64G，系统盘 100G，按业务挂载多块数据盘（MySQL、BookKeeper、OpenGemini、ES、OPS ES、镜像仓、upgrade 等，总量约 12.3T）；
  - `iotda-dmz-worker-0001~0006`：4C/16G，系统盘 100G，数据盘 100G（日志）；
  - `jumper-0001`：2C/8G。
  - VIP 示例：`10.187.25.198`（apiserver）、`10.187.25.199`（mysql）、`10.187.25.200`（mysql-ops）、`10.187.25.201`（NginxConsole）、`10.187.25.202`（LVS）、`10.187.25.203`（NginxNorth）。
- 虚机反亲和：master 三节点、worker 分组、DMZ 节点分组需分布在不同物理机；`node-0004` 不能与 `node-0003`、`node-0005` 同主机。

---

## 4. 搭建步骤（FC 场景）

以下为压缩后的操作主线，详细菜单与截图以《FC场景IoTDA安装指南》对应章节为准。

### 步骤 0：安装规划（指南第 3 章 + LLD）

1. 从 Support 获取配套版本 LLD，通读所有页签：设备布局/跳线、VLAN 和子网、公网 IP、服务器信息、虚拟机节点信息、虚机安全组、外部防火墙诉求、IoTDA VPC 资源。
2. 按项目实际修改 VLAN ID 和 IP 前三段；各网络平面 IP 前两段保持一致；避开 172.17。
3. 确定 1000TPS（标准版）或 2000TPS（智能站点版）规格，以及是否启用 IPv6、告警对接 Zabbix、域名访问、NAT 访问。

### 步骤 1：安装准备与硬件安装（指南第 4、5 章）

1. 本地 PC 准备 WinSCP、MobaXterm（包内已提供 `MobaXterm_Portable_v25.2`）、浏览器、ICS Lite（用于浏览华为电子文档，解压后运行 `Startup.exe`，默认访问 `127.0.0.1:51299`）。
2. 获取并安装 FusionCube Builder；软件包上传到 Builder 的 `/repo/iso/default`（默认路径）。
3. 按 LLD“设备入柜图”“跳线表”完成服务器上架、交换机连线。

### 步骤 2：网络配置及打通（指南第 6 章）

1. 交换机堆叠、创建 VLAN（示例 `vlan batch 300 to 304`）、配置 Vlanif 网关、端口 trunk/access、静态路由。
2. 检查端口与网关状态均为 up。
3. 与客户数据中心三层对接，互相指向路由。
4. 防火墙/NAT 优先打通“安装部署网络”（云端远程安装），其次本地运维网络和业务网络；按 LLD“4-3 外部防火墙诉求”配置 DNAT/SNAT。

### 步骤 3：服务器配置（指南第 7 章）

1. BMC 添加管理账号（指南示例用户名 `fc2mgmt`，权限管理员，密码由管理员提供）。
2.  UEFI（F11）进入 RAID 配置：系统盘 2 块做 RAID1，其余盘设为 JBOD，并设置硬盘为第一启动项。

### 步骤 4：I 层安装——FusionCube（指南第 8 章）

1. 安装 Builder：上传 `FusionCube 6.0.1_Builder.zip` 与 `.asc`，校验后 `unzip`，确认管理网口（默认 eth0，不符则修改 SSDP 包内 `mgnt_interface`），执行 `install.sh`；日志 `/var/log/fcb/install_fcb.log`。
2. 浏览器访问 `https://{Builder管理IP}:8443` 登录，上传软件包。
3. 选择安装场景“FusionSphere虚拟化超融合基础设施”，自动（SSDP）或手动发现服务器，填写各网络平面 IP 范围/掩码/网关/VLAN 与虚拟化浮动 IP。
4. 校验参数后安装，总进度 100% 即完成（通常 40–120 分钟）。
5. FusionCompute 配置：加载 License；配置 NTP 时区/时钟源；按 LLD 创建数据盘（普通、独立-持久）；创建 VLAN 池；添加安全组规则；添加端口组；导入 qcow2 模板（新版本需将文件名改为 `*-vda.qcow2` 规避导入问题）。
6. 用模板创建 IoTDA 虚拟机，按反亲和要求选择不同主机；不勾选与主机时间同步；按区域选择端口组；配置主机名/IP；创建后绑定数据盘。

### 步骤 5：业务安装（指南第 9 章）

1. **准备**：按 LLD 给虚机按顺序挂载多块数据盘（例如 `vdb`/`vdc`/`vdd`/`vde` 分别对应日志、MySQL、BK、OpenGemini），`lsblk` 核对；解压 HCE qcow2 OS 镜像、`iotda_agent_common_*.zip`、k8s-agent 普罗包、NginxAgent 普罗包。
2. **K8s 集群**：
   - `master-0001` 上传 `k8s-agent_*.tar.gz` 到 `/tmp`，解压后 `cd k8s-agent_*/action && sh appctl.sh deploy`，`netstat -tlpn | grep 6442` 验证。
   - `iotda-worker-0001/0003` 部署 NginxAgent；镜像仓库盘挂到 `/registry`。
   - 编辑 `/etc/ansible/k8s-agent/request/install-k8s-parameter.json`：填写 `master_node_vip`、`registry_vip`（与 master VIP 相同）、`ntp_server`（必填）、`pod_subnet`、`service_subnet`、`master_nodes`、`worker_nodes`；执行安装剧本后 `kubectl get node` 全部 Ready。
3. **Ops 安装**：将 CCOps 部署工具上传到 `master-0001`，按需修改 `node_config.json`（挂盘映射）与 `input_blueprint.json`（`deploy_type`、`master`、`k8s_api_ip`、`registry_url`、`mysql_vip`、`mysql_ops_vip`、`nginx_console_vip/eip`、`slaves` 等），执行 `sh install_ccops.sh fc-mgmt 1000 true`（首次挂盘；非首次用 `false`），约 40 分钟。失败时用 `gardener_client.py fc-mgmt-1000 RETRY` 重试，日志在 `/opt/CCOps/gardener/log`。
4. **IoTDA 应用安装**：
   - 将 `iotda_docker_image_{common,x86}_*.tar.gz`（x86 场景）和 `iotda_plugins_common_*.tar.gz` 上传到 `master-0001:/opt/iotda`；
   - 解压插件包，编辑 `script_new/config-fc-standard/input_blueprint.json`（标准版）或 `config-fc-agile/input_blueprint.json`（敏捷版）：`master`、`k8s_api_ip`、`k8s_api_token`、`helm_api_ip`、`registry_url`、`mysql_vip`、`mysql_ops_vip`、`nginx_north_vip/eip`、`nginx_console_vip/eip`、`lvs_vip/eip`、`slaves`、`vm_password`（加密）等；IPv6 场景另填 `lvs_ipv6_*`、`device_access_ipv6_*` 等；
   - 挂盘：`cd /opt/iotda && python main.py -a install -d fc-standard -j PartitionWork`；
   - 安装：`cd /opt/iotda/script_new && nohup sh install_iotda.sh fc-standard &`，`tail -f nohup.out` 出现 `run successfully!` 即完成；失败用 `gardener_client.py fc-standard RETRY`，日志 `/opt/garden/log`；
   - 服务入驻：访问 `https://{nginx_console_eip}/`，用 admin 登录，在“系统配置 → 设备接入-IOTDA”把状态更新为“已入驻”；再创建业务账号并赋予 `te_admin` 或 `sys_iotda_admin` 角色。
   - 运维入口：`https://{nginx_console_eip}:8443/apollo/`、`/grafana`、`/kibana`。

### 步骤 6：安装后配置（指南第 10 章，按需）

- 告警对接 Zabbix：在 Apollo 项目 `CCOpsSmartSiteAdapter` 覆盖 `ZabbixAddr.ipWithPort`，设置 `alarm.tunnel=zabbix`，导入 Zabbix 4.2.8 主机模板。
- 告警对接华为 IoT 运维：`alarm.tunnel=kafka`、`message.producer.type=kafka`、`message.producer.endpoint`，并配置 SSL/SASL 相关项（由技术支持提供）。
- 域名访问：在 `iosgwlite`、`iosiamlite`、`CCOpsIoTSiteUI` 等 Apollo 项目配置 `sso.server.url`、`sso.login.url`、`*-dns` 等并发布。
- NAT/IPv6：配置 Apollo、LVSAdapter、IoEdgeManager、operation-management、k8s ConfigMap `configmap-component`，开启 `ip6table_mangle`，重启 DeviceAccess。

### 步骤 7：业务调测与验收（指南第 11 章）

1. 用 admin 在 Console 新增拨测账号，赋予 `te_admin` 角色；用该账号创建访问密钥，得到 AK/SK；在“基本信息”获取 IAM 账号名、账号 ID、项目 ID。
2. 进入“服务总览 → IoT设备接入-IoTDA”。
3. Apollo 项目 `EchoTestService` 的 `EchoTest.EnvConfig.iotedge` 增加 `domainName`、`domainId`、`projectId`、`accessKey`、`secretAccessKey`（SK 需用 master 节点加解密组件加密后填写）。
4. 将 `active` 置为 `true` 启动拨测；可配置 `parallelNumber`、`taskTimeout`、`caseTimeout`、`taskIntervalTime`。
5. 验收：Grafana 查看拨测任务（推荐）；Kibana 搜索 `*json.type:CASEMETRIC` / `*json.type:TASKMETRIC`；或 `master01` 上 `tail -f /opt/cctm/cctmechotestservice/logs/echo-test.log`，`grep successCaseCount` 查看结果。

---

## 5. 交付包与镜像清单解读

### 5.1 镜像包内主要组件（从各 `manifest.json` 读取）

| 包 | 镜像数 | 关键组件（节选） |
|---|---|---|
| `iotda_docker_image_common_x86_*_0/1.tar.gz` | 14 + 15 | `devicecommunication`、`devicemanager`、`deviceaccess`、`devicecodec`、`iotdasite`、`iotdamgr`、`iotdagw`、`ioapig`、`push`、`amqpgateway`、`ioedgemanager`、`edgeaccess`、`edgehub-go`、`edge-schedule`、`operationmanagement`、`certificatemanagement`、`drservice` 等 |
| `iotda_docker_image_x86_*_0/1/2.tar.gz` | 14 + 13 + 14 | `iosiamlite`、`iossiservice`、`iosconsolelite`、`iosgwlite`、`ioshosting`、`iosrepo`、`hcsechotestservice`、`cctmechotestservice`、`opengauss`、`opengemini`、`edge-redis`、`lvsadapter`、`middleware-platform`、`upgrade`、`file-pkg-image` 等 |
| `OPS/iot_docker_image_ccops_fc_mgmt_*` | 13 | Apollo（config/admin/portal）、`ccopselasticsearch`、`ccopskibana`、`ccopsgrafana`、`ccopslogstashservice`、`ccopsfilebeatagent`、`ccopsmetricbeatagent`、`ccopsheartbeatagent`、`ccopsiotsiteui`、`ccopssmartsiteadapter`、`kube-state-metrics` |
| `OPS/iot_docker_image_middleware_fc_mgmt_*` | 6 | `nginx`、`pulsar`、`zookeeper`、`bookkeeper`、`keepalived`、`edge-mysql` |
| `OPS/iot_docker_image_gardener_fc_mgmt_*` | 1 | `iot-gardener`（部署编排） |
| `k8s/docker-registry-x8664.tar` | — | 离线容器镜像仓库数据 |
| `k8s/k8s-agent_1.27.13...tar.gz`、`NginxAgent_...tar.gz` | — | K8s 安装代理、Nginx 代理 |
| `OS/IoT-iotda-k8s-master-HCE-2-0-2503...qcow2` | — | 统一虚机模板，HCE 2.0 64bit，`min_disk=50G`、`min_ram=1024`，导入时改名为 `*-vda.qcow2` |

> 镜像版本号多为 `25.3.0.20250xxx` 时间戳形式，升级/扩容时务必保持同批次包一致。

### 5.2 部署脚本包

`iotda_plugins_common_25.3.0.*.tar.gz` 内含 1696 个条目，核心目录：

- `script_new/install_iotda.sh`、`upgrade_iotda.sh`、`gardener_client.py`、`docker_load.sh`、`docker_tag_push.sh`；
- `script_new/config-fc-standard/`、`config-fc-agile/`：各场景 `input_blueprint.json`、`manifest_jobs.json`，另有 `config-hcs-svc`、`config-hcs-mgmt`、`config-hcso-*` 等变体；
- `script_new/service-kafka-ep.yaml`、`namespace.yaml`、`secret.yaml`；
- `script_new/opengauss/`：GaussDB 迁移/切换脚本（`iotdamgr_switch_to_gaussdb.sh` 等）；
- `script/es_index/`：ES 索引模板（event、alarm、actuator、filebeat、metricbeat、heartbeat）。

### 5.3 设备模拟器

`MQTT_Simulator/device_demo_mqttnet.exe`（.NET Framework 4.5.2，基于 MQTTnet）用于验证设备接入：

- `device_demo_mqttnet.exe.config` 默认示例：`serverUri=iot-mqtts.cn-north-4.myhuaweicloud.com`、`portIsSsl=8883`、`portNotSsl=1883`，`deviceId`/`deviceSecret` 需填写实际值；
- `certificate/rootcert.pem`、`mqtts_ca_cert.pem` 为 CA 证书，本地 FC 环境必须替换为“总览”下载的 CA 证书，并将文件名改为 `rootcert.pem`；
- 支持 SSL 开关、QoS 0/1（不支持 QoS 2）、新建连接、订阅 Topic、发布 Topic、属性上报、接收同步命令。

---

## 6. 用户端如何接入

### 6.1 设备侧接入（以 MQTT(S) 为例）

1. **获取接入信息**：登录 IoTDA Console → “总览” → 查看 MQTTS/MQTT 接入地址与端口，下载 CA 证书。本地 FC 场景一般使用 IP 接入（域名显示 `default`）；非加密端口默认关闭。
2. **创建产品**：Console → “产品” → 创建产品，选择协议 `MQTT`、数据格式 `JSON`；在产品详情“模型定义”中添加 service 与属性/命令/事件（如 `Battery.batteryLevel`）。
3. **注册设备**：Console → “设备 > 所有设备” → 注册设备，填写资源空间、产品、设备标识码 `nodeId`、设备名称、认证类型（密钥或 X.509）、密钥/指纹。
   - 设备 ID 生成规则：`product_id + "_" + node_id`（也可指定）。
   - 密钥丢失只能重置，无法找回。
   - 批量注册可下载模板，单次最多 30000 行。
4. **获取连接参数**：设备详情 → “MQTT 连接参数”查看 `clientId`、`username`、`password`。
5. **建立连接**：MQTT.fx 或模拟器配置 Broker Address/Port、Client ID、Username/Password、SSL/TLS 开启、TLSv1.2、CA 证书文件；连接成功后设备状态显示“在线”。
6. **收发消息**：
   - 属性上报：按物模型上报（Console 设备详情可查看最新快照）；
   - 消息上报/自定义 Topic：平台不解析内容，适合透传给 Kafka；
   - 订阅下行 Topic 接收命令/消息，典型系统 Topic 见 2.3 节，完整清单以“设备侧 API 参考 > Topic 定义”为准；
   - 用“消息跟踪”排查上报/下发是否到达平台。
7. **NB-IoT/CoAP 设备**：创建产品时选 CoAP + 二进制码流，在“插件开发”中开发编解码脚本，将二进制转换为 `properties_report` 等标准 JSON，再走同样的规则转发。
8. **泛协议设备**：通过边缘网关协议转换（Modbus、OPC-UA）或自研云网关接入。

### 6.2 应用侧接入

1. **Console 访问**：`https://{nginx_console_eip}/`（业务面）与 `https://{nginx_console_eip}:8443/opsportal`（运维面）。admin 仅有管理权限，业务访问需新建账号并赋 `te_admin` / `sys_iotda_admin` 角色。
2. **北向 API**：`https://{Endpoint}/v5/iot/{project_id}/...`，使用 AK/SK 签名换取 `X-Auth-Token`。常用接口：查询/创建设备、下发命令、下发消息、软固件升级、查询历史数据等。
3. **订阅推送（数据出平台）**：

| 方式 | 配置要点 | 适用 |
|---|---|---|
| Kafka | Console → 规则 > 数据转发 → 数据来源/触发事件/SQL → 转发目标“第三方消息队列Kafka”（地址、Topic、SASL PLAIN 或 SCRAM-SHA-256/512）→ 启动规则 | 高吞吐、可回放、与 `car-monit-api` 对接 |
| AMQP | 平台服务端订阅，地址 `amqps://{address}:5671`，`vhost=default`，TLS 1.2+，Receiver Link 15 秒内建立，成功后 ACK | 应用直连平台接收实时推送 |
| HTTP/HTTPS | 配置推送 URL（如 `https://10.10.10.10:8443/example/`），`Content-Type: application/json; charset=utf-8` | 简单 Webhook 场景 |
| ROMA / MRS / OBS / InfluxDB / G100 | 按目标填写连接信息与凭证 | 集成、归档、时序分析 |

4. **规则 SQL**：在数据转发规则中编辑 SQL，做字段筛选、别名、条件过滤；未被订阅的数据类型不会推送。Kafka 为“推到 Kafka 后由应用自行消费”，不消费会造成积压；AMQP 未 ACK 的数据在断链后重推，超过 1 天缓存会清空。

### 6.3 与 `car-monit-api` 的对接建议（重要）

架构设计文档 `docs/architecture-traffic-query-design.md:570-617` 的规划是：设备 → IoTDA → Kafka（`device-raw-data`）→ Flink → GaussDB/CDC → ES，查询层为 `car-monit-api`。但当前代码实现与此不同：

```text
570:617:docs/architecture-traffic-query-design.md
### 4.1 总体架构
    subgraph 采集层
        D[华为/海康/信路威设备] --> I[华为 IoTDA]
    end
    I -->|规则引擎转发| K[(Kafka 集群)]
...
- `device-raw-data`：统一原始流，消息带 `stateType`、`deviceId`、`plateRaw`、`plateColorRaw`、`captureTime`、`payload`。
```

实际消费侧：

```text
88:92:ruoyi-system/src/main/java/com/ruoyi/base/kafka/consumer/SnapshotFlowKafkaConsumerV2.java
    @KafkaListener(
        topics = "${kafka.topic.snapshot-flow:ods-rt-szdn-snapshot-flow}",
        containerFactory = "kafkaListenerContainerFactory"
    )
    public void consumeBatch(List<ConsumerRecord<String, String>> records, Acknowledgment ack) {
```

```text
162:188:ruoyi-system/src/main/java/com/ruoyi/base/kafka/consumer/SnapshotFlowKafkaConsumerV2.java
            String operationType = jsonObject.getString("operationType");
            data = jsonObject.getObject("data", OdsRtSzdnSnapshotFlowAddcode.class);
            if (data == null || data.getBigId() == null) { ... sendToDLQ(...); }
            String idempotentKey = data.getBigId();
            if ("INSERT".equals(operationType) || "UPDATE".equals(operationType)) { ... }
            else if ("DELETE".equals(operationType)) { snapshotFlowService.removeById(data.getBigId()); }
```

```text
303:333:ruoyi-admin/src/main/resources/application.yml
kafka:
  bootstrap-servers: 127.0.0.1:9092
  topic:
    snapshot-flow: ods-rt-szdn-snapshot-flow
    snapshot-flow-dlq: ods-rt-szdn-snapshot-flow-dlq
  consumer:
    group-id: snapshot-flow-consumer-group
    enable-auto-commit: false
    auto-offset-reset: earliest
    max-poll-records: 500
  listener:
    ack-mode: manual_immediate
    concurrency: 3
```

因此推荐两种落地方式（二选一）：

- **方式 A（改 IoTDA 侧，推荐先做）**：在 IoTDA 创建数据转发规则，把门架/卡口等设备上报的属性或消息经 SQL 变换后写入 Kafka Topic `ods-rt-szdn-snapshot-flow`，消息体严格为 `{"operationType":"INSERT|UPDATE|DELETE","data":{...}}`，`data` 为 `OdsRtSzdnSnapshotFlowAddcode` 可反序列化字段，且必须包含 `bigId` 与用于月度分表的 `snapshottime`。分区键建议用 `bigId`（消费端以 `bigId` 做幂等键），生产端开启 `acks=all`/幂等，3 副本、`min.insync.replicas=2`。
- **方式 B（改应用侧）**：保留 IoTDA 原始流 `device-raw-data`（`stateType`/`deviceId`/`plateRaw`/`captureTime`/`payload` 等），在 `car-monit-api` 前增加适配消费者或 Flink 清洗任务，将其转换为现有 `{operationType, data}` 信封后再写入 `ods-rt-szdn-snapshot-flow`。

另外必须注意：

- `kafka.bootstrap-servers` 当前硬编码为 `127.0.0.1:9092`，部署时改为实际 Kafka 地址（建议通过环境变量注入）。
- 消费端为批量消费 + 手动立即确认 + `bigId` 幂等；失败重试 3 次后进 DLQ `ods-rt-szdn-snapshot-flow-dlq`，需在 IoTDA 规则或适配层保证 `bigId` 全局唯一。
- 数据按月分表/分区（按 `snapshottime` 路由），IoTDA 转发字段中必须带齐时间字段；时区与 NTP 配置要在部署阶段统一。
- 未发现仓库中有 IoTDA SDK、MQTT/AMQP 客户端或 IoTDA 地址/凭据配置；IoTDA 与后端之间目前仅通过 Kafka 契约衔接。相关实现参考：`KAFKA_CONSUMER_OPTIMIZATION_GUIDE.md`、`SNAPSHOT_FLOW_OPTIMIZATION_README.md`、`KAFKA_ES_INSTALL_GUIDE.md`。

---

## 7. 常见问题速查

| 现象 | 排查方向 |
|---|---|
| 设备连接失败 | 检查接入地址/端口、TLS 与 CA 证书、clientId/username/password、设备是否被冻结、安全组与 LVS DNAT |
| 设备在线但无数据 | 设备详情开启“消息跟踪”；确认上报 Topic/物模型属性定义与 payload 格式匹配；检查编解码插件 |
| 规则已创建但应用收不到 | 规则是否“启动”；数据来源/触发事件是否匹配；SQL 是否过滤掉字段；Kafka/AMQP/HTTP 目标连通性；消费组是否积压 |
| AMQP 频繁断连 | TLS 版本、15 秒内是否建立 Receiver Link、时间戳偏差是否超过 5 分钟、心跳 `idleTimeout`、1 天未 ACK 缓存过期 |
| 安装失败 | Builder：`/var/log/fcb/install_fcb.log`；Ops：`/opt/CCOps/gardener/log` + `gardener_client.py ... RETRY/SEARCH`；IoTDA 应用：`/opt/garden/log`、`nohup.out` |
| 虚机/容器网络不通 | 反亲和与节点分组、VLAN 池/端口组、安全组、防火墙/NAT、Pod/Service 网段是否与现有网络冲突（尤其避开 172.17） |

---

## 8. 资料索引

- `/mnt/d/IoTDAPak/FC场景IoTDA安装指南.pdf`（对应 Windows `D:\IoTDAPak\FC场景IoTDA安装指南.pdf`）：第 1–12 章，安装主流程。
- `/mnt/d/IoTDAPak/IoT设备接入(IoTDA)25.3.0用户指南(forHCSOnline25.3.0)01(3).pdf`：产品介绍、快速入门、规则/数据转发、订阅推送、最佳实践、FAQ。
- `/mnt/d/IoTDAPak/1_IoT基于FusionCube底座部署 LLD (Copy).xlsx`：`2-1-1 版本配套`、`3-1 IP&VLAN规划`、`4-1 虚机详细信息`、`4-2 虚机安全组规划`、`4-3 外部防火墙诉求`。
- `/mnt/d/IoTDAPak/IoTDA/`、`/mnt/d/IoTDAPak/OPS/`、`/mnt/d/IoTDAPak/k8s/`、`/mnt/d/IoTDAPak/OS/`：镜像与部署工具。
- `/mnt/d/IoTDAPak/MQTT_Simulator/`：设备侧 MQTT 模拟器与 CA 证书。
- 本仓库：`docs/architecture-traffic-query-design.md`、`ruoyi-admin/src/main/resources/application.yml`、`ruoyi-system/.../SnapshotFlowKafkaConsumerV2.java`。
