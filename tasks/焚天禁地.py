# tasks/fentianjindi.py
"""
焚天禁地任务定义
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
    任务ID="fentianjindi",
    任务名称="焚天禁地",
    调试模式=True,
    任务类型="定时任务",
    优先级=18,
    地图关键字="炼狱禁地|炼,禁地", 
    工作时间开始=19,
    工作时间结束=20,
    提前进场秒数=0,
    次数刷新区间列表="19:00-19:30",
    执行日期规则="星期1,3,5,7",
    次数刷新区间条件="星期1,3,5,7",
)
class 焚天禁地任务(战斗任务执行器):
    """焚天禁地任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
      
    # 验证当前打开页面
    def 验证当前打开页面(self) -> str:
        '''
        验证当前打开页面,跨服战场多次打开存在不跳右侧标签的BUG
        返回:
        "战场" | "坐骑" | "古剑" | "组队" | "陨圣" | "其他"
        '''
        文字识别器= self.线程.文字识别器
        截图=self.线程.截图
        if 截图 is None:
            截图=self.线程.刷新截图()
        if 截图 is None:
            return "其他"
        当前页面= 文字识别器.recognize_text(截图,self.游戏配置.区域.主界面.中间页面名称区域标签.元组)
        调试器.trace("上古剑冢", f"页面识别结果: '{当前页面}'")
        if 匹配分组关键字(当前页面, "战|场") :
            return "战场"
        elif 匹配分组关键字(当前页面, "坐|骑") :
            return "坐骑"
        elif 匹配分组关键字(当前页面, "古|剑") :
            return "古剑"
        elif 匹配分组关键字(当前页面, "组|队") :
            return "组队"
        elif 匹配分组关键字(当前页面, "陨|圣") :
            return "陨圣"
        else :
            return "其他"

    def 执行入口逻辑(self) -> bool:
        """执行焚天禁地入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False
        
             
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug(self.调试分类, "展开右上角任务帘失败")
            return False 

        if not self.页面.创建_通用点击图片验证文字切换( 
            self.游戏配置.区域.主界面.第二三排任务区域标签.元组,
            "焚天炎域图标.bmp",
            self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
            "炎域",
            True,   ).执行():    
            调试器.debug(self.调试分类, "进入焚天炎域页面失败")
            return False
        
        if not self.页面.创建_通用点击区域验证文字切换( 
            self.游戏配置.区域.焚天炎域.焚天炎域右侧禁地按钮标签.元组,
            self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
            "禁|地",
            True,   ).执行():    
            调试器.debug(self.调试分类, "进入焚天禁地页面失败")
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
        filter_config = {
                "color_range": "110,255,0,16,0,16|25,100,150,255,0,16",  
                "color_diff": "5-80,255,80,255,80,255",
                "keep_color": False,
                "background": "black"
            }
        if not self.更新区域任务次数(self.游戏配置.区域.焚天炎域.焚天炎域禁地页面禁地次数标签.元组,filter_config):
            调试器.warning(self.调试分类, "读取焚天禁地页面剩余次数失败，入口逻辑中断")
            return False
                 
        # 4. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            if 匹配分组关键字(self.线程.当前地图, "炼狱禁地|炼,禁地"):
                 self.退出副本()
            调试器.state(self.调试分类, f"读取次数后确认为0，次数已用完")
            return False
       
        
        # 5. 点击进入秘境  
        if not self.页面.创建_通用点击区域验证文字切换 ( 
                self.游戏配置.区域.焚天炎域.焚天炎域禁地页面前往挑战标签.元组,           
                self.游戏配置.区域.主界面.小地图地图名显示标签.元组,
                "炼狱|禁地"
                ).执行():
                调试器.debug(self.调试分类, f"{self.调试分类}: 进入副本失败")
                return False
      
        调试器.state(self.调试分类, "入口逻辑执行成功，已进入焚天禁地副本")
        return True
    
    def 检查退出条件(self) -> bool:
        """检查是否满足退出条件"""
        无目标超时 = self.公共变量.获取无目标时间() > self.无目标超时秒数
        静止超时 = self.公共变量.获取静止时长() > self.静止超时秒数
        
        调试器.debug(self.调试分类, f"退出条件检查: 无目标超时({self.无目标超时秒数}s)={无目标超时}, 静止超时({self.静止超时秒数}s)={静止超时}")
        
        if 无目标超时 and 静止超时:
            self.执行入口逻辑()
        return False
    def _领取奖励检查钩子(self) -> Optional[str]:
        if self.执行入口逻辑():
            return "任务结束，退出副本"
        

       
   