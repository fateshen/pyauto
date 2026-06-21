# tasks/fuliBOSS.py
"""
福利BOSS任务定义
"""

from core.utils import 匹配分组关键字, 是否为今天,是否有重叠
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from core.debug import 调试器
import time



@任务定义(
    任务ID="fuliBOSS",
    任务名称="福利BOSS",
    任务类型="每日任务",
    优先级=6,
    地图关键字="福利BOSS",    
    提前进场秒数=0,
    节日BOSS开启时间=0,
)
class 福利BOSS任务(战斗任务执行器):
    """福利BOSS任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)       
       
    def 执行入口逻辑(self) -> bool:
        """执行福利BOSS入口逻辑"""
        调试器.info("福利BOSS", "开始执行入口逻辑")
        if not 是否为今天(self.任务配置.节日BOSS开启时间):
            调试器.warning("福利BOSS", "今日未开启，跳过执行")
            self.任务状态.剩余次数=0
            return False
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("福利BOSS", "今日次数已用完，跳过执行")
            return False
        
        # 2. 进入跨服战场页面
        if not self.页面.创建_通用点击图片验证文字切换(
            self.游戏配置.区域.主界面.第一排任务区域标签.元组,
            "活动图标.bmp",
             self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
             "开服|活动",
        ).执行():
            调试器.error(self.调试分类, "进入活动页面失败，入口逻辑中断")
            return False
      
        图片坐标=self.辅助识别器.查找图片多结果(self.游戏配置.区域.各种活动.开服活动右侧小标签红点检查区域.元组,"红点1.bmp")
        if not 图片坐标:
            return False
        表头文字=""
        for 坐标 in 图片坐标: 
            校正坐标=坐标[0]-15,坐标[1]+15,坐标[0]+3,坐标[1]+45
            self.通用操作.点击区域(校正坐标,2)
            time.sleep(self.游戏配置.默认等待秒*2)
            self.页面.线程.刷新截图()
            表头文字=self.辅助识别器.获取区域文字(self.游戏配置.区域.主界面.中间页面名称区域标签.元组)
            if 匹配分组关键字(表头文字,"祈|愿|秘宝"):
                break
        if not 匹配分组关键字(表头文字,"祈|愿|秘宝"):
                return False

        左侧菜单=self.辅助识别器.获取区域文字坐标(self.游戏配置.区域.合成.合成左分类卡区域标签.元组)
        if 左侧菜单 is None:
            return False
        福利BOSS按钮区域=左侧菜单.find("福利BOSS|利BOS")  
        if 福利BOSS按钮区域 is  None:
            return False
        
        if not  self.页面.创建_通用点击区域验证文字切换(
            福利BOSS按钮区域,
            self.游戏配置.区域.各种活动.福利BOSS前往按钮区域.元组,
            "前往"

        ) .执行():
            return False
        if not self.辅助识别器.查找图片单结果(self.游戏配置.区域.各种活动.福利BOSS前往按钮区域.元组,"红点1.bmp"):
            self.任务状态.剩余次数=0
            调试器.warning("福利BOSS", "福利BOSS次数为0")
            # 注意：原代码这里直接return False，保持原逻辑
            return False
                            
        if not  self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.各种活动.福利BOSS前往按钮区域.元组,
            self.游戏配置.区域.主界面.小地图地图名显示标签.元组,
            "福利"

        ) .执行():
            调试器.state("福利BOSS", "入口逻辑执行失败")
            return False
        调试器.state("福利BOSS", "入口逻辑执行成功，已进入福利BOSS副本")
            
        return True