# tasks/reward/xukongjianjieshengji.py
from tasks.reward.base import 强化奖励任务基类
from core.debug import 调试器
import time,random
from core.utils import 缩放区域

class 虚空剑界升级(强化奖励任务基类):
    任务ID = "xukongjianjieshengji"
    任务名称 = "虚空剑界升级"  
    是否启用: bool = True  
    最小间隔秒 = 3000
    最大间隔秒 =6000
   
    
    def 执行(self) -> bool:
        调试器.debug("强化奖励", "虚空剑界: 开始检查")
        if not self.打开虚空剑界页面():
            return False    
        self._飞剑升级()    
        self._剑意升级()
       
      
        return True
    def _剑意升级(self):

        右侧卡区域 = self.配置.区域.战场光翼图鉴页面右侧坐标池.位置3.元组
        if not self.辅助识别器.查找图片单结果(缩放区域(右侧卡区域, 1.6), "红点1.bmp"):
            调试器.debug("虚空剑界升级", "剑意升级升级：无红点，跳过")
            return
        if not self.页面.创建_通用点击区域验证文字切换(
            右侧卡区域,
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "意"
        ).执行():
            调试器.debug("虚空剑界升级", "进剑意页面失败")
            return
        for _ in range(10):
            if not self.页面.创建寻图点击原区域验证图片切换(
                self.配置.区域.虚空剑界.虚空剑意页面升级按钮带红点区域标签.元组,
                "红点1.bmp",
                self.配置.区域.虚空剑界.虚空剑意页面升级按钮带红点区域标签.元组,
                "红点1.bmp",
                0.3
            ).执行():
                return
    def _飞剑升级(self):

        右侧卡区域 = self.配置.区域.战场光翼图鉴页面右侧坐标池.位置2.元组
        if not self.辅助识别器.查找图片单结果(缩放区域(右侧卡区域, 1.6), "红点1.bmp"):
            调试器.debug("虚空剑界升级", "飞剑升级：无红点，跳过")
            return
        if not self.页面.创建_通用点击区域验证文字切换(
            右侧卡区域,
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "飞"
        ).执行():
            调试器.debug("虚空剑界升级", "进入飞剑页面失败")
            return
        for _ in range(10):
            self.页面.创建_通用点击图片验证图片切换(
                self.配置.区域.虚空剑界.虚空飞剑页面小页面关闭按钮区域标签.元组,
                "关闭按钮.bmp",
                self.配置.区域.虚空剑界.虚空飞剑页面小页面关闭按钮区域标签.元组,
                "关闭按钮.bmp",
                False,
            ).执行()
            if not self.页面.创建寻图偏移点击验证图片切换(
                self.配置.区域.虚空剑界.虚空飞剑页面红点搜索区域标签.元组,
                "红点1.bmp",
                (0,20,10,50),
                self.配置.区域.虚空剑界.虚空飞剑页面小页面关闭按钮区域标签.元组,
                "关闭按钮.bmp",
            ).执行():
               调试器.debug("虚空剑界升级", "虚空飞剑升级：无红点，跳过")
               return
            self.通用操作.点击区域(self.配置.区域.虚空剑界.虚空飞剑页面激活按钮标签.元组)
            time.sleep(self.配置.默认等待秒)
                
           
    def 打开虚空剑界页面(self) -> bool:       
        
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug("虚空剑界升级",  "展开右上角任务帘失败")
            return False

        if not self.页面.大千世界.进入大千世界页面():    
            调试器.debug("虚空剑界升级",  "进入大千世界页面失败")
            return False
        

        if not self.页面.大千世界.虚空剑界.进入虚空剑界任务页面():    
            调试器.debug("虚空剑界升级","进入虚空剑界任务页面失败")
            return False   
       
        调试器.state("虚空剑界升级", "已进入虚空剑界页面")
        return True   