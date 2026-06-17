# tasks/reward/dajinbaoku.py
from tasks.reward.base import 强化奖励任务基类
from core.debug import 调试器
import time,random

class 打金宝库(强化奖励任务基类):
    任务ID = "dajinbaoku"
    任务名称 = "打金宝库"  
    任务类型: str = "每日任务"
    剩余次数: int = 1
    是否启用: bool = True  
    最小间隔秒 = 300
    最大间隔秒 = 600
    
    def 执行(self) -> bool:
        调试器.debug("强化奖励", "打金宝库: 开始检查")
        self.页面.主界面操作.展开右上角任务帘
        if not self.页面.创建_通用点击图片验证文字切换 (
            self.配置.区域.主界面.第一排任务区域标签.元组, 
            "打金宝库图标.bmp",
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "打|金"
            ).执行():
            self.下次执行时间 = time.time() + random.randint(180, 600)
            调试器.debug("强化奖励", "打金宝库: 获取金宝库失败")
            return False
        次数=self.辅助识别器.获取区域次数(self.配置.区域.日常强化.打金宝库剩余次数区域标签.元组,规则="/")
        if 次数 is None:
            self.下次执行时间 = time.time() + random.randint(180, 600)
            调试器.debug("强化奖励", "打金宝库: 获取次数失败")
            return True
        if 次数==0:
            self.上次确定任务结束时间 = time.time()
            self.管理器.保存配置()
            调试器.debug("强化奖励", "打金宝库: 获取次数为0")
            return True
        for i in range(30):        
            if not self.页面.创建寻图偏移点击操作(
                self.配置.区域.日常强化.打金宝库回收框红点区域标签.元组,
                "红点1.bmp",
                (-60,15,-10,25)
                ).执行():
                time.sleep(self.配置.默认等待秒)
                self.辅助识别器.线程.刷新截图()
                次数=self.辅助识别器.获取区域次数(self.配置.区域.日常强化.打金宝库剩余次数区域标签.元组,规则="/")
                if 次数 is None:               
                    continue
                if 次数==0:
                    self.上次确定任务结束时间 = time.time()
                    self.管理器.保存配置()
                    调试器.debug("强化奖励", "打金宝库收益: 获取次数为0")
                    return True
                break
            time.sleep(self.配置.默认等待秒)
            self.辅助识别器.线程.刷新截图()
            提取区域= self.辅助识别器.查找图片单结果(self.配置.区域.日常强化.打金宝库回收不再提示区域标签.元组,"不在提醒中间.bmp")
            if 提取区域 is not None:
                self.通用操作.点击区域(提取区域,缩放比例=0.3)
                self.页面.创建_通用点击文字验证文字切换(
                    self.配置.区域.日常强化.打金宝库回收不再提示关闭按钮标签.元组,
                    "确|定",
                    self.配置.区域.日常强化.打金宝库回收不再提示关闭按钮标签.元组,
                    "确|定",
                    False         
                ).执行()
                self.通用操作.覆盖鼠标提示到边缘()
                time.sleep(self.配置.默认等待秒)
                self.辅助识别器.线程.刷新截图()                    
        return True