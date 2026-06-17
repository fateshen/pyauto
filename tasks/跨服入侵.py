# tasks/kuafuruqing.py
"""
跨服入侵任务定义
"""
import datetime

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
    任务ID="kuafuruqing",
    任务名称="跨服入侵",
    调试模式=True,
    任务类型="定时任务",
    优先级=16,
    地图关键字="魔界", 
    工作时间开始=20,
    工作时间段列表="20:30-21:00",
    执行日期规则="除星期6",
    提前进场秒数=0,
    次数刷新区间列表="20:30-20:35,20:45-20:50",
    次数刷新区间条件="除星期6|星期1,2,3,4,5 & 日期单数日" , # 第二个区间只在单数日   
    跨服入侵默认BOSS="苍龙王",
    跨服入侵三首龙任务开启=False,
)

class 跨服入侵任务(战斗任务执行器):
    """跨服入侵任务执行器"""    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
   
    def 执行入口逻辑(self) -> bool:
        """执行跨服入侵入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False
        
        if not self.页面.主界面操作.进入跨服战场页面():
            调试器.debug(self.调试分类, "进入跨服战场页面失败，入口逻辑中断")
            return False

        if not self.页面.跨服战场.跨服入侵.进入跨服入侵页面():  
            调试器.debug(self.调试分类, "进入跨服入侵页面失败")
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
        
  
        三首龙开启情况=self._跨服入侵三首龙是否存在复查()
        if 三首龙开启情况 is not None:
            if 三首龙开启情况 != self.任务配置.跨服入侵三首龙任务开启:                
                self.任务配置.跨服入侵三首龙任务开启=三首龙开启情况
                任务定义.导出配置到JSON(self.线程.窗口名称,线程=self.线程)
                调试器.state(self.调试分类, f"已更新并保存到配置：跨服入侵三首龙任务开启状态为{self.任务配置.跨服入侵三首龙任务开启}")

        bossid=2
        默认BOSS=self.任务配置.跨服入侵默认BOSS
        if  默认BOSS=="苍龙王":
            bossid=4 
        elif  默认BOSS=="吞噬鲲":
            bossid=3
        else:
            bossid=2
        
        if datetime.datetime.now().minute>=45:
            bossid=1
        
        if not self.任务配置.跨服入侵三首龙任务开启 and bossid==1:
            self.任务状态.剩余次数=0
            调试器.state(self.调试分类, f"三首龙未开启，跳过执行")
            return False
        if self.任务配置.跨服入侵三首龙任务开启:
            BOSS选择按钮=self.游戏配置.区域.跨服入侵.获取(bossid)
        else:
            BOSS选择按钮=self.游戏配置.区域.跨服入侵旧.获取(bossid)
        if BOSS选择按钮 is None:
            调试器.error(self.调试分类, f"BOSS选择按钮未找到(bossid={bossid})")
            return False
        
        颜色统计=self.线程.像素分析器.count_colors(截图,BOSS选择按钮.元组,"000DFE,0.95")
        if 颜色统计[0]>2:
            调试器.debug(self.调试分类, "跨服入侵BOSS已被击杀")
            self.任务状态.剩余次数=0
            if self.是否在副本中():
                self.退出副本()
            return True
        
        # 三首龙已击杀
        if bossid==1 and datetime.datetime.now().minute>=48:
            结果= self.辅助识别器.查找图片单结果(self.游戏配置.区域.跨服入侵.跨服入侵页面BOSS选择图标范围标签.元组,目标图标路径="三首龙图标.bmp")
            if 结果:
                调试器.state(self.调试分类, "三首龙已击杀，跳过执行")  
                self.任务状态.剩余次数=0
                return False

        self.通用操作.点击区域(BOSS选择按钮.元组,2)
        if not self.页面.创建_通用点击文字验证文字切换(
            self.游戏配置.区域.跨服入侵.跨服入侵页面挑战按钮标签.元组,
            "挑|战",
            self.游戏配置.区域.跨服入侵.跨服入侵页面挑战确定按钮标签.元组,
            "确|定",
             ).执行():
            调试器.state(self.调试分类, "点击挑战按钮失败")
            return False
        
        if not self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.跨服入侵.跨服入侵页面挑战确定按钮标签.元组,           
            self.游戏配置.区域.主界面.小地图地图名显示标签.元组,
            "魔界",
             ).执行():
            调试器.state(self.调试分类, "进入副本失败，入口逻辑中断")
            return False
        
        self.通用操作.覆盖鼠标提示到边缘()
        调试器.state(self.调试分类, "入口逻辑执行成功，已进入跨服入侵副本")
        return True
    
    def _跨服入侵三首龙是否存在复查(self) -> Optional[bool]:
        截图 = self.线程.截图
        if 截图 is None:
            截图= self.线程.刷新截图()
        if 截图 is None:
            return None
        
        三首龙图片="三首龙图标.bmp"
        if datetime.datetime.now().minute>=40:
           三首龙图片="三首龙图标1.bmp"        
        结果= self.辅助识别器.查找图片单结果(self.游戏配置.区域.跨服入侵.跨服入侵页面BOSS选择图标范围标签.元组,目标图标路径=三首龙图片)
        if 结果 is None:
            return None
        if 结果:
            return True
        return False
    
    def _副本内检查钩子(self) -> str | None:
        截图 = self.线程.截图
        if 截图 is None:
            截图= self.线程.刷新截图()
        if 截图 is None:
            return None
        结果 = self.线程.文字识别器.recognize_result(
            截图, self.游戏配置.区域.跨服入侵.跨服入侵副本奖励确定按钮区域标签.元组
        ) .find("领取|退出|确","group")
        if 结果:    
            self.页面.创建点击区域操作(结果,0.5).执行()
            调试器.state(self.调试分类, "领取奖励退出操作完成")
            self._任务结束复查()
        return 

    def _任务结束复查(self) :
        if datetime.datetime.now().minute>=45:
            截图 = self.线程.截图
            if 截图 is None:
                return None
            颜色统计=self.线程.像素分析器.count_colors(截图,self.游戏配置.区域.跨服入侵.跨服入侵副本三头龙击杀提示区域.元组,"000DFE,0.95")
            if 颜色统计[0]>5:
                调试器.debug(self.调试分类, "跨服入侵BOSS已被击杀")
                self.任务状态.剩余次数=0                
                self.退出副本()
                return "已完成"
        self.执行入口逻辑() 
   
    def 检查退出条件(self) -> bool:
        """检查是否满足退出条件"""
        无目标超时 = self.公共变量.获取无目标时间() > self.无目标超时秒数
        静止超时 = self.公共变量.获取静止时长() > self.静止超时秒数
        
        调试器.debug(self.调试分类, f"退出条件检查: 无目标超时({self.无目标超时秒数}s)={无目标超时}, 静止超时({self.静止超时秒数}s)={静止超时}")
        if 无目标超时 and 静止超时:
            self._任务结束复查()
        return 无目标超时 and 静止超时 