# tasks/xiangmo.py
"""
降魔任务定义
"""

from typing import Optional, Tuple
from core.utils import 匹配分组关键字, 提取次数
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from core.debug import 调试器
import time
import re


@任务定义(
    任务ID="xiangmo",
    任务名称="降魔",
    调试模式=True,
    任务类型="每日任务",
    优先级=10,
    地图关键字="降魔",   
    工作时间开始=10, 
    提前进场秒数=0,
    启用自动战斗=True,
    启用自动走位=False,
    启用摇人按钮=True,
    启用响应召唤=True,
    召唤响应优先级模式="高优先级",
    召唤启用任务完成状况动态管理=True,
    召唤完成任务响应所有层级=True,
    召唤未完成任务响应当前层级=True,
    状态_协助剩余次数=3,
    状态_上次次数核查时间=0,
    状态_上次目标血量=0,
    状态_上次目标血量变化时间=0,

)
class 降魔任务(战斗任务执行器):
    """降魔任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)       
       
    def 执行入口逻辑(self) -> bool:
        """执行降魔入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0 and self.任务状态.协助剩余次数 <= 0:
            调试器.state(self.调试分类,"今日次数已用完，跳过执行")
            return False
        
        # 2. 进入跨服战场页面
        if not self.页面.主界面操作.进入首领页面():
            调试器.error(self.调试分类, "进入首领页面失败，入口逻辑中断")
            return False
      
        # 3. 进入专属页面
        if not self.页面.首领任务.降魔.点击右侧降魔页面():
            调试器.error(self.调试分类, f"点击右侧专属降魔失败，区域: {self.动态标签.首领页面右侧标签.降魔.元组}")
            return False
        
        # 等待刷新时间，强制等待服务器时间同步
        time.sleep(max(0.5, self.游戏配置.刷新等待秒))
        self.线程.刷新截图()

        # 4. 更新剩余次数        
        if not self.更新区域任务次数(self.游戏配置.区域.降魔.降魔页面剩余次数区域标签.元组):
            调试器.warning(self.调试分类, "读取降魔次数失败，仍继续尝试")
            # 注意：原代码这里直接return False，保持原逻辑
            return False
        协助次数文字=self.辅助识别器.获取区域文字(self.游戏配置.区域.降魔.降魔页面协助剩余次数区域标签.元组)
        self.任务状态.协助剩余次数=提取次数(协助次数文字)
        self.任务状态.上次次数核查时间=time.time()

        if self.是否在副本中():
            调试器.state(self.调试分类, "已进入副本，跳过执行")
            return False

        # 5. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"读取次数后确认已用完(剩余{self.任务状态.剩余次数})")
            return False
        if not self.检查刷新时间():
            调试器.state(self.调试分类, "刷新时间未到，等待下次调度")
            return False
        
        if not self.页面.首领任务.降魔.进入降魔副本():
            调试器.error(self.调试分类,  "进入降魔副本失败，入口逻辑中断")
            return False
        调试器.state(self.调试分类, "入口逻辑执行成功，已进入降魔副本")
        return True
    
    def 检查刷新时间(self)->bool:
        降魔定位区域=self.辅助识别器.查找图片单结果(self.游戏配置.区域.降魔.降魔页面当前层龙头标识区域标签.元组, "降魔定位.bmp", )
        if 降魔定位区域 is None:
            调试器.warning("降魔", "降魔定位失败，请检查配置")
            return False
        时间区域=降魔定位区域[0] + 52,降魔定位区域[1] + 191,降魔定位区域[0] + 167,降魔定位区域[1] + 226
        秒数=self.辅助识别器.获取刷新秒数(时间区域)
        调试器.debug("降魔", f"获取刷新时间: {秒数}")
        if 秒数 is not None:
            self.任务状态.下次刷新时间 = time.time() + 秒数
            if 秒数<=self.任务配置.提前进场秒数:
                调试器.state("降魔", f"刷新倒计时: {秒数}秒")
                return True
        return False
    def _召唤响应动态检查(self, 召唤信息: dict) -> Optional[bool]:
        """
        动态检查是否允许响应召唤（子类可覆盖，只读）
        
        ⚠️ 此方法必须是只读的：
        - 可以读取：self.任务状态、self.公共变量、self.是否在副本中()
        - 禁止修改：任何状态字段、任何游戏操作
        
        参数:
            召唤信息: {"玩家名": "xxx", "副本名": "xxx", "层数": 8, "类型": "协助"}
        
        返回:
            True: 允许响应
            False: 拒绝响应
            None: 进下一步条件处理
        
        示例:
            # 战斗中不接受召唤
            if self.是否在副本中():
                return False
        """
        if self.任务状态.剩余次数<=0 and self.任务状态.协助剩余次数<=0:
            调试器.state(self.调试分类, "今日次数已用完，跳过响应")
            return False
        return None
    

    def _降魔协助强制检查次数退出(self) ->str|None:
        if self.任务状态.剩余次数>0:
            return
        if self.任务状态.上次次数核查时间+600>time.time():
            return
        self.任务状态.上次次数核查时间=time.time()
        self.执行入口逻辑()
        if self.任务状态.协助剩余次数==0 and self.任务状态.剩余次数==0:
            调试器.state(self.调试分类, "已用完协助次数，跳过执行")
            self.退出副本()
            return "已用完协助次数"      
        return 
    def 检查退出条件(self) -> bool:
        if self.公共变量.地图切换时间 <time.time()-600:
            调试器.state(self.调试分类, "任务持续超过10分钟，跳过执行")
            return True
        return super().检查退出条件()
    
    def _战斗前钩子(self) -> str | None:
        
        return  self._降魔协助强制检查次数退出()
    
    def _领取奖励检查钩子(self) -> str | None:
        time.sleep(1.2)
        return self._降魔协助强制检查次数退出()
    

    
    def _副本内检查钩子(self): 
        血量=self.辅助识别器.获取目标血量
        调试器.debug(self.调试分类, f"目标血量: {血量}")
        if 血量 is None:
            return
        if 血量!=self.任务状态.上次目标血量:
            self.任务状态.上次目标血量=血量
            self.任务状态.上次目标血量变化时间=time.time()
            调试器.debug(self.调试分类, f"目标血量变化: {血量}")
            return
        if 血量>0 and 血量==self.任务状态.上次目标血量 and 600> time.time()-self.任务状态.上次目标血量变化时间>20:
            调试器.debug(self.调试分类, f"目标血量无变化: {血量}")
            return self.退出副本()