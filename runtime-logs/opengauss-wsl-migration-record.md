<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# openGauss 从 VirtualBox 迁移到 WSL2 + V3 带认证联调记录

- 日期：2026-11-12
- 目标：把 VM `192.168.56.10` 的 openGauss 容器（含数据）迁到 WSL openEuler，并启动 backend V3 / api V3 完成 openGauss 业务验证
- 凭据约定：所有口令、令牌、密钥**仅由运行环境注入**，本文档、仓库、日志一律不转录明文，统一写作 `<由运行环境注入>`

---

## 0. 环境事实（迁移前）

| 项 | 值 |
|---|---|
| 主机 | Windows 10 Home China / build 22000，13.8GB RAM，12 vCPU；C: 200GB、D: 275.7GB |
| VirtualBox | 7.1.8，VM `vagrant_box_node1_1770773366633_8782`，1GB / 1CPU，VMDK 动态盘 40GB 逻辑 / 27.86GB 已分配 |
| VM 网络 | NIC1 NAT 转发 `127.0.0.1:15432->5432`、`127.0.0.1:2222->22`；NIC2 host-only `192.168.56.10` |
| WSL | `openEuler-24.03-LTS-SP4`，WSL 3.0.3，内核 6.18.54.1，Docker 25.0.3 / overlay2 / journald |
| WSL 磁盘 | `D:\wsl\openEuler-24.03-LTS-SP4\ext4.vhdx`，初始 7.96GB，**非 sparse** |
| 共享文件夹 | `vagrant_data -> D:\vagrant_box\MyVagrantSyncFolder`，`autoMount=false`，不可用 |

关键结论：

- WSL2 的 `ext4.vhdx` 与 VirtualBox 动态 VMDK **同样只涨不缩**，且 VMDK 在 `discard=off` 下连 guest TRIM 都不传递。
- WSL 3.0.3 在本机 build 22000 上：`--set-sparse true` 可设置，但 `fstrim` 不触发自动回收；**`--compact` 与稀疏互斥**（稀疏时报错 `ERROR_VIRTUAL_DISK_LIMITATION`）。可靠做法是保持非稀疏 + 手动 `--compact`。
- `127.0.0.1:5432` 由 `wslrelay.exe` 转发到 WSL openGauss；`127.0.0.1:15432` 的 IPv4 被 `VirtualBoxVM` 旧 NAT 占用，**api 必须用 5432**。
- `networkingMode=mirrored` 需 Windows 11 22H2+，本机 22000 不支持，会回退 NAT。

---

## 1. 完整迁移命令清单（可复现，按顺序）

### 1.1 只读核查

```powershell
Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DeviceID -in 'C:','D:' }
& 'D:\VirtualBox\VBoxManage.exe' list vms
& 'D:\VirtualBox\VBoxManage.exe' showvminfo 'vagrant_box_node1_1770773366633_8782' --machinereadable
& 'D:\VirtualBox\VBoxManage.exe' showhdinfo 'D:\vagrant_box\VirtualBox VMs\vagrant_box_node1_1770773366633_8782\centos-7-1-1.x86_64.vmdk'
& 'D:\VirtualBox\VBoxManage.exe' list hostonlyifs
wsl.exe --list --verbose
wsl.exe --version
fsutil sparse queryflag 'D:\wsl\openEuler-24.03-LTS-SP4\ext4.vhdx'
Get-NetIPAddress -AddressFamily IPv4
arp -a -N 192.168.56.1
```

### 1.2 WSL 磁盘回收（正确顺序：先 compact，再决定是否 sparse）

```powershell
$d = 'openEuler-24.03-LTS-SP4'
wsl.exe --shutdown
wsl.exe --manage $d --set-sparse false          # 必须非稀疏，否则 compact 报错
wsl.exe --manage $d --compact                  # 16.454GB -> 9.617GB
fsutil sparse queryflag 'D:\wsl\openEuler-24.03-LTS-SP4\ext4.vhdx'
```

实测：`--set-sparse true` → `fstrim -av` 后 VHDX 仍 16.454GB（实际占用 16.028GB），自动回收无效；改回非稀疏后 `--compact` 成功。

失败/无效命令（记录以免重踩）：

```powershell
wsl.exe --manage $d --compact                  # 稀疏状态下：ERROR_VIRTUAL_DISK_LIMITATION
wsl.exe -d $d -u root --exec /usr/sbin/fstrim -av   # 有效 TRIM，但不缩小 VHDX
```

`.wslconfig` 最终变更（`C:\Users\abelz\.wslconfig`）：

```ini
[wsl2]
memory=4GB
swap=2GB
processors=2
swapFile=D:\\wsl\\swap\\swap.vhdx
localhostForwarding=true
vmIdleTimeout=3600000
kernelCommandLine=vsyscall=emulate

[general]
instanceIdleTimeout=-1
```

`kernelCommandLine=vsyscall=emulate` 是 Oracle 11g 老镜像所需（见 1.10）：WSL 6.18 内核默认不模拟 vsyscall 页，镜像内 `/bin/sh` 一启动即 SIGSEGV（容器 `Exited (139)`、日志为空）。加该参数并 `wsl --shutdown` 重启后生效，`/proc/cmdline` 可见 `vsyscall=emulate`。

原因：WSL 空闲超时会把实例连带 docker/容器终止，导致 openGauss 反复 `gaussdb exit(0)`。改后实测 90 秒持续 `Up`、`RestartCount=0`。**未启用 `sparseVhd`，`autoMemoryReclaim=gradual` 会破坏 WSL 内 docker daemon，禁用。**

### 1.3 腾空间（直接删除，不放回收站）

```powershell
Remove-Item -LiteralPath 'D:\vagrant_box\boxes' -Recurse -Force
Remove-Item -LiteralPath 'D:\vagrant_box\VirtualBox VMs\vagrant_box_node1_1770773366633_8782\Snapshots\2026-11-11T08-08-09-771490000Z.sav' -Force
# node1_华为源_带docker.ova 已不存在
```

保留 `centos-7-1-1.x86_64.vmdk`（数据仍在其中，作为回滚）；VM 全程未删。

### 1.4 VM 免密（一次交互，凭据不落命令）

```powershell
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" |
  ssh -p 2222 root@127.0.0.1 "mkdir -p /root/.ssh && cat >> /root/.ssh/authorized_keys && chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys"
```

VM 重启后 host-only 网卡曾漂移到 `169.254.x.x` 且 `192.168.56.1` 跑到另一张卡，导致 ping「一般故障」；重启后自动恢复 `以太网 7 = 192.168.56.1/24`。SSH 一律走 NAT `127.0.0.1:2222`。

### 1.5 openGauss 数据导出（`docker commit` 无效，必须导 bind mount）

实测挂载：

```text
opengauss : bind /data/opengauss -> /var/lib/opengauss
oracle11g: volume /var/lib/docker/volumes/c150ce.../_data -> /home/oracle/app/oracle/oradata
            bind   /oracle/data -> /opt/oracle/oradata
```

`docker commit opengauss opengauss-with-data:3.0.0` 得到 480MB（与基础镜像相同），**数据一个字节都没进去**：`docker commit` 只提交容器可写层，不含任何 mount。该镜像应删除。

```bash
# VM 侧只读核查
du -sh /data/opengauss
ls -ln /data/opengauss
docker inspect -f '{{json .HostConfig.Binds}}' opengauss
docker inspect -f 'Entrypoint={{json .Config.Entrypoint}} Cmd={{json .Config.Cmd}}' opengauss
docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' opengauss | sed 's/=.*/=<redacted>/'
docker stop opengauss          # 冷备一致性
docker rmi opengauss-with-data:3.0.0
```

流式冷备（**不落中间文件**，避免 7GB 落盘把 D 盘写满；必须用 `cmd /c` 保二进制，PowerShell 管道会破坏 tar）：

```cmd
cmd /c "ssh -p 2222 -o BatchMode=yes -o LogLevel=ERROR root@127.0.0.1 ""tar --numeric-owner -cf - -C /data/opengauss ."" | wsl -d openEuler-24.03-LTS-SP4 -u root --exec tar --numeric-owner -xf - -C /data/opengauss"
```

```powershell
wsl.exe -d openEuler-24.03-LTS-SP4 -u root --exec mkdir -p /data/opengauss /oracle/data /srv/oracle/oradata
```

验证：

```powershell
wsl.exe -d openEuler-24.03-LTS-SP4 -u root --exec bash -lc "du -sh /data/opengauss; ls -ln /data/opengauss/data | head -20; cat /data/opengauss/data/PG_VERSION"
# 期望 1.3G / uid=70 gid=70 / PG_VERSION 9.2
```

### 1.6 在 WSL 启动 openGauss 容器（环境变量从 VM 管道注入，不落盘不回显）

```powershell
$envLines = ssh -p 2222 -o BatchMode=yes -o LogLevel=ERROR root@127.0.0.1 "docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' opengauss"
$envLines | wsl -d openEuler-24.03-LTS-SP4 -u root --exec bash -c 'cat > /run/og.env && docker run -d --name opengauss -p 5432:5432 -p 15432:5432 -v /data/opengauss:/var/lib/opengauss --env-file /run/og.env enmotech/opengauss:3.0.0; rc=$?; rm -f /run/og.env; exit $rc'
wsl.exe -d openEuler-24.03-LTS-SP4 --exec docker update --restart always opengauss
wsl.exe -d openEuler-24.03-LTS-SP4 --exec docker start opengauss
```

gsql 不在默认 PATH，且需 `LD_LIBRARY_PATH`：

```powershell
$d='openEuler-24.03-LTS-SP4'
$ld='LD_LIBRARY_PATH=/usr/local/opengauss/lib:/usr/local/opengauss/lib/postgresql'
wsl.exe -d $d -u root --exec docker exec -e $ld -u 70 opengauss /usr/local/opengauss/bin/gsql -d RuoYi -c "select 1 as ok;"
wsl.exe -d $d -u root --exec docker exec -e $ld -u 70 opengauss /usr/local/opengauss/bin/gsql -d RuoYi -c "select schemaname,count(*) from pg_tables where schemaname not in ('pg_catalog','information_schema') group by 1 order by 2 desc;"
```

结果：`RuoYi / omm / postgres / template0 / template1` 5 库；`carmonitdb 84` 表、`jl_data01 59`、`dbe_pldeveloper 2`、`db4ai 1`、`public 1`；`jl_data01.ods_rt_szdn_snapshot_flow_addcode` 936 行。

`pg_hba.conf` 中 `host all all 0.0.0.0/0 md5` 允许从 Windows 经 WSL relay 密码连接。

### 1.7 启动依赖服务（每类仅 1 个实例，限制内存）

```powershell
# 清残留锁
Remove-Item 'D:\work\mysql-8.0.30-winx64\data\LAPTOP-R2ABR5SO.pid' -Force -ErrorAction SilentlyContinue
Remove-Item 'D:\work\Redis-8.10.2-Windows-x64-msys2\redis_6379.pid' -Force -ErrorAction SilentlyContinue

$env:ES_JAVA_OPTS='-Xms512m -Xmx512m'
$env:KAFKA_HEAP_OPTS='-Xmx512m'
$env:JAVA_HOME='D:\jdk\temurin-17\jdk-17.0.21+9'      # Kafka 4.0 需要 JDK17，系统 PATH 是 JDK8
$env:PATH="$env:JAVA_HOME\bin;$env:PATH"

Start-Process 'D:\work\mysql-8.0.30-winx64\bin\mysqld.exe' -ArgumentList @('--defaults-file=D:\work\mysql-8.0.30-winx64\my.ini','--console') -WindowStyle Hidden
Start-Process 'D:\work\Redis-8.10.2-Windows-x64-msys2\redis-server.exe' -ArgumentList @('redis.conf') -WorkingDirectory 'D:\work\Redis-8.10.2-Windows-x64-msys2' -WindowStyle Hidden
Start-Process 'cmd.exe' -ArgumentList @('/c','D:\work\elasticsearch-7.15.2\bin\elasticsearch.bat') -WorkingDirectory 'D:\work\elasticsearch-7.15.2' -WindowStyle Hidden
Start-Process 'cmd.exe' -ArgumentList @('/c','D:\work\kafka_2.13-4.0.0\bin\windows\kafka-server-start.bat D:\work\kafka_2.13-4.0.0\config\server.properties') -WorkingDirectory 'D:\work\kafka_2.13-4.0.0' -WindowStyle Hidden
```

两个坑：

- Redis 是 MSYS2 版，传 Windows 绝对路径会被拼成 `/work/.../D:\...` 而报 `can't open config file`；**必须传相对 `redis.conf`** 并设 WorkingDirectory。
- Kafka 4.0 KRaft 需要 JDK17；`D:\work\kafka-data-20261108\meta.properties` 已存在，无需 `kafka-storage format`。

### 1.8 启动 api V3 / backend V3

api（**覆盖 openGauss 地址为 WSL**）：

```powershell
$env:SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL='jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false&tinyInt1isBit=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai'
Start-Process 'powershell.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File','D:\work\runtime-logs\start-api-v3.ps1') -WindowStyle Hidden
```

`start-api-v3.ps1` 关键点：JDK8 `-Xms512m -Xmx1g -Dserver.port=9902 -jar ...pro-business-api-1.0.jar --spring.config.additional-location=file:D:/work/runtime-logs/api-local.properties`；`api-local.properties` 只提供 `spring.datasource.dynamic.datasource.master.password`；脚本内 `$env:` 注入若干开关与 MySQL 字典账号（**值不在本文档记录**）。

backend：

```powershell
$env:EXPORT_DOWNLOAD_SECRET = <运行时随机生成，长度 >=16，不落盘>
Start-Process 'D:\jdk\jdk1.8.0_202\bin\java.exe' -ArgumentList @(
  '-Xms512m','-Xmx1g','-jar',
  'D:\work\IdeaProjects\car-monit-backend-java-V3\ruoyi-admin\target\ruoyi-admin.jar',
  '--server.port=9989','--spring.profiles.active=druid',
  '--vehicleMonitor.baseUrl=http://127.0.0.1:9902'
) -WorkingDirectory 'D:\work\IdeaProjects\car-monit-backend-java-V3\ruoyi-admin\target' -WindowStyle Hidden `
  -RedirectStandardOutput 'D:\work\runtime-logs\backend-v3.console.out.log' `
  -RedirectStandardError  'D:\work\runtime-logs\backend-v3.console.err.log'
```

内部守卫两侧均保持默认空值（`traffic.security.internal-token` / `traffic-api.internal-token`），回环放行；若启用守卫，`TRAFFIC_INTERNAL_TOKEN` 与 `TRAFFIC_API_INTERNAL_TOKEN` 必须一致。`EXPORT_DOWNLOAD_SECRET` 每次启动随机，重启 backend 后需重新注入同一个值。

### 1.9 带认证端到端

```powershell
$pw = $env:E2E_PASSWORD                     # <由运行环境注入>，不落盘
$body = @{ username='<管理员账号>'; password=$pw } | ConvertTo-Json
$lg = Invoke-RestMethod -Uri 'http://127.0.0.1:9989/login' -Method Post -Body $body -ContentType 'application/json'
$h = @{ Authorization = "Bearer $($lg.token)" }
foreach ($u in @(
  '/manager/bigScreen/carStatistics?applyTime1=2026-11-01&applyTime2=2026-11-12',
  '/manager/bigScreen/incomeStatistic?queryDateType=suo&startDate=2026-11-01',
  '/manager/bigScreen/topTen?startTime=2026-11-01&endTime=2026-11-12')) {
  $w = Invoke-WebRequest -Uri "http://127.0.0.1:9989$u" -Headers $h
  "$u HTTP=$([int]$w.StatusCode) Cache=$($w.Headers['X-Cache']) Degrade=$($w.Headers['X-Degrade'])"
}
```

历史 `backend-v3-9989-token.txt` 的 JWT 已过期（401），必须重新登录；漏掉 `Bearer ` 前缀也会 401。

### 1.10 Oracle 11g 迁移（6.85GB 镜像 + 2.2GB 匿名 volume）

只读核对（VM 侧）：

```bash
docker ps -a --filter name=oracle11g --format '{{.Names}} {{.Status}} {{.Ports}}'
docker inspect -f '{{range .Mounts}}{{.Type}} {{.Source}} -> {{.Destination}}{{println}}{{end}}' oracle11g
docker inspect -f 'Privileged={{.HostConfig.Privileged}} ShmSize={{.HostConfig.ShmSize}} Restart={{.HostConfig.RestartPolicy.Name}} PortBindings={{json .HostConfig.PortBindings}}' oracle11g
docker inspect -f 'Entrypoint={{json .Config.Entrypoint}} Cmd={{json .Config.Cmd}} User={{.Config.User}}' oracle11g
docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' oracle11g | sed 's/=.*/=<redacted>/'
du -sh /oracle/data                        # 实测 0，空
du -sh /var/lib/docker/volumes/c150ce.../_data   # 实测 2.2G，属主 500:500
```

结论：数据全在匿名 volume `/var/lib/docker/volumes/c150ce72389024df2edffb02c291c00c4043b66b8f383a27300eaf33afa5bac5/_data`（内含 `helowin/` 与 `control01.ctl`、`system01.dbf`、`sysaux01.dbf`、`undotbs01.dbf`、`rvsystem.dbf`、`redo0*.log`）；`/oracle/data` 为空但容器仍以 bind mount 挂它，新容器需挂同名空目录。镜像默认 `User=oracle`，`ORACLE_PWD` 是运行时注入（不在镜像 env 中）。

**两个流式传输脚本**（放后台执行，避免 6.85GB 长命令超时；`cmd /c` 保二进制，凭据不落盘）：

`D:\work\runtime-logs\oracle-image-transfer.cmd`：

```bat
@echo off
ssh -p 2222 -o BatchMode=yes -o LogLevel=ERROR root@127.0.0.1 "docker save registry.cn-hangzhou.aliyuncs.com/helowin/oracle_11g:latest" | wsl -d openEuler-24.03-LTS-SP4 --exec docker load > "D:\work\runtime-logs\oracle-image-load.log" 2>&1
echo EXITCODE=%ERRORLEVEL% >> "D:\work\runtime-logs\oracle-image-load.log"
```

`D:\work\runtime-logs\oracle-volume-transfer.cmd`：

```bat
@echo off
ssh -p 2222 -o BatchMode=yes -o LogLevel=ERROR root@127.0.0.1 "tar --numeric-owner -cf - -C /var/lib/docker/volumes/c150ce72389024df2edffb02c291c00c4043b66b8f383a27300eaf33afa5bac5/_data ." | wsl -d openEuler-24.03-LTS-SP4 -u root --exec tar --numeric-owner -xf - -C /srv/oracle/oradata > "D:\work\runtime-logs\oracle-volume-transfer.log" 2>&1
echo EXITCODE=%ERRORLEVEL% >> "D:\work\runtime-logs\oracle-volume-transfer.log"
```

```powershell
# 冷备一致性：先停 VM 容器（Exited 137 为 docker stop 超时后的 SIGKILL，Oracle 会 crash recovery）
ssh -p 2222 -o BatchMode=yes root@127.0.0.1 "docker stop oracle11g"

# 后台启动两个传输（完成标志：日志出现 "Loaded image:" / EXITCODE=0）
Start-Process 'cmd.exe' -ArgumentList @('/c','D:\work\runtime-logs\oracle-image-transfer.cmd') -WindowStyle Hidden
Start-Process 'cmd.exe' -ArgumentList @('/c','D:\work\runtime-logs\oracle-volume-transfer.cmd') -WindowStyle Hidden
```

**关键：镜像导入后必须立刻 compact**。`docker load` 期间 `/var/lib/docker/tmp` 峰值 6.5GB、VHDX 涨到 25.558GB、D 盘只剩 1.38GB；临时文件删掉后 VHDX 不会自动缩：

```powershell
wsl.exe --shutdown
wsl.exe --manage openEuler-24.03-LTS-SP4 --compact      # 25.558GB -> 19.248GB，D 盘回到 10GB
```

**坑 1：`Exited (139)` / SIGSEGV（日志为空）**。镜像为 v2 schema1 旧格式但 `docker save/load` 不走 registry manifest，不需要 `legacy-schema1`；真正原因是老 glibc 依赖 vsyscall 页。验证方式：

```powershell
wsl -d openEuler-24.03-LTS-SP4 -u root --exec bash -lc "docker run --rm --entrypoint /bin/sh <image> -c 'echo SH_OK'"
# 修复前 exit=139；加 kernelCommandLine=vsyscall=emulate 并 wsl --shutdown 后输出 SH_OK
```

**坑 2：`ORA-00214` 控制文件版本不一致**。只迁 volume + 镜像会漏掉容器可写层里的第二份控制文件：

```text
/home/oracle/app/oracle/oradata/helowin/control01.ctl          -> 迁移来的，version 5506
/home/oracle/app/oracle/flash_recovery_area/helowin/control02.ctl -> 镜像自带 2016 年，version 841
```

修复（多路复用控制文件标准做法，用最新副本覆盖旧副本，保留 uid/gid）：

```powershell
$d='openEuler-24.03-LTS-SP4'
wsl -d $d --exec docker stop oracle11g
wsl -d $d -u root --exec docker cp --archive /srv/oracle/oradata/helowin/control01.ctl oracle11g:/home/oracle/app/oracle/flash_recovery_area/helowin/control02.ctl
wsl -d $d --exec docker start oracle11g
# 两份 md5 应一致：805081989c2a243041689c3a821597ef
```

启动容器（对齐原参数：privileged / shm 64MB / 1521 / 两个挂载点；环境变量从 VM 管道注入，不落盘不回显）：

```powershell
$envLines = ssh -p 2222 -o BatchMode=yes -o LogLevel=ERROR root@127.0.0.1 "docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' oracle11g"
$envLines | wsl -d openEuler-24.03-LTS-SP4 -u root --exec bash -c 'cat > /run/oracle.env && docker run -d --name oracle11g --privileged --shm-size 67108864 -p 1521:1521 -v /oracle/data:/opt/oracle/oradata -v /srv/oracle/oradata:/home/oracle/app/oracle/oradata --env-file /run/oracle.env registry.cn-hangzhou.aliyuncs.com/helowin/oracle_11g:latest; rc=$?; rm -f /run/oracle.env; exit $rc'
wsl -d openEuler-24.03-LTS-SP4 --exec docker update --restart always oracle11g
```

业务验证（OS 认证 `/ as sysdba`，无口令；脚本 `D:\work\runtime-logs\oracle-probe.sql` / `oracle-probe.sh`）：

```powershell
wsl -d openEuler-24.03-LTS-SP4 -u root --exec docker cp /mnt/d/work/runtime-logs/oracle-probe.sql oracle11g:/tmp/oracle-probe.sql
wsl -d openEuler-24.03-LTS-SP4 -u root --exec docker cp /mnt/d/work/runtime-logs/oracle-probe.sh oracle11g:/tmp/oracle-probe.sh
wsl -d openEuler-24.03-LTS-SP4 -u root --exec docker exec -u oracle oracle11g /bin/sh /tmp/oracle-probe.sh
```

注意：`sqlplus -S / as sysdba` 的 `/ as sysdba` 含空格，经 `wsl --exec` 会被拆词导致 sqlplus 打印用法；且 PowerShell 会把 `@/tmp/...` 当成 splatting。因此用容器内 shell 脚本执行，不要直接拼命令行。

---

## 2. 验证结果

| 项 | 结果 |
|---|---|
| login | `code=200`，取得 token（值不落盘） |
| carStatistics / incomeStatistic / topTen | 均 `HTTP=200`，`X-Cache=MISS`，`X-Degrade` 空（无降级） |
| api 日志新增 SQL | `SELECT ... FROM jl_data01.dws*`（escape/income/topTen 统计）、`SELECT big_id FROM jl_data01.ods_rt_szdn_snapshot_flow_addcode WHERE snapshottime BETWEEN ...`、`jl_data01.search_sync_*` 读写 |
| openGauss `pg_stat_activity` | `gaussdb / 172.17.0.1 / PostgreSQL JDBC Driver` 4~5 条空闲连接池 |
| api 回环端点 | `/api/v3/es/readiness` `code=200`；`/api/v3/export/capabilities` HTTP 200 |
| openGauss 容器 | `Up 37 minutes`，未再重启 |
| 端口 | 3307 / 6379 / 9092 / 9200 / 9902 / 9989 / 5432 全部监听；单实例约束满足 |
| java 进程 | `elasticsearch(5000)` / `kafka(21408)` / `api-v3(21832)` / `backend-v3(22480)` 各 1 |
| Oracle 镜像 | `Loaded image: registry.cn-hangzhou.aliyuncs.com/helowin/oracle_11g:latest`，`EXITCODE=0` |
| Oracle volume | `EXITCODE=0`，2.3GB 落 `/srv/oracle/oradata`，属主 `500:500`，`system01.dbf` / `sysaux01.dbf` / `undotbs01.dbf` / `rvsystem.dbf` / `redo0*.log` / `control01.ctl` 齐全 |
| Oracle 实例 | `helowin OPEN / ACTIVE`，`HELOWIN READ WRITE / NOARCHIVELOG`；crash recovery 后 `Database mounted. Database opened.` |
| Oracle 表空间 | 8 个全部 `ONLINE`（SYSTEM / SYSAUX / UNDOTBS1 / USERS / EXAMPLE / TEMP / RVSYSTEM / RVSYSTEM_TEMP） |
| Oracle 数据文件 | 6 个全部 `AVAILABLE`（system 690MB / sysaux 580MB / undotbs 95MB / users 5MB / example 100MB / rvsystem 500MB） |
| Oracle 业务对象 | `RVSYSTEM`：203 表 / 220 索引 / 84 LOB / 16 序列 / 1 函数；`SCOTT`：4 表 / 2 索引 |
| 迁移后端口 | 3307 / 6379 / 9092 / 9200 / 9902 / 9989 / 5432 / **1521** 全部监听 |
| 迁移后 openGauss | 重启 WSL 后仍 `jl_data01` 59 张表可查；api readiness `code=200` |

结论：`backend(9989) → api(9902) → WSL openGauss` 带认证链路打通，且统计 SQL 确实落在迁移后的 openGauss 业务库；Oracle 11g 也已在 WSL 以迁移后的数据卷 `OPEN / READ WRITE` 运行，业务 schema 完整。两个数据库迁移均完成，VM 仍保留作回滚。

---

## 3. 所有相关文档清单

### 3.1 用户提供的安装记录（临时目录，可能随会话清理，已脱敏归档）

三份原始文件在 `C:\Users\abelz\AppData\Local\Temp\codebuddy-dropped-files\`，会随会话清理，因此已**脱敏后归档**到：

```
D:\work\runtime-logs\install-records\docker-install-opengauss.redacted.txt
D:\work\runtime-logs\install-records\docker-install-oracle-setpassword.redacted.txt
D:\work\runtime-logs\install-records\docker-daemon.json            # 原文无凭据，未改动
```

归档时把所有口令替换为 `<由运行环境注入>`；已用严格模式扫描（口令字面量、`identified by xxx`、明文连接串等），三份归档文件均 `hits=0`。**归档文件不入库**，保留在 `runtime-logs` 供本机查阅；原始临时文件不建议复制进仓库。

注意：`helowin` 在下文出现时是镜像名 / `ORACLE_SID` / 数据目录名，**不是口令**；对应的 root 口令已脱敏。

| 原路径 | 关键内容 |
|---|---|
| `C:\Users\abelz\AppData\Local\Temp\codebuddy-dropped-files\cd319e8c-...\docker 安装openguass.txt` | 镜像 `enmotech/opengauss:3.0.0`；`docker run --restart=always -p 5432:5432 -v /data/opengauss:/var/lib/opengauss -e GS_PASSWORD=<由运行环境注入>`；早期命令带 `--privileged=true`（实际运行容器未启用）；daemon.json 配国内镜像加速 |
| `C:\Users\abelz\AppData\Local\Temp\codebuddy-dropped-files\b3cded03-...\docker安装Oracle，设置密码.txt` | 镜像 `registry.cn-hangzhou.aliyuncs.com/helowin/oracle_11g`（**v2 schema1 旧格式**，Docker 26.0 默认禁用 / 28.2 移除；WSL 为 25.0.3 可用，`skopeo` 转换曾失败）；`docker run --privileged --restart=always -p 1521:1521 -v /oracle/data:/opt/oracle/oradata -e ORACLE_PWD=<由运行环境注入>`；容器内需配 `ORACLE_HOME`/`ORACLE_SID=helowin`/`PATH` 与 sqlplus 软链；含 sys/system/scott 及各业务用户的建表/授权/改密 SQL（**口令不转录**）；`RVSYSTEM` 表空间数据文件位于 `/home/oracle/app/oracle/oradata/helowin/rvsystem.dbf`，即匿名 volume |
| `C:\Users\abelz\AppData\Local\Temp\codebuddy-dropped-files\8f5a8cea-...\docker-daemon.json` | 16 个 registry-mirrors；`"features": {"enabled": ["legacy-schema1"]}`。该开关只影响 `docker pull/push` 旧格式 registry manifest，**不影响 `docker save | docker load`**，故本次迁移未修改 WSL 的 `/etc/docker/daemon.json` |

补充事实：`/oracle/data` 实测为 `0`（空），Oracle 数据 2.2GB 全在匿名 volume `c150ce...`；迁 Oracle 时必须迁该 volume，且容器启动仍要挂同路径。

### 3.2 项目文档（两侧 `docs/v3/review/`，文件名一致）

```
01-code-audit-record.md
02-fix-record.md
03-independent-review-record.md
04-reproduction-guide.md
05-ci-verification-record.md
06-authenticated-e2e-record.md
07-wsl-k3s-self-hosted-cicd.md
08-opengauss-wsl-migration-record.md   # 本次新增（本文档副本）
```

绝对路径前缀：

- `D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\`
- `D:\work\IdeaProjects\car-monit-backend-java-V3\docs\v3\review\`

其中 `04-reproduction-guide.md` 记录端口约定（api 9902 / backend 9989 / openGauss 5432）与「单实例」约束；`06-authenticated-e2e-record.md` 记录登录与大屏接口调用方式（口令由环境注入）；`05-ci-verification-record.md` 记录启动前需 ES/Kafka/Redis/MySQL 就绪。

注：backend 侧 `.git/info/exclude` 忽略 `docs/`，新增文档如需纳入版本控制须 `git add -f`；本次未执行任何 git 操作。

### 3.3 配置与脚本

| 路径 | 用途 |
|---|---|
| `C:\Users\abelz\.wslconfig` | WSL 全局配置（本次新增 `vmIdleTimeout` / `instanceIdleTimeout`） |
| `D:\wsl\openEuler-24.03-LTS-SP4\ext4.vhdx` | WSL 根盘，迁移后约 10.7GB，非 sparse |
| `D:\work\runtime-logs\start-api-v3.ps1` | api V3 启动脚本（含 `$env:` 注入，值为凭据，不转录） |
| `D:\work\runtime-logs\api-local.properties` | 仅 `spring.datasource.dynamic.datasource.master.password` |
| `D:\work\runtime-logs\api-v3.console.log` | api 运行日志（含 openGauss SQL 证据） |
| `D:\work\runtime-logs\backend-v3.console.out/err.log` | backend 运行日志 |
| `D:\work\runtime-logs\redis-v3.out/err.log`、`kafka-v3.out/err.log` | 依赖启动日志 |
| `D:\work\runtime-logs\backend-v3-9989-token.txt` | 历史 JWT（已过期，勿复用） |
| `D:\work\runtime-logs\evidence-current-runtime-state.txt` | 迁移前「无 Java / 无中间件监听」基线 |
| `D:\work\runtime-logs\evidence-final-gate.txt` 等 `evidence-*.txt` | 历史门禁与验证证据 |
| `D:\work\IdeaProjects\car-monit-api-java-V3\pro-business-api\src\main\resources\application.yml` | api 主配置，第 42 行原写死 `jdbc:postgresql://192.168.56.10:5432/RuoYi`，由环境变量覆盖 |
| `D:\work\IdeaProjects\car-monit-backend-java-V3\ruoyi-admin\src\main\resources\application.yml` / `application-druid.yml` | backend 端口 9989、profile druid、MySQL 3307、Redis 6379、Kafka 9092、ES 9200、`vehicleMonitor.baseUrl` |
| `D:\work\IdeaProjects\car-monit-backend-java-V3\start-services.bat` | Kafka/ES 启动参考脚本 |
| `D:\work\mysql-8.0.30-winx64\my.ini` | port 3307、datadir 既有（**未另起实例**） |
| `D:\work\kafka_2.13-4.0.0\config\server.properties` | KRaft `process.roles=broker,controller`、`log.dirs=D:/work/kafka-data-20261108` |

### 3.4 本次新增记录

- `D:\work\runtime-logs\opengauss-wsl-migration-record.md`（本文档，主记录）
- `...\car-monit-api-java-V3\docs\v3\review\08-opengauss-wsl-migration-record.md`
- `...\car-monit-backend-java-V3\docs\v3\review\08-opengauss-wsl-migration-record.md`
- `D:\work\runtime-logs\install-records\*`（三份安装记录的脱敏归档，见 3.1）
- `D:\work\runtime-logs\oracle-image-transfer.cmd` / `oracle-volume-transfer.cmd`（两个流式传输脚本，无凭据）
- `D:\work\runtime-logs\oracle-image-load.log` / `oracle-volume-transfer.log`（传输日志，含 `Loaded image:` 与 `EXITCODE=0`）
- `D:\work\runtime-logs\oracle-probe.sql` / `oracle-probe.sh`（Oracle 业务验证脚本，OS 认证无口令）

backend 侧 `.git/info/exclude` 忽略 `docs/`，上述 `08-*.md` 如需纳入版本控制须 `git add -f`；本次未执行任何 git 操作，也未 push/CI。按项目门禁，push 前需独立只读会话复核确认无阻断项。

---

## 4. 状态 / 回滚 / 遗留

- **openGauss 与 Oracle 均已迁移完成并在 WSL 运行**（见第 2 节验证）。VM 中的 `opengauss`/`oracle11g` 容器均已停止，仅作回滚源。
- **磁盘**：VHDX 约 20.8GB、D 盘剩约 6.7GB。两个传输脚本与日志已保留；如需回收 `docker load` 后残留空间，在停机窗口执行 1.10 的 `wsl --shutdown` + `--compact`。
- **遗留**：`kernelCommandLine=vsyscall=emulate` 是全局 WSL 参数，为 Oracle 老镜像保留；若以后不再需要 Oracle 可移除并 `wsl --shutdown` 重启 WSL。
- **VM 仍保留**（VMDK 34.384GB）作为回滚，确认两个库业务无误前不要删除。确认后：

  ```powershell
  & 'D:\VirtualBox\VBoxManage.exe' controlvm 'vagrant_box_node1_1770773366633_8782' acpipowerbutton
  & 'D:\VirtualBox\VBoxManage.exe' unregistervm 'vagrant_box_node1_1770773366633_8782' --delete
  wsl.exe --shutdown
  wsl.exe --manage openEuler-24.03-LTS-SP4 --compact
  ```

- 若 api 配置仍写 `192.168.56.10`，需改为 `127.0.0.1:5432`；若必须保留 `192.168.56.10` 字面量，可在 Windows 侧给网卡附加该 IP 并用 `netsh interface portproxy` 转发（需先停 VM 避免冲突），或升级到 22H2+ 后用 `networkingMode=mirrored`。
- 清理与删除一律直接执行、不放回收站；`.codebuddy` 目录禁止删除。
