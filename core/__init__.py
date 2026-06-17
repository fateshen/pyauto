# core/__init__.py
"""
Core 模块
提供游戏自动化核心功能
"""

import sys
from pathlib import Path

# 将项目根目录添加到 sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


from core.runtime_state import 运行时公共变量
from core.page_switcher import (
    切换操作基类,
    点击文字切换,
    点击图片切换,
    点击坐标切换,
    切换操作工厂,
    点击类型枚举,
    验证类型枚举
)

from core.window_thread import 窗口线程
from core.action_executor import ActionExecutor
from core.window_manager import capture_window

__all__ = [
    '运行时公共变量',
    '切换操作基类',
    '点击文字切换',
    '点击图片切换',
    '点击坐标切换',
    '切换操作工厂',
    '点击类型枚举',
    '验证类型枚举',
    '窗口线程',
    'ActionExecutor',
    'capture_window'
]