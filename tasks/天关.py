# tasks/tianguan.py
"""
天关任务定义
"""

from core.utils import 匹配分组关键字
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from core.debug import 调试器
import time



@任务定义(
    任务ID="tianguan",
    任务名称="天关",
    任务类型="每日任务",
    优先级=10,
    地图关键字="天关",    
    提前进场秒数=0,
)
class 天关任务(战斗任务执行器):
    """天关任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)       
       
    def 执行入口逻辑(self) -> bool:
        """执行天关入口逻辑"""
        调试器.info("天关", "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("天关", "今日次数已用完，跳过执行")
            return False
        
        # 2. 进入跨服战场页面
        if not self.页面.主界面操作.进入首领页面():
            调试器.error(self.调试分类, "进入首领页面失败，入口逻辑中断")
            return False
      
        # 3. 进入专属页面
        if not self.页面.首领任务.天关.点击右侧天关页面():
            调试器.error(self.调试分类, f"点击右侧专属天关失败，区域: {self.动态标签.首领页面右侧标签.天关.元组}")
            return False
        
        

        # 4. 更新剩余次数        
        if not self.更新区域任务次数(self.游戏配置.区域.天关.天关页面剩余次数标签.元组):
            调试器.warning("天关", "读取天关次数失败，仍继续尝试")
            # 注意：原代码这里直接return False，保持原逻辑
            return False
        
        # 5. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("天关", f"读取次数后确认已用完(剩余{self.任务状态.剩余次数})")
            return False
        
        扫荡挑战按钮文字=self.辅助识别器.获取区域文字(self.游戏配置.区域.天关.天关页面扫荡按钮标签.元组)
        
        if 匹配分组关键字(扫荡挑战按钮文字, "扫|荡") :
             # 6. 进入天关页面
            if not self.页面.首领任务.天关.进入天关前往页面():
                调试器.error("天关", "进入天关前往页面失败，入口逻辑中断")
                return False 
            self.通用操作.点击区域(self.游戏配置.区域.天关.天关确认页面前往挑战按钮标签.元组,6,0.3)
            self.通用操作.清理页面状态()
            return True

        
        if 匹配分组关键字(扫荡挑战按钮文字, "挑|战") :
            # 6. 进入天关页面
            if not self.页面.首领任务.天关.进入天关前往页面():
                调试器.error("天关", "进入天关前往页面失败，入口逻辑中断")
                return False       
            
            # 7. 点击前往挑战
            调试器.debug("天关", "步骤6: 点击前往挑战")
            if not self.页面.首领任务.天关.进入天关副本():
                调试器.error("天关", "点击前往挑战失败，入口逻辑中断")
                return False
            
            调试器.state("天关", "入口逻辑执行成功，已进入天关副本")
            return True
        return False