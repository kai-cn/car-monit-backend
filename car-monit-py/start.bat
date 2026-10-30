@echo off
rem Migrated from: ry.bat
rem
rem Java 版是 start javaw %JVM_OPTS% -jar ruoyi-admin.jar；Python 版换成
rem start "car-monit-py" %PYTHON% run.py，端口从 config/application.yml 的
rem server.port 读（默认 9989），没有 JVM 参数。
rem
rem 进程识别：Java 版用 jps -l 再按 jar 名过滤；这里调 scripts/app_pid.py
rem （用 psutil 读命令行，按入口文件名 run.py 匹配），与 start.sh 共用同一份逻辑。
rem
rem 两种用法都支持：
rem     start.bat            交互菜单（与 ry.bat 一致：1 启动 / 2 关闭 / 3 重启 / 4 状态 / 5 退出）
rem     start.bat start      直接执行，便于写进计划任务 / 部署脚本
rem
rem 编码：本文件与 ry.bat 一样用 GBK。中文 Windows 的 cmd 按代码页 936 解析 .bat，
rem UTF-8 的多字节序列会被当成 GBK 双字节，把紧随其后的 ASCII 字节（含 CR/LF）吃掉。
setlocal

rem 工程目录：去掉 %~dp0 末尾的反斜杠，否则 cd /d "…\" 会报「文件名、目录名或卷标语法不正确」
set "APP_HOME=%~dp0"
if "%APP_HOME:~-1%"=="\" set "APP_HOME=%APP_HOME:~0,-1%"
cd /d "%APP_HOME%"

rem 解释器：优先工程自带的 .venv，其次 PATH 上的 python
set "PYTHON=%APP_HOME%\.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=python"

set AppName=run.py

if "%~1"=="" goto menu
if /i "%~1"=="start" goto start
if /i "%~1"=="stop" goto stop
if /i "%~1"=="restart" goto restart
if /i "%~1"=="status" goto status
echo 不支持的操作: %~1  {start^|stop^|restart^|status}
exit /b 1

:menu
ECHO.
	ECHO.  [1] 启动%AppName%
	ECHO.  [2] 关闭%AppName%
	ECHO.  [3] 重启%AppName%
	ECHO.  [4] 启动状态 %AppName%
	ECHO.  [5] 退 出
ECHO.

ECHO.请输入选择项目的序号:
set /p ID=
	IF "%ID%"=="1" GOTO start
	IF "%ID%"=="2" GOTO stop
	IF "%ID%"=="3" GOTO restart
	IF "%ID%"=="4" GOTO status
	IF "%ID%"=="5" EXIT /b 0
PAUSE
goto menu

rem 等价的 jps 查询：交给 scripts/app_pid.py。
rem 这里不用 for /f —— 反引号里的命令带中文路径/引号时，cmd 会把整串当程序名
rem （「不是内部或外部命令」），落到临时文件再 set /p 读第一行更稳。
:query
set "PID="
set "PID_FILE=%TEMP%\car-monit-py.pid"
"%PYTHON%" "%APP_HOME%\scripts\app_pid.py" > "%PID_FILE%" 2>nul
if exist "%PID_FILE%" set /p PID=<"%PID_FILE%"
goto :eof

:start
call :query
if defined PID goto start_already_running
start "car-monit-py" "%PYTHON%" %AppName%
echo  starting……
echo  Start %AppName% success...
goto :eof

:start_already_running
echo %AppName% is running... (pid:%PID%)
goto :eof

:stop
call :query
if not defined PID goto stop_not_running
echo prepare to kill %AppName% (pid:%PID%)
taskkill /f /pid %PID%
goto :eof

:stop_not_running
echo process %AppName% does not exists
goto :eof

:restart
call :stop
timeout /t 2 /nobreak > nul
call :start
goto :eof

:status
call :query
if not defined PID goto status_dead
echo %AppName% is running (pid:%PID%)
goto :eof

:status_dead
echo process %AppName% is dead
goto :eof
