# tasks/reward/hechengxilie.py
from re import S

from core.utils import 缩放区域

from tasks.reward.base import 强化奖励任务基类
from core.debug import 调试器
import time,random

class 合成系列强化(强化奖励任务基类):
    任务ID = "hechengxilie"
    任务名称 = "合成系列强化"  
    是否启用: bool = True  
    最小间隔秒 = 300
    最大间隔秒 = 600
    点击熔炼=False
    合成所见装备=False
    锻造所见装备=False
    
    def 执行(self) -> bool:
        调试器.debug("强化奖励", "合成系列强化: 开始检查")               
        if not self.页面.合成强化.进入小菜单带红点(self.配置.区域.主界面.合成按钮带红点区域标签.元组,
                                        "合|成"
                            ):            
            self.下次执行时间 = time.time() + random.randint(180, 600)
            调试器.debug("强化奖励", "合成系列强化: 进入合成失败")
            return False
      
        # 按顺序处理各模块
        self._熔炼装备()
        self._合成所见装备()
        self._锻造所见装备()        
        return True

    def _熔炼装备(self):
        if not self.点击熔炼:
            return
        右侧卡区域 = self.辅助识别器.线程.动态标签.合成页面右侧标签.熔炼.元组        
        if not self.页面.创建_通用点击区域验证文字切换(
            右侧卡区域,
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "熔|炼"
         ).执行():
            return 
        time.sleep(self.配置.默认等待秒)
        self.通用操作.点击区域(self.配置.区域.合成.熔炼页面熔炼按钮标签.元组,2)

    def _合成所见装备(self):
        if not self.合成所见装备:
            return
        右侧卡区域 = self.辅助识别器.线程.动态标签.合成页面右侧标签.合成.元组        
        if not self.页面.创建_通用点击区域验证文字切换(
            右侧卡区域,
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "成",
            True,
            True
         ).执行():
            return 
        time.sleep(max(0.5, self.配置.刷新等待秒))
        self.页面.线程.刷新截图()
        标签文字信息=self.辅助识别器.获取区域文字坐标(self.配置.区域.合成.合成左分类卡区域标签.元组)
        if 标签文字信息 is None:
            return
        二星标签区域=标签文字信息.find("二")
        三星标签区域=标签文字信息.find("三")
        if 二星标签区域 is None or 三星标签区域 is None:
            return
        idx=0
        count=0
        while idx<3:
            count+=1
            self.通用操作.点击区域(二星标签区域)
            time.sleep(self.配置.默认等待秒)
            self.页面.线程.刷新截图()
            if not self.页面.创建寻图点击原区域操作(
                self.配置.区域.合成.合成打造含红点区域标签.元组,
                "红点1.bmp",
                0.3
            ).执行():
                idx+=1
            else:
                idx=0
            self.通用操作.点击区域(三星标签区域)
            time.sleep(self.配置.默认等待秒)
            self.页面.线程.刷新截图()
            if not self.页面.创建寻图点击原区域操作(
                self.配置.区域.合成.合成打造含红点区域标签.元组,
                "红点1.bmp",
                0.3
            ).执行():
                idx+=1
            else:
                idx=0
            if count==30 :idx=30
    def _锻造所见装备(self):
        if not self.锻造所见装备:
            return
        右侧卡区域 = self.辅助识别器.线程.动态标签.合成页面右侧标签.锻造.元组        
        if not self.页面.创建_通用点击区域验证文字切换(
            右侧卡区域,
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "锻|造",
            True
         ).执行():
            return 
        time.sleep(max(0.5, self.配置.刷新等待秒))
        self.页面.线程.刷新截图()
        
        熔炼标签=self.辅助识别器.线程.动态标签.合成页面右侧标签.熔炼.元组   
      
        if 熔炼标签 is None :
            return
        idx=0
        count=0
        while idx<2:
            count+=1
           
            if not self.页面.创建寻图点击原区域操作(
                self.配置.区域.合成.锻造页面打造按钮含红点标签.元组,
                "红点1.bmp",
                0.3
            ).执行():
                idx+=1
            else:
                idx=0
            self.通用操作.点击区域(熔炼标签)     
            self.页面.创建_通用点击区域验证文字切换(
            右侧卡区域,
            self.配置.区域.主界面.中间页面名称区域标签.元组,
                "锻|造",
                True
                ).执行()
            time.sleep(self.配置.默认等待秒)
            self.页面.线程.刷新截图()
            if count==20 :idx=30
           

         

      
