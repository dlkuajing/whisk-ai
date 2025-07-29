@echo off
chcp 65001 >nul
echo ================================================
echo Whisk V2 Windows 打包脚本
echo ================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python未安装或未添加到PATH
    echo 请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

echo [1/4] 安装依赖...
pip install -r requirements_v2.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [2/4] 安装PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo [错误] PyInstaller安装失败
    pause
    exit /b 1
)

echo.
echo [3/4] 安装Playwright...
pip install playwright
python -m playwright install chromium
if errorlevel 1 (
    echo [警告] Playwright安装可能不完整
)

echo.
echo [4/4] 开始打包...
python build_exe_v2.py

echo.
echo ================================================
echo 打包流程完成！
echo 输出文件在 dist 目录中
echo ================================================
pause