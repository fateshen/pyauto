# tasks/moshenjindi.py
"""
魔神禁地任务定义
"""
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from typing import Optional, Tuple, List
from core.utils import 匹配分组关键字, 缩放区域, 解析时间文字
from core.debug import 调试器
import time
from core.recognition import OCRResult
import re

@任务定义(
    任务ID="moshenjindi",
    任务名称="魔神禁地",
    调试模式=True,
    任务类型="每日任务",
    优先级=10,
    地图关键字="魔神禁地|神禁地|魔神,地", 
    工作时间开始=6,
    工作时间结束=22,
    提前进场秒数=0,  
)
class 魔神禁地任务(战斗任务执行器):
    """魔神禁地任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
   
    def 执行入口逻辑(self) -> bool:
        """执行魔神禁地入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False        
        if self.通用操作.领取奖励退出操作():
            time.sleep(self.线程.游戏配置.默认等待秒)
        if not self.辅助识别器.区域包含文字(self.游戏配置.区域.主界面.中间页面名称区域标签.元组,"魔神|禁地"):          

            if not self.页面.主界面操作.展开右上角任务帘:
                调试器.debug(self.调试分类, "展开右上角任务帘失败")
                return False

            if not self.页面.群星圣域.进入群星圣域页面():    
                调试器.debug(self.调试分类, "进入群星圣域页面失败")
                return False
            else:
                # 等待刷新，页面独有措施
                time.sleep(1.5)
                self.线程.刷新截图()
                time.sleep(1.5)
                self.线程.刷新截图()
            
            if not self.页面.群星圣域.魔神禁地.进入魔神禁地任务页面():    
                调试器.debug(self.调试分类, "进入魔神禁地任务页面失败")
                return False
        
            # 等待刷新时间，强制等待服务器时间同步
            time.sleep(max(0.5, self.游戏配置.刷新等待秒))
            self.线程.刷新截图()

        # 3. 更新剩余次数

        filter_config = {
                "color_range": "110,255,0,16,0,16|20,50,150,255,0,16",                  
                "color_diff": "5-80,255,80,255,80,255",
                "keep_color": False,
                "background": "black"
            }
        调试器.debug(self.调试分类, "步骤2: 读取魔神禁地次数")
        if not self.更新区域任务次数(self.游戏配置.区域.魔神禁地.魔神禁地页面剩余奖励次数范围标签.元组,filter_config,"剩|余|次数"):
            调试器.warning(self.调试分类, "读取魔神禁地次数失败，入口逻辑中断")
            return False
        调试器.debug(self.调试分类, f"剩余次数: {self.任务状态.剩余次数}")

        # 4. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"读取次数后确认为0，次数已用完")
            return False
        
        if not self.辅助识别器.查找图片单结果(缩放区域( self.游戏配置.区域.魔神禁地.魔神禁地页面前往挑战按钮标签.元组,2),"红点.bmp"):
            调试器.debug(self.调试分类, "步骤4: 检测到前往挑战按钮没有红点")
            return False
        
        # 5. 点击进入秘境  
        调试器.debug(self.调试分类, "步骤5: 点击进入魔神禁地副本")
        if not self.页面.群星圣域.魔神禁地.进入魔神禁地副本():
            调试器.error(self.调试分类, "点击挑战按钮失败，入口逻辑中断")
            return False

        调试器.state(self.调试分类, "入口逻辑执行成功，已进入魔神禁地副本")
        return True
       
    