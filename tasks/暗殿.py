# tasks/andian.py
"""
暗殿任务定义
"""

from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from core.debug import 调试器
import time
import re
from core.utils import 匹配分组关键字


@任务定义(
    任务ID="andian_daily",
    任务名称="暗殿任务",
    任务类型="小时任务",
    优先级=5,
    地图关键字="暗殿",
    避让模式使用全局设置= True,
    启用位置复查=True,
    位置复查移动区域 = "729,404,814,467",
    位置复查目标中心 = "37,40",
    回城回血使用全局设置=True,
    提前进场秒数=15,
    次数刷新间隔小时 = 2 ,
)
class 暗殿任务(战斗任务执行器):
    """暗殿任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)       
       
    def 执行入口逻辑(self) -> bool:
        """执行暗殿入口逻辑"""
        调试器.info("暗殿", "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("暗殿", "今日次数已用完，跳过执行")
            return False
        
        # 2. 进入跨服战场页面
        调试器.debug("暗殿", "步骤1: 进入跨服战场页面")
        if not self.页面.主界面操作.进入跨服战场页面():
            调试器.error("暗殿", "进入跨服战场页面失败，入口逻辑中断")
            return False
        调试器.debug("暗殿", "跨服战场页面进入成功")
        
        # 3. 更新剩余次数
        调试器.debug("暗殿", "步骤2: 读取跨服页面暗殿次数")
        if not self.更新区域任务次数(self.游戏配置.区域.战场页面.跨服页面暗殿次数标签.元组):
            调试器.warning("暗殿", "读取跨服页面暗殿次数失败，仍继续尝试")
            # 注意：原代码这里直接return False，保持原逻辑
            return False
        
        # 4. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("暗殿", f"读取次数后确认已用完(剩余{self.任务状态.剩余次数})")
            return False
        
        # 5. 进入暗殿页面
        调试器.debug("暗殿", "步骤3: 进入暗殿页面")
        if not self.页面.跨服战场.暗殿.进入暗殿页面():
            调试器.error("暗殿", "进入暗殿页面失败，入口逻辑中断")
            return False
        调试器.debug("暗殿", "暗殿页面进入成功")
        
        # 6. 检查刷新时间
        调试器.debug("暗殿", "步骤4: 检查刷新时间")
        if not self.检查刷新时间(self.游戏配置.区域.暗殿.暗殿页面刷新时间标签.元组):
            调试器.state("暗殿", "刷新时间未到，等待下次调度")
            return False
        调试器.debug("暗殿", "刷新时间已到，可以进入")
        
        # 7. 更新剩余次数
        调试器.debug("暗殿", "步骤5: 读取暗殿页面次数")
        if not self.更新区域任务次数(self.游戏配置.区域.暗殿.暗殿页面暗殿次数标签.元组):
            调试器.warning("暗殿", "读取暗殿页面次数失败，仍继续尝试")
            return False
        
        if self.扫荡检查逻辑():
            return True

        # 8. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("暗殿", f"二次确认次数已用完(剩余{self.任务状态.剩余次数})")
            return False
        
        # 9. 点击前往挑战
        调试器.debug("暗殿", "步骤6: 点击前往挑战")
        if not self.页面.跨服战场.暗殿.点击暗殿前往挑战():
            调试器.error("暗殿", "点击前往挑战失败，入口逻辑中断")
            return False
        
        调试器.state("暗殿", "入口逻辑执行成功，已进入暗殿副本")
        return True
    
    def 扫荡检查逻辑(self) -> bool:
        """扫荡检查逻辑"""
        截图=self.线程.截图
        count=0        
        if 截图 is None:
            调试器.warning("暗殿", "刷新截图失败，扫荡检查逻辑中断")
            return False
        text = self.线程.文字识别器.recognize_text(截图, self.游戏配置.区域.暗殿.暗殿页面前往挑战按钮标签.元组)
        if 匹配分组关键字(text, "扫|荡" ):
            for i in range(5):   
                self.页面.创建点击区域操作(self.游戏配置.区域.暗殿.暗殿页面前往挑战按钮标签.元组).执行()
                time.sleep(self.游戏配置.战斗.等待.默认等待秒)
                self.线程.刷新截图()
                self.通用操作.领取奖励退出操作()                
                time.sleep(self.游戏配置.战斗.等待.默认等待秒)
                self.线程.刷新截图()
                self.更新区域任务次数(self.游戏配置.区域.暗殿.暗殿页面暗殿次数标签.元组)
                if self.任务状态.剩余次数 <= 0:
                    调试器.state("暗殿", "扫荡完成")
                    return True
                count+=1
                continue
        if count>0:
            调试器.state("暗殿", "扫荡完成")
            return True
        return False