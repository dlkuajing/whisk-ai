#!/usr/bin/env python3
"""
Google Whisk AI 图像生成自动化 - GUI版本 V2
支持新版 Whisk 页面和5种纵横比
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import json
import time
from pathlib import Path
from datetime import datetime
import queue
import logging

# 导入新的核心自动化类
from whisk_core_v2 import WhiskAutomationCoreV2

class WhiskGUIV2:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Whisk AI 图像生成自动化 V2")
        self.root.geometry("1100x750")
        
        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 线程管理
        self.threads = {}  # 存储活动线程
        self.thread_counter = 0
        self.max_concurrent_tasks = 3  # 最大并发任务数
        
        # 消息队列用于线程间通信
        self.message_queue = queue.Queue()
        
        # 加载配置
        self.load_config()
        
        # 创建界面
        self.create_widgets()
        
        # 启动消息处理
        self.process_messages()
        
        # 加载比特浏览器列表
        self.load_browser_list()
    
    def load_config(self):
        """加载配置文件"""
        self.config_file = Path("config_gui_v2.json")
        self.config = {
            "last_browser": "",
            "last_prompt": "A beautiful landscape with mountains and lakes",
            "last_ratio": "1:1",
            "last_count": 4,
            "save_directory": "./downloads",
            "use_enhanced_download": True,
            "create_task_folders": True,
            "min_delay": 5,
            "max_delay": 8,
            "max_concurrent": 2
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
            except:
                pass
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def create_widgets(self):
        """创建GUI组件"""
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 标题
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="Google Whisk AI 图像生成自动化", 
                               font=("Arial", 18, "bold"))
        title_label.pack(side=tk.LEFT)
        
        version_label = ttk.Label(title_frame, text="V2.0 - 支持5种纵横比", 
                                 font=("Arial", 10), foreground="gray")
        version_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 左侧配置面板
        config_frame = ttk.LabelFrame(main_frame, text="任务配置", padding="10")
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        row = 0
        
        # 任务名称
        ttk.Label(config_frame, text="任务名称:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.task_name_var = tk.StringVar(value=f"任务_{datetime.now().strftime('%H%M%S')}")
        ttk.Entry(config_frame, textvariable=self.task_name_var, width=25).grid(
            row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        row += 1
        
        # 比特浏览器选择
        ttk.Label(config_frame, text="比特浏览器:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.browser_var = tk.StringVar()
        self.browser_combo = ttk.Combobox(config_frame, textvariable=self.browser_var, 
                                         width=22, state="readonly")
        self.browser_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 存储浏览器ID映射
        self.browser_id_map = {}
        
        # 刷新浏览器列表按钮
        refresh_btn = ttk.Button(config_frame, text="刷新", command=self.load_browser_list, width=6)
        refresh_btn.grid(row=row, column=2, padx=(5, 0), pady=2)
        row += 1
        
        # 提示词
        ttk.Label(config_frame, text="提示词:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=2)
        self.prompt_text = scrolledtext.ScrolledText(config_frame, height=4, width=30, wrap=tk.WORD)
        self.prompt_text.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        self.prompt_text.insert(tk.END, self.config.get('last_prompt', ''))
        row += 1
        
        # 纵横比选择（新增5种选项）
        ttk.Label(config_frame, text="纵横比:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.ratio_var = tk.StringVar(value=self.config.get('last_ratio', '1:1'))
        ratio_frame = ttk.Frame(config_frame)
        ratio_frame.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        
        # 创建纵横比选项
        ratios = [
            ("1:1", "正方形"),
            ("4:3", "横向"),
            ("3:4", "纵向"),
            ("16:9", "宽屏"),
            ("9:16", "竖屏")
        ]
        
        ratio_combo = ttk.Combobox(ratio_frame, textvariable=self.ratio_var, 
                                  values=[r[0] for r in ratios], 
                                  state="readonly", width=8)
        ratio_combo.pack(side=tk.LEFT)
        
        self.ratio_desc_label = ttk.Label(ratio_frame, text="正方形", foreground="gray")
        self.ratio_desc_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # 更新描述
        def update_ratio_desc(*args):
            ratio = self.ratio_var.get()
            for r, desc in ratios:
                if r == ratio:
                    self.ratio_desc_label.config(text=desc)
                    break
        
        self.ratio_var.trace('w', update_ratio_desc)
        row += 1
        
        # 生成数量
        ttk.Label(config_frame, text="生成数量:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.count_var = tk.IntVar(value=self.config.get('last_count', 4))
        count_spinbox = ttk.Spinbox(config_frame, from_=1, to=50, textvariable=self.count_var, width=23)
        count_spinbox.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        row += 1
        
        # 保存目录
        ttk.Label(config_frame, text="保存目录:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.save_dir_var = tk.StringVar(value=self.config.get('save_directory', './downloads'))
        save_dir_entry = ttk.Entry(config_frame, textvariable=self.save_dir_var, width=18)
        save_dir_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        
        browse_btn = ttk.Button(config_frame, text="浏览", command=self.browse_directory, width=6)
        browse_btn.grid(row=row, column=2, padx=(5, 0), pady=2)
        row += 1
        
        # 分隔线
        ttk.Separator(config_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # 高级选项
        advanced_label = ttk.Label(config_frame, text="高级选项", font=("Arial", 10, "bold"))
        advanced_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        row += 1
        
        # 为每个任务创建独立目录
        self.create_folders_var = tk.BooleanVar(value=self.config.get('create_task_folders', True))
        create_folders_cb = ttk.Checkbutton(config_frame, text="为每个任务创建独立目录", 
                                           variable=self.create_folders_var)
        create_folders_cb.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=2)
        row += 1
        
        # 使用增强版下载机制
        self.enhanced_download_var = tk.BooleanVar(value=self.config.get('use_enhanced_download', True))
        enhanced_cb = ttk.Checkbutton(config_frame, text="使用增强版下载机制 (推荐)", 
                                     variable=self.enhanced_download_var)
        enhanced_cb.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=2)
        row += 1
        
        # 延时设置
        delay_frame = ttk.Frame(config_frame)
        delay_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(delay_frame, text="延时范围:").pack(side=tk.LEFT)
        self.min_delay_var = tk.IntVar(value=self.config.get('min_delay', 5))
        min_delay_spin = ttk.Spinbox(delay_frame, from_=1, to=30, textvariable=self.min_delay_var, 
                                    width=5)
        min_delay_spin.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(delay_frame, text="~").pack(side=tk.LEFT, padx=5)
        
        self.max_delay_var = tk.IntVar(value=self.config.get('max_delay', 8))
        max_delay_spin = ttk.Spinbox(delay_frame, from_=1, to=30, textvariable=self.max_delay_var, 
                                    width=5)
        max_delay_spin.pack(side=tk.LEFT)
        
        ttk.Label(delay_frame, text="秒").pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # 最大并发任务数
        concur_frame = ttk.Frame(config_frame)
        concur_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(concur_frame, text="最大并发任务:").pack(side=tk.LEFT)
        self.max_concurrent_var = tk.IntVar(value=self.config.get('max_concurrent', 2))
        concur_spin = ttk.Spinbox(concur_frame, from_=1, to=5, textvariable=self.max_concurrent_var, 
                                 width=5)
        concur_spin.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(concur_frame, text="个").pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # 操作按钮
        button_frame = ttk.Frame(config_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=(20, 0))
        
        self.add_task_btn = ttk.Button(button_frame, text="添加任务", command=self.add_task,
                                      style="Accent.TButton")
        self.add_task_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_all_btn = ttk.Button(button_frame, text="停止所有", command=self.stop_all_tasks,
                                      state=tk.DISABLED)
        self.stop_all_btn.pack(side=tk.LEFT, padx=5)
        
        # 右侧任务列表和日志
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.rowconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        
        # 任务列表
        task_label_frame = ttk.Frame(right_frame)
        task_label_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(task_label_frame, text="任务列表", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        self.running_label = ttk.Label(task_label_frame, text="运行中: 0", foreground="green")
        self.running_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 任务表格
        task_frame = ttk.Frame(right_frame)
        task_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 10))
        
        # 创建Treeview
        columns = ('浏览器', '提示词', '比例', '数量', '进度', '状态')
        self.task_tree = ttk.Treeview(task_frame, columns=columns, show='tree headings', height=6)
        
        # 设置列
        self.task_tree.column('#0', width=60, minwidth=60)
        self.task_tree.column('浏览器', width=80, minwidth=80)
        self.task_tree.column('提示词', width=150, minwidth=100)
        self.task_tree.column('比例', width=60, minwidth=60)
        self.task_tree.column('数量', width=50, minwidth=50)
        self.task_tree.column('进度', width=80, minwidth=80)
        self.task_tree.column('状态', width=80, minwidth=80)
        
        # 设置标题
        self.task_tree.heading('#0', text='ID')
        for col in columns:
            self.task_tree.heading(col, text=col)
        
        # 滚动条
        task_scrollbar = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=task_scrollbar.set)
        
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右键菜单
        self.create_context_menu()
        self.task_tree.bind("<Button-3>", self.show_context_menu)
        
        # 日志区域
        log_label = ttk.Label(right_frame, text="运行日志", font=("Arial", 12, "bold"))
        log_label.grid(row=2, column=0, sticky=tk.W)
        
        log_frame = ttk.Frame(right_frame)
        log_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 日志标签样式
        self.log_text.tag_config("info", foreground="black")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("error", foreground="red")
        
        # 状态栏
        self.create_status_bar()
    
    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="查看详情", command=self.view_task_details)
        self.context_menu.add_command(label="停止任务", command=self.stop_selected_task)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="清除已完成", command=self.clear_completed_tasks)
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        try:
            self.task_tree.selection_set(self.task_tree.identify_row(event.y))
            self.context_menu.post(event.x_root, event.y_root)
        except:
            pass
    
    def create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 下载模式指示
        self.download_mode_label = ttk.Label(status_frame, text="下载模式: ")
        self.download_mode_label.pack(side=tk.LEFT, padx=10)
        
        self.download_mode_value = ttk.Label(status_frame, text="增强版", foreground="green")
        self.download_mode_value.pack(side=tk.LEFT)
        
        # 并发数指示
        self.concurrent_label = ttk.Label(status_frame, text="最大并发: ")
        self.concurrent_label.pack(side=tk.LEFT, padx=(20, 0))
        
        self.concurrent_value = ttk.Label(status_frame, text="2")
        self.concurrent_value.pack(side=tk.LEFT)
        
        # 版本信息
        version_label = ttk.Label(status_frame, text="V2.0 - 适配新版 Whisk 页面", 
                                 foreground="gray")
        version_label.pack(side=tk.RIGHT, padx=10)
    
    def load_browser_list(self):
        """加载比特浏览器列表"""
        try:
            import requests
            
            # 使用正确的API参数
            payload = {"page": 0, "pageSize": 200}
            self.log_message("正在获取浏览器列表...", "info")
            
            response = requests.post("http://127.0.0.1:54345/browser/list", json=payload, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'data' in data:
                    browsers = []
                    self.browser_id_map = {}
                    data_obj = data['data']
                    
                    if isinstance(data_obj, dict) and 'list' in data_obj:
                        browser_list = data_obj['list']
                        
                        running_count = 0
                        for browser in browser_list:
                            if isinstance(browser, dict):
                                name = browser.get('name', '未命名')
                                browser_id = browser.get('id', '')
                                status_code = browser.get('status', 0)
                                
                                if status_code == 1:
                                    running_count += 1
                                    status = "运行中"
                                    display_name = f"{name} ({status})"
                                    browsers.append(display_name)
                                    self.browser_id_map[display_name] = browser_id
                        
                        self.log_message(f"找到 {running_count} 个运行中的浏览器", "success")
                        
                        if browsers:
                            current_value = self.browser_var.get()
                            self.browser_combo['values'] = browsers
                            
                            if current_value in browsers:
                                self.browser_var.set(current_value)
                            else:
                                self.browser_var.set(browsers[0])
                        else:
                            self.browser_combo['values'] = []
                            self.browser_var.set("")
                            self.log_message("没有找到运行中的浏览器", "warning")
                    else:
                        self.log_message("API响应格式错误", "error")
                else:
                    self.log_message("获取浏览器列表失败", "error")
            else:
                self.log_message(f"API请求失败: {response.status_code}", "error")
                
        except requests.exceptions.ConnectionError:
            self.log_message("无法连接到比特浏览器，请确保其正在运行", "error")
        except Exception as e:
            self.log_message(f"加载浏览器列表时出错: {str(e)}", "error")
    
    def browse_directory(self):
        """浏览目录"""
        directory = filedialog.askdirectory(initialdir=self.save_dir_var.get())
        if directory:
            self.save_dir_var.set(directory)
    
    def clean_task_name(self, name):
        """清理任务名称，移除特殊字符"""
        import re
        # 只保留字母、数字、中文、下划线和横线
        cleaned = re.sub(r'[^\w\u4e00-\u9fff\-_]', '', name)
        return cleaned or "task"
    
    def add_task(self):
        """添加新任务"""
        # 检查并发限制
        running_count = sum(1 for t in self.threads.values() if t['status'] == 'running')
        max_concurrent = self.max_concurrent_var.get()
        
        if running_count >= max_concurrent:
            messagebox.showwarning("并发限制", 
                                 f"当前已有 {running_count} 个任务在运行，\n"
                                 f"最大并发数为 {max_concurrent}。\n"
                                 f"请等待部分任务完成后再添加。")
            return
        
        # 验证输入
        browser_display = self.browser_var.get()
        if not browser_display:
            messagebox.showerror("错误", "请选择一个比特浏览器")
            return
        
        browser_id = self.browser_id_map.get(browser_display)
        if not browser_id:
            messagebox.showerror("错误", "无效的浏览器选择")
            return
        
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        if not prompt:
            messagebox.showerror("错误", "请输入提示词")
            return
        
        # 保存配置
        self.config['last_browser'] = browser_display
        self.config['last_prompt'] = prompt
        self.config['last_ratio'] = self.ratio_var.get()
        self.config['last_count'] = self.count_var.get()
        self.config['save_directory'] = self.save_dir_var.get()
        self.config['use_enhanced_download'] = self.enhanced_download_var.get()
        self.config['create_task_folders'] = self.create_folders_var.get()
        self.config['min_delay'] = self.min_delay_var.get()
        self.config['max_delay'] = self.max_delay_var.get()
        self.config['max_concurrent'] = self.max_concurrent_var.get()
        self.save_config()
        
        # 更新状态栏
        self.download_mode_value.config(
            text="增强版" if self.enhanced_download_var.get() else "标准版",
            foreground="green" if self.enhanced_download_var.get() else "blue"
        )
        self.concurrent_value.config(text=str(max_concurrent))
        
        # 创建保存目录
        save_dir = Path(self.save_dir_var.get())
        if self.create_folders_var.get():
            # 清理任务名称
            clean_name = self.clean_task_name(self.task_name_var.get())
            task_dir = save_dir / f"{clean_name}_{datetime.now().strftime('%H%M%S')}"
        else:
            task_dir = save_dir
        
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建任务
        self.thread_counter += 1
        task_id = f"T{self.thread_counter:03d}"
        
        # 添加到任务列表
        tree_item = self.task_tree.insert('', 'end', text=task_id, values=(
            browser_display.split(' ')[0],  # 只显示浏览器名称
            prompt[:30] + "..." if len(prompt) > 30 else prompt,
            self.ratio_var.get(),
            self.count_var.get(),
            "0/{}".format(self.count_var.get()),
            "准备中"
        ))
        
        # 创建线程
        thread = threading.Thread(
            target=self.run_task,
            args=(task_id, browser_id, prompt, self.count_var.get(), 
                 self.ratio_var.get(), str(task_dir), tree_item),
            daemon=True
        )
        
        # 存储线程信息
        self.threads[task_id] = {
            'thread': thread,
            'tree_item': tree_item,
            'status': 'running',
            'browser': browser_display,
            'prompt': prompt,
            'ratio': self.ratio_var.get(),
            'count': self.count_var.get(),
            'save_dir': str(task_dir)
        }
        
        # 启动线程
        thread.start()
        
        # 更新UI
        self.update_running_count()
        self.stop_all_btn.config(state=tk.NORMAL)
        
        # 更新任务名称
        self.task_name_var.set(f"任务_{datetime.now().strftime('%H%M%S')}")
        
        self.log_message(f"任务 {task_id} 已启动", "success")
    
    def run_task(self, task_id, browser_id, prompt, count, ratio, save_dir, tree_item):
        """在单独线程中运行任务"""
        def message_callback(msg):
            self.message_queue.put(('log', task_id, msg))
        
        def progress_callback(current, total):
            self.message_queue.put(('progress', task_id, (current, total)))
        
        try:
            # 更新状态
            self.message_queue.put(('status', task_id, "连接中"))
            
            # 创建自动化实例
            automation = WhiskAutomationCoreV2(
                browser_id=browser_id,
                save_directory=save_dir,
                message_callback=message_callback,
                progress_callback=progress_callback,
                use_enhanced_download=self.enhanced_download_var.get()
            )
            
            # 运行自动化
            automation.run(
                prompt=prompt,
                count=count,
                aspect_ratio=ratio,
                min_delay=self.min_delay_var.get(),
                max_delay=self.max_delay_var.get()
            )
            
            # 任务完成
            self.message_queue.put(('status', task_id, "已完成"))
            self.threads[task_id]['status'] = 'completed'
            
        except Exception as e:
            self.message_queue.put(('error', task_id, str(e)))
            self.message_queue.put(('status', task_id, "失败"))
            self.threads[task_id]['status'] = 'failed'
        
        finally:
            self.message_queue.put(('done', task_id, None))
    
    def process_messages(self):
        """处理来自线程的消息"""
        try:
            while True:
                msg_type, task_id, data = self.message_queue.get_nowait()
                
                if msg_type == 'log':
                    self.log_message(f"[{task_id}] {data}", "info")
                
                elif msg_type == 'progress':
                    current, total = data
                    if task_id in self.threads:
                        tree_item = self.threads[task_id]['tree_item']
                        self.task_tree.set(tree_item, 'progress', f"{current}/{total}")
                
                elif msg_type == 'status':
                    if task_id in self.threads:
                        tree_item = self.threads[task_id]['tree_item']
                        self.task_tree.set(tree_item, 'status', data)
                
                elif msg_type == 'error':
                    self.log_message(f"[{task_id}] 错误: {data}", "error")
                
                elif msg_type == 'done':
                    self.update_running_count()
                    if not any(t['status'] == 'running' for t in self.threads.values()):
                        self.stop_all_btn.config(state=tk.DISABLED)
                
        except queue.Empty:
            pass
        
        # 继续处理
        self.root.after(100, self.process_messages)
    
    def log_message(self, message, tag="info"):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
    
    def update_running_count(self):
        """更新运行中任务计数"""
        running_count = sum(1 for t in self.threads.values() if t['status'] == 'running')
        self.running_label.config(text=f"运行中: {running_count}")
    
    def view_task_details(self):
        """查看任务详情"""
        selection = self.task_tree.selection()
        if not selection:
            return
        
        task_id = self.task_tree.item(selection[0])['text']
        if task_id in self.threads:
            task_info = self.threads[task_id]
            
            details = f"""任务ID: {task_id}
浏览器: {task_info['browser']}
提示词: {task_info['prompt']}
纵横比: {task_info['ratio']}
数量: {task_info['count']}
状态: {task_info['status']}
保存目录: {task_info['save_dir']}"""
            
            messagebox.showinfo("任务详情", details)
    
    def stop_selected_task(self):
        """停止选中的任务"""
        selection = self.task_tree.selection()
        if not selection:
            return
        
        task_id = self.task_tree.item(selection[0])['text']
        if task_id in self.threads and self.threads[task_id]['status'] == 'running':
            # 这里需要实现停止机制
            self.log_message(f"正在停止任务 {task_id}...", "warning")
            self.threads[task_id]['status'] = 'stopped'
            self.task_tree.set(self.threads[task_id]['tree_item'], 'status', "已停止")
            self.update_running_count()
    
    def stop_all_tasks(self):
        """停止所有任务"""
        if messagebox.askyesno("确认", "确定要停止所有运行中的任务吗？"):
            for task_id, task_info in self.threads.items():
                if task_info['status'] == 'running':
                    task_info['status'] = 'stopped'
                    self.task_tree.set(task_info['tree_item'], 'status', "已停止")
            
            self.log_message("已停止所有任务", "warning")
            self.update_running_count()
            self.stop_all_btn.config(state=tk.DISABLED)
    
    def clear_completed_tasks(self):
        """清除已完成的任务"""
        to_remove = []
        for task_id, task_info in self.threads.items():
            if task_info['status'] in ['completed', 'failed', 'stopped']:
                self.task_tree.delete(task_info['tree_item'])
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.threads[task_id]
        
        self.log_message(f"已清除 {len(to_remove)} 个任务", "info")

def main():
    root = tk.Tk()
    app = WhiskGUIV2(root)
    root.mainloop()

if __name__ == "__main__":
    main()