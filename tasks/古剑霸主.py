# tasks/gujianbazhu.py
"""
古剑霸主任务定义
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
    任务ID="gujianbazhu",
    任务名称="古剑霸主",
    调试模式=True,
    任务类型="定时任务",
    优先级=18,
    地图关键字="剑,中心", 
    工作时间开始=18,
    工作时间结束=19,
    提前进场秒数=0,
    次数刷新区间列表="18:00-18:10"
)
class 古剑霸主任务(战斗任务执行器):
    """古剑霸主任务执行器"""
    
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
        """执行古剑霸主入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False
        
        当前页面= self.验证当前打开页面()
        调试器.debug("上古剑冢", f"当前页面: '{当前页面}'")
        if 当前页面 != "古剑":          
            # 2.1 进入跨服战场页面
            调试器.debug("上古剑冢", "步骤1: 进入跨服战场页面")
            if not self.页面.主界面操作.进入跨服战场页面():
                调试器.error("上古剑冢", "进入跨服战场页面失败，入口逻辑中断")
                return False
            调试器.debug("上古剑冢", "跨服战场页面进入成功")
            
            # 2.2 进入古剑页面
            调试器.debug("上古剑冢", "步骤2: 进入古剑页面")
            if not self.页面.跨服战场.古剑.点击右侧古剑页面():
                调试器.error("上古剑冢", "进入古剑页面失败，入口逻辑中断")
                return False
            调试器.debug("上古剑冢", "古剑页面进入成功")

            # 等待刷新时间，强制等待服务器时间同步
            time.sleep(max(0.5, self.游戏配置.刷新等待秒))
            self.线程.刷新截图()
            
        else:
            调试器.debug("上古剑冢", "当前已在古剑页面，跳过进入步骤")

        # 3. 更新次数    
        截图 = self.线程.截图
        if 截图 is None:
            截图= self.线程.刷新截图()
        if 截图 is None:
            return False
        filter_config = {
                "color_range": "110,255,0,16,0,16|25,100,150,255,0,16",  
                "keep_color": False,
                "background": "black"
            }
        ocr_result = self.线程.文字识别器.recognize_text(截图,self.游戏配置.区域.古剑.古剑页面古剑霸主刷新时间区域标签.元组,filter_config)
       
        if ocr_result:
            if 匹配分组关键字(ocr_result, "已|刷|新"):                
                self.任务状态.剩余次数=1                
            else:
                刷新时间秒数=解析时间文字(ocr_result)
                if 刷新时间秒数 is not None and 刷新时间秒数 > 0:              
                    self.任务状态.剩余次数= 0                   
                 
        # 4. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"读取次数后确认为0，次数已用完")
            return False
       
        
        # 5. 点击进入秘境  
        if not self.页面.创建_通用点击区域验证文字切换 ( 
                self.游戏配置.区域.古剑.古剑页面古剑霸主点击区域标签.元组,           
                self.游戏配置.区域.古剑.古剑页面前往按钮标签.元组,
                "前|往"
                ).执行():
                调试器.debug(self.调试分类, f"{self.调试分类}: 点击BOSS入口后未检测到前往按钮，跳过")
                return False

        调试器.debug(self.调试分类, "步骤5: 点击进入古剑霸主副本")
        if not self.页面.创建_通用点击区域验证文字切换 ( 
                self.游戏配置.区域.古剑.古剑页面前往按钮标签.元组,           
                self.游戏配置.区域.主界面.小地图地图名显示标签.元组,
                "中心,剑"
                ).执行() :
                调试器.debug("上古剑冢", f"{self.调试分类}: 进入副本失败，入口逻辑中断")
                return False

        调试器.state(self.调试分类, "入口逻辑执行成功，已进入古剑霸主副本")
        return True
       
   