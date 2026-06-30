# tasks/zhuzaizhanchang.py
"""
主宰战场任务定义
"""

import random
import re

from rich.repr import T

from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from typing import Optional, Tuple, List
from core.utils import 匹配分组关键字, 解析时间文字,缩放区域,提取次数
from core.debug import 调试器
import time
from core.recognition import OCRResult, ocr
from pydantic import Field
from datetime import datetime


@任务定义(
    任务ID="zhuzaizhanchang",
    任务名称="主宰战场",
    调试模式=True,
    任务类型="定时任务",
    优先级=18,
    地图关键字="主宰", 
    工作时间开始=0,
    提前进场秒数=18,#这个设置是防止胡乱读取的秒数
    启用位置复查=True,
    位置复查目标半径=10,
    启用响应召唤=True,
    次数刷新区间列表="10:59-11:10,15:59-16:10,21:14-21:20",
    击杀顺序="1,2,3,4,5",
    子任务队列="1,2,3,4,5",
    状态_子任务刷新情况=Field(default_factory=dict),
    状态_移动开始时间=0,
    状态_当前子任务ID="",
)
class 主宰战场任务(战斗任务执行器):
    """主宰战场任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
        self.BOSS坐标 = {
            "1": (181,200),
            "2": (300, 180),
            "3": (418, 200),
            "4": (220, 328),
            "5": (380, 330)
        }
        self.准备时间段 = [
            ("10:59:00", "11:00:10"),
            ("15:59:00", "16:00:10"),
            ("21:14:00", "21:15:10"),            
        ]
        self.当前子任务队列  = [1,2,3,4,5]
        #并不是好主意，增加2个执行器参数记录当前循环是否有抢归属按钮以及是否在准备时间见
        self._是否在准备时间 = False
        self._当前循环是否有抢归属按钮 = False
    def 执行入口逻辑(self) -> bool:
        """执行主宰战场入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False        
      
        if not self.页面.主界面操作.进入跨服战场页面():
            调试器.debug(self.调试分类, "进入跨服战场页面失败，入口逻辑中断")
            return False
        
        if not self.页面.跨服战场.主宰.进入主宰战场页面():    
            调试器.debug(self.调试分类, "进入主宰页面失败")
            return False
        
        # 等待刷新时间，强制等待服务器时间同步
        time.sleep(max(0.5, self.游戏配置.刷新等待秒))
        截图 =self.线程.刷新截图()       
        if 截图 is None:
            return False
        filter_config = {
                "color_range": "20,50,150,255,0,16",  
                "keep_color": True,
                "background": "black"
            }
        if not self.更新区域任务次数(self.游戏配置.区域.主宰.主宰综合信息页面主宰数量区域标签.元组,filter_config,f"/") :
            调试器.debug(self.调试分类, f"读取主宰数量失败")
            return False
        if self._是否为主宰准备时间() :
            self.任务状态.剩余次数=5 
        # 4. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"读取次数后确认为0，次数已用完")
            if 匹配分组关键字(self.线程.当前地图,"主宰"):
                self.退出副本()
            return False
       
        
        # 5. 点击进入副本 
        调试器.debug(self.调试分类, "步骤5: 点击进入主宰战场副本")
        if not self.页面.跨服战场.主宰.进入主宰战场副本():
            调试器.error(self.调试分类, "点击挑战按钮失败，入口逻辑中断")
            return False

        调试器.state(self.调试分类, "入口逻辑执行成功，已进入主宰战场副本")
        return True
       

    def _是否为主宰准备时间(self) -> bool:
        """判断当前时间是否为 准备时间段"""        
        当前 = datetime.now().time()
        
        for 开始, 结束 in self.准备时间段:
            开始时刻 = datetime.strptime(开始, "%H:%M:%S").time()
            结束时刻 = datetime.strptime(结束, "%H:%M:%S").time()
            if 开始时刻 <= 当前 <= 结束时刻:
                return True
        return False

    # ==================== 位置复查（覆盖基类） ====================
    def _当前所处BOSS范围ID(self) -> Optional[str]:
        当前坐标 = self.辅助识别器.获取当前玩家坐标()
        if 当前坐标 is None:
            调试器.debug(self.调试分类, "位置复查: 无法获取当前坐标")
            return None

        当前x, 当前y = 当前坐标
        for ID, 坐标 in self.BOSS坐标.items():
            目标x, 目标y = 坐标
            距离 = ((当前x - 目标x) ** 2 + (当前y - 目标y) ** 2) ** 0.5
            if 距离 <= self.任务配置.位置复查目标半径:
                return ID
        return "0"

    def _获取当前子任务ID(self) -> Optional[str]:
        '''
        获取当前任务ID
        按照击杀顺序进行，如果击杀顺序为空，则随机选择一个任务
        如果没有课击杀BOSS，则返回None
        返回击杀顺序的第一个可执行任务ID
        只有当只剩余泰坦的时候才返回泰坦（5号boss）
        返回值：
        - str: 当前任务ID
        - None: 无当前任务        
        '''
        self.更新同步子任务状态()#将子任务刷新时间重置完成，如果存在刷新时间，什么都不做，不存在，刷新时间重置为0
        需要处理的任务 = self.获取已刷新任务列表()
        调试器.debug(self.调试分类, f"需要处理的任务: {需要处理的任务}")
        if not 需要处理的任务:
            调试器.debug(self.调试分类, "无已刷新任务")            
            return None
              
        击杀顺序= self.任务配置.击杀顺序
        if 击杀顺序 == "":
            return str(random.choice(需要处理的任务))
        击杀顺序列表 = [x.strip() for x in 击杀顺序.split(",") if x.strip()]        
        for 队列号 in 击杀顺序列表:
            if int(队列号) in 需要处理的任务:
                return 队列号
        return str(random.choice(需要处理的任务))
    
    def _检查是否有抢归属按钮(self) -> bool:
        """有抢归属按钮证明附近有BOSS"""
        if self.辅助识别器.区域包含文字(self.游戏配置.区域.主宰.主宰抢归属按钮区域.元组,"抢|归|属"):
             self._当前循环是否有抢归属按钮 = True
             return True
        self._当前循环是否有抢归属按钮 = False
        return False
    def _检查位置复查(self) -> Optional[str]:
        """
        检查并调整角色位置到当前子任务boss坐标

        返回:
            None: 已在范围内，不需要复查
            "移动中": 正在移动或已触发移动
            "无新任务，退出副本": 没有可处理的子任务

        """
         # 在这里更新执行器属性，并不是好的设计
        if self._是否为主宰准备时间() :
            self._是否在准备时间=True
        else:
            self._是否在准备时间=False

        # 1. 检查是否有抢归属按钮,并更新执行器属性，并不是好的设计
        if self._检查是否有抢归属按钮():
            return None
        
        # 1. 检查位置复查开关
        if not self.任务配置.启用位置复查:
            return None
     
        

        静止时长 = self.公共变量.获取静止时长()
        移动已耗时 = (
            time.time() - self.任务状态.移动开始时间
            if self.任务状态.移动开始时间 > 0
            else 0
        )
        当前玩家所在BOSS范围ID = self._当前所处BOSS范围ID()

        # 2. 检查是否正在移动,是否移动到位置
        if self.任务状态.移动开始时间 > 0 and 移动已耗时 < 20 and 静止时长<=3:
            #在移动时间范围，且角色静止时间小于3秒，则认为正在移动
            if 当前玩家所在BOSS范围ID is not None and self.任务状态.当前子任务ID!="" and 当前玩家所在BOSS范围ID== self.任务状态.当前子任务ID:                
                # 移动结束，位置复查次数重置为0
                self.任务状态.移动开始时间 = 0.0
                self.任务状态.位置复查次数 = 0
                return None
            return "移动中"
        
        # 3. 非移动如果不能正确获取当前位置，则返回None
        if 当前玩家所在BOSS范围ID is None:
            return None
        #考虑到被召唤等原因，只要当前玩家在BOSS范围，则返回None
        if 当前玩家所在BOSS范围ID!="0":
            return None
                
        当前子任务ID= self._获取当前子任务ID()                       
        
        # 4. 无已刷新任务，在入口逻辑核查，确定是否完成任务，（入口逻辑已加入了退出条件）退出副本
        if 当前子任务ID is None:
            调试器.debug(self.调试分类, "位置复查: 无已刷新任务，退出副本")
            self.执行入口逻辑()
            return "无新任务，退出副本"        
               
        self.任务状态.当前子任务ID = 当前子任务ID

        # 6. 当前位置和当前子任务ID一致，不需要移动
        if 当前玩家所在BOSS范围ID == 当前子任务ID:
            self.任务状态.移动开始时间 = 0.0
            self.任务状态.位置复查次数 = 0
            return None
        
     
        self._大地图识别移动检查()

        # 画面还在变化 → 正在移动中
        调试器.trace(
            self.调试分类,
            f"位置复查: 移动中(静止{静止时长:.1f}秒，已耗时{移动已耗时:.0f}秒)",
        )

        return "移动中"
    def _获取boss坐标(self, 子任务ID: str) -> Optional[Tuple[int, int]]:
        """获取指定子任务的boss坐标"""
        boss坐标字典 = self.BOSS坐标
        if not boss坐标字典:
            return None

        坐标 = boss坐标字典.get(子任务ID)
        if not 坐标 or len(坐标) < 2:
            return None

        return (坐标[0], 坐标[1])

    def _大地图识别移动检查(self) -> None:
        """打开大地图，识别刷新时间，点击目标BOSS位置移动"""

        # 1. 打开大地图
        if not self.通用操作.打开大地图():
            调试器.debug(self.调试分类, "未打开中间地图")
            return

        # 2. 识别副本内刷新时间
        if not self._是否在准备时间:             
           self._识别全部刷新时间("主宰副本小地图BOSS刷新情况标签")

        需要处理的任务 = self.获取已刷新任务列表()
        调试器.debug(self.调试分类, f"副本内识别刷新时间:需要处理的任务: {需要处理的任务}")
        if not 需要处理的任务:
            调试器.debug(self.调试分类, "副本内识别刷新时间:无已刷新任务")
            self.通用操作.关闭大地图()
            #找不到任务的时候复查入口逻辑判断是否需要退出
            self.执行入口逻辑()
            return 

        子任务ID = self.任务状态.当前子任务ID 
        if 子任务ID=="" or 子任务ID =="0":
            return
        
        if int(子任务ID) not in 需要处理的任务:
            调试器.debug(self.调试分类, "位置复查: 无已刷新任务")
            self.通用操作.关闭大地图()
            return        
        

        移动目标区域 = getattr(
            self.游戏配置.区域.主宰,
            f"主宰副本小地图BOSS坐标标签{子任务ID}",
            None,
        )

        if 移动目标区域 is None:
            调试器.warning(self.调试分类, f"位置复查: 未找到子任务{子任务ID}的移动目标区域")
            self.通用操作.关闭大地图()
            return

        # 3. 点击目标坐标
        self.通用操作.点击区域(移动目标区域.元组, 3, 0.08)

        # 4. 记录移动开始时间
        self.任务状态.移动开始时间 = time.time()

        # 5. 关闭地图
        if not self.通用操作.关闭中间可能存在的窗口():
            调试器.debug(self.调试分类, "未关闭中间地图")

    # ==================== 刷新时间识别（公共方法） ====================

    def _识别全部刷新时间(self, 区域前缀: str) -> None:
        """
        循环识别6个BOSS的刷新时间，更新子任务刷新情况

        参数:
            区域前缀: 区域配置的属性名前缀
                      入口逻辑用 "神界战场页面刷新时间标签"
                      副本内用 "神界战场副本刷新时间标签"
        """
        filter_config = {
                "color_range": "110,255,0,16,0,16|0,50,150,255,0,16",  
                "keep_color": True,
                "background": "black"
            }
        for i in range(5):
            index = i + 1
            属性名 = f"{区域前缀}{index}"
            区域对象 = getattr(self.游戏配置.区域.主宰, 属性名, None)
            if 区域对象 is None:
                调试器.warning(self.调试分类, f"未找到区域配置: 诸神遗迹.{属性名}")
                continue
            区域坐标 = 区域对象.元组
            秒数 = self.辅助识别器.获取刷新秒数(区域坐标, filter_config, "已|己")
            if 秒数 is not None and 秒数 >=18:
                调试器.debug(self.调试分类, f"刷新时间[{index}]: {秒数}秒")
                self.任务状态.子任务刷新情况[str(index)] = time.time() + 390

    
    def 检查退出条件(self) -> bool:
        """检查是否满足退出条件"""
        无目标超时 = self.公共变量.获取无目标时间() > self.无目标超时秒数*2
        静止超时 = self.公共变量.获取静止时长() > self.静止超时秒数*2
        
        调试器.debug(self.调试分类, f"退出条件检查: 无目标超时({self.无目标超时秒数}s)={无目标超时}, 静止超时({self.静止超时秒数}s)={静止超时}")
        
        if 无目标超时 and 静止超时 :
            self._大地图识别移动检查()           

        return False
    
    
    def 检查自动战斗走位前置条件(self) -> bool:
        if self._当前循环是否有抢归属按钮:
            return True
        if not self._是否在准备时间:
            return True
        return False
    
     #覆盖检查召唤响应，在打boss不响应
    def _检查召唤响应(self) -> bool:
        # 全局总开关
        if not self.游戏配置.玩家.启用召唤响应:
            # 调试器.debug(self.调试分类, "未启用召唤响应")
            return False
        if not self.任务配置.启用响应召唤:  
            # 调试器.debug(self.调试分类, "未启用响应召唤")          
            return False
        if self._当前循环是否有抢归属按钮:
            # 调试器.debug(self.调试分类, "当前循环有抢归属按钮")
            return False
        if self._是否在准备时间:
            # 调试器.debug(self.调试分类, "当前在准备时间")
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
            if self.页面.创建_通用点击文字验证文字切换(
                self.游戏配置.区域.主界面.请求协助按钮窗口区域.元组,
                "前|往",
                self.游戏配置.区域.主界面.请求协助按钮窗口区域.元组,
                "前|往",
                False
            ).执行():
                time.sleep(0.3)
                self.检查调整自动战斗状态()
                time.sleep(0.3)
                self.检查调整自动战斗状态()
                time.sleep(0.3)
                self.检查调整自动战斗状态()
            调试器.debug(self.调试分类, "已响应召唤")            
            return True      
        return False
    
    def _检查点击摇人按钮(self):
        if self.任务配置.启用摇人按钮:
            if time.time() - self.任务状态.上次点击摇人按钮时间 > 61:
                if self.页面.创建点击图片操作(self.游戏配置.区域.主界面.摇人按钮区域标签.元组,"召集按钮.bmp").执行():
                    self.任务状态.上次点击摇人按钮时间 = time.time()

    
    #===========================抢怪相关方法===========================
    def _执行抢怪操作(self) -> bool:
        return self._执行抢归属动作主宰类副本()

    def _是否抢怪阶段(self) -> bool:
        """
        判断是否进入抢怪阶段
        
        条件：
        - 启用抢怪模式
        - 有目标（能估算死亡时间）
        - 预计死亡时间 < 抢怪触发秒数
        
        返回:
            True: 抢怪阶段

            =================需要补充，一旦抢怪开始，本任务30秒内不改变抢怪模式
        """
        if not self.任务配置.启用抢怪模式:            
            return False
        filter_config = {              
                "color_diff": "8-80,255,80,255,80,255",
                "keep_color": True,
                "background": "black"
            }
        血量文字=self.辅助识别器.获取区域文字(self.游戏配置.区域.主宰.主宰BOSS血量显示区域.元组,filter_config)
        血量=提取次数(血量文字)
        if 血量<=100 and 血量>0:
            self.公共变量.记录最小血量=血量
            if self.公共变量.记录最小血量<=self.任务配置.低于此血量抢怪:
                self.公共变量.抢怪开始=True
            else:
                self.公共变量.抢怪开始=False
        return self.公共变量.抢怪开始        
    

    #此策略永远在此本不可用
    def _策略_回城回血(self) -> bool:
        return False
    def _策略_高频死亡避让(self):
        return False
    def _是否启用高战避让(self):
        return False

       