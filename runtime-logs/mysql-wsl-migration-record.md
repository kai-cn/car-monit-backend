<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# MySQL 8 迁移到 WSL 记录

> 日期：2026-11-12
> 目标发行版：`openEuler-24.03-LTS-SP4`（WSL2）
> 凭据一律由运行环境注入，不写入本文档。

## 1. 范围与决策（用户最新指令）
- **迁移**：Windows 上 MySQL 8.0.30（端口 `3307`，`D:\work\mysql-8.0.30-winx64`）的**整个实例**迁到 WSL。
- **不迁**：Kafka、ES 数据全部留在 Windows（按新计划）。
- **Oracle**：WSL 内容器保持停止，等另一个项目使用时再启动；数据已持久化在 `/srv/oracle/oradata`。
- **git / maven**：不再用 Windows 版，改用 WSL 内已安装的 `git 2.54.0` / `maven 3.6.3`（配好身份与 SSH key）。
- **资源策略**：WSL 内存保持 `4GB` 不提额；先停 Oracle 容器释放内存（停后 WSL Mem used 2.0→1.6Gi，available 2.2Gi）。

## 2. 关键前提 / 坑
1. **跨平台不能直拷 data 目录**：Windows MySQL data 在 Linux 上不兼容（大小写、redo、文件路径）。必须逻辑导出。
2. **PowerShell 短选项解析歧义**：`mysqldump -h/-P/-r` 与 `$env:` 变量混合会被误解析报 `Usage`；改用全 `--long` 形式（`--host/--port/--result-file`）。
3. **docker exec 不继承宿主环境变量**：传密码要用 `docker exec -e MYSQL_PWD=...`；而 `wsl --exec` 直接 `-e` 时密码值由 PowerShell `$env:` 展开传入最稳。`bash -lc` 内做 `< /mnt/d/...` 重定向读文件最可靠。
4. **`-f` 静默模式会吞掉导入错误并整批丢数据**：首版用 `--all-databases | mysql -f` 导入，结果 `carmonitdb` 从源 57MB 变成 1.9MB（大表 INSERT 因外键/包错误被忽略）。改用 **"仅导业务库（排除 mysql/sys 系统库）+ 导入前 `SET FOREIGN_KEY_CHECKS=0` + 不用 `-f`"** 解决。
5. **Windows 实例开启 ANSI_QUOTES**：SQL 里双引号会被当列名；统一用单引号包裹字符串字面量。
6. **WSL 偶发 `WSAETIMEDOUT`**：重试即可（刚重启容器时易发）。

## 3. 执行步骤
```text
# (1) 停 WSL Oracle 容器释放内存（数据卷 /srv/oracle/oradata 保留）
docker stop oracle11g

# (2) 拉取与 Windows 同版本镜像
docker pull mysql:8.0.30

# (3) 建数据卷目录（容器 mysql uid=999 可写）
mkdir -p /srv/mysql_wsl/data && chmod 777 /srv/mysql_wsl/data

# (4) 起容器（临时端口 13306 避开 Windows 3307；root 密码与源实例保持一致）
docker run -d --name mysql_wsl --restart unless-stopped \
  -e MYSQL_ROOT_PASSWORD=<与 Windows 3307 源一致> \
  -p 13306:3306 -v /srv/mysql_wsl/data:/var/lib/mysql \
  mysql:8.0.30 \
  --default-authentication-plugin=mysql_native_password \
  --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci \
  --innodb-buffer-pool-size=256M

# (5) Windows 侧导出 12 个业务库（排除 mysql/sys/performance_schema/information_schema）
#     novel 只是 data 目录残留文件夹，Windows 实例 SHOW DATABASES 中并不存在，无需导出
mysqldump --host=127.0.0.1 --port=3307 --user=root --password=<源密码> \
  --single-transaction --routines --events --triggers \
  --databases acme_prod aiotqrd_admin aiotqrd_nacos carmonitdb fx_framedbnew \
              goadmin jszydbnew nacos_config ruoyi-vue-pro smart_work tylc vote \
  --default-character-set=utf8mb4 --set-gtid-purged=OFF --hex-blob \
  --result-file=mysql-biz.sql

# (6) 导入（关闭外键检查，不使用 -f 以便暴露真实错误）
printf 'SET FOREIGN_KEY_CHECKS=0;\n' | cat - mysql-biz.sql | \
  docker exec -i -e MYSQL_PWD=<源密码> mysql_wsl mysql -uroot --default-character-set=utf8mb4

# (7) 校验：库列表 / 各库表数 / carmonitdb 数据字节(≈源) / 抽样行数

# (8) 停 Windows MySQL 服务（mysql8 等），确认 3307 端口 FREE

# (9) 容器改端口接管 3307（停容器重建，数据卷保留，MySQL 检测已有 data 直接加载而非初始化）
docker stop mysql_wsl && docker rm mysql_wsl
docker run -d --name mysql_wsl --restart unless-stopped \
  -e MYSQL_ROOT_PASSWORD=<与源一致> \
  -p 3307:3306 -v /srv/mysql_wsl/data:/var/lib/mysql \
  mysql:8.0.30 <同上启动参数>

# (10) Windows 侧经 localhostForwarding 连 127.0.0.1:3307 验证 SHOW DATABASES 完整
```

## 4. git / maven 配置（WSL 内，root 用户）
```text
git config --global user.name zhukai
git config --global user.email abelzk123@outlook.com
# 复制 Windows SSH key 到 ~/.ssh（id_ed25519/id_rsa 及 .pub、known_hosts），权限 700/600/644
# maven：WSL 已装 3.6.3（Java 1.8.0_502 BiSheng），Windows 无自定义 settings.xml，使用默认
#       本地仓库 ~/.m2/repository（位于 ext4，比 /mnt/d 下快）
```
> 注意：项目工作树在 `/mnt/d`（9p 文件系统）。WSL 内对 `/mnt/d` 做 `git`/`mvn` 会走 9p，性能偏低；如需最佳体验可把仓库 clone 到 WSL ext4 内。

## 5. 验证结论
- WSL 与 Windows 源 **12 个业务库表数逐一一致**（carmonitdb 89、fx_framedbnew 188、acme_prod 430…）。
- `carmonitdb` 数据字节 `60080128` ≈ 源 `60211200`；`car_info` 实际 `248` 行一致。
- Windows 侧 `127.0.0.1:3307` 经 `localhostForwarding` 已指向 WSL 容器，`backend` 连 `127.0.0.1:3307/carmonitdb` 配置**无需改动**。

## 6. 回滚
- Windows 原 MySQL data 目录保留（`D:\work\mysql-8.0.30-winx64\data`，约 1.24GB）作直接回滚源。
- 若需回退：重启 Windows MySQL 服务，并将 WSL 容器端口从 3307 改回 13306 即可。
- VM（`vagrant_box_node1_1770773366633_8782`，VMDK 35.9GB）仍保留作最终回滚源。

## 7. 遗留 / 待办
- WSL 内存仍为 4GB；若后续同时跑 MySQL + openGauss + Oracle 需提 `.wslconfig` memory 并 `wsl --shutdown`。
- 全局内核参数 `vsyscall=emulate` 仅为 Oracle 老镜像保留。
- car-monit 的 `backend`/`api` 仍在 Windows，访问 WSL MySQL 多一跳 localhostForwarding（已验证可达，建议重启 backend 使其连接池重连到 WSL）。
- 建议手动启一次 `backend` 做端到端验证。
