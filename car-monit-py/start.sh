#!/bin/sh
# ./start.sh start 启动 stop 停止 restart 重启 status 状态
#
# Migrated from: ry.sh
#
# Java 版是 `nohup java $JVM_OPTS -jar ruoyi-admin.jar`；Python 版换成
# `python run.py`，端口从 config/application.yml 的 server.port 读（默认 9989），
# 不需要 -Xms/-Xmx/-XX:MetaspaceSize 之类的 JVM 参数。
#
# 进程识别：Java 版靠 `jps -l`（按 jar 名匹配）；这里调 scripts/app_pid.py
# （用 psutil 读命令行，按入口文件名 run.py 匹配），与 start.bat 共用同一份逻辑。
#
# 日志：Java 版由 logback 写 logs/ruoyi-admin.jar.log；Python 版由
# app/logging_config.py 写 logs/sys-{info,error,slow,user}.log，所以这里
# 和 ry.sh 一样把 nohup 的 stdout 丢掉。
AppName=run.py
APP_HOME=`cd "$(dirname "$0")" && pwd`
LOG_DIR=$APP_HOME/logs

# 解释器：优先 $PYTHON，其次工程自带的 .venv，最后退回 python3
if [ -z "$PYTHON" ]; then
    if [ -x "$APP_HOME/.venv/bin/python" ]; then
        PYTHON="$APP_HOME/.venv/bin/python"
    else
        PYTHON=python3
    fi
fi

if [ "$1" = "" ];
then
    printf "\033[0;31m 未输入操作名 \033[0m  \033[0;34m {start|stop|restart|status} \033[0m\n"
    exit 1
fi

if [ "$AppName" = "" ];
then
    printf "\033[0;31m 未输入应用名 \033[0m\n"
    exit 1
fi

query()
{
    PID=`"$PYTHON" "$APP_HOME/scripts/app_pid.py" 2>/dev/null`
}

start()
{
    query
    if [ x"$PID" != x"" ]; then
        echo "$AppName is running..."
    else
        cd "$APP_HOME" || exit 1
        mkdir -p "$LOG_DIR"
        nohup "$PYTHON" "$AppName" > /dev/null 2>&1 &
        echo "Start $AppName success..."
    fi
}

stop()
{
    echo "Stop $AppName"

    query
    if [ x"$PID" != x"" ]; then
        kill -TERM $PID
        echo "$AppName (pid:$PID) exiting..."
        while [ x"$PID" != x"" ]
        do
            sleep 1
            query
        done
        echo "$AppName exited."
    else
        echo "$AppName already stopped."
    fi
}

restart()
{
    stop
    sleep 2
    start
}

status()
{
    query
    if [ x"$PID" != x"" ]; then
        echo "$AppName is running..."
    else
        echo "$AppName is not running..."
    fi
}

case $1 in
    start)
    start;;
    stop)
    stop;;
    restart)
    restart;;
    status)
    status;;
    *)
    printf "\033[0;31m 不支持的操作 \033[0m  \033[0;34m {start|stop|restart|status} \033[0m\n"
    exit 1;;
esac
