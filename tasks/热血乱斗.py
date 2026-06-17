# tasks/rexueluandou.py
"""
热血乱斗任务定义
"""
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from typing import Optional, Tuple, List
from core.utils import 匹配分组关键字, 解析时间文字,缩放区域,提取次数
from core.debug import 调试器
from core.recognition import OCRResult, ocr
import datetime

@任务定义(
    任务ID="rexueluandou",
    任务名称="热血乱斗",
    调试模式=False,
    任务类型="每日任务",
    优先级=16,    
    地图关键字="热血", 
    工作时间开始=20,
    工作时间结束=21,
    工作时间段列表="20:00-20:16",
    次数刷新区间列表="20:00-20:15",
    提前进场秒数=0,
    执行日期规则="星期1,2,3,4,5",
)
class 热血乱斗任务(战斗任务执行器):
    """热血乱斗任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
   
    def 执行入口逻辑(self) -> bool:
        """执行热血乱斗入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False
        
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug(self.调试分类, "展开右上角任务帘失败")
            return False         
        
        查询异界图标=self.辅助识别器.查找图片单结果(self.游戏配置.区域.主界面.第二三排任务区域标签.元组,"异界夺宝图标.bmp")
       
        if 查询异界图标 is not None:
            weekday=datetime.datetime.today().isoweekday()
            if weekday==1   or weekday==3 or  weekday==5:
                调试器.debug(self.调试分类, "今日是周一、周三、周五，进入异界夺宝")
                self.任务状态.剩余次数=0
                return False

        if not self.页面.主界面操作.点击热血乱斗上标.执行():    
            调试器.debug(self.调试分类, "热血乱斗下标进入失败")
            return False
        
        if not self.页面.主界面操作.点击热血乱斗下标.执行():    
            调试器.debug(self.调试分类, "热血乱斗下标点击失败")
            return False
        
        if not self.页面.主界面操作.进入热血乱斗副本.执行():    
            调试器.debug(self.调试分类, "热血乱斗副本进入失败")
            return False
        
        调试器.state(self.调试分类, "入口逻辑执行成功，已进入热血乱斗副本")
        return True
       
    def 检查退出条件(self) -> bool:
        """覆盖检查退出条件，这里不需要设置，任务结束会强制弹出"""
        return False
    def 检查攻击模式(self) -> None:
        return None
      