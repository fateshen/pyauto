# tasks/shoushen.py
"""
兽神任务定义
"""

from core.utils import 匹配分组关键字
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from core.debug import 调试器
import time



@任务定义(
    任务ID="shoushen",
    任务名称="兽神仅扫荡",
    任务类型="每日任务",
    优先级=5,
    地图关键字="兽神战场",    
    提前进场秒数=0,
)
class 兽神扫荡任务(战斗任务执行器):
    """兽神任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)       
       
    def 执行入口逻辑(self) -> bool:
        """执行兽神入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, "今日次数已用完，跳过执行")
            return False
        
        # 2. 进入首领战场页面
        if not self.页面.主界面操作.进入首领页面():
            调试器.error(self.调试分类, "进入首领页面失败，入口逻辑中断")
            return False
      
        # 3. 进入兽神页面
        if not self.页面.首领任务.兽神.点击右侧兽神页面():
            调试器.error(self.调试分类, f"点击右侧专属兽神失败，区域: {self.动态标签.首领页面右侧标签.兽神.元组}")
            return False
        
        
        # 4. 更新剩余次数      

        剩余次数=self.辅助识别器.获取区域次数(self.游戏配置.区域.兽神.兽神页面剩余次数标签.元组)
        矿颜色筛查=self.辅助识别器.区域像素统计(self.游戏配置.区域.兽神.兽神页面矿物颜色检查标签.元组,"0A0AD9,0.9|01F801,0.9")
        if 剩余次数==0 and 矿颜色筛查[0]>0 and 矿颜色筛查[1]==0:
            self.任务状态.剩余次数=0 
            调试器.state(self.调试分类, f"读取次数后确认已用完(剩余{self.任务状态.剩余次数})")
            return False
        
        扫荡挑战按钮文字=self.辅助识别器.获取区域文字(self.游戏配置.区域.兽神.兽神页面扫荡按钮标签.元组)
        
        if 匹配分组关键字(扫荡挑战按钮文字, "进|入") :
            self.任务状态.剩余次数=0 
            调试器.state(self.调试分类, f"兽神未开启扫荡功能，无法继续执行")
            return False
        checked=0
        if 匹配分组关键字(扫荡挑战按钮文字, "扫|荡") :
             # 6. 进入兽神页面
            if not self.页面.创建_通用点击区域验证文字切换(
                self.游戏配置.区域.兽神.兽神页面扫荡按钮标签.元组,
                self.游戏配置.区域.兽神.兽神扫荡页面扫荡按钮标签1.元组,
                "扫|荡"
            ).执行():
                调试器.error(self.调试分类, "进入兽神扫荡页面失败，入口逻辑中断")
                return False 
            for i in range(3):
                bindex=i+1
                子按钮 = getattr(self.游戏配置.区域.兽神,  f"兽神扫荡页面扫荡按钮标签{bindex}", None)
                数字判断 = getattr(self.游戏配置.区域.兽神,  f"兽神扫荡页面扫荡次数标签{bindex}", None)
                if 子按钮 is None or 数字判断 is None:
                    continue
                子按钮标签 = 子按钮.元组
                数字判断标签 = 数字判断.元组
                for _ in range(10):
                    奖励文字=self.辅助识别器.获取区域文字坐标(self.游戏配置.区域.主界面.任务结束确定领取奖励区域标签.元组)
                    if 奖励文字 is not None:
                        领取区域=奖励文字.find("领|取|继|续|扫|荡")
                        if 领取区域:
                            self.通用操作.点击区域(领取区域)
                            time.sleep(self.游戏配置.默认等待秒)
                            self.线程.刷新截图()
                            continue
                    子任务颜色筛查=self.辅助识别器.区域像素统计(数字判断标签,"0A0AD9,0.9|03D603,0.9")
                    if 子任务颜色筛查[0]>0 and 子任务颜色筛查[1]==0:
                        checked+=1
                        break
                    if 子任务颜色筛查[0]==0 and 子任务颜色筛查[1]>0:
                        self.通用操作.点击区域(子按钮标签)
                        time.sleep(self.游戏配置.默认等待秒)
                        self.线程.刷新截图()
        if checked==3 :
            time.sleep(self.游戏配置.默认等待秒)
            self.线程.刷新截图()
            剩余次数=self.辅助识别器.获取区域次数(self.游戏配置.区域.兽神.兽神页面剩余次数标签.元组)
            矿颜色筛查=self.辅助识别器.区域像素统计(self.游戏配置.区域.兽神.兽神页面矿物颜色检查标签.元组,"0A0AD9,0.9|01F801,0.9")
            if 剩余次数==0 and 矿颜色筛查[0]>0 and 矿颜色筛查[1]==0:
                self.任务状态.剩余次数=0 
                调试器.state(self.调试分类, f"读取次数后确认已用完(剩余{self.任务状态.剩余次数})")
                return False
       
        return False