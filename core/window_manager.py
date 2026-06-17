# core/window_manager.py
"""
窗口管理模块

功能：
1. 窗口截图（PrintWindow / BitBlt）
2. 后台鼠标操作（PostMessage）
3. 虚拟键码常量
4. 前台/后台键盘操作
"""
import win32gui
import win32ui
import win32con
import numpy as np
import cv2
import ctypes
import win32api
import time
import random
from typing import Tuple, Optional
from core.debug import 调试器


# ---------------------------- 截图工具 ----------------------------

def capture_window(hwnd, client_only=True):
    """
    使用 PrintWindow 捕获指定窗口的内容，返回 numpy 数组 (BGR 格式，兼容 OpenCV)
    
    参数:
        hwnd: 窗口句柄
        client_only: 是否仅捕获客户区（True 通常用于游戏窗口）
    
    返回:
        numpy 数组 (height, width, 3)，失败时返回 None
    """
    hwnd_dc = None
    mfc_dc = None
    save_dc = None
    bitmap = None
    
    try:
        if not win32gui.IsWindow(hwnd):
            调试器.warning("截图", f"窗口无效: {hwnd}")
            return None
        # 获取窗口尺寸
        if client_only:
            left, top, right, bottom = win32gui.GetClientRect(hwnd)
            width = right - left
            height = bottom - top
        else:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

        # 创建设备上下文
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        # 创建位图
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)

        # 使用 ctypes 调用 PrintWindow
        PrintWindow = ctypes.windll.user32.PrintWindow
        flags = 2 if client_only else 0
        
        result = PrintWindow(hwnd, save_dc.GetSafeHdc(), flags)
        
        if result == 0:
            调试器.warning("截图", f"PrintWindow 失败(flags={flags})，尝试降级方案")
            if client_only:
                调试器.debug("截图", "尝试标志位 1 (PW_CLIENTONLY)...")
                result = PrintWindow(hwnd, save_dc.GetSafeHdc(), 1)
                if result == 0:
                    调试器.debug("截图", "尝试标志位 0...")
                    result = PrintWindow(hwnd, save_dc.GetSafeHdc(), 0)
                    if result == 0:
                        调试器.error("截图", "PrintWindow 所有标志位均失败")
                        win32gui.DeleteObject(bitmap.GetHandle())
                        save_dc.DeleteDC()
                        mfc_dc.DeleteDC()
                        win32gui.ReleaseDC(hwnd, hwnd_dc)
                        return None
            else:
                调试器.error("截图", "PrintWindow 失败且非 client_only 模式")
                win32gui.DeleteObject(bitmap.GetHandle())
                save_dc.DeleteDC()
                mfc_dc.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwnd_dc)
                return None

        # 将位图转换为 numpy 数组
        bmpinfo = bitmap.GetInfo()
        bmpstr = bitmap.GetBitmapBits(True)
        bits_pixel = bmpinfo['bmBitsPixel']
        
        if bits_pixel == 32:
            img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4))
            img = img[:, :, :3]
        elif bits_pixel == 24:
            img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((bmpinfo['bmHeight'], bmpinfo['bmWidth'], 3))
        else:
            调试器.warning("截图", f"不支持的位深: {bits_pixel}，尝试自动转换")
            img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((bmpinfo['bmHeight'], bmpinfo['bmWidth'], -1))
            if img.shape[2] == 4:
                img = img[:, :, :3]
            elif img.shape[2] == 1:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            else:
                调试器.error("截图", f"无法处理的位深: {bits_pixel}")
                win32gui.DeleteObject(bitmap.GetHandle())
                save_dc.DeleteDC()
                mfc_dc.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwnd_dc)
                return None

        # 成功，清理资源
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)

        return img
        
    except Exception as e:
        调试器.error("截图", f"截图异常: {e}")
        import traceback
        调试器.error("截图", f"异常堆栈:\n{traceback.format_exc()}")
        
        # 异常时确保资源清理
        if bitmap is not None:
            try:
                win32gui.DeleteObject(bitmap.GetHandle())
            except:
                pass
        if save_dc is not None:
            try:
                save_dc.DeleteDC()
            except:
                pass
        if mfc_dc is not None:
            try:
                mfc_dc.DeleteDC()
            except:
                pass
        if hwnd_dc is not None:
            try:
                win32gui.ReleaseDC(hwnd, hwnd_dc)
            except:
                pass
        
        return None


def capture_window_alt(hwnd):
    """
    备选截图方法：使用 BitBlt 捕获窗口
    
    参数:
        hwnd: 窗口句柄
    
    返回:
        numpy 数组 (BGR)，失败返回 None
    """
    hwnd_dc = None
    mfc_dc = None
    save_dc = None
    bitmap = None
    
    try:
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()

        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)

        save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

        bmpinfo = bitmap.GetInfo()
        bmpstr = bitmap.GetBitmapBits(True)
        bits_pixel = bmpinfo['bmBitsPixel']
        
        if bits_pixel == 32:
            img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((bmpinfo['bmHeight'], bmpinfo['bmWidth'], 4))
            img = img[:, :, :3]
        elif bits_pixel == 24:
            img = np.frombuffer(bmpstr, dtype=np.uint8).reshape((bmpinfo['bmHeight'], bmpinfo['bmWidth'], 3))
        else:
            调试器.warning("截图", f"备选方法不支持的位深: {bits_pixel}")
            win32gui.DeleteObject(bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)
            return None

        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)

        return img
        
    except Exception as e:
        调试器.error("截图", f"备选截图方法失败: {e}")
        
        # 异常时确保资源清理
        if bitmap is not None:
            try:
                win32gui.DeleteObject(bitmap.GetHandle())
            except:
                pass
        if save_dc is not None:
            try:
                save_dc.DeleteDC()
            except:
                pass
        if mfc_dc is not None:
            try:
                mfc_dc.DeleteDC()
            except:
                pass
        if hwnd_dc is not None:
            try:
                win32gui.ReleaseDC(hwnd, hwnd_dc)
            except:
                pass
        
        return None


# ==================== 后台鼠标操作类 ====================

class BackgroundMouse:
    """后台鼠标操作类（使用 PostMessage，不需要窗口焦点）"""
    
    def __init__(self, hwnd: int):
        """
        初始化后台鼠标控制器
        
        参数:
            hwnd: 目标窗口句柄
        """
        self.hwnd = hwnd
    
    def _get_button_params(self, button: str) -> Tuple[int, int, int]:
        """
        获取按钮对应的消息参数
        
        返回:
            (down_msg, up_msg, wParam)
        """
        if button == 'left':
            return (win32con.WM_LBUTTONDOWN, 
                    win32con.WM_LBUTTONUP, 
                    win32con.MK_LBUTTON)
        elif button == 'right':
            return (win32con.WM_RBUTTONDOWN, 
                    win32con.WM_RBUTTONUP, 
                    win32con.MK_RBUTTON)
        elif button == 'middle':
            return (win32con.WM_MBUTTONDOWN, 
                    win32con.WM_MBUTTONUP, 
                    win32con.MK_MBUTTON)
        else:
            raise ValueError(f"不支持的按钮类型: {button}")
    
    def click(self, x: int, y: int, button: str = 'left', delay: float = 0.05):
        """
        在指定位置点击
        
        参数:
            x, y: 客户区坐标
            button: 'left', 'right', 'middle'
            delay: 按下和释放之间的延迟（秒）
        """
        lParam = win32api.MAKELONG(x, y)
        down_msg, up_msg, wParam = self._get_button_params(button)
        
        win32api.PostMessage(self.hwnd, down_msg, wParam, lParam)
        time.sleep(delay)
        win32api.PostMessage(self.hwnd, up_msg, 0, lParam)
    
    def move(self, x: int, y: int):
        """
        移动鼠标到指定位置
        
        参数:
            x, y: 客户区坐标
        """
        lParam = win32api.MAKELONG(x, y)
        win32api.PostMessage(self.hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
    
    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.3, 
             button: str = 'left'):
        """
        拖拽（带轨迹）
        
        参数:
            x1, y1: 起始坐标
            x2, y2: 结束坐标
            button: 鼠标按钮
            duration: 拖拽持续时间（秒）
        """
        down_msg, up_msg, wParam = self._get_button_params(button)
        
        lParam_start = win32api.MAKELONG(x1, y1)
        win32api.PostMessage(self.hwnd, down_msg, wParam, lParam_start)
        time.sleep(0.05)
        
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy), 10)
        step_x = dx / steps
        step_y = dy / steps
        step_delay = duration / steps
        
        调试器.trace("动作", f"拖拽轨迹: ({x1},{y1})→({x2},{y2}), 步数={steps}, 间隔={step_delay*1000:.0f}ms")
        
        for i in range(1, steps + 1):
            x = int(x1 + step_x * i)
            y = int(y1 + step_y * i)
            lParam = win32api.MAKELONG(x, y)
            win32api.PostMessage(self.hwnd, win32con.WM_MOUSEMOVE, wParam, lParam)
            time.sleep(step_delay)
        
        time.sleep(random.uniform(0.3, 0.5))
        lParam_end = win32api.MAKELONG(x2, y2)
        win32api.PostMessage(self.hwnd, up_msg, 0, lParam_end)
    
    def drag_simple(self, x1: int, y1: int, x2: int, y2: int, button: str = 'left'):
        """
        简化拖拽：按下 → 直接移动到终点 → 释放
        
        参数:
            x1, y1: 起始坐标
            x2, y2: 结束坐标
            button: 鼠标按钮
        """
        down_msg, up_msg, wParam = self._get_button_params(button)
        
        lParam_start = win32api.MAKELONG(x1, y1)
        win32api.PostMessage(self.hwnd, down_msg, wParam, lParam_start)
        time.sleep(0.05)
        
        lParam_end = win32api.MAKELONG(x2, y2)
        win32api.PostMessage(self.hwnd, win32con.WM_MOUSEMOVE, wParam, lParam_end)
        time.sleep(0.05)
        
        win32api.PostMessage(self.hwnd, up_msg, 0, lParam_end)
    
    def scroll(self, delta: int, x: int = None, y: int = None):
        """
        滚动滚轮
        
        参数:
            delta: 滚动量，正数向上，负数向下（通常 120 为一格）
            x, y: 滚动位置（可选，默认客户区中心）
        """
        if x is None or y is None:
            rect = win32gui.GetClientRect(self.hwnd)
            x = (rect[2] - rect[0]) // 2
            y = (rect[3] - rect[1]) // 2
        
        lParam = win32api.MAKELONG(x, y)
        wParam = (delta << 16) | 0
        
        win32api.PostMessage(self.hwnd, win32con.WM_MOUSEWHEEL, wParam, lParam)


# ==================== 虚拟键码常量 ====================

class VK:
    """虚拟键码常量"""
    # 字母
    A = 0x41
    B = 0x42
    C = 0x43
    D = 0x44
    E = 0x45
    F = 0x46
    G = 0x47
    H = 0x48
    I = 0x49
    J = 0x4A
    K = 0x4B
    L = 0x4C
    M = 0x4D
    N = 0x4E
    O = 0x4F
    P = 0x50
    Q = 0x51
    R = 0x52
    S = 0x53
    T = 0x54
    U = 0x55
    V = 0x56
    W = 0x57
    X = 0x58
    Y = 0x59
    Z = 0x5A
    
    # 数字
    NUM_0 = 0x30
    NUM_1 = 0x31
    NUM_2 = 0x32
    NUM_3 = 0x33
    NUM_4 = 0x34
    NUM_5 = 0x35
    NUM_6 = 0x36
    NUM_7 = 0x37
    NUM_8 = 0x38
    NUM_9 = 0x39
    
    # 功能键
    F1 = 0x70
    F2 = 0x71
    F3 = 0x72
    F4 = 0x73
    F5 = 0x74
    F6 = 0x75
    F7 = 0x76
    F8 = 0x77
    F9 = 0x78
    F10 = 0x79
    F11 = 0x7A
    F12 = 0x7B
    
    # 控制键
    SPACE = 0x20
    RETURN = 0x0D
    ENTER = 0x0D
    ESCAPE = 0x1B
    TAB = 0x09
    BACKSPACE = 0x08
    DELETE = 0x2E
    INSERT = 0x2D
    HOME = 0x24
    END = 0x23
    PAGE_UP = 0x21
    PAGE_DOWN = 0x22
    
    # 方向键
    UP = 0x26
    DOWN = 0x28
    LEFT = 0x25
    RIGHT = 0x27
    
    # 修饰键
    CONTROL = 0x11
    ALT = 0x12
    SHIFT = 0x10
    WIN = 0x5B


# ==================== 前台键盘类 ====================

class ForegroundKeyboard:
    """
    前台键盘操作类
    使用 keybd_event 模拟按键，需要窗口有焦点
    """
    
    def __init__(self, hwnd: int = None, auto_activate: bool = True):
        """
        初始化前台键盘控制器
        
        参数:
            hwnd: 目标窗口句柄（可选）
            auto_activate: 是否在按键前自动激活窗口
        """
        self.hwnd = hwnd
        self.auto_activate = auto_activate
    
    def _activate_window(self) -> bool:
        """激活窗口"""
        if not self.hwnd:
            return True
        
        try:
            win32gui.SetForegroundWindow(self.hwnd)
            time.sleep(0.05)
            
            foreground = win32gui.GetForegroundWindow()
            if foreground == self.hwnd:
                return True
            
            rect = win32gui.GetWindowRect(self.hwnd)
            if rect[2] > rect[0] and rect[3] > rect[1]:
                x = (rect[0] + rect[2]) // 2
                y = (rect[1] + rect[3]) // 2
                original_pos = win32api.GetCursorPos()
                win32api.SetCursorPos((x, y))
                time.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                time.sleep(0.1)
                win32api.SetCursorPos(original_pos)
                return True
        except Exception as e:
            调试器.debug("动作", f"激活窗口失败: {e}")
        
        return False
    
    def _ensure_activated(self):
        """确保窗口已激活"""
        if self.auto_activate:
            self._activate_window()
    
    def press(self, key_code: int, delay: float = 0.05):
        """按下并释放一个键"""
        self._ensure_activated()
        win32api.keybd_event(key_code, 0, 0, 0)
        time.sleep(delay)
        win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)
    
    def key_down(self, key_code: int):
        """按下键（不释放）"""
        self._ensure_activated()
        win32api.keybd_event(key_code, 0, 0, 0)
    
    def key_up(self, key_code: int):
        """释放键"""
        win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)
    
    def hotkey(self, *key_codes: int, delay: float = 0.05):
        """组合键"""
        self._ensure_activated()
        
        for vk in key_codes:
            win32api.keybd_event(vk, 0, 0, 0)
            time.sleep(delay)
        
        for vk in reversed(key_codes):
            win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(delay)
    
    def type_text(self, text: str, delay: float = 0.05):
        """输入文本"""
        self._ensure_activated()
        for ch in text:
            if ch.isalpha():
                vk_code = ord(ch.upper())
            elif ch.isdigit():
                vk_code = ord(ch)
            else:
                continue
            
            win32api.keybd_event(vk_code, 0, 0, 0)
            time.sleep(delay)
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(delay / 2)
    
    def refresh(self, method: str = "f5", delay: float = 0.05):
        if method.lower() == "f5":
            self.press(VK.F5, delay)
        elif method.lower() == "ctrl+r":
            self.hotkey(VK.CONTROL, VK.R, delay=delay)
        else:
            raise ValueError(f"不支持的刷新方式: {method}")
    
    def copy(self, delay: float = 0.05):
        self.hotkey(VK.CONTROL, VK.C, delay=delay)
    
    def paste(self, delay: float = 0.05):
        self.hotkey(VK.CONTROL, VK.V, delay=delay)
    
    def cut(self, delay: float = 0.05):
        self.hotkey(VK.CONTROL, VK.X, delay=delay)
    
    def select_all(self, delay: float = 0.05):
        self.hotkey(VK.CONTROL, VK.A, delay=delay)
    
    def undo(self, delay: float = 0.05):
        self.hotkey(VK.CONTROL, VK.Z, delay=delay)
    
    def redo(self, delay: float = 0.05):
        self.hotkey(VK.CONTROL, VK.Y, delay=delay)
    
    def enter(self, delay: float = 0.05):
        self.press(VK.ENTER, delay)
    
    def space(self, delay: float = 0.05):
        self.press(VK.SPACE, delay)
    
    def backspace(self, delay: float = 0.05):
        self.press(VK.BACKSPACE, delay)
    
    def delete(self, delay: float = 0.05):
        self.press(VK.DELETE, delay)
    
    def arrow_up(self, delay: float = 0.05):
        self.press(VK.UP, delay)
    
    def arrow_down(self, delay: float = 0.05):
        self.press(VK.DOWN, delay)
    
    def arrow_left(self, delay: float = 0.05):
        self.press(VK.LEFT, delay)
    
    def arrow_right(self, delay: float = 0.05):
        self.press(VK.RIGHT, delay)
    
    def alt_tab(self, delay: float = 0.05):
        self.hotkey(VK.ALT, VK.TAB, delay=delay)


# ==================== 后台键盘类 ====================

class BackgroundKeyboard:
    """
    后台键盘操作类
    使用 PostMessage 发送消息，不需要窗口有焦点
    """
    
    def __init__(self, hwnd: int, auto_find_input: bool = True):
        """
        初始化后台键盘控制器
        
        参数:
            hwnd: 目标窗口句柄
            auto_find_input: 是否自动查找实际输入窗口
        """
        self.original_hwnd = hwnd
        if auto_find_input:
            self.hwnd = self._find_input_window(hwnd)
        else:
            self.hwnd = hwnd
    
    def _find_input_window(self, hwnd: int) -> int:
        """查找实际接收输入的窗口"""
        input_classes = ["Edit", "RichEdit20W", "RichEdit50W", "Scintilla", "QWidget"]
        
        class_name = win32gui.GetClassName(hwnd)
        if class_name in input_classes:
            return hwnd
        
        def find_child(parent_hwnd):
            try:
                child_hwnd = win32gui.GetWindow(parent_hwnd, win32con.GW_CHILD)
                while child_hwnd:
                    child_class = win32gui.GetClassName(child_hwnd)
                    if child_class in input_classes:
                        return child_hwnd
                    result = find_child(child_hwnd)
                    if result:
                        return result
                    child_hwnd = win32gui.GetWindow(child_hwnd, win32con.GW_HWNDNEXT)
            except:
                pass
            return None
        
        found = find_child(hwnd)
        return found if found else hwnd
    
    def press(self, key_code: int, delay: float = 0.05):
        """按下并释放一个键"""
        if 0x30 <= key_code <= 0x5A:
            ch = chr(key_code).lower()
            win32api.PostMessage(self.hwnd, win32con.WM_CHAR, ord(ch), 0)
        else:
            win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, key_code, 0)
            time.sleep(delay)
            win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, key_code, 0)
    
    def key_down(self, key_code: int):
        win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, key_code, 0)
    
    def key_up(self, key_code: int):
        win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, key_code, 0)
    
    def hotkey(self, *key_codes: int, delay: float = 0.05):
        for vk in key_codes:
            win32api.PostMessage(self.hwnd, win32con.WM_KEYDOWN, vk, 0)
            time.sleep(delay)
        for vk in reversed(key_codes):
            win32api.PostMessage(self.hwnd, win32con.WM_KEYUP, vk, 0)
            time.sleep(delay)
    
    def type_text(self, text: str, delay: float = 0.0005):
        for ch in text:
            win32api.PostMessage(self.hwnd, win32con.WM_CHAR, ord(ch), 0)
            time.sleep(delay)
    
    def refresh(self, method: str = "f5", delay: float = 0.05):
        if method.lower() == "f5":
            self.press(VK.F5, delay)
        elif method.lower() == "ctrl+r":
            self.hotkey(VK.CONTROL, VK.R, delay=delay)
    
    def copy(self, delay: float = 0.05):
        self.hotkey(VK.CONTROL, VK.C, delay=delay)
    
    def paste(self, delay: float = 0.05):
        self.hotkey(VK.CONTROL, VK.V, delay=delay)
    
    def cut(self, delay: float = 0.05):
        self.hotkey(VK.CONTROL, VK.X, delay=delay)
    
    def select_all(self, delay: float = 0.05):
        self.hotkey(VK.CONTROL, VK.A, delay=delay)
    
    def enter(self, delay: float = 0.05):
        self.press(VK.ENTER, delay)
    
    def space(self, delay: float = 0.05):
        self.press(VK.SPACE, delay)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    hwnd = 477299164
    capture_window(hwnd)
    