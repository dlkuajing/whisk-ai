#!/usr/bin/env python3
"""
构建 Whisk V2 Windows可执行文件
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_requirements():
    """检查必要的工具是否已安装"""
    print("检查构建环境...")
    
    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller 已安装 (版本: {PyInstaller.__version__})")
    except ImportError:
        print("✗ PyInstaller 未安装")
        print("请运行: pip install pyinstaller")
        return False
    
    # 检查其他依赖
    required_modules = ['requests', 'playwright']
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} 已安装")
        except ImportError:
            print(f"✗ {module} 未安装")
            print(f"请运行: pip install {module}")
            return False
    
    return True

def create_launcher_script():
    """创建启动器脚本（解决playwright路径问题）"""
    launcher_content = '''#!/usr/bin/env python3
"""
Whisk V2 启动器
解决打包后的路径问题
"""

import sys
import os

# 设置环境变量
if getattr(sys, 'frozen', False):
    # 如果是打包后的exe
    application_path = os.path.dirname(sys.executable)
else:
    # 如果是脚本
    application_path = os.path.dirname(os.path.abspath(__file__))

# 将路径添加到系统路径
sys.path.insert(0, application_path)

# 导入并运行主程序
try:
    from whisk_gui_v2 import WhiskGUIV2
    app = WhiskGUIV2()
    app.run()
except Exception as e:
    import tkinter as tk
    from tkinter import messagebox
    
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("启动错误", f"程序启动失败:\\n{str(e)}")
    root.destroy()
'''
    
    with open('whisk_launcher_v2.py', 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    print("✓ 创建启动器脚本")

def build_exe():
    """构建exe文件"""
    print("\n开始构建exe文件...")
    
    # 创建启动器脚本
    create_launcher_script()
    
    # 创建简化的spec文件
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['whisk_launcher_v2.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('whisk_gui_v2.py', '.'),
        ('whisk_core_v2.py', '.'),
    ],
    hiddenimports=[
        'requests',
        'playwright',
        'playwright.sync_api',
        'tkinter',
        'PIL',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WhiskAI_V2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('whisk_v2_simple.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    # 运行PyInstaller
    cmd = [sys.executable, '-m', 'PyInstaller', 
           '--clean',
           '--noconfirm',
           'whisk_v2_simple.spec']
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✓ 构建成功！")
        
        # 检查输出文件
        exe_path = Path('dist/WhiskAI_V2.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"生成的文件: {exe_path}")
            print(f"文件大小: {size_mb:.2f} MB")
        else:
            print("✗ 未找到生成的exe文件")
            
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 构建失败: {e}")
        return False
    
    return True

def create_readme():
    """创建使用说明"""
    readme_content = '''# WhiskAI V2 Windows版使用说明

## 系统要求
- Windows 10/11 64位
- 比特浏览器已安装并运行

## 使用步骤

1. **准备工作**
   - 启动比特浏览器
   - 打开一个或多个浏览器窗口
   - 访问 Google Whisk 网站

2. **运行程序**
   - 双击 WhiskAI_V2.exe
   - 程序会自动启动GUI界面

3. **配置参数**
   - 刷新并选择浏览器窗口
   - 输入生成提示词
   - 选择纵横比
   - 设置生成数量

4. **开始生成**
   - 点击"添加任务"
   - 程序会自动生成和下载图片

## 注意事项

1. **首次运行**
   - Windows可能会提示"Windows已保护你的电脑"
   - 点击"更多信息" → "仍要运行"

2. **防病毒软件**
   - 某些防病毒软件可能误报
   - 请将程序添加到白名单

3. **playwright问题**
   - 如果提示缺少playwright
   - 请在程序目录运行: pip install playwright

## 常见问题

**Q: 程序无法启动？**
A: 检查是否缺少依赖，尝试安装 Visual C++ Redistributable

**Q: 找不到浏览器？**
A: 确保比特浏览器正在运行，并已打开窗口

**Q: 下载失败？**
A: 检查网络连接，确保可以访问Google服务

## 技术支持
如遇到问题，请保留错误截图和日志
'''
    
    with open('README_Windows.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("✓ 创建使用说明")

def main():
    """主函数"""
    print("=" * 50)
    print("Whisk V2 Windows打包工具")
    print("=" * 50)
    
    # 检查环境
    if not check_requirements():
        print("\n请先安装必要的依赖")
        return
    
    # 构建exe
    if build_exe():
        create_readme()
        print("\n打包完成！")
        print("输出目录: dist/")
        print("请查看 README_Windows.md 了解使用方法")
    else:
        print("\n打包失败，请检查错误信息")

if __name__ == "__main__":
    main()