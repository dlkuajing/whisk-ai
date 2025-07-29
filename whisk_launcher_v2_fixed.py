#!/usr/bin/env python3
"""
Whisk V2 启动器
用于exe打包，解决路径和导入问题
"""

import sys
import os
import traceback

def setup_environment():
    """设置运行环境"""
    # 获取程序运行路径
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        application_path = os.path.dirname(sys.executable)
    else:
        # 如果是Python脚本
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    # 将路径添加到Python路径
    sys.path.insert(0, application_path)
    
    # 设置工作目录
    os.chdir(application_path)
    
    return application_path

def show_error(title, message):
    """显示错误对话框"""
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except:
        # 如果GUI也失败，使用控制台
        print(f"错误: {title}")
        print(message)
        input("按回车键退出...")

def main():
    """主函数"""
    try:
        # 设置环境
        app_path = setup_environment()
        
        # 尝试导入主程序
        try:
            # 首先尝试作为模块导入
            from whisk_gui_v2 import WhiskGUIV2
        except ImportError:
            # 如果失败，尝试直接执行文件
            import importlib.util
            gui_path = os.path.join(app_path, 'whisk_gui_v2.py')
            
            if not os.path.exists(gui_path):
                raise FileNotFoundError(f"找不到主程序文件: {gui_path}")
            
            spec = importlib.util.spec_from_file_location("whisk_gui_v2", gui_path)
            whisk_gui_v2 = importlib.util.module_from_spec(spec)
            sys.modules["whisk_gui_v2"] = whisk_gui_v2
            spec.loader.exec_module(whisk_gui_v2)
            WhiskGUIV2 = whisk_gui_v2.WhiskGUIV2
        
        # 同样处理核心模块
        try:
            import whisk_core_v2
        except ImportError:
            import importlib.util
            core_path = os.path.join(app_path, 'whisk_core_v2.py')
            
            if os.path.exists(core_path):
                spec = importlib.util.spec_from_file_location("whisk_core_v2", core_path)
                whisk_core_v2 = importlib.util.module_from_spec(spec)
                sys.modules["whisk_core_v2"] = whisk_core_v2
                spec.loader.exec_module(whisk_core_v2)
        
        # 创建tkinter根窗口并运行应用
        import tkinter as tk
        root = tk.Tk()
        app = WhiskGUIV2(root)
        root.mainloop()
        
    except Exception as e:
        # 捕获所有异常并显示
        error_msg = f"程序启动失败：\n\n{str(e)}\n\n详细信息：\n{traceback.format_exc()}"
        
        # 记录错误日志
        try:
            with open('error_log.txt', 'w', encoding='utf-8') as f:
                f.write(error_msg)
                f.write(f"\n\n运行路径: {os.getcwd()}")
                f.write(f"\nPython路径: {sys.path}")
        except:
            pass
        
        # 显示错误
        show_error("启动错误", error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main()