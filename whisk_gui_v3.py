#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨海帆-Imager V3 - AI 图像生成专业工具
基于CustomTkinter的现代化界面
支持标签页架构、窗口队列和批量任务
主题：深海探索风 - 专业、可靠、探索、创新
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import json
import time
from pathlib import Path
from datetime import datetime
import queue
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入主题配置
from gui.themes.colors import *

# 导入核心功能模块
from whisk_core_v2 import WhiskAutomationCoreV2
from whisk_window_queue import WindowQueueManager

# 设置CustomTkinter外观
ctk.set_appearance_mode("light")  # 可选: "light" 或 "dark"
ctk.set_default_color_theme("blue")  # 可选: "blue", "green", "dark-blue"


class WhiskGUIV3(ctk.CTk):
    """跨海帆-Imager V3 主窗口类 - 基于CustomTkinter"""

    def __init__(self):
        super().__init__()

        # 窗口基础设置
        self.title("跨海帆-Imager V3 - AI 图像生成专业工具")
        self.geometry("1200x800")
        self.minsize(900, 600)

        # 设置窗口图标（如果有的话）
        try:
            self.iconbitmap("icon.ico")
        except:
            pass

        # 线程管理（传统模式）
        self.threads = {}
        self.thread_counter = 0
        self.max_concurrent_tasks = 15

        # 消息队列用于线程间通信
        self.message_queue = queue.Queue()

        # 窗口队列管理器
        self.window_queue_manager = None
        self.queue_task_items = {}

        # 批量任务管理
        self.batch_tasks = []
        self.batch_queue_running = False  # 批量队列是否正在运行

        # 加载配置
        self.load_config()

        # 创建界面
        self.create_widgets()

        # 初始化窗口队列管理器
        self.init_window_queue_manager()

        # 启动消息处理
        self.process_messages()

        # 加载浏览器列表
        self.after(500, self.load_browser_list)

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
            "use_window_queue": False,
            "session_mode": "ask",
            "idle_timeout": 300,
            "session_timeout": 600,
            "appearance_mode": "light",  # 新增：界面主题
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
            except:
                pass

        # 应用主题设置
        ctk.set_appearance_mode(self.config.get("appearance_mode", "light"))

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

    def create_widgets(self):
        """创建GUI组件 - 使用CustomTkinter"""

        # 配置网格权重
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # =================================================================
        # 顶部标题栏
        # =================================================================
        self.create_header()

        # =================================================================
        # 主内容区 - 使用标签页架构
        # =================================================================
        self.create_main_content()

        # =================================================================
        # 底部状态栏
        # =================================================================
        self.create_status_bar()

    def create_header(self):
        """创建顶部标题栏"""
        header_frame = ctk.CTkFrame(self, fg_color=PRIMARY_COLOR, height=80)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_propagate(False)

        # 标题
        title_label = ctk.CTkLabel(
            header_frame,
            text="⛵ 跨海帆-Imager V3",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        )
        title_label.pack(side="left", padx=20, pady=20)

        # 副标题
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="AI 图像生成专业工具 | 探索无限创意",
            font=ctk.CTkFont(size=12),
            text_color="white"
        )
        subtitle_label.pack(side="left", padx=(0, 20), pady=20)

        # 右侧工具按钮区
        tools_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        tools_frame.pack(side="right", padx=20, pady=20)

        # 主题切换按钮
        self.theme_btn = ctk.CTkButton(
            tools_frame,
            text="🌙 深色",
            width=80,
            height=32,
            fg_color="transparent",
            hover_color=PRIMARY_HOVER,
            border_width=1,
            border_color="white",
            command=self.toggle_theme
        )
        self.theme_btn.pack(side="left", padx=5)

        # 设置按钮
        settings_btn = ctk.CTkButton(
            tools_frame,
            text="⚙️ 设置",
            width=80,
            height=32,
            fg_color="transparent",
            hover_color=PRIMARY_HOVER,
            border_width=1,
            border_color="white",
            command=self.open_settings
        )
        settings_btn.pack(side="left", padx=5)

        # 帮助按钮
        help_btn = ctk.CTkButton(
            tools_frame,
            text="❓ 帮助",
            width=80,
            height=32,
            fg_color="transparent",
            hover_color=PRIMARY_HOVER,
            border_width=1,
            border_color="white",
            command=self.open_help
        )
        help_btn.pack(side="left", padx=5)

    def create_main_content(self):
        """创建主内容区 - 标签页架构"""
        # 主容器
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=1)

        # 创建标签视图
        self.tabview = ctk.CTkTabview(main_container, height=700)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        # 添加两个标签页（窗口队列已整合到快速任务中）
        self.tab_quick = self.tabview.add("⚡ 快速任务")
        self.tab_batch = self.tabview.add("📋 批量任务")

        # 配置每个标签页的网格
        for tab in [self.tab_quick, self.tab_batch]:
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=0)  # 左侧配置区
            tab.grid_columnconfigure(1, weight=1)  # 右侧任务区

        # 创建各个标签页的内容
        self.create_quick_task_tab()
        self.create_batch_task_tab()

    def create_quick_task_tab(self):
        """创建快速任务标签页"""
        # 配置网格权重 - 左侧固定宽度，右侧自适应
        self.tab_quick.grid_columnconfigure(0, weight=0, minsize=520)
        self.tab_quick.grid_columnconfigure(1, weight=1)
        self.tab_quick.grid_rowconfigure(0, weight=1)

        # 左侧配置面板
        left_frame = ctk.CTkFrame(self.tab_quick, width=520)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        left_frame.grid_propagate(False)

        # 创建滚动框架
        scroll_frame = ctk.CTkScrollableFrame(left_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 💡 快速开始标题
        quick_label = ctk.CTkLabel(
            scroll_frame,
            text="💡 快速开始",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        quick_label.pack(anchor="w", pady=(0, 15))

        # 任务名称
        ctk.CTkLabel(scroll_frame, text="任务名称:").pack(anchor="w", pady=(5, 0))
        self.task_name_var = tk.StringVar(value=f"任务_{datetime.now().strftime('%H%M%S')}")
        self.task_name_entry = ctk.CTkEntry(
            scroll_frame,
            textvariable=self.task_name_var,
            height=36
        )
        self.task_name_entry.pack(fill="x", pady=(5, 10))

        # 浏览器选择
        browser_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        browser_frame.pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(browser_frame, text="浏览器:").pack(anchor="w")

        browser_select_frame = ctk.CTkFrame(browser_frame, fg_color="transparent")
        browser_select_frame.pack(fill="x", pady=(5, 0))

        self.browser_var = tk.StringVar()
        self.browser_combo = ctk.CTkComboBox(
            browser_select_frame,
            variable=self.browser_var,
            values=[],
            state="readonly",
            height=36
        )
        self.browser_combo.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # 存储浏览器ID映射
        self.browser_id_map = {}

        # 刷新按钮
        refresh_btn = ctk.CTkButton(
            browser_select_frame,
            text="🔄",
            width=40,
            height=36,
            command=self.load_browser_list
        )
        refresh_btn.pack(side="left")

        # 提示词输入
        ctk.CTkLabel(scroll_frame, text="提示词:").pack(anchor="w", pady=(5, 0))
        self.prompt_textbox = ctk.CTkTextbox(
            scroll_frame,
            height=120,
            wrap="word"
        )
        self.prompt_textbox.pack(fill="x", pady=(5, 10))
        self.prompt_textbox.insert("1.0", self.config.get('last_prompt', ''))

        # 纵横比选择 - 图形化按钮组
        ctk.CTkLabel(scroll_frame, text="纵横比:").pack(anchor="w", pady=(5, 0))
        self.create_ratio_selector(scroll_frame)

        # 生成数量
        ctk.CTkLabel(scroll_frame, text="生成数量 (轮数，每轮2张):").pack(anchor="w", pady=(5, 0))
        self.count_var = tk.IntVar(value=self.config.get('last_count', 4))

        # 数量控制框架（滑块+输入框）
        count_control_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        count_control_frame.pack(fill="x", pady=(5, 0))

        # 滑块
        count_slider = ctk.CTkSlider(
            count_control_frame,
            from_=1,
            to=50,
            variable=self.count_var,
            number_of_steps=49
        )
        count_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # 手动输入框
        self.count_entry = ctk.CTkEntry(
            count_control_frame,
            width=60,
            textvariable=self.count_var,
            justify="center"
        )
        self.count_entry.pack(side="left", padx=(0, 10))

        # 数量显示
        self.count_label = ctk.CTkLabel(
            count_control_frame,
            text=f"{self.count_var.get()} 轮 ({self.count_var.get() * 2} 张)",
            font=ctk.CTkFont(size=12),
            width=100
        )
        self.count_label.pack(side="left")

        # 更新数量显示和验证输入
        def update_count_label(*args):
            try:
                count = self.count_var.get()
                # 验证范围
                if count < 1:
                    self.count_var.set(1)
                    count = 1
                elif count > 50:
                    self.count_var.set(50)
                    count = 50
                self.count_label.configure(text=f"{count} 轮 ({count * 2} 张)")
            except:
                self.count_var.set(4)

        self.count_var.trace('w', update_count_label)

        # 保存目录
        ctk.CTkLabel(scroll_frame, text="保存目录:").pack(anchor="w", pady=(5, 0))
        save_dir_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        save_dir_frame.pack(fill="x", pady=(5, 10))

        self.save_dir_var = tk.StringVar(value=self.config.get('save_directory', './downloads'))
        save_dir_entry = ctk.CTkEntry(
            save_dir_frame,
            textvariable=self.save_dir_var,
            height=36
        )
        save_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        browse_btn = ctk.CTkButton(
            save_dir_frame,
            text="📁",
            width=40,
            height=36,
            command=self.browse_directory
        )
        browse_btn.pack(side="left")

        # 分隔线
        separator = ctk.CTkFrame(scroll_frame, height=2, fg_color=BORDER_LIGHT)
        separator.pack(fill="x", pady=15)

        # 高级选项（折叠面板）
        self.create_advanced_options(scroll_frame)

        # 执行模式切换（窗口队列）
        self.create_execution_mode_section(scroll_frame, context="quick")

        # 添加任务按钮（使用辅助色 - 海洋青）
        add_task_btn = ctk.CTkButton(
            scroll_frame,
            text="➕ 添加任务",
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=SECONDARY_COLOR,
            hover_color=SECONDARY_HOVER,
            text_color="#FFFFFF",
            command=self.add_task
        )
        add_task_btn.pack(fill="x", pady=(20, 10))

        # 右侧任务管理区
        self.create_task_management_panel(self.tab_quick)

    def create_ratio_selector(self, parent):
        """创建图形化纵横比选择器（网格布局2行）"""
        ratio_frame = ctk.CTkFrame(parent, fg_color="transparent")
        ratio_frame.pack(fill="x", pady=(5, 10))

        self.ratio_var = tk.StringVar(value=self.config.get('last_ratio', '1:1'))
        self.ratio_buttons = {}

        ratios = [
            ("1:1", "▢", "正方形"),
            ("4:3", "▬", "横向"),
            ("3:4", "▮", "纵向"),
            ("16:9", "▬▬", "宽屏"),
            ("9:16", "▮▮", "竖屏")
        ]

        # 配置网格列权重（3列）
        for col in range(3):
            ratio_frame.grid_columnconfigure(col, weight=1)

        # 使用网格布局：第一行3个，第二行2个
        for idx, (ratio, icon, desc) in enumerate(ratios):
            # 计算行列位置
            row = idx // 3  # 前3个在第0行，后2个在第1行
            col = idx % 3   # 列位置0,1,2

            btn_frame = ctk.CTkFrame(ratio_frame, fg_color="transparent")
            btn_frame.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")

            def make_ratio_command(r):
                return lambda: self.select_ratio(r)

            btn = ctk.CTkButton(
                btn_frame,
                text=f"{icon}\n{ratio}",
                height=60,
                fg_color=PRIMARY_COLOR if ratio == self.ratio_var.get() else ADAPTIVE_BG_SECONDARY,
                hover_color=PRIMARY_HOVER,
                text_color="white" if ratio == self.ratio_var.get() else ADAPTIVE_TEXT_PRIMARY,
                command=make_ratio_command(ratio)
            )
            btn.pack(fill="both", expand=True)

            # 描述文字
            desc_label = ctk.CTkLabel(
                btn_frame,
                text=desc,
                font=ctk.CTkFont(size=10),
                text_color=ADAPTIVE_TEXT_SECONDARY
            )
            desc_label.pack(pady=(2, 0))

            self.ratio_buttons[ratio] = btn

    def select_ratio(self, ratio):
        """选择纵横比"""
        self.ratio_var.set(ratio)
        # 更新按钮样式
        for r, btn in self.ratio_buttons.items():
            if r == ratio:
                btn.configure(fg_color=PRIMARY_COLOR, text_color="white")
            else:
                btn.configure(fg_color=ADAPTIVE_BG_SECONDARY, text_color=ADAPTIVE_TEXT_PRIMARY)

    def create_advanced_options(self, parent):
        """创建折叠式高级选项面板"""
        # 高级选项标题（可点击展开/折叠）
        self.advanced_expanded = tk.BooleanVar(value=False)

        advanced_header = ctk.CTkFrame(parent, fg_color="transparent")
        advanced_header.pack(fill="x", pady=(5, 0))

        self.advanced_toggle_btn = ctk.CTkButton(
            advanced_header,
            text="▶ 高级选项",
            fg_color="transparent",
            hover_color=ADAPTIVE_BG_HOVER,
            text_color=ADAPTIVE_TEXT_SECONDARY,
            anchor="w",
            command=self.toggle_advanced_options
        )
        self.advanced_toggle_btn.pack(fill="x")

        # 高级选项内容（默认隐藏）
        self.advanced_frame = ctk.CTkFrame(parent, fg_color=ADAPTIVE_BG_SECONDARY)

        # 为每个任务创建独立目录
        self.create_folders_var = tk.BooleanVar(value=self.config.get('create_task_folders', True))
        create_folders_cb = ctk.CTkCheckBox(
            self.advanced_frame,
            text="为每个任务创建独立目录",
            variable=self.create_folders_var
        )
        create_folders_cb.pack(anchor="w", padx=15, pady=(10, 5))

        # 使用增强版下载机制
        self.enhanced_download_var = tk.BooleanVar(value=self.config.get('use_enhanced_download', True))
        enhanced_cb = ctk.CTkCheckBox(
            self.advanced_frame,
            text="使用增强版下载机制 (推荐)",
            variable=self.enhanced_download_var
        )
        enhanced_cb.pack(anchor="w", padx=15, pady=5)

        # 延时设置
        delay_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        delay_frame.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(delay_frame, text="延时范围 (秒):").pack(side="left")

        self.min_delay_var = tk.IntVar(value=self.config.get('min_delay', 5))
        min_delay_entry = ctk.CTkEntry(delay_frame, width=50, textvariable=self.min_delay_var)
        min_delay_entry.pack(side="left", padx=(10, 5))

        ctk.CTkLabel(delay_frame, text="~").pack(side="left", padx=5)

        self.max_delay_var = tk.IntVar(value=self.config.get('max_delay', 8))
        max_delay_entry = ctk.CTkEntry(delay_frame, width=50, textvariable=self.max_delay_var)
        max_delay_entry.pack(side="left", padx=5)

        # 最大并发任务数
        concur_frame = ctk.CTkFrame(self.advanced_frame, fg_color="transparent")
        concur_frame.pack(fill="x", padx=15, pady=(5, 10))

        ctk.CTkLabel(concur_frame, text="最大并发任务:").pack(side="left")

        self.max_concurrent_var = tk.IntVar(value=self.config.get('max_concurrent', 2))
        concur_entry = ctk.CTkEntry(concur_frame, width=50, textvariable=self.max_concurrent_var)
        concur_entry.pack(side="left", padx=(10, 5))

        ctk.CTkLabel(concur_frame, text="个").pack(side="left")

    def toggle_advanced_options(self):
        """切换高级选项的展开/折叠状态"""
        if self.advanced_expanded.get():
            # 折叠
            self.advanced_frame.pack_forget()
            self.advanced_toggle_btn.configure(text="▶ 高级选项")
            self.advanced_expanded.set(False)
        else:
            # 展开
            self.advanced_frame.pack(fill="x", pady=(5, 10))
            self.advanced_toggle_btn.configure(text="▼ 高级选项")
            self.advanced_expanded.set(True)

    def create_task_management_panel(self, parent):
        """创建任务管理面板（右侧 - 双面板容器）"""
        # 创建两个面板：任务列表面板和队列状态面板
        # 通过grid的show/hide来切换显示

        # 面板1：任务列表面板（传统模式）
        self.quick_task_list_panel = self.create_task_list_panel_for_quick(parent)

        # 面板2：队列状态面板（队列模式）
        self.quick_queue_status_panel = self.create_queue_status_panel_for_quick(parent)

        # 初始显示任务列表面板
        self.quick_current_panel = "task_list"
        self.quick_task_list_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.quick_queue_status_panel.grid_forget()

    def create_task_list_panel_for_quick(self, parent):
        """创建任务列表面板（快速任务 - 传统模式）"""
        panel = ctk.CTkFrame(parent)
        panel.grid_rowconfigure(1, weight=3)
        panel.grid_rowconfigure(3, weight=2)
        panel.grid_columnconfigure(0, weight=1)

        # 任务列表标题栏
        task_header = ctk.CTkFrame(panel, fg_color=ADAPTIVE_BG_SECONDARY, height=50)
        task_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        task_header.grid_propagate(False)

        ctk.CTkLabel(
            task_header,
            text="📋 任务管理",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=15, pady=10)

        self.running_label = ctk.CTkLabel(
            task_header,
            text="运行中: 0",
            font=ctk.CTkFont(size=12),
            text_color=SUCCESS_COLOR
        )
        self.running_label.pack(side="right", padx=15, pady=10)

        # 任务列表区域
        task_list_frame = ctk.CTkFrame(panel)
        task_list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        task_list_frame.grid_rowconfigure(0, weight=1)
        task_list_frame.grid_columnconfigure(0, weight=1)

        # 创建Treeview
        tree_container = ctk.CTkFrame(task_list_frame, fg_color="white")
        tree_container.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ('浏览器', '提示词', '比例', '数量', '进度', '状态')
        self.task_tree = tk.ttk.Treeview(
            tree_container,
            columns=columns,
            show='tree headings',
            height=10
        )

        # 设置列
        self.task_tree.column('#0', width=60, minwidth=60)
        self.task_tree.column('浏览器', width=80, minwidth=80)
        self.task_tree.column('提示词', width=180, minwidth=100)
        self.task_tree.column('比例', width=60, minwidth=60)
        self.task_tree.column('数量', width=50, minwidth=50)
        self.task_tree.column('进度', width=100, minwidth=80)
        self.task_tree.column('状态', width=100, minwidth=80)

        # 设置标题
        self.task_tree.heading('#0', text='ID')
        for col in columns:
            self.task_tree.heading(col, text=col)

        # 配置Treeview样式
        style = tk.ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                       background="white",
                       foreground=ADAPTIVE_TEXT_PRIMARY,
                       rowheight=30,
                       fieldbackground="white",
                       font=('Arial', 10))
        style.map('Treeview', background=[('selected', PRIMARY_COLOR)])

        # 滚动条
        task_scrollbar = tk.ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=task_scrollbar.set)

        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 任务控制按钮
        task_control_frame = ctk.CTkFrame(panel, fg_color="transparent", height=50)
        task_control_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        task_control_frame.grid_propagate(False)

        self.stop_all_btn = ctk.CTkButton(
            task_control_frame,
            text="⏹️ 停止所有",
            fg_color=ERROR_COLOR,
            hover_color=ERROR_HOVER,
            text_color="#FFFFFF",
            command=self.stop_all_tasks,
            state="disabled"
        )
        self.stop_all_btn.pack(side="left", padx=5, pady=10)

        clear_btn = ctk.CTkButton(
            task_control_frame,
            text="🗑️ 清除已完成",
            fg_color=WARNING_COLOR,
            hover_color=WARNING_HOVER,
            text_color="#FFFFFF",
            command=self.clear_completed_tasks
        )
        clear_btn.pack(side="left", padx=5, pady=10)

        # 日志区域标题
        log_header = ctk.CTkFrame(panel, fg_color=ADAPTIVE_BG_SECONDARY, height=40)
        log_header.grid(row=3, column=0, sticky="new", padx=10, pady=(10, 5))
        log_header.grid_propagate(False)

        ctk.CTkLabel(
            log_header,
            text="📝 运行日志",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=15, pady=8)

        # 日志区域
        log_frame = ctk.CTkFrame(panel)
        log_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        # 使用CTkTextbox作为日志显示
        self.log_textbox = ctk.CTkTextbox(
            log_frame,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=10)
        )
        self.log_textbox.pack(fill="both", expand=True, padx=5, pady=5)

        return panel

    def create_queue_status_panel_for_quick(self, parent):
        """创建队列状态面板（快速任务 - 队列模式）"""
        panel = ctk.CTkFrame(parent, fg_color="transparent")

        # 标题
        status_label = ctk.CTkLabel(
            panel,
            text="📊 窗口队列状态",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=QUEUE_COLOR
        )
        status_label.pack(pady=(10, 10))

        # 队列容器
        queue_container = ctk.CTkFrame(panel, fg_color=ADAPTIVE_BG_SECONDARY)
        queue_container.pack(fill="both", expand=True, padx=10)

        # 队列列表标题
        queue_header = ctk.CTkLabel(
            queue_container,
            text="当前窗口队列",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        queue_header.pack(pady=10)

        # 队列信息显示区域
        self.quick_queue_status_text = ctk.CTkTextbox(
            queue_container,
            height=500,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=ADAPTIVE_BG_PRIMARY,
            wrap="word"
        )
        self.quick_queue_status_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 初始提示
        initial_text = """
暂无队列任务

💡 使用说明：
1. 勾选"启用窗口队列模式"
2. 选择浏览器和配置
3. 选择归档模式
4. 点击"添加任务"

窗口队列特点：
✅ 同一窗口任务串行执行
✅ 浏览器连接复用，效率更高
✅ 支持套图归档
✅ 任务间状态隔离
"""
        self.quick_queue_status_text.insert("1.0", initial_text)
        self.quick_queue_status_text.configure(state="disabled")

        # 刷新按钮
        refresh_btn = ctk.CTkButton(
            queue_container,
            text="🔄 刷新队列状态",
            command=self.refresh_queue_status_quick,
            fg_color=QUEUE_COLOR,
            hover_color=self.adjust_color(QUEUE_COLOR, 0.8),
            height=36
        )
        refresh_btn.pack(pady=(0, 10), padx=10, fill="x")

        return panel

    def refresh_queue_status_quick(self):
        """刷新快速任务的队列状态显示"""
        try:
            self.quick_queue_status_text.configure(state="normal")
            self.quick_queue_status_text.delete("1.0", "end")

            # 获取当前选择的浏览器
            browser_display = self.browser_var.get()
            if not browser_display or browser_display not in self.browser_id_map:
                self.quick_queue_status_text.insert("1.0", "⚠️ 请先选择浏览器")
                self.quick_queue_status_text.configure(state="disabled")
                return

            browser_id = self.browser_id_map[browser_display]

            # 从窗口队列管理器获取状态
            if hasattr(self, 'window_queue_manager'):
                queue = self.window_queue_manager.get_window_queue(browser_id)
                if queue:
                    status = queue.get_status()

                    # 格式化显示
                    status_text = f"""
🌐 浏览器: {browser_display.split(' ')[0]}
📊 队列状态: {'运行中' if status['is_running'] else '空闲'}
📝 待处理任务: {status['queue_size']}
✅ 已完成任务: {status['completed_count']}

"""
                    if status['current_task']:
                        task = status['current_task']
                        status_text += f"""
🔄 当前任务:
   任务名: {task.get('task_name', 'N/A')}
   提示词: {task.get('prompt', 'N/A')[:50]}...
   进度: 执行中

"""

                    if status['current_session']:
                        session = status['current_session']
                        status_text += f"""
📁 当前任务组:
   组名: {session.get('session_name', 'N/A')}
   包含任务: {session.get('task_count', 0)}
   空闲时间: {session.get('idle_time', 0):.1f}秒

"""

                    self.quick_queue_status_text.insert("1.0", status_text)
                else:
                    self.quick_queue_status_text.insert("1.0", f"""
🌐 浏览器: {browser_display.split(' ')[0]}
📊 队列状态: 未初始化

💡 提示: 添加第一个任务后队列将自动创建
""")
            else:
                self.quick_queue_status_text.insert("1.0", "❌ 窗口队列管理器未初始化")

        except Exception as e:
            self.quick_queue_status_text.insert("1.0", f"❌ 获取队列状态失败: {str(e)}")
        finally:
            self.quick_queue_status_text.configure(state="disabled")

    def create_batch_task_tab(self):
        """创建批量任务标签页 - 完整实现"""
        # 配置网格权重 - 左侧固定宽度，右侧自适应
        self.tab_batch.grid_rowconfigure(0, weight=1)
        self.tab_batch.grid_columnconfigure(0, weight=0, minsize=520)
        self.tab_batch.grid_columnconfigure(1, weight=1)

        # ============== 左侧：批量导入区域 ==============
        left_panel = ctk.CTkFrame(self.tab_batch, width=520, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
        left_panel.grid_propagate(False)

        # 滚动框
        scroll_frame = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 标题
        header_label = ctk.CTkLabel(
            scroll_frame,
            text="📋 批量任务导入",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=PRIMARY_COLOR
        )
        header_label.pack(anchor="w", pady=(0, 10))

        # 说明卡片
        info_card = ctk.CTkFrame(scroll_frame, fg_color=ADAPTIVE_BG_SECONDARY, corner_radius=8)
        info_card.pack(fill="x", pady=(0, 15))

        info_text = ctk.CTkLabel(
            info_card,
            text="💡 每行输入一个提示词，快速生成批量任务\n"
                 "   所有任务将使用相同的浏览器和配置",
            font=ctk.CTkFont(size=12),
            text_color=ADAPTIVE_TEXT_SECONDARY,
            justify="left"
        )
        info_text.pack(padx=15, pady=10, anchor="w")

        # -------- 批量提示词输入 --------
        prompt_label = ctk.CTkLabel(
            scroll_frame,
            text="批量提示词（每行一个）:",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        prompt_label.pack(anchor="w", pady=(5, 5))

        self.batch_prompt_text = ctk.CTkTextbox(
            scroll_frame,
            height=180,
            wrap="word",
            font=ctk.CTkFont(size=12)
        )
        self.batch_prompt_text.pack(fill="x", pady=(0, 10))

        # 占位提示
        placeholder = "示例：\nA beautiful sunset over mountains\nA cute cat playing with yarn\nModern architecture design"
        self.batch_prompt_text.insert("1.0", placeholder)
        self.batch_prompt_text.bind("<FocusIn>", lambda e: self.clear_batch_placeholder())

        # -------- 统一设置区 --------
        settings_card = ctk.CTkFrame(scroll_frame, fg_color=ADAPTIVE_BG_SECONDARY, corner_radius=8)
        settings_card.pack(fill="x", pady=(10, 15))

        settings_title = ctk.CTkLabel(
            settings_card,
            text="⚙️ 统一配置",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        settings_title.pack(anchor="w", padx=15, pady=(12, 10))

        # 浏览器选择
        browser_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
        browser_frame.pack(fill="x", padx=15, pady=(0, 8))

        ctk.CTkLabel(
            browser_frame,
            text="浏览器:",
            width=80,
            anchor="w"
        ).pack(side="left")

        self.batch_browser_var = ctk.StringVar(value="")
        self.batch_browser_combo = ctk.CTkComboBox(
            browser_frame,
            variable=self.batch_browser_var,
            values=[],
            width=200,
            state="readonly"
        )
        self.batch_browser_combo.pack(side="left", padx=(0, 5))

        refresh_batch_btn = ctk.CTkButton(
            browser_frame,
            text="🔄",
            width=30,
            command=self.refresh_batch_browser_list,
            fg_color=PRIMARY_COLOR,
            hover_color=self.adjust_color(PRIMARY_COLOR, 0.8)
        )
        refresh_batch_btn.pack(side="left")

        # 纵横比选择
        ratio_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
        ratio_frame.pack(fill="x", padx=15, pady=(0, 8))

        ctk.CTkLabel(
            ratio_frame,
            text="纵横比:",
            width=80,
            anchor="w"
        ).pack(side="left")

        self.batch_ratio_var = ctk.StringVar(value="1:1")
        ratio_options = ["1:1", "4:3", "3:4", "16:9", "9:16"]
        batch_ratio_combo = ctk.CTkComboBox(
            ratio_frame,
            variable=self.batch_ratio_var,
            values=ratio_options,
            width=200,
            state="readonly"
        )
        batch_ratio_combo.pack(side="left")

        # 生成轮数
        count_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
        count_frame.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(
            count_frame,
            text="生成轮数:",
            width=80,
            anchor="w"
        ).pack(side="left")

        self.batch_count_var = ctk.IntVar(value=2)

        # 滑块
        batch_count_slider = ctk.CTkSlider(
            count_frame,
            from_=1,
            to=50,
            number_of_steps=49,
            variable=self.batch_count_var,
            width=120
        )
        batch_count_slider.pack(side="left", padx=(0, 10))

        # 手动输入框
        self.batch_count_entry = ctk.CTkEntry(
            count_frame,
            width=60,
            textvariable=self.batch_count_var,
            justify="center"
        )
        self.batch_count_entry.pack(side="left", padx=(0, 5))

        # 单位标签
        self.batch_count_label = ctk.CTkLabel(
            count_frame,
            text="轮",
            width=30
        )
        self.batch_count_label.pack(side="left")

        # 输入框验证：确保输入值在1-50之间
        def validate_batch_count(*args):
            try:
                value = self.batch_count_var.get()
                if value < 1:
                    self.batch_count_var.set(1)
                elif value > 50:
                    self.batch_count_var.set(50)
            except:
                self.batch_count_var.set(2)

        self.batch_count_var.trace_add('write', validate_batch_count)

        # -------- 执行模式选择区（批量任务） --------
        execution_mode_frame = self.create_execution_mode_section(scroll_frame, context="batch")
        execution_mode_frame.pack(fill="x", pady=(15, 10))

        # 保存目录
        save_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        save_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            save_frame,
            text="保存目录:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", pady=(5, 5))

        dir_input_frame = ctk.CTkFrame(save_frame, fg_color="transparent")
        dir_input_frame.pack(fill="x")

        self.batch_save_dir_var = ctk.StringVar(value=self.config.get('save_directory', './downloads'))
        batch_dir_entry = ctk.CTkEntry(
            dir_input_frame,
            textvariable=self.batch_save_dir_var,
            height=36
        )
        batch_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        browse_batch_dir_btn = ctk.CTkButton(
            dir_input_frame,
            text="📁 浏览",
            width=80,
            command=self.browse_batch_directory,
            fg_color=ADAPTIVE_BG_SECONDARY,
            text_color=ADAPTIVE_TEXT_PRIMARY
        )
        browse_batch_dir_btn.pack(side="left")

        # 生成批量任务按钮（使用强调色 - 航海金）
        generate_batch_btn = ctk.CTkButton(
            scroll_frame,
            text="📋 生成批量任务",
            command=self.generate_batch_tasks,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color="#FFFFFF"
        )
        generate_batch_btn.pack(fill="x", pady=(5, 10))

        # 继续添加任务按钮（使用辅助色 - 海洋青）
        self.continue_add_batch_btn = ctk.CTkButton(
            scroll_frame,
            text="➕ 继续添加任务",
            command=self.continue_add_batch_tasks,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=SECONDARY_COLOR,
            hover_color=SECONDARY_HOVER,
            text_color="#FFFFFF",
            state="disabled"  # 初始禁用，队列运行后启用
        )
        self.continue_add_batch_btn.pack(fill="x", pady=(0, 10))

        # ============== 右侧：队列预览和管理 ==============
        self.create_batch_queue_panel(self.tab_batch)

    def create_status_bar(self):
        """创建底部状态栏"""
        status_frame = ctk.CTkFrame(self, fg_color=ADAPTIVE_BG_SECONDARY, height=40)
        status_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        status_frame.grid_propagate(False)

        # 左侧状态信息
        left_status = ctk.CTkFrame(status_frame, fg_color="transparent")
        left_status.pack(side="left", padx=15, pady=8)

        self.download_mode_label = ctk.CTkLabel(
            left_status,
            text="下载模式: 增强版",
            font=ctk.CTkFont(size=11),
            text_color=SUCCESS_COLOR
        )
        self.download_mode_label.pack(side="left", padx=(0, 15))

        self.concurrent_label = ctk.CTkLabel(
            left_status,
            text="最大并发: 2",
            font=ctk.CTkFont(size=11),
            text_color=ADAPTIVE_TEXT_SECONDARY
        )
        self.concurrent_label.pack(side="left", padx=(0, 15))

        # 右侧版本信息
        version_label = ctk.CTkLabel(
            status_frame,
            text="跨海帆-Imager V3.0 - 专业图像生成工具 | Powered by AI",
            font=ctk.CTkFont(size=10),
            text_color=ADAPTIVE_TEXT_TERTIARY
        )
        version_label.pack(side="right", padx=15, pady=8)

    # =========================================================================
    # 工具方法
    # =========================================================================

    def adjust_color(self, color, factor):
        """调整颜色亮度

        Args:
            color: 十六进制颜色字符串，如 "#4A90E2"
            factor: 调整因子，小于1变暗，大于1变亮

        Returns:
            调整后的十六进制颜色字符串
        """
        # 移除 # 号
        color = color.lstrip('#')

        # 转换为 RGB
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)

        # 调整亮度
        r = int(min(255, max(0, r * factor)))
        g = int(min(255, max(0, g * factor)))
        b = int(min(255, max(0, b * factor)))

        # 转换回十六进制
        return f"#{r:02x}{g:02x}{b:02x}"

    def toggle_theme(self):
        """切换深色/浅色主题"""
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Light":
            ctk.set_appearance_mode("dark")
            self.theme_btn.configure(text="☀️ 浅色")
            self.config['appearance_mode'] = "dark"
        else:
            ctk.set_appearance_mode("light")
            self.theme_btn.configure(text="🌙 深色")
            self.config['appearance_mode'] = "light"
        self.save_config()

    def open_settings(self):
        """打开设置对话框"""
        messagebox.showinfo("设置", "设置对话框开发中...")

    def open_help(self):
        """打开帮助文档"""
        messagebox.showinfo("帮助", "帮助文档开发中...\n\n请参考项目文档目录中的说明文件。")

    def browse_directory(self):
        """浏览保存目录"""
        directory = filedialog.askdirectory(initialdir=self.save_dir_var.get())
        if directory:
            self.save_dir_var.set(directory)

    def load_browser_list(self):
        """加载比特浏览器列表"""
        try:
            import requests

            payload = {"page": 0, "pageSize": 200}
            self.log_message("正在获取浏览器列表...")

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

                        self.log_message(f"✅ 找到 {running_count} 个运行中的浏览器", "success")

                        if browsers:
                            self.browser_combo.configure(values=browsers)
                            current_value = self.browser_var.get()
                            if current_value in browsers:
                                self.browser_var.set(current_value)
                            else:
                                self.browser_var.set(browsers[0])
                        else:
                            self.browser_combo.configure(values=[])
                            self.browser_var.set("")
                            self.log_message("⚠️ 没有找到运行中的浏览器", "warning")
        except Exception as e:
            self.log_message(f"❌ 加载浏览器列表失败: {str(e)}", "error")

    def add_task(self):
        """添加任务（快速模式）"""
        # 验证输入
        browser_display = self.browser_var.get()
        if not browser_display:
            messagebox.showerror("错误", "请选择一个比特浏览器")
            return

        browser_id = self.browser_id_map.get(browser_display)
        if not browser_id:
            messagebox.showerror("错误", "无效的浏览器选择")
            return

        prompt = self.prompt_textbox.get("1.0", "end-1c").strip()
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

        # 根据执行模式选择添加方式
        use_queue_mode = self.quick_use_window_queue_var.get()

        if use_queue_mode:
            # 窗口队列模式
            self.add_task_to_queue_quick(browser_id, browser_display, prompt)
        else:
            # 传统并发模式
            self.add_independent_task(browser_id, browser_display, prompt)

    def add_independent_task(self, browser_id, browser_display, prompt):
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

        # 创建保存目录
        save_dir = Path(self.save_dir_var.get())
        if self.create_folders_var.get():
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
            browser_display.split(' ')[0],
            prompt[:30] + "..." if len(prompt) > 30 else prompt,
            self.ratio_var.get(),
            self.count_var.get(),
            "准备中",
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

    def add_task_to_queue_quick(self, browser_id, browser_display, prompt):
        """添加任务到窗口队列（快速任务）"""
        # 生成任务ID
        self.thread_counter += 1
        task_id = f"Q{self.thread_counter:03d}"

        # 准备任务参数
        task_params = {
            'task_id': task_id,
            'task_name': self.task_name_var.get(),
            'prompt': prompt,
            'count': self.count_var.get(),
            'aspect_ratio': self.ratio_var.get(),
            'base_save_dir': self.save_dir_var.get()
        }

        # 获取归档模式
        archive_mode = self.quick_archive_mode.get()

        # 目前简化处理，直接使用选择的归档模式
        # TODO: 如果是ask模式，弹出对话框询问用户
        session_mode = archive_mode
        session_name = None

        if archive_mode == 'new_session':
            # 创建新任务组，使用任务名作为组名
            session_name = self.task_name_var.get()

        # 切换到队列状态面板
        self.switch_right_panel_to_queue_status()

        # 添加到窗口队列
        if not hasattr(self, 'window_queue_manager'):
            from whisk_window_queue import WindowQueueManager
            self.window_queue_manager = WindowQueueManager(gui_callback=self.handle_queue_callback_quick)

        success = self.window_queue_manager.add_task_to_window(
            browser_id, browser_display, task_params, session_mode, session_name
        )

        if success:
            self.log_quick(f"✅ 任务 {task_id} 已添加到窗口队列")
            # 刷新队列状态显示
            self.refresh_queue_status_quick()
            # 更新任务名称为下一个
            self.task_name_var.set(f"任务_{datetime.now().strftime('%H%M%S')}")
        else:
            self.log_quick(f"❌ 添加任务失败", level="ERROR")

    def handle_queue_callback_quick(self, event_type, browser_id, data):
        """处理窗口队列的回调（快速任务）

        Args:
            event_type: 事件类型
            browser_id: 浏览器ID
            data: 事件数据
        """
        # 在主线程中更新UI
        task_id = data.get('task_id', '') if data else ''

        if event_type == 'task_start':
            message = f"🔄 任务 {task_id} 开始执行"
            self.log_quick(message)

        elif event_type == 'task_progress':
            message = data.get('message', '')
            self.log_quick(f"📊 {task_id}: {message}")

        elif event_type == 'task_complete':
            downloads = data.get('downloads', 0)
            message = f"✅ 任务 {task_id} 完成，下载了 {downloads} 张图片"
            self.log_quick(message)

        elif event_type == 'task_error':
            error = data.get('error', '未知错误')
            message = f"❌ 任务 {task_id} 失败: {error}"
            self.log_quick(message, level="ERROR")

        # 刷新队列状态
        if hasattr(self, 'quick_current_panel') and self.quick_current_panel == 'queue_status':
            self.refresh_queue_status_quick()

        # 更新UI
        self.update_running_count()
        self.stop_all_btn.configure(state="normal")

        # 更新任务名称
        self.task_name_var.set(f"任务_{datetime.now().strftime('%H%M%S')}")

        self.log_message(f"✅ 任务 {task_id} 已启动", "success")

    def run_task(self, task_id, browser_id, prompt, count, ratio, save_dir, tree_item):
        """在线程中运行任务"""
        def message_callback(msg):
            self.message_queue.put(('log', task_id, msg))

        def progress_callback(current, total, progress_type='generation'):
            self.message_queue.put(('progress', task_id, (current, total, progress_type)))

        try:
            self.message_queue.put(('status', task_id, "连接中"))

            automation = WhiskAutomationCoreV2(
                browser_id=browser_id,
                save_directory=save_dir,
                message_callback=message_callback,
                progress_callback=progress_callback,
                use_enhanced_download=self.enhanced_download_var.get()
            )

            self.threads[task_id]['automation'] = automation

            automation.run(
                prompt=prompt,
                count=count,
                aspect_ratio=ratio,
                min_delay=self.min_delay_var.get(),
                max_delay=self.max_delay_var.get()
            )

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

    def stop_all_tasks(self):
        """停止所有任务"""
        if messagebox.askyesno("确认", "确定要停止所有运行中的任务吗？"):
            for task_id, task_info in self.threads.items():
                if task_info['status'] == 'running':
                    if 'automation' in task_info:
                        automation = task_info['automation']
                        automation.stop_task()

                    task_info['status'] = 'stopping'
                    self.task_tree.set(task_info['tree_item'], '状态', "停止中")

            self.log_message("⚠️ 已发送停止信号给所有任务", "warning")
            self.update_running_count()

    def clear_completed_tasks(self):
        """清除已完成的任务"""
        to_remove = []
        for task_id, task_info in self.threads.items():
            if task_info['status'] in ['completed', 'failed', 'stopped']:
                self.task_tree.delete(task_info['tree_item'])
                to_remove.append(task_id)

        for task_id in to_remove:
            del self.threads[task_id]

        self.log_message(f"🗑️ 已清除 {len(to_remove)} 个任务", "info")
        self.update_running_count()

    def update_running_count(self):
        """更新运行中任务计数"""
        running_count = sum(1 for t in self.threads.values() if t['status'] in ['running', 'stopping'])
        self.running_label.configure(text=f"运行中: {running_count}")

        if running_count == 0:
            self.stop_all_btn.configure(state="disabled")

    def clean_task_name(self, name):
        """清理任务名称"""
        import re
        cleaned = re.sub(r'[^\w\u4e00-\u9fff\-_]', '', name)
        return cleaned or "task"

    def log_message(self, message, level="info"):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"

        self.log_textbox.insert("end", formatted_message)
        self.log_textbox.see("end")

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
                            if progress_type == 'download':
                                self.task_tree.set(tree_item, '进度', f"下载:{current}/{total}")
                            else:
                                self.task_tree.set(tree_item, '进度', f"生成:{current}/{total}")

                elif msg_type == 'status':
                    if task_id in self.threads:
                        tree_item = self.threads[task_id]['tree_item']
                        self.task_tree.set(tree_item, '状态', data)

                elif msg_type == 'error':
                    self.log_message(f"[{task_id}] ❌ 错误: {data}", "error")

                elif msg_type == 'done':
                    self.update_running_count()

        except queue.Empty:
            pass

        self.after(100, self.process_messages)

    def handle_queue_callback(self, event_type, browser_id, data):
        """处理窗口队列回调"""
        # TODO: 实现窗口队列回调处理
        pass

    # ==================== 可复用组件：执行模式和归档选择 ====================

    def create_execution_mode_section(self, parent, context="quick"):
        """创建执行模式选择区（可复用组件）

        Args:
            parent: 父容器
            context: 上下文标识，"quick"表示快速任务，"batch"表示批量任务
        """
        mode_frame = ctk.CTkFrame(parent, fg_color="transparent")
        mode_frame.pack(fill="x", pady=(15, 0))

        # 分割线
        separator = ctk.CTkFrame(mode_frame, height=2, fg_color=BORDER_LIGHT)
        separator.pack(fill="x", pady=(0, 10))

        # 标题
        mode_title = ctk.CTkLabel(
            mode_frame,
            text="🔁 执行模式",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        mode_title.pack(anchor="w", pady=(0, 8))

        # 窗口队列开关
        var_name = f"{context}_use_window_queue_var"
        setattr(self, var_name, ctk.BooleanVar(value=self.config.get('use_window_queue', False)))
        use_queue_var = getattr(self, var_name)

        queue_checkbox = ctk.CTkCheckBox(
            mode_frame,
            text="启用窗口队列模式",
            variable=use_queue_var,
            command=lambda: self.toggle_execution_mode(context),
            font=ctk.CTkFont(size=12)
        )
        queue_checkbox.pack(anchor="w", pady=(0, 10))

        # 说明文本
        help_text = ctk.CTkLabel(
            mode_frame,
            text="💡 队列模式：同一浏览器的任务串行执行，支持套图归档",
            font=ctk.CTkFont(size=10),
            text_color=ADAPTIVE_TEXT_SECONDARY,
            wraplength=360,
            justify="left"
        )
        help_text.pack(anchor="w", pady=(0, 10))

        # 归档模式区域（条件显示）
        archive_frame_name = f"{context}_archive_mode_frame"
        archive_frame = ctk.CTkFrame(mode_frame, fg_color=ADAPTIVE_BG_SECONDARY, corner_radius=8)
        setattr(self, archive_frame_name, archive_frame)

        # 初始隐藏或显示
        if use_queue_var.get():
            archive_frame.pack(fill="x", pady=(0, 10))
        else:
            archive_frame.pack_forget()

        # 归档模式内容
        self.create_archive_mode_content(archive_frame, context)

        return mode_frame

    def create_archive_mode_content(self, parent, context):
        """创建归档模式选择内容（可复用）

        Args:
            parent: 父容器
            context: 上下文标识
        """
        # 标题
        archive_label = ctk.CTkLabel(
            parent,
            text="归档模式：",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        archive_label.pack(anchor="w", padx=15, pady=(12, 5))

        # 单选按钮变量
        var_name = f"{context}_archive_mode"
        setattr(self, var_name, ctk.StringVar(value="independent"))
        archive_mode_var = getattr(self, var_name)

        modes = [
            ("independent", "独立任务", "每个任务独立文件夹"),
            ("new_session", "创建新任务组", "开始新的套图系列"),
            ("join_current", "加入当前任务组", "追加到现有套图")
        ]

        for value, label, desc in modes:
            radio = ctk.CTkRadioButton(
                parent,
                text=label,
                variable=archive_mode_var,
                value=value,
                command=lambda c=context: self.on_archive_mode_changed(c)
            )
            radio.pack(anchor="w", padx=25, pady=2)

            desc_label = ctk.CTkLabel(
                parent,
                text=f"  └─ {desc}",
                font=ctk.CTkFont(size=10),
                text_color=ADAPTIVE_TEXT_TERTIARY
            )
            desc_label.pack(anchor="w", padx=40, pady=(0, 5))

        # 任务组名称（条件显示）
        session_frame_name = f"{context}_session_name_frame"
        session_name_frame = ctk.CTkFrame(parent, fg_color="transparent")
        setattr(self, session_frame_name, session_name_frame)
        session_name_frame.pack(fill="x", padx=15, pady=(5, 12))

        label_name = f"{context}_session_name_label"
        session_name_label = ctk.CTkLabel(
            session_name_frame,
            text="任务组名称:",
            font=ctk.CTkFont(size=11)
        )
        setattr(self, label_name, session_name_label)
        session_name_label.pack(anchor="w", pady=(0, 3))

        var_name = f"{context}_session_name_var"
        setattr(self, var_name, ctk.StringVar(value=f"套图_{datetime.now().strftime('%H%M%S')}"))
        session_name_var = getattr(self, var_name)

        entry_name = f"{context}_session_name_entry"
        session_name_entry = ctk.CTkEntry(
            session_name_frame,
            textvariable=session_name_var,
            height=32
        )
        setattr(self, entry_name, session_name_entry)
        session_name_entry.pack(fill="x", pady=(0, 5))

        # 初始状态
        self.update_session_name_visibility(context)

    def toggle_execution_mode(self, context):
        """切换执行模式时的UI更新

        Args:
            context: 上下文标识
        """
        use_queue_var = getattr(self, f"{context}_use_window_queue_var")
        is_queue_mode = use_queue_var.get()

        archive_frame = getattr(self, f"{context}_archive_mode_frame")

        if is_queue_mode:
            # 显示归档模式区域
            archive_frame.pack(fill="x", pady=(0, 10))
            # 切换右侧面板为队列状态
            if context == "quick":
                self.switch_right_panel_to_queue_status()
            elif context == "batch":
                self.switch_batch_panel_to_window_queue_status()
        else:
            # 隐藏归档模式区域
            archive_frame.pack_forget()
            # 切换右侧面板为任务列表
            if context == "quick":
                self.switch_right_panel_to_task_list()
            elif context == "batch":
                self.switch_batch_panel_to_task_queue()

        # 保存配置
        self.config['use_window_queue'] = is_queue_mode
        self.save_config()

    def on_archive_mode_changed(self, context):
        """归档模式改变时更新UI

        Args:
            context: 上下文标识
        """
        self.update_session_name_visibility(context)

    def update_session_name_visibility(self, context):
        """根据归档模式更新任务组名称输入框的可见性

        Args:
            context: 上下文标识
        """
        archive_mode_var = getattr(self, f"{context}_archive_mode")
        mode = archive_mode_var.get()

        session_name_entry = getattr(self, f"{context}_session_name_entry")
        session_name_label = getattr(self, f"{context}_session_name_label")

        if mode == "new_session":
            # 创建新任务组时需要输入名称
            session_name_entry.configure(state="normal")
            session_name_label.configure(text_color=ADAPTIVE_TEXT_PRIMARY)
        else:
            # 其他模式不需要名称
            session_name_entry.configure(state="disabled")
            session_name_label.configure(text_color=TEXT_LIGHT_DISABLED)

    # ==================== 可复用组件结束 ====================

    # ==================== 右侧面板切换方法 ====================

    def switch_right_panel_to_task_list(self):
        """切换右侧面板为任务列表（传统模式）"""
        if hasattr(self, 'quick_current_panel') and self.quick_current_panel == "task_list":
            return  # 已经是任务列表面板，无需切换

        if hasattr(self, 'quick_queue_status_panel'):
            self.quick_queue_status_panel.grid_forget()

        if hasattr(self, 'quick_task_list_panel'):
            self.quick_task_list_panel.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        self.quick_current_panel = "task_list"

    def switch_right_panel_to_queue_status(self):
        """切换右侧面板为队列状态（队列模式）"""
        if hasattr(self, 'quick_current_panel') and self.quick_current_panel == "queue_status":
            return  # 已经是队列状态面板，无需切换

        if hasattr(self, 'quick_task_list_panel'):
            self.quick_task_list_panel.grid_forget()

        if hasattr(self, 'quick_queue_status_panel'):
            self.quick_queue_status_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
            # 刷新队列状态
            if hasattr(self, 'refresh_queue_status_quick'):
                self.refresh_queue_status_quick()

        self.quick_current_panel = "queue_status"

    # ==================== 右侧面板切换方法结束 ====================

    # ==================== 窗口队列相关方法 ====================

    def create_queue_status_panel(self, parent):
        """创建窗口队列状态显示面板（右侧）"""
        right_panel = ctk.CTkFrame(parent, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)

        # 标题
        status_label = ctk.CTkLabel(
            right_panel,
            text="📊 队列状态",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=QUEUE_COLOR
        )
        status_label.pack(pady=(0, 10))

        # 队列列表容器
        list_frame = ctk.CTkFrame(right_panel, fg_color=ADAPTIVE_BG_SECONDARY)
        list_frame.pack(fill="both", expand=True)

        # 队列列表标题
        list_header = ctk.CTkLabel(
            list_frame,
            text="当前窗口队列",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        list_header.pack(pady=10)

        # 队列信息显示区域（滚动框）
        self.queue_status_text = ctk.CTkTextbox(
            list_frame,
            height=400,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=ADAPTIVE_BG_PRIMARY,
            wrap="word"
        )
        self.queue_status_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 初始提示
        initial_text = """
暂无队列任务

💡 使用说明：
1. 在左侧选择浏览器
2. 配置任务参数
3. 选择归档模式
4. 点击"添加到窗口队列"

窗口队列特点：
✅ 同一窗口任务串行执行
✅ 浏览器连接复用，效率更高
✅ 支持套图归档
✅ 任务间状态隔离
"""
        self.queue_status_text.insert("1.0", initial_text)
        self.queue_status_text.configure(state="disabled")

        # 刷新按钮
        refresh_btn = ctk.CTkButton(
            list_frame,
            text="🔄 刷新队列状态",
            command=self.refresh_queue_status,
            fg_color=QUEUE_COLOR,
            hover_color=self.adjust_color(QUEUE_COLOR, 0.8),
            height=36
        )
        refresh_btn.pack(pady=(0, 10), padx=10, fill="x")

    def toggle_queue_session_name(self):
        """切换会话名称输入框的显示状态"""
        mode = self.queue_archive_mode.get()
        if mode == "new_session":
            self.queue_session_name_entry.configure(state="normal")
            self.queue_session_name_label.configure(text_color=ADAPTIVE_TEXT_PRIMARY)
        else:
            self.queue_session_name_entry.configure(state="disabled")
            self.queue_session_name_label.configure(text_color=TEXT_LIGHT_DISABLED)

    def refresh_queue_browser_list(self):
        """刷新窗口队列的浏览器列表"""
        try:
            import requests

            payload = {"page": 0, "pageSize": 200}
            self.log_message("🔄 正在刷新队列浏览器列表...")

            response = requests.post("http://127.0.0.1:54345/browser/list", json=payload, timeout=5)

            if response.status_code == 200:
                data = response.json()

                if data.get('success') and 'data' in data:
                    browsers = []
                    self.queue_browser_id_map = {}
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
                                    self.queue_browser_id_map[display_name] = browser_id

                        self.log_message(f"✅ 找到 {running_count} 个运行中的浏览器", "success")

                        if browsers:
                            self.queue_browser_combo.configure(values=browsers)
                            current_value = self.queue_browser_var.get()
                            if current_value in browsers:
                                self.queue_browser_var.set(current_value)
                            else:
                                self.queue_browser_var.set(browsers[0])
                        else:
                            self.queue_browser_combo.configure(values=[])
                            self.queue_browser_var.set("")
                            self.log_message("⚠️ 没有找到运行中的浏览器", "warning")
        except Exception as e:
            self.log_message(f"❌ 刷新浏览器列表失败: {str(e)}", "error")

    def on_queue_browser_selected(self, choice):
        """处理队列浏览器选择"""
        if choice and choice in self.queue_browser_id_map:
            browser_id = self.queue_browser_id_map[choice]
            self.log_message(f"📱 已选择浏览器: {choice.split(' ')[0]}", "info")

            # TODO: 显示该浏览器的队列状态
            self.refresh_queue_status()

    def browse_queue_directory(self):
        """浏览队列保存目录"""
        directory = filedialog.askdirectory(initialdir=self.queue_save_dir_var.get())
        if directory:
            self.queue_save_dir_var.set(directory)

    def refresh_queue_status(self):
        """刷新队列状态显示"""
        try:
            self.queue_status_text.configure(state="normal")
            self.queue_status_text.delete("1.0", "end")

            # 获取选中的浏览器
            browser_display = self.queue_browser_var.get()
            if not browser_display or browser_display not in self.queue_browser_id_map:
                self.queue_status_text.insert("1.0", "⚠️ 请先选择浏览器")
                self.queue_status_text.configure(state="disabled")
                return

            browser_id = self.queue_browser_id_map[browser_display]

            # 从窗口队列管理器获取状态
            if hasattr(self, 'window_queue_manager'):
                queue = self.window_queue_manager.get_window_queue(browser_id)
                if queue:
                    status = queue.get_status()

                    # 格式化显示
                    status_text = f"""
🌐 浏览器: {browser_display.split(' ')[0]}
📊 队列状态: {'运行中' if status['is_running'] else '空闲'}
📝 待处理任务: {status['queue_size']}
✅ 已完成任务: {status['completed_count']}

"""
                    if status['current_task']:
                        task = status['current_task']
                        status_text += f"""
🔄 当前任务:
   任务名: {task.get('task_name', 'N/A')}
   提示词: {task.get('prompt', 'N/A')[:50]}...
   进度: 执行中

"""

                    if status['current_session']:
                        session = status['current_session']
                        status_text += f"""
📁 当前任务组:
   组名: {session.get('session_name', 'N/A')}
   包含任务: {session.get('task_count', 0)}
   空闲时间: {session.get('idle_time', 0):.1f}秒

"""

                    self.queue_status_text.insert("1.0", status_text)
                else:
                    self.queue_status_text.insert("1.0", f"""
🌐 浏览器: {browser_display.split(' ')[0]}
📊 队列状态: 未初始化

💡 提示: 添加第一个任务后队列将自动创建
""")
            else:
                self.queue_status_text.insert("1.0", "❌ 窗口队列管理器未初始化")

        except Exception as e:
            self.queue_status_text.insert("1.0", f"❌ 获取队列状态失败: {str(e)}")
        finally:
            self.queue_status_text.configure(state="disabled")

    def add_task_to_window_queue(self):
        """添加任务到窗口队列"""
        # 验证输入
        browser_display = self.queue_browser_var.get()
        if not browser_display or browser_display not in self.queue_browser_id_map:
            messagebox.showerror("错误", "请选择一个运行中的比特浏览器")
            return

        browser_id = self.queue_browser_id_map[browser_display]

        task_name = self.queue_task_name_var.get().strip()
        if not task_name:
            messagebox.showerror("错误", "请输入任务名称")
            return

        prompt = self.queue_prompt_text.get("1.0", "end-1c").strip()
        if not prompt:
            messagebox.showerror("错误", "请输入提示词")
            return

        archive_mode = self.queue_archive_mode.get()
        if archive_mode == "new_session":
            session_name = self.queue_session_name_var.get().strip()
            if not session_name:
                messagebox.showerror("错误", "请输入任务组名称")
                return
        else:
            session_name = None

        # 准备任务参数
        task_params = {
            'task_id': f"Q{self.thread_counter:03d}",
            'task_name': task_name,
            'prompt': prompt,
            'count': self.queue_count_var.get(),
            'aspect_ratio': self.queue_ratio_var.get(),
            'save_dir': self.queue_save_dir_var.get(),
            'use_enhanced_download': self.config.get('use_enhanced_download', True),
            'min_delay': self.config.get('min_delay', 2),
            'max_delay': self.config.get('max_delay', 3)
        }

        self.thread_counter += 1

        try:
            # 添加到窗口队列
            if not hasattr(self, 'window_queue_manager'):
                from whisk_window_queue import WindowQueueManager
                self.window_queue_manager = WindowQueueManager()

            self.window_queue_manager.add_task_to_window(
                browser_id=browser_id,
                browser_name=browser_display.split(' ')[0],
                task_params=task_params,
                session_mode=archive_mode,
                session_name=session_name,
                gui_callback=self.handle_queue_callback
            )

            self.log_message(f"✅ 任务 [{task_name}] 已添加到窗口队列", "success")
            self.log_message(f"   浏览器: {browser_display.split(' ')[0]}", "info")
            self.log_message(f"   归档模式: {archive_mode}", "info")

            # 刷新队列状态
            self.refresh_queue_status()

            # 更新任务名称
            self.queue_task_name_var.set(f"任务_{datetime.now().strftime('%H%M%S')}")

        except Exception as e:
            messagebox.showerror("错误", f"添加任务失败: {str(e)}")
            self.log_message(f"❌ 添加任务失败: {str(e)}", "error")

    # ==================== 窗口队列方法结束 ====================

    # ==================== 批量任务相关方法 ====================

    def create_batch_queue_panel(self, parent):
        """创建批量任务双面板容器（右侧）"""
        # 创建两个面板
        self.batch_task_queue_panel = self.create_batch_task_queue_view(parent)
        self.batch_window_queue_status_panel = self.create_batch_window_queue_status_view(parent)

        # 初始显示批量任务队列面板
        self.batch_current_panel = "task_queue"
        self.batch_task_queue_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        self.batch_window_queue_status_panel.grid_forget()

        # 批量任务队列数据结构
        self.batch_tasks = []  # 存储批量任务
        self.batch_browser_id_map = {}  # 浏览器ID映射

    def create_batch_task_queue_view(self, parent):
        """创建批量任务队列预览面板（传统模式）"""
        right_panel = ctk.CTkFrame(parent, fg_color="transparent")

        # 标题
        header_label = ctk.CTkLabel(
            right_panel,
            text="📊 批量任务队列",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=SUCCESS_COLOR
        )
        header_label.pack(pady=(0, 10))

        # 队列容器
        queue_container = ctk.CTkFrame(right_panel, fg_color=ADAPTIVE_BG_SECONDARY)
        queue_container.pack(fill="both", expand=True)

        # 队列列表标题
        queue_header = ctk.CTkLabel(
            queue_container,
            text="任务队列预览",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        queue_header.pack(pady=10)

        # 批量任务列表（使用Textbox显示）
        self.batch_queue_text = ctk.CTkTextbox(
            queue_container,
            height=400,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=ADAPTIVE_BG_PRIMARY,
            wrap="word"
        )
        self.batch_queue_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 初始提示
        initial_text = """
暂无批量任务

💡 使用说明：
1. 在左侧批量输入提示词（每行一个）
2. 选择统一的浏览器和配置
3. 点击"生成批量任务"
4. 任务将加入队列并逐个执行

批量任务特点：
✅ 快速导入多个提示词
✅ 统一配置，节省时间
✅ 按顺序执行，避免冲突
✅ 支持随时查看进度
"""
        self.batch_queue_text.insert("1.0", initial_text)
        self.batch_queue_text.configure(state="disabled")

        # 控制按钮区
        button_frame = ctk.CTkFrame(queue_container, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        # 启动所有任务按钮（使用强调色 - 航海金）
        self.start_batch_btn = ctk.CTkButton(
            button_frame,
            text="▶️ 启动队列",
            command=self.start_batch_queue,
            state="disabled",
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            text_color="#FFFFFF",
            height=36
        )
        self.start_batch_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # 停止所有任务按钮
        self.stop_batch_btn = ctk.CTkButton(
            button_frame,
            text="⏹️ 停止",
            command=self.stop_batch_queue,
            state="disabled",
            fg_color=ERROR_COLOR,
            hover_color=self.adjust_color(ERROR_COLOR, 0.8),
            text_color="#FFFFFF",
            height=36
        )
        self.stop_batch_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # 清空队列按钮
        self.clear_batch_btn = ctk.CTkButton(
            button_frame,
            text="🗑️ 清空",
            command=self.clear_batch_queue,
            state="disabled",
            fg_color=WARNING_COLOR,
            hover_color=self.adjust_color(WARNING_COLOR, 0.8),
            text_color="#FFFFFF",
            height=36
        )
        self.clear_batch_btn.pack(side="left", fill="x", expand=True)

        return right_panel

    def create_batch_window_queue_status_view(self, parent):
        """创建批量任务窗口队列状态面板（队列模式）"""
        panel = ctk.CTkFrame(parent, fg_color="transparent")

        # 标题
        status_label = ctk.CTkLabel(
            panel,
            text="📊 窗口队列状态 (批量任务)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=QUEUE_COLOR
        )
        status_label.pack(pady=(0, 10))

        # 队列状态容器
        queue_container = ctk.CTkFrame(panel, fg_color=ADAPTIVE_BG_SECONDARY)
        queue_container.pack(fill="both", expand=True)

        # 状态标题
        queue_header = ctk.CTkLabel(
            queue_container,
            text="队列实时状态",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        queue_header.pack(pady=10)

        # 队列状态显示
        self.batch_window_queue_status_text = ctk.CTkTextbox(
            queue_container,
            height=500,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=ADAPTIVE_BG_PRIMARY,
            wrap="word"
        )
        self.batch_window_queue_status_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 初始提示
        initial_text = """
暂无窗口队列任务

💡 使用说明：
1. 勾选"启用窗口队列模式"
2. 选择归档模式
3. 输入批量提示词
4. 点击"生成批量任务"
5. 点击"启动队列"开始执行

窗口队列特点：
✅ 同一窗口任务串行执行
✅ 浏览器连接复用，效率更高
✅ 支持套图归档
✅ 任务间状态隔离
"""
        self.batch_window_queue_status_text.insert("1.0", initial_text)
        self.batch_window_queue_status_text.configure(state="disabled")

        # 刷新按钮
        refresh_btn = ctk.CTkButton(
            queue_container,
            text="🔄 刷新队列状态",
            command=self.refresh_batch_window_queue_status,
            fg_color=QUEUE_COLOR,
            hover_color=self.adjust_color(QUEUE_COLOR, 0.8),
            height=36
        )
        refresh_btn.pack(fill="x", padx=10, pady=(0, 10))

        return panel

    def refresh_batch_window_queue_status(self):
        """刷新批量任务的窗口队列状态显示"""
        try:
            self.batch_window_queue_status_text.configure(state="normal")
            self.batch_window_queue_status_text.delete("1.0", "end")

            # 获取选中的浏览器
            browser_display = self.batch_browser_var.get()
            if not browser_display or browser_display not in self.batch_browser_id_map:
                self.batch_window_queue_status_text.insert("1.0", "⚠️ 请先选择浏览器")
                return

            browser_id = self.batch_browser_id_map[browser_display]

            # 获取队列状态
            if hasattr(self, 'window_queue_manager'):
                queue = self.window_queue_manager.get_window_queue(browser_id)
                if queue:
                    status = queue.get_status()

                    # 格式化显示
                    status_text = f"""
🌐 浏览器: {browser_display.split(' ')[0]}
📊 队列状态: {'运行中' if status['is_running'] else '空闲'}
📝 待处理任务: {status['queue_size']}
✅ 已完成任务: {status['completed_count']}
"""

                    # 显示当前任务
                    if status['current_task']:
                        task = status['current_task']
                        status_text += f"""
🔄 当前任务:
   任务ID: {task.get('task_id', 'N/A')}
   提示词: {task.get('prompt', 'N/A')[:50]}...
"""

                    # 显示任务组信息
                    if status['current_session']:
                        session = status['current_session']
                        status_text += f"""
📁 当前任务组:
   组名: {session.get('name', 'N/A')}
   任务数: {session.get('task_count', 0)}
"""

                    # 显示批量任务列表状态
                    if self.batch_tasks:
                        status_text += f"\n\n📋 批量任务列表状态:\n"
                        for task in self.batch_tasks:
                            status_emoji = {
                                '待执行': '⏸️',
                                '队列中': '⏳',
                                '执行中': '🔄',
                                '已完成': '✅',
                                '失败': '❌',
                                '已停止': '⏹️'
                            }.get(task['status'], '❓')

                            status_text += f"\n{status_emoji} {task['id']}: {task['status']}"
                            if task.get('progress'):
                                status_text += f" - {task['progress']}"

                    self.batch_window_queue_status_text.insert("1.0", status_text)
                else:
                    self.batch_window_queue_status_text.insert("1.0", "暂无队列数据")
            else:
                self.batch_window_queue_status_text.insert("1.0", "窗口队列管理器未初始化")

        except Exception as e:
            self.batch_window_queue_status_text.insert("1.0", f"❌ 获取队列状态失败: {str(e)}")
        finally:
            self.batch_window_queue_status_text.configure(state="disabled")

    def switch_batch_panel_to_task_queue(self):
        """切换批量任务右侧面板为任务队列预览"""
        if hasattr(self, 'batch_current_panel') and self.batch_current_panel == "task_queue":
            return

        if hasattr(self, 'batch_window_queue_status_panel'):
            self.batch_window_queue_status_panel.grid_forget()

        if hasattr(self, 'batch_task_queue_panel'):
            self.batch_task_queue_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)

        self.batch_current_panel = "task_queue"

    def switch_batch_panel_to_window_queue_status(self):
        """切换批量任务右侧面板为窗口队列状态"""
        if hasattr(self, 'batch_current_panel') and self.batch_current_panel == "window_queue_status":
            return

        if hasattr(self, 'batch_task_queue_panel'):
            self.batch_task_queue_panel.grid_forget()

        if hasattr(self, 'batch_window_queue_status_panel'):
            self.batch_window_queue_status_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
            # 刷新队列状态
            self.refresh_batch_window_queue_status()

        self.batch_current_panel = "window_queue_status"

    def clear_batch_placeholder(self):
        """清除批量输入框的占位文本"""
        current_text = self.batch_prompt_text.get("1.0", "end-1c")
        if current_text.startswith("示例："):
            self.batch_prompt_text.delete("1.0", "end")

    def refresh_batch_browser_list(self):
        """刷新批量任务的浏览器列表"""
        try:
            import requests

            payload = {"page": 0, "pageSize": 200}
            self.log_message("🔄 正在刷新批量浏览器列表...")

            response = requests.post("http://127.0.0.1:54345/browser/list", json=payload, timeout=5)

            if response.status_code == 200:
                data = response.json()

                if data.get('success') and 'data' in data:
                    browsers = []
                    self.batch_browser_id_map = {}
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
                                    self.batch_browser_id_map[display_name] = browser_id

                        self.log_message(f"✅ 找到 {running_count} 个运行中的浏览器", "success")

                        if browsers:
                            self.batch_browser_combo.configure(values=browsers)
                            current_value = self.batch_browser_var.get()
                            if current_value in browsers:
                                self.batch_browser_var.set(current_value)
                            else:
                                self.batch_browser_var.set(browsers[0])
                        else:
                            self.batch_browser_combo.configure(values=[])
                            self.batch_browser_var.set("")
                            self.log_message("⚠️ 没有找到运行中的浏览器", "warning")
        except Exception as e:
            self.log_message(f"❌ 刷新浏览器列表失败: {str(e)}", "error")

    def browse_batch_directory(self):
        """浏览批量任务保存目录"""
        directory = filedialog.askdirectory(initialdir=self.batch_save_dir_var.get())
        if directory:
            self.batch_save_dir_var.set(directory)

    def generate_batch_tasks(self):
        """生成批量任务"""
        # 验证输入
        browser_display = self.batch_browser_var.get()
        if not browser_display or browser_display not in self.batch_browser_id_map:
            messagebox.showerror("错误", "请选择一个运行中的比特浏览器")
            return

        browser_id = self.batch_browser_id_map[browser_display]

        # 获取所有提示词
        prompts_text = self.batch_prompt_text.get("1.0", "end-1c").strip()
        if not prompts_text or prompts_text.startswith("示例："):
            messagebox.showerror("错误", "请输入批量提示词")
            return

        # 分割提示词（按行）
        prompts = [p.strip() for p in prompts_text.split('\n') if p.strip()]
        if not prompts:
            messagebox.showerror("错误", "没有有效的提示词")
            return

        # 确认生成
        confirm_msg = f"将生成 {len(prompts)} 个任务，是否继续？\n\n" \
                     f"浏览器: {browser_display.split(' ')[0]}\n" \
                     f"纵横比: {self.batch_ratio_var.get()}\n" \
                     f"生成轮数: {self.batch_count_var.get()}"

        if not messagebox.askyesno("确认", confirm_msg):
            return

        # 清空现有队列
        self.batch_tasks.clear()

        # 生成任务列表
        for idx, prompt in enumerate(prompts, 1):
            task = {
                'id': f"B{idx:03d}",
                'browser_id': browser_id,
                'browser_name': browser_display.split(' ')[0],
                'prompt': prompt,
                'ratio': self.batch_ratio_var.get(),
                'count': self.batch_count_var.get(),
                'save_dir': self.batch_save_dir_var.get(),
                'status': '待执行',
                'progress': '0/0'
            }
            self.batch_tasks.append(task)

        # 更新显示
        self.update_batch_queue_display()

        # 启用按钮
        self.start_batch_btn.configure(state="normal")
        self.clear_batch_btn.configure(state="normal")

        self.log_message(f"✅ 已生成 {len(prompts)} 个批量任务", "success")

    def continue_add_batch_tasks(self):
        """继续添加任务到运行中的批量队列（方案C核心功能）"""
        # 验证队列是否正在运行
        if not self.batch_queue_running:
            messagebox.showwarning("警告", "批量队列未运行，请先启动队列")
            return

        # 验证输入
        browser_display = self.batch_browser_var.get()
        if not browser_display or browser_display not in self.batch_browser_id_map:
            messagebox.showerror("错误", "请选择一个运行中的比特浏览器")
            return

        browser_id = self.batch_browser_id_map[browser_display]

        # 获取新的提示词
        prompts_text = self.batch_prompt_text.get("1.0", "end-1c").strip()
        if not prompts_text or prompts_text.startswith("示例："):
            messagebox.showerror("错误", "请输入新的批量提示词")
            return

        # 分割提示词（按行）
        prompts = [p.strip() for p in prompts_text.split('\n') if p.strip()]
        if not prompts:
            messagebox.showerror("错误", "没有有效的提示词")
            return

        # 确认添加
        confirm_msg = f"将添加 {len(prompts)} 个新任务到运行中的队列，是否继续？\n\n" \
                     f"浏览器: {browser_display.split(' ')[0]}\n" \
                     f"纵横比: {self.batch_ratio_var.get()}\n" \
                     f"生成轮数: {self.batch_count_var.get()}"

        if not messagebox.askyesno("确认", confirm_msg):
            return

        # 获取当前任务数量，用于生成新的任务ID
        current_task_count = len(self.batch_tasks)

        # 获取归档模式
        archive_mode = self.batch_archive_mode.get()

        # 获取任务组名称（如果是new_session模式）
        session_name = None
        if archive_mode == 'new_session':
            if hasattr(self, 'batch_session_name_entry'):
                user_input = self.batch_session_name_entry.get().strip()
                if user_input:
                    session_name = user_input
                else:
                    session_name = f"批量任务_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            else:
                session_name = f"批量任务_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 生成新任务并直接添加到窗口队列
        new_tasks_count = 0
        for idx, prompt in enumerate(prompts, current_task_count + 1):
            # 创建任务对象
            task = {
                'id': f"B{idx:03d}",
                'browser_id': browser_id,
                'browser_name': browser_display.split(' ')[0],
                'prompt': prompt,
                'ratio': self.batch_ratio_var.get(),
                'count': self.batch_count_var.get(),
                'save_dir': self.batch_save_dir_var.get(),
                'status': '队列中',
                'progress': '0/0'
            }

            # 添加到批量任务列表
            self.batch_tasks.append(task)

            # 直接添加到窗口队列
            task_params = {
                'task_id': task['id'],
                'task_name': task['id'],
                'prompt': task['prompt'],
                'count': task['count'],
                'aspect_ratio': task['ratio'],
                'base_save_dir': task['save_dir']
            }

            self.window_queue_manager.add_task_to_window(
                task['browser_id'],
                task['browser_name'],
                task_params,
                archive_mode,
                session_name
            )

            new_tasks_count += 1

        # 更新显示
        self.update_batch_queue_display()

        # 刷新窗口队列状态显示
        self.refresh_batch_window_queue_status()

        # 清空输入框，准备下一次添加
        self.batch_prompt_text.delete("1.0", "end")
        self.batch_prompt_text.insert("1.0", "示例：\nA beautiful sunset\nA cute cat")

        self.log_message(f"✅ 已动态添加 {new_tasks_count} 个任务到队列", "success")

    def update_batch_queue_display(self):
        """更新批量队列显示"""
        self.batch_queue_text.configure(state="normal")
        self.batch_queue_text.delete("1.0", "end")

        if not self.batch_tasks:
            self.batch_queue_text.insert("1.0", "队列为空")
        else:
            display_text = f"📋 批量任务队列 (共 {len(self.batch_tasks)} 个任务)\n\n"

            for task in self.batch_tasks:
                status_emoji = {
                    '待执行': '⏸️',
                    '执行中': '🔄',
                    '已完成': '✅',
                    '失败': '❌',
                    '已停止': '⏹️'
                }.get(task['status'], '❓')

                display_text += f"{status_emoji} {task['id']} | {task['status']}\n"
                display_text += f"   提示词: {task['prompt'][:50]}{'...' if len(task['prompt']) > 50 else ''}\n"
                display_text += f"   配置: {task['ratio']} / {task['count']}轮 / {task['browser_name']}\n"
                if task['progress'] != '0/0':
                    display_text += f"   进度: {task['progress']}\n"
                display_text += "\n"

            self.batch_queue_text.insert("1.0", display_text)

        self.batch_queue_text.configure(state="disabled")

    def start_batch_queue(self):
        """启动批量队列"""
        if not self.batch_tasks:
            messagebox.showwarning("警告", "批量任务队列为空")
            return

        # 检查是否启用窗口队列模式
        use_queue_mode = self.batch_use_window_queue_var.get()

        if use_queue_mode:
            # 窗口队列模式 - 将所有批量任务添加到窗口队列
            self.start_batch_with_queue_mode()
        else:
            # 传统模式 - 并发执行批量任务
            self.start_batch_with_traditional_mode()

    def start_batch_with_queue_mode(self):
        """使用窗口队列模式执行批量任务"""
        # 获取归档模式
        archive_mode = self.batch_archive_mode.get()

        # 初始化窗口队列管理器
        if not hasattr(self, 'window_queue_manager'):
            from whisk_window_queue import WindowQueueManager
            self.window_queue_manager = WindowQueueManager(gui_callback=self.handle_queue_callback_batch)

        session_name = None
        if archive_mode == 'new_session':
            # 从用户输入获取任务组名称
            if hasattr(self, 'batch_session_name_entry'):
                user_input = self.batch_session_name_entry.get().strip()
                if user_input:
                    session_name = user_input
                else:
                    # 如果用户没有输入，使用默认名称
                    session_name = f"批量任务_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            else:
                session_name = f"批量任务_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 逐个添加到窗口队列
        for task in self.batch_tasks:
            task_params = {
                'task_id': task['id'],
                'task_name': task['id'],
                'prompt': task['prompt'],
                'count': task['count'],
                'aspect_ratio': task['ratio'],
                'base_save_dir': task['save_dir']
            }

            self.window_queue_manager.add_task_to_window(
                task['browser_id'],
                task['browser_name'],
                task_params,
                archive_mode,
                session_name
            )

            task['status'] = '队列中'

        self.update_batch_queue_display()
        self.log_message(f"✅ 已将 {len(self.batch_tasks)} 个任务添加到窗口队列", "success")

        # 设置队列运行标志
        self.batch_queue_running = True

        # 切换到窗口队列状态面板
        self.switch_batch_panel_to_window_queue_status()

        # 禁用启动按钮，启用继续添加按钮
        self.start_batch_btn.configure(state="disabled")
        self.continue_add_batch_btn.configure(state="normal")

    def start_batch_with_traditional_mode(self):
        """使用传统模式执行批量任务"""
        # 在单独线程中执行所有批量任务
        thread = threading.Thread(
            target=self.execute_batch_tasks_traditional,
            daemon=True
        )
        thread.start()

        # 禁用按钮
        self.start_batch_btn.configure(state="disabled")
        self.stop_batch_btn.configure(state="normal")

    def execute_batch_tasks_traditional(self):
        """传统模式：逐个执行批量任务"""
        for task in self.batch_tasks:
            if task['status'] == '已停止':
                break

            task['status'] = '执行中'
            self.update_batch_queue_display()

            try:
                # TODO: 实际执行任务逻辑
                # 这里需要集成whisk_core_v2的自动化逻辑
                self.log_message(f"🔄 执行任务 {task['id']}: {task['prompt'][:30]}...")

                # 暂时模拟执行
                import time
                time.sleep(2)

                task['status'] = '已完成'
                task['progress'] = f"{task['count']}/{task['count']}"

            except Exception as e:
                task['status'] = '失败'
                self.log_message(f"❌ 任务 {task['id']} 失败: {str(e)}", "error")

            self.update_batch_queue_display()

        self.log_message("✅ 批量任务队列执行完成", "success")
        self.start_batch_btn.configure(state="disabled")
        self.stop_batch_btn.configure(state="disabled")

    def handle_queue_callback_batch(self, event_type, browser_id, data):
        """处理窗口队列的回调（批量任务）

        Args:
            event_type: 事件类型
            browser_id: 浏览器ID
            data: 事件数据
        """
        # 处理可能为None的data
        if not data:
            return

        task_id = data.get('task_id', '')
        if not task_id:
            return

        # 在批量任务列表中查找对应任务
        for task in self.batch_tasks:
            if task['id'] == task_id:
                if event_type == 'task_start':
                    task['status'] = '执行中'
                    self.log_message(f"🔄 批量任务 {task_id} 开始执行 [浏览器:{browser_id}]")

                elif event_type == 'task_progress':
                    # 增强进度提取逻辑
                    current = data.get('current', 0)
                    total = data.get('total', 0)
                    progress_type = data.get('progress_type', 'unknown')

                    # 格式化进度文本
                    if progress_type == 'generation':
                        task['progress'] = f"生成:{current}/{total}"
                    elif progress_type == 'download':
                        task['progress'] = f"下载:{current}/{total}"
                    else:
                        # Fallback: 尝试从message获取
                        message = data.get('message', '')
                        if message:
                            task['progress'] = message
                        else:
                            task['progress'] = f"{current}/{total}"

                    self.log_message(f"📊 {task_id}: {task['progress']}")

                elif event_type == 'task_complete':
                    task['status'] = '已完成'
                    downloads = data.get('downloads', 0)
                    task['progress'] = f'{downloads}张'
                    self.log_message(f"✅ 批量任务 {task_id} 完成")

                elif event_type == 'task_failed':
                    task['status'] = '失败'
                    error = data.get('error', '未知错误')
                    task['progress'] = '失败'
                    self.log_message(f"❌ 批量任务 {task_id} 失败: {error}", "error")

                elif event_type == 'task_error':
                    task['status'] = '错误'
                    error = data.get('error', '未知错误')
                    task['progress'] = '错误'
                    self.log_message(f"❌ 批量任务 {task_id} 错误: {error}", "error")

                self.update_batch_queue_display()

                # 如果当前显示的是窗口队列状态面板，自动刷新
                if hasattr(self, 'batch_current_panel') and self.batch_current_panel == "window_queue_status":
                    self.refresh_batch_window_queue_status()

                break

    def stop_batch_queue(self):
        """停止批量队列"""
        # TODO: 实现停止逻辑
        if messagebox.askyesno("确认", "确定要停止批量任务队列吗？"):
            self.log_message("⏹️ 批量任务已停止", "warning")

    def clear_batch_queue(self):
        """清空批量队列"""
        if messagebox.askyesno("确认", "确定要清空批量任务队列吗？"):
            self.batch_tasks.clear()
            self.update_batch_queue_display()
            self.start_batch_btn.configure(state="disabled")
            self.stop_batch_btn.configure(state="disabled")
            self.clear_batch_btn.configure(state="disabled")
            self.log_message("🗑️ 批量任务队列已清空", "info")

    # ==================== 批量任务方法结束 ====================

    def on_closing(self):
        """窗口关闭时的处理"""
        # 保存配置
        self.save_config()

        # 停止所有任务
        for task_id, task_info in self.threads.items():
            if task_info['status'] == 'running' and 'automation' in task_info:
                task_info['automation'].stop_task()

        # 关闭窗口
        self.destroy()


def main():
    """主函数"""
    app = WhiskGUIV3()

    # 绑定关闭事件
    app.protocol("WM_DELETE_WINDOW", app.on_closing)

    # 运行主循环
    app.mainloop()


if __name__ == "__main__":
    main()
