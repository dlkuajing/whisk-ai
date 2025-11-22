#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量任务队列对话框
用于管理和配置多个任务的队列执行
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
from pathlib import Path

class TaskQueueDialog:
    """任务队列管理对话框"""

    def __init__(self, parent, browser_id_map, config):
        self.parent = parent
        self.browser_id_map = browser_id_map
        self.config = config

        # 任务队列
        self.task_queue = []

        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("批量任务队列")
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)

        # 设置样式
        self.style = ttk.Style()

        # 创建界面
        self.create_widgets()

        # 加载保存的队列（如果有）
        self.load_saved_queue()

        # 居中窗口
        self.center_window()

        # 设置为模态对话框
        self.dialog.grab_set()

    def center_window(self):
        """窗口居中"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'+{x}+{y}')

    def create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # 标题
        title_label = ttk.Label(main_frame, text="批量任务队列管理",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # 左侧：任务配置区
        config_frame = ttk.LabelFrame(main_frame, text="添加任务", padding="10")
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        row = 0

        # 任务名称
        ttk.Label(config_frame, text="任务名称:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.task_name_var = tk.StringVar(value="任务1")
        ttk.Entry(config_frame, textvariable=self.task_name_var, width=25).grid(
            row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        row += 1

        # 提示词
        ttk.Label(config_frame, text="提示词:").grid(row=row, column=0, sticky=(tk.W, tk.N), pady=2)
        self.prompt_text = scrolledtext.ScrolledText(config_frame, height=4, width=30, wrap=tk.WORD)
        self.prompt_text.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        row += 1

        # 纵横比
        ttk.Label(config_frame, text="纵横比:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.ratio_var = tk.StringVar(value="1:1")
        ratio_combo = ttk.Combobox(config_frame, textvariable=self.ratio_var,
                                  values=["1:1", "4:3", "3:4", "16:9", "9:16"],
                                  state="readonly", width=22)
        ratio_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        row += 1

        # 生成数量
        ttk.Label(config_frame, text="生成数量:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.count_var = tk.IntVar(value=2)
        count_spinbox = ttk.Spinbox(config_frame, from_=1, to=50, textvariable=self.count_var, width=23)
        count_spinbox.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        row += 1

        # 添加按钮
        add_frame = ttk.Frame(config_frame)
        add_frame.grid(row=row, column=0, columnspan=2, pady=10)

        ttk.Button(add_frame, text="添加到队列", command=self.add_to_queue,
                  style="Accent.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(add_frame, text="清空输入", command=self.clear_input).pack(side=tk.LEFT, padx=2)
        row += 1

        # 分隔线
        ttk.Separator(config_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1

        # 批量导入区域
        batch_label = ttk.Label(config_frame, text="批量导入提示词", font=("Arial", 10, "bold"))
        batch_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        row += 1

        ttk.Label(config_frame, text="每行一个提示词:").grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        row += 1

        self.batch_text = scrolledtext.ScrolledText(config_frame, height=6, width=30, wrap=tk.WORD)
        self.batch_text.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        row += 1

        # 批量设置
        batch_settings_frame = ttk.Frame(config_frame)
        batch_settings_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(batch_settings_frame, text="统一纵横比:").pack(side=tk.LEFT)
        self.batch_ratio_var = tk.StringVar(value="1:1")
        ttk.Combobox(batch_settings_frame, textvariable=self.batch_ratio_var,
                    values=["1:1", "4:3", "3:4", "16:9", "9:16"],
                    state="readonly", width=8).pack(side=tk.LEFT, padx=(5, 10))

        ttk.Label(batch_settings_frame, text="数量:").pack(side=tk.LEFT)
        self.batch_count_var = tk.IntVar(value=2)
        ttk.Spinbox(batch_settings_frame, from_=1, to=50, textvariable=self.batch_count_var,
                   width=5).pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        ttk.Button(config_frame, text="批量添加", command=self.batch_add_to_queue).grid(
            row=row, column=0, columnspan=2, pady=5)

        # 右侧：任务队列显示
        queue_frame = ttk.LabelFrame(main_frame, text="任务队列", padding="10")
        queue_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        queue_frame.columnconfigure(0, weight=1)
        queue_frame.rowconfigure(0, weight=1)

        # 队列列表
        columns = ('任务名', '提示词', '比例', '数量')
        self.queue_tree = ttk.Treeview(queue_frame, columns=columns, show='tree headings', height=15)

        # 设置列
        self.queue_tree.column('#0', width=50, minwidth=50)
        self.queue_tree.column('任务名', width=100, minwidth=80)
        self.queue_tree.column('提示词', width=200, minwidth=150)
        self.queue_tree.column('比例', width=60, minwidth=60)
        self.queue_tree.column('数量', width=60, minwidth=60)

        # 设置标题
        self.queue_tree.heading('#0', text='序号')
        for col in columns:
            self.queue_tree.heading(col, text=col)

        # 滚动条
        queue_scrollbar = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=queue_scrollbar.set)

        self.queue_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        queue_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # 队列操作按钮
        queue_btn_frame = ttk.Frame(queue_frame)
        queue_btn_frame.grid(row=1, column=0, columnspan=2, pady=10)

        # 使用Unicode转义序列确保兼容性
        ttk.Button(queue_btn_frame, text="\u4e0a\u79fb", command=self.move_up).pack(side=tk.LEFT, padx=2)  # 上移
        ttk.Button(queue_btn_frame, text="\u4e0b\u79fb", command=self.move_down).pack(side=tk.LEFT, padx=2)  # 下移
        ttk.Button(queue_btn_frame, text="\u7f16\u8f91", command=self.edit_task).pack(side=tk.LEFT, padx=2)  # 编辑
        ttk.Button(queue_btn_frame, text="\u5220\u9664", command=self.delete_task).pack(side=tk.LEFT, padx=2)  # 删除
        ttk.Button(queue_btn_frame, text="\u6e05\u7a7a\u961f\u5217", command=self.clear_queue).pack(side=tk.LEFT, padx=10)  # 清空队列

        # 队列统计
        self.queue_stats_label = ttk.Label(queue_frame, text="队列中有 0 个任务", foreground="blue")
        self.queue_stats_label.grid(row=2, column=0, columnspan=2, pady=5)

        # 底部：选择浏览器和操作按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))

        # 浏览器选择
        browser_frame = ttk.Frame(bottom_frame)
        browser_frame.pack(side=tk.TOP, pady=10)

        ttk.Label(browser_frame, text="选择执行浏览器:").pack(side=tk.LEFT, padx=(0, 10))
        self.browser_var = tk.StringVar()
        browser_combo = ttk.Combobox(browser_frame, textvariable=self.browser_var,
                                    values=list(self.browser_id_map.keys()),
                                    state="readonly", width=30)
        browser_combo.pack(side=tk.LEFT)

        # 设置默认浏览器
        if self.browser_id_map:
            browser_combo.set(list(self.browser_id_map.keys())[0])

        # 保存目录设置
        save_frame = ttk.Frame(bottom_frame)
        save_frame.pack(side=tk.TOP, pady=5)

        ttk.Label(save_frame, text="保存目录:").pack(side=tk.LEFT, padx=(0, 10))
        self.save_dir_var = tk.StringVar(value=self.config.get('save_directory', './downloads'))
        ttk.Entry(save_frame, textvariable=self.save_dir_var, width=40).pack(side=tk.LEFT)

        # 执行选项
        options_frame = ttk.Frame(bottom_frame)
        options_frame.pack(side=tk.TOP, pady=10)

        self.create_folders_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="为每个任务创建独立文件夹",
                       variable=self.create_folders_var).pack(side=tk.LEFT, padx=10)

        # 操作按钮
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(side=tk.TOP, pady=10)

        ttk.Button(button_frame, text="保存队列", command=self.save_queue).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="加载队列", command=self.load_queue).pack(side=tk.LEFT, padx=5)

        ttk.Separator(button_frame, orient='vertical').pack(side=tk.LEFT, padx=10, fill=tk.Y)

        self.execute_btn = ttk.Button(button_frame, text="开始执行队列",
                                     command=self.execute_queue,
                                     style="Accent.TButton")
        self.execute_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.LEFT, padx=5)

    def add_to_queue(self):
        """添加任务到队列"""
        task_name = self.task_name_var.get().strip()
        prompt = self.prompt_text.get(1.0, tk.END).strip()

        if not task_name:
            messagebox.showwarning("警告", "请输入任务名称")
            return

        if not prompt:
            messagebox.showwarning("警告", "请输入提示词")
            return

        # 创建任务
        task = {
            'task_name': task_name,
            'prompt': prompt,
            'aspect_ratio': self.ratio_var.get(),
            'count': self.count_var.get()
        }

        # 添加到队列
        self.task_queue.append(task)

        # 更新显示
        self.update_queue_display()

        # 清空输入（准备下一个）
        self.task_name_var.set(f"任务{len(self.task_queue) + 1}")
        self.prompt_text.delete(1.0, tk.END)

        # 提示
        self.queue_stats_label.config(text=f"已添加: {task_name}")

    def batch_add_to_queue(self):
        """批量添加任务到队列"""
        batch_text = self.batch_text.get(1.0, tk.END).strip()
        if not batch_text:
            messagebox.showwarning("警告", "请输入批量提示词，每行一个")
            return

        # 分割提示词
        prompts = [line.strip() for line in batch_text.split('\n') if line.strip()]

        if not prompts:
            messagebox.showwarning("警告", "没有有效的提示词")
            return

        # 批量添加
        ratio = self.batch_ratio_var.get()
        count = self.batch_count_var.get()

        for i, prompt in enumerate(prompts, 1):
            task = {
                'task_name': f"批量任务{len(self.task_queue) + 1}",
                'prompt': prompt,
                'aspect_ratio': ratio,
                'count': count
            }
            self.task_queue.append(task)

        # 更新显示
        self.update_queue_display()

        # 清空批量输入
        self.batch_text.delete(1.0, tk.END)

        # 提示
        messagebox.showinfo("成功", f"已添加 {len(prompts)} 个任务到队列")

    def clear_input(self):
        """清空输入"""
        self.task_name_var.set(f"任务{len(self.task_queue) + 1}")
        self.prompt_text.delete(1.0, tk.END)

    def update_queue_display(self):
        """更新队列显示"""
        # 清空现有显示
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)

        # 添加任务
        for idx, task in enumerate(self.task_queue, 1):
            prompt_display = task['prompt'][:50] + "..." if len(task['prompt']) > 50 else task['prompt']
            self.queue_tree.insert('', 'end', text=str(idx), values=(
                task['task_name'],
                prompt_display,
                task['aspect_ratio'],
                task['count']
            ))

        # 更新统计
        total_images = sum(task['count'] * 2 for task in self.task_queue)
        self.queue_stats_label.config(text=f"队列中有 {len(self.task_queue)} 个任务，预计生成 {total_images} 张图片")

    def move_up(self):
        """上移任务"""
        selection = self.queue_tree.selection()
        if not selection:
            return

        item = selection[0]
        index = self.queue_tree.index(item)

        if index > 0:
            # 交换任务
            self.task_queue[index], self.task_queue[index-1] = self.task_queue[index-1], self.task_queue[index]
            self.update_queue_display()

            # 重新选中
            new_items = self.queue_tree.get_children()
            if index-1 < len(new_items):
                self.queue_tree.selection_set(new_items[index-1])

    def move_down(self):
        """下移任务"""
        selection = self.queue_tree.selection()
        if not selection:
            return

        item = selection[0]
        index = self.queue_tree.index(item)

        if index < len(self.task_queue) - 1:
            # 交换任务
            self.task_queue[index], self.task_queue[index+1] = self.task_queue[index+1], self.task_queue[index]
            self.update_queue_display()

            # 重新选中
            new_items = self.queue_tree.get_children()
            if index+1 < len(new_items):
                self.queue_tree.selection_set(new_items[index+1])

    def edit_task(self):
        """编辑任务"""
        selection = self.queue_tree.selection()
        if not selection:
            return

        item = selection[0]
        index = self.queue_tree.index(item)
        task = self.task_queue[index]

        # 填充到输入框
        self.task_name_var.set(task['task_name'])
        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(1.0, task['prompt'])
        self.ratio_var.set(task['aspect_ratio'])
        self.count_var.set(task['count'])

        # 删除原任务
        del self.task_queue[index]
        self.update_queue_display()

        messagebox.showinfo("提示", "任务已加载到输入框，请修改后重新添加")

    def delete_task(self):
        """删除任务"""
        selection = self.queue_tree.selection()
        if not selection:
            return

        if messagebox.askyesno("确认", "确定要删除选中的任务吗？"):
            item = selection[0]
            index = self.queue_tree.index(item)
            del self.task_queue[index]
            self.update_queue_display()

    def clear_queue(self):
        """清空队列"""
        if self.task_queue and messagebox.askyesno("确认", "确定要清空整个队列吗？"):
            self.task_queue.clear()
            self.update_queue_display()

    def save_queue(self):
        """保存队列到文件"""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="task_queue.json"
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.task_queue, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", f"队列已保存到 {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")

    def load_queue(self):
        """从文件加载队列"""
        from tkinter import filedialog

        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    loaded_queue = json.load(f)

                if isinstance(loaded_queue, list):
                    self.task_queue = loaded_queue
                    self.update_queue_display()
                    messagebox.showinfo("成功", f"已加载 {len(loaded_queue)} 个任务")
                else:
                    messagebox.showerror("错误", "文件格式不正确")
            except Exception as e:
                messagebox.showerror("错误", f"加载失败: {str(e)}")

    def save_saved_queue(self):
        """保存队列到临时文件（自动保存）"""
        try:
            queue_file = Path("temp_queue.json")
            with open(queue_file, 'w', encoding='utf-8') as f:
                json.dump(self.task_queue, f, ensure_ascii=False, indent=2)
        except:
            pass

    def load_saved_queue(self):
        """加载临时保存的队列"""
        try:
            queue_file = Path("temp_queue.json")
            if queue_file.exists():
                with open(queue_file, 'r', encoding='utf-8') as f:
                    self.task_queue = json.load(f)
                    self.update_queue_display()
        except:
            pass

    def execute_queue(self):
        """执行队列"""
        if not self.task_queue:
            messagebox.showwarning("警告", "队列为空，请先添加任务")
            return

        browser = self.browser_var.get()
        if not browser:
            messagebox.showwarning("警告", "请选择执行浏览器")
            return

        # 保存队列（以防崩溃）
        self.save_saved_queue()

        # 返回执行信息
        self.result = {
            'browser': browser,
            'browser_id': self.browser_id_map[browser],
            'task_queue': self.task_queue.copy(),
            'save_directory': self.save_dir_var.get(),
            'create_folders': self.create_folders_var.get()
        }

        self.dialog.destroy()

    def cancel(self):
        """取消"""
        self.result = None
        self.dialog.destroy()

    def get_result(self):
        """获取结果"""
        return getattr(self, 'result', None)