# tasks/taigumijing.py
"""
太古秘境任务定义
"""


from core.utils import 匹配分组关键字
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from core.debug import 调试器
from pydantic import  Field
import time

@任务定义(
    任务ID="taigumijing",
    调试模式=True,
    任务名称="太古秘境",
    任务类型="小时任务",
    优先级=5,
    地图关键字="太古秘",    
    提前进场秒数=0,
    次数刷新间隔小时 = 2 ,
    子任务队列="",
    击杀顺序="1,2,3,4",
    状态_子任务刷新情况=Field(default_factory=dict),

)
class 太古秘境任务(战斗任务执行器):
    """太古秘境任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)       

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
        调试器.trace(self.调试分类, f"页面识别结果: '{当前页面}'")
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
    def 执行入口逻辑(self) -> bool:
        """执行太古秘境入口逻辑"""
        调试器.info("太古秘境", "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 < 20:
            self.任务状态.剩余次数=0
            调试器.state("太古秘境", "次数不足，跳过执行")
            return False
        
        当前页面= self.验证当前打开页面()
        if 当前页面 != "陨圣":          
            # 2.1 进入跨服战场页面           
            if not self.页面.主界面操作.进入跨服战场页面():
                调试器.error(self.调试分类, "进入跨服战场页面失败，入口逻辑中断")
                return False            
            
            # 2.2 进入古剑页面           
            if not self.页面.跨服战场.陨圣.点击右侧陨圣页面():
                调试器.error(self.调试分类, "进入陨圣页面失败，入口逻辑中断")
                return False            

            # 等待刷新时间，强制等待服务器时间同步
            time.sleep(max(0.5, self.游戏配置.刷新等待秒))
            self.线程.刷新截图()
            
        else:
            调试器.debug(self.调试分类, "当前已在陨圣页面，跳过进入步骤")
 
        if not self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.陨圣.陨圣页面太古秘境标签.元组, 
            self.游戏配置.区域.陨圣.太古秘境页面太古层数区域标签.元组,
            "古"
            ).执行():
            调试器.error(self.调试分类, "点击太古秘境失败，入口逻辑中断")
            return False
        

        # 3. 更新剩余次数
        调试器.debug(self.调试分类,"步骤3: 读取陨圣页面剩余次数")
        filter_config = {
            "color_range": "110,255,0,16,0,16|0,20,90,255,0,16",  
            "keep_color": False,
            "background": "black"
        }
        if not self.更新区域任务次数(self.游戏配置.区域.陨圣.太古秘境页面太古体力值区域标签.元组,filter_config):
            调试器.warning(self.调试分类, "读取陨圣页面体力值次数失败，入口逻辑中断")
            return False
          
        # 4. 再次检查次数
        if self.任务状态.剩余次数 <20:
            调试器.state(self.调试分类, f"读取次数后确认为{self.任务状态.剩余次数}，不进入")
            self.任务状态.剩余次数 =0
            return False

        # 5. 检查刷新时间并进入副本
        调试器.debug(self.调试分类, "步骤4: 检查刷新时间并进入副本")
        if not self.检查刷新时间并进入副本():
            调试器.debug(self.调试分类, "检查刷新时间并进入副本失败(无可用刷新任务或进入失败)")
            return False

        调试器.state(self.调试分类, "入口逻辑执行成功，已进入上古剑冢副本")
        return True
    
   
    def 检查刷新时间并进入副本(self) -> bool:
        """检查剑冢刷新时间，判断是否可以进入"""
        
   
        # 先同步子任务状态（确保配置和状态一致）
        子任务队列 = self.任务配置.子任务队列
        击杀顺序= self.任务配置.击杀顺序
        if 击杀顺序:
            self.当前子任务队列 = [int(x.strip()) for x in 击杀顺序.split(',') if x.strip()]
        else:
            import random
            self.当前子任务队列 = [1, 2, 3, 4]
            random.shuffle(self.当前子任务队列)
        self.更新同步子任务状态()   
        
        需要处理的任务 = self.获取已刷新任务列表()
        调试器.debug(self.调试分类, f"需要处理的任务: {需要处理的任务}")
        if not 需要处理的任务:
            调试器.debug(self.调试分类,"无已刷新任务")
            self.更新下一次刷新时间()
            return False
              
        for 队列号 in 需要处理的任务:
           
            # 获取剑冢选择区域
            区域对象 =self.游戏配置.区域.陨圣.获取刷新标签(队列号)
            if 区域对象 is None:
                调试器.warning(self.调试分类, f"未找到区域配置: 陨圣刷新.{队列号}")
                continue          
            
            区域 = 区域对象.元组
            调试器.debug(self.调试分类, f"队列{队列号}: 获取陨圣选择区域: {区域}")     

            filter_config = {
                "color_range": "110,255,0,16,0,16|0,25,150,255,0,16",                  
                "keep_color": True,
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
                    boss入口=self.游戏配置.区域.陨圣.获取前往标签(队列号)
                    if boss入口 is None:
                        调试器.warning(self.调试分类, f"未找到区域配置: 古剑.古剑页面古剑BOSS进入区域标签{队列号}")
                        continue
                    boss入口区域=boss入口.元组
                                        
                    调试器.debug(self.调试分类, f"队列{队列号}: 点击BOSS详情入口")
                    if not self.页面.创建_通用点击区域验证文字切换 ( 
                        boss入口区域,           
                        self.游戏配置.区域.主界面.小地图地图名显示标签.元组,
                        "太古|秘境"
                        ).执行():
                        调试器.debug(self.调试分类, f"队列{队列号}: 点击BOSS入口后未检测到前往按钮，跳过")
                        continue                    
                    
                    调试器.state(self.调试分类, f"队列{队列号}: 成功触发进入副本")
                    return True
                else:
                    调试器.debug(self.调试分类, f"队列{队列号}: 刷新倒计时{秒数}秒 > 提前{self.任务配置.提前进场秒数}秒，等待中")
        
        # 更新下次刷新时间
        self.更新下一次刷新时间()
        
        调试器.debug(self.调试分类, "所有已刷新任务处理完毕，无可用进入的副本")
        return False