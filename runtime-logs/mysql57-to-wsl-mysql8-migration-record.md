<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-26 14:45:00
-->

# MySQL 5.7.40 目录实例迁移到 WSL Docker MySQL 8.0 记录

> 日期：2026-11-26
> 源：Windows `D:\work\mysql-5.7.40-winx64`（`my.ini`：端口 `3306`，datadir 为同目录 `data`）
> 目标：WSL2 Docker 容器 `mysql8.0`（`mysql:8.0.30`，宿主 `3307` -> 容器 `3306`）
> 凭据：源/目标均为 `root`，密码由运行环境注入（`SRC_PWD` / `DST_PWD`），不写入本文档。

## 1. 关键发现 / 坑

1. 目录名虽为 `mysql-5.7.40-winx64`，但实际运行的二进制是 `D:\work\mysql-8.0.30-winx64\bin\mysqld.exe`，命令行参数为 `--defaults-file=D:\work\mysql-5.7.40-winx64\my.ini --console`；`SELECT VERSION()` 返回 `8.0.30`，data 目录已是 8.0 格式（`.sdi`、`mysql.ibd`）。因此按 **8.0 -> 8.0 逻辑导出导入**处理，不直接拷贝 data 目录。
2. Windows 服务 `mysql5`、`mysql8` 均为 `STOPPED`，`net start mysql5` 返回“拒绝访问”（非管理员）。改用 `cmd.exe /c start /B mysqld.exe --defaults-file=...` 启动。注意 PATH 优先解析到 8.0 的 `mysqld.exe`，启动后用 `Get-CimInstance Win32_Process` 核对 `ExecutablePath` / `CommandLine`。
3. 误启动出两个 `mysqld` 会同时写同一 data 目录，必须 `taskkill /PID <多余PID> /F` 只保留监听 `3306` 的那个。
4. WSL 调用 Windows `.exe` 时 `MYSQL_PWD` 不会被继承（一直报 `using password: NO`），因此用显式 `--password="$SRC_PWD"`。
5. 库名以 `information_schema.SCHEMATA` 为准：实际是 `pmpx*`，不是 `pmmp*`；共 **21 个业务库**，排除 `mysql` / `sys` / `performance_schema` / `information_schema`。
6. 目标已存在 `nacos_config`（同样 12 张表），导入会 `DROP/CREATE` 覆盖；其余源库在目标为新增。目标原有 `acme_prod` / `carmonitdb` 等库不受影响。

## 2. 执行步骤（本次实际使用的命令）

```bash
# 0) 运行时注入密码，不落盘
read -rs SRC_PWD; export SRC_PWD
read -rs DST_PWD; export DST_PWD

# 1) 启动源实例（Windows 服务启动被拒绝时的替代方案）
/mnt/c/Windows/System32/cmd.exe /c 'cd /d D:\work\mysql-5.7.40-winx64 && start /B mysqld.exe --defaults-file=D:\work\mysql-5.7.40-winx64\my.ini --console'

# 2) 核对进程与源实例连通性
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command \
  "Get-CimInstance Win32_Process -Filter \"name='mysqld.exe'\" | Select-Object ProcessId,ExecutablePath,CommandLine | Format-List"
'/mnt/d/work/mysql-5.7.40-winx64/bin/mysql.exe' --host=127.0.0.1 --port=3306 --user=root --password="$SRC_PWD" \
  -e 'SELECT VERSION(); SHOW DATABASES;'

# 3) 取精确库名（避免 pmmp / pmpx 混淆）
'/mnt/d/work/mysql-5.7.40-winx64/bin/mysql.exe' --host=127.0.0.1 --port=3306 --user=root --password="$SRC_PWD" \
  -N -e "SELECT SCHEMA_NAME, HEX(SCHEMA_NAME) FROM information_schema.SCHEMATA ORDER BY SCHEMA_NAME;"

# 4) 逻辑导出 21 个业务库
mkdir -p /home/dev/mysql-migration
'/mnt/d/work/mysql-5.7.40-winx64/bin/mysqldump.exe' \
  --host=127.0.0.1 --port=3306 --user=root --password="$SRC_PWD" \
  --single-transaction --routines --events --triggers \
  --hex-blob --default-character-set=utf8mb4 --set-gtid-purged=OFF \
  --databases admin.net aymssaas bootstrapadmin diyueframe dzcg_pro lamp_none \
              nacos_config netcoredev openauthdb pmpx pmpx_ac pmpx_app pmpx_bi \
              pmpx_codegen pmpx_config pmpx_job pmpx_mp pmpx_pay pmpx_report \
              rvsystem wzgl \
  > /home/dev/mysql-migration/mysql57_biz_20261126.sql 2>/home/dev/mysql-migration/dump.err

# 5) 导入 WSL Docker 目标（不使用 -f，让错误显式暴露）
docker exec -i -e MYSQL_PWD="$DST_PWD" mysql8.0 mysql -uroot --default-character-set=utf8mb4 \
  < /home/dev/mysql-migration/mysql57_biz_20261126.sql

# 6) 校验：逐库表数 / 数据字节
DBS='admin.net aymssaas bootstrapadmin diyueframe dzcg_pro lamp_none nacos_config netcoredev openauthdb pmpx pmpx_ac pmpx_app pmpx_bi pmpx_codegen pmpx_config pmpx_job pmpx_mp pmpx_pay pmpx_report rvsystem wzgl'
for db in $DBS; do
  s=$('/mnt/d/work/mysql-5.7.40-winx64/bin/mysql.exe' --host=127.0.0.1 --port=3306 --user=root --password="$SRC_PWD" -N \
       -e "SELECT COUNT(*),COALESCE(SUM(data_length+index_length),0) FROM information_schema.tables WHERE table_schema='$db'" 2>/dev/null)
  d=$(docker exec -e MYSQL_PWD="$DST_PWD" mysql8.0 mysql -uroot -N -e "SELECT COUNT(*),COALESCE(SUM(data_length+index_length),0) FROM information_schema.tables WHERE table_schema='$db'")
  echo "$db src=$s dst=$d"
done

# 7) 校验：逐表精确 COUNT(*)，对比源与目标输出
#    counts.sql 由 information_schema.tables 生成，形如：
#    SELECT 'wzgl.表名', COUNT(*) FROM `wzgl`.`表名`;
'/mnt/d/work/mysql-5.7.40-winx64/bin/mysql.exe' --host=127.0.0.1 --port=3306 --user=root --password="$SRC_PWD" -N -B \
  < /home/dev/mysql-migration/counts.sql > /home/dev/mysql-migration/counts_src.txt
docker exec -i -e MYSQL_PWD="$DST_PWD" mysql8.0 mysql -uroot -N -B \
  < /home/dev/mysql-migration/counts.sql > /home/dev/mysql-migration/counts_dst.txt
diff -u /home/dev/mysql-migration/counts_src.txt /home/dev/mysql-migration/counts_dst.txt
```

## 3. 验证结论

- 导出：`mysql57_biz_20261126.sql` 约 24MB，含 21 个 `CREATE DATABASE`；`dump.err` 只有密码告警。
- 导入：`exit=0`，stderr 为空，无 `-f` 吞错。
- 表数：21 个库逐一一致；合计 **652 张表**。
- 精确行数：652 张表 `COUNT(*)` 源/目标 `diff` 为空（完全一致）。
- 数据字节差异来自源库碎片/统计口径，非数据丢失：`wzgl` 10,354,688 -> 7,274,496，`nacos_config` 5,652,480 -> 6,701,056，`admin.net` 2,523,136 -> 2,555,904。
- `nacos_config` 12 张表已按源重建；目标原有业务库未被修改。

## 4. 回滚 / 遗留

- Windows 原 data 目录 `D:\work\mysql-5.7.40-winx64\data` 未做任何修改，保留为直接回滚源。
- 备份 SQL 与校验脚本位于 `/home/dev/mysql-migration/`（dump、dump.err、counts.sql、counts_src.txt、counts_dst.txt）。
- 本次未停止源实例（占用 3306，与目标容器宿主 3307 无冲突）；如需释放资源可手动停掉该 `mysqld.exe` 进程。
- 恢复时只需重放第 5 步导入命令；注意 `nacos_config` 会再次被源库覆盖。
