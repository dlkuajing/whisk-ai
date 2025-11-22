@echo off
chcp 65001 > nul
echo ========================================
echo  WhiskAI V3 启动器
echo  现代化界面版本
echo ========================================
echo.

:: 检查Python是否安装
python --version > nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [信息] Python已安装
echo.

:: 检查CustomTkinter是否安装
python -c "import customtkinter" > nul 2>&1
if errorlevel 1 (
    echo [警告] CustomTkinter未安装
    echo [提示] 正在安装依赖...
    echo.
    pip install customtkinter>=5.2.0
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [信息] 依赖检查完成
echo [信息] 正在启动WhiskAI V3...
echo.

:: 启动V3界面
python whisk_gui_v3.py

if errorlevel 1 (
    echo.
    echo [错误] 程序运行失败
    pause
)
