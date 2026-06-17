# models/game_config.py
"""
游戏全局配置 - 整合所有配置模块

注意：此类不再是单例，每个窗口线程应创建自己的实例
"""
from typing import Optional, Any,List,Tuple
from pydantic import BaseModel, Field
import json
from pathlib import Path

from rich.repr import T
from core.path_manager import path_mgr
from core.debug import 调试器
from .region_config import 区域配置, 区域坐标
from .battle_config import 战斗配置

class 玩家配置(BaseModel):
    """
    玩家配置 - 每个窗口独立
    
    包括：窗口名称、游戏标题、窗口偏移、战斗参数等
    """
    
    # 窗口标识
    窗口名称: str = "游戏1"
    
    # 游戏基本信息
    游戏标题: str = "上古"
    游戏分辨率: tuple = (1700, 884)
    
    # 窗口偏移（解决窗口边框问题）
    窗口偏移X: int = 0
    窗口偏移Y: int = 0    
    
    # ========== 玩家信息 ==========
    玩家角色名称: str = ""           # 玩家角色名（空则自动识别）
    玩家角色名称更新时间: float = 0.0
    玩家公会名称: str = ""
    服务器规则视为队友: bool = True
    服务器范围低:int = 0
    服务器范围高: int = 0
    公会成员列表: List[str] = []     # 公会成员名单
    公会名单更新时间: float = 0.0    # 上次更新时间戳
    # ========== 敌人信息面板相关 ==========
    敌人面板坐标:Optional[Tuple[int, int, int, int]] =None
    敌人面板上次检查时间: float = 0.0
    # ========== 召唤响应配置 ==========
    启用召唤响应: bool = True
    启用召唤白名单: bool = False
    启用召唤黑名单: bool = False
    召唤响应白名单: str = ""
    召唤响应黑名单: str = ""

    # ========== 攻击模式 ==========
    默认攻击模式: str = "行会模式"  # 空=不检查，"全体模式"/"和平模式"等

    # ========== 通知消息配置 ==========
    启用通知消息: bool = False
    发送太古祖龙刷新通知: bool = True
    # 上部信息框检查间隔
    上部信息框检查间隔: float = 1.3
    
    # 战斗配置（玩家可调整）
    战斗: 战斗配置 = Field(default_factory=战斗配置.创建默认)
    
    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def 创建默认(cls, 窗口名称: str = "游戏1") -> '玩家配置':
        """创建默认玩家配置"""
        return cls(窗口名称=窗口名称)
    
    @classmethod
    def 从文件加载(cls, 窗口名称: str) -> '玩家配置':
        """从JSON文件加载玩家配置"""
        文件名 = f"{窗口名称}/user_config.json"
        文件路径 = path_mgr.get_config_path(文件名)
        
        if not Path(文件路径).exists():
            调试器.warning("玩家配置", f"配置文件不存在: {文件路径}，使用默认配置")
            return cls.创建默认(窗口名称)
        
        try:
            with open(文件路径, 'r', encoding='utf-8') as f:
                数据 = json.load(f)
            调试器.info("玩家配置", f"从文件加载: {文件路径}")
            return cls(**数据)
        except Exception as e:
            调试器.error("玩家配置", f"加载配置文件失败: {文件路径}, 错误: {e}")
            return cls.创建默认(窗口名称)
    
    def 保存到文件(self) -> bool:
        """保存玩家配置到JSON文件"""
        文件名 = f"{self.窗口名称}/user_config.json"
        文件路径 = path_mgr.get_config_path(文件名)
          # 确保目录存在
        Path(文件路径).parent.mkdir(parents=True, exist_ok=True)
        
        # 转换值函数：处理嵌套的 BaseModel
        def 转换值(值):
            if isinstance(值, BaseModel):
                return 值.dict()
            return 值
        
        # 排除不需要保存的字段
        exclude_fields = {'静止检测点组'}
        
        # 构建数据字典，排除私有字段和指定字段
        数据 = {}
        for k, v in self.__dict__.items():
            # 跳过私有字段和排除字段
            if k.startswith('_'):
                continue
            if k in exclude_fields:
                continue
            数据[k] = 转换值(v)
        
        try:
            with open(文件路径, 'w', encoding='utf-8') as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
            调试器.info("玩家配置", f"保存到文件: {文件路径}")
            return True
        except Exception as e:
            调试器.error("玩家配置", f"保存配置文件失败: {文件路径}, 错误: {e}")
            return False
class 游戏全局配置(BaseModel):
    """
    游戏全局配置 - 整合区域配置和玩家配置
    
    区域配置：所有窗口共享（只读）
    玩家配置：每个窗口独立
    
    使用方式：
        # 创建配置
        配置 = 游戏全局配置.创建默认("游戏1")
        
        # 应用窗口偏移
        配置.应用窗口偏移()
        
        # 保存/加载
        配置.保存到文件()
        配置 = 游戏全局配置.从文件加载("游戏1")
    """
    
        
    # 子配置
    区域: 区域配置 = Field(default_factory=区域配置.创建默认)
    玩家: 玩家配置 = Field(default_factory=玩家配置.创建默认)
    
    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def 创建默认(cls, 窗口名称: str = "游戏1") -> '游戏全局配置':
        """创建默认配置"""
        return cls(玩家=玩家配置.创建默认(窗口名称))
    
    @classmethod
    def 从字典加载(cls, 数据: dict) -> '游戏全局配置':
        """从字典加载配置"""
        return cls(**数据)
    
    @classmethod  
    def 从文件加载(cls, 窗口名称: str) -> '游戏全局配置':
        """从文件加载配置"""
        区域 = 区域配置.从文件加载()
        玩家 = 玩家配置.从文件加载(窗口名称)
        
        return  cls(区域=区域, 玩家=玩家)
    
    def 保存到文件(self) -> bool:
        """保存配置到文件"""
        return self.玩家.保存到文件()
    
    def 应用窗口偏移(self, offset_x: int, offset_y: int):
        """应用窗口偏移到所有区域"""
        ##这个必须先应用全局偏移才能应用其他,应用全局会给线程偏移赋值
        self.区域.应用全局偏移(offset_x, offset_y)
        self.玩家.战斗.检测.静止点应用偏移(offset_x, offset_y)
        
        调试器.info("游戏配置", f"应用窗口偏移: X={offset_x}, Y={offset_y}")
    
    def 重置窗口偏移(self):
        """重置窗口偏移"""
        self.区域.应用全局偏移(0, 0)
    
    # ==================== 快捷访问 ====================
    @property
    def 战斗(self):
        """代理到玩家.战斗"""
        return self.玩家.战斗
    @property
    def 页面名称区域(self):
        return self.区域.主界面.中间页面名称区域标签
    
    @property
    def 第一排任务区域(self):
        return self.区域.主界面.第一排任务区域标签
    
    @property
    def 目标信息区域(self):
        return self.区域.主界面.目标信息显示区域标签
    
    @property
    def 退出按钮区域(self):
        return self.区域.主界面.退出按钮标签
    
    @property
    def 自动战斗按钮区域(self):
        return self.区域.主界面.自动战斗按钮标签
        
    # 战斗配置快捷访问
    @property
    def 目标存在像素规则(self) -> str:
        return self.玩家.战斗.目标存在像素规则
    
    @property
    def 静止检测点(self) -> str:
        return self.玩家.战斗.静止检测点
    
    @property
    def 无目标超时秒数(self) -> float:
        return self.玩家.战斗.无目标超时秒数
    
    @property
    def 静止超时秒数(self) -> float:
        return self.玩家.战斗.静止超时秒数
    
    @property
    def 默认等待秒(self) -> float:
        return self.玩家.战斗.默认等待秒
    
    @property
    def 刷新等待秒(self) -> float:
        return self.玩家.战斗.等待.刷新等待秒
    
    def 打印配置(self):
        """打印所有配置"""
        self.区域.打印所有区域()
        self.玩家.战斗.打印所有配置()


# 注意：不再提供全局单例，由窗口线程自行创建和管理配置