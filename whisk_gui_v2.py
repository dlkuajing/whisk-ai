#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
# 导入窗口队列管理器
from whisk_window_queue import WindowQueueManager

class WhiskGUIV2:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Whisk AI 图像生成自动化 V2")
        self.root.geometry("1100x750")
        
        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 线程管理（保留用于向后兼容）
        self.threads = {}  # 存储活动线程
        self.thread_counter = 0
        self.max_concurrent_tasks = 15  # 最大并发任务数

        # 消息队列用于线程间通信
        self.message_queue = queue.Queue()

        # 窗口队列管理器（新功能）
        self.window_queue_manager = None  # 延迟初始化
        self.queue_task_items = {}  # 窗口队列任务的TreeView项映射 {task_id: tree_item}
        
        # 加载配置
        self.load_config()
        
        # 创建界面
        self.create_widgets()

        # 初始化窗口队列管理器
        self.init_window_queue_manager()

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
            "max_concurrent": 2,
            # 窗口队列相关配置
            "use_window_queue": False,  # 是否启用窗口队列模式
            "session_mode": "ask",  # 任务归档模式: ask/independent/always_session
            "idle_timeout": 300,  # 队列空闲超时（秒）
            "session_timeout": 600  # 任务组自动结束超时（秒）
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

    def init_window_queue_manager(self):
        """初始化窗口队列管理器"""
        queue_config = {
            'idle_timeout': self.config.get('idle_timeout', 300),
            'session_timeout': self.config.get('session_timeout', 600),
            'use_enhanced_download': self.config.get('use_enhanced_download', True),
            'min_delay': self.config.get('min_delay', 5),
            'max_delay': self.config.get('max_delay', 8)
        }

        self.window_queue_manager = WindowQueueManager(
            gui_callback=self.handle_queue_callback,
            config=queue_config
        )

    def handle_queue_callback(self, event_type: str, browser_id: str, data):
        """处理窗口队列的回调事件"""
        # 将队列事件转换为消息队列消息
        if event_type == 'task_added':
            self.message_queue.put(('log', browser_id, f"任务已添加到队列"))

        elif event_type == 'task_start':
            task_id = data.get('task_id', '')
            task_name = data.get('task_name', '未命名')
            self.message_queue.put(('log', browser_id, f"开始执行任务: {task_name}"))
            # 更新TreeView状态
            self.message_queue.put(('queue_task_status', task_id, ('进度', '执行中', '状态', '运行中')))

        elif event_type == 'task_complete':
            task_id = data.get('task_id', '')
            task_name = data.get('task_name', '未命名')
            self.message_queue.put(('log', browser_id, f"任务完成: {task_name}"))
            # 更新TreeView状态
            self.message_queue.put(('queue_task_status', task_id, ('进度', '已完成', '状态', '已完成')))

        elif event_type == 'task_failed':
            task_id = data.get('task_id', '')
            task_name = data.get('task_name', '未命名')
            self.message_queue.put(('log', browser_id, f"任务失败: {task_name}"))
            # 更新TreeView状态
            self.message_queue.put(('queue_task_status', task_id, ('进度', '失败', '状态', '失败')))

        elif event_type == 'task_error':
            self.message_queue.put(('log', browser_id, f"错误: {data}"))

        elif event_type == 'log':
            self.message_queue.put(('log', browser_id, data))

        elif event_type == 'task_progress':
            # 处理进度更新
            task = data['task']
            task_id = task.get('task_id', '')
            current = data['current']
            total = data['total']
            progress_type = data['progress_type']

            # 更新进度显示
            if progress_type == 'download':
                progress_text = f"下载:{current}/{total}"
            elif progress_type == 'generation':
                progress_text = f"生成:{current}/{total}"
            else:
                progress_text = f"{current}/{total}"

            self.message_queue.put(('queue_task_progress', task_id, progress_text))

        elif event_type == 'browser_connected':
            self.message_queue.put(('log', browser_id, "浏览器已连接"))

        elif event_type == 'worker_started':
            self.message_queue.put(('log', browser_id, "窗口队列工作线程已启动"))

        elif event_type == 'worker_stopped':
            self.message_queue.put(('log', browser_id, "窗口队列工作线程已停止"))

        elif event_type == 'idle_timeout':
            self.message_queue.put(('log', browser_id, "队列空闲超时，已断开连接"))

        elif event_type == 'session_created':
            session_name = data['session_name']
            self.message_queue.put(('log', browser_id, f"创建任务组: {session_name}"))

        elif event_type == 'session_closed':
            session_name = data['session_name']
            self.message_queue.put(('log', browser_id, f"结束任务组: {session_name}"))

        elif event_type == 'task_cancelled':
            task_id = data.get('task_id', '')
            task_name = data.get('task_name', '未命名')
            self.message_queue.put(('log', browser_id, f"任务已取消: {task_name}"))
            # 更新TreeView状态
            self.message_queue.put(('queue_task_status', task_id, ('进度', '已取消', '状态', '已取消')))

        elif event_type == 'worker_start_failed':
            error_msg = data
            self.message_queue.put(('log', browser_id, f"❌ 浏览器连接失败（重试3次后仍失败）: {error_msg}"))

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

        # 启用窗口队列模式
        self.use_window_queue_var = tk.BooleanVar(value=self.config.get('use_window_queue', False))
        queue_cb = ttk.Checkbutton(config_frame, text="启用窗口队列模式（同窗口任务自动串行）",
                                   variable=self.use_window_queue_var,
                                   command=self.toggle_queue_options)
        queue_cb.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=2)
        row += 1

        # 任务归档模式（仅在启用窗口队列时显示）
        self.archive_frame = ttk.Frame(config_frame)
        self.archive_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2)

        ttk.Label(self.archive_frame, text="  归档模式:").pack(side=tk.LEFT)
        self.session_mode_var = tk.StringVar(value=self.config.get('session_mode', 'ask'))

        ttk.Radiobutton(self.archive_frame, text="每次询问", variable=self.session_mode_var,
                       value='ask').pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.archive_frame, text="总是独立", variable=self.session_mode_var,
                       value='independent').pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.archive_frame, text="总是套图", variable=self.session_mode_var,
                       value='always_session').pack(side=tk.LEFT, padx=5)

        row += 1

        # 初始状态
        self.toggle_queue_options()

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
        concur_spin = ttk.Spinbox(concur_frame, from_=1, to=15, textvariable=self.max_concurrent_var, 
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

        self.batch_task_btn = ttk.Button(button_frame, text="批量任务队列", command=self.open_batch_queue,
                                        style="Accent.TButton")
        self.batch_task_btn.pack(side=tk.LEFT, padx=5)

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
    
    def toggle_queue_options(self):
        """切换窗口队列选项的显示状态"""
        if self.use_window_queue_var.get():
            # 显示归档模式选项
            for widget in self.archive_frame.winfo_children():
                widget.configure(state=tk.NORMAL)
        else:
            # 隐藏归档模式选项
            for widget in self.archive_frame.winfo_children():
                widget.configure(state=tk.DISABLED)

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
        self.config['use_window_queue'] = self.use_window_queue_var.get()
        self.config['session_mode'] = self.session_mode_var.get()
        self.save_config()

        # 判断使用哪种模式
        if self.use_window_queue_var.get():
            # 窗口队列模式
            self.add_task_to_queue(browser_id, browser_display, prompt)
        else:
            # 传统独立任务模式
            self.add_independent_task(browser_id, browser_display, prompt)

    def add_task_to_queue(self, browser_id: str, browser_display: str, prompt: str):
        """添加任务到窗口队列（新模式）"""
        # 生成任务ID
        self.thread_counter += 1
        task_id = f"Q{self.thread_counter:03d}"

        # 准备任务参数
        task_params = {
            'task_id': task_id,  # 添加任务ID
            'task_name': self.task_name_var.get(),
            'prompt': prompt,
            'count': self.count_var.get(),
            'aspect_ratio': self.ratio_var.get(),
            'base_save_dir': self.save_dir_var.get()
        }

        # 确定归档模式
        session_mode = self.session_mode_var.get()
        session_name = None

        if session_mode == 'ask':
            # 询问用户选择归档方式
            window_queue = self.window_queue_manager.get_window_queue(browser_id)

            if window_queue and window_queue.current_session:
                # 有活跃任务组，询问是否加入
                choice = self.ask_session_choice(window_queue.current_session)
                if choice == 'join':
                    session_mode = 'join_current'
                elif choice == 'new':
                    session_mode = 'new_session'
                    session_name = self.ask_session_name()
                elif choice == 'independent':
                    session_mode = 'independent'
                else:
                    return  # 用户取消
            else:
                # 没有活跃任务组，询问创建新组还是独立
                choice = self.ask_first_task_choice()
                if choice == 'new_session':
                    session_mode = 'new_session'
                    session_name = self.ask_session_name()
                elif choice == 'independent':
                    session_mode = 'independent'
                else:
                    return
        elif session_mode == 'always_session':
            # 总是套图模式
            window_queue = self.window_queue_manager.get_window_queue(browser_id)
            if window_queue and window_queue.current_session:
                session_mode = 'join_current'
            else:
                session_mode = 'new_session'
                session_name = self.ask_session_name()
        # else: session_mode == 'independent', 保持不变

        # 在TreeView中创建任务项
        tree_item = self.task_tree.insert('', 'end', text=task_id, values=(
            browser_display.split(' ')[0],  # 只显示浏览器名称
            prompt[:30] + "..." if len(prompt) > 30 else prompt,
            self.ratio_var.get(),
            self.count_var.get(),
            "排队中",
            "等待中"
        ))

        # 保存TreeView项的映射
        self.queue_task_items[task_id] = {
            'tree_item': tree_item,
            'browser_id': browser_id,
            'browser_display': browser_display,
            'task_params': task_params
        }

        # 添加到窗口队列
        success = self.window_queue_manager.add_task_to_window(
            browser_id, browser_display, task_params, session_mode, session_name
        )

        if success:
            self.log_message(f"任务 {task_id} 已添加到窗口队列: {browser_display}", "success")

            # 启用停止按钮
            self.stop_all_btn.config(state=tk.NORMAL)
            self.update_running_count()

            # 更新任务名称为下一个
            self.task_name_var.set(f"任务_{datetime.now().strftime('%H%M%S')}")
        else:
            self.log_message(f"添加任务失败", "error")
            # 失败时删除TreeView项
            self.task_tree.delete(tree_item)
            del self.queue_task_items[task_id]

    def ask_session_choice(self, current_session):
        """询问用户是否加入现有任务组"""
        dialog = tk.Toplevel(self.root)
        dialog.title("任务归档方式")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

        result = tk.StringVar(value='join')

        # 提示信息
        info = current_session.get_info()
        message = f"该窗口有活跃的任务组：\n\n" \
                  f"任务组名称：{info['session_name']}\n" \
                  f"已有任务：{info['task_count']} 个\n\n" \
                  f"新任务如何归档？"

        ttk.Label(dialog, text=message, justify=tk.LEFT).pack(pady=20, padx=20)

        # 选择选项
        ttk.Radiobutton(dialog, text=f"加入当前任务组（推荐）", variable=result,
                       value='join').pack(anchor=tk.W, padx=40, pady=5)
        ttk.Radiobutton(dialog, text="创建新任务组", variable=result,
                       value='new').pack(anchor=tk.W, padx=40, pady=5)
        ttk.Radiobutton(dialog, text="独立文件夹", variable=result,
                       value='independent').pack(anchor=tk.W, padx=40, pady=5)

        # 按钮
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)

        def on_ok():
            dialog.result = result.get()
            dialog.destroy()

        def on_cancel():
            dialog.result = None
            dialog.destroy()

        ttk.Button(btn_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(dialog)
        return getattr(dialog, 'result', None)

    def ask_first_task_choice(self):
        """第一个任务时询问归档方式"""
        dialog = tk.Toplevel(self.root)
        dialog.title("任务归档方式")
        dialog.geometry("350x200")
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

        result = tk.StringVar(value='new_session')

        # 提示信息
        ttk.Label(dialog, text="这是该窗口的第一个任务\n请选择归档方式：").pack(pady=20)

        # 选择选项
        ttk.Radiobutton(dialog, text="创建新任务组（套图模式）", variable=result,
                       value='new_session').pack(anchor=tk.W, padx=40, pady=5)
        ttk.Radiobutton(dialog, text="独立文件夹", variable=result,
                       value='independent').pack(anchor=tk.W, padx=40, pady=5)

        # 按钮
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)

        def on_ok():
            dialog.result = result.get()
            dialog.destroy()

        def on_cancel():
            dialog.result = None
            dialog.destroy()

        ttk.Button(btn_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(dialog)
        return getattr(dialog, 'result', None)

    def ask_session_name(self):
        """询问任务组名称"""
        dialog = tk.Toplevel(self.root)
        dialog.title("任务组名称")
        dialog.geometry("350x150")
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f'+{x}+{y}')

        # 提示信息
        ttk.Label(dialog, text="请输入任务组名称：").pack(pady=20)

        # 输入框
        name_var = tk.StringVar(value=f"套图_{datetime.now().strftime('%H%M%S')}")
        entry = ttk.Entry(dialog, textvariable=name_var, width=30)
        entry.pack(pady=10)
        entry.select_range(0, tk.END)
        entry.focus()

        # 按钮
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)

        def on_ok():
            dialog.result = name_var.get().strip()
            if dialog.result:
                dialog.destroy()
            else:
                messagebox.showwarning("警告", "请输入任务组名称", parent=dialog)

        def on_cancel():
            dialog.result = None
            dialog.destroy()

        ttk.Button(btn_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=5)

        # 回车键确认
        entry.bind('<Return>', lambda e: on_ok())

        self.root.wait_window(dialog)
        return getattr(dialog, 'result', None)

    def add_independent_task(self, browser_id: str, browser_display: str, prompt: str):
        """添加独立任务（传统模式）"""
        # 检查并发限制
        running_count = sum(1 for t in self.threads.values() if t['status'] == 'running')
        max_concurrent = self.max_concurrent_var.get()

        if running_count >= max_concurrent:
            messagebox.showwarning("并发限制",
                                 f"当前已有 {running_count} 个任务在运行，\n"
                                 f"最大并发数为 {max_concurrent}。\n"
                                 f"请等待部分任务完成后再添加。")
            return
        
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
            "下载:0/{}".format(self.count_var.get() * 2),
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
        
        def progress_callback(current, total, progress_type='generation'):
            self.message_queue.put(('progress', task_id, (current, total, progress_type)))
        
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
            
            # 存储automation实例以便停止任务
            self.threads[task_id]['automation'] = automation
            
            # 运行自动化
            automation.run(
                prompt=prompt,
                count=count,
                aspect_ratio=ratio,
                min_delay=self.min_delay_var.get(),
                max_delay=self.max_delay_var.get()
            )
            
            # 任务完成
            if automation.is_task_stopped():
                self.message_queue.put(('status', task_id, "已停止"))
                self.threads[task_id]['status'] = 'stopped'
            else:
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
                    if len(data) == 3:
                        current, total, progress_type = data

                        if task_id in self.threads:
                            tree_item = self.threads[task_id]['tree_item']
                            if progress_type == 'queue':
                                # 显示队列进度
                                try:
                                    self.task_tree.set(tree_item, '进度', f"任务:{current}/{total}")
                                except:
                                    self.task_tree.set(tree_item, 4, f"任务:{current}/{total}")
                            elif progress_type == 'download':
                                # 显示下载进度
                                try:
                                    self.task_tree.set(tree_item, '进度', f"下载:{current}/{total}")
                                except:
                                    self.task_tree.set(tree_item, 4, f"下载:{current}/{total}")
                            else:
                                # 显示生成进度
                                try:
                                    self.task_tree.set(tree_item, '进度', f"生成:{current}/{total}")
                                except:
                                    self.task_tree.set(tree_item, 4, f"生成:{current}/{total}")
                    else:
                        # 兼容旧格式
                        current, total = data

                        if task_id in self.threads:
                            tree_item = self.threads[task_id]['tree_item']
                            try:
                                self.task_tree.set(tree_item, '进度', f"{current}/{total}")
                            except:
                                self.task_tree.set(tree_item, 4, f"{current}/{total}")
                
                elif msg_type == 'status':
                    if task_id in self.threads:
                        tree_item = self.threads[task_id]['tree_item']
                        try:
                            self.task_tree.set(tree_item, '状态', data)
                        except:
                            # 使用索引设置
                            self.task_tree.set(tree_item, 5, data)
                
                elif msg_type == 'error':
                    self.log_message(f"[{task_id}] 错误: {data}", "error")

                elif msg_type == 'queue_task_status':
                    # 窗口队列任务状态更新
                    if task_id in self.queue_task_items:
                        tree_item = self.queue_task_items[task_id]['tree_item']
                        # data 是一个元组: ('进度', value1, '状态', value2)
                        try:
                            self.task_tree.set(tree_item, data[0], data[1])
                            if len(data) > 2:
                                self.task_tree.set(tree_item, data[2], data[3])
                        except:
                            pass

                elif msg_type == 'queue_task_progress':
                    # 窗口队列任务进度更新
                    if task_id in self.queue_task_items:
                        tree_item = self.queue_task_items[task_id]['tree_item']
                        try:
                            self.task_tree.set(tree_item, '进度', data)
                        except:
                            pass

                elif msg_type == 'done':
                    self.update_running_count()

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
        """更新运行中任务计数（支持传统模式和窗口队列模式）"""
        # 统计传统模式运行中的任务
        running_count = sum(1 for t in self.threads.values() if t['status'] in ['running', 'stopping'])

        # 统计窗口队列中的任务
        queue_running_count = 0
        if self.window_queue_manager:
            all_status = self.window_queue_manager.get_all_status()
            for browser_id, status in all_status.items():
                # 统计正在运行的窗口数量
                if status['is_running']:
                    queue_running_count += 1
                # 加上队列中等待的任务数
                queue_running_count += status['queue_size']

        total_running = running_count + queue_running_count
        self.running_label.config(text=f"运行中: {total_running}")

        # 如果没有运行中的任务，禁用停止按钮
        if total_running == 0:
            self.stop_all_btn.config(state=tk.DISABLED)
        else:
            self.stop_all_btn.config(state=tk.NORMAL)
    
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
        """停止选中的任务（支持传统模式和窗口队列模式）"""
        selection = self.task_tree.selection()
        if not selection:
            return

        task_id = self.task_tree.item(selection[0])['text']

        # 传统模式任务
        if task_id in self.threads and self.threads[task_id]['status'] == 'running':
            # 实现真正的停止机制
            self.log_message(f"正在停止任务 {task_id}...", "warning")

            # 调用automation的停止方法
            if 'automation' in self.threads[task_id]:
                automation = self.threads[task_id]['automation']
                automation.stop_task()

            # 更新状态
            self.threads[task_id]['status'] = 'stopping'
            try:
                self.task_tree.set(self.threads[task_id]['tree_item'], '状态', "停止中")
            except:
                self.task_tree.set(self.threads[task_id]['tree_item'], 5, "停止中")
            self.update_running_count()

        # 窗口队列任务（新增）
        elif task_id in self.queue_task_items:
            self.log_message(f"正在取消任务 {task_id}...", "warning")
            task_info = self.queue_task_items[task_id]
            browser_id = task_info['browser_id']

            # 获取当前状态
            try:
                current_status = self.task_tree.set(task_info['tree_item'], '状态')
            except:
                current_status = "未知"

            # 调用窗口队列管理器取消任务
            if self.window_queue_manager:
                success = self.window_queue_manager.cancel_task_in_window(browser_id, task_id)
                if success:
                    # 乐观更新UI（worker会发送正式的cancelled回调）
                    if current_status in ['等待中', '排队中']:
                        # 等待中的任务，立即更新为已取消
                        try:
                            self.task_tree.set(task_info['tree_item'], '状态', "已取消")
                            self.task_tree.set(task_info['tree_item'], '进度', "已取消")
                        except:
                            pass
                    else:
                        # 运行中的任务，显示取消中
                        try:
                            self.task_tree.set(task_info['tree_item'], '状态', "取消中")
                        except:
                            pass

                    self.log_message(f"任务 {task_id} 取消请求已发送", "success")
                else:
                    self.log_message(f"任务 {task_id} 取消失败（可能已完成）", "warning")

            self.update_running_count()

        else:
            self.log_message(f"任务 {task_id} 未找到或已完成", "warning")
    
    def stop_all_tasks(self):
        """停止所有任务（传统模式 + 窗口队列模式）"""
        if messagebox.askyesno("确认", "确定要停止所有运行中的任务吗？"):
            # 停止传统模式任务
            traditional_stopped = 0
            for task_id, task_info in self.threads.items():
                if task_info['status'] == 'running':
                    # 调用automation的停止方法
                    if 'automation' in task_info:
                        automation = task_info['automation']
                        automation.stop_task()

                    task_info['status'] = 'stopping'
                    try:
                        self.task_tree.set(task_info['tree_item'], '状态', "停止中")
                    except:
                        self.task_tree.set(task_info['tree_item'], 5, "停止中")
                    traditional_stopped += 1

            # 停止窗口队列任务
            if self.window_queue_manager:
                self.window_queue_manager.stop_all()
                self.log_message("已发送停止信号给所有窗口队列", "warning")

            self.log_message(f"已发送停止信号给所有任务 (传统:{traditional_stopped}个)", "warning")
            self.update_running_count()
    
    def clear_completed_tasks(self):
        """清除已完成的任务（支持传统模式和窗口队列模式）"""
        to_remove_threads = []
        to_remove_queue = []

        # 清除传统模式任务
        for task_id, task_info in self.threads.items():
            if task_info['status'] in ['completed', 'failed', 'stopped']:
                self.task_tree.delete(task_info['tree_item'])
                to_remove_threads.append(task_id)

        # 清除窗口队列模式任务
        for task_id, task_item_info in self.queue_task_items.items():
            tree_item = task_item_info['tree_item']
            try:
                # 获取任务状态
                status = self.task_tree.set(tree_item, '状态')
                # 只清除真正结束的任务：已完成、失败、已停止、已取消
                if status in ['已完成', '失败', '已停止', '已取消']:
                    self.task_tree.delete(tree_item)
                    to_remove_queue.append(task_id)
            except Exception as e:
                # TreeView项可能已被删除或无效
                import logging
                logging.warning(f"清除任务 {task_id} 时出错: {e}")
                # 如果TreeView项不存在，也从字典中移除
                to_remove_queue.append(task_id)

        # 从字典中移除
        for task_id in to_remove_threads:
            del self.threads[task_id]

        for task_id in to_remove_queue:
            del self.queue_task_items[task_id]

        total_removed = len(to_remove_threads) + len(to_remove_queue)

        # 改进：更详细的用户反馈
        if total_removed > 0:
            self.log_message(
                f"已清除 {total_removed} 个任务 (传统:{len(to_remove_threads)}, 队列:{len(to_remove_queue)})",
                "info"
            )
        else:
            self.log_message("没有需要清除的任务", "info")

        self.update_running_count()

    def open_batch_queue(self):
        """打开批量任务队列对话框"""
        # 重新加载模块以确保获取最新版本
        import importlib
        import sys
        if 'whisk_queue_dialog' in sys.modules:
            importlib.reload(sys.modules['whisk_queue_dialog'])

        from whisk_queue_dialog import TaskQueueDialog

        # 创建对话框
        dialog = TaskQueueDialog(self.root, self.browser_id_map, self.config)
        self.root.wait_window(dialog.dialog)

        # 获取结果
        result = dialog.get_result()
        if result:
            # 执行批量任务
            self.execute_batch_queue(result)

    def execute_batch_queue(self, queue_info):
        """执行批量任务队列（使用窗口队列机制）"""
        browser_display = queue_info['browser']
        browser_id = queue_info['browser_id']
        task_queue = queue_info['task_queue']
        save_directory = queue_info['save_directory']
        create_folders = queue_info['create_folders']

        if not task_queue:
            messagebox.showwarning("警告", "任务队列为空")
            return

        # 询问任务组名称
        session_name = self.ask_session_name()
        if not session_name:
            return  # 用户取消

        # 批量添加所有任务到窗口队列
        first_task = True
        added_tasks = []

        for idx, task in enumerate(task_queue, 1):
            # 生成任务ID
            self.thread_counter += 1
            task_id = f"Q{self.thread_counter:03d}"

            # 准备任务参数
            task_params = {
                'task_id': task_id,  # 添加任务ID
                'task_name': task.get('task_name', f'任务{idx}'),
                'prompt': task['prompt'],
                'count': task['count'],
                'aspect_ratio': task['aspect_ratio'],
                'base_save_dir': save_directory
            }

            # 在TreeView中创建任务项
            tree_item = self.task_tree.insert('', 'end', text=task_id, values=(
                browser_display.split(' ')[0],
                task_params['prompt'][:30] + "..." if len(task_params['prompt']) > 30 else task_params['prompt'],
                task_params['aspect_ratio'],
                task_params['count'],
                "排队中",
                "等待中"
            ))

            # 保存TreeView项的映射
            self.queue_task_items[task_id] = {
                'tree_item': tree_item,
                'browser_id': browser_id,
                'browser_display': browser_display,
                'task_params': task_params
            }

            # 第一个任务创建新任务组，后续任务加入该组
            if first_task:
                session_mode = 'new_session'
                first_task = False
            else:
                session_mode = 'join_current'

            # 添加到窗口队列
            success = self.window_queue_manager.add_task_to_window(
                browser_id, browser_display, task_params, session_mode, session_name
            )

            if not success:
                self.log_message(f"添加任务 {task_params['task_name']} 失败", "error")
                # 删除失败的TreeView项
                self.task_tree.delete(tree_item)
                del self.queue_task_items[task_id]
                break
            else:
                added_tasks.append(task_id)

        if added_tasks:
            total_tasks = len(added_tasks)
            total_images = sum(task['count'] * 2 for task in task_queue[:len(added_tasks)])
            self.log_message(f"批量任务队列已创建: {session_name}", "success")
            self.log_message(f"共 {total_tasks} 个任务已添加，预计生成 {total_images} 张图片", "info")

    def run_batch_queue(self, task_id, browser_id, task_queue, save_dir, tree_item, create_folders):
        """在单独线程中运行批量任务队列"""
        def message_callback(msg):
            self.message_queue.put(('log', task_id, msg))

        def progress_callback(current, total, progress_type='generation'):
            self.message_queue.put(('progress', task_id, (current, total, progress_type)))

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

            # 存储automation实例以便停止任务
            self.threads[task_id]['automation'] = automation

            # 为队列中的每个任务创建子目录（如果需要）
            processed_queue = []
            base_dir = Path(save_dir)

            for idx, task in enumerate(task_queue, 1):
                task_copy = task.copy()

                # 如果需要为每个任务创建文件夹
                if create_folders:
                    task_name = task.get('task_name', f'task_{idx}')
                    # 清理任务名称
                    import re
                    clean_name = re.sub(r'[^\w\u4e00-\u9fff\-_]', '', task_name)
                    task_dir = base_dir / f"{idx:02d}_{clean_name}"
                    task_dir.mkdir(parents=True, exist_ok=True)

                    # 将保存目录添加到任务参数中
                    task_copy['save_directory'] = str(task_dir)
                else:
                    # 所有任务使用同一个目录
                    task_copy['save_directory'] = str(save_dir)

                processed_queue.append(task_copy)

            # 运行队列
            automation.run_queue(
                task_queue=processed_queue,
                min_delay=self.min_delay_var.get(),
                max_delay=self.max_delay_var.get()
            )

            # 任务完成
            if automation.is_task_stopped():
                self.message_queue.put(('status', task_id, "已停止"))
                self.threads[task_id]['status'] = 'stopped'
            else:
                self.message_queue.put(('status', task_id, "已完成"))
                self.threads[task_id]['status'] = 'completed'

        except Exception as e:
            self.message_queue.put(('error', task_id, str(e)))
            self.message_queue.put(('status', task_id, "失败"))
            self.threads[task_id]['status'] = 'failed'

        finally:
            self.message_queue.put(('done', task_id, None))

def main():
    root = tk.Tk()
    app = WhiskGUIV2(root)
    root.mainloop()

if __name__ == "__main__":
    main()