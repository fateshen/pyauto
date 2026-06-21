# tasks/reward/base.py
"""
强化奖励任务基类
"""
from abc import ABC, abstractmethod
import time
import random
from core.utils import 是否为今天
from typing import Tuple, Optional,TYPE_CHECKING
if TYPE_CHECKING:    
    from models.game_config import 游戏全局配置
    from core.page_operations import 页面操作集
    from core.action_executor import ActionExecutor
    # from core.window_thread import 窗口线程
    from core.common_operations import 通用操作集
    from core.assistant import 战斗辅助识别器
    from core.reward_manager import 强化奖励管理器

class 强化奖励任务基类(ABC):
    """强化奖励任务基类，所有强化奖励任务继承此类"""
    
    # 子类必须定义
    任务ID: str = ""
    任务名称: str = ""
    
    # 子类可选覆盖    
    是否启用: bool = False
    在盟重省执行: bool = False
    工作时间开始: int = 0
    工作时间结束: int = 24
    剩余次数: int = 1
    最小间隔秒: int = 300
    最大间隔秒: int = 600
    下次执行时间: float = 0
    任务类型: str = "不定时任务"
    上次确定任务结束时间: float = 0
    
    def __init__(self, 管理器):
        
        self.管理器: '强化奖励管理器' = 管理器
        self.动作:'ActionExecutor' = 管理器.动作执行器
        self.配置: '游戏全局配置' = 管理器.游戏配置
        self.页面: '页面操作集' = 管理器.页面
        self.通用操作: '通用操作集' = 管理器.通用操作
        self.辅助识别器: '战斗辅助识别器' = 管理器.辅助识别器
    
    def 是否可以执行(self) -> bool:
        if not self.是否启用:
            return False
        
        当前小时 = time.localtime().tm_hour
        if not (self.工作时间开始 <= 当前小时 < self.工作时间结束):
            return False
        
        if self.任务类型=="每日任务" and 是否为今天(self.上次确定任务结束时间):
            return False
        
        if self.下次执行时间 > 0 and time.time() < self.下次执行时间:
            return False
        
        return True
    
    @abstractmethod
    def 执行(self) -> bool:
        """执行任务，返回True=成功"""
        pass
    
    def 标记已执行(self):
        self.下次执行时间 = time.time()+ random.randint(self.最小间隔秒, self.最大间隔秒)
    def _重复点击红点(self, 区域, 最大次数: int, 点击缩放: float,图片路径:str= "红点1.bmp") -> None:
        """重复点击红点直到消失"""
        for _ in range(最大次数):
            if not self.页面.创建寻图点击原区域操作(
                区域.元组,
                图片路径,
                点击缩放
            ).执行():
                break
            self.页面.线程.刷新截图()
    