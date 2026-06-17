# tasks/shenjiezhidian.py
"""
神界之巅任务定义
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
    任务ID="shenjiezhidian",
    任务名称="神界之巅",
    调试模式=True,
    任务类型="定时任务",
    优先级=16,
    地图关键字="神界之", 
    工作时间开始=11,
    工作时间段列表="11:30-23:30",
    提前进场秒数=0,
    次数刷新区间列表="11:30-11:36",
)
class 神界之巅任务(战斗任务执行器):
    """神界之巅任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
   
    def 执行入口逻辑(self) -> bool:
        """执行神界之巅入口逻辑"""
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
        
        if not self.页面.大千世界.神界页面.进入神界页面():    
            调试器.debug(self.调试分类, "进入神界页面失败")
            return False
        
        if not self.页面.大千世界.神界页面.进入神界之巅页面():    
            调试器.debug(self.调试分类, "进入神界之巅页面失败")
            return False
        
        # 等待刷新时间，强制等待服务器时间同步
        time.sleep(max(0.5, self.游戏配置.刷新等待秒))
        self.线程.刷新截图()

        # 3. 更新次数    
        截图 = self.线程.截图
        if 截图 is None:
            截图= self.线程.刷新截图()
        if 截图 is None:
            return False
        ocr_result = self.线程.文字识别器.recognize_text(截图,self.游戏配置.区域.神界大陆.神界之巅刷新情况标签.元组)
       
        if ocr_result:
            if 匹配分组关键字(ocr_result, "已|刷|新"):                
                self.任务状态.剩余次数=1                
            elif 匹配分组关键字(ocr_result, "后|复|活"):  
                self.任务状态.剩余次数= 0                   
                 
        # 4. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"读取次数后确认为0，次数已用完")
            return False
       
        
        # 5. 点击进入秘境  
        调试器.debug(self.调试分类, "步骤5: 点击进入神界之巅副本")
        if not self.页面.大千世界.神界页面.进入神界之巅副本():
            调试器.error(self.调试分类, "点击挑战按钮失败，入口逻辑中断")
            return False

        调试器.state(self.调试分类, "入口逻辑执行成功，已进入神界之巅副本")
        return True
       
   