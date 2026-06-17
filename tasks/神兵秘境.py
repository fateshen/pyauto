# tasks/shenbing.py
"""
神兵秘境任务定义
"""
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from typing import Optional, Tuple, List
from core.utils import 解析时间文字
from core.debug import 调试器
import time
from core.recognition import OCRResult
import re

@任务定义(
    任务ID="shenbing_mijing",
    任务名称="神兵秘境",
    任务类型="小时任务",
    优先级=5,
    地图关键字="神兵", 
    工作时间开始=0,
    提前进场秒数=0,
    次数刷新间隔小时 = 1 ,
)
class 神兵秘境任务(战斗任务执行器):
    """神兵秘境任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)
    
    def _解析刷新时间(self,文字列表: list) -> int:
        """
        从识别到的文字列表中解析刷新时间，返回最小秒数
        
        规则：
            1. 如果存在"已刷新"字样，直接返回 0
            2. 否则，提取所有"xx分xx秒"格式，转换为秒数，取最小值
            3. 如果没有找到任何时间格式，返回 None（表示无法解析）
        
        参数:
            文字列表: OCR 识别返回的文字列表，每个元素可能是字符串或包含文字的嵌套结构
        
        返回:
            int: 最小秒数，如果有"已刷新"则返回 0
                如果没有任何时间格式，返回 None
            
        示例:
            >>> 解析刷新时间(["剩余时间: 5分30秒", "怪物等级: 50级"])
            330
            >>> 解析刷新时间(["已刷新", "5分30秒"])
            0
            >>> 解析刷新时间(["无时间信息"])
            None
            """
        # 辅助函数：从单个字符串中提取秒数
        def 提取秒数(文本: str) -> Optional[int]:
            """从文本中提取"xx分xx秒"并转换为秒数，返回 None 表示没有匹配"""
            # 匹配模式：数字+分+数字+秒
            # 支持：5分30秒、05分05秒、0分0秒 等
            匹配 = re.search(r'(\d+)\s*分\s*(\d+)\s*秒', 文本)
            if 匹配:
                分钟 = int(匹配.group(1))
                秒 = int(匹配.group(2))
                return 分钟 * 60 + 秒
            return None
        
        # 步骤1：展平文字列表，提取所有字符串
        所有文本 = []
        for 项 in 文字列表:
            if isinstance(项, str):
                所有文本.append(项)
            elif isinstance(项, (list, tuple)):
                # 递归展平嵌套结构（应对 OCR 返回的复杂格式）
                def 展平(嵌套列表):
                    for 元素 in 嵌套列表:
                        if isinstance(元素, str):
                            yield 元素
                        elif isinstance(元素, (list, tuple)):
                            yield from 展平(元素)
                        elif isinstance(元素, dict) and 'text' in 元素:
                            # 处理 paddleocr 返回的格式: [文本框, [文字, 置信度]]
                            yield 元素['text']
                for 子项 in 展平(项):
                    所有文本.append(子项)
        
        # 步骤2：检查是否有"已刷新"
        for 文本 in 所有文本:
            if "已刷新" in 文本:
                调试器.trace("神兵秘境", f"检测到'已刷新'字样: '{文本}'")
                return 0
        
        # 步骤3：提取所有时间格式，取最小值
        秒数列表 = []
        for 文本 in 所有文本:
            秒数 = 提取秒数(文本)
            if 秒数 is not None:
                秒数列表.append(秒数)
        
        if 秒数列表:
            最小秒数 = min(秒数列表)
            调试器.trace("神兵秘境", f"解析到时间列表: {秒数列表}, 取最小值={最小秒数}秒")
            return 最小秒数
        
        调试器.trace("神兵秘境", f"无法解析任何时间格式，原始文字: {所有文本}")
        return None  # 没有找到任何时间格式
    def 检查刷新时间(self,区域:Tuple[int,int,int,int]) -> bool:
        """检查刷新时间，判断是否可以进入"""
        截图 = self.线程.刷新截图()
        if 截图 is None:
            调试器.warning("神兵秘境", "刷新截图失败，无法检查刷新时间")
            return False
        
        结果= self.线程.文字识别器.recognize_result(
            截图, 区域
        ).get_all_texts()
        
        if not 结果:
            调试器.debug("神兵秘境", "未识别到刷新时间文字")
            return False
        
               
        # 解析时间数字
        秒数 = self._解析刷新时间(结果)
        if 秒数 is not None:
            self.任务状态.下次刷新时间 = time.time() + 秒数
            调试器.debug("神兵秘境", f"刷新倒计时: {秒数}秒")
            
            # 判断是否在提前进场时间内
            if 秒数 <= self.任务配置.提前进场秒数:
                调试器.state("神兵秘境", f"刷新倒计时{秒数}秒 <= 提前{self.任务配置.提前进场秒数}秒，立即进入")
                return True
            else:
                调试器.debug("神兵秘境", f"刷新倒计时{秒数}秒 > 提前{self.任务配置.提前进场秒数}秒，等待中")
                return False
        
        调试器.debug("神兵秘境", f"无法解析刷新时间，原始识别结果: {结果}")
        return False

    def 执行入口逻辑(self) -> bool:
        """执行神兵秘境入口逻辑"""
        调试器.info("神兵秘境", "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("神兵秘境", f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False
        
        # 2. 进入跨服战场页面
        调试器.debug("神兵秘境", "步骤1: 进入跨服战场页面")
        if not self.页面.主界面操作.进入跨服战场页面():
            调试器.error("神兵秘境", "进入跨服战场页面失败，入口逻辑中断")
            return False
        调试器.debug("神兵秘境", "跨服战场页面进入成功")
        
        # 3. 更新剩余次数
        调试器.debug("神兵秘境", "步骤2: 读取跨服页面神兵次数")
        if not self.更新区域任务次数(self.游戏配置.区域.战场页面.跨服页面神兵次数标签.元组):
            调试器.warning("神兵秘境", "读取跨服页面神兵次数失败，入口逻辑中断")
            return False
        调试器.debug("神兵秘境", f"剩余次数: {self.任务状态.剩余次数}")
        
        # 4. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("神兵秘境", f"读取次数后确认为0，次数已用完")
            return False
 
                 
        # 5. 进入秘境入口页面
        调试器.debug("神兵秘境", "步骤3: 进入神兵页面")
        if not self.页面.跨服战场.神兵.进入神兵页面():
            调试器.error("神兵秘境", "进入神兵页面失败，入口逻辑中断")
            return False
        调试器.debug("神兵秘境", "神兵页面进入成功")
        
        time.sleep(1)
        # 6. 检查刷新时间
        调试器.debug("神兵秘境", "步骤4: 检查刷新时间")
        if not self.检查刷新时间(self.游戏配置.区域.神兵.神兵页面刷新情况标签.元组):
            调试器.debug("神兵秘境", "刷新时间未到或检查失败")
            return False
        
        # 7. 点击进入秘境  
        调试器.debug("神兵秘境", "步骤5: 点击进入神兵秘境副本")
        if not self.页面.跨服战场.神兵.进入神兵秘境副本():
            调试器.error("神兵秘境", "点击挑战按钮失败，入口逻辑中断")
            return False

        调试器.state("神兵秘境", "入口逻辑执行成功，已进入神兵秘境副本")
        return True
       
    def _副本内检查钩子(self) -> str | None:
        if  self.更新区域任务次数(self.游戏配置.区域.神兵.神兵副本剩余次数标签.元组):
            if self.任务状态.剩余次数 <= 0:
                调试器.state("神兵秘境", "副本内检查次数已用完，退出副本")
                self.退出副本()
                return "完成"
            else:
                调试器.debug("神兵秘境", f"副本内剩余次数: {self.任务状态.剩余次数}")
        return None