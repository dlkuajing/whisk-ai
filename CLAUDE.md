# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
WhiskAI V2 是一个Google Whisk AI图像生成自动化工具，使用Python开发，提供GUI界面和浏览器自动化功能。

**最新更新**：V2.1 - 新增窗口串行队列功能，支持同一浏览器窗口的任务动态排队执行，提升工作效率。

## Key Commands

### 开发运行
```bash
# 安装依赖
pip install -r requirements_v2.txt

# 运行应用
python whisk_launcher_v2.py
```

### 打包EXE
```bash
# 使用批处理脚本（推荐）
一键打包EXE.bat

# 或使用Python脚本
python build_exe_v2.py

# 或直接使用PyInstaller
pyinstaller whisk_v2.spec
```

## Architecture

### 核心模块结构
- **whisk_launcher_v2.py**: 应用启动器，处理路径和导入问题，是程序入口点
- **whisk_core_v2.py**: 包含`WhiskAutomationCoreV2`类，实现浏览器自动化核心逻辑
- **whisk_gui_v2.py**: 包含`WhiskGUIV2`类，实现Tkinter GUI界面
- **whisk_window_queue.py**: (V2.1新增) 窗口队列管理模块，实现单窗口串行任务队列
- **whisk_queue_dialog.py**: 批量任务队列对话框

### 关键类和功能
1. **WhiskAutomationCoreV2** (whisk_core_v2.py):
   - 使用Playwright控制浏览器
   - 处理图像生成和下载
   - 管理并发任务队列
   - 实现重试机制和错误处理

2. **WhiskGUIV2** (whisk_gui_v2.py):
   - 管理GUI窗口和控件
   - 处理用户输入和配置
   - 与核心自动化模块通信
   - 实现多线程任务管理

3. **WindowQueueManager** (whisk_window_queue.py, V2.1新增):
   - 全局管理所有窗口的任务队列
   - 提供统一的任务添加接口
   - 处理队列状态查询和控制

4. **WindowTaskQueue** (whisk_window_queue.py, V2.1新增):
   - 单个浏览器窗口的持久化任务队列
   - 维护浏览器连接复用
   - 工作线程自动处理队列任务

5. **TaskSession** (whisk_window_queue.py, V2.1新增):
   - 管理任务组（套图模式）
   - 处理文件归档结构
   - 跟踪任务组状态和超时

### 配置管理
- **config_gui_v2.json**: 存储用户设置（浏览器选择、提示词、纵横比等）
- 配置自动保存和加载机制在GUI模块中实现
- **V2.1新增配置项**:
  - `use_window_queue`: 是否启用窗口队列模式（默认: false）
  - `session_mode`: 任务归档模式 - "ask"(每次询问)/"independent"(总是独立)/"always_session"(总是套图)
  - `idle_timeout`: 队列空闲超时时间（秒，默认: 300）
  - `session_timeout`: 任务组自动结束超时（秒，默认: 600）

### 线程模型
- GUI运行在主线程
- 每个自动化任务运行在独立线程（传统模式）
- **V2.1窗口队列模式**: 每个窗口有独立的工作线程，自动处理队列中的任务
- 使用线程安全的队列进行任务管理
- 通过回调函数和消息队列更新GUI状态
- 任务间使用`reopen_page()`和`reset_task_state()`实现状态隔离

## Development Guidelines

### 修改自动化逻辑
- 主要修改`whisk_core_v2.py`中的`WhiskAutomationCoreV2`类
- 关注`run_automation()`方法实现主要流程
- 下载逻辑在`download_image()`方法中

### 修改GUI界面
- 编辑`whisk_gui_v2.py`中的`WhiskGUIV2`类
- 界面布局在`setup_ui()`方法中定义
- 事件处理在相应的callback方法中

### 窗口队列功能开发 (V2.1)
- **队列管理**: 修改`whisk_window_queue.py`中的队列逻辑
- **任务添加**: GUI中通过`add_task_to_queue()`方法添加队列任务
- **状态更新**: 通过`handle_queue_callback()`处理队列事件回调
- **TreeView映射**: 使用`self.queue_task_items`字典维护任务ID到TreeView项的映射
- **任务隔离**: 确保在`reset_task_state()`中清空`downloaded_urls`和`pre_generation_urls`
- **归档模式**:
  - `independent`: 每个任务独立文件夹
  - `join_current`: 加入当前任务组
  - `new_session`: 创建新任务组（套图）

### 打包注意事项
- 使用`whisk_v2.spec`文件配置打包参数
- 确保`datas`参数包含所有必要的配置文件
- 打包后测试路径处理是否正确（见launcher中的路径处理逻辑）

### 依赖管理
- 新增依赖需更新`requirements_v2.txt`
- Playwright需要额外安装浏览器：`playwright install chromium`
- 打包时PyInstaller会自动包含所有依赖

## Important Patterns

### 错误处理模式
```python
try:
    # 核心操作
    result = perform_operation()
except Exception as e:
    self.log_message(f"错误: {str(e)}")
    # 更新GUI状态
    if self.status_callback:
        self.status_callback("error", str(e))
```

### 线程通信模式
```python
# 从GUI启动任务
thread = threading.Thread(target=self.core.run_automation, args=(...))
thread.start()

# 核心模块回调GUI
if self.status_callback:
    self.status_callback("update", message)
```

### 配置保存模式
```python
# 保存配置
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config_data, f, ensure_ascii=False, indent=2)

# 加载配置
if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
```

### 窗口队列模式 (V2.1)
```python
# 添加任务到窗口队列
self.window_queue_manager.add_task_to_window(
    browser_id=browser_id,
    browser_name=browser_name,
    task_params=task_params,
    session_mode='join_current',  # 或 'independent', 'new_session'
    session_name='任务组名称'
)

# 队列回调处理
def handle_queue_callback(self, event_type, data):
    """处理窗口队列的所有事件回调"""
    if event_type == 'task_start':
        # 任务开始，更新UI
        self.message_queue.put(('queue_task_status', task_id, ('进度', '执行中')))
    elif event_type == 'task_progress':
        # 进度更新
        self.message_queue.put(('queue_task_progress', task_id, progress_text))

# TreeView映射管理
self.queue_task_items[task_id] = {
    'tree_item': tree_item,
    'browser_id': browser_id,
    'task_params': task_params
}
```

## V2.1 窗口队列功能详解

### 核心工作流
```
用户添加任务 → add_task_to_queue() → WindowQueueManager.add_task_to_window()
                                              ↓
                                        WindowTaskQueue.add_task()
                                              ↓
                                        加入Queue队列
                                              ↓
                                        WorkerThread自动获取
                                              ↓
                                        执行WhiskAutomationCoreV2
                                              ↓
                                        完成后继续下一个任务
```

### 任务归档结构
**独立任务模式**:
```
downloads/
 ├─ 任务A_20250121_100000/
 ├─ 任务B_20250121_100500/
 └─ 任务C_20250121_101000/
```

**套图模式（任务组）**:
```
downloads/
 └─ 赛博朋克系列_20250121_100000/
     ├─ 01_城市夜景/
     ├─ 02_人物肖像/
     └─ 03_科技元素/
```

### 向后兼容性
- 默认情况下窗口队列功能**禁用**（`use_window_queue: false`）
- 不勾选"启用窗口队列模式"时，保持传统独立任务行为
- 用户可自由选择使用传统模式或窗口队列模式

### 相关文档
- **窗口队列功能实现总结.md**: 技术实现详细说明
- **窗口队列功能测试指南.md**: 7个测试场景和使用指南
- **修复窗口队列进度显示.md**: 进度显示bug修复说明