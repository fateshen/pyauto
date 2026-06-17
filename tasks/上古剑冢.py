# tasks/shanggujianzhong.py
"""
上古剑冢任务定义
"""


from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from typing import Optional, Tuple, List,Dict, Any
from pydantic import  Field
from core.utils import 匹配分组关键字, 解析时间文字, 重试, 随机点
from core.debug import 调试器
import time
from core.recognition import OCRResult, ocr, 分离粘连文字



@任务定义(
    任务ID="shanggujianzhong",
    任务名称="上古剑冢",
    任务类型="每日任务",
    调试模式=False,   #########正式需要关闭
    优先级=10,    
    地图关键字="上古剑|上,剑|上古剑冢|上古剑家",
    避让模式使用全局设置= True,
    启用位置复查=True,
    位置复查移动区域 = "",
    位置复查目标中心 = "56,50",
    回城回血使用全局设置=True,
    怪物有无敌=True,      
    工作时间开始=10,
    提前进场秒数=15,
    子任务队列="3,4",
    次优先级任务队列="1,2",
    每日更新任务数量=4,
    次优先级任务开始时间=22,
    不使用多倍奖励=False,
    状态_子任务刷新情况=Field(default_factory=dict),
    状态_当前子任务ID="",#这个当前子任务ID主要是为了正确处理避让冷却等，不作为其他逻辑使用
)
class 上古剑冢(战斗任务执行器):
    """上古剑冢任务执行器"""
    
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
        return  当前时间小时 >= self.任务配置.次优先级任务开始时间 and self.任务状态.剩余次数 > self.任务配置.每日更新任务数量
    def 更新当前任务队列(self) -> bool:
        """
        获取任务队列（根据溢出情况决定）
        
        返回:
            任务号列表（已排序）
        """             
       
        """
        获取任务队列（根据溢出情况决定）
        
        返回:
            任务号列表（已排序）
        """             
        主任务列表 = [int(x.strip()) for x in self.任务配置.子任务队列.split(',') if x.strip()]
        主任务列表.sort(reverse=True)
        # 检查是否需要溢出处理
        if not self.检查任务数量溢出():
            # 不需要溢出，只返回主任务
            self.当前子任务队列 = 主任务列表
            调试器.debug(self.调试分类, f"任务队列(正常模式): {self.当前子任务队列}")
            return True
        次优先级列表 = [int(x.strip()) for x in self.任务配置.次优先级任务队列.split(',') if x.strip()]
        合并后列表 = list(set(主任务列表 + 次优先级列表))
        合并后列表.sort(reverse=True)
        self.当前子任务队列  = 合并后列表
        调试器.debug(self.调试分类, f"任务队列(溢出模式): {self.当前子任务队列}")
        return True
    def _排序已刷新列表(self, 列表: List[int]) -> List[int]:
        """
        对已刷新列表排序（子类可覆盖）
        默认从大到小排序
        
        坐骑任务需要覆盖此方法使用专用排序
        """
        列表.sort(reverse=True)
        return 列表 
    
    def 检查刷新时间并进入副本(self) -> bool:
        """检查剑冢刷新时间，判断是否可以进入"""
        
   
        # 先同步子任务状态（确保配置和状态一致）
        self.更新当前任务队列()
        self.更新同步子任务状态()   
        
        需要处理的任务 = self.获取已刷新任务列表()
        调试器.debug("上古剑冢", f"需要处理的任务: {需要处理的任务}")
        if not 需要处理的任务:
            调试器.debug("上古剑冢", "无已刷新任务")
            self.更新下一次刷新时间()
            return False
              
        for 队列号 in 需要处理的任务:
           
            # 获取剑冢选择区域
            属性名 = f"古剑页面刷新时间区域标签{队列号}"
            区域对象 = getattr(self.游戏配置.区域.古剑, 属性名, None)
            if 区域对象 is None:
                调试器.warning("上古剑冢", f"未找到区域配置: 古剑.{属性名}")
                continue          
            
            区域 = 区域对象.元组
            调试器.debug("上古剑冢", f"队列{队列号}: 获取剑冢选择区域: {区域}")     

            filter_config = {
                "color_range": "110,255,0,16,0,16|25,100,150,255,0,16",  
                "keep_color": False,
                "background": "black"
            }
            秒数 = self.辅助识别器.获取刷新秒数(区域,filter_config)
            调试器.trace("上古剑冢", f"队列{队列号}: 获取刷新秒数={秒数}")
            
            if 秒数 is not None:
                # 更新刷新时间
                self.任务状态.子任务刷新情况[str(队列号)] = time.time() + 秒数
                
                # 判断是否在提前进场时间内
                if 秒数 <= self.任务配置.提前进场秒数:
                    调试器.state("上古剑冢", f"队列{队列号}: 刷新倒计时{秒数}秒 <= 提前{self.任务配置.提前进场秒数}秒，立即进入")
                    self.任务状态.下次刷新时间 = time.time() + 秒数
                    
                    # 点击进入副本
                    boss详情入口=getattr(self.游戏配置.区域.古剑,  f"古剑页面古剑BOSS进入区域标签{队列号}", None)
                    boss详情入口区域=boss详情入口.元组
                    if not boss详情入口区域:
                        调试器.warning("上古剑冢", f"未找到BOSS入口区域配置: 古剑.古剑页面古剑BOSS进入区域标签{队列号}")
                        continue
                    
                    调试器.debug("上古剑冢", f"队列{队列号}: 点击BOSS详情入口")
                    if not self.页面.创建_通用点击区域验证文字切换 ( 
                        boss详情入口区域,           
                        self.游戏配置.区域.古剑.古剑页面前往按钮标签.元组,
                        "前|往"
                        ).执行():
                        调试器.debug("上古剑冢", f"队列{队列号}: 点击BOSS入口后未检测到前往按钮，跳过")
                        continue
                    #这里还是增加时间二次确认好了
                    # self.辅助识别器.移出鼠标提示()
                    秒数确认 = self.辅助识别器.获取刷新秒数(self.游戏配置.区域.古剑.古剑页面前往页面刷新时间区域标签.元组,filter_config)
                    if 秒数确认 is not None:
                        self.任务状态.子任务刷新情况[str(队列号)] = time.time() + 秒数确认
                        if 秒数确认 > self.任务配置.提前进场秒数:
                            调试器.state("上古剑冢", f"队列{队列号}: 刷新倒计时{秒数确认}秒 > 提前{self.任务配置.提前进场秒数}秒，等待刷新")
                            return False
                    调试器.debug("上古剑冢", f"队列{队列号}: 点击前往按钮")
                    if not self.页面.创建_通用点击区域验证文字切换 ( 
                        self.游戏配置.区域.古剑.古剑页面前往按钮标签.元组,           
                        self.游戏配置.区域.古剑.古剑页面前往击杀按钮标签.元组,
                        "前|往|击杀"
                        ).执行() :
                        调试器.debug("上古剑冢", f"队列{队列号}: 点击前往后未检测到击杀按钮，跳过")
                        continue
                    
                    if self.任务配置.不使用多倍奖励:
                        调试器.debug("上古剑冢", "选择1倍奖励")
                        self.页面.创建点击区域操作(
                            self.游戏配置.区域.古剑.古剑页面1倍奖励选择区域标签.元组,
                            0.3
                        ).执行()
                    
                    调试器.debug("上古剑冢", "点击进入古剑副本")
                    if  self.页面.跨服战场.古剑.进入古剑副本.执行():
                        self.任务状态.当前子任务ID = str(队列号)
                        调试器.state("上古剑冢", f"队列{队列号}: 成功触发进入副本")
                        return True
                else:
                    调试器.debug("上古剑冢", f"队列{队列号}: 刷新倒计时{秒数}秒 > 提前{self.任务配置.提前进场秒数}秒，等待中")
        
        # 更新下次刷新时间
        self.更新下一次刷新时间()
        
        调试器.debug("上古剑冢", "所有已刷新任务处理完毕，无可用进入的副本")
        return False

    def 执行入口逻辑(self) -> bool:
        """执行上古剑冢入口逻辑"""
        调试器.info("上古剑冢", "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("上古剑冢", f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
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
        
        # 3. 更新剩余次数
        调试器.debug("上古剑冢", "步骤3: 读取古剑页面剩余次数")
        filter_config = {
            "color_range": "110,255,0,16,0,16|0,20,90,255,0,16",  
            "keep_color": False,
            "background": "black"
        }
        if not self.更新区域任务次数(self.游戏配置.区域.古剑.古剑页面剩余次数区域标签.元组,filter_config):
            调试器.warning("上古剑冢", "读取古剑页面剩余次数失败，入口逻辑中断")
            return False
        调试器.debug("上古剑冢", f"剩余次数: {self.任务状态.剩余次数}")
        
        # 4. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("上古剑冢", f"读取次数后确认为0，次数已用完")
            return False
        
        # 5. 检查刷新时间并进入副本
        调试器.debug("上古剑冢", "步骤4: 检查刷新时间并进入副本")
        if not self.检查刷新时间并进入副本():
            调试器.debug("上古剑冢", "检查刷新时间并进入副本失败(无可用刷新任务或进入失败)")
            return False

        调试器.state("上古剑冢", "入口逻辑执行成功，已进入上古剑冢副本")
        return True
   

    def _副本内检查钩子(self) -> str | None:
        #位置同古剑
        return self._古剑类副本勾子检查更新副本内剩余次数()
    
    def _执行抢怪操作(self) -> bool:
        return self._执行抢归属动作古剑类副本()
    
    def _开战前避让检查(self) -> str | None:
        return self._开战前避让检查古剑类副本()
    