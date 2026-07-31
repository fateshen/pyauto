# core/__init__.py
"""
Core 模块
提供游戏自动化核心功能
"""

import sys
from importlib import import_module
from pathlib import Path

# 将项目根目录添加到 sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


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


_懒加载导出 = {
    '运行时公共变量': ('core.runtime_state', '运行时公共变量'),
    '切换操作基类': ('core.page_switcher', '切换操作基类'),
    '点击文字切换': ('core.page_switcher', '点击文字切换'),
    '点击图片切换': ('core.page_switcher', '点击图片切换'),
    '点击坐标切换': ('core.page_switcher', '点击坐标切换'),
    '切换操作工厂': ('core.page_switcher', '切换操作工厂'),
    '点击类型枚举': ('core.page_switcher', '点击类型枚举'),
    '验证类型枚举': ('core.page_switcher', '验证类型枚举'),
    '窗口线程': ('core.window_thread', '窗口线程'),
    'ActionExecutor': ('core.action_executor', 'ActionExecutor'),
    'capture_window': ('core.window_manager', 'capture_window'),
}


def __getattr__(名称):
    """按需加载平台相关组件，允许独立使用跨平台核心模块。"""

    if 名称 not in _懒加载导出:
        raise AttributeError(f"module {__name__!r} has no attribute {名称!r}")
    模块名, 属性名 = _懒加载导出[名称]
    属性 = getattr(import_module(模块名), 属性名)
    globals()[名称] = 属性
    return 属性


def __dir__():
    return sorted(set(globals()) | set(__all__))
