# tasks/reward/qunxingshengdian.py
from tasks.reward.base import 强化奖励任务基类
from core.debug import 调试器
import time,random
from core.utils import 缩放区域

class 群星圣殿升级(强化奖励任务基类):
    任务ID = "qunxingshengdian"
    任务名称 = "群星圣殿"  
    是否启用: bool = True  
    最小间隔秒 = 6000
    最大间隔秒 =8000
    使用星魂令=True
    星魂升级=True
    专属卡牌升级=True
    
    def 执行(self) -> bool:
        调试器.debug("强化奖励", "群星圣殿: 开始检查")
        if not self.打开群星圣殿页面():
            return False
        self._使用群星令()
        self._星魂升级()
        self._专属卡牌升级()
      
        return True
    def _星魂升级(self):
        if not self.星魂升级:
            return 
        右侧卡区域 = self.配置.区域.战场光翼图鉴页面右侧坐标池.位置2.元组
        if not self.辅助识别器.查找图片单结果(缩放区域(右侧卡区域, 1.6), "红点1.bmp"):
            调试器.debug("群星圣殿升级", "星魂升级：无红点，跳过")
            return
        if not self.页面.创建_通用点击区域验证文字切换(
            右侧卡区域,
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "星|魂"
        ).执行():
            调试器.debug("群星圣殿升级", "进入星魂页面失败")
            return
        for _ in range(10):
            if not self.页面.创建寻图偏移点击操作(
                self.配置.区域.群星圣域.星魂升级页面五行标头区域标签.元组,
                "红点1.bmp",
                (-50,5,-5,45)
            ).执行():
                return
            self.通用操作.点击区域(self.配置.区域.群星圣域.星魂升级页面升级按钮标签.元组)
            time.sleep( self.配置.默认等待秒)
            self.页面.线程.刷新截图()
    def _专属卡牌升级(self):
        if not self.专属卡牌升级:
            return
        右侧卡区域 = self.配置.区域.战场光翼图鉴页面右侧坐标池.位置3.元组
        if not self.辅助识别器.查找图片单结果(缩放区域(右侧卡区域, 1.6), "红点1.bmp"):
            调试器.debug("群星圣殿升级", "星魂卡牌升级：无红点，跳过")
            return
        if not self.页面.创建_通用点击区域验证文字切换(
            右侧卡区域,
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "专|属"
        ).执行():
            调试器.debug("群星圣殿升级", "进入星魂专属页面失败")
            return
        for _ in range(5):
            if not self.页面.创建寻图偏移点击操作(
                self.配置.区域.群星圣域.星魂升级页面五行标头区域标签.元组,
                "红点1.bmp",
                (-50,5,-5,45)
            ).执行():
                return
            for _ in range(5):
                time.sleep(self.配置.默认等待秒)
                self.页面.线程.刷新截图()
                if not self.页面.创建寻图偏移点击操作(
                    self.配置.区域.群星圣域.星魂专属页面左侧卡牌红点搜索区域标签.元组,
                    "红点1.bmp",
                    (-50,5,-5,45)
                ).执行():
                    break
                for _ in range(3):     
                    time.sleep(self.配置.默认等待秒)               
                    if not self.页面.创建寻图偏移点击验证文字切换(
                        self.配置.区域.群星圣域.星魂专属页面中间卡牌红点搜索区域标签.元组,
                        "红点1.bmp",
                        (-50,5,-5,45),
                        self.配置.区域.群星圣域.星魂专属页面升级窗口升级按钮标签.元组,
                        "升|级"
                    ).执行():
                        break
                    self.通用操作.点击区域(self.配置.区域.群星圣域.星魂专属页面升级窗口升级按钮标签.元组)
                    time.sleep(self.配置.默认等待秒)
                    self.页面.创建_通用点击图片验证图片切换(
                        self.配置.区域.群星圣域.星魂专属页面升级窗口关闭按钮区域标签.元组,
                        "关闭按钮.bmp",
                        self.配置.区域.群星圣域.星魂专属页面升级窗口关闭按钮区域标签.元组,
                        "关闭按钮.bmp",
                        False
                    ).执行()




            
    def _使用群星令(self):
        if not self.使用星魂令:
            return
        filter_config = {
                "color_range": "0,20,120,255,0,16",  
                "keep_color": True,
                "background": "black"
            }
        for _ in range(5):
            数量=self.辅助识别器.获取区域次数(self.配置.区域.群星圣域.群星圣殿页面十连群星令数量标签.元组,filter_config)
            if 数量 is None:
                return
            if 数量<10:
                return
            if not self.页面.创建_通用点击图片验证图片切换(
                self.配置.区域.群星圣域.群星圣殿页面不显示奖励界面按钮标签.元组,
                "不在提醒中间.bmp",
                self.配置.区域.群星圣域.群星圣殿页面不显示奖励界面按钮标签.元组,
                "不在提醒中间.bmp",
                False,
                True
            ).执行():
                continue
            self.通用操作.点击区域(self.配置.区域.群星圣域.群星圣殿页面十连按钮标签.元组)
            time.sleep( self.配置.默认等待秒)
            self.页面.线程.刷新截图()
            
 
    def 打开群星圣殿页面(self) -> bool:        
        
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug("群星圣殿升级", "展开右上角任务帘失败")
            return False

        if not self.页面.群星圣域.进入群星圣域页面():    
            调试器.debug("群星圣殿升级", "进入大千世界页面失败")
            return False
        else:
            # 等待刷新，页面独有措施
            time.sleep(1.5)
            self.页面.线程.刷新截图()
            time.sleep(1.5)
            self.页面.线程.刷新截图()
        
        if not self.页面.创建_通用点击区域验证文字切换(
            self.配置.区域.群星圣域.群星圣域页面群星圣殿进入标签.元组,
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "圣殿"
        ).执行():       
            调试器.debug("群星圣殿升级", "进入群星圣殿页面失败")
            return False     
       
        调试器.state("群星圣殿升级", "已进入群星圣殿页面")
        return True