# tasks/dianfeng_yuxuan.py
"""
巅峰预选任务定义
"""
import datetime

from core.utils import 缩放区域
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from core.debug import 调试器
import time
import re


@任务定义(
    任务ID="dianfeng_yuxuan",
    任务名称="巅峰预选",
    任务类型="小时任务",
    优先级=5,
    地图关键字="巅,预|选,峰|选,巅|预选",    
    提前进场秒数=0,
    次数刷新间隔小时 = 1 ,
)
class 巅峰预选(战斗任务执行器):
    """巅峰预选任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)       
       
    def 执行入口逻辑(self) -> bool:
        """执行巅峰预选逻辑"""
        调试器.info("巅峰预选", "开始执行入口逻辑")
        #周天修正
        if time.localtime().tm_wday == 6:
            当前时分 = time.localtime().tm_hour * 60 + time.localtime().tm_min
            if 当前时分 >= 1170:
                调试器.debug("巅峰预选", "周天，今日次数已用完，跳过执行")
                self.任务状态.剩余次数 = 0
                self.任务状态.上次次数刷新时间 =datetime.datetime.now().replace(hour=23, minute=0, second=0, microsecond=0).timestamp()
                return True            
           
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("巅峰预选", "今日次数已用完，跳过执行")
            return False
        
        if self.通用操作.领取奖励退出操作():
            调试器.debug("巅峰预选", "执行了领取奖励退出操作")
            time.sleep(1)
            截图=self.线程.刷新截图()

        # 2.检查当前处于的界面状态
        截图= self.线程.截图
        区域= self.游戏配置.区域.主界面.中间页面名称区域标签.元组
        打开页面名称= self.线程.文字识别器.recognize_text(
            截图, 区域
           )
        调试器.trace("巅峰预选", f"主界面页面名称识别: '{打开页面名称}'")
        
        所处页面=""
        if "战场" in 打开页面名称:
            所处页面="战场"
            调试器.debug("巅峰预选", "检测到当前在战场页面，跳过进入战场步骤")
        else:
            打开页面名称= self.线程.文字识别器.recognize_text(
            截图, self.游戏配置.区域.巅峰竞技.巅峰预选页面匹配按钮标签.元组
             ) 
            调试器.trace("巅峰预选", f"匹配按钮文字识别: '{打开页面名称}'")
            if "匹配" in 打开页面名称:
                所处页面="预选"
                调试器.debug("巅峰预选", "检测到当前在巅峰预选页面，跳过所有进入步骤")
        
        if 所处页面=="":
            调试器.debug("巅峰预选", "未在特定页面，步骤1: 进入跨服战场页面")
            # 3. 进入跨服战场页面
            if not self.页面.主界面操作.进入跨服战场页面():
                调试器.error("巅峰预选", "进入跨服战场页面失败，入口逻辑中断")
                return False
            调试器.debug("巅峰预选", "跨服战场页面进入成功")
        
        if 所处页面=="战场" or 所处页面=="":
            # 3.1. 更新次数
            调试器.debug("巅峰预选", "步骤2: 读取跨服页面巅峰次数")
            if not self.更新区域任务次数(self.游戏配置.区域.战场页面.跨服页面巅峰次数标签.元组):
                调试器.warning("巅峰预选", "读取跨服页面巅峰次数失败，入口逻辑中断")
                return False
            if self.任务状态.剩余次数 <= 0:
                调试器.state("巅峰预选", f"跨服页面检查次数已用完(剩余{self.任务状态.剩余次数})")
                return False
            
            调试器.debug("巅峰预选", "步骤3: 进入巅峰竞技页面")
            if not self.页面.跨服战场.巅峰竞技.进入巅峰竞技页面():
                调试器.error("巅峰预选", "进入巅峰竞技页面失败，入口逻辑中断")
                return False
            调试器.debug("巅峰预选", "巅峰竞技页面进入成功")
        
        # 4. 更新剩余次数
        filter_config = {
                "color_range": "110,255,0,16,0,16|25,100,150,255,0,16",  
                "keep_color": True,
                "background": "black"
            }
        调试器.debug("巅峰预选", "步骤4: 读取巅峰预选页面次数")
        if not self.更新区域任务次数(self.游戏配置.区域.巅峰竞技.巅峰预选页面次数标签.元组,filter_config):
            调试器.warning("巅峰预选", "读取巅峰预选页面次数失败，入口逻辑中断")
            return False
        
        # 5. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("巅峰预选", f"巅峰预选页面检查次数已用完(剩余{self.任务状态.剩余次数})")
            return False
      
        # 6. 点击匹配
        调试器.debug("巅峰预选", "步骤5: 点击匹配按钮")
        if not self.页面.跨服战场.巅峰竞技.进入巅峰竞技副本():
            调试器.error("巅峰预选", "点击匹配按钮失败，入口逻辑中断")
            return False
        
        调试器.state("巅峰预选", "入口逻辑执行成功，已开始匹配")
        return True
    
    def 检查攻击模式(self) -> None:
        return None