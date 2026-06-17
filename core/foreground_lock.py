"""
前台操作全局锁

用于多窗口线程间协调前台操作，避免多个窗口同时抢焦点
"""
import time
import threading
from core.debug import 调试器


class 前台操作锁:
    """
    全局前台操作锁（单例）
    
    使用方式：
        # 申请前台操作
        if 前台锁.申请(窗口名称, 超时=10):
            # 执行前台操作
            ...
            前台锁.释放(窗口名称)
        
        # 检查是否可进行前台操作
        if 前台锁.是否可用(窗口名称):
            ...
    """
    
    _实例 = None
    _锁 = threading.Lock()
    
    def __new__(cls):
        if cls._实例 is None:
            with cls._锁:
                if cls._实例 is None:
                    cls._实例 = super().__new__(cls)
                    cls._实例._初始化()
        return cls._实例
    
    def _初始化(self):
        self._操作锁 = threading.Lock()
        self.当前占用者: str = ""          # 正在执行前台操作的窗口名称
        self.占用开始时间: float = 0.0     # 开始占用的时间戳
        self.占用超时秒数: int = 10        # 默认超时
    
    def 申请(self, 窗口名称: str, 超时: int = 10) -> bool:
        """
        申请前台操作权限
        
        参数:
            窗口名称: 申请者标识
            超时: 等待超时秒数
        
        返回:
            True: 获得权限
            False: 超时或被其他线程占用
        """
        开始等待 = time.time()
        
        while time.time() - 开始等待 < 超时:
            if self._操作锁.acquire(blocking=False):
                self.当前占用者 = 窗口名称
                self.占用开始时间 = time.time()
                self.占用超时秒数 = 超时
                调试器.debug("前台锁", f"'{窗口名称}' 获得前台操作权限")
                return True
            
            # 检查占用者是否超时（卡死保护）
            if self.当前占用者:
                if time.time() - self.占用开始时间 > self.占用超时秒数:
                    调试器.warning("前台锁", f"'{self.当前占用者}' 前台操作超时，强制释放")
                    self._强制释放()
                    continue
            
            time.sleep(0.1)
        
        调试器.debug("前台锁", f"'{窗口名称}' 申请超时，当前占用者='{self.当前占用者}'")
        return False
    
    def 释放(self, 窗口名称: str):
        """释放前台操作权限"""
        if self.当前占用者 == 窗口名称:
            self.当前占用者 = ""
            self.占用开始时间 = 0.0
            try:
                self._操作锁.release()
            except RuntimeError:
                pass
            调试器.debug("前台锁", f"'{窗口名称}' 释放前台操作权限")
    
    def 是否可用(self, 窗口名称: str) -> bool:
        """
        检查前台操作是否可用（非阻塞）
        
        返回:
            True: 可用（无人占用 或 自己占用）
            False: 被其他线程占用
        """
        if self.当前占用者 == "" or self.当前占用者 == 窗口名称:
            return True
        return False
    
    def _强制释放(self):
        """强制释放（占用者超时时使用）"""
        self.当前占用者 = ""
        self.占用开始时间 = 0.0
        try:
            self._操作锁.release()
        except RuntimeError:
            pass
    
    def 获取占用者(self) -> str:
        """获取当前占用者名称"""
        return self.当前占用者
    
    def 获取剩余占用时间(self) -> float:
        """获取当前占用剩余时间（秒）"""
        if not self.当前占用者:
            return 0
        return self.占用超时秒数 - (time.time() - self.占用开始时间)


# 全局实例
前台锁 = 前台操作锁()