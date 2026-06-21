# tasks/baokushenchu.py
"""
宝库深处任务定义
"""
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from typing import Optional, Tuple, List
from core.utils import 匹配分组关键字, 解析时间文字,缩放区域,提取次数
from core.debug import 调试器
import time
from core.recognition import OCRResult, ocr
import re

@任务定义(
    任务ID="baokushenchu",
    任务名称="宝库深处",
    调试模式=False,
    任务类型="定时任务",
    优先级=14,    
    地图关键字="宝库深处|宝库深", 
    工作时间开始=20,   
    工作时间结束=21, 
    提前进场秒数=0,
    工作时间段列表="20:30-20:45",
    次数刷新区间列表="20:30-20:45",
    次数刷新区间条件="星期6,7",
    执行日期规则="星期6,7",
    圣兽宝库完成时间="",
)
class 宝库深处任务(战斗任务执行器):
    """宝库深处任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
   
    def 执行入口逻辑(self) -> bool:
        """执行宝库深处入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False
        
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug(self.调试分类, "展开右上角任务帘失败")
            return False

        if not self.页面.大千世界.进入大千世界页面():    
            调试器.debug(self.调试分类, "进入大千世界页面失败")
            return False
        
        if not self.页面.大千世界.圣兽页面.进入圣兽试炼任务页面():    
            调试器.debug(self.调试分类, "进入圣兽试炼任务页面失败")
            return False
        
        if not self.页面.大千世界.圣兽页面.进入圣兽宝库页面():    
            调试器.debug(self.调试分类, "进入宝库深处页面失败")
            return False
        
        # 等待刷新时间，强制等待服务器时间同步
        time.sleep(max(0.5, self.游戏配置.刷新等待秒))
        截图=self.线程.刷新截图()

        # 3. 更新刷新时间        
        if 截图 is None:
            return False
        时间文字 = self.线程.文字识别器.recognize_text(截图, self.游戏配置.区域.圣兽宝库.圣兽宝库页面深处刷新时间标签.元组)
        
        剩余时间 = 解析时间文字(时间文字)
        if 剩余时间 is not None and 剩余时间>0:
            self.任务状态.剩余次数=0
            return False
        
        if not 匹配分组关键字(时间文字, "已|己"):  
            调试器.debug(self.调试分类, "宝库深处页面刷新时间未到")
            return False     

        # 4. 点击进入副本  
        调试器.debug(self.调试分类, "步骤5: 点击进入宝库深处副本")
        if not self.页面.大千世界.圣兽页面.进入宝库深处副本():
            调试器.error(self.调试分类, "点击挑战按钮失败，入口逻辑中断")
            return False

        调试器.state(self.调试分类, "入口逻辑执行成功，已进入宝库深处副本")
        return True
    

    def _执行抢怪操作(self) -> bool:
        return self._执行抢归属动作宝库类副本()
   