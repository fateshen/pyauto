# models/battle_config.py
"""
战斗配置模块 - 管理战斗相关的参数配置

设计原则：
1. 游戏配置：所有任务共享的通用配置
2. 任务配置：每个任务可覆盖的配置（继承全局配置）
3. 区域配置：统一从全局区域配置获取，不在此处定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Tuple
from core.debug import 调试器


# ==================== 全局战斗检测配置 ====================

class 战斗检测配置(BaseModel):
    """
    战斗检测配置（全局统一）
    
    用于检测血条面板，所有任务通用
    """
    # 自动战斗检测像素规则
    自动战斗像素规则: str = "F3FFFF,0.98|E8FFFF,0.98|D0D5DA,0.98"   

    # 自动走位检测像素规则
    自动走位像素规则: str = "F3FFFF,0.98|E8FFFF,0.98|4c95b6,0.98|3F87A9,0.98"

    # 目标存在像素规则
    # 格式: "颜色1,相似度|颜色2,相似度"
    目标存在像素规则: str = "74B7D1,0.98|E7E6E7,0.98"
    
    # 目标检测阈值（像素数量超过此值认为目标存在）
    目标检测阈值: int = 10
    
    # 小地图安全区像素规则
    小地图安全区检查像素规则: str = "06EF28,0.98|0005FF,0.98"

    启用回城回血: bool=False              # 是否启用低血量回城
    回城血量阈值: int =30                 # 血量低于此百分比触发回城

    # 静止检测点
    # 格式: "x,y|x,y|x,y"
    静止检测点: str = "10,460|1535,90|271,8"
    静止检测点组: List[Tuple[int, int]]=Field(default_factory=list, exclude=True)    

    class Config:
        arbitrary_types_allowed = True
    def __init__(self, **data):
        super().__init__(**data)
        if self.静止检测点:
            self.静止检测点组 = self.解析静止检测点()
    def 解析像素规则(self) -> List[Tuple[str, float]]:
        """解析目标存在像素规则"""
        if not self.目标存在像素规则:
            return []
        
        结果 = []
        for 部分 in self.目标存在像素规则.split('|'):
            部分 = 部分.strip()
            if ',' in 部分:
                颜色, 相似度 = 部分.split(',')
                结果.append((颜色.strip(), float(相似度.strip())))
        
        return 结果
    
    def 解析静止检测点(self) -> List[Tuple[int, int]]:
        """解析静止检测点"""
        if not self.静止检测点:
            return []
        
        结果 = []
        for 点 in self.静止检测点.split('|'):
            点 = 点.strip()
            if ',' in 点:
                x_str, y_str = 点.split(',')
                try:
                    结果.append((int(x_str), int(y_str)))
                except ValueError:
                    pass
        
        return 结果
    def 静止点应用偏移(self, offset_x: int, offset_y: int) -> None:
        """应用窗口偏移"""
        
        原始点组 = self.解析静止检测点()
        self.静止检测点组 = [(x + offset_x, y + offset_y) for x, y in 原始点组]

# ==================== 全局超时配置 ====================

class 超时配置(BaseModel):
    """
    超时配置（全局统一）
    """
    
    # 战斗相关超时
    无目标超时秒数: float = 3.0      # 无目标超过此时间视为战斗结束条件之一
    静止超时秒数: float = 3.0        # 画面静止超过此时间视为战斗结束条件之一
    开战超时秒数: float = 3.0        # 开战后超过此时间，方检查无目标和静止状态
    
    # 页面切换超时
    页面切换超时秒数: float = 10.0    # 页面切换最大等待时间
    等待进入副本超时秒数: float = 10.0  # 等待进入副本最大时间
    
    # 截图超时
    截图超时秒数: float = 5.0         # 截图失败重试超时
    
    # 任务执行超时
    任务执行超时秒数: float = 300.0   # 单个任务最大执行时间


# ==================== 全局等待配置 ====================

class 等待配置(BaseModel):
    """
    等待时间配置（全局统一）
    """
    
    # 基础等待（毫秒）
    默认等待毫秒: int = 300
    短等待毫秒: int = 100
    长等待毫秒: int = 1000
    超长等待毫秒: int = 3000
    
    # 操作间隔（秒）
    点击后等待秒: float = 0.05
    按键后等待秒: float = 0.05
    拖拽后等待秒: float = 0.1
    
    # 循环间隔（秒）
    主循环间隔秒: float = 1.0
    检测间隔秒: float = 0.5
    刷新等待秒: float = 1.2
    
    @property
    def 默认等待秒(self) -> float:
        return self.默认等待毫秒 / 1000
    
    @property
    def 短等待秒(self) -> float:
        return self.短等待毫秒 / 1000
    
    @property
    def 长等待秒(self) -> float:
        return self.长等待毫秒 / 1000
    
    @property
    def 超长等待秒(self) -> float:
        return self.超长等待毫秒 / 1000


# ==================== 全局复活配置 ====================

class 复活配置(BaseModel):
    """
    复活配置（全局统一）
    """
  
    启用高战避让模式: bool=False             # 是否启用避让模式
    启用高频死亡避让模式: bool=False
    避让杀手名单: str=""                # 用|分隔的杀手名字
    高频死亡避让秒数: int =60            # 倒数第3次死亡距今 < N秒触发避让
    高频死亡避让次数: int = 3
    避让冷却秒数: int =180                # 避让后冷却秒数
    

# ==================== 全局重试配置 ====================

class 重试配置(BaseModel):
    """
    重试配置（全局默认，任务可覆盖）
    """
    
    # 默认重试次数
    最大重试次数: int = 3
    
    # 默认重试延迟（毫秒）
    重试延迟毫秒: int = 300
    
    def 计算重试延迟(self, 尝试次数: int) -> float:
        """
        计算重试延迟（秒）
        
        参数:
            尝试次数: 当前是第几次重试（从0开始）
        
        返回:
            延迟秒数
        """
        import random
        
        # 基础延迟
        延迟 = self.重试延迟毫秒 / 1000
        
        # 递增延迟：每次重试增加基础延迟
        延迟 = 延迟 + (尝试次数 * 延迟)
        
        # 添加随机偏移（±20%）
        偏移 = 延迟 * 0.2
        延迟 += random.uniform(-偏移, 偏移)
        
        return max(0.1, 延迟)  # 最小0.1秒

# ==================== 全局自动战斗配置 ====================

class 自动战斗配置(BaseModel):
    """
    自动战斗配置（全局默认，任务可覆盖）
    
    区域配置统一从全局区域配置获取
    """
    
    # 是否启用自动战斗
    启用自动战斗: bool = True
    
    # 是否启用自动走位
    启用自动走位: bool = True

# ==================== 全局战斗配置（整合） ====================

class 战斗配置(BaseModel):
    """
    战斗配置 - 整合所有战斗相关配置
    
    使用方式：
        # 创建全局配置
        全局配置 = 战斗配置.创建默认()
        
        # 创建任务配置（覆盖部分值）
        任务配置 = 战斗配置.创建任务配置(
            重试=任务重试配置(最大重试次数=5),
            自动战斗=任务自动战斗配置(启用自动战斗=False)
        )
    """
    
    # 全局统一配置（不可覆盖）
    检测: 战斗检测配置 = Field(default_factory=战斗检测配置)
    超时: 超时配置 = Field(default_factory=超时配置)
    等待: 等待配置 = Field(default_factory=等待配置)
    复活: 复活配置 = Field(default_factory=复活配置)
    
    # 全局默认配置（任务可覆盖）
    重试: 重试配置 = Field(default_factory=重试配置)
    自动战斗: 自动战斗配置 = Field(default_factory=自动战斗配置)
    
    class Config:
        arbitrary_types_allowed = True
    
    # ==================== 工厂方法 ====================
    
    @classmethod
    def 创建默认(cls) -> '战斗配置':
        """创建默认战斗配置"""
        return cls()
    
     
    # ==================== 快捷方法 ====================
    
    @property
    def 目标存在像素规则(self) -> str:
        return self.检测.目标存在像素规则
    
    @property
    def 静止检测点(self) -> str:
        return self.检测.静止检测点
    
    @property
    def 无目标超时秒数(self) -> float:
        return self.超时.无目标超时秒数
    
    @property
    def 静止超时秒数(self) -> float:
        return self.超时.静止超时秒数
    
    @property
    def 默认等待秒(self) -> float:
        return self.等待.默认等待秒
        
    def 短等待(self) -> float:
        return self.等待.短等待秒
    
    def 长等待(self) -> float:
        return self.等待.长等待秒
    
    # ==================== 打印方法 ====================
    
    def 打印所有配置(self):
        """打印所有战斗配置（使用日志输出）"""
        调试器.info("战斗配置", "=" * 60)
        调试器.info("战斗配置", "战斗配置列表")
        调试器.info("战斗配置", "=" * 60)
        
        调试器.info("战斗配置", "[战斗检测配置]（全局统一）")
        调试器.debug("战斗配置", f"  目标存在像素规则: {self.检测.目标存在像素规则}")
        调试器.debug("战斗配置", f"  目标检测阈值: {self.检测.目标检测阈值}")
        调试器.debug("战斗配置", f"  静止检测点: {self.检测.静止检测点}")
        
        调试器.info("战斗配置", "[超时配置]（全局统一）")
        调试器.debug("战斗配置", f"  无目标超时: {self.超时.无目标超时秒数}秒")
        调试器.debug("战斗配置", f"  静止超时: {self.超时.静止超时秒数}秒")
        调试器.debug("战斗配置", f"  开战超时: {self.超时.开战超时秒数}秒")
        调试器.debug("战斗配置", f"  页面切换超时: {self.超时.页面切换超时秒数}秒")
        调试器.debug("战斗配置", f"  等待进入副本超时: {self.超时.等待进入副本超时秒数}秒")
        
        调试器.info("战斗配置", "[等待配置]（全局统一）")
        调试器.debug("战斗配置", f"  默认等待: {self.等待.默认等待毫秒}ms")
        调试器.debug("战斗配置", f"  短等待: {self.等待.短等待毫秒}ms")
        调试器.debug("战斗配置", f"  长等待: {self.等待.长等待毫秒}ms")
        调试器.debug("战斗配置", f"  主循环间隔: {self.等待.主循环间隔秒}秒")        
       
        
        调试器.info("战斗配置", "[重试配置]（全局默认）")
        调试器.debug("战斗配置", f"  最大重试次数: {self.重试.最大重试次数}")
        调试器.debug("战斗配置", f"  重试延迟: {self.重试.重试延迟毫秒}ms")
        
        调试器.info("战斗配置", "[自动战斗配置]（全局默认）")
        调试器.debug("战斗配置", f"  启用自动战斗: {self.自动战斗.启用自动战斗}")
        调试器.debug("战斗配置", f"  启用自动走位: {self.自动战斗.启用自动走位}")
        调试器.info("战斗配置", "=" * 60)