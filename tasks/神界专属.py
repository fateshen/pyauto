# tasks/shenjiezhuanshu.py
"""
神界专属任务定义
"""
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from typing import Optional, Tuple, List
from core.utils import 匹配分组关键字, 解析时间文字
from core.debug import 调试器
import time
from core.recognition import OCRResult
import re

@任务定义(
    任务ID="shenjiezhuanshu",
    任务名称="神界专属",
    调试模式=True,
    任务类型="每日任务",
    优先级=3,
    地图关键字="专属秘境|专属秘|专属,境", 
    工作时间开始=6,
    工作时间结束=22,
    提前进场秒数=0,
    不使用多倍奖励=True,
)
class 神界专属任务(战斗任务执行器):
    """神界专属任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
   
    def 执行入口逻辑(self) -> bool:
        """执行神界专属入口逻辑"""
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
        
        if not self.页面.大千世界.神界页面.进入神界专属页面():    
            调试器.debug(self.调试分类, "进入神界专属页面失败")
            return False
        
        # 等待刷新时间，强制等待服务器时间同步
        time.sleep(max(0.5, self.游戏配置.刷新等待秒))
        self.线程.刷新截图()

        # 3. 更新剩余次数
        调试器.debug(self.调试分类, "步骤2: 读取神界专属次数")
        if not self.更新区域任务次数(self.游戏配置.区域.神界大陆.神界专属挑战次数标签.元组):
            调试器.warning(self.调试分类, "读取神界专属次数失败，入口逻辑中断")
            return False
        调试器.debug(self.调试分类, f"剩余次数: {self.任务状态.剩余次数}")

        # 4. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"读取次数后确认为0，次数已用完")
            return False
        
        if not self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.神界大陆.神界专属前往挑战按钮标签.元组,            
            self.游戏配置.区域.神界大陆.神界专属前往击杀按钮标签.元组,
            "前往|击杀"
            ).执行():
           time.sleep(1)
           self.线程.刷新截图()
           地图名= self.线程.识别地图()
           if 匹配分组关键字(地图名, self.任务配置.地图关键字):
               return True

        
        if self.任务配置.不使用多倍奖励 :
            self.通用操作.点击区域(self.游戏配置.区域.神界大陆.神界专属单倍奖励按钮标签.元组)
        
        
        # 7. 点击进入秘境  
        调试器.debug(self.调试分类, "步骤5: 点击进入神界专属副本")
        if not self.页面.大千世界.神界页面.进入神界专属副本():
            调试器.error(self.调试分类, "点击挑战按钮失败，入口逻辑中断")
            return False

        调试器.state(self.调试分类, "入口逻辑执行成功，已进入神界专属副本")
        return True
       
    def _副本内检查钩子(self) -> str | None:
        if  self.更新区域任务次数(self.游戏配置.区域.神界大陆.神界专属副本内boss次数标签.元组,None,"剩|余"):
            if self.任务状态.剩余次数 == 0:
                调试器.state(self.调试分类, "副本内检查次数已用完，退出副本")
                self.退出副本()
                return "完成"
            else:
                调试器.debug(self.调试分类, f"副本内剩余次数: {self.任务状态.剩余次数}")
        return None