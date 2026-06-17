# tasks/zuoqi.py
"""
坐骑任务定义
"""

from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from typing import Optional, Tuple, List,Dict, Any
from pydantic import  Field
from core.utils import 匹配分组关键字, 解析时间文字, 重试
from core.debug import 调试器
import time
from core.recognition import OCRResult, ocr, 分离粘连文字
import re

def 专用排序(数字列表: List[int]) -> List[int]:
    """
    专用排序函数
    
    规则：
    - 数字 >= 30：从大到小排序
    - 数字 < 30：按十位从大到小，个位从小到大排序
    """
    # 分离两组
    大数字组 = [x for x in 数字列表 if x >= 30]
    小数字组 = [x for x in 数字列表 if x < 30]
    
    # 大数字组：从大到小排序
    大数字组.sort(reverse=True)
    
    # 小数字组：按十位从大到小，个位从小到大
    小数字组.sort(key=lambda x: (-(x // 10), x % 10))
    
    return 大数字组 + 小数字组

@任务定义(
    任务ID="zuoqi",
    任务名称="坐骑",
    任务类型="每日任务",
    调试模式=True,
    优先级=10,
    地图关键字="坐骑战场|坐,战场|坐骑,场",
    避让模式使用全局设置= True,
    启用位置复查=True,
    位置复查移动区域 = "",
    位置复查目标中心 = "38,35",
    回城回血使用全局设置=True,
    怪物有无敌=True,  
    工作时间开始=0,
    提前进场秒数=15,
    子任务队列="11",
    次优先级任务队列="12,13,14",
    每日更新任务数量=3,
    次优先级任务开始时间=22,
    状态_子任务刷新情况=Field(default_factory=dict),
    状态_当前子任务ID="",#这个当前子任务ID主要是为了正确处理避让冷却等，不作为其他逻辑使用
)
class 坐骑任务(战斗任务执行器):
    """坐骑任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)        
        self.校检规则文字={
            "1": "上古|麒|麟",
            "2": "钟山|山兽|镇",
            "3": "明|狼王|幻灵",
            "4": "狂|蝎王|毒,王",
            "5": "青,王|青鸾|凤仪|青鸾",
            "6": "狐|尾",
            "7": "破|魔能|天兽",
            "8": "恶|穷奇"            
        }
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
        调试器.trace("坐骑", f"页面识别结果: '{当前页面}'")
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

    def 检查任务数量溢出(self) -> bool:
        """
        检查是否需要处理任务溢出
        
        条件：
        1. 剩余次数 + 每日新增次数 > 最多保存数量
        2. 当前时间 >= 次优先级任务开始时间        
        返回:
            True: 需要处理溢出，使用主任务+次优先级任务
            False: 不需要处理溢出，只使用主任务
        """
        当前时间小时 = time.localtime().tm_hour     
        return  当前时间小时 >= self.任务配置.次优先级任务开始时间 and self.任务状态.剩余次数 > self.任务配置.每日更新任务数量*2
    def 更新当前任务队列(self) -> bool:
        """
        获取合并后的任务队列（根据溢出情况决定）
        
        返回:
            任务号列表（已排序）
        """
                
        # 解析主任务队列
        主任务列表 = [int(x.strip()) for x in self.任务配置.子任务队列.split(',') if x.strip()]
        
        # 检查是否需要溢出处理
        if not self.检查任务数量溢出():
            # 不需要溢出，只返回主任务
            self.当前子任务队列 = 专用排序(主任务列表)
            调试器.debug("坐骑", f"任务队列(正常模式): {self.当前子任务队列}")
            return True

        
        # 需要溢出，合并主任务和次优先级任务
        次优先级列表 = [int(x.strip()) for x in self.任务配置.次优先级任务队列.split(',') if x.strip()]
        
        # 合并去重
        合并后列表 = list(set(主任务列表 + 次优先级列表))
        
        # 应用专用排序
        self.当前子任务队列  = 专用排序(合并后列表)
        调试器.debug("坐骑", f"任务队列(溢出模式): {self.当前子任务队列}")

        return True   
    def _排序已刷新列表(self, 列表: List[int]) -> List[int]:
        """
        对已刷新列表排序（子类可覆盖）
        默认从大到小排序
        
        坐骑任务需要覆盖此方法使用专用排序
        """
        return 专用排序(列表)
    def 获取层选项标签组织(self) -> Optional[OCRResult] :
        """获取层选项标签组"""
        from core.recognition import 分离粘连文字
        文字识别器= self.线程.文字识别器
        截图 = self.线程.截图
        if 截图 is None:
            截图=self.线程.刷新截图()
        if 截图 is None:
            调试器.warning("坐骑", "获取层选项标签组时截图失败")
            return  None
        ocr_result = 文字识别器.recognize_result(截图, self.游戏配置.区域.坐骑.坐骑页面选层区域标签.元组)
        ocr_result = 分离粘连文字(ocr_result)
        return ocr_result
    
    from core.utils import 重试
    @重试(最大次数=2, 延迟毫秒=300,重试假值=True)
    def 点击层选项(self,目标层标签:Tuple[int,int,int,int],层号:int) -> bool:
        """点击层选项"""        
        if 目标层标签 is not None:
            self.页面.创建点击区域操作(目标层标签).执行()
            time.sleep(self.游戏配置.战斗.等待.默认等待秒)
            if self.校检是否进入层(层号):
                调试器.debug("坐骑", f"点击层选项成功，已进入第{层号}层")
                return True
        调试器.debug("坐骑", f"点击层选项失败，层号={层号}")
        return False
    @重试(最大次数=2, 延迟毫秒=300,重试假值=True)
    def 校检是否进入层(self, 层号: int) -> bool:
        """校验是否进入层"""
        属性名 = f"坐骑页面坐骑选择范围标签{层号}1"
        区域对象 = getattr(self.游戏配置.区域.坐骑, 属性名)
        if 区域对象 is None:
            调试器.warning("坐骑", f"未找到区域配置: 坐骑.{属性名}")
            return False
        
        区域 = 区域对象.元组
        截图 = self.线程.刷新截图()
        if 截图 is None:
            调试器.debug("坐骑", f"校检第{层号}层时截图失败")
            return False
        
        # 不要直接修改区域列表，创建新区域
        校验区域 = (区域[0], 区域[1], 区域[2], 区域[1] + 32)
        
        识别器 = self.线程.文字识别器
        filter_config = {
            "color_diff": "5-98,255,98,255,98,255",  
            "keep_color": True,
            "background": "black"
        }
        
        切换页面文字 = 识别器.recognize_text(截图, 校验区域, filter_config)
        文字规则 = self.校检规则文字[str(层号)]
        结果 = 匹配分组关键字(切换页面文字, 文字规则)
        调试器.trace("坐骑", f"校检第{层号}层: 识别文字='{切换页面文字}', 规则='{文字规则}', 结果={结果}")
        
        return 结果
   
    def 检查刷新时间并进入副本(self, 层标签组: OCRResult) -> bool:
        """检查坐骑刷新时间，判断是否可以进入"""
        
   
        # 先同步子任务状态（确保配置和状态一致）
        self.更新当前任务队列()
        self.更新同步子任务状态()   

        需要处理的任务 = self.获取已刷新任务列表()
        调试器.debug("坐骑", f"需要处理的任务: {需要处理的任务}")
        if not 需要处理的任务:
            调试器.debug("坐骑", "无已刷新任务")
            self.更新下一次刷新时间()
            return False
        # 记录上次点击的层，避免重复点击
        上次目标选项卡层数 = -1
        
        for 队列号 in 需要处理的任务:
            当前目标选项卡层数 = 队列号 // 10
            调试器.trace("坐骑", f"处理队列{队列号}: 目标层={当前目标选项卡层数}")
            if 当前目标选项卡层数 <= 0:
                调试器.warning("坐骑", f"队列{队列号}: 计算出的层数异常({当前目标选项卡层数})，跳过")
                continue
            
            # 获取目标层标签
            目标层标签 = 层标签组.find(str(当前目标选项卡层数))
            if not 目标层标签:
                调试器.debug("坐骑", f"未找到层标签: {当前目标选项卡层数}")
                continue
            
            # 切换层（如果需要）
            if 上次目标选项卡层数 != 当前目标选项卡层数:
                调试器.debug("坐骑", f"切换层: {上次目标选项卡层数} -> {当前目标选项卡层数}")
                if not self.点击层选项(目标层标签, 当前目标选项卡层数):
                    调试器.debug("坐骑", f"点击层选项失败，目标层标签: {目标层标签}")
                    continue
                上次目标选项卡层数 = 当前目标选项卡层数
            
            # 获取坐骑选择区域
            属性名 = f"坐骑页面坐骑选择范围标签{队列号}"
            区域对象 = getattr(self.游戏配置.区域.坐骑, 属性名, None)
            if 区域对象 is None:
                调试器.warning("坐骑", f"未找到区域配置: 坐骑.{属性名}")
                continue
            
            区域 = 区域对象.元组
            filter_config = {
                "color_range": "110,255,0,16,0,16|25,45,150,255,0,16",  
                "keep_color": False,
                "background": "black"
            }
            秒数 = self.辅助识别器.获取刷新秒数(区域,filter_config)
            调试器.trace("坐骑", f"队列{队列号}: 获取刷新秒数={秒数}")
            
            if 秒数 is not None:
                # 更新刷新时间
                self.任务状态.子任务刷新情况[str(队列号)] = time.time() + 秒数
                
                # 判断是否在提前进场时间内
                if 秒数 <= self.任务配置.提前进场秒数:
                    调试器.state("坐骑", f"队列{队列号}: 刷新倒计时{秒数}秒 <= 提前{self.任务配置.提前进场秒数}秒，立即进入")
                    self.任务状态.下次刷新时间 = time.time() + 秒数
                    
                    # 点击进入副本
                    self.页面.创建点击区域操作(区域, 0.2).执行()
                    time.sleep(self.游戏配置.战斗.等待.默认等待秒)
                    self.页面.创建点击区域操作(区域, 0.2).执行()
                    time.sleep(self.游戏配置.战斗.等待.默认等待秒)
                    
                    调试器.debug("坐骑", f"队列{队列号}: 点击进入坐骑副本")
                    if self.页面.跨服战场.坐骑.进入坐骑副本():
                        self.任务状态.当前子任务ID = str(队列号)
                        调试器.state("坐骑", f"队列{队列号}: 成功触发进入副本")
                        return True
                else:
                    调试器.debug("坐骑", f"队列{队列号}: 刷新倒计时{秒数}秒 > 提前{self.任务配置.提前进场秒数}秒，等待中")
        
        # 更新下次刷新时间
        self.更新下一次刷新时间()
        
        调试器.debug("坐骑", "所有已刷新任务处理完毕，无可用进入的副本")
        return False

    def 获取层标签组(self) ->Optional[OCRResult]:
        if self.页面.创建点击区域操作(self.游戏配置.区域.坐骑.坐骑页面1层区域标签.元组, 0.5).执行():
            time.sleep(self.游戏配置.战斗.等待.默认等待秒)
        识别器 = self.线程.文字识别器
        截图 = self.线程.刷新截图()
        if 截图 is None:
            调试器.warning("坐骑", "获取层标签组时截图失败")
            return None

        ocr_result = 识别器.recognize_result(截图,self.游戏配置.区域.坐骑.坐骑页面选层区域标签.元组)
        if not ocr_result:
            调试器.debug("坐骑", "获取层标签组时OCR识别为空")
            return None
        ocr_result=分离粘连文字(ocr_result)
        return ocr_result
    def 执行入口逻辑(self) -> bool:
        """执行坐骑任务入口逻辑"""
        调试器.info("坐骑", "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("坐骑", f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False
        
        当前页面= self.验证当前打开页面()
        调试器.debug("坐骑", f"当前页面: '{当前页面}'")
        if 当前页面 != "坐骑":          
            # 2.1 进入跨服战场页面
            调试器.debug("坐骑", "步骤1: 进入跨服战场页面")
            if not self.页面.主界面操作.进入跨服战场页面():
                调试器.error("坐骑", "进入跨服战场页面失败，入口逻辑中断")
                return False
            调试器.debug("坐骑", "跨服战场页面进入成功")
            
            # 2.2 进入坐骑页面
            调试器.debug("坐骑", "步骤2: 进入坐骑页面")
            if not self.页面.跨服战场.坐骑.点击右侧坐骑页面():
                调试器.error("坐骑", "进入坐骑页面失败，入口逻辑中断")
                return False
            调试器.debug("坐骑", "坐骑页面进入成功")
        else:
            调试器.debug("坐骑", "当前已在坐骑页面，跳过进入步骤")

        
        # 3. 更新剩余次数
        调试器.debug("坐骑", "步骤3: 读取坐骑页面剩余次数")
        if not self.更新区域任务次数(self.游戏配置.区域.坐骑.坐骑页面归属次数标签.元组):
            调试器.warning("坐骑", "读取坐骑页面剩余次数失败，入口逻辑中断")
            return False
        调试器.debug("坐骑", f"剩余次数: {self.任务状态.剩余次数}")
        
        # 4. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("坐骑", f"读取次数后确认为0，次数已用完")
            return False
        
        # 5. 检查刷新时间并进入副本
        层标签组 = self.获取层标签组()
        if not 层标签组:
            调试器.debug("坐骑", "获取层标签组失败")
            return False

        if not self.检查刷新时间并进入副本(层标签组):
            调试器.debug("坐骑", "检查刷新时间并进入副本失败(无可用刷新任务或进入失败)")
            return False

        调试器.state("坐骑", "入口逻辑执行成功，已进入坐骑副本")
        return True
    
  