#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
窗口任务队列管理模块
实现单窗口串行队列功能，支持动态添加任务和任务组（套图）管理
"""

import queue
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable
import logging


class TaskSession:
    """任务组/会话 - 管理一组相关任务的文件归档（套图功能）"""

    def __init__(self, session_name: str, base_dir: str):
        """
        初始化任务组

        Args:
            session_name: 任务组名称（例如："赛博朋克系列"）
            base_dir: 基础保存目录
        """
        self.session_name = session_name
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 套图顶层文件夹
        self.session_dir = Path(base_dir) / f"{session_name}_{self.session_id}"
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # 任务列表
        self.tasks = []
        self.task_counter = 0

        # 时间戳
        self.created_at = time.time()
        self.last_task_added_at = time.time()

    def add_task(self, task_params: dict) -> dict:
        """
        添加任务到组，为任务分配子文件夹

        Args:
            task_params: 任务参数字典

        Returns:
            更新后的任务参数（包含save_directory等）
        """
        self.task_counter += 1

        # 为任务分配子文件夹
        task_name = task_params.get('task_name', f'任务{self.task_counter}')
        # 清理任务名称，移除特殊字符
        import re
        clean_name = re.sub(r'[^\w\u4e00-\u9fff\-_]', '', task_name)

        task_dir = self.session_dir / f"{self.task_counter:02d}_{clean_name}"
        task_dir.mkdir(exist_ok=True)

        # 更新任务参数
        task_params['save_directory'] = str(task_dir)
        task_params['session_name'] = self.session_name
        task_params['session_id'] = self.session_id
        task_params['session_dir'] = str(self.session_dir)
        task_params['task_index_in_session'] = self.task_counter

        self.tasks.append(task_params)
        self.last_task_added_at = time.time()

        return task_params

    def get_idle_time(self) -> float:
        """获取空闲时间（秒）"""
        return time.time() - self.last_task_added_at

    def get_info(self) -> dict:
        """获取任务组信息"""
        return {
            'session_name': self.session_name,
            'session_id': self.session_id,
            'session_dir': str(self.session_dir),
            'task_count': self.task_counter,
            'created_at': self.created_at,
            'last_task_added_at': self.last_task_added_at,
            'idle_time': self.get_idle_time()
        }


class WindowTaskQueue:
    """单个浏览器窗口的持久化任务队列"""

    def __init__(self, browser_id: str, browser_name: str,
                 gui_callback: Optional[Callable] = None,
                 config: Optional[dict] = None):
        """
        初始化窗口任务队列

        Args:
            browser_id: 比特浏览器ID
            browser_name: 浏览器显示名称
            gui_callback: GUI回调函数，用于通知GUI更新
            config: 配置参数
        """
        self.browser_id = browser_id
        self.browser_name = browser_name
        self.gui_callback = gui_callback or (lambda *args: None)

        # 任务队列（线程安全）
        self.task_queue = queue.Queue()
        self.current_task = None

        # 工作线程
        self.worker_thread = None
        self.is_running = False
        self.should_stop = False

        # 自动化实例（保持连接）
        self.automation = None
        self.connected = False

        # 任务组管理
        self.current_session = None  # 当前活跃的任务组
        self.sessions = {}  # session_id -> TaskSession

        # 配置
        config = config or {}
        self.idle_timeout = config.get('idle_timeout', 300)  # 5分钟无任务则断开
        self.session_auto_close_timeout = config.get('session_timeout', 600)  # 10分钟自动结束任务组
        self.use_enhanced_download = config.get('use_enhanced_download', True)
        self.min_delay = config.get('min_delay', 5)
        self.max_delay = config.get('max_delay', 8)

        # 重试配置
        self.max_connect_retries = 3  # 最大重试次数
        self.retry_delays = [2, 5, 10]  # 重试延迟（秒）

        # 统计信息
        self.completed_count = 0
        self.failed_count = 0
        self.total_tasks_added = 0

        # 线程锁
        self.lock = threading.Lock()

        # 任务取消管理
        self.cancelled_task_ids = set()  # 被取消的任务ID集合
        self.cancel_current_task = False  # 当前任务是否被手动取消

    def add_task(self, task_params: dict, session_mode: str = 'independent',
                 session_name: Optional[str] = None) -> bool:
        """
        添加任务到队列

        Args:
            task_params: 任务参数字典，必须包含：
                - prompt: 提示词
                - count: 生成数量
                - aspect_ratio: 纵横比
                - task_name: 任务名称
                - base_save_dir: 基础保存目录
            session_mode: 会话模式
                - 'independent': 独立任务，创建独立文件夹
                - 'join_current': 加入当前任务组
                - 'new_session': 创建新任务组
            session_name: 新任务组名称（仅当session_mode='new_session'时需要）

        Returns:
            是否成功添加
        """
        try:
            # 检查是否需要自动结束当前任务组
            if self.current_session and session_mode != 'join_current':
                idle_time = self.current_session.get_idle_time()
                if idle_time > self.session_auto_close_timeout:
                    self.close_current_session()

            # 根据模式处理任务
            if session_mode == 'independent':
                # 独立任务：创建独立文件夹
                task_params = self._prepare_independent_task(task_params)

            elif session_mode == 'join_current':
                # 加入当前组
                if not self.current_session:
                    raise ValueError("没有活跃的任务组，无法加入")
                task_params = self.current_session.add_task(task_params)

            elif session_mode == 'new_session':
                # 创建新组
                if not session_name:
                    session_name = task_params.get('session_name', '新套图')
                self.create_session(session_name, task_params['base_save_dir'])
                task_params = self.current_session.add_task(task_params)
            else:
                raise ValueError(f"未知的session_mode: {session_mode}")

            # 添加到队列
            with self.lock:
                self.task_queue.put(task_params)
                self.total_tasks_added += 1

            # 通知GUI
            self.gui_callback('task_added', self.browser_id, task_params)

            # 如果工作线程未启动，启动它
            if not self.is_running:
                self.start_worker()

            return True

        except Exception as e:
            logging.error(f"添加任务失败: {e}")
            self.gui_callback('error', self.browser_id, str(e))
            return False

    def _prepare_independent_task(self, task_params: dict) -> dict:
        """准备独立任务的保存路径"""
        task_name = task_params.get('task_name', 'task')
        # 清理任务名称
        import re
        clean_name = re.sub(r'[^\w\u4e00-\u9fff\-_]', '', task_name)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        task_dir = Path(task_params['base_save_dir']) / f"{clean_name}_{timestamp}"
        task_dir.mkdir(parents=True, exist_ok=True)

        task_params['save_directory'] = str(task_dir)
        task_params['is_independent'] = True

        return task_params

    def create_session(self, session_name: str, base_dir: str) -> TaskSession:
        """创建新的任务组"""
        # 关闭当前任务组（如果有）
        if self.current_session:
            self.close_current_session()

        # 创建新任务组
        self.current_session = TaskSession(session_name, base_dir)
        self.sessions[self.current_session.session_id] = self.current_session

        # 通知GUI
        self.gui_callback('session_created', self.browser_id, self.current_session.get_info())

        return self.current_session

    def close_current_session(self):
        """结束当前任务组"""
        if self.current_session:
            # 通知GUI
            self.gui_callback('session_closed', self.browser_id, self.current_session.get_info())
            self.current_session = None

    def start_worker(self):
        """启动工作线程"""
        with self.lock:
            if self.worker_thread and self.worker_thread.is_alive():
                return

            self.is_running = True
            self.should_stop = False

        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name=f"WindowQueue-{self.browser_id}"
        )
        self.worker_thread.start()

        # 通知GUI
        self.gui_callback('worker_started', self.browser_id, None)

    def _worker_loop(self):
        """工作线程主循环"""
        try:
            # 连接浏览器（使用重试机制）
            self._connect_browser_with_retry()

            while not self.should_stop:
                try:
                    # 从队列获取任务（带超时）
                    task = self.task_queue.get(timeout=self.idle_timeout)

                    with self.lock:
                        # 检查任务是否被取消
                        task_id = task.get('task_id', '')
                        if task_id in self.cancelled_task_ids:
                            self.cancelled_task_ids.remove(task_id)
                            self.gui_callback('task_cancelled', self.browser_id, task)
                            self.task_queue.task_done()
                            continue  # 跳过这个任务，继续下一个

                        self.current_task = task
                        self.cancel_current_task = False  # 重置取消标志

                    # 通知GUI任务开始
                    self.gui_callback('task_start', self.browser_id, task)

                    # 执行任务
                    success = self._execute_task(task)

                    with self.lock:
                        # 检查是否被手动取消
                        if self.cancel_current_task:
                            # 手动取消，不算失败
                            self.gui_callback('task_cancelled', self.browser_id, task)
                        elif success:
                            self.completed_count += 1
                            self.gui_callback('task_complete', self.browser_id, task)
                        else:
                            self.failed_count += 1
                            self.gui_callback('task_failed', self.browser_id, task)

                except queue.Empty:
                    # 超时无任务，断开连接并退出
                    self.gui_callback('idle_timeout', self.browser_id, None)
                    break

                except Exception as e:
                    logging.error(f"任务执行异常: {e}")
                    with self.lock:
                        # 区分取消和失败
                        if not self.cancel_current_task:
                            self.failed_count += 1
                            if self.current_task:
                                self.gui_callback('task_failed', self.browser_id, self.current_task)
                        # 如果是取消，前面已经回调过了
                    self.gui_callback('task_error', self.browser_id, str(e))

                finally:
                    with self.lock:
                        self.current_task = None
                        self.cancel_current_task = False  # 重置标志
                    self.task_queue.task_done()

        except Exception as e:
            # 浏览器连接失败（重试后仍失败）
            logging.error(f"工作线程启动失败: {e}")
            self.gui_callback('worker_start_failed', self.browser_id, str(e))

            # 将所有排队中的任务标记为失败
            self._mark_all_queued_tasks_as_failed()

        finally:
            self._cleanup()
            with self.lock:
                self.is_running = False
            self.gui_callback('worker_stopped', self.browser_id, None)

    def _connect_browser_with_retry(self):
        """带重试机制的浏览器连接"""
        last_error = None

        for attempt in range(1, self.max_connect_retries + 1):
            try:
                # 通知GUI正在尝试连接
                self.gui_callback('log', self.browser_id,
                    f"🔄 正在连接浏览器 (第 {attempt}/{self.max_connect_retries} 次尝试)...")

                # 尝试连接
                self._connect_browser()

                # 成功连接
                self.gui_callback('log', self.browser_id, "✅ 浏览器连接成功")
                return  # 成功则退出

            except Exception as e:
                last_error = e

                if attempt < self.max_connect_retries:
                    # 还有重试机会
                    delay = self.retry_delays[attempt - 1]
                    error_msg = str(e)[:50]  # 截取前50字符
                    self.gui_callback('log', self.browser_id,
                        f"⚠️ 连接失败: {error_msg}... | {delay}秒后重试")
                    time.sleep(delay)
                else:
                    # 最后一次重试也失败
                    self.gui_callback('log', self.browser_id,
                        f"❌ 浏览器连接失败（已重试 {self.max_connect_retries} 次）")
                    raise  # 抛出最后的异常

    def _connect_browser(self):
        """连接浏览器"""
        try:
            # 导入核心模块
            from whisk_core_v2 import WhiskAutomationCoreV2

            # 创建自动化实例（临时目录，后续每个任务会使用自己的目录）
            self.automation = WhiskAutomationCoreV2(
                browser_id=self.browser_id,
                save_directory="./temp",  # 临时目录
                message_callback=lambda msg: self.gui_callback('log', self.browser_id, msg),
                progress_callback=self._progress_callback,
                use_enhanced_download=self.use_enhanced_download
            )

            # 连接浏览器
            self.automation.connect_browser()
            self.connected = True

            self.gui_callback('browser_connected', self.browser_id, None)

        except Exception as e:
            logging.error(f"连接浏览器失败: {e}")
            self.gui_callback('connection_error', self.browser_id, str(e))
            raise

    def _execute_task(self, task: dict) -> bool:
        """执行单个任务"""
        try:
            if not self.automation or not self.connected:
                raise Exception("浏览器未连接")

            # 更新保存目录
            self.automation.save_directory = Path(task['save_directory'])
            self.automation.save_directory.mkdir(exist_ok=True, parents=True)

            # 如果不是第一个任务，重新打开页面
            if self.completed_count > 0 or self.failed_count > 0:
                self.automation.reopen_page()
                time.sleep(2)

            # 重置任务状态
            self.automation.reset_task_state()

            # 执行生成
            self.automation.generate_images(
                prompt=task['prompt'],
                count=task['count'],
                aspect_ratio=task['aspect_ratio'],
                min_delay=self.min_delay,
                max_delay=self.max_delay
            )

            return True

        except Exception as e:
            logging.error(f"执行任务失败: {e}")
            self.gui_callback('log', self.browser_id, f"任务执行失败: {e}")
            return False

    def _progress_callback(self, current, total, progress_type='generation'):
        """进度回调转发"""
        if self.current_task:
            self.gui_callback('task_progress', self.browser_id, {
                'task': self.current_task,
                'current': current,
                'total': total,
                'progress_type': progress_type
            })

    def _cleanup(self):
        """清理资源"""
        try:
            if self.automation:
                self.automation.cleanup()
            self.connected = False
            self.automation = None
        except Exception as e:
            logging.error(f"清理资源失败: {e}")

    def cancel_task(self, task_id: str) -> bool:
        """
        取消指定任务（改进版，避免重建Queue）

        Args:
            task_id: 要取消的任务ID

        Returns:
            True - 任务被标记为取消
            False - 任务未找到或已完成
        """
        with self.lock:
            # 情况1：正在执行的任务
            if self.current_task and self.current_task.get('task_id') == task_id:
                if self.automation:
                    self.automation.stop_task()
                self.cancel_current_task = True  # 设置取消标志
                self.gui_callback('log', self.browser_id, f"正在取消任务: {task_id}")
                return True

            # 情况2：在队列中等待的任务
            # 不重建Queue，而是标记为取消，让worker跳过
            self.cancelled_task_ids.add(task_id)

            # 立即通知GUI（乐观更新）
            self.gui_callback('log', self.browser_id, f"任务 {task_id} 已标记为取消，将在执行前跳过")
            return True

    def stop(self):
        """停止队列"""
        with self.lock:
            self.should_stop = True

        # 停止当前任务
        if self.automation:
            self.automation.stop_task()

        self.gui_callback('queue_stopping', self.browser_id, None)

    def clear_queue(self):
        """清空等待中的任务"""
        cleared_count = 0
        with self.lock:
            while not self.task_queue.empty():
                try:
                    self.task_queue.get_nowait()
                    cleared_count += 1
                except queue.Empty:
                    break

        self.gui_callback('queue_cleared', self.browser_id, cleared_count)
        return cleared_count

    def get_status(self) -> dict:
        """获取队列状态"""
        with self.lock:
            status = {
                'browser_id': self.browser_id,
                'browser_name': self.browser_name,
                'queue_size': self.task_queue.qsize(),
                'current_task': self.current_task,
                'is_running': self.is_running,
                'connected': self.connected,
                'completed_count': self.completed_count,
                'failed_count': self.failed_count,
                'total_tasks_added': self.total_tasks_added,
                'current_session': self.current_session.get_info() if self.current_session else None
            }
        return status

    def _mark_all_queued_tasks_as_failed(self):
        """将队列中所有等待任务标记为失败"""
        failed_tasks = []
        while not self.task_queue.empty():
            try:
                task = self.task_queue.get_nowait()
                failed_tasks.append(task)
                self.gui_callback('task_failed', self.browser_id, task)
                self.task_queue.task_done()
            except queue.Empty:
                break

        with self.lock:
            self.failed_count += len(failed_tasks)

        if failed_tasks:
            self.gui_callback('log', self.browser_id,
                f"❌ {len(failed_tasks)} 个排队任务因连接失败被取消")


class WindowQueueManager:
    """管理所有浏览器窗口的任务队列"""

    def __init__(self, gui_callback: Optional[Callable] = None, config: Optional[dict] = None):
        """
        初始化窗口队列管理器

        Args:
            gui_callback: GUI回调函数
            config: 全局配置
        """
        self.windows = {}  # browser_id -> WindowTaskQueue
        self.gui_callback = gui_callback or (lambda *args: None)
        self.config = config or {}
        self.lock = threading.Lock()

    def get_or_create_queue(self, browser_id: str, browser_name: str) -> WindowTaskQueue:
        """获取或创建窗口队列"""
        with self.lock:
            if browser_id not in self.windows:
                self.windows[browser_id] = WindowTaskQueue(
                    browser_id=browser_id,
                    browser_name=browser_name,
                    gui_callback=self.gui_callback,
                    config=self.config
                )
            return self.windows[browser_id]

    def add_task_to_window(self, browser_id: str, browser_name: str,
                          task_params: dict, session_mode: str = 'independent',
                          session_name: Optional[str] = None) -> bool:
        """
        添加任务到指定窗口

        Args:
            browser_id: 浏览器ID
            browser_name: 浏览器名称
            task_params: 任务参数
            session_mode: 会话模式
            session_name: 任务组名称

        Returns:
            是否成功添加
        """
        window_queue = self.get_or_create_queue(browser_id, browser_name)
        return window_queue.add_task(task_params, session_mode, session_name)

    def get_window_queue(self, browser_id: str) -> Optional[WindowTaskQueue]:
        """获取窗口队列"""
        with self.lock:
            return self.windows.get(browser_id)

    def cancel_task_in_window(self, browser_id: str, task_id: str) -> bool:
        """
        取消指定窗口的指定任务

        Args:
            browser_id: 浏览器ID
            task_id: 任务ID

        Returns:
            是否成功取消
        """
        with self.lock:
            if browser_id in self.windows:
                return self.windows[browser_id].cancel_task(task_id)
        return False

    def get_all_status(self) -> Dict[str, dict]:
        """获取所有窗口状态"""
        with self.lock:
            return {
                browser_id: queue.get_status()
                for browser_id, queue in self.windows.items()
            }

    def stop_window(self, browser_id: str):
        """停止指定窗口的队列"""
        with self.lock:
            if browser_id in self.windows:
                self.windows[browser_id].stop()

    def stop_all(self):
        """停止所有窗口队列"""
        with self.lock:
            for queue in self.windows.values():
                queue.stop()

    def clear_window_queue(self, browser_id: str) -> int:
        """清空指定窗口的等待任务"""
        with self.lock:
            if browser_id in self.windows:
                return self.windows[browser_id].clear_queue()
        return 0

    def remove_window(self, browser_id: str):
        """移除窗口队列（在停止后调用）"""
        with self.lock:
            if browser_id in self.windows:
                self.windows[browser_id].stop()
                del self.windows[browser_id]
