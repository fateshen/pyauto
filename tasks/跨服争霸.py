# tasks/kuafuzhengba.py
"""
跨服争霸任务定义
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
    任务ID="kuafuzhengba",
    任务名称="跨服争霸",
    调试模式=True,
    任务类型="每日任务",
    优先级=10,
    地图关键字="服争", 
    工作时间开始=12,
    工作时间段列表="12:00-12:30,19:30-20:00",
    提前进场秒数=0,
    启用购买次数=True,
    状态_上次匹配核查时间=0,

)
class 跨服争霸任务(战斗任务执行器):
    """跨服争霸任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
   
    def 执行入口逻辑(self) -> bool:
        """执行跨服争霸入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        if self.任务状态.上次匹配核查时间>=time.time()-20:
            return True
        else:
            self.任务状态.上次匹配核查时间=time.time() 
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False
        
        # 2. 进入跨服争霸页面
        if not self._进入跨服争霸页面():
            return False
        
        # 3. 同步服务器时间
        time.sleep(max(0.5, self.游戏配置.刷新等待秒))
        self.线程.刷新截图()
        
        # 4. 读取次数
        if not self._读取跨服争霸次数():
            return False
        
        # 5. 次数为0时尝试购买
        if self.任务状态.剩余次数 == 0:
            if not self.任务配置.启用购买次数:
                return False
            if not self._尝试购买跨服争霸次数():
                return False
        
        # 6. 再次确认次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"二次确认次数已用完(剩余{self.任务状态.剩余次数})")
            return False
        
        # 7. 点击快速匹配
        if not self._点击快速匹配():
            return False
        
        self._等待中借调普通任务()
        
        调试器.state(self.调试分类, "入口逻辑完成，进入匹配队列")
        return True


    def _进入跨服争霸页面(self) -> bool:
        """进入跨服争霸页面"""
        if self.辅助识别器.区域包含文字(self.游戏配置.区域.主界面.中间页面名称区域标签.元组,"跨服|争霸"):
            return True
                       
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug(self.调试分类, "展开右上角任务帘失败")
            return False
        
        if not self.页面.主界面操作.点击跨服争霸上标():
            调试器.debug(self.调试分类, "点击跨服争霸上标失败")
            return False
        
        if not self.页面.主界面操作.点击跨服争霸下标():
            调试器.debug(self.调试分类, "点击跨服争霸下标失败")
            return False
        
        return True


    def _读取跨服争霸次数(self) -> bool:
        """读取跨服争霸剩余次数"""
        结果 = self.更新区域任务次数(
            self.游戏配置.区域.跨服争霸.跨服争霸页面剩余次数标签.元组,
            None,
            "/"
        )
        if not 结果:
            调试器.warning(self.调试分类, "读取跨服争霸次数失败，入口逻辑中断")
            return False
        
        调试器.trace(self.调试分类, f"剩余次数: {self.任务状态.剩余次数}")
        return True


    def _尝试购买跨服争霸次数(self) -> bool:
        """尝试购买跨服争霸次数"""
        调试器.debug(self.调试分类, "次数为0，尝试购买")
        
        # 打开购买页面
        if not self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.跨服争霸.跨服争霸进入购买按钮标签.元组,
            self.游戏配置.区域.跨服争霸.跨服争霸剩余购买次数标签.元组,
            "次"
        ).执行():
            调试器.debug(self.调试分类, "打开购买页面失败")
            return False
        
        # 读取可购买次数
        结果 = self.辅助识别器.获取区域文字(
            self.游戏配置.区域.跨服争霸.跨服争霸剩余购买次数标签.元组
        )
        购买次数 = 提取次数(结果)
        
        if 购买次数 < 0:
            调试器.debug(self.调试分类, "读取购买次数失败")
            return False
        
        if 购买次数 == 0:
            调试器.debug(self.调试分类, "无可购买次数，但次数为0仍继续")
            return True
        
        # 点击购买
        if not self._执行购买操作():
            return False
        
        # 购买后重新读取次数
        time.sleep(self.游戏配置.默认等待秒)
        self.线程.刷新截图()
        
        if not self._读取跨服争霸次数():
            return False
        
        return True


    def _执行购买操作(self) -> bool:
        """执行购买的两步确认"""
        # 第一步：点击购买按钮
        if not self.页面.创建_通用点击文字验证文字切换(
            self.游戏配置.区域.跨服争霸.跨服争霸购买按钮标签.元组,
            "买",
            self.游戏配置.区域.跨服争霸.跨服争霸购买二次确认按钮标签.元组,
            "买",
        ).执行():
            调试器.debug(self.调试分类, "第一步购买确认失败")
            return False
        
        # 第二步：点击二次确认（验证确认窗口消失）
        if not self.页面.创建_通用点击文字验证文字切换(
            self.游戏配置.区域.跨服争霸.跨服争霸购买二次确认按钮标签.元组,
            "买",
            self.游戏配置.区域.跨服争霸.跨服争霸购买二次确认按钮标签.元组,
            "买",
            False
        ).执行():
            调试器.debug(self.调试分类, "第二步购买确认失败")
            return False
        
        调试器.debug(self.调试分类, "购买操作完成")
        return True


    def _点击快速匹配(self) -> bool:
        """点击快速匹配按钮（验证按钮消失=已进入匹配队列）"""
        if not self.页面.创建_通用点击文字验证文字切换(
            self.游戏配置.区域.跨服争霸.跨服争霸快速匹配按钮标签.元组,
            "快速",
            self.游戏配置.区域.跨服争霸.跨服争霸快速匹配按钮标签.元组,
            "取消",
            True,
            True
        ).执行():
            调试器.debug(self.调试分类, "点击快速匹配失败")
            return False
        
        return True
    
    
    def 检查并处理复活(self, 安全复活: bool = True, 记录杀手: bool = False) -> bool:
        if self.是否在副本中():
            return False
        return super().检查并处理复活(安全复活, 记录杀手)
    

    #这个副本不检查攻击模式
    def 检查攻击模式(self) -> None:
        
        return 
       
    def _领取奖励检查钩子(self) -> str | None:
        self.任务状态.上次匹配核查时间=time.time() - 20
        return super()._领取奖励检查钩子()