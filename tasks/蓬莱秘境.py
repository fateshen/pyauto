# tasks/penglaimijing.py
"""
蓬莱秘境任务定义
"""

from typing import Optional

from core.utils import 匹配分组关键字, 是否为今天,是否有重叠,坐标在目标半径内
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from core.debug import 调试器
import time



@任务定义(
    任务ID="penglaimijing",
    任务名称="蓬莱秘境",
    任务类型="每日任务",
    调试模式=True,
    优先级=6,
    启用位置复查=True,
    地图关键字="蓬莱秘境|蓬莱,境|蓬莱秘",   
    默认攻击模式="和平模式", 
    提前进场秒数=0,
    节日BOSS开启时间=0,  
    状态_移动开始时间=0,
)
class 蓬莱秘境任务(战斗任务执行器):
    """蓬莱秘境任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)   
        self.BOSS坐标 = {
            "1": (8,49),
            "2": (76, 46),
            "3": (42, 24),
            "4": (44, 74),
            "5": (44, 45)
        }  
        self.刷新时间={
             "1": -1.0,
            "2": -1.0,
            "3": -1.0,
            "4": -1.0,
            "5": -1.0
        }
        self.各BOSS剩余次数={
             "1": 4,
            "2": 4,
            "3": 4,
            "4": 4,
            "5": 4
        }
        self.当前子任务队列  = []
       
    def 执行入口逻辑(self) -> bool:
        """执行蓬莱秘境入口逻辑"""
        调试器.info("蓬莱秘境", "开始执行入口逻辑")
        if not 是否为今天(self.任务配置.节日BOSS开启时间):
            调试器.warning("蓬莱秘境", "今日未开启，跳过执行")
            self.任务状态.剩余次数=0
            return False
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("蓬莱秘境", "今日次数已用完，跳过执行")
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
                    文字区域=文字集合.find("蓬莱秘境|蓬莱,境|蓬莱秘")
                    if 文字区域 is None: continue
                    self.通用操作.点击区域(文字区域,2)
                    time.sleep(self.游戏配置.默认等待秒)
                    self.页面.线程.刷新截图()
                    if not self._校核是否刷新():
                         调试器.state("蓬莱秘境", "刷新检查，未刷新")
                            
                    if not  self.页面.创建_通用点击区域验证文字切换(
                        self.游戏配置.区域.各种活动.蓬莱秘境进入按钮区域.元组,
                        self.游戏配置.区域.主界面.小地图地图名显示标签.元组,
                        self.任务配置.地图关键字
                    ) .执行():
                        调试器.state("蓬莱秘境", "入口逻辑执行失败")
                        return False
                    调试器.state("蓬莱秘境", "入口逻辑执行成功，已进入蓬莱秘境副本")            
                    return True
        return False
    
    def _校核是否刷新(self)->bool:
        次数为0项目统计=0
        剩余时间临时数据=600

        for i in range(5):
            index=i+1
            
            属性名 = f"蓬莱秘境次数区域{index}"
            print(属性名)
            区域对象 = getattr(self.游戏配置.区域.各种活动, 属性名, None)            
           
            if 区域对象 is None:               
                continue
            识别区域 = 区域对象.元组
            结果 = self.辅助识别器.获取区域次数(识别区域,放大倍数=3)
            if 结果 is None:continue
            if 结果==0:次数为0项目统计+=1
            if 结果>0:
               时间区域对象=getattr(self.游戏配置.区域.各种活动, f"蓬莱秘境刷新时间{index}", None)
               if 时间区域对象 is None :continue
               时间=self.辅助识别器.获取刷新秒数(时间区域对象.元组,放大=3)
               if 时间 is None:continue
               if 时间==0:
                   self.任务状态.下次刷新时间=0
                   return True
               剩余时间临时数据=min(时间,剩余时间临时数据)
        self.任务状态.下次刷新时间=剩余时间临时数据
        if 次数为0项目统计==5:
           self.任务状态.剩余次数=0
        return False
    def _副本内更新刷新情况(self)->Optional[bool]:
        if not self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.各种活动.蓬莱秘境副本内首领信息按钮区域.元组,
            self.游戏配置.区域.各种活动.蓬莱秘境副本内首领面板归属次数文字验证区域.元组,
            "归|属|次|数"
        ).执行():
            return None
            
        次数为0项目统计=0
        下次刷新时间=600+time.time()
        需要处理的任务列表=[]
        for i in range(5):
            index=i+1
            id=str(index)
            属性名 = f"蓬莱秘境副本内次数{index}"
            print(属性名)
            区域对象 = getattr(self.游戏配置.区域.各种活动, 属性名, None)            
           
            if 区域对象 is None:               
                continue
            识别区域 = 区域对象.元组
            结果 = self.辅助识别器.获取区域次数(识别区域,放大倍数=10)
            if 结果 is None:continue
            self.各BOSS剩余次数[id]=结果
            if 结果==0:次数为0项目统计+=1
            if 结果>0:
               时间区域对象=getattr(self.游戏配置.区域.各种活动, f"蓬莱秘境副本内剩余时间{index}", None)
               if 时间区域对象 is None :continue
               时间=self.辅助识别器.获取刷新秒数(时间区域对象.元组,放大=2)
               if 时间 is None:continue
               if 时间<=5:
                   需要处理的任务列表.append(index)
               self.刷新时间[id]=time.time()+时间
               下次刷新时间=min(time.time()+时间,下次刷新时间)
        self.任务状态.下次刷新时间=下次刷新时间
        self.当前子任务队列=需要处理的任务列表        
        if 次数为0项目统计==5:
            self.任务状态.剩余次数=0
            return False
        return True
               
    def _当前所处的BOSS位置(self)->Optional[int]:
        玩家坐标=self.辅助识别器.获取当前玩家坐标()
        if 玩家坐标 is None:return None
        for i in range(5):
            index=i+1
            id=str(index)
            boss坐标=self.BOSS坐标[id]
            if 坐标在目标半径内(玩家坐标,boss坐标,7):
                return index
        return None
    
    def _检查位置复查(self) -> Optional[str]:
        """
        检查并调整角色位置到当前子任务boss坐标

        返回:
            None: 已在范围内，不需要复查
            "移动中": 正在移动或已触发移动
            "无新任务，退出副本": 没有可处理的子任务
        """
        # 1. 检查位置复查开关
        if not self.任务配置.启用位置复查:
            return None
        
        if self.当前子任务队列==[]:
             刷新结果=self._副本内更新刷新情况()
             if 刷新结果 is None :return None
             self.通用操作.关闭中间可能存在的窗口()
             if self.当前子任务队列==[] :                 
                 self.退出副本()
                 return "无新任务，退出副本"
            

        静止时长 = self.公共变量.获取静止时长()
        移动已耗时 = (
            time.time() - self.任务状态.移动开始时间
            if self.任务状态.移动开始时间 > 0
            else 0
        )
        当前玩家所在BOSS范围ID = self._当前所处的BOSS位置()
        调试器.debug(self.调试分类, f"当前处于BOSS位置: {当前玩家所在BOSS范围ID}") 
        # 2. 检查是否正在移动,是否移动到位置
        if self.任务状态.移动开始时间 > 0 and 移动已耗时 < 15 and 静止时长<=3:
            #在移动时间范围，且角色静止时间小于3秒，则认为正在移动
            if 当前玩家所在BOSS范围ID is not None and 当前玩家所在BOSS范围ID in self.当前子任务队列:                
                # 移动结束，位置复查次数重置为0
                self.任务状态.移动开始时间 = 0.0
                self.任务状态.位置复查次数 = 0  
                return None
            return "移动中"
        
     
        # # 3. 非移动如果不能正确获取当前位置，则返回None
        if 当前玩家所在BOSS范围ID in self.当前子任务队列 and self.辅助识别器.是否有目标():
            return None
      
     
        self._识别移动检查()

        # 画面还在变化 → 正在移动中
        调试器.trace(
            self.调试分类,
            f"位置复查: 移动中(静止{静止时长:.1f}秒，已耗时{移动已耗时:.0f}秒)",
        )

        return "移动中"

    def _识别移动检查(self) -> None:
        """打开大地图，识别刷新时间，点击目标BOSS位置移动"""

        # 1. 更新首领信息
        刷新结果=self._副本内更新刷新情况()
        if 刷新结果 is None :return None
        if self.当前子任务队列==[] :
            self.通用操作.关闭中间可能存在的窗口()
            self.退出副本()
            return


        需要处理的任务 = self.当前子任务队列
        调试器.debug(self.调试分类, f"副本内识别刷新时间:需要处理的任务: {需要处理的任务}")        

        子任务ID=需要处理的任务[0]

        移动目标区域 = getattr(
            self.游戏配置.区域.各种活动,
            f"蓬莱秘境副本内次数{子任务ID}",
            None,
        )

        if 移动目标区域 is None:
            调试器.warning(self.调试分类, f"位置复查: 未找到子任务{子任务ID}的移动目标区域")
            self.通用操作.关闭中间可能存在的窗口()
            return

        # 3. 点击目标坐标
        self.通用操作.点击区域(移动目标区域.元组, 2, 0.08)

        # 4. 记录移动开始时间
        self.任务状态.移动开始时间 = time.time()

        # 5. 关闭地图
        if not self.通用操作.关闭中间可能存在的窗口():
            调试器.debug(self.调试分类, "未关闭中间地图")

    def 检查退出条件(self) -> bool:
        """检查是否满足退出条件"""
        无目标超时 = self.公共变量.获取无目标时间() > self.无目标超时秒数
        静止超时 = self.公共变量.获取静止时长() > 120
        
        调试器.debug(self.调试分类, f"退出条件检查: 无目标超时({self.无目标超时秒数}s)={无目标超时}, 静止超时({self.静止超时秒数}s)={静止超时}")
        
        return 无目标超时 and 静止超时 
       

       

                
