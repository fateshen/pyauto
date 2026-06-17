# tasks/reward/kaifukuanghuan.py

from core.utils import 匹配分组关键字, 是否为今天

from tasks.reward.base import 强化奖励任务基类
from core.debug import 调试器
import time,random

class 开服狂欢(强化奖励任务基类):
    任务ID = "kaifukuanghuan"
    任务名称 = "开服狂欢"  
    任务类型: str = "每日任务"
    是否启用: bool = True  
    最小间隔秒 = 300
    最大间隔秒 = 600
    每日必买购买=True
    每日必买不买龙魂 = True

    登录奖励完成时间=0
    每日必买完成时间=0
    在线奖励完成时间=0
    

    def 执行(self) -> bool:
        self.页面.主界面操作.展开右上角任务帘
        if not self.页面.创建_通用点击图片验证文字切换 (
            self.配置.区域.主界面.第二三排任务区域标签.元组, 
            "开服狂欢图标.bmp",
            self.配置.区域.主界面.中间页面名称区域标签.元组,
            "开|服"
            ).执行():
            self.下次执行时间 = time.time() + random.randint(180, 600)
            调试器.debug("强化奖励", "开服狂欢: 进入页面失败")
            return False
        ocr_result=self.辅助识别器.获取区域文字坐标(self.配置.区域.日常强化.开服活动内容清单显示区域.元组)  
        if not ocr_result:  
            self.下次执行时间 = time.time() + random.randint(180, 600)
            调试器.debug("强化奖励", "开服狂欢: 获取内容失败")  
            return True
        登录奖励区域=ocr_result.find("七日")
        本次有领取操作=False
        if 登录奖励区域 and not 是否为今天(self.登录奖励完成时间) :
            self.通用操作.点击区域(登录奖励区域)
            time.sleep(self.配置.默认等待秒)
            for _ in range(5):                  
                if not self.页面.创建寻图点击原区域操作(
                    self.配置.区域.日常强化.登录领取奖励按钮带红点显示区域.元组,
                    "红点1.bmp",
                    0.3,  
                    刷新=True              
                ).执行():
                    break
                time.sleep(self.配置.默认等待秒)
            if self.辅助识别器.区域包含文字(self.配置.区域.日常强化.登录领取奖励按钮带红点显示区域.元组,"已|己|暂"):   
                self.登录奖励完成时间=time.time()
                本次有领取操作=True
        每日必买区域=ocr_result.find("必买")        
        if 每日必买区域 and not 是否为今天(self.每日必买完成时间) :
            self.通用操作.点击区域(每日必买区域)
            time.sleep(self.配置.默认等待秒)
            self.通用操作.线程.刷新截图()
            奖励名称文字=self.辅助识别器.获取区域文字(self.配置.区域.日常强化.每日必买奖励奖品文字区域.元组)
            if 匹配分组关键字(奖励名称文字,"斗|披|面|盾") or (匹配分组关键字(奖励名称文字,"龙") and not self.每日必买不买龙魂):
                for _ in range(5):                  
                    if not self.页面.创建寻图点击原区域操作(
                        self.配置.区域.日常强化.每日必买奖励按钮带红点显示区域.元组,
                        "红点1.bmp",
                        0.3,  
                        刷新=True              
                    ).执行():
                        break
                    time.sleep(self.配置.默认等待秒)
            if 匹配分组关键字(奖励名称文字,"龙") and self.每日必买不买龙魂:
                self.每日必买完成时间=time.time()
                本次有领取操作=True
            else:
                if self.辅助识别器.区域包含文字(self.配置.区域.日常强化.每日必买奖励按钮带红点显示区域.元组,"已|己"):   
                    self.每日必买完成时间=time.time()
                    本次有领取操作=True
        在线奖励区域=ocr_result.find("在线")
        if 在线奖励区域 and not 是否为今天(self.在线奖励完成时间) :
            self.通用操作.点击区域(在线奖励区域)
            time.sleep(self.配置.默认等待秒)           
            for _ in range(10):                  
                if not self.页面.创建寻图点击原区域操作(
                    self.配置.区域.日常强化.在线奖励领取奖励按钮带红点区域.元组,
                    "红点1.bmp",
                    0.3,  
                    刷新=True              
                ).执行():
                    break
                time.sleep(self.配置.默认等待秒)
            if self.辅助识别器.区域包含文字(self.配置.区域.日常强化.在线奖励领取奖励按钮带红点区域.元组,"已|己"):   
                self.在线奖励完成时间=time.time()
                本次有领取操作=True
        任务完成时间=min(self.登录奖励完成时间,self.每日必买完成时间,self.在线奖励完成时间)
        if 是否为今天(任务完成时间):  
            self.上次确定任务结束时间 =任务完成时间
            调试器.debug("强化奖励", "开服狂欢: 今日已完全领取")      
        if 本次有领取操作: 
            self.管理器.保存配置()
              
        return True