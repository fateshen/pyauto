# tasks/juezhanshabake.py
"""
决战沙巴克任务定义
"""
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from typing import Optional, Tuple, List
from core.utils import 匹配分组关键字, 坐标在目标区域内,缩放区域,提取次数
from core.debug import 调试器
from core.recognition import OCRResult, ocr
import datetime
import time

@任务定义(
    任务ID="juezhanshabake",
    任务名称="决战沙巴克",
    调试模式=False,
    任务类型="定时任务",
    优先级=18,    
    地图关键字="沙巴克|沙巴", 
    工作时间开始=20,
    工作时间结束=21,
    工作时间段列表="20:00-20:30",
    次数刷新区间列表="20:00-20:30",
    次数刷新区间条件="星期6",
    提前进场秒数=0,
    执行日期规则="星期6",
    启用位置复查=True,
    启用响应召唤=True,
)
class 决战沙巴克任务(战斗任务执行器):
    """决战沙巴克任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
   
    def 执行入口逻辑(self) -> bool:
        """执行决战沙巴克入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False
        
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug(self.调试分类, "展开右上角任务帘失败")
            return False     

        if not self.页面.主界面操作.点击决战沙巴克上标.执行():    
            调试器.debug(self.调试分类, "决战沙巴克下标进入失败")
            return False
        
        if not self.页面.主界面操作.点击决战沙巴克下标.执行():    
            调试器.debug(self.调试分类, "决战沙巴克下标点击失败")
            return False
        
        if not self.页面.主界面操作.进入决战沙巴克副本.执行():    
            调试器.debug(self.调试分类, "决战沙巴克副本进入失败")
            return False
        
        调试器.state(self.调试分类, "入口逻辑执行成功，已进入决战沙巴克副本")
        return True
       
    def 检查退出条件(self) -> bool:
        """覆盖检查退出条件，这里不需要设置，任务结束会强制弹出"""
        return False
    
    #覆盖检查召唤响应，在皇宫不响应
    def _检查召唤响应(self) -> bool:
        # 全局总开关
        if not self.游戏配置.玩家.启用召唤响应:
            return False
        if not self.任务配置.启用响应召唤:            
            return False
        if 匹配分组关键字(self.线程.当前地图, "皇宫"):
            return False

        # 频率控制：每2秒检查一次
        当前时间 = time.time()
        if 当前时间 - self.公共变量.上次召唤检查时间 < 2:
            return False
        self.公共变量.上次召唤检查时间 = 当前时间
        
        # 识别召唤信息
        召唤信息 = self.辅助识别器.获取召唤信息()
        if not 召唤信息:
            return False
        
        类型名=召唤信息.get("类型", "")
        if 类型名 == "集结令":           
            self.页面.创建_通用点击文字验证文字切换(
                self.游戏配置.区域.主界面.请求协助按钮窗口区域.元组,
                "前|往",
                self.游戏配置.区域.主界面.请求协助按钮窗口区域.元组,
                "前|往",
                False
            ).执行()
            调试器.debug(self.调试分类, "已响应召唤")  
            time.sleep(self.游戏配置.默认等待秒)
            self.检查调整自动战斗状态()          
            return True      
        return False
    def _检查点击摇人按钮(self):
        if self.任务配置.启用摇人按钮:
            if 匹配分组关键字(self.线程.当前地图, "皇宫"):
                if time.time() - self.任务状态.上次点击摇人按钮时间 > 61:
                    if self.页面.创建点击图片操作(self.游戏配置.区域.主界面.摇人按钮区域标签.元组,"召集按钮.bmp").执行():
                        self.任务状态.上次点击摇人按钮时间 = time.time()
    #覆盖位置检查，不在皇宫向皇宫跑路
    def _检查位置复查(self) -> str | None:
        
        if 匹配分组关键字(self.线程.当前地图, "皇宫"):
            return None        
        
        当前坐标 = self.辅助识别器.获取当前玩家坐标()
        if 当前坐标 is None:
            调试器.warning(self.调试分类, "位置复查: 获取当前坐标失败")
            return "获取当前坐标失败"
        沙巴克皇宫入口范围=85, 82, 89, 86
        if 坐标在目标区域内(当前坐标, 沙巴克皇宫入口范围):  
            self.通用操作.点击区域(self.游戏配置.区域.主界面.决战沙巴克进入房间点击位置范围.元组,3,0.3)          
            return "已点击大门"
        
        if self.线程.获取静止时长() < 3:
             return "None"
        
        if self.通用操作.打开地图移动到(self.游戏配置.区域.主界面.沙巴克外城小地图9080点位.元组):
            调试器.debug(self.调试分类, "已向皇宫大门移动")
            return "已向皇宫大门移动"
        
        return "None"


      