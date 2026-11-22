<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# car-monit k3d 运维命令速查（本会话有效命令）

> 环境：WSL2 `openEuler-24.03-LTS-SP4`；k3d 集群 `v3`（node 容器 `k3d-v3-server-0`）；
> server 节点 IP `172.18.0.5`，桥接网关 `172.18.0.1`；NodePort backend 30989 / api 30902。
> 约定：`wsl -d openEuler-24.03-LTS-SP4 -- bash -c "..."` 为入口；复杂含 `$`/`|`/引号 的请写成 `.sh` 文件再 `bash /mnt/d/work/runtime-logs/xxx.sh`，最省事。

## A. WSL 基础 / 资源 / 磁盘
```powershell
wsl -l -v                                   # 列出发行版与状态
wsl --shutdown                              # 冷重启（应用 .wslconfig 的内存/CPU）
wsl -d openEuler-24.03-LTS-SP4 -- nproc      # vCPU 数
wsl -d openEuler-24.03-LTS-SP4 -- free -m    # 内存
```
```powershell
# 查 ext4.vhdx 位置（BasePath）
Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' | % { "$($_.GetValue('DistributionName')) => $($_.GetValue('BasePath'))" }
# 磁盘压缩：转稀疏 + WSL 内 fstrim（无需管理员）
wsl --manage openEuler-24.03-LTS-SP4 --set-sparse true
wsl -d openEuler-24.03-LTS-SP4 -- sudo fstrim -av
# 逻辑容量硬压缩（需【管理员】+ Hyper-V 服务，本机未启用则用不了）
Optimize-VHD -Path "D:\wsl\openEuler-24.03-LTS-SP4\ext4.vhdx" -Mode Full
```
`.wslconfig` 关键项：`memory=8GB`、`swap=4GB`、`processors=4`。

## B. Docker 守护与镜像
```bash
systemctl start docker && systemctl is-active docker
docker info | grep -A14 'Registry Mirrors'     # 确认镜像加速已加载
docker ps --format '{{.Names}}\t{{.Status}}'
docker start mysql_wsl opengauss                # 重启后手动拉起 DB
```
```bash
# 启动失败定位（前台下 dockerd 看真实报错）
sudo timeout 8 dockerd 2>&1 | head -25
# 清理
docker image prune -f
docker rmi hello-world:latest
docker exec k3d-v3-server-0 crictl rmi --prune  # 清 k3d containerd 旧镜像
docker system df                                # 镜像/卷占用
```
镜像加速 `/etc/docker/daemon.json`：仅保留 https 镜像，**不要**写 `features:{enabled:[...]}`（非法），**不要**放 `http://` 镜像（dockerd 拒绝）。

## C. Redis 8.10.3（单节点 6379 / 集群 7000-7005 / 切换）
```bash
# 单节点（默认，systemd 自启）
systemctl is-active redis-single
redis-cli -p 6379 ping
redis-cli -p 6379 info server | grep -E 'redis_version|tcp_port'
redis-cli -p 6379 dbsize
redis-cli -p 6379 info clients | grep connected_clients
redis-cli -p 6379 --scan --pattern 'captcha_codes:*' | wc -l
```
```bash
# 集群
sudo bash /mnt/d/work/runtime-logs/start-redis-cluster.sh
redis-cli -p 7000 cluster info | grep cluster_state
redis-cli -p 7000 cluster nodes | awk '{print $1,$3,$4}'   # id/角色
redis-cli -c -p 7000 set foo bar && redis-cli -c -p 7000 get foo   # 跨槽
redis-cli --cluster create 172.18.0.1:7000 172.18.0.1:7001 172.18.0.1:7002 172.18.0.1:7003 172.18.0.1:7004 172.18.0.1:7005 --cluster-replicas 1 --cluster-yes
# 默认只留单节点：停集群
sudo bash /mnt/d/work/runtime-logs/stop-redis-cluster-default.sh
```
```bash
# 单/集群模式切换（务必用“删除+按清单重建”，不要用 set env --remove）
sudo bash /mnt/d/work/runtime-logs/switch-redis-mode.sh single
sudo bash /mnt/d/work/runtime-logs/switch-redis-mode.sh cluster
```

## D. k3d / kubectl / 部署
```bash
k3d cluster list
k3d cluster start v3
docker exec k3d-v3-server-0 kubectl get pods -l 'app in (car-monit-api,car-monit-backend)' -o wide
docker exec k3d-v3-server-0 kubectl get svc
docker exec k3d-v3-server-0 kubectl get endpoints car-monit-backend
docker exec k3d-v3-server-0 kubectl logs deployment/car-monit-api --tail=80
docker exec k3d-v3-server-0 kubectl rollout restart deployment/car-monit-backend deployment/car-monit-api
docker exec k3d-v3-server-0 kubectl exec deployment/car-monit-backend -- bash -c 'env | grep -i redis'
```
```bash
# 应用清单（推荐：cat 管道进 node 的 kubectl apply）
cat /mnt/d/work/runtime-logs/manifests-final.yaml | docker exec -i k3d-v3-server-0 kubectl apply -f -
# 环境变量残留导致串味时：删除重建（最可靠）
docker exec k3d-v3-server-0 kubectl delete deployment car-monit-backend car-monit-api
cat /mnt/d/work/runtime-logs/manifests-final.yaml | docker exec -i k3d-v3-server-0 kubectl apply -f -
# 校验清单语法
docker exec -i k3d-v3-server-0 kubectl apply --dry-run=client -f - < /mnt/d/work/runtime-logs/manifests-final.yaml
```
> 注：`kubectl set env --remove=KEY` 与 `kubectl apply` 的三方合并**都不会删除**此前 `set env` 追加的键；切 Redis 模式一律「删除+重建」。

## E. 数据库（WSL 容器，桥接网关）
```bash
docker start mysql_wsl    # 3307
docker start opengauss    # 5432
docker inspect --format '{{.Name}} {{.Config.Image}} {{json .NetworkSettings.Ports}}' mysql_wsl opengauss
```

## F. ES / Kafka
```bash
# 启动（各 400M）
sudo bash /mnt/d/work/runtime-logs/start-es.sh
sudo bash /mnt/d/work/runtime-logs/start-kafka.sh
# ES 探活 / 索引
curl -s http://172.18.0.1:9200/_cluster/health
curl -s 'http://172.18.0.1:9200/_cat/indices?v'
sysctl -w vm.max_map_count=262144        # ES 启动前
```
```bash
# Kafka 探活 / 主题 / 消费者组
sudo docker exec kafka-wsl /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
sudo docker exec kafka-wsl /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list
sudo docker exec kafka-wsl /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group search-sync-api
# 广播地址往返（验证 172.18.0.1:9092 可达）
sudo docker exec kafka-wsl bash -c "echo hi | /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server 172.18.0.1:9092 --topic search-sync"
sudo docker exec kafka-wsl timeout 10 /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server 172.18.0.1:9092 --topic search-sync --from-beginning --max-messages 1
```

## G. 验证 / 冒烟 / 诊断
```bash
bash /mnt/d/work/runtime-logs/smoke-test.sh          # 冒烟：captcha/api 守卫/list
bash /mnt/d/work/runtime-logs/captcha-check.sh        # 验证码连测
bash /mnt/d/work/runtime-logs/verify-login.sh         # 登录链路（读 6379）
bash /mnt/d/work/runtime-logs/verify-login-cluster.sh # 登录链路（读集群 7000）
bash /mnt/d/work/runtime-logs/final-verify.sh         # 综合状态（Pod/环境/captcha/ES/Kafka/版本）
bash /mnt/d/work/runtime-logs/fault-drill.sh          # 删 Pod 自愈演练
# NodePort 直连（经 server 节点 IP）
curl -s -m 10 http://172.18.0.5:30989/captchaImage | head -c 60
curl -s -m 8 -o /dev/null -w '%{http_code}\n' http://172.18.0.5:30902/api/v3/es/readiness
```
```bash
# Pod 内直连 Redis（诊断 RESP 数据面）
docker exec k3d-v3-server-0 kubectl exec deployment/car-monit-backend -- bash -c \
  'exec 3<>/dev/tcp/172.18.0.1/6379; printf "*1\r\n\$4\r\nPING\r\n" >&3; timeout 5 head -c 24 <&3'
```

## H. 常见坑 / 正确写法
1. **PowerShell 会吞 `$` 和误跑 `|`**：`wsl ... -- bash -c "... | grep ..."` 的管道必须在双引号内；含 `$(...)`/`$var`/复杂引号请写成 `.sh` 文件再 `bash` 执行。
2. **`docker exec k3d-v3-server-0 kubectl exec ... -- sh -c '...'`** 多层引号易崩，同样建议落脚本。
3. **k3s 容器名 ≠ Pod 名**，`crictl ps --name car-monit-backend` 匹配不到，用 `crictl ps | grep` 或直接 `kubectl logs deployment/...`。
4. **验证码接口失败也可能是 HTTP 200 + body `{"msg":"Unable to connect to Redis","code":500}`**，只判 HTTP 码会误判成功，要看 body。
5. **`Metrics API not available`**：k3d 默认无 metrics-server，`kubectl top` 不可用。
