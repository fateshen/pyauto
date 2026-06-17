# tasks/reward/huodong.py


from core.recognition import OCRResult
from core.utils import 缩放区域,匹配分组关键字,是否有重叠,提取次数
from typing import List, Tuple
from tasks.reward.base import 强化奖励任务基类
from core.debug import 调试器
import time,random

class 活动系列强化(强化奖励任务基类):
    任务ID = "huodong"
    任务名称 = "活动系列强化"  
    是否启用: bool = True  
    最小间隔秒 = 3000
    最大间隔秒 = 6000
    灵符特惠购买节日特殊奖励=True
    
    def 执行(self) -> bool:
        调试器.debug("强化奖励", "活动页面系列强化: 开始检查")               
        if not self.页面.创建_通用点击图片验证文字切换(
            self.配置.区域.主界面.第一排任务区域标签.元组,
            "活动图标.bmp",
             self.配置.区域.主界面.中间页面名称区域标签.元组,
             "开服|活动",
        ).执行():
            return False
        #=========这里面写开服活动相关，暂时空缺待补充

            
        图片坐标=self.辅助识别器.查找图片多结果(self.配置.区域.各种活动.开服活动右侧小标签红点检查区域.元组,"红点1.bmp")
        if 图片坐标:
            for 坐标 in 图片坐标: 
                校正坐标=坐标[0]-15,坐标[1]+15,坐标[0]+3,坐标[1]+45
                self.通用操作.点击区域(校正坐标,2)
                time.sleep(self.配置.默认等待秒*2)
                self.页面.线程.刷新截图()
                表头文字=self.辅助识别器.获取区域文字(self.配置.区域.主界面.中间页面名称区域标签.元组)
                if 匹配分组关键字(表头文字,"祈|愿"):
                    左侧菜单=self.辅助识别器.获取区域文字坐标(self.配置.区域.合成.合成左分类卡区域标签.元组)
                    if 左侧菜单 is None:
                        continue
                    怪物试炼按钮区域=左侧菜单.find("怪物试炼")  
                    if 怪物试炼按钮区域 is not None:
                        if self.页面.创建_通用点击区域验证文字切换(
                            怪物试炼按钮区域,
                            self.配置.区域.各种活动.怪物试炼活动倒计时文字区域.元组,
                            "活|动"

                        ) .执行():
                            for _ in range(10):
                                if self.辅助识别器.区域包含文字(self.配置.区域.各种活动.怪物试炼活动领取奖励按钮区域.元组,"已|己"):
                                    break
                                if not self.页面.创建点击文字操作(self.配置.区域.各种活动.怪物试炼活动领取奖励按钮区域.元组,"奖|励").执行():
                                    break
                                time.sleep(self.配置.默认等待秒)
                                self.页面.线程.刷新截图()

        self.通用操作.关闭中间可能存在的窗口()
        self._各种节日检查()
        return True
    
    def _各种节日检查(self):
        调试器.debug("强化奖励", "各种节日检查: 启动")
        if self.页面.创建寻图偏移点击验证文字切换(
            self.配置.区域.各种活动.左上角活动检查区域.元组,
            "红点1.bmp",
            (-30, 10, -5, 30),
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "开|服|活动",           
        ).执行():
            文字集合=self.辅助识别器.获取区域文字坐标(self.配置.区域.合成.合成左分类卡区域标签.元组)
            图标集合=self.辅助识别器.查找图片多结果(self.配置.区域.合成.合成左分类卡区域标签.元组,"红点1.bmp")

            if self.灵符特惠购买节日特殊奖励:
                if self._激活可用标签(文字集合,图标集合,标题规则="特惠"):
                    self._灵符特惠()                    
            if self._激活可用标签(文字集合,图标集合,标题规则="试炼"):
                self._节日试炼()
            if self._激活可用标签(文字集合,图标集合,标题规则="福利"):
                self._节日福利()
            


    def _激活可用标签(self,文字集合:OCRResult,图标集合:List[Tuple[int, int,int, int]],标题规则:str)->bool:
        文字区域=文字集合.find(标题规则)
        if 文字区域 is None: return False
        if 是否有重叠(文字区域,图标集合):
            self.通用操作.点击区域(文字区域,2)
            time.sleep(self.配置.默认等待秒)
            self.页面.线程.刷新截图()
            return True
        return False
    
    def _节日试炼(self):
        for _ in range(10):
            if not self.页面.创建寻图点击原区域操作(
                self.配置.区域.各种活动.节日试炼积分领取按钮区域.元组,
                "红点1.bmp",                   
            ).执行():
                break
            time.sleep(self.配置.默认等待秒)
            self.页面.线程.刷新截图()
        for _ in range(10):
            if not self.页面.创建寻图偏移点击操作(
                self.配置.区域.各种活动.节日试炼积分奖励红点搜寻区域.元组,
                "红点1.bmp",  
                (-30, 5, -5, 30)                 
            ).执行():
                break
            time.sleep(self.配置.默认等待秒)
            self.页面.线程.刷新截图()

    def _节日福利(self):
        for _ in range(5):
            if not self.页面.创建点击文字操作(
                self.配置.区域.各种活动.节日福利领取奖励按钮区域.元组,
                "奖|励",                   
            ).执行():
                break
            time.sleep(self.配置.默认等待秒)
            self.页面.线程.刷新截图()

    def _灵符特惠(self):
        for _ in range(5):
            灵符按钮信息=self.辅助识别器.获取区域文字(self.配置.区域.各种活动.灵符特惠购买按钮区域.元组)
            特惠礼包信息=self.辅助识别器.获取区域文字(self.配置.区域.各种活动.灵符特惠礼包信息区域.元组)
            if 灵符按钮信息 is None or 特惠礼包信息 is None: continue
            灵符数=提取次数(灵符按钮信息)
            礼包数=提取次数(特惠礼包信息)
            if 灵符数>=328: break
            if 灵符数>0 and 礼包数>0:
                if (灵符数==18 and 礼包数<=6 ) or (灵符数==38 and 礼包数<=12) or (灵符数==198 and 礼包数<=40) or (灵符数==68 and 礼包数<=18 ) or (灵符数==98 and 礼包数<=24):
                    self.通用操作.点击区域(self.配置.区域.各种活动.灵符特惠购买按钮区域.元组,1)
                    time.sleep(self.配置.默认等待秒)
                    self.页面.线程.刷新截图()
                else:
                    break



            
           

   
           

         

      
