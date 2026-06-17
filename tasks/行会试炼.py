# tasks/hanghuishilian.py
"""
行会试炼定义
"""

from typing import Tuple


from core.utils import 匹配分组关键字, 提取次数
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from core.debug import 调试器
import time



@任务定义(
    任务ID="hanghuishilian",
    任务名称="行会试炼",
    任务类型="召唤任务",
    优先级=10,
    地图关键字="会试|行会试炼",  

    工作时间开始=0, 
    提前进场秒数=0,
    启用自动战斗=True,
    启用自动走位=True,
    启用响应召唤=True,
    状态_剩余次数=0
)
class 行会试炼任务(战斗任务执行器):
    """行会试炼任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)       
        self.任务状态.剩余次数=0

    # 行会试炼，这个不需要正常进入，只接受召唤进入，入口即重置    
    def 执行入口逻辑(self) -> bool:
        self.任务状态.剩余次数=0
        return True
    
      #行会试炼召唤都为真
    def _召唤响应动态检查(self, 召唤信息: dict) -> bool:
        """
        动态检查是否允许响应召唤（子类可覆盖，只读）
        
        ⚠️ 此方法必须是只读的：
        - 可以读取：self.任务状态、self.公共变量、self.是否在副本中()
        - 禁止修改：任何状态字段、任何游戏操作
        
        参数:
            召唤信息: {"玩家名": "xxx", "副本名": "xxx", "层数": 8, "类型": "协助"}
        
        返回:
            True: 允许响应
            False: 拒绝响应
        
        示例:
            # 战斗中不接受召唤
            if self.是否在副本中():
                return False
        """      
        self.任务状态.剩余次数=1
        return True
    

    
