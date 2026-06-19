# tasks/lianqibaoge.py
"""
炼器宝阁任务定义
"""

from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from typing import Optional, Self, Tuple, List
from core.utils import 匹配分组关键字, 解析时间文字,缩放区域,提取次数, 解析玩家全名
from core.debug import 调试器
import time
from core.recognition import OCRResult, ocr
from datetime import datetime

"""
炼器宝阁，抢夺，占领位置偏移情况
目标名字，-49，-77,104,-49
占领时间，-17，-47,65，-27
"""
def 比较宝阁等级(宝阁1: str, 宝阁2: str) -> int:
    """
    比较两个宝阁的等级大小
    
    返回:
         1: 宝阁1 > 宝阁2
         0: 宝阁1 == 宝阁2
        -1: 宝阁1 < 宝阁2
    """
    等级表 = ["鸿蒙宝阁", "混沌宝阁", "洪荒宝阁", "混元宝阁", 
              "玄天宝阁", "上古宝阁", "先天宝阁", "后天宝阁"]
    
    if 宝阁1 not in 等级表 or 宝阁2 not in 等级表:
        return 0
    
    索引1 = 等级表.index(宝阁1)
    索引2 = 等级表.index(宝阁2)
    
    if 索引1 < 索引2:
        return 1
    elif 索引1 > 索引2:
        return -1
    else:
        return 0


def 获取最高宝阁(宝阁列表: list) -> str:
    """获取等级最高的宝阁"""
    等级表 = ["鸿蒙宝阁", "混沌宝阁", "洪荒宝阁", "混元宝阁", 
              "玄天宝阁", "上古宝阁", "先天宝阁", "后天宝阁"]
    
    最高 = ""
    最高索引 = 99
    for 宝阁 in 宝阁列表:
        if 宝阁 in 等级表:
            索引 = 等级表.index(宝阁)
            if 索引 < 最高索引:
                最高索引 = 索引
                最高 = 宝阁
    return 最高
def 判断是否满足日期和时间规则(执行日期规则: str, 工作时间段列表: str = "") -> bool:
        """判断今天是否满足日期规则，且当前时间在工作时间段内"""
        if not 判断是否满足日期规则(执行日期规则):
            return False
        
        if not 工作时间段列表:
            return True
        
        现在 = datetime.now()
        当前分钟 = 现在.hour * 60 + 现在.minute
        
        段列表 = 工作时间段列表.split(",")
        for 段 in 段列表:
            if "-" in 段:
                开始, 结束 = 段.split("-")
                开始时, 开始分 = 开始.split(":")
                结束时, 结束分 = 结束.split(":")
                开始分钟 = int(开始时) * 60 + int(开始分)
                结束分钟 = int(结束时) * 60 + int(结束分)
                if 开始分钟 <= 当前分钟 <= 结束分钟:
                    return True
        
        return False

def 判断是否满足日期规则(执行日期规则: str) -> bool:
    """判断今天是否满足日期规则"""
    if not 执行日期规则:
        return False
    
    今天 = datetime.now()
    条件列表 = [c.strip() for c in 执行日期规则.split("&")]
    
    for 条件 in 条件列表:
        if 条件.startswith("日期") and "-" in 条件:
            范围 = 条件.replace("日期", "")
            起, 止 = 范围.split("-")
            if not (int(起) <= 今天.day <= int(止)):
                return False
        elif 条件 == "日期双数日":
            if 今天.day % 2 != 0:
                return False
        elif 条件 == "日期单数日":
            if 今天.day % 2 == 0:
                return False
        elif 条件.startswith("星期"):
            星期列表 = [int(x) for x in 条件.replace("星期", "").split(",")]
            if 今天.isoweekday() not in 星期列表:
                return False
    return True
def 获取当天21_15时间戳() -> float:
        """返回今天21:15的时间戳"""
        今天 = datetime.now()
        截止 = 今天.replace(hour=21, minute=15, second=0, microsecond=0)
        return 截止.timestamp()


@任务定义(
    任务ID="lianqibaoge",
    任务名称="炼器宝阁",
    调试模式=True,
    任务类型="小时任务",
    优先级=6,    
    地图关键字="炼器宝阁|宝阁守护", 
    工作时间开始=10,
    工作时间结束=22,
    提前进场秒数=0,
    次数刷新间隔小时=0.5,
    执行日期规则="星期6,7",
    抢夺宝阁="玄天宝阁",
    低于等于此抢夺次数启用次级抢夺=2,
    次级抢夺="玄天宝阁",
    占领宝阁="上古宝阁",
    低于等于此占领次数启用次级占领=2,
    次级占领="先天宝阁",
    十点几分后启用抢夺=0,
    避让的玩家 = "",
    打不过的敌人 = [],

    状态_当前占领宝阁名字="",
    状态_当前占领状态=False,
    状态_当前抢夺目标玩家="",
    状态_上次抢夺失败时间=0,
)

class 炼器宝阁任务(战斗任务执行器):
    """炼器宝阁任务执行器"""
  
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)    
        self.拖动数量={
             "鸿蒙宝阁":1, 
             "混沌宝阁":2, 
             "洪荒宝阁":2, "混元宝阁":3, 
              "玄天宝阁":4, "上古宝阁":9, "先天宝阁":16, "后天宝阁":26
        }
    def 执行入口逻辑(self) -> bool:
        """执行炼器宝阁入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")
        #避让决战盟重时间
        if 判断是否满足日期和时间规则(工作时间段列表="20:45-21:15", 执行日期规则="日期8-26 & 日期双数日"):
            self.任务状态.下次刷新时间= 获取当天21_15时间戳()
            return True

        self.同步避让玩家到打不过列表()
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False
        
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug(self.调试分类, "展开右上角任务帘失败")
            return False 
        
        if not self.页面.创建_通用点击图片验证图片切换(
            self.游戏配置.区域.主界面.第二三排任务区域标签.元组,            
            "炼器宝阁上标.bmp",
            self.游戏配置.区域.主界面.任务小页面检查区域标签.元组,
            "炼器宝阁下标.bmp",
            True,
            True
        ).执行() : 
            调试器.debug(self.调试分类, "炼器宝阁下标进入失败")
            return False
        
        if not self.页面.创建_通用点击图片验证文字切换(
            self.游戏配置.区域.主界面.任务小页面检查区域标签.元组,            
            "炼器宝阁下标.bmp",
            self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
            "炼|器",
            True,
        ).执行() :     
            调试器.debug(self.调试分类, "炼器宝阁下标点击失败")
            return False
        return  self._炼器宝阁情况更新()
       
    #  抢夺宝阁="",
    # 低于等于此抢夺次数启用次级抢夺=2,
    # 次级抢夺="",
    # 占领宝阁="",
    # 低于等于此抢夺次数启用次级占领=2,
    # 次级占领="",
    # 十点几分后启用抢夺=0,   
    def _炼器宝阁情况更新(self)-> bool:
        主页颜色统计=self.辅助识别器.区域像素统计(self.游戏配置.区域.炼器宝阁.炼器宝阁宝阁信息区域.元组,"00FF7F,0.95|F5F1F1,0.95")
        if 主页颜色统计[0]>0 and 主页颜色统计[1]>0:
            self.任务状态.当前占领状态=True
        elif 主页颜色统计[0]==0 and 主页颜色统计[1]>0:
            self.任务状态.当前占领状态=False
        占领次数=self.辅助识别器.获取区域次数(self.游戏配置.区域.炼器宝阁.炼器宝阁主页面占领剩余次数标签.元组,规则="次|数|欠")    
        抢夺次数= self.辅助识别器.获取区域次数(self.游戏配置.区域.炼器宝阁.炼器宝阁主页面抢夺剩余次数标签.元组,规则="次|数|欠")  
        if 占领次数==0 and 抢夺次数==0 :
            self.任务状态.剩余次数=0
            return False
        if self.任务状态.当前占领状态:
            self.任务状态.当前占领宝阁名字=self.辅助识别器.获取区域文字(self.游戏配置.区域.炼器宝阁.炼器宝阁主页面当前占领对象名称标签.元组)
        else:
            self.任务状态.当前占领宝阁名字=""
        
        抢夺开启=self._抢夺开启()
        if 抢夺次数 is not None and 抢夺次数>0 and 抢夺开启 and time.time()-self.任务状态.上次抢夺失败时间>600:
           return self._执行抢夺(抢夺次数)
        return self._执行占领(占领次数)

    def _抢夺开启(self)->bool:
        小时 = time.localtime().tm_hour  
        分钟 = time.localtime().tm_min   
        当前时分 = 小时 * 60 + 分钟    
        开始时间=self.任务配置.十点几分后启用抢夺+600
        return 当前时分>=开始时间
    
    def _执行占领(self,占领次数)-> bool:
        if 占领次数==0 and time.time()-self.任务状态.上次抢夺失败时间<600:
            self.任务状态.下次刷新时间=self.任务状态.上次抢夺失败时间+600
        占领对象=self.任务配置.占领宝阁
        if 占领对象=="":
            占领对象=self.任务配置.次级占领  
        if 占领对象=="":
            占领对象="先天宝阁" 
        if 占领次数<=self.任务配置.低于等于此占领次数启用次级占领:
           if not self.任务配置.次级占领=="":
              占领对象=self.任务配置.次级占领 
        结果=1
        if not self.任务状态.当前占领宝阁名字=="":
            结果=比较宝阁等级(占领对象,self.任务状态.当前占领宝阁名字)
        if 结果<1 :
            if self.任务状态.当前占领状态:
                self.任务状态.下次刷新时间=time.time()+self.任务配置.次数刷新间隔小时*3600              
            return  True
        if not 匹配分组关键字(self.线程.当前地图,"盟重省"):
              self.退出副本()
              return False
        获取宝阁列表=self.辅助识别器.获取区域文字坐标(self.游戏配置.区域.合成.合成左分类卡区域标签.元组)
        if 获取宝阁列表 is None:
            return False
        按钮区域=获取宝阁列表.find(占领对象)
        if 按钮区域 is None:
            return False
        self.通用操作.点击区域(按钮区域,2) 
        time.sleep(self.游戏配置.默认等待秒*2)  
        # filter_config=self._获取颜色校正规则(占领对象)
        if self._占领宝阁(占领对象):
            return True
        
    
    def _占领宝阁(self,宝阁名称)-> Optional [bool]:
        次数=self.拖动数量.get(宝阁名称)
        if 次数 is None:
            return None
        for i in range(次数):
            x,y= self.游戏配置.区域.炼器宝阁.炼器宝阁拖拽区域.随机点()
            if i==0:
                self.线程.动作执行器.drag(x,y,x+2,y-80) 
            else:
                self.线程.动作执行器.drag(x,y,x+2,y-257)    
                time.sleep(0.5)
                self.线程.动作执行器.drag(x,y,x+2,y-257)    
            time.sleep(0.5)
            self.线程.刷新截图() 
            #检索目标
            页面信息=self.辅助识别器.获取区域文字坐标(self.游戏配置.区域.炼器宝阁.炼器宝阁宝阁信息区域.元组)
            if 页面信息 is not None:
               获取抢夺文字坐标=页面信息.find("占领","exact",True)
               if 获取抢夺文字坐标 is not None:
                   for myrect in 获取抢夺文字坐标:
                        if self.页面.创建_通用点击区域验证文字切换(
                            myrect,
                            self.游戏配置.区域.炼器宝阁.炼器宝阁被抢夺后进入确定提示区域.元组,
                            "确|定"
                        ).执行():
                            if  self.页面.创建_通用点击区域验证文字切换(
                                self.游戏配置.区域.炼器宝阁.炼器宝阁被抢夺后进入确定提示区域.元组,
                                self.游戏配置.区域.主界面.小地图地图名显示标签.元组,
                                "炼器|宝阁|守护"
                            ).执行():                                        
                                return True
                        return False
        return None

    def _执行抢夺(self,抢夺次数)-> bool:
        抢夺对象=self.任务配置.抢夺宝阁
        if 抢夺对象=="":
            抢夺对象=self.任务配置.次级抢夺
        if 抢夺对象=="":
            抢夺对象=self.任务配置.占领宝阁
        if 抢夺对象=="":
            抢夺对象=self.任务配置.次级占领   
        if 抢夺对象=="":
            抢夺对象="先天宝阁"   
        if 抢夺次数<=self.任务配置.低于等于此抢夺次数启用次级抢夺:
           if not self.任务配置.次级抢夺=="":
              抢夺对象=self.任务配置.次级抢夺 
        结果=1
        if not self.任务状态.当前占领宝阁名字=="":
            结果=比较宝阁等级(抢夺对象,self.任务状态.当前占领宝阁名字)
        if 结果<1 :
            if self.任务状态.当前占领状态:
                self.任务状态.下次刷新时间=time.time()+self.任务配置.次数刷新间隔小时*3600
            return   True
        if not 匹配分组关键字(self.线程.当前地图,"盟重省"):
              self.退出副本()
              return False
                   
        获取宝阁列表=self.辅助识别器.获取区域文字坐标(self.游戏配置.区域.合成.合成左分类卡区域标签.元组)
        if 获取宝阁列表 is None:
            return False
        按钮区域=获取宝阁列表.find(抢夺对象)
        if 按钮区域 is None:
            return False
        self.通用操作.点击区域(按钮区域,2) 
        time.sleep(self.游戏配置.默认等待秒*2)  
        filter_config=self._获取颜色校正规则(抢夺对象)
        次数=self.拖动数量.get(抢夺对象)
        if 次数 is None:
            return False
        for i in range(次数):
            x,y= self.游戏配置.区域.炼器宝阁.炼器宝阁拖拽区域.随机点()
            if i==0:
                self.线程.动作执行器.drag(x,y,x+2,y-80) 
            else:
                self.线程.动作执行器.drag(x,y,x+2,y-257)    
                time.sleep(0.5)
                self.线程.动作执行器.drag(x,y,x+2,y-257)    
            time.sleep(0.5)
            self.线程.刷新截图() 
            #检索目标
            页面信息=self.辅助识别器.获取区域文字坐标(self.游戏配置.区域.炼器宝阁.炼器宝阁宝阁信息区域.元组)
            if 页面信息 is not None:
               获取抢夺文字坐标=页面信息.find("抢夺","exact",True)
               if 获取抢夺文字坐标 is not None:
                   for myrect in 获取抢夺文字坐标:
                      x=int(myrect[0])
                      y=int(myrect[1])
                      目标名字区域=x-49,y-77,x+104,y-49
                      占领时间区域=x-17,y-47,x+65,y-27
                      名字文字=self.辅助识别器.获取区域文字(目标名字区域,filter_config)
                      占领时间=self.辅助识别器.获取刷新秒数(占领时间区域,filter_config)
                      if 占领时间 is None:
                          if len(名字文字)>2 :
                              玩家信息=解析玩家全名(名字文字)
                              玩家名字=玩家信息["名字"].strip()
                              if not 玩家名字=="" and not 玩家名字 in self.任务配置.打不过的敌人:
                                    self.任务状态.当前抢夺目标玩家=玩家名字                                 
                                    if self.页面.创建_通用点击区域验证文字切换(
                                        myrect,
                                        self.游戏配置.区域.炼器宝阁.炼器宝阁被抢夺后进入确定提示区域.元组,
                                        "确|定"
                                    ).执行():
                                        if  self.页面.创建_通用点击区域验证文字切换(
                                            self.游戏配置.区域.炼器宝阁.炼器宝阁被抢夺后进入确定提示区域.元组,
                                            self.游戏配置.区域.主界面.小地图地图名显示标签.元组,
                                            "炼器|宝阁|守护"
                                        ).执行():                                        
                                            return True

                                    return False
        return False
         
    def 执行副本战斗逻辑(self) -> str:
            """
            执行副本战斗逻辑（模板方法）
            
            流程：
            1. 死亡复活 + 避让联动
            2. 更新战斗状态
            3. 位置复查（仅战斗前）
            4. 领取奖励退出
            5. 副本内检查钩子
            6. 正常阶段策略（回血）
            7. 抢怪阶段操作
            8. 退出条件检查
            9. 自动战斗/走位
            """
            调试器.debug(self.调试分类, "执行副本战斗逻辑")        
            
            文字信息=self.辅助识别器.获取区域文字(self.游戏配置.区域.炼器宝阁.炼器宝阁战斗结果情况标签.元组)
            if 匹配分组关键字(文字信息,"成功,轻而"):
                self.任务状态.下次刷新时间=time.time()+self.任务配置.次数刷新间隔小时*3600
                self.通用操作.领取奖励退出操作()
                self._点击中间确定按钮()
                return "胜利"
            if 匹配分组关键字(文字信息,"失败,乃兵"):
                self.添加打不过敌人(self.任务状态.当前抢夺目标玩家)
                任务定义.导出配置到JSON(self.线程.窗口名称,线程=self.线程)   
                self.任务状态.上次抢夺失败时间=time.time()
                self.通用操作.领取奖励退出操作()
                self._点击中间确定按钮()
                return "失败"

            截图 = self.线程.截图
            self.更新目标状态()
            self.更新静止状态(截图)


          
         
            self.检查调整自动战斗状态()
            self.检查调整自动走位状态()
          
            return "进行中"
    def _点击中间确定按钮(self):
        if self.页面.创建_通用点击文字验证文字切换(
            self.游戏配置.区域.主界面.中间任务结束按钮区域标签.元组,
            "确|定",
            self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
            "炼|器"
        ).执行():
            self.通用操作.关闭中间可能存在的窗口()
    
    def _获取颜色校正规则(self,宝阁名字:str)->dict:
        if 匹配分组关键字(宝阁名字,"洪荒|混元"):
            filter_config = {
                    # "color_range": "110,255,0,24,0,20|0,25,150,255,0,16",  
                    "color_range":"162,178,9,14,9,15|125,130,6,15,2,15|229,233,7,11,7,11|138,165,10,18,10,18|215,219,8,12,8,12|186,205,8,13,8,13|110,120,11,17,11,18",                
                    "keep_color": True,
                    "background": "black"
                }
        else:
            filter_config = {
                    "color_range": "110,255,0,24,0,20",  
                    # "color_range":"162,178,9,14,9,15|125,130,6,15,2,15|229,233,7,11,7,11|138,165,10,18,10,18|215,219,8,12,8,12|186,205,8,13,8,13|110,120,11,17,11,18",                
                    "keep_color": True,
                    "background": "black"
                }
        return filter_config
    def 添加打不过敌人(self, 敌人名: str):
        """添加打不过的敌人，重复不添加"""
        敌人名 = 敌人名.strip()
        if not 敌人名:
            return
        
        列表 = self.任务配置.打不过的敌人
        
        if 敌人名 in 列表:
            return
        
        列表.append(敌人名)       
        调试器.debug("战斗助手", f"添加打不过敌人: {敌人名}")

    def 同步避让玩家到打不过列表(self):
        """将 避让的玩家 字符串解析并加入 打不过敌人列表（去重）"""
        避让字符串 = self.任务配置.避让的玩家
        if not 避让字符串:
            return
        
        列表 =  self.任务配置.打不过的敌人
        新增 = 0
        
        for 玩家名 in 避让字符串.split(','):
            玩家名 = 玩家名.strip()
            if 玩家名 and 玩家名 not in 列表:
                列表.append(玩家名)
                新增 += 1
        
        # if 新增 > 0:
        #     self.游戏配置.保存到文件()
        #     调试器.debug("战斗助手", f"同步避让玩家 {新增} 人到打不过列表")

    