# tasks/wuxingdongtian.py
"""
五行洞天任务定义
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
    任务ID="wuxingdongtian",
    任务名称="五行洞天",
    任务类型="每日任务",
    调试模式=False,   #########正式需要关闭
    优先级=10,
    地图关键字="腐,毒,林|腐,毒疼林|尘,地脉谷|战场万剑|弱水牢|炎熔核|尘,地,谷|场万剑|冥,弱水牢|劫炎,核",
    避让模式使用全局设置= True,
    启用位置复查=True,
    位置复查移动区域 = "",
    位置复查目标中心 = "15,19",
    回城回血使用全局设置=True,
    怪物有无敌=True,      
    工作时间开始=10,
    提前进场秒数=15,
    子任务队列="1",
    次优先级任务队列="2,3",
    每日更新任务数量=3,
    次优先级任务开始时间=22,
    不使用多倍奖励=False,
    状态_子任务刷新情况=Field(default_factory=dict),
    状态_当前子任务ID="",#这个当前子任务ID主要是为了正确处理避让冷却等，不作为其他逻辑使用
)
class 五行洞天(战斗任务执行器):
    """五行洞天任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)
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
        主任务列表 = [int(x.strip()) for x in self.任务配置.子任务队列.split(',') if x.strip()]
        主任务列表.sort()
        # 检查是否需要溢出处理
        if not self.检查任务数量溢出():
            # 不需要溢出，只返回主任务
            self.当前子任务队列 = 主任务列表
            调试器.debug(self.调试分类, f"任务队列(正常模式): {self.当前子任务队列}")
            return True
        次优先级列表 = [int(x.strip()) for x in self.任务配置.次优先级任务队列.split(',') if x.strip()]
        合并后列表 = list(set(主任务列表 + 次优先级列表))
        合并后列表.sort()
        self.当前子任务队列  = 合并后列表
        调试器.debug(self.调试分类, f"任务队列(溢出模式): {self.当前子任务队列}")
        return True
   
    def 检查刷新时间并进入副本(self) -> bool:
        """检查剑冢刷新时间，判断是否可以进入"""
        
   
        # 先同步子任务状态（确保配置和状态一致）
        self.更新当前任务队列()
        self.更新同步子任务状态()   
        
        需要处理的任务 = self.获取已刷新任务列表()
        调试器.debug(self.调试分类, f"需要处理的任务: {需要处理的任务}")
        if not 需要处理的任务:
            调试器.debug(self.调试分类, "无已刷新任务")
            self.更新下一次刷新时间()
            return False

        for 队列号 in 需要处理的任务:
           
            # 获取剑冢选择区域
            属性名 = f"五行洞天页面BOSS详情进入范围标签{队列号}"
            区域对象 = getattr(self.游戏配置.区域.五行洞天, 属性名, None)
            if 区域对象 is None:
                调试器.warning(self.调试分类, f"未找到区域配置: 五行洞天.{属性名}")
                continue          
            
            区域 = 区域对象.元组
            调试器.debug(self.调试分类, f"队列{队列号}: 获取时间选择区域: {区域}")     

            filter_config = {
                "color_range": "110,255,0,16,0,16|25,100,150,255,0,16",  
                "keep_color": False,
                "background": "black"
            }
            秒数 = self.辅助识别器.获取刷新秒数(区域,filter_config)
            调试器.trace(self.调试分类, f"队列{队列号}: 获取刷新秒数={秒数}")
            
            if 秒数 is not None:
                # 更新刷新时间
                self.任务状态.子任务刷新情况[str(队列号)] = time.time() + 秒数
                
                # 判断是否在提前进场时间内
                if 秒数 <= self.任务配置.提前进场秒数:
                    调试器.state(self.调试分类, f"队列{队列号}: 刷新倒计时{秒数}秒 <= 提前{self.任务配置.提前进场秒数}秒，立即进入")
                    self.任务状态.下次刷新时间 = time.time() + 秒数
                    
                    # 点击进入副本                    
                    调试器.debug(self.调试分类, f"队列{队列号}: 点击BOSS详情入口")
                    色彩校正区域=区域[0],区域[1]-64,区域[2],区域[3]+25
                    checkN=0
                    for i in range(3):                    
                        self.通用操作.点击区域(区域)
                        time.sleep(self.游戏配置.战斗.等待.默认等待秒)
                        截图 = self.线程.刷新截图()
                        if 截图 is None: continue
                        numbers=self.线程.像素分析器.count_colors_by_range(截图,色彩校正区域,"246,255,248,255,246,255")
                        if numbers and  numbers[0]>0: 
                            checkN=numbers[0]
                            调试器.debug(self.调试分类, f"队列{队列号}: 切换到洞天BOSS选项卡")
                            break
                    if checkN==0:
                        调试器.debug(self.调试分类, f"队列{队列号}: 未找到洞天BOSS选项卡")
                        continue                    
                    # self.辅助识别器.移出鼠标提示()  
                    
                    调试器.debug(self.调试分类, "点击进入副本")
                    if  self.页面.大千世界.五行洞天.进入五行洞天副本.执行():
                        调试器.state(self.调试分类, f"队列{队列号}: 成功触发进入副本")
                        self.任务状态.当前子任务ID = str(队列号)
                        return True
                else:
                    调试器.debug(self.调试分类, f"队列{队列号}: 刷新倒计时{秒数}秒 > 提前{self.任务配置.提前进场秒数}秒，等待中")
        
        # 更新下次刷新时间
        self.更新下一次刷新时间()
        
        调试器.debug(self.调试分类, "所有已刷新任务处理完毕，无可用进入的副本")
        return False

    def 执行入口逻辑(self) -> bool:
        """执行五行洞天入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False
        
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug(self.调试分类, "展开右上角任务帘失败")
            return False

        if not self.页面.大千世界.进入大千世界页面():    
            调试器.debug(self.调试分类, "进入大千世界页面失败")
            return False
        

        if not self.页面.大千世界.五行洞天.进入五行洞天任务页面():    
            调试器.debug(self.调试分类, "进入五行洞天任务页面失败")
            return False
        
        # 等待刷新时间，强制等待服务器时间同步
        time.sleep(max(0.5, self.游戏配置.刷新等待秒))
        self.线程.刷新截图()

        # 3. 更新剩余次数
        调试器.debug(self.调试分类, "步骤3: 读取五行洞天页面剩余次数")
        filter_config = {
                "color_range": "110,255,0,16,0,16|0,20,90,255,0,20",  
                "color_diff": "5-80,255,80,255,80,255",
                "keep_color": False,
                "background": "black"
            }
        if not self.更新区域任务次数(self.游戏配置.区域.五行洞天.五行洞天页面剩余奖励次数范围标签.元组,filter_config):
            调试器.warning(self.调试分类, "读取五行洞天页面剩余次数失败，入口逻辑中断")
            return False
        调试器.debug(self.调试分类, f"剩余次数: {self.任务状态.剩余次数}")
        
        # 4. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"读取次数后确认为0，次数已用完")
            return False
        
        # 5. 检查刷新时间并进入副本
        调试器.debug(self.调试分类, "步骤4: 检查刷新时间并进入副本")
        if not self.检查刷新时间并进入副本():
            调试器.debug(self.调试分类, "检查刷新时间并进入副本失败(无可用刷新任务或进入失败)")
            return False

        调试器.state(self.调试分类, "入口逻辑执行成功，已进入五行洞天副本")
        return True
   
    def _副本内检查钩子(self) -> str | None:
        #位置同古剑
        return self._古剑类副本勾子检查更新副本内剩余次数()
    
    def _执行抢怪操作(self) -> bool:
        return self._执行抢归属动作古剑类副本()
    
    def _开战前避让检查(self) -> str | None:
        return self._开战前避让检查古剑类副本()
    