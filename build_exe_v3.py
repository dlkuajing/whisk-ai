#!/usr/bin/env python3
"""
构建 跨海帆-Imager V3 Windows可执行文件
基于CustomTkinter的现代化界面
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

def check_requirements():
    """检查必要的工具是否已安装"""
    print("检查构建环境...")

    # 检查PyInstaller
    try:
        import PyInstaller
        print(f"[OK] PyInstaller 已安装 (版本: {PyInstaller.__version__})")
    except ImportError:
        print("[FAIL] PyInstaller 未安装")
        print("正在安装 PyInstaller...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
            print("[OK] PyInstaller 安装成功")
        except subprocess.CalledProcessError:
            print("[FAIL] PyInstaller 安装失败，请手动安装")
            return False

    # 检查其他依赖
    required_modules = {
        'requests': 'requests>=2.31.0',
        'playwright': 'playwright>=1.40.0',
        'PIL': 'Pillow>=10.0.0',
        'customtkinter': 'customtkinter>=5.2.0'
    }

    for module, package in required_modules.items():
        try:
            if module == 'PIL':
                import PIL
                print(f"[OK] Pillow 已安装")
            else:
                __import__(module)
                print(f"[OK] {module} 已安装")
        except ImportError:
            print(f"[FAIL] {module} 未安装")
            print(f"正在安装 {package}...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
                print(f"[OK] {package} 安装成功")
            except subprocess.CalledProcessError:
                print(f"[FAIL] {package} 安装失败")
                return False

    return True

def clean_build_dirs():
    """清理之前的构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"[OK] 清理目录: {dir_name}")

def create_spec_file():
    """创建优化的spec文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# 添加隐藏导入
hiddenimports = [
    'requests',
    'requests.adapters',
    'requests.auth',
    'requests.cookies',
    'requests.models',
    'requests.sessions',
    'requests.utils',
    'playwright',
    'playwright.sync_api',
    'playwright._impl',
    'playwright._impl._connection',
    'playwright._impl._page',
    'playwright._impl._browser_context',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'tkinter.scrolledtext',
    'customtkinter',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL._tkinter_finder',
    'json',
    'threading',
    'queue',
    'logging',
    'pathlib',
    'datetime',
    'time',
    'random',
    'typing',
    'base64',
]

# 数据文件
datas = [
    ('whisk_core_v2.py', '.'),
    ('whisk_window_queue.py', '.'),      # V2.1新增: 窗口队列管理
    ('whisk_queue_dialog.py', '.'),      # 批量任务对话框
    ('config_gui_v2.json', '.'),
    ('gui', 'gui'),                      # V3新增: GUI主题模块
]

# 如果存在downloads目录，也包含进去
if Path('downloads').exists():
    datas.append(('downloads', 'downloads'))

a = Analysis(
    ['whisk_gui_v3.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='跨海帆-Imager_V3',
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
    icon=None,
)
'''

    with open('whisk_v3.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("[OK] 创建spec文件")

def build_exe():
    """构建exe文件"""
    print("\n开始构建exe文件...")

    # 清理旧文件
    clean_build_dirs()

    # 创建spec文件
    create_spec_file()

    # 运行PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        '--log-level=INFO',
        'whisk_v3.spec'
    ]

    print(f"执行命令: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        print("\n[OK] 构建成功！")

        # 检查输出文件
        exe_path = Path('dist/跨海帆-Imager_V3.exe')
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"生成的文件: {exe_path}")
            print(f"文件大小: {size_mb:.2f} MB")

            # 复制配置文件到dist目录
            config_file = Path('config_gui_v2.json')
            if config_file.exists():
                shutil.copy2(config_file, 'dist/')
                print("[OK] 复制配置文件到dist目录")

            return True
        else:
            print("[FAIL] 未找到生成的exe文件")
            return False

    except subprocess.CalledProcessError as e:
        print(f"\n[FAIL] 构建失败: {e}")
        if e.stdout:
            print("标准输出:", e.stdout)
        if e.stderr:
            print("错误输出:", e.stderr)
        return False

def create_distribution_package():
    """创建完整的分发包"""
    exe_name = '跨海帆-Imager_V3.exe'
    if not Path(f'dist/{exe_name}').exists():
        print("[FAIL] exe文件不存在，无法创建分发包")
        return False

    print("\n创建分发包...")

    # 创建分发目录
    dist_dir = Path('跨海帆-Imager_V3_Distribution')
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()

    # 复制exe文件
    shutil.copy2(f'dist/{exe_name}', dist_dir / exe_name)

    # 复制配置文件
    config_file = Path('config_gui_v2.json')
    if config_file.exists():
        shutil.copy2(config_file, dist_dir / 'config_gui_v2.json')

    # 创建启动脚本
    start_script = dist_dir / '启动跨海帆.bat'
    start_script.write_text(f'''@echo off
chcp 65001 >nul
echo 启动 跨海帆-Imager V3...
echo.
"{exe_name}"
if errorlevel 1 (
    echo.
    echo 程序异常退出，请检查错误信息
    pause
)
''', encoding='utf-8')

    print(f"[OK] 创建分发包: {dist_dir}")
    return True

def create_readme():
    """创建使用说明"""
    readme_content = '''# 跨海帆-Imager V3 Windows版使用说明

## 📋 系统要求
- Windows 10/11 64位系统
- 比特浏览器 (BitBrowser) 已安装并运行
- 网络连接正常，能访问Google服务

## 🚀 快速开始

### 1. 准备工作
1. **启动比特浏览器**
   - 打开BitBrowser应用
   - 创建并启动一个或多个浏览器实例

2. **访问Whisk网站**
   - 在浏览器中访问 Google Whisk AI
   - 确保页面正常加载

### 2. 运行程序
1. **启动应用**
   - 双击 `跨海帆-Imager_V3.exe` 或运行 `启动跨海帆.bat`
   - 等待程序界面加载

2. **配置参数**
   - 点击"刷新浏览器列表"获取可用窗口
   - 选择要使用的浏览器窗口
   - 输入图像生成提示词
   - 选择纵横比（1:1, 4:3, 3:4, 16:9, 9:16）
   - 设置生成数量

3. **开始生成**
   - 点击"添加任务"开始自动化流程
   - 程序会自动生成并下载图片到downloads目录

## ⚠️ 重要注意事项

### 首次运行
- Windows可能显示"Windows已保护你的电脑"警告
- 点击"更多信息" → "仍要运行"即可

### 防病毒软件
- 某些防病毒软件可能误报
- 请将程序添加到白名单或信任列表

### 网络要求
- 需要稳定的网络连接
- 确保能正常访问Google服务
- 建议使用科学上网工具

## 🔧 故障排除

### 常见问题

**Q: 程序无法启动？**
A:
- 检查是否安装了 Visual C++ Redistributable
- 确保Windows系统为64位
- 尝试以管理员身份运行

**Q: 找不到浏览器窗口？**
A:
- 确保比特浏览器正在运行
- 检查是否已打开浏览器窗口
- 点击"刷新浏览器列表"重新扫描

**Q: 图片下载失败？**
A:
- 检查网络连接状态
- 确保能访问Google服务
- 检查downloads目录权限

**Q: 程序运行缓慢？**
A:
- 减少并发任务数量
- 关闭不必要的浏览器窗口
- 确保系统内存充足

### 错误日志
程序运行时会生成错误日志文件：
- `error_log.txt` - 详细错误信息
- 请在报告问题时提供此文件

## 📁 文件说明

```
跨海帆-Imager_V3_Distribution/
├── 跨海帆-Imager_V3.exe    # 主程序
├── config_gui_v2.json      # 配置文件
├── 启动跨海帆.bat           # 启动脚本
├── README.md               # 本说明文件
└── downloads/              # 图片下载目录（自动创建）
```

## 🔄 更新说明

### V3版本特性（最新）
- **现代化界面** - 基于CustomTkinter的全新界面设计
- **深海探索风主题** - 专业、可靠、创新的视觉体验
- **标签页架构** - 多功能区域清晰分离
- **窗口队列功能** - 同一窗口任务自动排队执行
- **任务组管理** - 相关任务统一文件夹归档
- **批量任务支持** - 一次添加多个任务
- **三种归档模式** - 独立/套图/每次询问
- **浏览器连接复用** - 提升执行效率
- **动态任务添加** - 运行中随时添加新任务

### V2版本特性
- 支持新版Whisk界面
- 支持5种纵横比选择
- 优化下载逻辑
- 改进错误处理

## 📞 技术支持

如遇到问题：
1. 查看错误日志文件
2. 截图保存错误界面
3. 记录操作步骤
4. 联系技术支持

---
**版本**: V3.0
**构建日期**: {build_date}
**支持系统**: Windows 10/11 x64
**界面框架**: CustomTkinter 5.2+
'''.format(build_date=datetime.now().strftime('%Y-%m-%d'))

    # 写入分发目录
    dist_dir = Path('跨海帆-Imager_V3_Distribution')
    if dist_dir.exists():
        readme_path = dist_dir / 'README.md'
        readme_path.write_text(readme_content, encoding='utf-8')
        print("[OK] 创建使用说明文件")

    # 也在当前目录创建一份
    with open('README_V3_Windows.md', 'w', encoding='utf-8') as f:
        f.write(readme_content)

def main():
    """主函数"""
    print("=" * 60)
    print("跨海帆-Imager V3 Windows EXE 打包工具")
    print("=" * 60)

    # 检查环境
    print("\n步骤 1/4: 检查构建环境")
    if not check_requirements():
        print("\n[ERROR] 环境检查失败，请先安装必要的依赖")
        input("按回车键退出...")
        return

    # 构建exe
    print("\n步骤 2/4: 构建EXE文件")
    if not build_exe():
        print("\n[ERROR] EXE构建失败，请检查错误信息")
        input("按回车键退出...")
        return

    # 创建分发包
    print("\n步骤 3/4: 创建分发包")
    if not create_distribution_package():
        print("\n[ERROR] 分发包创建失败")
        input("按回车键退出...")
        return

    # 创建说明文档
    print("\n步骤 4/4: 创建使用说明")
    create_readme()

    print("\n" + "=" * 60)
    print("[SUCCESS] 打包完成！")
    print("=" * 60)
    print(f"输出目录: 跨海帆-Imager_V3_Distribution/")
    print(f"主程序: 跨海帆-Imager_V3_Distribution/跨海帆-Imager_V3.exe")
    print(f"使用说明: 跨海帆-Imager_V3_Distribution/README.md")
    print("=" * 60)

    # 显示文件大小信息
    exe_path = Path('跨海帆-Imager_V3_Distribution/跨海帆-Imager_V3.exe')
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"文件大小: {size_mb:.2f} MB")

    print("\n[SUCCESS] 现在您可以将 跨海帆-Imager_V3_Distribution 文件夹复制到其他Windows电脑上使用！")
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()
