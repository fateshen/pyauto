# tasks/reward/fentianhuolian.py
from tasks.reward.base import 强化奖励任务基类
from core.debug import 调试器
import time,random
from core.utils import 缩放区域

class 焚天火莲升级(强化奖励任务基类):
    任务ID = "fentianhuolian"
    任务名称 = "焚天火莲升级"  
    是否启用: bool = True  
    最小间隔秒 = 3000
    最大间隔秒 =6000
   
    
    def 执行(self) -> bool:
        调试器.debug("强化奖励", "圣兽血脉: 开始检查")
        if not self.打开焚天炎域页面():
            return False        
        self._火莲升级()
       
      
        return True
    def _火莲升级(self):

        右侧卡区域 = self.配置.区域.首领合成页面右侧标签坐标池.位置3.元组
        if not self.辅助识别器.查找图片单结果(缩放区域(右侧卡区域, 1.6), "红点1.bmp"):
            调试器.debug("焚天火莲升级", "火莲升级：无红点，跳过")
            return
        if not self.页面.创建_通用点击区域验证文字切换(
            右侧卡区域,
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "火莲"
        ).执行():
            调试器.debug("焚天火莲升级", "进火莲页面失败")
            return
        for _ in range(10):
            if not self.页面.创建寻图点击原区域操作(
                self.配置.区域.焚天炎域.焚天火莲页面提升按钮带红点区域.元组,
                "红点1.bmp",               
            ).执行():
                return            
            time.sleep( self.配置.默认等待秒)
            self.页面.线程.刷新截图()
    def 打开焚天炎域页面(self) -> bool:       
        
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug("焚天火莲升级",  "展开右上角任务帘失败")
            return False

        if not self.页面.创建_通用点击图片验证文字切换( 
            self.配置.区域.主界面.第二三排任务区域标签.元组,
            "焚天炎域图标.bmp",
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "炎域",
            True,   ).执行():    
            调试器.debug("焚天火莲升级", "进入焚天炎域任务页面失败")
            return False
       
        调试器.state("焚天火莲升级", "已进入焚天炎域页面")
        return True   