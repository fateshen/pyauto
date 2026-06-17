# tasks/shenjiemijing.py
"""
神界秘境任务定义
"""
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
    任务ID="shenjiemijing",
    任务名称="神界秘境",
    调试模式=False,
    任务类型="每日任务",
    优先级=2,    
    地图关键字="星宿秘境|星宿秘|星宿,境", 
    工作时间开始=0,
    提前进场秒数=0
)
class 神界秘境任务(战斗任务执行器):
    """神界秘境任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
   
    def 执行入口逻辑(self) -> bool:
        """执行神界秘境入口逻辑"""
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
        
        if not self.页面.大千世界.神界页面.进入神界页面():    
            调试器.debug(self.调试分类, "进入神界页面失败")
            return False
        
        if not self.页面.大千世界.神界页面.进入神界秘境页面():    
            调试器.debug(self.调试分类, "进入神界秘境页面失败")
            return False
        
        # 等待刷新时间，强制等待服务器时间同步
        time.sleep(max(0.5, self.游戏配置.刷新等待秒))
        self.线程.刷新截图()

        # 3. 更新剩余次数
        filter_config = {
                "color_range": "25,60,150,255,0,16",                 
                "keep_color": False,
                "background": "black"
            }
        调试器.debug(self.调试分类, "步骤2: 读取神界秘境次数")
        if not self.更新区域任务次数(self.游戏配置.区域.神界大陆.神界秘境页面剩余体力值标签.元组,filter_config):
            调试器.warning(self.调试分类, "读取神界秘境次数失败，入口逻辑中断")
            return False
        调试器.debug(self.调试分类, f"剩余次数: {self.任务状态.剩余次数}")

        # 4. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"读取次数后确认为0，次数已用完")
            return False
        
        截图 = self.线程.截图
        if 截图 is None:
            截图= self.线程.刷新截图()
        if 截图 is None:
            return False
        ocr_result = self.线程.文字识别器.recognize_result(截图,缩放区域(self.游戏配置.区域.神界大陆.神界秘境前往挑战按钮标签.元组,1.2))
        print( ocr_result.get_all_text())
        if ocr_result:
            挑战文字区域=ocr_result.find("前往|挑战")
            扫荡文字区域=ocr_result.find("扫|荡")
        else:
            调试器.debug(self.调试分类, "未能正确识别前往|挑战|扫荡文字区域")
            return False
        
        if 扫荡文字区域:
            self.通用操作.点击区域(扫荡文字区域)
            调试器.debug(self.调试分类, "点击扫荡按钮")
            time.sleep(1)
            self.线程.刷新截图()
            if self.通用操作.领取奖励退出操作():
                调试器.state(self.调试分类, "扫荡成功")
                self.更新区域任务次数(self.游戏配置.区域.神界大陆.神界秘境页面剩余体力值标签.元组,filter_config)
                return True

        if not 挑战文字区域:
            调试器.debug(self.调试分类, "未找到前往|挑战文字区域")            
            return False
        
        # 7. 点击进入秘境  
        调试器.debug(self.调试分类, "步骤5: 点击进入神界秘境副本")
        if not self.页面.大千世界.神界页面.进入神界秘境副本():
            调试器.error(self.调试分类, "点击挑战按钮失败，入口逻辑中断")
            return False

        调试器.state(self.调试分类, "入口逻辑执行成功，已进入神界秘境副本")
        return True
       
    def _副本内检查钩子(self) -> str | None:
        截图 = self.线程.截图
        if 截图 is None:
            截图= self.线程.刷新截图()
        if 截图 is None:
            return None
        filter_config = {               
                "color_diff": "5-80,255,80,255,80,255",
                "keep_color": True,
                "background": "black"
            }
        副本内剩余能量文字=self.线程.文字识别器.recognize_text(截图,self.游戏配置.区域.神界大陆.神界秘境副本剩余体力值标签.元组,filter_config)
        if 匹配分组关键字(副本内剩余能量文字, f"/"):
            文字=副本内剩余能量文字.split("/")[0]
            调试器.debug(self.调试分类, f"副本内检查钩子: 读取神界秘境副本剩余体力值{文字}")
            if len(文字) == 1:
                次数=提取次数(文字)
                self.任务状态.剩余次数=次数                
                调试器.debug(self.调试分类, f"剩余次数: {次数}")
                if self.任务状态.剩余次数 <= 0:                    
                    调试器.state(self.调试分类, f"剩余次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
                    self.退出副本()
                    return "任务完成"                    
        return None