# tasks/juezhanmengzhong.py
"""
决战盟重任务定义
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
    任务ID="juezhanmengzhong",
    任务名称="决战盟重",
    调试模式=True,
    任务类型="每日任务",
    优先级=10,
    地图关键字="决战盟", 
    工作时间开始=20,
    避让冷却秒数=10,
    工作时间段列表="20:45-21:15",
    执行日期规则="日期8-26 & 日期双数日",
    提前进场秒数=0,
    开始几分钟以后未排队使用强制匹配=10,
    开始几分钟以后队长使用匹配=1,
    状态_使用强制匹配=False,
    状态_上次匹配核查时间=0,
    状态_已准备完成=False,
)
class 决战盟重任务(战斗任务执行器):
    """决战盟重任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
   
    def 执行入口逻辑(self) -> bool:
        """执行决战盟重入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        
        if self.任务状态.上次匹配核查时间>=time.time()-20:
            return True
        else:
            self.任务状态.上次匹配核查时间=time.time() 

        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False
        
        # 2. 进入决战盟重页面
        if not self._进入决战盟重页面():
            return False
        
        if not self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.决战盟重.决战盟重页面前往匹配按钮标签.元组,
            self.游戏配置.区域.决战盟重.决战盟重页面挑战次数区域标签.元组,
            "挑|战",            
        ).执行():
            return False
        
        # 3. 同步服务器时间
        time.sleep(max(0.5, self.游戏配置.刷新等待秒))
        self.线程.刷新截图()
        
        # 4. 读取次数
        if not self._读取决战盟重次数():
            return False        
     
        # 5. 再次确认次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"确认次数已用完(剩余{self.任务状态.剩余次数})")
            return False
        

        # 7. 点击快速匹配
        if not self._检查并排队():
            return False
        
        self._等待中借调普通任务()
        
        调试器.state(self.调试分类, "入口逻辑完成，进入匹配队列")
        return True


    def _进入决战盟重页面(self) -> bool:
        """进入决战盟重页面"""
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug(self.调试分类, "展开右上角任务帘失败")
            return False
        
        if not self.页面.大千世界.进入大千世界页面():
            调试器.debug(self.调试分类, "点击决战盟重上标失败")
            return False
        
        if not self.页面.大千世界.决战盟重.进入决战盟重页面():
            调试器.debug(self.调试分类, "进入决战盟重失败")
            return False
        
        return True


    def _读取决战盟重次数(self) -> bool:
        """读取决战盟重剩余次数"""
        像素统计=self.辅助识别器.区域像素统计(self.游戏配置.区域.决战盟重.决战盟重页面挑战次数区域标签.元组,"0606EF,0.9") 
        if 像素统计 and 像素统计[0]>5: 
            self.任务状态.剩余次数=0
            return True
        结果 = self.更新区域任务次数(
            self.游戏配置.区域.决战盟重.决战盟重页面挑战次数区域标签.元组,
            None,
            "/"
        )        
        if not 结果:
            调试器.warning(self.调试分类, "读取决战盟重次数失败，入口逻辑中断")
            return False
        调试器.trace(self.调试分类, f"剩余次数: {self.任务状态.剩余次数}")
        return True

    def _检查并排队(self):
        """检查并排队"""
        左按钮文字=self.辅助识别器.获取区域文字(self.游戏配置.区域.决战盟重.决战盟重页面准备按键左边按钮标签.元组)
        准备匹配按钮文字=self.辅助识别器.获取区域文字(self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组)
        右按钮文字=self.辅助识别器.获取区域文字(self.游戏配置.区域.决战盟重.决战盟重页面准备按键右边按钮标签.元组)
        玩家是队长=False
        if 左按钮文字 and 匹配分组关键字(左按钮文字, "队长"):
            玩家是队长=True
        if 右按钮文字 and 匹配分组关键字(右按钮文字, "队长"):
            玩家是队长=True
        
        if 准备匹配按钮文字 == "已准备":            
            return True
        elif 准备匹配按钮文字=="准备":
            if self.页面.创建_通用点击区域验证文字切换(
                self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组,
                self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组,
                "已准备",
            ).执行():
                return True
            return False
        elif 准备匹配按钮文字=="匹配中":
            return True

        分钟数=datetime.datetime.now().minute
        if 分钟数<15 :分钟数=分钟数+60
        if self.任务配置.开始几分钟以后未排队使用强制匹配<=分钟数-45:
            if 玩家是队长:
                self.任务状态.使用强制匹配=True
            else:
                if self.任务状态.剩余次数==5:
                   self.任务状态.使用强制匹配=False
        else:
            self.任务状态.使用强制匹配=False
        
        开始匹配任务=False
        if 玩家是队长:
            if self.任务配置.开始几分钟以后队长使用匹配<=分钟数-45:
                开始匹配任务=True
        
        if 开始匹配任务==False and self.任务状态.使用强制匹配==False:
            return True
       
        准备数量=0
        for i in range(3):            
            属性名 = f"决战盟重页面玩家准备情况标签{i + 1}"
            区域对象 = getattr(self.游戏配置.区域.决战盟重, 属性名, None)
            if 区域对象 is None:
                continue
            if  self.辅助识别器.区域包含文字(区域对象.元组,"准|备"):
                准备数量=准备数量+1

        if 玩家是队长 and 开始匹配任务:
            
            if 准备数量>=3:
                if self.页面.创建_通用点击区域验证文字切换(
                    self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组,
                    self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组,
                    "匹配中",
                ).执行():
                    return True
                return False
        if  self.任务状态.使用强制匹配:
            if 玩家是队长:
                if 准备数量>=3:
                    if self.页面.创建_通用点击区域验证文字切换(
                        self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组,
                        self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组,
                        "匹配中",
                    ).执行():
                        return True
                    return False
                else:       
                    self.通用操作.点击区域(self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组)           
                    if self.页面.创建_通用点击区域验证文字切换(
                        self.游戏配置.区域.决战盟重.决战盟重页面AI确定按钮标签.元组,
                        self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组,
                        "匹配中",
                    ).执行():
                        return True
                    return False
            else:
                if 匹配分组关键字(左按钮文字, "强制|匹配"):
                    点击区域=self.游戏配置.区域.决战盟重.决战盟重页面准备按键左边按钮标签.元组
                if 匹配分组关键字(右按钮文字, "强制|匹配"):
                    点击区域=self.游戏配置.区域.决战盟重.决战盟重页面准备按键右边按钮标签.元组
                if not 点击区域:
                    return False
                if 准备数量>=3:
                    if self.页面.创建_通用点击区域验证文字切换(
                        点击区域,
                        self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组,
                        "匹配中",
                    ).执行():
                        return True
                    return False
                else:
                    self.通用操作.点击区域(点击区域)
                    if self.页面.创建_通用点击区域验证文字切换(
                        self.游戏配置.区域.决战盟重.决战盟重页面AI确定按钮标签.元组,
                        self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组,
                        "匹配中",
                    ).执行():
                        return True
                    return False
        return False

    def 检查攻击模式(self) -> None:
            return 


# # tasks/juezhanmengzhong.py
# """
# 决战盟重任务定义
# """
# import datetime

# from tasks.base import 任务定义
# from core.task_executors.battle_executor import 战斗任务执行器
# from core.page_operations import 页面操作集
# from typing import Optional, Tuple, List
# from core.utils import 匹配分组关键字, 解析时间文字, 缩放区域, 提取次数
# from core.debug import 调试器
# import time
# from core.recognition import OCRResult, ocr
# import re

# @任务定义(
#     任务ID="juezhanmengzhong",
#     任务名称="决战盟重",
#     调试模式=True,
#     任务类型="每日任务",
#     优先级=10,
#     地图关键字="决战盟",
#     工作时间开始=20,
#     工作时间段列表="20:45-21:15",
#     执行日期规则="日期8-26 & 日期双数日",
#     提前进场秒数=0,
#     开始几分钟以后未排队使用强制匹配=10,
#     开始几分钟以后队长使用匹配=1,
#     状态_使用强制匹配=False,
# )
# class 决战盟重任务(战斗任务执行器):
#     """决战盟重任务执行器"""
    
#     def __init__(self, 线程, 任务配置, 任务状态):
#         super().__init__(线程, 任务配置, 任务状态)
#         self.页面 = 页面操作集(线程)
    
#     # ==================== 主入口 ====================
    
#     def 执行入口逻辑(self) -> bool:
#         """执行决战盟重入口逻辑"""
#         调试器.info(self.调试分类, "开始执行入口逻辑")
        # if self.任务状态.上次匹配核查时间>=time.time()-20:
        #     return True
        # else:
        #     self.任务状态.上次匹配核查时间=time.time() 
#         # 1. 检查剩余次数
#         if self.任务状态.剩余次数 <= 0:
#             调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
#             return False
        
#         # 2. 进入决战盟重页面
#         if not self._进入决战盟重页面():
#             return False
        
#         # 3. 点击前往匹配
#         if not self.页面.创建_通用点击区域验证文字切换(
#             self.游戏配置.区域.决战盟重.决战盟重页面前往匹配按钮标签.元组,
#             self.游戏配置.区域.决战盟重.决战盟重页面挑战次数区域标签.元组,
#             "挑|战",
#         ).执行():
#             return False
        
#         # 4. 同步服务器时间
#         time.sleep(max(0.5, self.游戏配置.刷新等待秒))
#         self.线程.刷新截图()
        
#         # 5. 读取次数
#         if not self._读取决战盟重次数():
#             return False
        
#         if self.任务状态.剩余次数 <= 0:
#             调试器.state(self.调试分类, f"确认次数已用完(剩余{self.任务状态.剩余次数})")
#             return False
        
#         # 6. 检查并排队
#         if not self._检查并排队():
#             return False
        
#         self._等待中借调普通任务()
        
#         调试器.state(self.调试分类, "入口逻辑完成，进入匹配队列")
#         return True
    
#     # ==================== 页面进入 ====================
    
#     def _进入决战盟重页面(self) -> bool:
#         """进入决战盟重页面"""
#         if not self.页面.主界面操作.展开右上角任务帘:
#             调试器.debug(self.调试分类, "展开右上角任务帘失败")
#             return False
        
#         if not self.页面.大千世界.进入大千世界页面():
#             调试器.debug(self.调试分类, "进入大千世界页面失败")
#             return False
        
#         if not self.页面.大千世界.决战盟重.进入决战盟重页面():
#             调试器.debug(self.调试分类, "进入决战盟重页面失败")
#             return False
        
#         return True
    
#     # ==================== 次数读取 ====================
    
#     def _读取决战盟重次数(self) -> bool:
#         """读取决战盟重剩余次数"""
#         区域 = self.游戏配置.区域.决战盟重.决战盟重页面挑战次数区域标签.元组
        
#         # 先检查是否次数已用完（红色像素=已消耗标记）
#         像素统计 = self.辅助识别器.区域像素统计(区域, "0606EF,0.9")
#         if 像素统计 and 像素统计[0] > 5:
#             self.任务状态.剩余次数 = 0
#             调试器.debug(self.调试分类, "检测到次数已消耗标记")
#             return True
        
#         # OCR读取剩余次数
#         结果 = self.更新区域任务次数(区域, None, "/")
#         if not 结果:
#             调试器.warning(self.调试分类, "读取决战盟重次数失败，入口逻辑中断")
#             return False
        
#         调试器.trace(self.调试分类, f"剩余次数: {self.任务状态.剩余次数}")
#         return True
    
#     # ==================== 排队匹配 ====================
    
#     def _检查并排队(self) -> bool:
#         """检查队伍状态并排队匹配"""
#         区域 = self.游戏配置.区域.决战盟重
        
#         # 读取按钮文字
#         左按钮文字 = self.辅助识别器.获取区域文字(区域.决战盟重页面准备按键左边按钮标签.元组) or ""
#         准备匹配按钮文字 = self.辅助识别器.获取区域文字(区域.决战盟重页面准备匹配按钮标签.元组) or ""
#         右按钮文字 = self.辅助识别器.获取区域文字(区域.决战盟重页面准备按键右边按钮标签.元组) or ""
        
#         调试器.trace(self.调试分类, f"按钮文字: 左='{左按钮文字}', 匹配='{准备匹配按钮文字}', 右='{右按钮文字}'")
        
#         玩家是队长 = self._判断是否队长(左按钮文字, 右按钮文字)
        
#         # 已经在排队中
#         if 准备匹配按钮文字 in ("已准备", "匹配中"):
#             调试器.debug(self.调试分类, f"已在排队状态: '{准备匹配按钮文字}'")
#             return True
        
#         # 需要点击准备
#         if 准备匹配按钮文字 == "准备":
#             return self._点击准备匹配按钮()
        
#         # 计算已过分钟数
#         分钟数 = self._计算已过分钟数()
#         调试器.trace(self.调试分类, f"当前已过{分钟数}分钟")
        
#         # 判断是否使用强制匹配
#         self.任务状态.使用强制匹配 = self._判断强制匹配(分钟数, 玩家是队长)
        
#         # 判断是否开始匹配
#         开始匹配任务 = 玩家是队长 and 分钟数 >= self.任务配置.开始几分钟以后队长使用匹配
        
#         if not 开始匹配任务 and not self.任务状态.使用强制匹配:
#             调试器.trace(self.调试分类, "未满足匹配条件，等待中")
#             return True
        
#         # 统计准备人数
#         准备数量 = self._统计准备人数()
        
#         # 执行匹配
#         return self._执行匹配操作(玩家是队长, 开始匹配任务, 准备数量, 左按钮文字, 右按钮文字)
    
#     def _判断是否队长(self, 左按钮文字: str, 右按钮文字: str) -> bool:
#         """判断当前玩家是否队长"""
#         return (左按钮文字 and 匹配分组关键字(左按钮文字, "队长")) or \
#                (右按钮文字 and 匹配分组关键字(右按钮文字, "队长"))
    
#     def _计算已过分钟数(self) -> int:
#         """计算从20:45到现在过了多少分钟"""
#         当前 = datetime.datetime.now()
#         分钟数 = 当前.minute
#         if 分钟数 < 15:
#             分钟数 += 60
#         return 分钟数 - 45
    
#     def _判断强制匹配(self, 分钟数: int, 玩家是队长: bool) -> bool:
#         """判断是否使用强制匹配"""
#         if 分钟数 < self.任务配置.开始几分钟以后未排队使用强制匹配:
#             return False
        
#         if 玩家是队长:
#             return True
#         else:
#             # 队员：只剩1次时不用强制匹配
#             return self.任务状态.剩余次数 != 5
    
#     def _统计准备人数(self) -> int:
#         """统计已准备的玩家数量"""
#         准备数量 = 0
#         for i in range(3):
#             属性名 = f"决战盟重页面玩家准备情况标签{i + 1}"
#             区域对象 = getattr(self.游戏配置.区域.决战盟重, 属性名, None)
#             if 区域对象 and self.辅助识别器.区域包含文字(区域对象.元组, "准|备"):
#                 准备数量 += 1
        
#         调试器.trace(self.调试分类, f"准备人数: {准备数量}")
#         return 准备数量
    
#     def _执行匹配操作(self, 玩家是队长: bool, 开始匹配任务: bool, 
#                        准备数量: int, 左按钮文字: str, 右按钮文字: str) -> bool:
#         """执行匹配点击操作"""
#         区域 = self.游戏配置.区域.决战盟重
#         匹配按钮区域 = 区域.决战盟重页面准备匹配按钮标签.元组
        
#         # 队长开始匹配
#         if 玩家是队长 and 开始匹配任务:
#             return self._队长匹配(准备数量, 匹配按钮区域)
        
#         # 强制匹配
#         if self.任务状态.使用强制匹配:
#             return self._强制匹配(玩家是队长, 准备数量, 匹配按钮区域, 左按钮文字, 右按钮文字)
        
#         return False
    
#     def _队长匹配(self, 准备数量: int, 匹配按钮区域) -> bool:
#         """队长点击匹配"""
#         if 准备数量 >= 3:
#             return self._点击匹配并验证(匹配按钮区域)
        
#         调试器.debug(self.调试分类, f"准备人数不足(需要3，实际{准备数量})")
#         return True  # 不算失败，继续等待
    
#     def _强制匹配(self, 玩家是队长: bool, 准备数量: int, 
#                    匹配按钮区域, 左按钮文字: str, 右按钮文字: str) -> bool:
#         """执行强制匹配"""
#         if 玩家是队长:
#             return self._队长强制匹配(准备数量, 匹配按钮区域)
#         else:
#             return self._队员强制匹配(准备数量, 左按钮文字, 右按钮文字)
    
#     def _队长强制匹配(self, 准备数量: int, 匹配按钮区域) -> bool:
#         """队长强制匹配"""
#         AI按钮区域 = self.游戏配置.区域.决战盟重.决战盟重页面AI确定按钮标签.元组
        
#         if 准备数量 >= 3:
#             return self._点击匹配并验证(匹配按钮区域)
#         else:
#             # 人数不足，点匹配 → 点AI确认
#             self.通用操作.点击区域(匹配按钮区域)
#             return self._点击并验证(AI按钮区域, 匹配按钮区域, "匹配中")
    
#     def _队员强制匹配(self, 准备数量: int, 左按钮文字: str, 右按钮文字: str) -> bool:
#         """队员强制匹配"""
#         AI按钮区域 = self.游戏配置.区域.决战盟重.决战盟重页面AI确定按钮标签.元组
        
#         # 找到强制匹配按钮
#         点击区域 = None
#         if 匹配分组关键字(左按钮文字, "强制|匹配"):
#             点击区域 = self.游戏配置.区域.决战盟重.决战盟重页面准备按键左边按钮标签.元组
#         elif 匹配分组关键字(右按钮文字, "强制|匹配"):
#             点击区域 = self.游戏配置.区域.决战盟重.决战盟重页面准备按键右边按钮标签.元组
        
#         if not 点击区域:
#             调试器.warning(self.调试分类, "未找到强制匹配按钮")
#             return False
        
#         if 准备数量 >= 3:
#             return self._点击并验证(点击区域, self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组, "匹配中")
#         else:
#             self.通用操作.点击区域(点击区域)
#             return self._点击并验证(AI按钮区域, self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组, "匹配中")
    
#     # ==================== 通用操作 ====================
    
#     def _点击准备匹配按钮(self) -> bool:
#         """点击准备匹配按钮"""
#         区域 = self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组
#         return self._点击并验证(区域, 区域, "已准备")
    
#     def _点击匹配并验证(self, 点击区域) -> bool:
#         """点击匹配按钮并验证进入匹配中"""
#         匹配按钮区域 = self.游戏配置.区域.决战盟重.决战盟重页面准备匹配按钮标签.元组
#         return self._点击并验证(点击区域, 匹配按钮区域, "匹配中")
    
#     def _点击并验证(self, 点击区域, 验证区域, 验证文字: str) -> bool:
#         """通用点击验证"""
#         return self.页面.创建_通用点击区域验证文字切换(
#             点击区域,
#             验证区域,
#             验证文字,
#         ).执行()
       

              


       