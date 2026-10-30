@echo off
chcp 65001 >nul
echo ========================================
echo   启动 Kafka & Elasticsearch 启动脚本
echo ========================================
echo.

REM 设置目录（根据实际目录调整
set KAFKA_DIR=D:\work\kafka_2.13-4.0.0
set ES_DIR=D:\work\elasticsearch-7.15.2

echo [1/3] 检查目录检查...
if not exist "%KAFKA_DIR%" (
    echo [错误] Kafka 目录不存在: %KAFKA_DIR%
    pause
    exit /b 1
)
if not exist "%ES_DIR%" (
    echo [错误] Elasticsearch 目录不存在: %ES_DIR%
    pause
    exit /b 1
)
echo [OK] 目录检查通过
echo.

REM 启动 Kafka（KRaft模式，无需ZooKeeper
echo [2/3] 正在启动 Kafka...
cd /d "%KAFKA_DIR%"
start "Kafka Server" cmd /k ".\bin\windows\kafka-server-start.bat .\config\server.properties

timeout /t 10 /nobreak >nul

REM 启动 Elasticsearch
echo [3/3] 正在启动 Elasticsearch...
cd /d "%ES_DIR%"
start "Elasticsearch" cmd /k ".\bin\elasticsearch.bat

echo.
echo ========================================
echo   服务启动中，请检查各窗口日志...
echo ========================================
echo.
echo Kafka 端口: 9092
echo Elasticsearch 端口: 9200
echo.
echo 提示：按任意键关闭此窗口（不会停止服务
echo.
echo 停止服务请手动关闭各命令行窗口
pause
