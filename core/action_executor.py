# core/action_executor.py
"""
动作执行器
统一封装鼠标和键盘操作，提供频率限制、日志记录、异常处理
"""
import time
import logging
from typing import Optional, Tuple, Union
from enum import Enum, IntEnum
import win32gui
from core.debug import 调试器

# 修正导入路径：使用相对导入或完整路径
from core.window_manager import (
    capture_window, 
    capture_window_alt,
    VK,
    BackgroundKeyboard,
    BackgroundMouse,
    ForegroundKeyboard
)


class KeyboardMode(Enum):
    """键盘模式"""
    BACKGROUND = "background"  # 后台模式（PostMessage）
    FOREGROUND = "foreground"  # 前台模式（keybd_event，需要焦点）


class LogLevel(IntEnum):
    NONE = 0
    ERROR = 1
    SIMPLE = 2
    DETAIL = 3


class ActionExecutor:
    """
    动作执行器（完整版）
    
    特性：
    - 鼠标操作：始终后台（PostMessage）
    - 键盘操作：支持前台/后台两种模式
    - 可配置日志级别
    - 内置频率限制
    """
    
    def __init__(self, 
                 hwnd: int,
                 keyboard_mode: KeyboardMode = KeyboardMode.FOREGROUND,
                 auto_activate: bool = True,
                 min_interval: float = 0.05,
                 log_level: LogLevel = LogLevel.SIMPLE,
                 enable_stats: bool = True):
        """
        初始化动作执行器
        
        参数:
            hwnd: 目标窗口句柄
            keyboard_mode: 键盘模式（前台/后台）
            auto_activate: 前台模式下是否自动激活窗口
            min_interval: 最小操作间隔（秒）
            log_level: 日志级别
            enable_stats: 是否启用统计
        """
        self.hwnd = hwnd
        self.keyboard_mode = keyboard_mode
        self.auto_activate = auto_activate
        self.min_interval = min_interval
        self.log_level = log_level
        self.enable_stats = enable_stats
        
        # 延迟初始化
        self._mouse = None
        self._bg_keyboard = None
        self._fg_keyboard = None
        
        # 频率控制
        self._last_action_time = 0
        
        # 统计
        self.stats = {
            "total_clicks": 0,
            "total_keys": 0,
            "failed_actions": 0
        } if enable_stats else None
    
    def _lazy_init(self):
        """延迟初始化底层操作器"""
        if self._mouse is None:
            from core.window_manager import BackgroundMouse
            self._mouse = BackgroundMouse(self.hwnd)
        
        if self._bg_keyboard is None:
            from core.window_manager import BackgroundKeyboard
            self._bg_keyboard = BackgroundKeyboard(self.hwnd)
        
        if self._fg_keyboard is None:
            from core.window_manager import ForegroundKeyboard
            self._fg_keyboard = ForegroundKeyboard(self.hwnd, self.auto_activate)
    
    def _check_frequency(self) -> bool:
        """检查操作频率"""
        now = time.time()
        if now - self._last_action_time < self.min_interval:
            return False
        self._last_action_time = now
        return True
    
    def _log(self, level: LogLevel, msg: str, success: bool = True):
        """记录日志（使用统一日志系统）"""
        if self.log_level < level:
            return
        
        if level == LogLevel.ERROR:
            if success:
                调试器.warning("动作", msg)
            else:
                调试器.error("动作", msg)
        elif level == LogLevel.SIMPLE:
            调试器.debug("动作", msg)
        elif level >= LogLevel.DETAIL:
            调试器.trace("动作", msg)
    
    # ==================== 鼠标操作 ====================
    
    def click(self, x: int, y: int, button: str = 'left', delay: float = 0.05) -> bool:
        """点击"""
        self._lazy_init()
        
        if not self._check_frequency():
            return False
        
        try:
            self._mouse.click(x, y, button, delay)
            if self.log_level >= LogLevel.SIMPLE:
                self._log(LogLevel.SIMPLE, f"点击 ({x},{y})")
            
            if self.stats:
                self.stats["total_clicks"] += 1
            
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"点击({x},{y})异常: {e}", False)
            if self.stats:
                self.stats["failed_actions"] += 1
            return False
    
    def move(self, x: int, y: int) -> bool:
        """移动鼠标"""
        self._lazy_init()
        
        try:
            self._mouse.move(x, y)           
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"移动({x},{y})异常: {e}", False)
            return False
    
    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.2,
             button: str = 'left') -> bool:
        """拖拽"""
        self._lazy_init()
        
        if not self._check_frequency():
            return False
        
        try:
            self._mouse.drag(x1, y1, x2, y2, duration, button)            
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"拖拽({x1},{y1})→({x2},{y2})异常: {e}", False)
            if self.stats:
                self.stats["failed_actions"] += 1
            return False
    
    def scroll(self, delta: int, x: int = None, y: int = None) -> bool:
        """滚动"""
        self._lazy_init()
        
        try:
            success = self._mouse.scroll(delta, x, y)
            if self.log_level >= LogLevel.DETAIL:
                self._log(LogLevel.DETAIL, f"滚动 delta={delta}", success)
            return success
        except Exception as e:
            self._log(LogLevel.ERROR, f"滚动(delta={delta})异常: {e}", False)
            return False
    
    # ==================== 键盘操作（根据模式选择） ====================
    
    def press_key(self, key_code: int, delay: float = 0.05) -> bool:
        """按下并释放一个键"""
        self._lazy_init()
        
        if not self._check_frequency():
            return False
        
        try:
            if self.keyboard_mode == KeyboardMode.BACKGROUND:
                self._bg_keyboard.press(key_code, delay)
            else:
                self._fg_keyboard.press(key_code, delay)
            
            if self.stats:
                self.stats["total_keys"] += 1
            
            if self.log_level >= LogLevel.DETAIL:
                mode = "后台" if self.keyboard_mode == KeyboardMode.BACKGROUND else "前台"
                self._log(LogLevel.DETAIL, f"{mode}按键 0x{key_code:X}")
            
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"按键(0x{key_code:X})异常: {e}", False)
            if self.stats:
                self.stats["failed_actions"] += 1
            return False
    
    def hotkey(self, *key_codes: int, delay: float = 0.05) -> bool:
        """组合键"""
        self._lazy_init()
        
        if not self._check_frequency():
            return False
        
        try:
            if self.keyboard_mode == KeyboardMode.BACKGROUND:
                self._bg_keyboard.hotkey(*key_codes, delay=delay)
            else:
                self._fg_keyboard.hotkey(*key_codes, delay=delay)
            
            if self.stats:
                self.stats["total_keys"] += len(key_codes)
            
            if self.log_level >= LogLevel.DETAIL:
                keys = [f"0x{k:X}" for k in key_codes]
                mode = "后台" if self.keyboard_mode == KeyboardMode.BACKGROUND else "前台"
                self._log(LogLevel.DETAIL, f"{mode}组合键 {'+'.join(keys)}")
            
            return True
        except Exception as e:
            keys = [f"0x{k:X}" for k in key_codes]
            self._log(LogLevel.ERROR, f"组合键({' + '.join(keys)})异常: {e}", False)
            if self.stats:
                self.stats["failed_actions"] += 1
            return False
    
    def type_text(self, text: str, delay: float = 0.0005) -> bool:
        """输入文本"""
        self._lazy_init()
        
        if not self._check_frequency():
            return False
        
        try:
            if self.keyboard_mode == KeyboardMode.BACKGROUND:
                self._bg_keyboard.type_text(text, delay)
            else:
                self._fg_keyboard.type_text(text, delay)
            
            if self.stats:
                self.stats["total_keys"] += len(text)
            
            if self.log_level >= LogLevel.DETAIL:
                display = text[:20] + "..." if len(text) > 20 else text
                self._log(LogLevel.DETAIL, f"输入文本: {display}")
            
            return True
        except Exception as e:
            self._log(LogLevel.ERROR, f"输入文本异常: {e}", False)
            if self.stats:
                self.stats["failed_actions"] += 1
            return False
    
    # ==================== 快捷方法（常用键） ====================
    
    def enter(self, delay: float = 0.05) -> bool:
        """回车键"""
        return self.press_key(0x0D, delay)
    
    def space(self, delay: float = 0.05) -> bool:
        """空格键"""
        return self.press_key(0x20, delay)
    
    def backspace(self, delay: float = 0.05) -> bool:
        """退格键"""
        return self.press_key(0x08, delay)
    
    def escape(self, delay: float = 0.05) -> bool:
        """ESC键"""
        return self.press_key(0x1B, delay)
    
    def tab(self, delay: float = 0.05) -> bool:
        """Tab键"""
        return self.press_key(0x09, delay)
    
    # 方向键
    def arrow_up(self, delay: float = 0.05) -> bool:
        return self.press_key(0x26, delay)
    
    def arrow_down(self, delay: float = 0.05) -> bool:
        return self.press_key(0x28, delay)
    
    def arrow_left(self, delay: float = 0.05) -> bool:
        return self.press_key(0x25, delay)
    
    def arrow_right(self, delay: float = 0.05) -> bool:
        return self.press_key(0x27, delay)
    
    # 功能键
    def f1(self, delay: float = 0.05) -> bool:
        return self.press_key(0x70, delay)
    
    def f2(self, delay: float = 0.05) -> bool:
        return self.press_key(0x71, delay)
    
    # ==================== 状态查询 ====================
    
    def is_window_valid(self) -> bool:
        """检查窗口是否有效"""
        import win32gui
        return win32gui.IsWindow(self.hwnd)
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return self.stats.copy() if self.stats else {}
    
    def set_keyboard_mode(self, mode: str='后台'):
        """运行时切换键盘模式
        mode: 模式
        '后台': 后台模式
        '前台': 前台模式
        
        """
        if mode=='后台':
            self.keyboard_mode = KeyboardMode.BACKGROUND
        elif mode=='前台':
            self.keyboard_mode = KeyboardMode.FOREGROUND
        
        调试器.debug("动作", f"键盘模式切换为 {mode}")
    
    def set_log_level(self, level: LogLevel):
        """设置日志级别"""
        self.log_level = level

    