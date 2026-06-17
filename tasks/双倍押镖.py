# tasks/shuangbeiyabiao.py
"""
双倍押镖任务定义
"""
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from typing import Optional, Tuple, List
from core.utils import 匹配分组关键字, 解析时间文字,缩放区域,提取次数,是否为今天
from core.debug import 调试器
import time
from core.recognition import OCRResult, ocr
import re

@任务定义(
    任务ID="shuangbeiyabiao",
    任务名称="双倍押镖",
    调试模式=True,
    任务类型="每日任务",
    优先级=10,
    地图关键字="上古战场|上古战|上古,场", 
    工作时间开始=11,
    工作时间段列表="11:00-12:00,16:00-17:00,21:00-22:00",
    提前进场秒数=0,
    默认攻击模式="和平模式",
    启用自动战斗=False,
    接取高级镖车=True,
    上一次完成时间=0,
)
class 双倍押镖任务(战斗任务执行器):
    """双倍押镖任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
   
    def 执行入口逻辑(self) -> bool:
        """执行双倍押镖入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        #这段主要是为了完成后不进入押镖检查，存在漏检查风险
        if not self.是否在副本中():          
           
            if 是否为今天(self.任务配置.上一次完成时间):            
                调试器.debug(self.调试分类, "今日已执行，跳过执行")
                self.任务状态.剩余次数 = 0
                return False
            #1. 检查剩余次数
            if self.任务状态.剩余次数 <= 0:
                调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
                return False
        
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug(self.调试分类, "展开右上角任务帘失败")
            return False

        if not self.页面.主界面操作.点击双倍押镖上标():    
            调试器.debug(self.调试分类, "点击双倍押镖上标失败")
            return False
        
        if not self.页面.主界面操作.进入双倍押镖副本():     
            调试器.debug(self.调试分类, "进入双倍押镖副本失败")
            return False
               
        # 等待刷新时间，强制等待服务器时间同步
        time.sleep(max(0.5, self.游戏配置.刷新等待秒))
        self.线程.刷新截图()

        # 3. 更新次数    
        if not self.更新区域任务次数(self.游戏配置.区域.双倍押镖.双倍押镖次数标签.元组,None,f"/"):
            调试器.warning(self.调试分类, "读取双倍押镖次数失败，入口逻辑中断")
            return False
        调试器.debug(self.调试分类, f"剩余次数: {self.任务状态.剩余次数}")
        
        #为了统一刷新次数，这个押镖是反着的，将0设置为有，将2设置为0
        if self.任务状态.剩余次数==0:
            self.任务状态.剩余次数=1

        if self.任务状态.剩余次数==2:
            self.任务状态.剩余次数=0
            #这段主要是为了完成后不进入押镖检查，存在漏检查风险
            self.任务配置.上一次完成时间=time.time()
            调试器.debug(self.调试分类, f"导出配置到文件")
            任务定义.导出配置到JSON(self.线程.窗口名称,线程=self.线程)      
        # 4. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"读取次数后确认为0，次数已用完")
            # if self.是否在副本中():
            self._等待中借调普通任务()
            return False
        self._接取镖车()

        调试器.state(self.调试分类, "入口逻辑执行成功，已进入双倍押镖副本")
        return True
    def 检查退出条件(self) -> bool:
        """检查是否满足退出条件"""        
        静止超时 = self.公共变量.获取静止时长() > self.静止超时秒数*3
        return  静止超时 
    def _副本内检查钩子(self) -> str | None:
        截图=self.线程.截图
        if 截图 is None:
            截图= self.线程.刷新截图()
        if 截图 is None:
            return None
        filter_config = {
                "color_range": "110,255,0,16,0,16|20,50,150,255,0,16",                 
                "keep_color": True,
                "background": "black"
            }
        押运情况文字=self.线程.文字识别器.recognize_text(截图, self.游戏配置.区域.双倍押镖.双倍押镖副本内押镖状态区域.元组,filter_config)
        # 匹配押镖关键字，如果是押运中，什么都不管。如果是..点击押运。如果没有此类文字，检查是否是其他状态
        if 匹配分组关键字(押运情况文字, "车,动中"):
            调试器.state(self.调试分类, "押镖任务中")
            return 
        elif 匹配分组关键字(押运情况文字, "车,停|车,止"):
            调试器.state(self.调试分类, "押镖任务开始")
            self.通用操作.点击区域(self.游戏配置.区域.双倍押镖.双倍押镖自动押镖按钮.元组)
            return 
        if self.公共变量.获取静止时长() > self.静止超时秒数*2:
           if  self.执行入口逻辑():
              return "检查重新押镖"            

        return None
    def _领取奖励检查钩子(self) -> str | None:
        time.sleep(self.游戏配置.默认等待秒)
        self.线程.刷新截图()
        if self.页面.创建_通用点击文字验证文字切换(
            self.游戏配置.区域.双倍押镖.双倍押镖再次押镖确定按钮.元组,
            "确|定",
            self.游戏配置.区域.双倍押镖.双倍押镖次数标签.元组,
            "今日|押镖|次数",
        ).执行():            

            if not self.更新区域任务次数(self.游戏配置.区域.双倍押镖.双倍押镖次数标签.元组,None,f"/"):
                调试器.warning(self.调试分类, "读取双倍押镖次数失败，入口逻辑中断")
                return "未能正确获取次数"
            调试器.debug(self.调试分类, f"剩余次数: {self.任务状态.剩余次数}")
            
            if self.任务状态.剩余次数==2:
                self.任务状态.剩余次数=0
                #这段主要是为了完成后不进入押镖检查，存在漏检查风险
                self.任务配置.上一次完成时间=time.time()
                调试器.debug(self.调试分类, f"导出配置到文件xxxx")
                任务定义.导出配置到JSON(self.线程.窗口名称,线程=self.线程) 
            # 4. 再次检查次数
            if self.任务状态.剩余次数 <= 0:
                调试器.state(self.调试分类, f"读取次数后确认为0，次数已用完")
                if self.是否在副本中():
                    self._等待中借调普通任务()
                return "退出"
            self._接取镖车()
            return "接取镖车"
        
        return None
    
    def _接取镖车(self) -> None:
        if self.任务配置.接取高级镖车:
            点击区域=self.游戏配置.区域.双倍押镖.双倍押镖接取高级镖车按钮.元组
        else:
            点击区域=self.游戏配置.区域.双倍押镖.双倍押镖接取低级镖车按钮.元组
        self.页面.创建_通用点击文字验证文字切换(
            点击区域,
            "接|取",
            self.游戏配置.区域.双倍押镖.双倍押镖自动押镖按钮.元组,
            "自动|押镖"
            ).执行()
        return

