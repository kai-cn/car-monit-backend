#!/usr/bin/env bash
# LEGACY-SCRIPT-ANNOTATION
# 文件：13-install-build-tools.sh
# 用途：运维辅助脚本。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：执行前确认目标环境、凭据与影响范围。
set -u
LOG=/tmp/build-tools.log
echo "start $(date -Is)" > "$LOG"
dnf install -y java-1.8.0-openjdk-devel maven >> "$LOG" 2>&1
echo "DNF_RC=$? $(date -Is)" >> "$LOG"
mkdir -p /home/dev/.m2
cat > /home/dev/.m2/settings.xml <<'EOF'
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0">
  <mirrors>
    <mirror>
      <id>aliyun-public</id>
      <mirrorOf>central</mirrorOf>
      <url>https://maven.aliyun.com/repository/public</url>
    </mirror>
  </mirrors>
</settings>
EOF
chown -R dev:dev /home/dev/.m2
usermod -aG docker dev
java -version >> "$LOG" 2>&1
mvn -v >> "$LOG" 2>&1
echo "GROUPS=$(id dev)" >> "$LOG"
systemctl restart actions-runner.service >> "$LOG" 2>&1
sleep 8
echo "RUNNER=$(systemctl is-active actions-runner.service)" >> "$LOG"
echo "done $(date -Is)" >> "$LOG"
touch /tmp/build-tools.done
