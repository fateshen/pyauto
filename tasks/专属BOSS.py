# tasks/zhuanshu_BOSS.py
"""
专属BOSS任务定义
"""
from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from core.debug import 调试器
import time
import random
import re
from typing import Tuple, Union, List, Optional
from core.utils import 匹配分组关键字, 解析时间文字, 随机点
def 提取等级数字(text: str) -> Union[int, bool]:
        """
        从文字中提取等级数字
        
        参数:
            text: 如 "天之主[5400级]" 或 "雷使[5300级]"
        
        返回:
            等级数字，如 5400，未找到返回 False
        """
        import re
        
        # 匹配 [数字级] 格式
        match = re.search(r'\[(\d+)级\]', text)
        if match:
            return int(match.group(1))
        
        # 匹配 数字级 格式（无括号）
        match = re.search(r'(\d+)级', text)
        if match:
            return int(match.group(1))
        
        return False
def 获取需击杀专属BOSS刷新等级信息(ocr_result) -> Tuple[Union[str, bool], Tuple[int, int, int, int], Union[int, bool]]:
        """
        从OCR结果中获取倒数第二次出现的含有"刷"的文字、坐标，以及该文字前的等级
        
        参数:
            ocr_result: OCRResult 对象（有序列表版本）
        
        返回:
            (状态文字, 坐标, 等级)
            - 状态文字: 找到时返回 "已刷新" / "未刷新" 等，未找到时返回 False
            - 坐标: 找到时返回 (left, top, right, bottom)，未找到时返回 (-1,-1,-1,-1)
            - 等级: 找到时返回等级数字，未找到时返回 False
        
        示例:
            如果OCR结果中有多个"已刷新"：
                ["已首杀", "已刷新", "雷使[5300级]", "已刷新", "天之主[5400级]"]
            返回: ("已刷新", 坐标, 5400)
            
            如果只有1个"已刷新"：
                返回: (False, (-1,-1,-1,-1), False)
            
            如果没有"已刷新"：
                返回: (False, (-1,-1,-1,-1), False)
        """
        if not ocr_result or len(ocr_result) == 0:
            return False, (-1, -1, -1, -1), False
        
        # 收集所有包含"刷"的文字及其索引
        刷新项列表 = []
        for i, (text, box) in enumerate(ocr_result.items):
            if "刷" in text:
                刷新项列表.append({
                    "index": i,
                    "text": text,
                    "box": box
                })
        
        # 如果没有找到或只找到1个包含"刷"的文字
        if len(刷新项列表) < 2:
            return False, (-1, -1, -1, -1), False
        
        # 获取倒数第二个（索引为 -2）
        目标项 = 刷新项列表[-1]
        目标索引 = 目标项["index"]    
        
        # 查找该文字前面的等级
        # 向前搜索，找到第一个包含"级"的文字（通常是BOSS名称）
        等级 = False
        for i in range(目标索引 - 1, -1, -1):
            text, _ = ocr_result[i]
            if "级" in text:
                # 提取等级数字
                等级 = 提取等级数字(text)
                if 等级 is not False:
                    break
        # 获取倒数第二个（索引为 -2）
        目标项 = 刷新项列表[-2]
        目标文字 = 目标项["text"]
        目标坐标 = 目标项["box"]

        return 目标文字, 目标坐标, 等级


@任务定义(
    任务ID="zhuanshu_BOSS",
    任务名称="专属BOSS",
    任务类型="小时任务",
    优先级=5,
    地图关键字="专属,B|BOSS,专",
    提前进场秒数=0,
    次数刷新间隔小时=2,
)
class 专属任务(战斗任务执行器):
    """专属BOSS任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)        
    
    def 检查刷新时间(self, 区域: Tuple[int, int, int, int]) -> bool:
        截图 = self.线程.截图
        if 截图 is None:
            调试器.debug("专属BOSS", "截图为空，无法检查刷新时间")
            return False        
        识别器= self.线程.文字识别器
        鼠标= self.线程.动作执行器
        当前BOSS信息区域= 区域
        专属BOSS等级选项卡区域= self.游戏配置.区域.专属BOSS.专属BOSS等级选择卡区域标签.元组        
        原始lev=提取等级数字(识别器.recognize_text(截图,当前BOSS信息区域))

        调试器.debug("专属BOSS", "识别等级选项卡区域")
        ocr_result = 识别器.recognize_result(截图,专属BOSS等级选项卡区域)
        text,region,maxlevel=获取需击杀专属BOSS刷新等级信息(ocr_result)
        调试器.trace("专属BOSS", f"等级选项卡识别: text='{text}', region={region}, maxlevel={maxlevel}")
        if not text :
            调试器.debug("专属BOSS", "未识别到刷新信息，尝试拖拽等级列表")
            x,y=随机点(专属BOSS等级选项卡区域, 0.5)
            鼠标.drag(x, y, x+random.randint(0, 10), y+random.randint(100, 200),random.uniform(0.1, 0.5))
            截图=self.线程.刷新截图()
            ocr_result = 识别器.recognize_result(截图,专属BOSS等级选项卡区域)
            text,region,maxlevel=获取需击杀专属BOSS刷新等级信息(ocr_result)
            调试器.trace("专属BOSS", f"拖拽后重新识别: text='{text}', region={region}, maxlevel={maxlevel}")
        if not text :
            调试器.debug("专属BOSS", "拖拽后仍未识别到刷新信息")
            return False
        
        for i in range(2):
            调试器.debug("专属BOSS", f"第{i+1}次点击BOSS等级选项卡")
            self.页面.创建点击区域操作(region).执行()
            time.sleep(self.游戏配置.战斗.等待.默认等待秒)
            截图=self.线程.刷新截图()
            if 截图 is None:
                调试器.warning("专属BOSS", f"第{i+1}次点击后截图失败")
                continue
            当前专属BOSS信息 = 识别器.recognize_text(截图,当前BOSS信息区域)
            lev=提取等级数字(当前专属BOSS信息)
            调试器.trace("专属BOSS", f"当前BOSS信息: '{当前专属BOSS信息}', 提取等级: {lev}, 需要等级: {maxlevel}")
            if lev+100==maxlevel and maxlevel>=原始lev:
                秒数=解析时间文字(当前专属BOSS信息)
                if "已刷" in text:
                    秒数=0
                    调试器.trace("专属BOSS", "检测到'已刷'字样，秒数=0")
                if 秒数 is not None:
                    self.任务状态.下次刷新时间 = time.time() + 秒数
                    调试器.debug("专属BOSS", f"刷新倒计时: {秒数}秒")
                    
                    # 判断是否在提前进场时间内
                    if 秒数 <= self.任务配置.提前进场秒数:
                        调试器.state("专属BOSS", f"刷新倒计时{秒数}秒 <= 提前{self.任务配置.提前进场秒数}秒，立即进入")
                        return True
                    else:
                        调试器.debug("专属BOSS", f"刷新倒计时{秒数}秒 > 提前{self.任务配置.提前进场秒数}秒，等待中")
                        return False
                
                调试器.debug("专属BOSS", f"无法解析时间: '{当前专属BOSS信息}'")
            else:
                调试器.trace("专属BOSS", f"等级不匹配: {lev}+100 != {maxlevel}，跳过")
        
        调试器.debug("专属BOSS", "2次尝试后仍未找到匹配的BOSS")
        return False

    def 执行入口逻辑(self) -> bool:
        """执行专属BOSS入口逻辑"""
        调试器.info("专属BOSS", "开始执行入口逻辑")
        
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("专属BOSS", f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False
       
        # 2. 进入首领页面
        调试器.debug("专属BOSS", "步骤1: 进入首领页面")
        if not self.页面.主界面操作.进入首领页面():
            调试器.error("专属BOSS", "进入首领页面失败，入口逻辑中断")
            return False
        调试器.debug("专属BOSS", "首领页面进入成功")
        
        # 3. 进入专属页面
        调试器.debug("专属BOSS", "步骤2: 点击专属页面标签")
        if not self.页面.首领任务.专属BOSS.点击右侧专属页面():
            调试器.error("专属BOSS", f"点击右侧专属页面失败，区域: {self.动态标签.首领页面右侧标签.专属.元组}")
            return False
        调试器.debug("专属BOSS", "专属页面进入成功")
      
        #  4. 更新剩余次数
        调试器.debug("专属BOSS", "步骤3: 读取专属BOSS剩余次数")
        if not self.更新区域任务次数(self.游戏配置.区域.专属BOSS.专属BOSS剩余次数区域标签.元组):
            调试器.warning("专属BOSS", "读取专属BOSS剩余次数失败，入口逻辑中断")
            return False
        调试器.debug("专属BOSS", f"剩余次数: {self.任务状态.剩余次数}")
        
        # 5. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state("专属BOSS", f"读取次数后确认为0，次数已用完")
            return False        
        
        # 6. 检查刷新时间
        调试器.debug("专属BOSS", "步骤4: 检查刷新时间")
        if not self.检查刷新时间(self.游戏配置.区域.专属BOSS.专属当前BOSS当前情况区域标签.元组):
            调试器.debug("专属BOSS", "刷新时间未到或检查失败")
            return False        

        if self.扫荡检查逻辑():
            return True

        # 7. 进入专属BOSS副本
        调试器.debug("专属BOSS", "步骤5: 进入专属BOSS副本")
        if not self.页面.首领任务.专属BOSS.进入专属BOSS副本():
            调试器.error("专属BOSS", "进入专属BOSS副本失败，入口逻辑中断")
            return False
        
        调试器.state("专属BOSS", "入口逻辑执行成功，已进入专属BOSS副本")
        return True
    
    def 扫荡检查逻辑(self) -> bool:
        """扫荡检查逻辑"""
        截图=self.线程.截图
        count=0        
        if 截图 is None:
            调试器.warning("专属BOSS", "刷新截图失败，扫荡检查逻辑中断")
            return False
        text = self.线程.文字识别器.recognize_text(截图, self.游戏配置.区域.专属BOSS.专属BOSS前往挑战按钮标签.元组)
        if 匹配分组关键字(text, "扫|荡" ):
            for i in range(5):   
                self.页面.创建点击区域操作(self.游戏配置.区域.专属BOSS.专属BOSS前往挑战按钮标签.元组).执行()
                time.sleep(self.游戏配置.战斗.等待.默认等待秒)
                self.线程.刷新截图()
                self.通用操作.领取奖励退出操作()                
                time.sleep(self.游戏配置.战斗.等待.默认等待秒)
                self.线程.刷新截图()
                self.更新区域任务次数(self.游戏配置.区域.专属BOSS.专属BOSS剩余次数区域标签.元组)
                if self.任务状态.剩余次数 <= 0:
                    调试器.state("专属BOSS", "扫荡完成")
                    return True
                count+=1
                continue
        if count>0:
            调试器.state("专属BOSS", "扫荡完成")
            return True
        return False

