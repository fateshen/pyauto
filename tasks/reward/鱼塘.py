# tasks/reward/tujian.py
from tasks.reward.base import 强化奖励任务基类
from core.debug import 调试器
import time,random

class 鱼塘(强化奖励任务基类):
    任务ID = "yutang"
    任务名称 = "鱼塘"  
    是否启用: bool = True  
    最小间隔秒 = 300
    最大间隔秒 = 600
    
    def 执行(self) -> bool:
        调试器.debug("强化奖励", "收鱼塘: 开始检查")
        if not self.页面.创建_通用点击区域验证文字切换 (
            self.配置.区域.鱼塘.主页面鱼塘区域.元组, 
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "鱼|塘"
            ).执行():
            self.下次执行时间 = time.time() + random.randint(180, 600)
            调试器.debug("强化奖励", "收鱼塘: 获取鱼塘失败")
            return False
        if  self.页面.创建_通用点击区域验证文字切换 (
            self.配置.区域.鱼塘.鱼塘一件售卖按钮区域.元组, 
            self.配置.区域.鱼塘.鱼塘售卖确定区域.元组,
            "确|定"
            ).执行():
            调试器.debug("强化奖励", "收鱼塘: 获取鱼塘成功")             
        return True