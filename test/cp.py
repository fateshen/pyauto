# core/window_manager.py
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# core/window_manager.py (纯 ctypes 版本)

# core/window_manager.py (纯 ctypes 版本 - 修正)
# core/window_manager.py (补全 GetWindowRect)

import ctypes
from ctypes import wintypes
import numpy as np
import win32gui


# ==================== GDI 常量 ====================

PW_CLIENTONLY = 0x00000001
PW_RENDERFULLCONTENT = 0x00000002


# ==================== 结构体定义 ====================

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


# ==================== 函数声明 ====================

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# 窗口相关
GetDC = user32.GetDC
GetDC.argtypes = [wintypes.HWND]
GetDC.restype = wintypes.HDC

ReleaseDC = user32.ReleaseDC
ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
ReleaseDC.restype = wintypes.BOOL

GetClientRect = user32.GetClientRect
GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
GetClientRect.restype = wintypes.BOOL

GetWindowRect = user32.GetWindowRect
GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(RECT)]
GetWindowRect.restype = wintypes.BOOL

PrintWindow = user32.PrintWindow
PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
PrintWindow.restype = wintypes.BOOL

# DC 和位图相关
CreateCompatibleDC = gdi32.CreateCompatibleDC
CreateCompatibleDC.argtypes = [wintypes.HDC]
CreateCompatibleDC.restype = wintypes.HDC

DeleteDC = gdi32.DeleteDC
DeleteDC.argtypes = [wintypes.HDC]
DeleteDC.restype = wintypes.BOOL

CreateCompatibleBitmap = gdi32.CreateCompatibleBitmap
CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
CreateCompatibleBitmap.restype = wintypes.HBITMAP

SelectObject = gdi32.SelectObject
SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
SelectObject.restype = wintypes.HGDIOBJ

DeleteObject = gdi32.DeleteObject
DeleteObject.argtypes = [wintypes.HGDIOBJ]
DeleteObject.restype = wintypes.BOOL

GetBitmapBits = gdi32.GetBitmapBits
GetBitmapBits.argtypes = [wintypes.HBITMAP, ctypes.c_int, ctypes.c_void_p]
GetBitmapBits.restype = ctypes.c_int


def capture_window_ctypes(hwnd, client_only=True):
    """
    纯 ctypes 实现截图
    """
    # 1. 获取窗口尺寸
    rect = RECT()
    
    if client_only:
        if not GetClientRect(hwnd, ctypes.byref(rect)):
            print("[截图] GetClientRect 失败")
            return None
    else:
        if not GetWindowRect(hwnd, ctypes.byref(rect)):
            print("[截图] GetWindowRect 失败")
            return None
    
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    
    if width <= 0 or height <= 0:
        print(f"[截图] 无效尺寸: {width}x{height}")
        return None
    
    # 2. 获取窗口 DC
    hdc_window = GetDC(hwnd)
    if not hdc_window:
        print("[截图] GetDC 失败")
        return None
    
    # 3. 创建兼容 DC
    hdc_mem = CreateCompatibleDC(hdc_window)
    if not hdc_mem:
        ReleaseDC(hwnd, hdc_window)
        print("[截图] CreateCompatibleDC 失败")
        return None
    
    # 4. 创建兼容位图
    hbitmap = CreateCompatibleBitmap(hdc_window, width, height)
    if not hbitmap:
        DeleteDC(hdc_mem)
        ReleaseDC(hwnd, hdc_window)
        print("[截图] CreateCompatibleBitmap 失败")
        return None
    
    # 5. 选入位图
    old_bitmap = SelectObject(hdc_mem, hbitmap)
    
    # 6. PrintWindow 捕获
    flags = PW_RENDERFULLCONTENT if client_only else 0
    result = PrintWindow(hwnd, hdc_mem, flags)
    error_code = ctypes.GetLastError()
    print(f"[截图] GetLastError: {error_code}")
    if not result:
        print("[截图] PrintWindow 尝试使用标志位 2 (PW_RENDERFULLCONTENT)...")
    if not result:
        flags = PW_CLIENTONLY if client_only else 0
        result = PrintWindow(hwnd, hdc_mem, flags)
    
    if not result:
        result = PrintWindow(hwnd, hdc_mem, 0)
    
    if not result:
        SelectObject(hdc_mem, old_bitmap)
        DeleteObject(hbitmap)
        DeleteDC(hdc_mem)
        ReleaseDC(hwnd, hdc_window)
        print("[截图] PrintWindow 失败")
        return None
    
    # 7. 获取位图数据
    # 计算缓冲区大小（32位色深，每行4字节对齐）
    stride = ((width * 32 + 31) // 32) * 4
    total_bytes = stride * height
    
    buffer = ctypes.create_string_buffer(total_bytes)
    bits_copied = GetBitmapBits(hbitmap, total_bytes, buffer)
    
    if bits_copied == 0:
        SelectObject(hdc_mem, old_bitmap)
        DeleteObject(hbitmap)
        DeleteDC(hdc_mem)
        ReleaseDC(hwnd, hdc_window)
        print("[截图] GetBitmapBits 失败")
        return None
    
    # 8. 转换为 numpy 数组
    img = np.frombuffer(buffer, dtype=np.uint8).reshape(height, stride, 4)
    img = img[:, :width, :3]  # 去掉填充和Alpha，保留 BGR
    
    # 9. 清理资源
    SelectObject(hdc_mem, old_bitmap)
    DeleteObject(hbitmap)
    DeleteDC(hdc_mem)
    ReleaseDC(hwnd, hdc_window)
    
    print(f"[截图] 成功: {width}x{height}")
    return img


def capture_window(hwnd, client_only=True):
    """统一截图接口"""
    return capture_window_ctypes(hwnd, client_only)

# capture_window_direct(477299164)
# from core.window_manager import capture_window
capture_window(477299164)