# core/task_scheduler.py
"""
任务调度器

功能：
1. 根据地图匹配当前任务
2. 获取优先级最高的可执行任务
3. 比较优先级决定是否切换任务
4. 创建并管理任务执行器

依赖：
- core.task_executors.registry (任务执行器注册表)
"""
import time
from typing import Optional, List,TYPE_CHECKING
from core.debug import 调试器, DebugLevel, set_global_level
# 解决循环导入，同时提供类型提示
if TYPE_CHECKING:    
    from models.game_config import 游戏全局配置
    from models.task_config import 任务配置基类
    from models.task_state import 任务状态基类
    from core.runtime_state import 运行时公共变量
    from core.page_operations import 页面操作集
    from models.dynamic_tags import 动态标签
    from core.window_thread import 窗口线程
    from core.common_operations import 通用操作集
    from core.assistant import 战斗辅助识别器

class 任务调度器:
    """
    任务调度器
    
    调度逻辑：
    1. 根据地图获取匹配的任务（地图任务）
    2. 获取优先级最高的可执行任务（优先任务）
    3. 比较优先任务与当前任务：
       - 如果优先任务的优先级 > 当前任务优先级 → 切换到优先任务
       - 否则保持当前任务不变
    """
    
    def __init__(self, 线程):
        """
        初始化调度器
        
        参数:
            线程: 窗口线程实例
        """
        self.线程:'窗口线程' = 线程
        self.当前任务 = None
        self.当前执行器 = None
    
    def 调度一次(self) -> str:
        """
        执行一次调度
        
        返回:
            "执行中": 有任务在执行
            "无任务": 没有可执行的任务
            "失败": 执行失败
        """
        调试器.debug("调度", "=" * 50)
        调试器.debug("调度", "开始调度")
        调试器.debug("调度", f"当前地图: {self.线程.当前地图}")
        调试器.debug("调度", "=" * 50)
        
        # 检查并切换任务
        选中任务 = self._检查切换任务()
        
        if not 选中任务:
            调试器.debug("调度", "无任务可执行")
            return "无任务"
        
        # 执行任务
        if self.当前执行器:
            # 结果 = self.当前执行器.执行()
            结果 = self._执行任务带调试()
            调试器.debug("调度", f"执行结果: {结果}")
            return 结果
        
        return "失败"
    def _执行任务带调试(self) -> str:
        """
        执行当前任务，如果任务开启了调试模式则临时提升日志级别
        
        返回:
            任务执行结果
        """
        需要调试 = getattr(self.当前任务, '调试模式', False)
        
        if 需要调试:
            # 记录原级别并提升到 VERBOSE
            self._调试原级别 = 调试器.获取当前全局级别()
            set_global_level(DebugLevel.VERBOSE.value)
            调试器.info("调度", f"🔍 [{self.当前任务.任务名称}] 调试模式开启，日志级别: {self._调试原级别.name} → VERBOSE")
            
            try:
                return self.当前执行器.执行()
            finally:
                # 恢复原级别
                set_global_level(self._调试原级别.value)
                调试器.info("调度", f"🔍 [{self.当前任务.任务名称}] 调试模式关闭，日志级别恢复: VERBOSE → {self._调试原级别.name}")
        else:
            return self.当前执行器.执行()
    def _检查切换任务(self) -> Optional[object]:
        """
        检查是否需要切换任务，并执行切换
        
        返回:
            最终选中的任务
        """
        # 1. 获取地图匹配的任务
        地图任务 = self.线程.获取当前地图任务()
        
        # 2. 获取优先级最高的可执行任务
        优先任务 = self.线程.获取顺序列表最优先任务()
        
        # 3. 确定目标任务
        目标任务 = None
        
        if 地图任务 and 优先任务:
            # 两者都存在，比较优先级
            if 优先任务.优先级 > 地图任务.优先级:
                调试器.debug("调度", f"优先任务优先级({优先任务.优先级}) > 地图任务优先级({地图任务.优先级})，切换到优先任务")
                目标任务 = 优先任务
            else:
                调试器.debug("调度", f"保持地图匹配任务: {地图任务.任务名称}")
                目标任务 = 地图任务
        elif 地图任务:
            调试器.debug("调度", f"仅地图匹配任务: {地图任务.任务名称}")
            目标任务 = 地图任务
        elif 优先任务:
            调试器.debug("调度", f"仅优先任务: {优先任务.任务名称}")
            目标任务 = 优先任务
        else:
            调试器.debug("调度", "无可用任务")
            return None
        
        # 4. 与当前任务比较，决定是否切换
        if self.当前任务 == 目标任务:
            调试器.trace("调度", f"保持当前任务: {self.当前任务.任务名称}")
            return self.当前任务
        
        # 5. 切换任务
        self._切换任务(目标任务)
        
        return self.当前任务
    
    def _切换任务(self, 新任务):
        """切换任务"""
        if self.当前任务:
            调试器.state("调度", f"切换任务: {self.当前任务.任务名称} -> {新任务.任务名称}")
        else:
            调试器.state("调度", f"首次创建执行器: {新任务.任务名称}")
        
        self.当前任务 = 新任务
        self.当前执行器 = self._创建执行器(新任务)
        
        # 重置公共变量中的任务状态
        self.线程.公共变量.重置任务状态()
        self.线程.公共变量.设置当前任务(新任务.任务ID)
    
    def _创建执行器(self, 任务):
        """根据任务类型创建执行器"""
        from core.task_executors import 创建执行器
        return 创建执行器(self.线程, 任务)
    
    def 获取当前任务信息(self) -> dict:
        """获取当前任务信息"""
        if not self.当前任务:
            return {}
        
        return {
            "任务ID": getattr(self.当前任务, '任务ID', ''),
            "任务名称": getattr(self.当前任务, '任务名称', ''),
            "优先级": getattr(self.当前任务, '优先级', 0)
        }
    
    def 重置(self):
        """重置调度器状态"""
        self.当前任务 = None
        self.当前执行器 = None
        调试器.debug("调度", "调度器已重置")


# ==================== 注意 ====================
# 窗口线程中需要实现以下方法供调度器调用：
# - 获取当前地图任务() - 根据地图名称匹配任务
# - 获取顺序列表最优先任务() - 获取优先级最高的可执行任务