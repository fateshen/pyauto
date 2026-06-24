# tasks/yijieduobao.py
"""
异界夺宝任务定义

每周1、3、5的20:00-20:16:30
3轮报名+战斗：报名150秒，战斗180秒
"""
import datetime
import re
import time
from typing import List, Tuple, Optional

from rich.repr import T

from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from core.utils import 匹配分组关键字, 提取次数, 缩放区域,解析玩家全名
from core.debug import 调试器
from pydantic import Field


@任务定义(
    任务ID="yijieduobao",
    任务名称="异界夺宝",
    调试模式=True,
    任务类型="每日任务",
    地图关键字="异界夺|界夺宝",
    优先级=16,
    执行日期规则="星期1,3,5",
    工作时间段列表="20:00-20:16",
    
    异界我已组好队并是队员=False,
    异界作为队长=False,
    异界队友名单="",
    异界等级范围="1,2,3,4",
    状态_异界当前轮次=0,
    状态_异界是否已报名=False,
    状态_异界报名等级=0,
    状态_异界报名图标相对特征1位置=Field(default_factory=list),
    状态_异界报名图标相对特征2位置=Field(default_factory=list),
    状态_异界上次复查时间=0.0,
    状态_异界组队完成=False,
    状态_报名开始时间=0,
    状态_队友名字=[],
    状态_报名页面=0,
)
class 异界夺宝任务(战斗任务执行器):
    """异界夺宝任务执行器"""
    
    _邀请按钮X偏移 = 200
    _邀请按钮Y偏移 = -10
    _邀请按钮宽度 = 60
    _邀请按钮高度 = 20
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)
    
    # ==================== 主入口 ====================
    def 执行(self) -> str:
        """
        执行任务（模板方法）
        
        子类不应继承此方法，而是重写：
        - 是否在副本中()
        - 执行入口逻辑()
        """
        调试器.info(self.调试分类, f"开始执行: {self.任务配置.任务名称}({self.任务配置.任务ID})")
        调试器.debug(self.调试分类, f"当前地图: {self.线程.当前地图}")
        
        
        # 1. 判断是否在副本中
        if self.是否在副本中():
            调试器.debug(self.调试分类, "判定在副本中，执行战斗逻辑")
            return self.执行副本战斗逻辑()
        
        if self.检查并处理复活():
            return "死亡"
        
        # 2. 检查前置条件
        if not self.检查前置条件():
            调试器.debug(self.调试分类, "前置条件不满足，等待中")
            return "等待"
        
        # 3. 执行入口逻辑
        调试器.debug(self.调试分类, "执行入口逻辑")
        if not self.执行入口逻辑():
            
            self.通用操作.覆盖鼠标提示到边缘()
            self.通用操作.关闭中间可能存在的窗口()  
            self._等待中借调普通任务()
            return "失败"        
        self.通用操作.关闭中间可能存在的窗口()
        调试器.state(self.调试分类, "已进入副本，开始战斗")
        self.任务状态.记录入口成功()
        self.任务状态.重置位置复查()
        self._等待中借调普通任务()
        return "进行中"
    
    def 执行入口逻辑(self) -> bool:
        """异界夺宝入口逻辑"""
        调试器.info(self.调试分类, "开始执行异界夺宝入口逻辑")
        
        # 1. 判断是否报名期
        轮次 = self._计算当前轮次()
       
        if 轮次 == 0:
            self._活动结束重置()
            return False

        self.任务状态.异界当前轮次 = 轮次
        调试器.debug(self.调试分类, f"当前第{轮次}轮报名期")

        if 轮次>0 and self.任务配置.异界我已组好队并是队员:
            调试器.debug(self.调试分类, "已组队，等待队长操作")            
            return True
        
        if 轮次>0:
            #5秒进入检查一次
            当前时间 = time.time()
            if 当前时间 - self.任务状态.异界上次复查时间 < 5:
                return True
            
            self.任务状态.异界上次复查时间 = 当前时间
        
        # 2. 打开报名界面
        if not self._打开报名界面():
            return False
        
        # 进场期（轮次为负数）
        if 轮次 < 0:
            调试器.debug(self.调试分类, f"当前第{-轮次}轮进场期")
            if self._点击进入异界副本():
                return True
            return False

        # 3. 已报名 → 复查
        if self.任务状态.异界是否已报名:
            if self._复查报名状态():
                return True
            self._重置报名状态()

        # 4. 组队阶段（前30秒）
        是否前30秒 = time.time() - self.任务状态.报名开始时间 < 30
        
        if 是否前30秒 and not self.任务状态.异界组队完成:
            if self.任务配置.异界作为队长:
                self._队长组队()
            else:
                self._队员组队()
            return True
        
        # 5. 队员组队成功后不需要报名，等队长操作
        if not self.任务配置.异界作为队长 and self.任务状态.异界组队完成:
            调试器.trace(self.调试分类, "队员组队完成，等待队长报名")
            return True
        
        # 6. 报名（队长 / 队员超时后）
        if self._报名工作():
            self.任务状态.异界是否已报名 = True
            return True
        
        return False
    
    # ==================== 轮次计算 ====================
    def _计算当前轮次(self) -> int:
        """
        返回: 0=不在活动期, 正数=报名期, 负数=进场期（取绝对值即轮次）
        """
        now = datetime.datetime.now()
        基准 = now.replace(hour=20, minute=0, second=0, microsecond=0)
        秒偏移 = (now - 基准).total_seconds()
        
        if 秒偏移 < 0:
            return 0
        
        轮次表 = [
            (0, 150, 150, 210),
            (330, 480, 480, 540),
            (660, 810, 810, 870),
        ]
        
        for i, (报开, 报结, 进开, 进结) in enumerate(轮次表, 1):
            if 报开 <= 秒偏移 < 报结:
                if abs(self.任务状态.异界当前轮次) != i:
                    self.任务状态.报名开始时间 = time.time() - 秒偏移 + 报开
                    调试器.trace(self.调试分类, f"轮次切换 →{i}报名期")
                return i
            
            if 进开 <= 秒偏移 < 进结:
                if abs(self.任务状态.异界当前轮次) != i:
                    self.任务状态.报名开始时间 = time.time() - 秒偏移 + 报开
                    调试器.trace(self.调试分类, f"轮次切换 →{i}进场期")
                return -i
        
        return 0
    
    def _活动结束重置(self):
        if self.任务状态.异界当前轮次 != 0:
            调试器.debug(self.调试分类, "活动已结束，重置状态")
        self._重置报名状态()
        self.任务状态.异界组队完成 = False
        self.任务状态.异界当前轮次 = 0
        self.任务状态.报名开始时间 = 0
    
    # ==================== 界面操作 ====================
    
    def _打开报名界面(self) -> bool:
        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug(self.调试分类, "展开右上角任务帘失败")
            return False
        if not self.页面.主界面操作.进入异界夺宝界面.执行():
            调试器.debug(self.调试分类, "进入异界夺宝页面失败")
            return False
        return True
    
    # ==================== 队长组队 ====================
    
    def _队长组队(self):
        if not self.页面.异界夺宝.进入异界夺宝组队页面.执行():
            return
        if not self._已组队完成():
            self._邀请队友()
    
    # ==================== 队员组队 ====================
    
    def _队员组队(self):
        """
        队员组队逻辑（前30秒）
        1. 检测并接受组队邀请
        2. 检查是否已2人 → 组队完成
        3. 单人 → 退出队伍
        """
        # 1. 检测并接受组队邀请
        self._检测并接受组队邀请()
        
        # 2. 检查是否组队完成
        if not self.页面.异界夺宝.进入异界夺宝组队页面.执行():
            return
        
        if self._已组队完成():
            self.任务状态.异界组队完成 = True
            调试器.debug(self.调试分类, "队员组队完成")
            return
        
        # 3. 单人 → 退出队伍
        self._退出单人队伍()
    
    def _检测并接受组队邀请(self):
        """在异界页面范围寻找邀请图标并点击接受"""
        邀请区域 = self.游戏配置.区域.异界夺宝.异界夺宝被邀请按钮区域标签
        if not 邀请区域:
            return
        
        截图 = self.线程.截图
        if 截图 is None:
            return
        
        结果 = self.线程.模板匹配器.match_bypicture(
            截图, "被邀请图标.bmp", threshold=0.8, region=邀请区域.元组
        )
        
        if not 结果:
            return
        if not self.页面.创建_通用点击区域验证文字切换(
                结果.rect,
                self.游戏配置.区域.异界夺宝.异界夺宝被邀请操作文字区域标签.元组,
                "操|作"
            ).执行():
            return
        ocr_result =self.辅助识别器.获取区域文字坐标(self.游戏配置.区域.异界夺宝.异界夺宝被邀请名字检查区域标签.元组)
        if not ocr_result:
            return
        
        # 遍历每条文字，提取玩家名
        for 文字, 坐标 in ocr_result.items:
            玩家名 = self._提取邀请玩家名(文字)
            if not 玩家名:
                continue
            
            调试器.trace(self.调试分类, f"检测到邀请: '{玩家名}' 来自 '{文字}'")
            
            # 匹配队友名单
            if self._是否队友(玩家名):
                同意按钮区域=坐标[0]+510, 坐标[1]-16, 坐标[0]+610, 坐标[1]+36 
                if  self.页面.创建_通用点击文字验证文字切换(
                        同意按钮区域,
                        "同|意",
                        同意按钮区域,
                        "同|意",
                        False
                    ).执行():
                    return
                
        self._关闭报名页()       

    def _提取邀请玩家名(self, 文字: str) -> str:
        """
        从邀请文字中提取玩家名
        
        "巢元畅邀请您加入他的战队" → "巢元畅"
        "古剑宝贝多出邀请您加入他的战队" → "古剑宝贝多出"
        """
        if not 文字:
            return ""
        
        # 找到"邀请"的位置，之前的部分就是玩家名
        位置 = 文字.find("邀请")
        if 位置 > 0:
            return 文字[:位置]
        
        return ""
    
    def _是否队友(self, 玩家名: str) -> bool:
        """检查玩家名是否在队友名单中（精确匹配）"""
        队友名单 = self._解析队友名单()
        if not 队友名单:
            return False
        
        return 玩家名 in 队友名单
    def _退出单人队伍(self):
        """退出当前单人队伍（子类填充）"""
        return self.页面.创建_通用点击文字验证文字切换(
            self.游戏配置.区域.异界夺宝.异界夺宝组队页面退出队伍按钮标签.元组,
            "退|出",
            self.游戏配置.区域.异界夺宝.异界夺宝组队页面玩家名字标题标签.元组,
            "名|字",
            False
        ).执行()
    
    # ==================== 通用组队方法 ====================
    
    def _已组队完成(self) -> bool:
        # 邀请图标存在 = 队伍未满
        if self.辅助识别器.查找图片单结果(
            self.游戏配置.区域.异界夺宝.异界夺宝邀请队友按钮标签.元组,
            "异界夺宝邀请队友图标.bmp"
        ):
            self.任务状态.异界组队完成 = False
            调试器.debug(self.调试分类, "邀请图标存在，队伍未满")
            return False
        
        self.线程.刷新截图()
        txt = self.辅助识别器.获取区域文字(
            self.游戏配置.区域.异界夺宝.异界夺宝组队页面第二个玩家名字区域标签.元组
        )
        if txt and len(txt) > 0:  
            第一个名字=self.辅助识别器.获取区域文字(
            self.游戏配置.区域.异界夺宝.异界夺宝组队页面第一个玩家名字区域标签.元组
            )
            self.任务状态.队友名字=[txt,第一个名字]

            self.任务状态.异界组队完成 = True
            调试器.debug(self.调试分类, "组队完成")
            return True
        
        # 不确定状态，保持原值
        return self.任务状态.异界组队完成
    
    def _邀请队友(self):
        队友名单 = self._解析队友名单()
        if not 队友名单:
            return
        
        if not self.页面.创建_通用点击图片验证文字切换(
            self.游戏配置.区域.异界夺宝.异界夺宝邀请队友按钮标签.元组,
            "异界夺宝邀请队友图标.bmp",
            self.游戏配置.区域.异界夺宝.异界夺宝组队页面玩家名字标题标签.元组,
            "行会"
        ).执行():
            return
        
        可邀请名单 = self.辅助识别器.获取区域文字坐标(
            self.游戏配置.区域.异界夺宝.异界夺宝邀请队友页面玩家名字区域标签.元组
        )
        if 可邀请名单 is None:
            return
        
        for 队友名 in 队友名单:
            调试器.trace(self.调试分类, f"尝试邀请: {队友名}")
            名字坐标区域 = 可邀请名单.find(队友名, "exact")
            if 名字坐标区域 is None:
                continue
            
            邀请按钮区域 = (
                int(名字坐标区域[0] + self._邀请按钮X偏移),
                int(名字坐标区域[1] + self._邀请按钮Y偏移),
                int(名字坐标区域[2] + self._邀请按钮X偏移 + self._邀请按钮宽度),
                int(名字坐标区域[3] + self._邀请按钮Y偏移 + self._邀请按钮高度),
            )
            
            self.页面.创建_通用点击文字验证文字切换(
                邀请按钮区域, "邀请",
                邀请按钮区域, "已|己",
                True, True,
            ).执行()
    
    def _解析队友名单(self) -> List[str]:
        名单 = self.任务配置.异界队友名单
        if not 名单:
            return []
        return [x.strip() for x in 名单.split(',') if x.strip()]
    
    # ==================== 报名 ====================
    
    def _报名工作(self) -> bool:        
        
        等级列表 = self._解析等级范围()
        调试器.debug(self.调试分类, f"报名等级范围: {等级列表}")
        if self.任务状态.报名页面==1:
            time.sleep(self.游戏配置.刷新等待秒)
            self.线程.刷新截图()
            self.通用操作.关闭中间可能存在的窗口()
            if not self._打开报名界面():return False
        
        for 等级 in 等级列表:  
            序号=1
            if 等级>2: 序号=2         
            for i in range(序号):
                self._关闭报名页()
                图标路径 = f"{等级}级异界.bmp"
                图标位置列表 = self._识别图标所有位置(图标路径)
                
                if not 图标位置列表:
                    调试器.trace(self.调试分类, f"未找到{等级}级异界图标")
                    continue
                
                for 图标位置 in 图标位置列表:
                    #防止报名页遮蔽
                    self._关闭报名页()

                    if not self._指定区域打开报名页(图标位置):
                        continue
                    
                    if self._验证报名按钮为已报名():
                        self._记录报名位置(等级, 图标位置,i)
                        调试器.state(self.调试分类, f"报名成功: {等级}级")
                        return True
                #1、2级别不需要翻页
                if i==0 and 等级>2:
                    x,y =self.游戏配置.区域.合成.合成左分类卡区域标签.随机点(0.5)
                    self.线程.动作执行器.drag(x,y,x,y+300)
                    time.sleep(0.5)
                    self.线程.刷新截图()
                    if self.辅助识别器.查找图片单结果(
                        self.游戏配置.区域.异界夺宝.报名标记查找区域标签.元组,
                        "特征2.bmp"
                    ):
                        break
            #3级检查完成，同时需要检查4级，重新打开
            if 等级==3 and 4 in 等级列表:
                time.sleep(self.游戏配置.刷新等待秒)
                self.线程.刷新截图()
                self.通用操作.关闭中间可能存在的窗口()
                if not self._打开报名界面(): break


        调试器.warning(self.调试分类, "所有等级均报名失败")
        return False
    
    def _指定区域打开报名页(self,指定区域:Tuple[int,int,int,int])-> bool:
        return self.页面.创建_通用点击区域验证文字切换(
            指定区域,
            self.游戏配置.区域.异界夺宝.异界夺宝报名玩家名字标题标签.元组,
            "名字"
        ).执行()

    # ==================== 复查 ====================
    
    def _复查报名状态(self) -> bool:   
        if self.任务状态.报名页面==1:
            正确打开页面=False
            for _ in range(2):               
                x,y =self.游戏配置.区域.合成.合成左分类卡区域标签.随机点(0.5)
                self.线程.动作执行器.drag(x,y,x,y+300)
                time.sleep(0.5)
                self.线程.刷新截图()
                if not self.辅助识别器.查找图片单结果(
                    self.游戏配置.区域.异界夺宝.报名标记查找区域标签.元组,
                    "特征2.bmp"
                ):
                    正确打开页面=True
                    break
            if not 正确打开页面: return False
        
        if self._检测报名记号():
            调试器.trace(self.调试分类, "复查: 报名记号存在")
            return True
        
        调试器.debug(self.调试分类, "复查: 报名记号消失，尝试特征图标定位")
        
        for 特征名, 偏移属性 in [
            ("特征1", "异界报名图标相对特征1位置"),
            ("特征2", "异界报名图标相对特征2位置"),
        ]:
            偏移 = getattr(self.任务状态, 偏移属性, [])
            if not 偏移:
                continue
            
            特征位置 = self._查找特征图标(特征名)
            if not 特征位置:
                continue
            
            入口位置 = (
                特征位置[0] + 偏移[0],
                特征位置[1] + 偏移[1],
                特征位置[0] + 偏移[0] + 偏移[2],
                特征位置[1] + 偏移[1] + 偏移[3],
            )
            入口位置 = 缩放区域(入口位置, 1.5)
            
            self._关闭报名页()
            
            if not self.页面.创建_通用点击图片验证文字切换(
                入口位置,
                f"{self.任务状态.异界报名等级}级异界.bmp",
                self.游戏配置.区域.异界夺宝.异界夺宝报名玩家名字标题标签.元组,
                "名字"
            ).执行():
                continue
            
            if self._验证报名按钮为已报名():
                调试器.debug(self.调试分类, f"通过{特征名}复查成功")
                return True
        
        调试器.state(self.调试分类, "复查失败，已被挤出")
        return False
    
    # ==================== 位置记录 ====================
    
    def _记录报名位置(self, 等级: int, 图标位置: Tuple[int, int, int, int],报名页:int):
        self.任务状态.异界报名等级 = 等级
        self.任务状态.报名页面 = 报名页
        
        for 特征名, 偏移属性 in [
            ("特征1", "异界报名图标相对特征1位置"),
            ("特征2", "异界报名图标相对特征2位置"),
        ]:
            特征位置 = self._查找特征图标(特征名)
            if 特征位置:
                偏移 = [
                    图标位置[0] - 特征位置[0],
                    图标位置[1] - 特征位置[1],
                    图标位置[2] - 图标位置[0],
                    图标位置[3] - 图标位置[1],
                ]
                setattr(self.任务状态, 偏移属性, 偏移)
                调试器.trace(self.调试分类, f"记录{特征名}偏移: {偏移}")
            else:
                setattr(self.任务状态, 偏移属性, [])
    
    def _重置报名状态(self):
        self.任务状态.异界是否已报名 = False
        self.任务状态.异界报名等级 = 0
        self.任务状态.报名页面=0
        self.任务状态.异界报名图标相对特征1位置 = []
        self.任务状态.异界报名图标相对特征2位置 = []
    
    # ==================== 识别方法 ====================
       
    def _解析等级范围(self) -> List[int]:
        范围字符串 = self.任务配置.异界等级范围
        if not 范围字符串:
            return [1, 2, 3, 4]
        结果 = [int(x.strip()) for x in 范围字符串.split(',') if x.strip() and x.strip().isdigit()]
        结果.sort()
        return 结果
    
    def _检测报名记号(self) -> bool:
        截图 = self.线程.截图
        if 截图 is None:
            return False
        区域 = self.游戏配置.区域.异界夺宝.报名标记查找区域标签
        if 区域:
            结果 = self.线程.模板匹配器.match_bypicture(截图, "异界报名标记.bmp", threshold=0.8, region=区域.元组)
        else:
            结果 = self.线程.模板匹配器.match_bypicture(截图, "异界报名标记.bmp", threshold=0.8)
        if 结果 is None:
            调试器.debug(self.调试分类, "未找到报名记号")
            return False
        区域= 结果.rect  
        调试器.debug(self.调试分类, f"已找到报名记号: {区域}")
        if not 区域:            
            return False          
        return True
    
    def _识别图标所有位置(self, 图标路径: str) -> List[Tuple[int, int, int, int]]:
        截图 = self.线程.截图
        if 截图 is None:
            return []
        区域 = self.游戏配置.区域.异界夺宝.报名标记查找区域标签
        if 区域:
            结果列表 = self.线程.模板匹配器.match_all_bypicture(截图, 图标路径, threshold=0.8, region=区域.元组)
        else:
            结果列表 = self.线程.模板匹配器.match_all_bypicture(截图, 图标路径, threshold=0.8)
        return [r.rect for r in 结果列表]
    
    def _验证报名按钮为已报名(self) -> bool:
        区域 = self.游戏配置.区域.异界夺宝.异界夺宝报名按钮标签
        if not 区域:
            return False
        截图 = self.线程.截图
        if 截图 is None:
            return False
        文字 = self.线程.文字识别器.recognize_text(截图, 区域.元组)
        调试器.trace(self.调试分类, f"报名按钮文字: '{文字}'")
        if 文字=="报名":
            self.通用操作.点击区域(区域.元组)
            return True

        return 匹配分组关键字(文字 or "", "已|己")
    
    def _查找特征图标(self, 特征名: str) -> Optional[Tuple[int, int, int, int]]:
        区域 = self.游戏配置.区域.异界夺宝.报名标记查找区域标签
        if not 区域:
            return None
        结果 = self.线程.模板匹配器.match_bypicture(self.线程.截图, f"{特征名}.bmp", threshold=0.8, region=区域.元组)
        return 结果.rect if 结果 else None
    
    def _关闭报名页(self):
        self.页面.创建点击图片操作(
            self.游戏配置.区域.异界夺宝.异界夺宝关闭报名页范围标签.元组,
            "关闭按钮.bmp"
        ).执行()


    def _点击进入异界副本(self)->bool:
        按钮文字=self.辅助识别器.获取区域文字坐标(self.游戏配置.区域.异界夺宝.异界夺宝进入战场按钮标签.元组 )
        if not 按钮文字: return False
        按钮区域=按钮文字.find("进|入")
        if not 按钮区域:return False
        if self.页面.创建_通用点击区域验证文字切换(
            按钮区域,
            self.游戏配置.区域.主界面.小地图地图名显示标签.元组,
            "异界夺宝|界夺宝",
        ).执行():
            return True
        return False
    
    def _执行抢怪操作(self) -> bool:
        #增加归属判定
        归属者名字文字=self.辅助识别器.获取区域文字(self.游戏配置.区域.异界夺宝.异界夺宝战场归属者名字标签.元组)
        归属信息=解析玩家全名(归属者名字文字)
        if  归属信息["名字"] in self.任务状态.队友名字: 
            return False
        #这里需要增加走位操作    
        return self.通用操作.点击区域(self.游戏配置.区域.异界夺宝.异界夺宝战场抢归属标签.元组)
    
    def _是否抢怪阶段(self) -> bool:
        #重写简单判断，是否有必要复杂判断？
        if not self.任务配置.启用抢怪模式:            
            return False
        目标血量=self.辅助识别器.获取区域文字(self.游戏配置.区域.异界夺宝.异界夺宝战场BOSS剩余血量标签.元组)
        
        if 目标血量 is not None: 
            血量=提取次数(目标血量)
            if 血量>0 :
                self.公共变量.记录最小血量=血量
        if self.公共变量.记录最小血量<=self.任务配置.低于此血量抢怪:
            return True    
        return False  
    
    def 检查攻击模式(self) -> None:
        return 
    
    #异界夺宝不主动退出
    def 检查退出条件(self) -> bool:
        return False

    