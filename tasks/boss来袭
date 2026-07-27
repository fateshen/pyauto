# tasks/bosslaixi.py
"""
BOSS来袭任务定义
"""

from rich.repr import T

from core.utils import 匹配分组关键字, 是否为今天,是否有重叠
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from core.debug import 调试器
import time



@任务定义(
    任务ID="bosslaixi",
    任务名称="BOSS来袭",
    任务类型="每日任务",
    优先级=16,
    地图关键字="节日广场",   
    工作时间段列表="12:30-12:38", 
    提前进场秒数=0,
    节日BOSS开启时间=0,
)
class BOSS来袭任务(战斗任务执行器):
    """BOSS来袭任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)       
       
    def 执行入口逻辑(self) -> bool:
        """执行BOSS来袭入口逻辑"""
        调试器.info("BOSS来袭", "开始执行入口逻辑")
        if not 是否为今天(self.任务配置.节日BOSS开启时间):
            调试器.warning("BOSS来袭", "今日未开启，跳过执行")
            self.任务状态.剩余次数=0
            return False
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("BOSS来袭", "今日次数已用完，跳过执行")
            return False
        
        # 2. 进入蓬莱秘境页面
        红点位置集合=self.辅助识别器.查找图片多结果(self.游戏配置.区域.各种活动.左上角活动检查区域.元组,"红点1.bmp")
        if  红点位置集合:
            for 位置 in 红点位置集合:
                x,y=位置[0],位置[1]
                新区域=x-30,y+10,x-5,y+30
                if self.页面.创建_通用点击区域验证文字切换(
                    新区域,
                    self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
                    "开|服|活动",  
                    重试配置={"最大重试次数": 1, 
                            "重试延迟": 300  
                            }         
                ).执行():
                    文字集合=self.辅助识别器.获取区域文字坐标(self.游戏配置.区域.合成.合成左分类卡区域标签.元组)
                    if 文字集合 is None:  continue
                    文字区域=文字集合.find("BOSS来袭|BOSS来")
                    if 文字区域 is None: continue
                    self.通用操作.点击区域(文字区域,2)
                    time.sleep(self.游戏配置.默认等待秒)
                    self.页面.线程.刷新截图()                   
                    if not  self.页面.创建_通用点击区域验证文字切换(
                        self.游戏配置.区域.各种活动.BOSS来袭前往按钮区域.元组,
                        self.游戏配置.区域.主界面.小地图地图名显示标签.元组,
                        self.任务配置.地图关键字
                    ) .执行():
                        调试器.state("BOSS来袭", "入口逻辑执行失败")
                        return False
                    调试器.state("BOSS来袭", "入口逻辑执行成功，已进入BOSS来袭副本")            
                    return True
        return False
    def 检查退出条件(self) -> bool:
            """检查是否满足退出条件"""
            无目标超时 = self.公共变量.获取无目标时间() > 5
            静止超时 = self.公共变量.获取静止时长() >10
            
            调试器.debug(self.调试分类, f"退出条件检查: 无目标超时({self.无目标超时秒数}s)={无目标超时}, 静止超时({self.静止超时秒数}s)={静止超时}")
            if 无目标超时 and 静止超时:
                self.任务状态.剩余次数 = 0
                return True
            return False