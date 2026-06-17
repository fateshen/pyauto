# core/task_executors/registry.py
"""
任务执行器注册表 - 注册表模式

支持多窗口独立配置（线程安全）
"""
import threading
from typing import Optional, Dict, Type, Any, List
from dataclasses import dataclass
from core.debug import 调试器


@dataclass
class 任务注册信息:
    """任务注册信息"""
    配置类: Type  # 任务配置类
    状态类: Type  # 任务状态类
    执行器类: Type  # 任务执行器类


class 任务执行器注册表:
    """
    任务执行器注册表 - 单例模式
    
    支持多窗口独立配置（线程安全）
    """
    
    _注册表: Dict[str, 任务注册信息] = {}
    # 配置参数缓存：{窗口名称: {任务ID: 配置参数}}
    _配置参数缓存: Dict[str, Dict[str, dict]] = {}
    # 默认配置参数（装饰器中的默认值）
    _默认配置参数: Dict[str, dict] = {}
    # 线程局部存储
    _thread_local = threading.local()
    _实例 = None
    _锁 = threading.Lock()

    def __new__(cls):
        if cls._实例 is None:
            cls._实例 = super().__new__(cls)
        return cls._实例
    
    # ==================== 窗口管理（线程安全） ====================
    
    @classmethod
    def 设置当前窗口(cls, 窗口名称: str):
        """设置当前线程的窗口名称"""
        cls._thread_local.当前窗口名称 = 窗口名称
    
    @classmethod
    def 获取当前窗口(cls) -> str:
        """获取当前线程的窗口名称"""
        return getattr(cls._thread_local, '当前窗口名称', 'default')
    
    # ==================== 配置参数缓存管理 ====================
    
    @classmethod
    def _获取窗口缓存(cls, 窗口名称: str = None) -> Dict[str, dict]:
        """获取指定窗口的配置缓存"""
        if 窗口名称 is None:
            窗口名称 = cls.获取当前窗口()
        
        if 窗口名称 not in cls._配置参数缓存:
            cls._配置参数缓存[窗口名称] = {}
        
        return cls._配置参数缓存[窗口名称]
    
    @classmethod
    def 获取配置参数(cls, 任务ID: str, 窗口名称: str = None) -> dict:
        """
        获取指定窗口的任务配置参数
        
        优先级：窗口配置 > 默认配置
        """
        窗口缓存 = cls._获取窗口缓存(窗口名称)
        
        if 任务ID in 窗口缓存:
            return 窗口缓存[任务ID].copy()
        
        return cls._默认配置参数.get(任务ID, {}).copy()
    
    @classmethod
    def 设置配置参数(cls, 任务ID: str, 配置参数: dict, 窗口名称: str = None):
        """设置指定窗口的任务配置参数"""
        窗口缓存 = cls._获取窗口缓存(窗口名称)
        窗口缓存[任务ID] = 配置参数.copy()
    
    @classmethod
    def 设置默认配置参数(cls, 任务ID: str, 配置参数: dict):
        """设置默认配置参数（从装饰器加载）"""
        cls._默认配置参数[任务ID] = 配置参数.copy()
    
    @classmethod
    def 获取所有配置参数(cls, 窗口名称: str = None) -> Dict[str, dict]:
        """
        获取指定窗口的所有任务配置参数
        
        返回：窗口配置 + 默认配置（窗口配置覆盖默认配置）
        """
        窗口缓存 = cls._获取窗口缓存(窗口名称)
        
        结果 = {}
        for 任务ID, 配置 in cls._默认配置参数.items():
            结果[任务ID] = 配置.copy()
        
        for 任务ID, 配置 in 窗口缓存.items():
            if 任务ID in 结果:
                结果[任务ID].update(配置)
            else:
                结果[任务ID] = 配置.copy()
        
        return 结果
    
    @classmethod
    def 清空窗口缓存(cls, 窗口名称: str = None):
        """清空指定窗口的配置缓存"""
        if 窗口名称 is None:
            窗口名称 = cls.获取当前窗口()
        
        if 窗口名称 in cls._配置参数缓存:
            cls._配置参数缓存[窗口名称] = {}
            调试器.debug("注册表", f"已清空窗口缓存: {窗口名称}")
    
    @classmethod
    def 获取所有窗口名称(cls) -> List[str]:
        """获取所有已有配置缓存的窗口名称"""
        return list(cls._配置参数缓存.keys())
    
    # ==================== 任务注册 ====================
    
    @classmethod
    def 注册(cls, 
             任务ID: str, 
             配置类: Type, 
             状态类: Type, 
             执行器类: Type):
        """注册任务类型"""
        with cls._锁:
            cls._注册表[任务ID] = 任务注册信息(
                配置类=配置类,
                状态类=状态类,
                执行器类=执行器类
            )
            调试器.debug("注册表", f"注册任务: {任务ID} -> {执行器类.__name__}")
        
    @classmethod
    def 创建(cls, 线程, 任务配置) -> Optional[object]:
        """根据任务配置创建对应的执行器"""
        任务ID = getattr(任务配置, '任务ID', '')
        
        if 任务ID not in cls._注册表:
            调试器.error("注册表", f"未注册的任务类型: '{任务ID}'")
            return None
        
        注册信息 = cls._注册表[任务ID]
        
        # 获取或创建任务状态
        状态 = cls._获取或创建状态(线程, 任务ID, 注册信息.状态类)
        
        # 创建执行器
        return 注册信息.执行器类(线程, 任务配置, 状态)
    
    @classmethod
    def _获取或创建状态(cls, 线程, 任务ID: str, 状态类: Type):
        """获取或创建任务状态"""
        if 任务ID not in 线程.任务状态映射:
            线程.任务状态映射[任务ID] = 状态类()
            调试器.debug("注册表", f"创建新状态: {任务ID}")
        
        return 线程.任务状态映射[任务ID]
    
    # ==================== 查询方法 ====================
    
    @classmethod
    def 获取所有已注册任务(cls) -> List[str]:
        """获取所有已注册的任务ID列表"""
        return list(cls._注册表.keys())
    
    @classmethod
    def 是否已注册(cls, 任务ID: str) -> bool:
        """检查任务是否已注册"""
        return 任务ID in cls._注册表
    
    @classmethod
    def 获取注册信息(cls, 任务ID: str) -> Optional[任务注册信息]:
        """获取任务注册信息"""
        return cls._注册表.get(任务ID)
    
    @classmethod
    def 打印注册表(cls):
        """打印所有已注册的任务"""
        调试器.info("注册表", "=" * 50)
        调试器.info("注册表", "任务注册表")
        调试器.info("注册表", "=" * 50)
        for 任务ID, 信息 in cls._注册表.items():
            调试器.info("注册表", f"  {任务ID}:")
            调试器.debug("注册表", f"    配置类: {信息.配置类.__name__}")
            调试器.debug("注册表", f"    状态类: {信息.状态类.__name__}")
            调试器.debug("注册表", f"    执行器类: {信息.执行器类.__name__}")
        调试器.info("注册表", "=" * 50)
    
    @classmethod
    def 清空注册表(cls):
        """清空注册表（用于测试）"""
        cls._注册表.clear()
        cls._配置参数缓存.clear()
        cls._默认配置参数.clear()
        调试器.info("注册表", "注册表已清空")


# 便捷函数
def 创建执行器(线程, 任务配置) -> Optional[object]:
    """创建任务执行器"""
    return 任务执行器注册表.创建(线程, 任务配置)