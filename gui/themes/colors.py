#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨海帆-Imager V3 - 颜色系统配置
定义全局颜色变量和主题配置
主题：深海探索风 - 专业、可靠、探索、创新
"""

# ============================================================================
# 主色调系统 - 深海探索风
# ============================================================================

# 主色调 - 深海蓝（专业、信任、科技）
PRIMARY_COLOR = "#1E88E5"           # 主按钮、链接、品牌标识
PRIMARY_HOVER = "#1976D2"           # 主色悬停
PRIMARY_LIGHT = "#42A5F5"           # 主色浅色
PRIMARY_DARK = "#1565C0"            # 主色深色

# 辅助色 - 海洋青（清新、创新、和谐）
SECONDARY_COLOR = "#26A69A"         # 次要按钮、成功状态
SECONDARY_HOVER = "#00897B"         # 辅助色悬停
SECONDARY_LIGHT = "#4DB6AC"         # 辅助色浅色
SECONDARY_DARK = "#00695C"          # 辅助色深色

# 强调色 - 航海金（温暖、引导、重点）
ACCENT_COLOR = "#FFA726"            # 重要操作、强调按钮
ACCENT_HOVER = "#FB8C00"            # 强调色悬停
ACCENT_LIGHT = "#FFB74D"            # 强调色浅色
ACCENT_DARK = "#F57C00"             # 强调色深色

# 功能色
SUCCESS_COLOR = "#26A69A"           # 成功状态 - 海洋青（统一主题）
SUCCESS_HOVER = "#00897B"
SUCCESS_LIGHT = "#4DB6AC"

WARNING_COLOR = "#FFA726"           # 警告状态 - 航海金（温暖友好）
WARNING_HOVER = "#FB8C00"
WARNING_LIGHT = "#FFB74D"

ERROR_COLOR = "#EF5350"             # 错误状态 - 珊瑚红（醒目不刺眼）
ERROR_HOVER = "#E53935"
ERROR_LIGHT = "#EF5350"

INFO_COLOR = "#42A5F5"              # 信息提示 - 天空蓝（清晰明快）
INFO_HOVER = "#1E88E5"

# 窗口队列专用色
QUEUE_COLOR = "#7E57C2"             # 队列模式标识 - 深紫色（沉稳专业）
QUEUE_HOVER = "#673AB7"
QUEUE_LIGHT = "#9575CD"

# ============================================================================
# 背景色系统
# ============================================================================

# 浅色主题背景（深海探索风 - 清爽专业）
BG_LIGHT_PRIMARY = "#FAFBFC"        # 主背景（更柔和）
BG_LIGHT_SECONDARY = "#F4F6F8"      # 次级背景（淡雅灰）
BG_LIGHT_TERTIARY = "#E8EAED"       # 三级背景（卡片边框等）
BG_LIGHT_HOVER = "#EEF1F4"          # 悬停背景

# 深色主题背景
BG_DARK_PRIMARY = "#1E1E1E"         # 主背景
BG_DARK_SECONDARY = "#2C2C2C"       # 次级背景
BG_DARK_TERTIARY = "#3A3A3A"        # 三级背景
BG_DARK_HOVER = "#333333"           # 悬停背景

# ============================================================================
# 文本色系统
# ============================================================================

# 浅色主题文本（深海探索风 - 清晰易读）
TEXT_LIGHT_PRIMARY = "#263238"      # 主文本（更深邃）
TEXT_LIGHT_SECONDARY = "#546E7A"    # 次要文本（海洋灰）
TEXT_LIGHT_TERTIARY = "#78909C"     # 三级文本（提示等）
TEXT_LIGHT_DISABLED = "#B0BEC5"     # 禁用文本

# 深色主题文本
TEXT_DARK_PRIMARY = "#FFFFFF"       # 主文本
TEXT_DARK_SECONDARY = "#B0B0B0"     # 次要文本
TEXT_DARK_TERTIARY = "#808080"      # 三级文本
TEXT_DARK_DISABLED = "#606060"      # 禁用文本

# ============================================================================
# 边框和分割线
# ============================================================================

BORDER_LIGHT = "#E1E8ED"            # 浅色主题边框
BORDER_DARK = "#404040"             # 深色主题边框
DIVIDER_LIGHT = "#ECF0F1"           # 浅色分割线
DIVIDER_DARK = "#3A3A3A"            # 深色分割线

# ============================================================================
# 状态指示色 - 深海探索风
# ============================================================================

# 任务状态色（统一主题风格）
STATUS_PENDING = "#78909C"          # 待执行 - 海洋灰
STATUS_RUNNING = "#26A69A"          # 运行中 - 海洋青（象征创作进行中）
STATUS_COMPLETED = "#2E7D32"        # 已完成 - 深绿色（成功达成）
STATUS_FAILED = "#EF5350"           # 失败 - 珊瑚红（需要关注）
STATUS_STOPPED = "#FFA726"          # 已停止 - 航海金（温暖提醒）
STATUS_QUEUE = "#7E57C2"            # 排队中 - 深紫色（沉稳等待）

# ============================================================================
# 进度条色 - 深海探索风
# ============================================================================

PROGRESS_BG_LIGHT = "#E8EAED"       # 进度条背景（浅色）
PROGRESS_BG_DARK = "#3A3A3A"        # 进度条背景（深色）
PROGRESS_FILL = "#1E88E5"           # 进度条填充 - 深海蓝
PROGRESS_SUCCESS = "#26A69A"        # 完成进度条 - 海洋青

# ============================================================================
# CustomTkinter 主题配置
# ============================================================================

# 浅色主题配置
LIGHT_THEME = {
    "CTk": {
        "fg_color": [BG_LIGHT_PRIMARY, BG_DARK_PRIMARY]
    },
    "CTkFrame": {
        "fg_color": [BG_LIGHT_SECONDARY, BG_DARK_SECONDARY],
        "border_color": [BORDER_LIGHT, BORDER_DARK]
    },
    "CTkButton": {
        "fg_color": [PRIMARY_COLOR, PRIMARY_COLOR],
        "hover_color": [PRIMARY_HOVER, PRIMARY_HOVER],
        "border_color": [PRIMARY_COLOR, PRIMARY_COLOR],
        "text_color": ["#FFFFFF", "#FFFFFF"]
    },
    "CTkLabel": {
        "text_color": [TEXT_LIGHT_PRIMARY, TEXT_DARK_PRIMARY]
    },
    "CTkEntry": {
        "fg_color": [BG_LIGHT_PRIMARY, BG_DARK_TERTIARY],
        "border_color": [BORDER_LIGHT, BORDER_DARK],
        "text_color": [TEXT_LIGHT_PRIMARY, TEXT_DARK_PRIMARY]
    },
    "CTkProgressBar": {
        "fg_color": [PROGRESS_BG_LIGHT, PROGRESS_BG_DARK],
        "progress_color": [PROGRESS_FILL, PROGRESS_FILL]
    }
}

# ============================================================================
# 自适应颜色（支持深色/浅色主题自动切换）
# ============================================================================

# 背景色自适应 [浅色, 深色]
ADAPTIVE_BG_PRIMARY = [BG_LIGHT_PRIMARY, BG_DARK_PRIMARY]
ADAPTIVE_BG_SECONDARY = [BG_LIGHT_SECONDARY, BG_DARK_SECONDARY]
ADAPTIVE_BG_TERTIARY = [BG_LIGHT_TERTIARY, BG_DARK_TERTIARY]
ADAPTIVE_BG_HOVER = [BG_LIGHT_HOVER, BG_DARK_HOVER]

# 文本色自适应 [浅色, 深色]
ADAPTIVE_TEXT_PRIMARY = [TEXT_LIGHT_PRIMARY, TEXT_DARK_PRIMARY]
ADAPTIVE_TEXT_SECONDARY = [TEXT_LIGHT_SECONDARY, TEXT_DARK_SECONDARY]
ADAPTIVE_TEXT_TERTIARY = [TEXT_LIGHT_TERTIARY, TEXT_DARK_TERTIARY]
ADAPTIVE_TEXT_DISABLED = [TEXT_LIGHT_DISABLED, TEXT_DARK_DISABLED]

# 边框色自适应 [浅色, 深色]
ADAPTIVE_BORDER = [BORDER_LIGHT, BORDER_DARK]
ADAPTIVE_DIVIDER = [DIVIDER_LIGHT, DIVIDER_DARK]

# ============================================================================
# 辅助函数
# ============================================================================

def get_status_color(status: str) -> str:
    """根据任务状态返回对应颜色"""
    status_colors = {
        "准备中": STATUS_PENDING,
        "pending": STATUS_PENDING,
        "运行中": STATUS_RUNNING,
        "running": STATUS_RUNNING,
        "执行中": STATUS_RUNNING,
        "已完成": STATUS_COMPLETED,
        "completed": STATUS_COMPLETED,
        "完成": STATUS_COMPLETED,
        "失败": STATUS_FAILED,
        "failed": STATUS_FAILED,
        "错误": STATUS_FAILED,
        "已停止": STATUS_STOPPED,
        "stopped": STATUS_STOPPED,
        "停止中": STATUS_STOPPED,
        "排队中": STATUS_QUEUE,
        "queue": STATUS_QUEUE,
        "等待中": STATUS_QUEUE,
        "waiting": STATUS_QUEUE
    }
    return status_colors.get(status.lower(), STATUS_PENDING)


def get_status_emoji(status: str) -> str:
    """根据任务状态返回对应emoji"""
    status_emojis = {
        "准备中": "🔵",
        "pending": "🔵",
        "运行中": "🟢",
        "running": "🟢",
        "执行中": "🟢",
        "已完成": "✅",
        "completed": "✅",
        "完成": "✅",
        "失败": "❌",
        "failed": "❌",
        "错误": "❌",
        "已停止": "⏹️",
        "stopped": "⏹️",
        "停止中": "⏸️",
        "排队中": "🟣",
        "queue": "🟣",
        "等待中": "⏳",
        "waiting": "⏳"
    }
    return status_emojis.get(status.lower(), "⚪")


def hex_to_rgb(hex_color: str) -> tuple:
    """将十六进制颜色转换为RGB元组"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple) -> str:
    """将RGB元组转换为十六进制颜色"""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def lighten_color(hex_color: str, factor: float = 0.2) -> str:
    """使颜色变浅

    Args:
        hex_color: 十六进制颜色
        factor: 变浅因子 (0-1)，越大越浅
    """
    rgb = hex_to_rgb(hex_color)
    new_rgb = tuple(int(c + (255 - c) * factor) for c in rgb)
    return rgb_to_hex(new_rgb)


def darken_color(hex_color: str, factor: float = 0.2) -> str:
    """使颜色变深

    Args:
        hex_color: 十六进制颜色
        factor: 变深因子 (0-1)，越大越深
    """
    rgb = hex_to_rgb(hex_color)
    new_rgb = tuple(int(c * (1 - factor)) for c in rgb)
    return rgb_to_hex(new_rgb)
