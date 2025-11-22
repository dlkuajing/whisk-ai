@echo off
chcp 65001 >nul
echo 启动 Whisk AI V2...
echo.
WhiskAI_V2.exe
if errorlevel 1 (
    echo.
    echo 程序异常退出，请检查错误信息
    pause
)
