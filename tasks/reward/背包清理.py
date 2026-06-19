# tasks/reward/dajinbaoku.py


from tasks.reward.base import 强化奖励任务基类
from core.debug import 调试器
import time,random

class 背包清理(强化奖励任务基类):
    任务ID = "beibaoqingli"
    任务名称 = "背包清理"  
    剩余次数: int = 1
    是否启用: bool = True  
    在盟重省执行: bool = True
    最小间隔秒 = 3000
    最大间隔秒 = 6000
    
    def 执行(self) -> bool:
        self.通用操作.清理页面状态()
        定位坐标=self.通用操作._打开背包()  

        if 定位坐标 is None:
            调试器.debug("强化奖励", "背包清理: 打开背包失败")
            return True
        格子坐标集合=self.通用操作._生成背包格子区域(定位坐标)
        分页按钮标签=self.通用操作._生成背包翻页标签区域(定位坐标)
        图片集合=("丹药1.bmp", "丹药2.bmp", "丹药3.bmp", "丹药4.bmp","丹药5.bmp", 
              "丹药6.bmp",  "丹药7.bmp", "丹药8.bmp","丹药9.bmp", "丹药10.bmp","丹药11.bmp",
             "宝箱1.bmp",  "宝箱2.bmp","宝箱3.bmp",  "宝箱4.bmp","宝箱5.bmp",  "宝箱6.bmp",
             "宝箱7.bmp",  "宝箱8.bmp"           
        )
        背包区域=定位坐标[0]+11,定位坐标[1]-400,定位坐标[0]+523,定位坐标[1]-16
        右键不可用=False
        检查1次=False
        for 分页标签 in 分页按钮标签:
            self.通用操作.点击区域(分页标签,2,缩放比例=0.5)
            time.sleep(self.配置.默认等待秒*3)
            截图=self.页面.线程.刷新截图()
            if 截图 is None:continue
            找寻结果=self.页面.线程.模板匹配器.match_multiple_flat_bypictures(截图, 图片集合,0.9,背包区域)
            if not 找寻结果:continue
            countB=len(找寻结果)
            for 结果 in 找寻结果:
                if 右键不可用:
                    self.通用操作.点击区域(结果.rect,2,0.1)
                else:
                    self.通用操作.点击区域(结果.rect,1,button="right")
                time.sleep(self.配置.默认等待秒)
            if not 检查1次:
                检查1次=True
                time.sleep(self.配置.默认等待秒)
                截图=self.页面.线程.刷新截图()
                if 截图 is None:continue    
                找寻结果=self.页面.线程.模板匹配器.match_multiple_flat_bypictures(截图, 图片集合,0.9,背包区域)
                if not 找寻结果:continue
                countE=len(找寻结果)
                if countE<countB:continue
                右键不可用=True
                调试器.debug("强化奖励", "背包清理: 检测到右键不可用")
                for 结果 in 找寻结果:
                    self.通用操作.点击区域(结果.rect,2,0.1)

        return True