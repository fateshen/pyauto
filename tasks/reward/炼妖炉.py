# tasks/reward/lianyaolu.py

from core.utils import 缩放区域

from tasks.reward.base import 强化奖励任务基类
from core.debug import 调试器
import time,random
from typing import Tuple,Optional

class 炼妖炉(强化奖励任务基类):
    任务ID = "lianyaolu"
    任务名称 = "炼妖炉"  
    是否启用: bool = True  
    最小间隔秒 = 300
    最大间隔秒 = 600
    
    def 执行(self) -> bool:
        调试器.debug("强化奖励", "炼妖炉: 开始检查")
        if not self.页面.合成强化.进入小菜单带红点(self.配置.区域.主界面.图鉴按钮带红点区域标签.元组,
                                     "图|鉴"
                           ):            
            self.下次执行时间 = time.time() + random.randint(180, 600)
            调试器.debug("强化奖励", "炼妖炉: 进入图鉴失败")
            return False
        图鉴标签= self.辅助识别器.线程.动态标签.图鉴页面右侧标签.图鉴.元组
        图鉴放大标签=缩放区域(图鉴标签,1.6)
        if self.辅助识别器.查找图片单结果(图鉴放大标签,"红点1.bmp"):
            # if self.页面.创建_通用点击区域验证文字切换 (
            #     self.辅助识别器.线程.动态标签.图鉴页面右侧标签.图鉴.元组,
            #     self.配置.区域.主界面.中间页面名称区域标签.元组,
            #     "图|鉴"
            #     ).执行(): 
            for i in range(10):  
                if not self.页面.创建寻图点击原区域操作(
                    self.配置.区域.图鉴强化.图鉴页面激活按钮带红点区域标签.元组,
                    "红点1.bmp",
                    0.3
                ).执行():                  
                    break
                self.页面.线程.刷新截图()
        if not self.页面.创建_通用点击区域验证文字切换 (
            self.辅助识别器.线程.动态标签.图鉴页面右侧标签.炼化.元组,
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "炼|化"
            ).执行():            
            self.下次执行时间 = time.time() + random.randint(180, 600)
            调试器.debug("强化奖励", "炼妖炉: 点击右侧炼化按钮失败")
            return True
        #关闭小页面        
        self.关闭小窗口()
        # 处理右丹炉
        self._炼化单个丹炉(
            self.配置.区域.图鉴强化.炼化丹药右位带红点按钮标签,
            "右丹炉"
        )
        
        # 处理左丹炉
        self._炼化单个丹炉(
            self.配置.区域.图鉴强化.炼化丹药左位带红点按钮标签,
            "左丹炉"
        )

      
        return True
    def 关闭小窗口(self):
        self.页面.创建_通用点击图片验证图片切换(
            self.配置.区域.图鉴强化.炼化丹药关闭按钮区域标签.元组,
            "关闭按钮.bmp",
            self.配置.区域.图鉴强化.炼化丹药关闭按钮区域标签.元组,
            "关闭按钮.bmp",
            False,
            True
        ).执行()

    def _炼化单个丹炉(self, 丹炉按钮标签, 名称: str) -> bool:
        """打开丹炉 → 放入丹药 → 关闭"""
        
        # 1. 打开丹炉页面（带重试）
        if not self._尝试打开丹炉页面(丹炉按钮标签):
            调试器.trace("强化奖励", f"炼化丹药-{名称}: 无法打开")
            return False
        time.sleep(self.配置.默认等待秒)
        self.页面.线程.刷新截图()
        # 2. 放入丹药
        放入区域 = self._查找放入按钮()
        if 放入区域:
            self.通用操作.点击区域(放入区域)
            调试器.trace("强化奖励", f"炼化丹药-{名称}: 已放入")
        
        # 3. 关闭窗口 + 领奖
        self.关闭小窗口()
        self.通用操作.领取奖励退出操作()
        
        return True


    def _尝试打开丹炉页面(self, 丹炉按钮标签) -> bool:
        """尝试打开丹炉页面，失败时先领奖再重试"""
        关闭按钮区域 = self.配置.区域.图鉴强化.炼化丹药关闭按钮区域标签
        
        # 第一次尝试
        if self.页面.创建寻图点击原区域验证图片切换(
            丹炉按钮标签.元组,
            "红点1.bmp",
            关闭按钮区域.元组,
            "关闭按钮.bmp"
        ).执行():
            return True
        
        # 领奖后重试
        if self.通用操作.领取奖励退出操作():
            if self.页面.创建寻图点击原区域验证图片切换(
                丹炉按钮标签.元组,
                "红点1.bmp",
                关闭按钮区域.元组,
                "关闭按钮.bmp"
            ).执行():
                return True
        
        return False


    def _查找放入按钮(self) -> Optional[Tuple[int, int, int, int]]:
        """在放入文字群中查找'放入'按钮坐标"""
        文字区域 = self.辅助识别器.获取区域文字坐标(
            self.配置.区域.图鉴强化.炼化丹药放入文字群标签.元组
        )
        if not 文字区域:
            return None
        
        return 文字区域.find("放|入")