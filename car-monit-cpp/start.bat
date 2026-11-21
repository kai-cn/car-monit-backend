@echo off
rem 启动 car-monit-cpp（Windows）
setlocal

set ROOT=%~dp0
cd /d "%ROOT%"

if "%CM_SERVER_PORT%"=="" set CM_SERVER_PORT=9989
if "%CM_CONFIG_DIR%"=="" set CM_CONFIG_DIR=%ROOT%config

where cmake >nul 2>nul
if errorlevel 1 (
  echo 缺少依赖: cmake
  exit /b 1
)

echo ==^> 配置 Release
cmake -S "%ROOT%" -B "%ROOT%build" -DCMAKE_BUILD_TYPE=Release
if errorlevel 1 exit /b 1

echo ==^> 编译
cmake --build "%ROOT%build" --config Release
if errorlevel 1 exit /b 1

echo ==^> 单元测试
"%ROOT%build\Release\carmonit_tests.exe"
if errorlevel 1 exit /b 1

echo ==^> 启动: http://0.0.0.0:%CM_SERVER_PORT%
if exist "%ROOT%build\Release\car-monit-cpp.exe" (
  "%ROOT%build\Release\car-monit-cpp.exe" --config "%CM_CONFIG_DIR%"
) else (
  "%ROOT%build\car-monit-cpp.exe" --config "%CM_CONFIG_DIR%"
)
