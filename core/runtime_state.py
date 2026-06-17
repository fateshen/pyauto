# core/runtime_state.py
"""
运行时公共变量 - 存储当前线程的运行时状态

功能：
1. 静止检测（基于配置的静止检测点）
2. 目标检测（基于配置的像素规则）
3. 战斗状态管理（无目标持续时间）
4. 任务状态管理（当前任务ID、复活次数等）

依赖：
- models.game_config (全局配置)
"""
import time
from typing import Tuple, Optional,List
from dataclasses import dataclass, field
import numpy as np
from core.debug import 调试器


@dataclass
class 运行时公共变量:
    """
    运行时公共变量容器
    
    存储当前线程的运行时状态，所有任务共享
    """
    
    # ========== 静止检测 ==========
    
    # 静止开始时间（时间戳）
    静止开始时间: float = field(default_factory=time.time)
    
    # ========== 目标检测 ==========
    
    # 最后一次检测到目标的时间（时间戳）
    最后一次有目标时间: float = field(default_factory=time.time)
    
    # ========== 战斗状态 ==========
    
    # 当前怪物血量（百分比，0-100）
    当前怪物血量: int = 100
    
    # 当前玩家血量（百分比，0-100）
    当前玩家血量: int = 100
    
    # ========== 任务状态 ==========
    
    # 当前任务ID
    当前任务ID: str = ""
    当前地图名: str = ""
    地图切换时间: float = field(default_factory=time.time)
    # 任务内复活次数
    任务内复活次数: int = 0

    # 任务切换时间
    任务切换时间: float = field(default_factory=time.time)

    # ========== 抢怪相关 ==========
    是否有敌人:bool=False
    抢怪开始:bool=False

    # ========== 目标死亡时间估算 ==========
    # 血量记录（只记录最大和最小）
    记录最大血量: int = 0
    记录最大血量时间: float = 0
    记录最小血量: int = 100
    记录最小血量时间: float = 0
    目标预计死亡时间: float = 0.0  # 目标预计死亡的时间戳，0=未设置

    任务可能结束时间:float=0.0 #检查后如果任务可能结束，目标可能死亡，记录此时间
    # 无敌状态    
    无敌开始时间: float = 0
    
    # 战斗标记
    当前战斗怪物标识: str = ""  # 用于判断怪物是否切换
    # ========== 死亡记录 ==========
    死亡时间列表: List[float] = field(default_factory=list)  # 死亡时间戳列表（最多10条）
    死亡地图名: str = ""                                      # 最后死亡的地图名
    死亡杀手名: str = ""                                      # 最后死亡的杀手名
    最大死亡记录数: int = 10                                   # 最大记录条数
    # ========== 私有缓存 ==========
    
    # 上一帧像素缓存（用于静止检测）
    _上一帧像素: dict = field(default_factory=dict, repr=False, compare=False)
    
     # ========== 召唤响应 ==========
    上次召唤检查时间: float = 0.0

    # ========== 攻击模式核验 ==========
    本次攻击模式核验时间: float = 0.0
 
    # ========== 聊天系统 ==========
    # 待发送聊天队列 [{"频道": "行会", "内容": "xxx", "添加时间": 时间戳}, ...]
    待发送聊天队列: List[dict] = field(default_factory=list)
    
    # 上次聊天发送时间戳（控制10秒间隔）
    上次聊天发送时间: float = 0.0

    # 上部信息框检查时间,检查祖龙刷新用
    上部信息框检查时间: float = 0.0
    

    
    # ========== 静止检测方法 ==========
    
    def 重置静止时间(self):
        """重置静止开始时间为当前时间"""
        self.静止开始时间 = time.time()
    
    def 更新静止时间(self, 画面有变化: bool):
        """
        根据画面是否有变化更新静止时间
        
        参数:
            画面有变化: True=画面有变化，False=画面静止
        """
        if 画面有变化:
            self.静止开始时间 = time.time()
    
    def 获取静止时长(self) -> float:
        """
        获取当前静止时长（秒）
        不主动更新，请使用检测画面变化和更新静止时间方法
        返回:
            从最后一次画面变化到现在的秒数
        """
        return time.time() - self.静止开始时间
    
    def 检测画面变化(self, 截图: np.ndarray, 静止检测点组: List[Tuple[int, int]]) -> bool:
        """
        检测画面是否变化（基于配置的静止检测点）
        
        参数:
            截图: numpy 数组 (BGR格式)
            静止检测点组: 静止检测点配置列表 [(x,y), ...]
        
        返回:
            True: 画面有变化
            False: 画面无变化或截图无效
        """
        if 截图 is None:
            return False
        
        点列表 = 静止检测点组
        if not 点列表:
            return False
        
        h, w = 截图.shape[:2]
        
        # 记录当前帧的像素值
        当前像素 = {}
        for x, y in 点列表:
            if 0 <= x < w and 0 <= y < h:
                当前像素[(x, y)] = tuple(截图[y, x])  # OpenCV是 (y, x)
        
        if not 当前像素:
            return False
        
        # 与上一帧比较
        if not self._上一帧像素:
            self._上一帧像素 = 当前像素
            return True  # 第一帧视为有变化
        
        有变化 = False
        for 点, 颜色 in 当前像素.items():
            if 点 in self._上一帧像素:
                if 颜色 != self._上一帧像素[点]:
                    有变化 = True
                    break
            else:
                有变化 = True
                break
        
        # 更新缓存
        self._上一帧像素 = 当前像素
        
        return 有变化
   
    
    def 更新目标状态(self, 有目标: bool, 当前时间: float = None):
        """
        更新目标状态
        
        参数:
            有目标: 是否存在目标
            当前时间: 当前时间戳（默认使用time.time()）
        """
        if 当前时间 is None:
            当前时间 = time.time()
        
        if 有目标:
            self.最后一次有目标时间 = 当前时间
    
    def 获取无目标时间(self, 当前时间: float = None) -> float:
        """
        获取无目标持续时间（秒）
        
        参数:
            当前时间: 当前时间戳（默认使用time.time()）
        
        返回:
            从最后一次有目标到现在的秒数
        """
        if 当前时间 is None:
            当前时间 = time.time()
        
        return 当前时间 - self.最后一次有目标时间
    
    def 重置目标状态(self):
        """重置目标检测状态"""
        self.最后一次有目标时间 = time.time()
    
    # ==================== 目标死亡时间估算方法 ====================
    def _重置血量记录(self):
        """重置血量记录"""
        self.记录最大血量 = 0
        self.记录最大血量时间 = 0
        self.记录最小血量 = 100
        self.记录最小血量时间 = 0
    
    def _重置无敌状态(self):
        """重置无敌状态"""       
        self.无敌开始时间 = 0
    
    def 重置战斗估算(self):
        """重置所有战斗估算相关状态"""
        self.目标预计死亡时间 = 0.0
        self._重置血量记录()
        self._重置无敌状态()
        self.当前战斗怪物标识 = ""

    # ==================== 抢怪相关方法 ====================
    def 重置抢怪参数(self):
        """      
        """
        self.是否有敌人 = False
        self.抢怪开始=False


    # ==================== 死亡记录方法 ====================

    def 记录死亡(self, 杀手名: str = ""):
        """
        记录一次死亡
        
        参数:
            杀手名: 击杀者的名字（可选）
        """
        当前时间 = time.time()
        
        # 如果地图名变化，清空所有记录
        if self.当前地图名 != self.死亡地图名:
            self.死亡地图名 = self.当前地图名
            self.死亡时间列表.clear()
              
        # 将新记录插入到最前面（索引0）
        self.死亡时间列表.insert(0, 当前时间)
        
        # 记录杀手名字
        self.死亡杀手名 = 杀手名
    def 获取第N次死亡时间(self, n: int) -> float:
        """
        获取离现在最近的第N次死亡时间
        
        参数:
            n: 第几次（1=最近一次死亡，2=上一次死亡，以此类推）
        
        返回:
            死亡时间戳，如果不存在返回 -1
        """
        # 防御性检查1：参数类型和范围
        if not isinstance(n, int):
            return -1
        if n < 1:
            return -1
        
        索引 = n - 1
        列表长度 = len(self.死亡时间列表)
        
        # 防御性检查2：索引边界
        if 索引 >= 列表长度:
            return -1
        
        # 安全访问
        return self.死亡时间列表[索引]
    def 获取死亡间隔(self, n: int = 1) -> float:
        """
        获取距离第N次死亡过去了多少秒
        
        参数:
            n: 第几次（1=最近一次）
        
        返回:
            间隔秒数，如果没有死亡记录返回 -1
        """
        import time
        死亡时间 = self.获取第N次死亡时间(n)
        if 死亡时间 == -1:
            return -1
        return time.time() - 死亡时间
    def 清空死亡记录(self):
        """清空所有死亡记录（切换任务时调用）"""
        self.死亡时间列表.clear()
        self.死亡地图名 = ""
        self.死亡杀手名 = ""
    # ========== 任务状态方法 ==========
    
    def 重置任务状态(self):
        """重置任务相关状态（切换任务时调用）"""
        self.当前任务ID = ""
        self.任务内复活次数 = 0
        self.清空死亡记录()   
        self.重置战斗估算()
        self.重置抢怪参数()
    
    def 设置当前任务(self, 任务ID: str):
        """
        设置当前任务ID
        
        参数:
            任务ID: 任务标识
        """
        self.当前任务ID = 任务ID
        self.任务切换时间 = time.time()
    
    def 增加复活次数(self):
        """增加复活次数计数"""
        self.任务内复活次数 += 1
    
    # ========== 静止检测点设置 ==========
    
    def 重置画面缓存(self):
        """重置画面变化检测缓存"""
        self._上一帧像素.clear()
    
    # ========== 调试方法 ==========
    
    def 打印状态(self):
        """打印当前运行时状态（调试用）"""
        调试器.info("运行时", "=" * 50)
        调试器.info("运行时", "运行时状态")
        调试器.info("运行时", "=" * 50)
        调试器.debug("运行时", f"  当前任务ID: {self.当前任务ID}")
        调试器.debug("运行时", f"  静止时长: {self.获取静止时长():.1f}秒")
        调试器.debug("运行时", f"  无目标时间: {self.获取无目标时间():.1f}秒")
        调试器.debug("运行时", f"  怪物血量: {self.当前怪物血量}%")
        调试器.debug("运行时", f"  玩家血量: {self.当前玩家血量}%")
        调试器.debug("运行时", f"  复活次数: {self.任务内复活次数}")
        调试器.info("运行时", "=" * 50)
    
    def 重置所有(self):
        """重置所有状态（线程重启时调用）"""
        self.重置任务状态()
        self.重置画面缓存()