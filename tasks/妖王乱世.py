# tasks/yaowangluanshi.py
"""
妖王乱世任务定义
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
    任务ID="yaowangluanshi",
    任务名称="妖王乱世",
    调试模式=True,
    任务类型="定时任务",
    优先级=6,    
    地图关键字="妖王乱", 
    默认攻击模式="和平模式",
    工作时间开始=15,
    工作时间结束=16,
    提前进场秒数=0,
    工作时间段列表="15:30-15:58",
    次数刷新区间列表="15:30-15:35,15:40-15:45,15:50-15:55",
)
class 妖王乱世任务(战斗任务执行器):
    """妖王乱世任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
   
    def 执行入口逻辑(self) -> bool:
        """执行妖王乱世入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False
        
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug(self.调试分类, "展开右上角任务帘失败")
            return False 
        
        if not self.页面.主界面操作.点击妖王乱世上标.执行():    
            调试器.debug(self.调试分类, "妖王乱世下标进入失败")
            return False
        
        if not self.页面.主界面操作.点击妖王乱世下标.执行():    
            调试器.debug(self.调试分类, "妖王乱世下标点击失败")
            return False
        
        if not self.页面.主界面操作.进入妖王乱世副本.执行():    
            调试器.debug(self.调试分类, "妖王乱世副本进入失败")
            return False
        
        调试器.state(self.调试分类, "入口逻辑执行成功，已进入妖王乱世副本")
        return True
       
    def 检查退出条件(self) -> bool:
        """覆盖检查退出条件，检查是否满足退出条件"""
        无目标超时 = self.公共变量.获取无目标时间() > self.无目标超时秒数
        静止超时 = self.公共变量.获取静止时长() > self.静止超时秒数
        self.任务状态.剩余次数 = 0
        调试器.debug(self.调试分类, f"退出条件检查: 无目标超时({self.无目标超时秒数}s)={无目标超时}, 静止超时({self.静止超时秒数}s)={静止超时}")
        
        return 无目标超时 and 静止超时 
      