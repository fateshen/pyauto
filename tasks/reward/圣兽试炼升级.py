# tasks/reward/shengshoushilianshengji.py
from tasks.reward.base import 强化奖励任务基类
from core.debug import 调试器
import time,random
from core.utils import 缩放区域

class 圣兽试炼升级(强化奖励任务基类):
    任务ID = "shengshoushilianshengji"
    任务名称 = "圣兽试炼升级"  
    是否启用: bool = True  
    最小间隔秒 = 3000
    最大间隔秒 =6000
   
    
    def 执行(self) -> bool:
        调试器.debug("强化奖励", "圣兽血脉: 开始检查")
        if not self.打开圣兽血脉页面():
            return False        
        self._血脉升级()
       
      
        return True
    def _血脉升级(self):

        右侧卡区域 = self.配置.区域.战场光翼图鉴页面右侧坐标池.位置3.元组
        if not self.辅助识别器.查找图片单结果(缩放区域(右侧卡区域, 1.6), "红点1.bmp"):
            调试器.debug("圣兽试炼升级", "血脉升级：无红点，跳过")
            return
        if not self.页面.创建_通用点击区域验证文字切换(
            右侧卡区域,
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "血|脉"
        ).执行():
            调试器.debug("圣兽试炼升级", "进血脉页面失败")
            return
        for _ in range(10):
            if not self.页面.创建寻图偏移点击操作(
                self.配置.区域.圣兽试炼.圣兽血脉上部小标题页面标签.元组,
                "红点1.bmp",
                (-50,5,-5,25)
            ).执行():
                return
            self.通用操作.点击区域(self.配置.区域.圣兽试炼.圣兽血脉升级按钮标签.元组)
            time.sleep( self.配置.默认等待秒)
            self.页面.线程.刷新截图()
    def 打开圣兽血脉页面(self) -> bool:       
        
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug("圣兽试炼升级",  "展开右上角任务帘失败")
            return False

        if not self.页面.大千世界.进入大千世界页面():    
            调试器.debug("圣兽试炼升级",  "进入大千世界页面失败")
            return False
        

        if not self.页面.大千世界.圣兽页面.进入圣兽试炼任务页面():    
            调试器.debug("圣兽试炼升级",  "进入圣兽试炼任务页面失败")
            return False        
       
        调试器.state("圣兽试炼升级", "已进入圣兽试炼页面")
        return True   