@echo off
chcp 65001 >nul
title 🚀 Whisk AI V2 - 一键打包EXE工具

cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                   🚀 Whisk AI V2 一键打包工具                ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 📋 功能说明：
echo    • 自动检查并安装所有依赖
echo    • 一键打包成Windows EXE可执行文件  
echo    • 生成完整的分发包，可直接在其他电脑使用
echo.
echo ⚠️  注意事项：
echo    • 请确保网络连接正常
echo    • 整个过程需要3-10分钟，请耐心等待
echo    • 首次运行会下载较多依赖文件
echo.
echo 按任意键开始打包...
pause >nul

cls
echo.
echo ════════════════════════════════════════════════════════════════
echo 🔍 正在检查环境...
echo ════════════════════════════════════════════════════════════════

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ 未检测到Python环境！
    echo.
    echo 🔧 解决方案：
    echo    1. 下载Python：https://www.python.org/downloads/
    echo    2. 安装时务必勾选 "Add Python to PATH"
    echo    3. 重启命令提示符后重新运行此脚本
    echo.
    goto :error_exit
)

echo ✅ Python环境检查通过
python --version

echo.
echo ════════════════════════════════════════════════════════════════
echo 📦 正在安装和更新依赖...
echo ════════════════════════════════════════════════════════════════

REM 静默安装所有依赖
echo 🔄 更新pip...
python -m pip install --upgrade pip --quiet

echo 🔄 安装项目依赖...
pip install -r requirements_v2.txt --quiet

echo 🔄 安装打包工具...
pip install pyinstaller --quiet

echo 🔄 安装浏览器驱动...
python -m playwright install chromium --quiet >nul 2>&1

echo ✅ 所有依赖安装完成

echo.
echo ════════════════════════════════════════════════════════════════
echo 🔨 正在打包EXE文件...
echo ════════════════════════════════════════════════════════════════

python build_exe_v2.py

REM 检查打包结果
if exist "WhiskAI_V2_Distribution\WhiskAI_V2.exe" (
    goto :success
) else (
    goto :failed
)

:success
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                      🎉 打包成功完成！                        ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 📁 输出位置：WhiskAI_V2_Distribution\
echo.
echo 📋 包含文件：
echo    🎯 WhiskAI_V2.exe          主程序文件
echo    📖 README.md               使用说明
echo    🚀 启动Whisk.bat           启动脚本
echo    ⚙️  config_gui_v2.json      配置文件
echo.
echo 💡 使用方法：
echo    1. 将整个 WhiskAI_V2_Distribution 文件夹复制到目标电脑
echo    2. 双击 WhiskAI_V2.exe 或 启动Whisk.bat 运行程序
echo    3. 首次运行可能需要允许防火墙访问
echo.
echo ✅ 现在可以在任何Windows 10/11电脑上使用了！
echo.
goto :end

:failed
cls
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                      ❌ 打包失败                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 🔍 可能原因：
echo    • 网络连接问题，依赖下载失败
echo    • 磁盘空间不足（需要至少500MB空间）
echo    • 防病毒软件阻止了打包过程
echo    • Python环境配置问题
echo.
echo 🔧 解决建议：
echo    1. 检查网络连接，重新运行脚本
echo    2. 临时关闭防病毒软件
echo    3. 清理磁盘空间
echo    4. 以管理员身份运行此脚本
echo.
goto :end

:error_exit
echo.
echo ════════════════════════════════════════════════════════════════
pause
exit /b 1

:end
echo ════════════════════════════════════════════════════════════════
echo 按任意键退出...
pause >nul 