# tasks/shengshoubaoku.py
"""
圣兽宝库任务定义
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
    任务ID="shengshoubaoku",
    任务名称="圣兽宝库",
    调试模式=True,
    任务类型="每日任务",
    优先级=4,    
    地图关键字="圣兽宝库|圣,宝库|圣兽,库", 
    工作时间开始=0,    
    提前进场秒数=0,
    次数刷新区间条件="星期6,7",
    执行日期规则="星期6,7",
)
class 圣兽宝库任务(战斗任务执行器):
    """圣兽宝库任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
   
    def 执行入口逻辑(self) -> bool:
        """执行圣兽宝库入口逻辑"""
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
        
        if not self.页面.大千世界.圣兽页面.进入圣兽试炼任务页面():    
            调试器.debug(self.调试分类, "进入圣兽试炼任务页面失败")
            return False
        
        if not self.页面.大千世界.圣兽页面.进入圣兽宝库页面():    
            调试器.debug(self.调试分类, "进入圣兽宝库页面失败")
            return False
        
        # 等待刷新时间，强制等待服务器时间同步
        time.sleep(max(0.5, self.游戏配置.刷新等待秒))
        self.线程.刷新截图()

        # 3. 更新剩余次数
        filter_config = {
                "color_diff": "5-80,255,80,255,80,255",               
                "keep_color": False,
                "background": "black"
            }
        调试器.debug(self.调试分类, "步骤2: 读取圣兽宝库次数")

        次数=self.辅助识别器.获取区域次数(self.游戏配置.区域.圣兽宝库.圣兽宝库页面积分标签.元组,filter_config,f"/")
        if 次数 is None:
            调试器.warning(self.调试分类, "读取圣兽宝库次数失败，入口逻辑中断")
            return False
        调试器.debug(self.调试分类, f"剩余次数: {次数}")

        # 4. 再次检查次数
        if 次数 >= 800:
            if self._圣兽宝库页面领取奖励成功():

                #记住将宝库深处设置为可用，这里增加领取奖励设置，然后调整次数                
                圣兽试炼状态=self.线程.获取任务状态_按名称("圣兽试炼")
                
                if 圣兽试炼状态 is not None:
                    圣兽试炼状态.剩余次数=3
                宝库深处配置=self.线程.获取任务配置("宝库深处")
                import datetime
                if 宝库深处配置 is not None:
                    宝库深处配置.圣兽宝库完成时间=datetime.date.today().isoformat()
                self.任务状态.剩余次数= 0
            调试器.state(self.调试分类, f"读取次数后确认为0，次数已用完")
            return False
        

        # 5. 点击进入副本  
        调试器.debug(self.调试分类, "步骤5: 点击进入圣兽宝库副本")
        if not self.页面.大千世界.圣兽页面.进入圣兽宝库副本():
            调试器.error(self.调试分类, "点击挑战按钮失败，入口逻辑中断")
            return False

        调试器.state(self.调试分类, "入口逻辑执行成功，已进入圣兽宝库副本")
        return True
       
    # def _副本内检查钩子(self) -> str | None:
    #     截图 = self.线程.截图
    #     if 截图 is None:
    #         截图= self.线程.刷新截图()
    #     if 截图 is None:
    #         return None
    #     filter_config = {               
    #             "color_diff": "5-80,255,80,255,80,255",
    #             "keep_color": True,
    #             "background": "black"
    #         }
    #     副本内剩余能量文字=self.线程.文字识别器.recognize_text(截图,self.游戏配置.区域.神界大陆.圣兽宝库副本剩余体力值标签.元组,filter_config)
    #     if 匹配分组关键字(副本内剩余能量文字, f"/"):
    #         文字=副本内剩余能量文字.split("/")[0]
    #         调试器.debug(self.调试分类, f"副本内检查钩子: 读取圣兽宝库副本剩余体力值{文字}")
    #         if len(文字) == 1:
    #             次数=提取次数(文字)
    #             self.任务状态.剩余次数=次数                
    #             调试器.debug(self.调试分类, f"剩余次数: {次数}")
    #             if self.任务状态.剩余次数 <= 0:                    
    #                 调试器.state(self.调试分类, f"剩余次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
    #                 self.退出副本()
    #                 return "任务完成"                    
    #     return None

    def _圣兽宝库页面领取奖励成功(self) -> bool:
         
        # if not self.辅助识别器.查找图片单结果(self.游戏配置.区域.圣兽宝库.圣兽宝库页面积分奖励标签.元组,"红点1.bmp"):
        #     return False
        
        if not self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.圣兽宝库.圣兽宝库页面积分奖励标签.元组, 
            self.游戏配置.区域.圣兽宝库.圣兽宝库页面积分奖励面板标头文字标签.元组, 
            "积|分", 
            True,
        ).执行():            
            调试器.debug(self.调试分类, "未能进入圣兽宝库页面积分奖励面板")
            return False
        
        截图 = self.线程.截图
        if 截图 is None:
            截图= self.线程.刷新截图()
        if 截图 is None:
            return False
        ocr_result = self.线程.文字识别器.recognize_result(截图, self.游戏配置.区域.圣兽宝库.圣兽宝库页面积分奖励面板领取按钮区域标签.元组)
        领取按钮列表 = ocr_result.find("领取", return_all=True)
        已领取=ocr_result.find("已|己", return_all=True)
        if 已领取:            
            if len(已领取)==5:                
                return True
        count=0
        if 领取按钮列表:
            for 区域 in 领取按钮列表:
                if  self.页面.创建_通用点击区域验证文字切换(
                        区域,
                        缩放区域(区域,2),
                        "已|己",
                        True,   # 切换后文字存在
                        False   # 不先验证
                    ).执行():
                    count+=1
        if count>0:
            return True
        return False