# tasks/reward/xunbaozhongshenka.py
from tasks.reward.base import 强化奖励任务基类
from core.debug import 调试器
import time,random

class 寻宝终身卡(强化奖励任务基类):
    任务ID = "xunbaozhongshenka"
    任务名称 = "寻宝终身卡"  
    任务类型: str = "每日任务"   
    是否启用: bool = True  
    最小间隔秒 = 300
    最大间隔秒 = 600
    
    def 执行(self) -> bool:
        调试器.debug("强化奖励", "寻宝终身卡: 开始检查")
        self.页面.主界面操作.展开右上角任务帘
        if not self.页面.创建_通用点击图片验证文字切换 (
            self.配置.区域.主界面.第二三排任务区域标签.元组, 
            "本服顶赞图标.bmp",
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "赞|助"
            ).执行():
            self.下次执行时间 = time.time() + random.randint(180, 600)
            调试器.debug("强化奖励", "寻宝终身卡: 获取图标失败")
            return False
        已完成=False
        if self.页面.创建_通用点击区域验证文字切换(
            self.配置.区域.神界战灵坐骑古剑页面右侧坐标池.位置2.元组,           
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "终|身|卡"
        ).执行():
            for _ in range(5): 
                if not self.页面.创建寻图偏移点击操作(
                     self.配置.区域.日常强化.寻宝终身卡奖励红点范围区域.元组,
                    "红点1.bmp",
                    (-50, 15, -20, 25)
                ).执行():
                    调试器.debug("强化奖励", "寻宝终身卡: 获取图标失败")
                    self.上次确定任务结束时间= time.time()
                    已完成= True
                    break
        if 已完成:
            self.管理器.保存配置()
                                
        return True