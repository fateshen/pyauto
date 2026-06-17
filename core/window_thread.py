# core/window_thread.py
"""
窗口工作线程

功能：
1. 每个窗口独立运行，持有该窗口的全局变量
2. 管理截图、地图识别、任务调度
3. 死亡复活处理
4. 主循环调度

依赖：
- core.runtime_state (运行时公共变量)
- core.task_scheduler (任务调度器)
- core.map_navigator (地图进入器)
- core.action_executor (动作执行器)
- core.recognition (识别模块)
- models.game_config (游戏配置)
"""
import threading
import time
from typing import Optional, Self, Tuple, List
import numpy as np
import datetime
import re as re_module
from PySide6.QtCore import QObject, Signal

from core.runtime_state import 运行时公共变量
from core.task_scheduler import 任务调度器
from core.map_navigator import 步骤式地图进入器
from core.page_operations import 页面操作集
from core.action_executor import ActionExecutor
from core.recognition import TextRecognizer, TemplateMatcher, PixelAnalyzer
from core.window_manager import capture_window
from models.dynamic_tags import 动态标签
from core.task_executors.registry import 任务执行器注册表
from core.utils import 匹配分组关键字, 是否是纯色截图,是否重复聊天内容,是否为今天
from core.debug import 调试器, 初始化线程日志, 关闭线程日志
from core.common_operations import 通用操作集
from core.assistant import 战斗辅助识别器
from core.chat_manager import 聊天管理器
from core.reward_manager import 强化奖励管理器
from tasks.base import 任务定义
import win32api
import win32gui
import win32con


class 窗口线程信号(QObject):
    """窗口线程的信号发射器"""
    停止信号 = Signal(str)
    启动信号 = Signal(str)

class 窗口线程(threading.Thread):
    """单个窗口的工作线程"""
    
    def __init__(self, 窗口句柄: int, 窗口名称: str = "游戏1", 游戏配置=None, 任务配置列表=None):
        """
        初始化窗口线程
        
        参数:
            窗口句柄: 窗口句柄
            窗口名称: 窗口名称（用于多窗口配置隔离）
            游戏配置: 游戏全局配置实例（如果不提供则创建默认）
        """
        super().__init__()
        初始化线程日志(窗口名称)
        self.信号 = 窗口线程信号() 
        self._暂停标志 = False

        self.窗口句柄 = 窗口句柄
        self.窗口名称 = 窗口名称
        self.daemon = True

        self.主城死亡= False
        self.最后成功获取地图时间=time.time()
        
        # ========== 初始化线程日志 ==========
        # 初始化线程日志(窗口名称)
        
        # ========== 设置当前窗口（线程局部存储） ==========
        任务执行器注册表.设置当前窗口(窗口名称)
        
        # ========== 配置 ==========
        from models.game_config import 游戏全局配置
        if 游戏配置:
            self.游戏配置 = 游戏配置
        else:
            # 从窗口专属配置文件加载
            self.游戏配置 = 游戏全局配置.从文件加载(窗口名称)
        
        self.动态标签 = 动态标签(self, self.游戏配置.区域)
        
        # ========== 线程全局变量 ==========
        self.截图: Optional[np.ndarray] = None
        self.当前地图: str = ""
        
        # 识别器（每个线程独立实例）
        self.文字识别器 = TextRecognizer()
        self.模板匹配器 = TemplateMatcher()
        self.像素分析器 = PixelAnalyzer()
        
        # 动作执行器
        self.动作执行器 = ActionExecutor(窗口句柄)
        
        # 公共变量（运行时状态）
        self.公共变量 = 运行时公共变量()
        
        # ========== 任务管理 ==========
        self.任务排序列表: List = []      # 按优先级排序的任务列表
        # self.任务映射: dict = {}          # 任务ID -> 任务配置
        self.任务状态映射: dict = {}      # 任务ID -> 任务状态
        
        # ========== 子模块 ==========
        self.调度器 = 任务调度器(self)
        # self.进入器 = 步骤式地图进入器(self)
        
        self.页面 = 页面操作集(self)
       
        self.辅助识别器 = 战斗辅助识别器(self) 
       
        self.通用操作 = 通用操作集(self)
        
        self.聊天管理器 = 聊天管理器(self)

        
        self.强化奖励管理器 = 强化奖励管理器(
            窗口名称=self.窗口名称,
            游戏配置=self.游戏配置,
            动作执行器=self.动作执行器,
            页面=self.页面,
            通用操作=self.通用操作,
            辅助识别器=self.辅助识别器,
        )
       

        # ========== 运行控制 ==========
        self._运行中 = False
        self._停止标志 = False
        self._窗口无效计数 = 0
        self._最大无效次数 = 3
        # ========== 任务管理 ==========
        if 任务配置列表:
            self.加载任务配置(任务配置列表)
            调试器.info("任务", f"已加载{len(任务配置列表)}个任务")
            
        else:
            任务定义.导入配置从JSON(窗口名称)
            from tasks import 获取所有任务配置
            self.加载任务配置(获取所有任务配置())
            调试器.info("任务定义", f"已加载{len(获取所有任务配置())}个任务")

        #===================一些不公开的设置 ====================
        self.界面信息抽查间隔=3
        self.界面信息抽查时间=0
        self.特殊活动存在=False
        self.上次特殊活动检查时间=0
            
    def 暂停(self):
        self._暂停标志 = True
    
    def 恢复(self):
        self._暂停标志 = False 
    @property
    def 暂停中(self) -> bool:
        return self._暂停标志
    
    def _检查窗口有效性(self) -> bool:
        """检查窗口是否仍然有效"""
        import win32gui
        if not win32gui.IsWindow(self.窗口句柄):
            self._窗口无效计数 += 1
            if self._窗口无效计数 >= self._最大无效次数:
                调试器.error("线程", f"窗口 '{self.窗口名称}' 已关闭，中止线程")
                return False
            return True
        self._窗口无效计数 = 0
        return True
    # ==================== 截图管理 ====================
    
    def 刷新截图(self, 检测纯色: bool = True) -> Optional[np.ndarray]:
        """刷新当前截图，返回最新截图"""
        if not win32gui.IsWindow(self.窗口句柄):
            return None
        最大重试次数 = 2
        
        for 尝试次数 in range(最大重试次数):
            self.截图 = capture_window(self.窗口句柄, client_only=True)
            调试器.warning("截图", f"刷新截图(第{尝试次数+1}/{最大重试次数}次)")
            if self.截图 is None:
                调试器.warning("截图", f"截图失败(第{尝试次数+1}/{最大重试次数}次)，准备重试")
                time.sleep(0.05)
                continue
            
            if 检测纯色 and 是否是纯色截图(self.截图):
                调试器.warning("截图", f"检测到纯色截图(第{尝试次数+1}/{最大重试次数}次)，可能是加载画面，准备重试")
                time.sleep(0.05)
                continue
            
            # 截图成功，静默返回
            #================祖龙刷新监控放这里，避免漏掉=====================
            self._太古祖龙刷新监控()
            return self.截图
        
        调试器.error("截图", f"截图失败(已重试{最大重试次数}次)，无法获取有效截图")
        return None
    
    def _太古祖龙刷新监控(self) -> None:
        if self.游戏配置.玩家.启用通知消息 == False:
            return
        if self.游戏配置.玩家.发送太古祖龙刷新通知 == False: 
            return
        
        if self.游戏配置.玩家.上部信息框检查间隔 > time.time()-self.公共变量.上部信息框检查时间: 
            return
        截图=self.截图
        if 截图 is None: 
            截图=self.刷新截图 ()
        if 截图 is None: 
            return
        查询区域=self.游戏配置.区域.主界面.服务器喇叭文字显示区域标签.元组
        if not 查询区域 :   
           return
        颜色结果=self.像素分析器.count_colors(
            截图, 
            查询区域, 
            "00E4FF,0.95|FFFFFF,0.99"
        )
        if len(颜色结果) < 2:  
            调试器.debug("战斗助手", f"像素统计结果不足: {颜色结果}")
            return 
        if 颜色结果[0] < 10 or 颜色结果[1]<20:             
            return 
        filter_config = {
            "color_range": "115,255,80,235,0,10",  
            "color_diff": "5-160,255,160,255,160,255",
            "keep_color": True,
            "background": "black"
        }
        text=self.文字识别器.recognize_text(截图,查询区域,filter_config)
        if not text and len(text) < 5: return
        if 匹配分组关键字(text, "太古") :
            text=f"时间:{datetime.datetime.now().strftime("%H:%M:%S")} {text}"
            待核验文本 = self._祖龙聊天文字重置(text)
            队列 = self.公共变量.待发送聊天队列
            if 队列:
                最后一项 = 队列[-1].get("内容", "")
                去符号内容 = self._去除所有符号(待核验文本)
                去符号最后 = self._去除所有符号(最后一项)
                if 是否重复聊天内容(去符号内容, 去符号最后, 时间差阈值=3, 相似度阈值=0.85): 
                    调试器.debug("聊天管理器", "重复内容，跳过") 
                    return
                            
            self.公共变量.待发送聊天队列.append({
                "频道": "行会",
                "内容": 待核验文本,
                "添加时间": time.time()
            })
            return  
    
     
    def _祖龙聊天文字重置(self, 内容: str) -> str:
        """
        文字过滤/替换
        
        用于规避游戏敏感词屏蔽和去除无效内容
        """
        if not 内容:
            return ""
        
        内容 = 内容.replace("西", "晒")
        内容 = 内容.replace("|", "]")
        内容 = 内容.replace("文太古", "")
        内容 = 内容.replace("陨圣战场", "")
        内容 = 内容.replace("成功召唤出了", "召唤")
        内容 = 内容.replace("18", "1[8]")
        
        return 内容.strip()     
    
    def _去除所有符号(self, 文字: str) -> str:
        """
        去除所有符号，只保留中文、英文、数字
        
        用于去重比较，避免OCR识别误差导致的重复
        """
        import re
        if not 文字:
            return ""
        # 只保留中文字符、英文字母、数字
        return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', 文字)
    
    #=====================每日更新公会成员列表 ====================
    def _检查更新公会成员(self):
        """在盟重省且17-18点时更新公会成员"""
        # 条件1：地图是盟重省     
        
        # 条件2：17点到18点
        当前小时 = time.localtime().tm_hour
        if not (17 <= 当前小时 ):
            return
        
        # 条件3：今天还没更新过
        上次更新 = self.游戏配置.玩家.公会名单更新时间
        if 是否为今天(上次更新):
            return
        
        # 执行更新
        调试器.info("线程", "定时更新公会成员列表")
        self.辅助识别器.更新公会成员列表()

    # ==================== 地图管理 ====================
    
    def 识别地图(self) -> str:
        """
        识别当前地图，更新当前地图变量
        
        返回:
            识别到的地图名称
        """
        if self.截图 is None:
            return ""
        
        # 使用配置中的地图名称区域
        结果 = self.文字识别器.recognize_text(
            self.截图, 
            region=self.游戏配置.区域.主界面.小地图地图名显示标签.元组
        )
                
        if 结果:
            self.最后成功获取地图时间=time.time()
            旧地图 = self.当前地图
            self.当前地图 = 结果
            self.公共变量.当前地图名 = 结果
            if 旧地图 != 结果 and 结果:
                self.公共变量.地图切换时间=time.time()
                调试器.state("地图", f"地图切换: '{旧地图}' → '{结果}'")
        
        return self.当前地图
    
    # ==================== 任务管理（核心方法） ====================
    
    def 获取当前地图任务(self) -> Optional[object]:
        """
        根据当前地图名称，匹配对应的任务配置
        
        规则：
        1. 遍历任务排序列表
        2. 调用任务的 匹配地图() 方法
        3. 返回第一个匹配的任务
        
        返回:
            匹配的任务配置，None表示无匹配
        """
        if not self.当前地图:
            return None
        
        for 任务 in self.任务排序列表:
            if 任务.匹配地图(self.当前地图):
                调试器.state("调度", f"地图 '{self.当前地图}' 匹配到任务: {任务.任务名称}({任务.任务ID})")
                return 任务
        
        调试器.trace("调度", f"地图 '{self.当前地图}' 未匹配到任何任务")
        return None
    
    def 获取顺序列表最优先任务(self) -> Optional[object]:
        """
        从任务排序列表中，按优先级从高到低，
        找到第一个满足运行条件的任务
        
        检查条件：
        - 是否启用
        - 工作时间
        - 剩余次数
        - 刷新时间
        
        返回:
            满足条件的任务，None表示无任务可执行
        """
        for 任务 in self.任务排序列表:
            if self._检查任务可执行(任务):
                调试器.state("调度", f"选中任务: {任务.任务名称}({任务.任务ID}) 优先级={任务.优先级}")
                return 任务
        
        调试器.trace("调度", "当前无可用任务")
        return None
    
    # def _检查任务可执行(self, 任务) -> bool:
    #     """
    #     检查单个任务是否可执行
        
    #     检查项：
    #     - 是否启用
    #     - 工作时间
    #     - 剩余次数
    #     - 刷新时间
    #     """
    #     任务名 = f"{任务.任务名称}({任务.任务ID})"
        
    #     # 1. 是否启用
    #     if not getattr(任务, '是否启用', True):
    #         调试器.trace("调度", f"{任务名}: 未启用")
    #         return False
        
    #     # 2. 工作时间检查
    #     当前小时 = time.localtime().tm_hour
    #     开始 = getattr(任务, '工作时间开始', 0)
    #     结束 = getattr(任务, '工作时间结束', 24)
        
    #     if not (开始 <= 当前小时 < 结束):
    #         调试器.trace("调度", f"{任务名}: 不在工作时间({开始}:00-{结束}:00)，当前{当前小时}点")
    #         return False
        
    #     # 3. 剩余次数检查
    #     状态 = self.任务状态映射.get(任务.任务ID)
    #     if 状态:
    #         剩余次数 = getattr(状态, '剩余次数', 1)
    #         if 剩余次数 <= 0:
    #             调试器.trace("调度", f"{任务名}: 剩余次数不足(剩余{剩余次数})")
    #             return False
    #     else:
    #         # 无状态时，使用配置的每日次数
    #         每日次数 = getattr(任务, '每日次数', 1)
    #         if 每日次数 <= 0:
    #             调试器.trace("调度", f"{任务名}: 每日次数为0")
    #             return False
        
    #     # 4. 刷新时间检查（定时任务）
    #     if 状态 and hasattr(状态, '下次刷新时间') and 状态.下次刷新时间 > 0:
    #         提前秒数 = getattr(任务, '提前进场秒数', 0)
    #         当前时间 = time.time()
    #         if 当前时间 < 状态.下次刷新时间 - 提前秒数:
    #             剩余秒数 = int(状态.下次刷新时间 - 当前时间)
    #             调试器.trace("调度", f"{任务名}: 刷新时间未到(还需等待{剩余秒数}秒)")
    #             return False
        
    #     return True

    def _检查任务可执行(self, 任务) -> bool:
        if not getattr(任务, '是否启用', True):
            return False
        
        if not self._检查执行日期(任务):
            return False
        
        if not self._检查执行时间(任务):
            return False
        
        状态 = self.任务状态映射.get(任务.任务ID)
        self._刷新任务次数(任务, 状态)
        if self._获取剩余次数(任务, 状态) <= 0:
            return False
        
        if 状态 and hasattr(状态, '下次刷新时间') and 状态.下次刷新时间 > 0:
            提前秒数 = getattr(任务, '提前进场秒数', 0)
            if time.time() < 状态.下次刷新时间 - 提前秒数:
                return False
        
        return True
    
    

    # ==================== 执行日期检查 ====================  

    def _检查执行日期(self, 任务) -> bool:
        return self._检查执行日期规则(getattr(任务, '执行日期规则', ''))


    def _检查执行日期规则(self, 规则: str) -> bool:
        if not 规则:
            return True
        for 条件 in 规则.split('&'):
            if not self._检查单个日期条件(条件.strip()):
                return False
        return True


    def _检查单个日期条件(self, 条件: str) -> bool:
        if not 条件:
            return True
        
        today = datetime.date.today()
        星期 = today.isoweekday()
        日 = today.day
        
        if 条件.startswith("星期"):
            return str(星期) in 条件[2:].split(',')
        
        if 条件 == "日期单数日":
            return 日 % 2 == 1
        if 条件 == "日期双数日":
            return 日 % 2 == 0
        
        if 条件.startswith("日期") and 条件[2:].replace(',', '').replace(' ', '').isdigit():
            return str(日) in 条件[2:].split(',')
        
        if 条件.startswith("日期"):
            match = re_module.match(r'日期(\d+)-(\d+)$', 条件)
            if match:
                return int(match.group(1)) <= 日 <= int(match.group(2))
        
        if 条件.startswith("除星期"):
            排除列表 = [int(x.strip()) for x in 条件[3:].split(',')]
            return 星期 not in 排除列表
        
        return True


    # ========== 执行时间检查 ==========

    def _检查执行时间(self, 任务) -> bool:
        
        当前时分 = time.localtime().tm_hour * 60 + time.localtime().tm_min
        时间段列表 = getattr(任务, '工作时间段列表', '')
        
        if 时间段列表:
            return self._匹配多时段(当前时分, 时间段列表)
        
        开始 = getattr(任务, '工作时间开始', 0) * 60
        结束 = getattr(任务, '工作时间结束', 24) * 60
        return 开始 <= 当前时分 < 结束


    def _匹配多时段(self, 当前时分: int, 时间段列表: str) -> bool:
        for 段 in 时间段列表.split(','):
            段 = 段.strip()
            if '-' in 段:
                开始, 结束 = 段.split('-')
                if self._时分转分钟(开始.strip()) <= 当前时分 < self._时分转分钟(结束.strip()):
                    return True
        return False


    def _时分转分钟(self, 时间字符串: str) -> int:
        if ':' in 时间字符串:
            时, 分 = 时间字符串.split(':')
            return int(时) * 60 + int(分)
        return int(时间字符串) * 60


    # ========== 次数刷新 ==========

    def _刷新任务次数(self, 任务, 状态):
        if not 状态 or getattr(状态, '剩余次数', 0) > 0:
            return
        
        #不得不对宝库深处单列。
        if 任务.任务名称 == "宝库深处":
            if 任务.圣兽宝库完成时间=="" or 任务.圣兽宝库完成时间!=datetime.date.today().isoformat():
                return
        if self._是否到刷新时机(任务, 状态):
            状态.剩余次数 = 20
            状态.上次次数刷新时间 = time.time()


    def _是否到刷新时机(self, 任务, 状态) -> bool:
        当前时间 = time.time()
        上次刷新 = getattr(状态, '上次次数刷新时间', 0)
        
        # 每日刷新
        if getattr(任务, '任务类型', '') == "每日任务":
            if not 是否为今天(上次刷新):
                return True
        
        # 间隔刷新
        间隔 = getattr(任务, '次数刷新间隔小时', 0)
        if 间隔 > 0 and 当前时间 - 上次刷新 >= 间隔 * 3600:
            return True
        
        # 区间刷新
        区间列表 = getattr(任务, '次数刷新区间列表', '')
        if 区间列表:
            条件列表_str = getattr(任务, '次数刷新区间条件', '')
            区间数组 = [x.strip() for x in 区间列表.split(',') if x.strip()]
            条件数组 = [x.strip() for x in 条件列表_str.split('|')] if 条件列表_str else []
            当前时分 = time.localtime().tm_hour * 60 + time.localtime().tm_min
            
            for i, 区间 in enumerate(区间数组):
                if '-' not in 区间:
                    continue
                开始, 结束 = 区间.split('-')
                开始分 = self._时分转分钟(开始.strip())
                结束分 = self._时分转分钟(结束.strip())
                
                if 开始分 <= 当前时分 <= 结束分:
                    if self._该区间已刷新(状态, 开始分, 结束分):
                        continue
                    
                    条件 = 条件数组[i] if i < len(条件数组) else ""
                    if not 条件 or self._检查执行日期规则(条件):
                        return True
        
        return False


    def _该区间已刷新(self, 状态, 开始分: int, 结束分: int) -> bool:
        上次 = getattr(状态, '上次次数刷新时间', 0)
        if 上次 <= 0:
            return False
        if not 是否为今天(上次):  
           return False
        
        上次时分 = time.localtime(上次).tm_hour * 60 + time.localtime(上次).tm_min
        return 开始分 <= 上次时分 <= 结束分


    def _获取剩余次数(self, 任务, 状态) -> int:
        if 状态:
            return getattr(状态, '剩余次数', 1)
        return getattr(任务, '每日次数', 1)
    
    # ==================== 任务配置加载 ====================
    
    def 加载任务配置(self, 任务配置列表: List):
        """
        加载任务配置并排序
        
        参数:
            任务配置列表: 任务配置对象列表
        """
        # 按优先级排序（高优先级在前）
        self.任务排序列表 = sorted(
            任务配置列表,
            key=lambda t: getattr(t, '优先级', 0),
            reverse=True
        )
        
        调试器.info("配置", f"窗口 '{self.窗口名称}' 加载 {len(self.任务排序列表)} 个任务")
        for 任务 in self.任务排序列表:
            调试器.debug("配置", f"  {任务.任务名称}({任务.任务ID}) 优先级={任务.优先级} 每日={getattr(任务, '每日次数', '?')}次 地图='{任务.地图关键字}'")
    
    def 重新加载任务配置(self, 任务配置列表: List):
        """
        重新加载任务配置（UI修改后调用）
        
        参数:
            任务配置列表: 新的任务配置列表
        """
        调试器.info("配置", f"窗口 '{self.窗口名称}' 重新加载任务配置")
        self.加载任务配置(任务配置列表)
        # 重置调度器状态
        self.调度器.重置()
    
    def 获取静止时长(self) -> float:
        """
        根据画面是否有变化更新静止时间        
        获取当前静止时长（秒）
        返回:
            从最后一次画面变化到现在的秒数
        """
        截图 = self.截图
        if 截图 is None:
            return 0
        
        有变化 = self.公共变量.检测画面变化(截图, self.游戏配置.玩家.战斗.检测.静止检测点组)
        if 有变化:
            self.公共变量.静止开始时间 = time.time()
            return 0
        else:
            静止时长 = time.time() - self.公共变量.静止开始时间
            if 静止时长 > 5:
                调试器.verbose("战斗", f"画面静止中，持续 {静止时长:.1f} 秒")
            return 静止时长

    #========================按任务名称获取任务配置====================
    def 获取任务配置(self, 任务名称: str) :
        """按任务名称获取任务配置"""
        for 任务 in self.任务排序列表:
            if 任务.任务名称 == 任务名称:
                return 任务
        return None
   
    # ==================== 主循环 ====================
    
    def _主循环(self):
        """主循环"""
        调试器.info("线程", f"窗口 '{self.窗口名称}' 进入主循环 (句柄={self.窗口句柄})")
        循环计数 = 0
        循环结束时间 = time.time()
        # for 任务 in self.任务排序列表:
        #       调试器.info("线程",f"{任务.任务名称}: 地图关键字='{任务.地图关键字}'")
        while not self._停止标志:
            if not self._检查窗口有效性():
                break
            循环计数 += 1

            if self._暂停标志:
                time.sleep(1)
                continue
            if self._卡死检测():
               continue  # 刷新游戏后跳过本次循环
            # 1. 刷新截图
            if self.刷新截图() is None:
                time.sleep(0.5)
                continue
            
            # 2. 识别当前地图
            self.识别地图()
            调试器.trace("线程", f"第{循环计数}次循环 地图='{self.当前地图}'")           
            

            # 3. 定时更新公会成员（盟重省 + 17点开始 + 每日一次）
            if self.当前地图=="盟重省":
               self._检查更新公会成员()
               self.辅助识别器.检查并更新敌人面板()
               self.强化奖励管理器.检查并执行(True)
            #    self._盟重特殊任务()
            
            if self.界面信息抽查时间 +3<= time.time():
               #干点杂事
                右上提示区域= self.辅助识别器.查找图片单结果(self.游戏配置.区域.主界面.右上角关闭不在提示区域.元组,"下次不在提示右上.bmp")
                中间提示区域= self.辅助识别器.查找图片单结果(self.游戏配置.区域.主界面.中间关闭不在提示区域.元组,"不在提醒中间.bmp")
                if 中间提示区域:
                    self.通用操作.点击区域(中间提示区域)
                if 右上提示区域: 
                    self.通用操作.点击区域(右上提示区域)
                    time.sleep(self.游戏配置.默认等待秒)
                    self.页面.创建_通用点击文字验证文字切换(
                        self.游戏配置.区域.主界面.右上角关闭不在提示区域.元组,
                        "取|消",
                         self.游戏配置.区域.主界面.右上角关闭不在提示区域.元组,
                         "取|消",
                         False,
                    ).执行()
                # 检查炼妖炉
                if self.辅助识别器.查找图片单结果(self.游戏配置.区域.图鉴强化.炼妖炉完成提示区域标签.元组,"炼妖炉.bmp"):
                    
                    for 任务 in self.强化奖励管理器.任务实例列表:
                        if 任务.任务ID == "lianyaolu":
                            任务.下次执行时间 = time.time() 
                            break

                self.界面信息抽查时间 = time.time() 
            # print(self.辅助识别器.敌人面板有敌人())

            # time.sleep(1)
            # continue 

            # 3. 检查静止时长
            静止时长 = self.获取静止时长()

            self.聊天管理器.处理发送队列()


            # 4. 执行调度
            结果 = self.调度器.调度一次()
            if 结果:
                调试器.debug("调度", f"调度完成: {结果}")
            
            # 5. 控制循环频率
            耗时 = time.time() - 循环结束时间
            调试器.verbose("线程", f"第{循环计数}次循环 耗时{耗时*1000:.0f}ms 静止{静止时长:.1f}s")
            time.sleep(self.游戏配置.战斗.等待.主循环间隔秒)
            循环结束时间 = time.time()
    
    def _盟重特殊任务(self):
        #特殊活动的检查更新
        现在 = datetime.datetime.now()
        分钟= 现在.minute
        小时= 现在.hour
        #避免服务器和本地时间误差和延迟导致失败
        if 分钟> 2:
            if not 是否为今天(self.上次特殊活动检查时间):
                self._检查特殊任务今天是否刷新()
        if 小时==0 and 分钟<= 2:
            self.特殊活动存在 = False
           
        


        pass
    def _检查特殊任务今天是否刷新(self):
        """检查更新"""
        if self.页面.创建_通用点击图片验证文字切换(
            self.游戏配置.区域.主界面.第一排任务区域标签.元组,
            "活动图标.bmp",
             self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
             "开服|活动",
        ).执行():
            图片坐标=self.辅助识别器.查找图片多结果(self.游戏配置.区域.各种活动.开服活动右侧小标签红点检查区域.元组,"红点1.bmp")
            if 图片坐标:
                for 坐标 in 图片坐标: 
                    校正坐标=坐标[0]-15,坐标[1]+15,坐标[0]+3,坐标[1]+45
                    self.通用操作.点击区域(校正坐标,2)
                    time.sleep(self.游戏配置.默认等待秒*2)
                    self.刷新截图()
                    表头文字=self.辅助识别器.获取区域文字(self.游戏配置.区域.主界面.中间页面名称区域标签.元组)
                    if 匹配分组关键字(表头文字,"祈|愿"):
                        #.....
                        self.上次特殊活动检查时间 = time.time()                        
                        self.特殊活动存在 = True

    def run(self):
        """线程入口"""
        

        self._运行中 = True
        self.信号.启动信号.emit(self.窗口名称)
        调试器.info("线程", f"窗口线程启动: {self.窗口名称} (句柄={self.窗口句柄})")
        try:
            初始化线程日志(self.窗口名称)
            self._主循环()
        except Exception as e:
            调试器.error("线程", f"窗口 '{self.窗口名称}' 发生异常: {e}")
            import traceback
            调试器.error("线程", f"异常堆栈:\n{traceback.format_exc()}")
        finally:
            self._运行中 = False
            self.信号.停止信号.emit(self.窗口名称)
            调试器.info("线程", f"窗口线程停止: {self.窗口名称} (句柄={self.窗口句柄})")
            # 关闭线程日志
            关闭线程日志()
    
    def stop(self):
        """停止线程"""
        调试器.info("线程", f"窗口 '{self.窗口名称}' 收到停止信号")
        self._停止标志 = True
    
    @property
    def 运行中(self) -> bool:
        return self._运行中
    

    #=======================掉线检查 ======================
    def _卡死检测(self) -> bool:
        """
        检测卡死情况，返回 True 表示已刷新游戏
        """
        # ===== 检测1: 主城死亡 =====
        if self.主城死亡:
            self._检测主城死亡()
            调试器.state("卡死检测", "主城死亡，刷新游戏")
            self.主城死亡= False
            self._刷新游戏(重置次数=False)            
            return True
        
        # ===== 检测2: 超长静止 =====
        if self.公共变量.获取静止时长() > 600:
            复查情况=self._复核_检查主宰页面是否掉线()
            if 复查情况 is False:
                调试器.trace("卡死检测", "静止超时复核通过，未卡死")
                self.公共变量.重置静止时间()
            else:
                调试器.state("卡死检测", "静止超时卡死，刷新游戏")
                return  self._根据复查情况选择刷新路径(复查情况)
        
        # ===== 检测3: 超长无目标 =====
        if  self.公共变量.获取无目标时间() > 120:
            复查情况=self._复核_检查主宰页面是否掉线()
            if 复查情况 is False:
                调试器.trace("卡死检测", "无目标超时复核通过，未卡死")
                self.公共变量.重置目标状态()
            else:
                调试器.state("卡死检测", "无目标超时卡死，刷新游戏")
                return  self._根据复查情况选择刷新路径(复查情况)
        
        # ===== 检测4: 无地图识别 =====
        if self.当前地图 == "" and time.time()- self.最后成功获取地图时间 > 25:
            复查情况=self._复核_检查主宰页面是否掉线()
            if 复查情况 is False:
                调试器.trace("卡死检测", "无地图复核通过，未卡死")                
            else:
                调试器.state("卡死检测", "无地图卡死，刷新游戏")
                return  self._根据复查情况选择刷新路径(复查情况)
        
        return False


    def _检测主城死亡(self) -> bool:
        """检测主城死亡：在盟重省且检测到死亡面板"""
        if self.当前地图 != "盟重省":
            return False
        
        # 检查是否有死亡面板
        区域= self.辅助识别器.获取复活按钮区域() 
        if 区域 is None:
            return False
        if 区域:
            return True
        return False

    def _根据复查情况选择刷新路径(self,复查情况):
        if 复查情况 is None:
            if self.页面.创建点击文字操作(self.游戏配置.区域.掉线检查.掉线刷新游戏按钮区域标签.元组, "刷|新"):
                time.sleep(2)
                self.刷新截图()
                self._处理游戏加载弹窗()
                
                # 等待游戏加载完成
                time.sleep(2)
                self.刷新截图()
                self.识别地图()
                
                # 重置次数                
                self._重置卡死相关任务次数()                
                调试器.info("卡死检测", "掉线，游戏刷新完成")
                return True
        self._刷新游戏(重置次数=True)
        return True
    def _复核_检查主宰页面是否掉线(self) -> Optional[bool]:
        """
        复核：打开主宰页面检查是否能获取次数
        返回 True 表示已掉线
        """
        try:
            # 尝试打开主宰页面获取次数
            截图 = self.刷新截图()
            if 截图 is None:
                return None
            
            if not self.页面.主界面操作.进入跨服战场页面():
                调试器.debug("掉线检查", "进入跨服战场页面失败，入口逻辑中断")
                return None
        
            if not self.页面.跨服战场.主宰.进入主宰战场页面():    
                调试器.debug("掉线检查",  "进入主宰页面失败")
                return None
            
            # 等待刷新时间，强制等待服务器时间同步
            time.sleep(max(0.5, self.游戏配置.刷新等待秒))
            截图 =self.刷新截图()       
            if 截图 is None:
                return None
            数量文字= self.文字识别器.recognize_text(截图,self.游戏配置.区域.主宰.主宰综合信息页面主宰数量区域标签.元组)
            信息文字= self.文字识别器.recognize_text(截图,self.游戏配置.区域.主宰.主宰综合信息页面最强玩家区域标签.元组)
            if len(数量文字)>0 or len(信息文字)>0:
                调试器.debug("掉线检查", f"读取主宰成功，未掉线")
                return False
            调试器.debug("掉线检查", f"读取主宰数量失败")
            return True
        except:
            return None
        
    #======================= 刷新游戏 ======================
    def _刷新游戏(self, 重置次数: bool = False):
        """
        刷新游戏流程
        
        参数:
            重置次数: True=重置主宰、预言圣殿、失落圣殿、神界巅峰次数为1
        """
        from core.foreground_lock import 前台锁
        
        调试器.info("卡死检测", "开始刷新游戏")
        
        # ===== 申请前台操作权限 =====
        if not 前台锁.申请(self.窗口名称, 超时=10):
            调试器.warning("卡死检测", "无法获得前台操作权限，跳过刷新")
            time.sleep(3)
            return
        
        try:
            # ===== 前台操作：激活窗口 + F5 + 点重新加载 =====
            hwnd = self.窗口句柄
            
            # 找到顶层父窗口
            父窗口 = hwnd
            while True:
                上级 = win32gui.GetParent(父窗口)
                if 上级 == 0:
                    break
                父窗口 = 上级
            
            # 置顶并点击激活
            win32gui.SetForegroundWindow(父窗口)
            time.sleep(0.3)
            
            rect = win32gui.GetWindowRect(父窗口)
            x = (rect[0] + rect[2]) // 2
            y = (rect[1] + rect[3]) // 2
            win32api.SetCursorPos((x, y))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.1)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(0.3)
            
            # F5 刷新
            win32api.keybd_event(0x74, 0, 0, 0)
            time.sleep(0.1)
            win32api.keybd_event(0x74, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(1)
            
            # 截图找"重新加载"
            self.刷新截图()
            截图 = self.截图
            
            if 截图 is not None:
                文字结果 = self.文字识别器.recognize_result(截图, None)
                if 文字结果:
                    重新加载坐标 = 文字结果.find("重新加载|重,加载|新加载", match_type="group")
                    if 重新加载坐标:
                        cx = (重新加载坐标[0] + 重新加载坐标[2]) // 2
                        cy = (重新加载坐标[1] + 重新加载坐标[3]) // 2
                        win32api.SetCursorPos((cx, cy))
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                        time.sleep(0.1)
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    else:
                        # 没找到，按回车
                        win32api.keybd_event(0x0D, 0, 0, 0)
                        time.sleep(0.1)
                        win32api.keybd_event(0x0D, 0, win32con.KEYEVENTF_KEYUP, 0)
        
        finally:
            # ===== 释放前台操作权限 =====
            前台锁.释放(self.窗口名称)
        
        # ===== 后台操作：等待加载 + 处理弹窗 + 进入游戏 =====
        time.sleep(2)
        self.刷新截图()
        self._处理游戏加载弹窗()
        
        # 等待游戏加载完成
        time.sleep(2)
        self.刷新截图()
        self.识别地图()
        
        # 重置次数
        if 重置次数:
            self._重置卡死相关任务次数()
        
        调试器.info("卡死检测", "游戏刷新完成")


    def _处理游戏加载弹窗(self):
        """处理游戏加载过程中的各种弹窗"""
        for _ in range(20):
            time.sleep(1)
            截图 = self.刷新截图()
            if 截图 is None:
                time.sleep(1)
                self.刷新截图()
                continue
            
            if  self.页面.创建点击文字操作(
                  self.游戏配置.区域.掉线检查.登录界面开始按钮区域标签.元组,
                 "开,始").执行():
                time.sleep(1)
                self.刷新截图()
                self.最后成功获取地图时间= time.time()
                continue
            if  self.辅助识别器.区域包含文字(
                self.游戏配置.区域.掉线检查.登录后提示区域标签.元组,
                 "高端版本"
               ):
                if self.页面.创建点击文字操作(
                  self.游戏配置.区域.掉线检查.登录后确认按钮区域标签.元组,
                 "确|认").执行():
                    time.sleep(1)
                    self.刷新截图()
                    self.最后成功获取地图时间= time.time()
                    break
                self.最后成功获取地图时间= time.time()
                continue
            if  len(self.辅助识别器.获取区域文字(
                self.游戏配置.区域.主界面.小地图地图名显示标签.元组))>1:
                self.最后成功获取地图时间= time.time()
                break

      


    def _重置卡死相关任务次数(self):
        """重置相关任务次数为1"""
        需要重置的任务ID列表 = [
            "zhuzaizhanchang",
            "yuyanshengdian", 
            "shiluoshengdian",
            "shenjiezhidian"
        ]
        
        for 任务ID in 需要重置的任务ID列表:
            if 任务ID in self.任务状态映射:
                self.任务状态映射[任务ID].剩余次数 = 1
                调试器.debug("卡死检测", f"重置 {任务ID} 次数=1")