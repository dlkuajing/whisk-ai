@echo off
chcp 65001 >nul
title Whisk AI V2 - Windows EXE 打包工具

echo.
echo ========================================================
echo 🚀 Whisk AI V2 Windows EXE 打包工具
echo ========================================================
echo.
echo 此工具将自动安装依赖并打包成EXE可执行文件
echo 请确保已连接互联网，整个过程可能需要几分钟时间
echo.
pause

REM 检查Python是否安装
echo [检查] 验证Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ [错误] Python未安装或未添加到PATH环境变量
    echo.
    echo 请先安装Python 3.8或更高版本：
    echo 1. 访问 https://www.python.org/downloads/
    echo 2. 下载并安装Python
    echo 3. 安装时勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

python --version
echo ✅ Python环境检查通过
echo.

REM 升级pip
echo [1/5] 升级pip包管理器...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ⚠️ [警告] pip升级失败，继续执行...
)
echo.

REM 安装项目依赖
echo [2/5] 安装项目依赖...
echo 正在安装：requests, playwright, Pillow...
pip install -r requirements_v2.txt
if errorlevel 1 (
    echo.
    echo ❌ [错误] 项目依赖安装失败
    echo 请检查网络连接或手动执行：pip install -r requirements_v2.txt
    echo.
    pause
    exit /b 1
)
echo ✅ 项目依赖安装完成
echo.

REM 安装PyInstaller
echo [3/5] 安装PyInstaller打包工具...
pip install pyinstaller
if errorlevel 1 (
    echo.
    echo ❌ [错误] PyInstaller安装失败
    echo 请检查网络连接或手动执行：pip install pyinstaller
    echo.
    pause
    exit /b 1
)
echo ✅ PyInstaller安装完成
echo.

REM 安装Playwright浏览器
echo [4/5] 安装Playwright浏览器驱动...
echo 正在下载Chromium浏览器驱动，请耐心等待...
python -m playwright install chromium
if errorlevel 1 (
    echo ⚠️ [警告] Playwright浏览器驱动安装可能不完整
    echo 这不会影响EXE打包，但可能影响运行时功能
)
echo ✅ Playwright浏览器驱动安装完成
echo.

REM 开始打包
echo [5/5] 开始EXE打包流程...
echo 正在执行打包脚本，请等待...
echo.
python build_exe_v2.py

REM 检查打包结果
if exist "WhiskAI_V2_Distribution\WhiskAI_V2.exe" (
    echo.
    echo ========================================================
    echo 🎉 打包成功完成！
    echo ========================================================
    echo.
    echo 📁 输出目录：WhiskAI_V2_Distribution\
    echo 🎯 主程序：WhiskAI_V2_Distribution\WhiskAI_V2.exe
    echo 📖 使用说明：WhiskAI_V2_Distribution\README.md
    echo 🚀 启动脚本：WhiskAI_V2_Distribution\启动Whisk.bat
    echo.
    echo ✅ 现在您可以将整个 WhiskAI_V2_Distribution 文件夹
    echo    复制到其他Windows电脑上使用！
    echo.
    echo 💡 使用提示：
    echo    1. 双击 WhiskAI_V2.exe 直接运行
    echo    2. 或使用 启动Whisk.bat 脚本运行
    echo    3. 首次运行可能需要允许Windows防火墙访问
    echo.
) else (
    echo.
    echo ========================================================
    echo ❌ 打包失败
    echo ========================================================
    echo.
    echo 可能的原因：
    echo 1. 依赖安装不完整
    echo 2. 磁盘空间不足
    echo 3. 防病毒软件阻止了打包过程
    echo.
    echo 建议解决方案：
    echo 1. 重新运行此脚本
    echo 2. 临时关闭防病毒软件
    echo 3. 确保有足够的磁盘空间（至少500MB）
    echo.
)

echo ========================================================
pause