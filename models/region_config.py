# models/region_config.py
"""
区域配置模块 - 完整多级配置
"""
import json
import random
from pathlib import Path
from typing import Tuple,Optional, Dict, Any, List
from pydantic import BaseModel, Field
import threading
from core.path_manager import path_mgr
from tasks import 炼器宝阁

# 线程局部存储（独立于Pydantic）
_线程本地存储 = threading.local()


def _获取当前线程偏移() -> Tuple[int, int]:
    """获取当前线程的偏移量"""
    return (
        getattr(_线程本地存储, '偏移X', 0),
        getattr(_线程本地存储, '偏移Y', 0)
    )


def _设置当前线程偏移(offset_x: int, offset_y: int):
    """设置当前线程的偏移量"""
    _线程本地存储.偏移X = offset_x
    _线程本地存储.偏移Y = offset_y
    print(f"[区域坐标] 线程 {threading.current_thread().name} 设置偏移: X={offset_x}, Y={offset_y}")


def _重置当前线程偏移():
    """重置当前线程的偏移量"""
    _线程本地存储.偏移X = 0
    _线程本地存储.偏移Y = 0
    print(f"[区域坐标] 线程 {threading.current_thread().name} 重置偏移")


class 区域坐标(BaseModel):
    """区域坐标类 - 支持每线程独立偏移"""
    
    # 原始坐标（存储）
    原始左: int
    原始上: int
    原始右: int
    原始下: int
    
    class Config:
        arbitrary_types_allowed = True
        # 允许额外属性
        extra = 'allow'
    
    def __init__(self, 左: int = 0, 上: int = 0, 右: int = 0, 下: int = 0, **data):
        if '原始左' not in data:
            data['原始左'] = 左
            data['原始上'] = 上
            data['原始右'] = 右
            data['原始下'] = 下
        super().__init__(**data)
        # 初始化缓存字典
        self._缓存 = {}
        self._预计算偏移值()
     # 让对象本身可调用返回元组
    def __call__(self) -> Tuple[int, int, int, int]:
        return self.元组
    # ==================== 私有方法 ====================
    
    def _应用偏移边界保护(self, 值: int, 偏移: int) -> int:
        return max(0, 值 + 偏移)
    
    def _预计算偏移值(self):
        """预计算所有偏移后的值"""
        偏移X, 偏移Y = _获取当前线程偏移()
        self._缓存['左'] = self._应用偏移边界保护(self.原始左, 偏移X)
        self._缓存['右'] = self._应用偏移边界保护(self.原始右, 偏移X)
        self._缓存['上'] = self._应用偏移边界保护(self.原始上, 偏移Y)
        self._缓存['下'] = self._应用偏移边界保护(self.原始下, 偏移Y)
        self._缓存['中心点_x'] = (self._缓存['左'] + self._缓存['右']) // 2
        self._缓存['中心点_y'] = (self._缓存['上'] + self._缓存['下']) // 2
        self._缓存['宽'] = self._缓存['右'] - self._缓存['左']
        self._缓存['高'] = self._缓存['下'] - self._缓存['上']
    
    def _重新计算偏移(self):
        """重新计算偏移值"""
        self._预计算偏移值()
    
    # ==================== 类方法：线程偏移管理 ====================
    
    @classmethod
    def 设置当前线程偏移(cls, offset_x: int, offset_y: int):
        """设置当前线程的偏移量（每个线程独立）"""
        _设置当前线程偏移(offset_x, offset_y)
    
    @classmethod
    def 获取当前线程偏移(cls) -> Tuple[int, int]:
        """获取当前线程的偏移量"""
        return _获取当前线程偏移()
    
    @classmethod
    def 重置当前线程偏移(cls):
        """重置当前线程的偏移量为0"""
        _重置当前线程偏移()
    
    # ==================== 属性访问 ====================
    
    @property
    def 左(self) -> int:
        return self._缓存['左']
    
    @property
    def 右(self) -> int:
        return self._缓存['右']
    
    @property
    def 上(self) -> int:
        return self._缓存['上']
    
    @property
    def 下(self) -> int:
        return self._缓存['下']
    
    @property
    def 中心点(self) -> Tuple[int, int]:
        return (self._缓存['中心点_x'], self._缓存['中心点_y'])
    
    @property
    def 元组(self) -> Tuple[int, int, int, int]:
        return (self._缓存['左'], self._缓存['上'], self._缓存['右'], self._缓存['下'])
    
    @property
    def 宽(self) -> int:
        return self._缓存['宽']
    
    @property
    def 高(self) -> int:
        return self._缓存['高']
    
    # @property
    # def 原始左(self) -> int:
    #     return self.原始左
    
    # @property
    # def 原始上(self) -> int:
    #     return self.原始上
    
    # @property
    # def 原始右(self) -> int:
    #     return self.原始右
    
    # @property
    # def 原始下(self) -> int:
    #     return self.原始下
    
    @property
    def 是否有效(self) -> bool:
        """判断区域是否有效（坐标合理，左<右且上<下）"""
        return self.原始左 >= 0 and self.原始上 >= 0 and self.原始右 > self.原始左 and self.原始下 > self.原始上

    # ==================== 随机点 ====================
    
    def 随机点(self, 缩放比例: float = 1.0) -> Tuple[int, int]:
        """获取区域内一个随机点"""
        if 缩放比例 == 1.0:
            return (random.randint(self._缓存['左'], self._缓存['右']),
                    random.randint(self._缓存['上'], self._缓存['下']))
        
        中心点_x, 中心点_y = self._缓存['中心点_x'], self._缓存['中心点_y']
        半宽 = int(self._缓存['宽'] * 缩放比例 / 2)
        半高 = int(self._缓存['高'] * 缩放比例 / 2)
        
        左 = max(self._缓存['左'], 中心点_x - 半宽)
        右 = min(self._缓存['右'], 中心点_x + 半宽)
        上 = max(self._缓存['上'], 中心点_y - 半高)
        下 = min(self._缓存['下'], 中心点_y + 半高)
        
        if 左 >= 右 or 上 >= 下:
            return (中心点_x, 中心点_y)
        
        return (random.randint(左, 右), random.randint(上, 下))
    
    # ==================== 序列化 ====================
    
    def 转字典(self) -> dict:
        """转换为字典（用于JSON序列化）"""
        return {
            "左": self.原始左,
            "上": self.原始上,
            "右": self.原始右,
            "下": self.原始下
        }
    
    def __repr__(self) -> str:
        偏移X, 偏移Y = _获取当前线程偏移()
        return f"区域坐标(原始=({self.原始左},{self.原始上},{self.原始右},{self.原始下}), 偏移=({偏移X},{偏移Y}), 偏移后=({self._缓存['左']},{self._缓存['上']},{self._缓存['右']},{self._缓存['下']}))"
    
    def __str__(self) -> str:
        return f"({self._缓存['左']},{self._缓存['上']},{self._缓存['右']},{self._缓存['下']})"

# ==================== 神器位置配置 ====================

class 神器位置配置(BaseModel):
    """神器位置配置"""
    位置1: 区域坐标 = Field(default_factory=lambda: 区域坐标(720, 311, 737, 333))
    位置2: 区域坐标 = Field(default_factory=lambda: 区域坐标(804, 253, 824, 272))
    位置3: 区域坐标 = Field(default_factory=lambda: 区域坐标(720, 540, 737, 561))
    位置4: 区域坐标 = Field(default_factory=lambda: 区域坐标(917, 253, 936, 274))
    位置5: 区域坐标 = Field(default_factory=lambda: 区域坐标(691, 423, 709, 445))
    位置6: 区域坐标 = Field(default_factory=lambda: 区域坐标(1014, 313, 1031, 333))
    位置7: 区域坐标 = Field(default_factory=lambda: 区域坐标(1040, 425, 1057, 445))
    位置8: 区域坐标 = Field(default_factory=lambda: 区域坐标(1014, 540, 1033, 561))
    位置9: 区域坐标 = Field(default_factory=lambda: 区域坐标(917, 595, 938, 615))
    位置10: 区域坐标 = Field(default_factory=lambda: 区域坐标(807, 594, 829, 616))
    位置11: 区域坐标 = Field(default_factory=lambda: 区域坐标(917, 425, 938, 447))
    位置12: 区域坐标 = Field(default_factory=lambda: 区域坐标(807, 423, 829, 447))
    
    def 获取(self, 索引: int) -> Optional[区域坐标]:
        return getattr(self, f"位置{索引}", None)


# ==================== 攻击模式配置 ====================

class 攻击模式配置(BaseModel):
    """攻击模式相关区域"""
    当前攻击模式显示区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(407, 860, 474, 884))
    攻击模式展开显示区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(420, 651, 508, 861))
    攻击模式全体模式按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(414, 663, 480, 677))
    攻击模式和平模式按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(419, 700, 487, 713))
    攻击模式编组模式按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(420, 733, 483, 745))
    攻击模式行会模式按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(420, 770, 482, 781))
    攻击模式善恶模式按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(419, 804, 487, 815))
    攻击模式盟友模式按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(426, 840, 489, 851))


# ==================== 掉线检查配置 ====================

class 掉线检查配置(BaseModel):
    """掉线检查相关区域"""
    掉线刷新游戏按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(869, 460, 1044, 522))
    异地登录情况区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(749, 381, 947, 524))
    登录界面开始按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(735, 647, 963, 719))
    登录后提示区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(804, 442, 897, 577))
    登录后确认按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(757, 615, 929, 693))
    断开连接情况区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(731, 375, 976, 519))


# ==================== BOSS相关配置 ====================

class Boss相关配置(BaseModel):
    """首领图标内相关区域"""
    第三个BOSS选项卡位置标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(481, 523, 680, 552))
    BOSS页面进入第一层位置: 区域坐标 = Field(default_factory=lambda: 区域坐标(740, 523, 816, 553))
    地图传送选层位置: 区域坐标 = Field(default_factory=lambda: 区域坐标(469, 231, 916, 269))
    地图传送进入地图按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1025, 617, 1117, 648))
    首领页面神之领域数量区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(888, 506, 1012, 532))
    首领页面BOSS之家数量区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1041, 509, 1183, 533))
    首领页面阶数显示标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(554,277,688,676))
    首领页面各层信息显示标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(707,509,847,675))



# ==================== 专属BOSS配置 ====================

class 专属BOSS配置(BaseModel):
    """专属BOSS相关区域"""
    专属BOSS等级选择卡区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(471, 228, 614, 666))
    专属当前BOSS当前情况区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(791, 235, 1032, 285))
    专属BOSS前往挑战按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1090, 629, 1177, 655))
    专属BOSS剩余次数区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(832, 552, 1002, 586))


# ==================== 降魔配置 ====================

class 降魔配置(BaseModel):
    """降魔相关区域"""
    降魔页面剩余次数区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1009, 575, 1144, 608))
    降魔页面协助剩余次数区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(548, 546, 677, 578))
    降魔页面当前层龙头标识区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(469, 269, 1210, 353))
    降魔页面前往挑战按钮: 区域坐标 = Field(default_factory=lambda: 区域坐标(1035, 613, 1126, 642))
    降魔副本归属显示区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(167, 62, 207, 182))
    降魔副本内玩家名字显示区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(62, 58, 166, 183))


# ==================== 天关配置 ====================

class 天关配置(BaseModel):
    """天关相关区域"""
    天关页面扫荡按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(882, 606, 979, 634))
    天关页面剩余次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(925, 639, 1008, 666))
    # 天关扫荡页面扫荡按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(808, 622, 891, 650))
    天关确认页面前往挑战按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(803,623,898,649))


# ==================== 行会配置 ====================

class 行会配置(BaseModel):
    """行会相关区域"""
    行会页面行会名称区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(558,249,661,284))
    行会页面创建行会按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1077,633,1174,664))
    行会页面右侧成员按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1228, 330, 1249, 372))
    行会成员数量区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(590,611,700,642))
    成员页面成员名单区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(505, 263, 643, 623))
    人员名单拖动区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(886, 578, 914, 602))


# ==================== 鱼塘配置 ====================

class 鱼塘配置(BaseModel):
    """鱼塘相关区域"""
    主页面鱼塘区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(431, 601, 468, 624))
    鱼塘一件售卖按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1055, 615, 1146, 640))
    鱼塘售卖确定区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(810, 526, 891, 554))

# models/region_config.py - 添加以下配置类

# ==================== 兽神相关配置 ====================

class 兽神相关配置(BaseModel):
    """兽神相关区域"""
    兽神页面扫荡按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1027, 639, 1105, 666))
    兽神页面剩余次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1069, 570, 1138, 599))
    兽神页面矿物颜色检查标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(687, 620, 732, 674))
    兽神扫荡页面扫荡按钮标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(996, 393, 1063, 420))
    兽神扫荡页面扫荡按钮标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(988, 444, 1068, 470))
    兽神扫荡页面扫荡按钮标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(995, 496, 1064, 520))
    兽神扫荡页面扫荡次数标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(874, 394, 925, 417))
    兽神扫荡页面扫荡次数标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(878, 440, 920, 471))
    兽神扫荡页面扫荡次数标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(883, 489, 913, 520))
    兽神战场BOSS剩余次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(85, 68, 150, 103))
    兽神战场矿晶剩余次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(85, 121, 150, 153))
    兽神战场矿铁剩余次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(85, 176, 150, 211))


# ==================== 战场页面相关配置 ====================

class 战场页面相关配置(BaseModel):
    """跨服战场图标内相关区域"""
    跨服页面暗殿次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1103, 623, 1164, 646))
    跨服页面神兵次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(799, 405, 870, 427))
    跨服页面巅峰次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1037, 374, 1102, 399))
    跨服页面主宰入口标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(573, 413, 630, 466))
    跨服页面跨服入侵入口标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(780, 509, 895, 580))


# ==================== 暗殿相关配置 ====================

class 暗殿相关配置(BaseModel):
    """暗殿相关区域"""
    暗殿页面暗殿次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(938, 535, 1163, 573))
    暗殿页面刷新时间标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(712, 371, 834, 411))
    暗殿页面前往挑战按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1002, 616, 1085, 645))
    暗殿地图归属情况标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(41, 99, 226, 146))


# ==================== 巅峰竞技相关配置 ====================

class 巅峰竞技相关配置(BaseModel):
    """巅峰竞技相关区域"""
    巅峰页面右侧预选选项卡标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1278, 294, 1299, 339))
    巅峰页面右侧决赛选项卡标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1277, 372, 1300, 417))
    巅峰页面右侧膜拜选项卡含红点标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1272, 504, 1311, 576))
    巅峰预选页面次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(782, 684, 941, 721))
    巅峰预选页面匹配按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(808, 618, 900, 649))
    巅峰膜拜按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(803, 656, 908, 681))


# ==================== 神兵相关配置 ====================

class 神兵相关配置(BaseModel):
    """神兵相关区域"""
    神兵页面神兵次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(661, 591, 823, 619))
    神兵页面刷新情况标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(983, 240, 1172, 650))
    神兵页面前往挑战按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(764, 632, 854, 660))
    神兵副本剩余次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(62, 109, 220, 149))


# ==================== 跨服入侵相关配置 ====================

class 跨服入侵相关配置(BaseModel):
    """跨服入侵相关区域"""
    跨服入侵页面BOSS选择按钮1: 区域坐标 = Field(default_factory=lambda: 区域坐标(573, 620, 601, 647))
    跨服入侵页面BOSS选择按钮2: 区域坐标 = Field(default_factory=lambda: 区域坐标(656, 619, 684, 645))
    跨服入侵页面BOSS选择按钮3: 区域坐标 = Field(default_factory=lambda: 区域坐标(736, 618, 765, 649))
    跨服入侵页面BOSS选择按钮4: 区域坐标 = Field(default_factory=lambda: 区域坐标(818, 621, 845, 648))
    跨服入侵页面BOSS选择图标范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(515, 584, 886, 672))
    跨服入侵副本三头龙击杀提示区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(99, 94, 178, 152))
    跨服入侵页面挑战按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(993, 633, 1086, 663))
    跨服入侵页面挑战确定按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(919, 480, 990, 506))
    跨服入侵副本奖励确定按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(500, 462, 952, 650))
    
    def 获取(self, 索引: int) -> Optional[区域坐标]:
        return getattr(self, f"跨服入侵页面BOSS选择按钮{索引}", None)

class 跨服入侵相关旧配置(BaseModel):
    """跨服入侵相关区域（旧版）"""
    跨服入侵页面BOSS选择按钮2: 区域坐标 = Field(default_factory=lambda: 区域坐标(613, 619, 643, 645))
    跨服入侵页面BOSS选择按钮3: 区域坐标 = Field(default_factory=lambda: 区域坐标(696, 620, 723, 648))
    跨服入侵页面BOSS选择按钮4: 区域坐标 = Field(default_factory=lambda: 区域坐标(777, 622, 803, 647))

    def 获取(self, 索引: int) -> Optional[区域坐标]:
        return getattr(self, f"跨服入侵页面BOSS选择按钮{索引}", None)

# ==================== 主宰相关配置 ====================

class 主宰相关配置(BaseModel):
    """主宰相关区域"""
    主宰综合信息页面主宰数量区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(936,406,999,435))
    主宰综合信息页面立即前往区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(867, 437, 932, 455))
    主宰综合信息页面最强玩家区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(591, 262, 947, 359))
    主宰副本小地图主宰战场标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(711, 229, 831, 265))
    主宰副本小地图BOSS坐标标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(653, 404, 658, 411))
    主宰副本小地图BOSS坐标标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(774, 387, 779, 393))
    主宰副本小地图BOSS坐标标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(893, 406, 899, 412))
    主宰副本小地图BOSS坐标标签4: 区域坐标 = Field(default_factory=lambda: 区域坐标(693, 522, 698, 529))
    主宰副本小地图BOSS坐标标签5: 区域坐标 = Field(default_factory=lambda: 区域坐标(853, 522, 859, 529))
    主宰副本小地图BOSS刷新情况标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(624,408,691,441))
    主宰副本小地图BOSS刷新情况标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(747,392,807,420))
    主宰副本小地图BOSS刷新情况标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(864,411,936,438))
    主宰副本小地图BOSS刷新情况标签4: 区域坐标 = Field(default_factory=lambda: 区域坐标(664,526,728,554))
    主宰副本小地图BOSS刷新情况标签5: 区域坐标 = Field(default_factory=lambda: 区域坐标(819,527,890,559))
    主宰归属玩家检查区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(44,134,238,159))
    主宰归属行会检查区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(63,155,218,182))
    主宰BOSS血量显示区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(117, 116, 159, 139))
    主宰抢归属按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(97, 184, 178, 211))


# ==================== 坐骑相关配置 ====================

class 坐骑相关配置(BaseModel):
    """坐骑相关区域"""
    坐骑页面选层区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(470, 230, 1206, 265))
    坐骑页面1层区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(492, 239, 528, 257))
    坐骑页面坐骑选择范围标签11: 区域坐标 = Field(default_factory=lambda: 区域坐标(674, 287, 837, 391))
    坐骑页面坐骑选择范围标签12: 区域坐标 = Field(default_factory=lambda: 区域坐标(558, 423, 670, 483))
    坐骑页面坐骑选择范围标签13: 区域坐标 = Field(default_factory=lambda: 区域坐标(770, 425, 881, 479))
    坐骑页面坐骑选择范围标签14: 区域坐标 = Field(default_factory=lambda: 区域坐标(555, 520, 675, 577))
    坐骑页面坐骑选择范围标签15: 区域坐标 = Field(default_factory=lambda: 区域坐标(767, 519, 885, 575))
    坐骑页面坐骑选择范围标签21: 区域坐标 = Field(default_factory=lambda: 区域坐标(666, 287, 845, 385))
    坐骑页面坐骑选择范围标签22: 区域坐标 = Field(default_factory=lambda: 区域坐标(516, 494, 643, 585))
    坐骑页面坐骑选择范围标签23: 区域坐标 = Field(default_factory=lambda: 区域坐标(726, 500, 849, 580))
    坐骑页面坐骑选择范围标签31: 区域坐标 = Field(default_factory=lambda: 区域坐标(486, 287, 653, 427))
    坐骑页面坐骑选择范围标签32: 区域坐标 = Field(default_factory=lambda: 区域坐标(484, 448, 652, 587))
    坐骑页面坐骑选择范围标签41: 区域坐标 = Field(default_factory=lambda: 区域坐标(486, 287, 653, 427))
    坐骑页面坐骑选择范围标签42: 区域坐标 = Field(default_factory=lambda: 区域坐标(484, 448, 652, 587))
    坐骑页面坐骑选择范围标签51: 区域坐标 = Field(default_factory=lambda: 区域坐标(486, 287, 653, 427))
    坐骑页面坐骑选择范围标签52: 区域坐标 = Field(default_factory=lambda: 区域坐标(484, 448, 652, 587))
    坐骑页面坐骑选择范围标签61: 区域坐标 = Field(default_factory=lambda: 区域坐标(486, 287, 653, 427))
    坐骑页面坐骑选择范围标签62: 区域坐标 = Field(default_factory=lambda: 区域坐标(484, 448, 652, 587))
    坐骑页面坐骑选择范围标签71: 区域坐标 = Field(default_factory=lambda: 区域坐标(486, 287, 653, 427))
    坐骑页面坐骑选择范围标签72: 区域坐标 = Field(default_factory=lambda: 区域坐标(484, 448, 652, 587))
    坐骑页面坐骑选择范围标签81: 区域坐标 = Field(default_factory=lambda: 区域坐标(486, 287, 653, 427))
    坐骑页面坐骑选择范围标签82: 区域坐标 = Field(default_factory=lambda: 区域坐标(484, 448, 652, 587))
    坐骑页面进入按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1077, 631, 1167, 659))
    坐骑页面归属次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1139, 593, 1213, 623))
    坐骑副本内归属区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(58, 137, 214, 161))
    坐骑副本内抢归属区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(80, 178, 189, 218))


# ==================== 古剑相关配置 ====================

class 古剑相关配置(BaseModel):
    """古剑相关区域"""
    古剑页面1倍奖励选择区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(649,275,781,320))
    古剑页面古剑霸主刷新时间区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(876, 510, 988, 553))
    古剑页面古剑霸主点击区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(891, 405, 966, 470))
    古剑页面古剑BOSS进入区域标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(704, 293, 734, 343))
    古剑页面古剑BOSS进入区域标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(1088, 327, 1121, 367))
    古剑页面古剑BOSS进入区域标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(767, 590, 808, 615))
    古剑页面古剑BOSS进入区域标签4: 区域坐标 = Field(default_factory=lambda: 区域坐标(1093, 520, 1125, 559))
    古剑页面刷新时间区域标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(665,396,763,427))
    古剑页面刷新时间区域标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(1061,404,1151,432))
    古剑页面刷新时间区域标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(751,614,830,642))
    古剑页面刷新时间区域标签4: 区域坐标 = Field(default_factory=lambda: 区域坐标(1070,612,1155,638))
    古剑页面前往按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(806, 606, 895, 632))
    古剑页面前往页面刷新时间区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(789, 560, 908, 601))
    古剑页面前往击杀按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(804, 521, 895, 549))
    古剑副本归属区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(52,102,221,142))
    古剑页面剩余次数区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(761, 646, 800, 677))
    古剑副本抢归属按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(92, 153, 182, 182))
    古剑副本内剩余次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(35, 191, 241, 222))


# ==================== 大千世界相关配置 ====================

class 大千世界各任务入口配置(BaseModel):
    """大千世界各任务入口区域"""
    大千世界页面神界大陆按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(797, 525, 913, 568))
    大千世界页面决战盟重按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(504, 413, 637, 458))
    大千世界页面诸神遗迹按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(533, 561, 682, 610))
    大千世界页面修罗魔域按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1103, 557, 1227, 602))
    大千世界页面虚空剑界按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(727, 312, 834, 352))
    大千世界页面圣兽试炼按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(940, 358, 1049, 392))
    大千世界页面五行洞天按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1117, 341, 1232, 376))


# ==================== 神界大陆相关配置 ====================

class 神界大陆相关配置(BaseModel):
    """神界大陆相关区域"""
    神界页面右侧神界按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1225, 253, 1249, 299))
    神界页面右侧专属按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1228, 332, 1250, 378))
    神界页面右侧秘境按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1227, 412, 1251, 454))
    神界页面神界之巅按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(612, 237, 699, 265))
    神界之巅前往挑战按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1000, 611, 1093, 638))
    神界之巅刷新情况标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(668, 282, 832, 320))
    神界专属前往挑战按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(895, 639, 991, 666))
    神界专属挑战次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(884, 600, 1000, 629))
    神界专属前往击杀按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(807, 541, 890, 569))
    神界专属单倍奖励按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(661, 313, 776, 329))
    神界专属副本内boss次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(61, 101, 210, 128))
    神界秘境前往挑战按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(733, 636, 820, 666))
    神界秘境页面剩余体力值标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(657, 240, 893, 291))
    神界秘境副本剩余体力值标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(51, 185, 220, 216))


# ==================== 神界战场相关配置 ====================

class 神界战场相关配置(BaseModel):
    """神界战场相关区域"""
    神界战场剩余神元区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(971, 550, 1152, 576))
    神界战场前往挑战按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1016, 509, 1103, 537))
    神界战场页面刷新时间标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(762, 329, 888, 365))
    神界战场页面刷新时间标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(762, 369, 886, 400))
    神界战场页面刷新时间标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(762, 405, 891, 443))
    神界战场页面刷新时间标签4: 区域坐标 = Field(default_factory=lambda: 区域坐标(762, 440, 888, 479))
    神界战场页面刷新时间标签5: 区域坐标 = Field(default_factory=lambda: 区域坐标(762, 479, 893, 515))
    神界战场页面刷新时间标签6: 区域坐标 = Field(default_factory=lambda: 区域坐标(762, 516, 894, 556))
    神界战场副本剩余神元区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(96, 191, 185, 218))
    神界战场副本刷新时间标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(592, 338, 675, 363))
    神界战场副本刷新时间标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(909, 360, 975, 382))
    神界战场副本刷新时间标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(734, 422, 803, 442))
    神界战场副本刷新时间标签4: 区域坐标 = Field(default_factory=lambda: 区域坐标(676, 573, 750, 592))
    神界战场副本刷新时间标签5: 区域坐标 = Field(default_factory=lambda: 区域坐标(925, 548, 1002, 569))
    神界战场副本刷新时间标签6: 区域坐标 = Field(default_factory=lambda: 区域坐标(574, 451, 647, 473))
    神界战场副本地图BOSS位置标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(603, 320, 653, 340))
    神界战场副本地图BOSS位置标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(917, 332, 967, 362))
    神界战场副本地图BOSS位置标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(737, 398, 793, 423))
    神界战场副本地图BOSS位置标签4: 区域坐标 = Field(default_factory=lambda: 区域坐标(687, 552, 740, 575))
    神界战场副本地图BOSS位置标签5: 区域坐标 = Field(default_factory=lambda: 区域坐标(942, 526, 989, 552))
    神界战场副本地图BOSS位置标签6: 区域坐标 = Field(default_factory=lambda: 区域坐标(584, 429, 634, 453))
    角色面板右侧神装标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(473, 478, 495, 525))
    角色神装面板神器按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(255, 567, 303, 592))
    角色神器面板神器文字标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(825, 221, 886, 247))


# models/region_config.py - 添加以下配置类

# ==================== 诸神遗迹相关配置 ====================

class 诸神遗迹相关配置(BaseModel):
    """诸神遗迹相关区域"""
    诸神遗迹地图范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(631, 278, 1202, 594))
    预言圣殿选项卡区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(506, 337, 595, 369))
    诸神遗迹立即前往按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1094, 614, 1182, 643))
    诸神遗迹预言遗迹按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(486, 240, 573, 267))
    诸神遗迹失落遗迹按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(599, 240, 682, 267))
    诸神遗迹时光遗迹按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(708, 240, 799, 268))
    诸神遗迹顶分页卡区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(479, 236, 1197, 267))


class 诸神遗迹BOSS地图位置配置(BaseModel):
    """诸神遗迹BOSS地图位置，喜怒哀乐泰坦"""
    位置1: 区域坐标 = Field(default_factory=lambda: 区域坐标(620, 526, 632, 547))
    位置2: 区域坐标 = Field(default_factory=lambda: 区域坐标(607, 337, 629, 354))
    位置3: 区域坐标 = Field(default_factory=lambda: 区域坐标(915, 341, 938, 354))
    位置4: 区域坐标 = Field(default_factory=lambda: 区域坐标(904, 518, 919, 535))
    位置5: 区域坐标 = Field(default_factory=lambda: 区域坐标(757, 443, 782, 459))
    
    def 获取(self, 索引: int) -> Optional[区域坐标]:
        return getattr(self, f"位置{索引}", None)
    
class 诸神遗迹BOSS地图刷新时间区域配置(BaseModel):
    """诸神遗迹BOSS地图位置，喜怒哀乐泰坦"""
    位置1: 区域坐标 = Field(default_factory=lambda: 区域坐标(573,540,658,571))
    位置2: 区域坐标 = Field(default_factory=lambda: 区域坐标(583,340,655,365))
    位置3: 区域坐标 = Field(default_factory=lambda: 区域坐标(890,340,970,369))
    位置4: 区域坐标 = Field(default_factory=lambda: 区域坐标(891,528,975,561))
    位置5: 区域坐标 = Field(default_factory=lambda: 区域坐标(731,433,816,460))
    
    def 获取(self, 索引: int) -> Optional[区域坐标]:
        return getattr(self, f"位置{索引}", None)


# ==================== 修罗魔域相关配置 ====================

class 修罗魔域相关配置(BaseModel):
    """修罗魔域相关区域"""
    修罗魔域页面剩余奖励次数范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(719, 558, 780, 600))
    修罗魔域页面BOSS详情进入范围标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(884, 277, 936, 314))
    修罗魔域页面BOSS详情进入范围标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(727, 454, 764, 492))
    修罗魔域页面BOSS详情进入范围标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(1069, 473, 1116, 510))
    修罗魔域页面BOSS刷新时间范围标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(857,400,957,434))
    修罗魔域页面BOSS刷新时间范围标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(700,529,803,565))
    修罗魔域页面BOSS刷新时间范围标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(1031,548,1128,578))
    修罗BOSS页面刷新时间范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(787, 567, 913, 600))
    修罗BOSS页面前往按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(801, 606, 900, 633))

    修罗血脉页面升级按钮带红点区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(999,612,1153,675))


# ==================== 圣兽试炼相关配置 ====================

class 圣兽试炼相关配置(BaseModel):
    """圣兽试炼相关区域"""
    圣兽试炼页面剩余奖励次数范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1037, 592, 1194, 625))
    圣兽试炼页面BOSS详情进入范围标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(1004, 321, 1118, 350))
    圣兽试炼页面BOSS详情进入范围标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(1006, 376, 1115, 432))
    圣兽试炼页面BOSS详情进入范围标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(1010, 455, 1111, 509))
    圣兽试炼页面前往按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1077, 631, 1163, 661))
    圣兽试炼页面圣兽标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(492, 243, 566, 265))
    圣兽试炼页面圣兽标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(602, 242, 684, 263))
    圣兽试炼页面圣兽标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(719, 241, 795, 264))
    圣兽试炼页面圣兽标签4: 区域坐标 = Field(default_factory=lambda: 区域坐标(829, 241, 901, 264))
    圣兽试炼页面层数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(492, 291, 605, 332))
    圣兽试炼页面个人入口标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1011, 530, 1106, 565))
    圣兽试炼页面个人BOSS详情进入范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1016, 545, 1111, 587))
    青龙小地图刷新区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(704, 390, 727, 411))
    白虎小地图刷新区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(731, 415, 744, 428))
    朱雀小地图刷新区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(717, 410, 733, 426))
    圣兽试炼前往页面前往按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(801, 538, 890, 570))
    圣兽试炼前往页面单倍奖励按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(675, 315, 767, 331))

    圣兽血脉上部小标题页面标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(474,222,899,260))
    圣兽血脉升级按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1043,639,1129,669))


# ==================== 圣兽宝库相关配置 ====================

class 圣兽宝库相关配置(BaseModel):
    """圣兽宝库相关区域"""
    圣兽试炼页面右侧宝库标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1230, 336, 1248, 377))
    圣兽宝库页面积分标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(840, 302, 941, 327))
    圣兽宝库页面前往击杀按钮: 区域坐标 = Field(default_factory=lambda: 区域坐标(1013, 636, 1099, 665))
    圣兽宝库页面积分奖励标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(867, 233, 935, 312))
    圣兽宝库页面积分奖励面板标头文字标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(663, 209, 808, 242))
    圣兽宝库页面积分奖励面板领取按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(913, 281, 1003, 648))
    圣兽宝库页面深处刷新时间标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(667, 259, 776, 293))
    圣兽宝库页面深处挑战按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(649, 594, 795, 643))
    宝库深处页面抢归属按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(88,153,184,182))
    宝库深处页面归属玩家区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(55,101,214,138))


# ==================== 虚空剑界相关配置 ====================

class 虚空剑界相关配置(BaseModel):
    """虚空剑界相关区域"""
    虚空剑界页面剩余奖励次数范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(684, 639, 846, 674))
    虚空剑界页面BOSS详情进入范围标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(920, 248, 1084, 318))
    虚空剑界页面BOSS详情进入范围标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(680, 311, 835, 386))
    虚空剑界页面BOSS详情进入范围标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(835, 400, 988, 471))
    虚空剑界页面BOSS详情进入范围标签4: 区域坐标 = Field(default_factory=lambda: 区域坐标(927, 488, 1084, 561))
    虚空剑界页面BOSS详情进入范围标签5: 区域坐标 = Field(default_factory=lambda: 区域坐标(701, 557, 851, 625))
    虚空BOSS页面刷新时间范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(794, 569, 901, 594))
    虚空BOSS页面前往按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(801, 604, 902, 636))
    虚空剑意页面升级按钮带红点区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(993,613,1137,676))
    虚空飞剑页面小页面关闭按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1016,182,1084,273))
    虚空飞剑页面激活按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(788,600,884,633))
    虚空飞剑页面红点搜索区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(597,234,996,663))


# ==================== 决战盟重相关配置 ====================

class 决战盟重相关配置(BaseModel):
    """决战盟重相关区域"""
    决战盟重页面前往匹配按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(782, 631, 887, 660))
    决战盟重页面准备匹配按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(803, 586, 898, 615))
    决战盟重页面准备按键右边按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(993, 576, 1088, 604))
    决战盟重页面准备按键左边按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(611, 576, 704, 606))
    决战盟重页面挑战次数区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(764, 538, 924, 576))
    决战盟重页面玩家准备情况标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(595, 542, 720, 568))
    决战盟重页面玩家准备情况标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(816,517,887,539))
    决战盟重页面玩家准备情况标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(981, 545, 1103, 569))
    决战盟重页面AI确定按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(910, 480, 998, 508))


# ==================== 五行洞天相关配置 ====================

class 五行洞天相关配置(BaseModel):
    """五行洞天相关区域"""
    五行洞天页面剩余奖励次数范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(720, 534, 785, 569))
    五行洞天页面BOSS详情进入范围标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(652, 630, 804, 657))
    五行洞天页面BOSS详情进入范围标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(838, 629, 991, 658))
    五行洞天页面BOSS详情进入范围标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(1015, 629, 1176, 655))
    五行洞天页面前往按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1027, 478, 1115, 505))


# ==================== 跨服争霸相关配置 ====================

class 跨服争霸相关配置(BaseModel):
    """跨服争霸相关区域"""
    跨服争霸页面剩余次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(929, 626, 971, 665))
    跨服争霸快速匹配按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1090, 632, 1174, 660))
    跨服争霸进入购买按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(974, 638, 991, 652))
    跨服争霸剩余购买次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(857, 388, 996, 420))
    跨服争霸购买按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(880, 429, 960, 456))
    跨服争霸购买二次确认按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(800, 543, 873, 573))


# ==================== 群星圣域相关配置 ====================

class 群星圣域相关配置(BaseModel):
    """群星圣域相关区域"""
    群星圣域页面飞升灵境进入含红点范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1039, 541, 1085, 587))
    群星圣域页面魔神禁地进入含红点范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1046, 393, 1109, 458))
    群星圣域页面渡劫飞升进入含红点范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1039, 284, 1088, 333))
    群星圣域页面群星试炼进入范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(677,528,731,597))
    群星圣域页面群星试炼开始挑战按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(991,612,1087,645))
    群星圣域页面群星圣殿进入标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(822,372,865,418))
    群星圣殿页面十连按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(918,605,992,634))
    群星圣殿页面不显示奖励界面按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(758,644,802,684))
    群星圣殿页面十连群星令数量标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(958,568,1021,595))
    星魂升级页面五行标头区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(652,228,1161,274))
    星魂升级页面升级按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(853,632,945,661))
    星魂专属页面左侧卡牌红点搜索区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(539,224,591,671))
    星魂专属页面中间卡牌红点搜索区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(635,315,1182,598))
    星魂专属页面升级窗口关闭按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1016,191,1111,307))
    星魂专属页面升级窗口升级按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(803,601,899,631))

    
    
# ==================== 魔神禁地相关配置 ====================

class 魔神禁地相关配置(BaseModel):
    """魔神禁地相关区域"""
    魔神禁地页面剩余奖励次数范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(921, 584, 1109, 624))
    魔神禁地页面前往挑战按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(974, 632, 1068, 659))


# ==================== 飞升灵境相关配置 ====================

class 飞升灵境相关配置(BaseModel):
    """飞升灵境相关区域"""
    飞升灵境页面剩余奖励次数范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(470, 561, 649, 603))
    飞升灵境页面BOSS详情进入范围标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(788, 260, 835, 300))
    飞升灵境页面BOSS详情进入范围标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(623, 403, 661, 440))
    飞升灵境页面BOSS详情进入范围标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(930, 473, 966, 506))
    飞升灵境页面BOSS刷新时间标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(752,401,849,434))
    飞升灵境页面BOSS刷新时间标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(596,513,687,544))
    飞升灵境页面BOSS刷新时间标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(888,548,979,579))
    飞升BOSS页面刷新时间范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(787, 567, 913, 600))
    飞升BOSS页面前往按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(801, 606, 900, 633))
    飞升灵境归属玩家名字区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(48, 99, 236, 144))


# ==================== 异界夺宝相关配置 ====================

class 异界夺宝相关配置(BaseModel):
    """异界夺宝相关区域"""
    异界夺宝报名按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(803, 429, 902, 460))
    异界夺宝关闭报名页范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(991, 145, 1217, 300))
    异界夺宝进入战场按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(787, 620, 882, 649))
    异界夺宝被邀请按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(466, 538, 533, 602))
    # 异界夺宝报名入口按钮标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(815, 400, 851, 432))
    # 异界夺宝报名入口按钮标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(699, 325, 725, 348))
    # 异界夺宝报名入口按钮标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(901, 326, 924, 345))
    # 异界夺宝报名入口按钮标签4: 区域坐标 = Field(default_factory=lambda: 区域坐标(935, 463, 953, 477))
    # 异界夺宝报名入口按钮标签5: 区域坐标 = Field(default_factory=lambda: 区域坐标(1065, 522, 1082, 537))
    # 异界夺宝报名入口按钮标签6: 区域坐标 = Field(default_factory=lambda: 区域坐标(555, 568, 578, 583))
    # 异界夺宝报名入口按钮标签7: 区域坐标 = Field(default_factory=lambda: 区域坐标(832, 571, 854, 586))
    # 异界夺宝报名入口按钮标签8: 区域坐标 = Field(default_factory=lambda: 区域坐标(598, 446, 613, 459))
    # 异界夺宝报名入口按钮标签9: 区域坐标 = Field(default_factory=lambda: 区域坐标(716, 495, 733, 512))
    # 异界夺宝报名入口按钮标签10: 区域坐标 = Field(default_factory=lambda: 区域坐标(1041, 356, 1052, 369))
    # 异界夺宝报名入口按钮标签11: 区域坐标 = Field(default_factory=lambda: 区域坐标(988, 237, 994, 241))
    # 异界夺宝报名入口按钮标签15: 区域坐标 = Field(default_factory=lambda: 区域坐标(606, 485, 613, 492))
    # 异界夺宝报名入口按钮标签16: 区域坐标 = Field(default_factory=lambda: 区域坐标(772, 479, 784, 490))
    # 异界夺宝报名入口按钮标签17: 区域坐标 = Field(default_factory=lambda: 区域坐标(993, 504, 1008, 515))
    # 异界夺宝报名入口按钮标签18: 区域坐标 = Field(default_factory=lambda: 区域坐标(662, 352, 673, 362))
    # 异界夺宝报名入口按钮标签19: 区域坐标 = Field(default_factory=lambda: 区域坐标(900, 411, 912, 422))
    # 异界夺宝报名入口按钮标签20: 区域坐标 = Field(default_factory=lambda: 区域坐标(1170, 537, 1181, 546))
    异界夺宝报名拖动位置标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(795, 339, 827, 362))
    异界夺宝报名玩家名字标题标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(800, 483, 896, 518))
    异界夺宝组队按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1139, 628, 1161, 652))
    异界夺宝邀请队友按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(716, 364, 741, 387))
    异界夺宝组队页面玩家名字标题标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(801, 215, 893, 252))
    异界夺宝组队页面第一个玩家名字区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(786,274,910,307))
    异界夺宝组队页面第二个玩家名字区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(783, 351, 921, 395))
    异界夺宝组队页面邀请队友按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(705, 354, 747, 391))
    异界夺宝组队页面退出队伍按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(803, 620, 898, 649))
    异界夺宝邀请队友页面玩家名字区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(667, 256, 797, 677))
    异界夺宝被邀请名字检查区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(550,290,853,626))
    异界夺宝被邀请确认按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1089, 308, 1158, 332))
    异界夺宝被邀请操作文字区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1028,254,1111,291))
    异界夺宝战场归属者名字标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(70, 119, 223, 145))
    异界夺宝战场BOSS剩余血量标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(108, 146, 165, 166))
    异界夺宝战场抢归属标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(102, 189, 176, 217))
    报名标记查找区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(473,227,1209,595))
    异界夺宝抢归属按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(103,192,176,215))
    


# ==================== 双倍押镖相关配置 ====================

class 双倍押镖相关配置(BaseModel):
    """双倍押镖相关区域"""
    双倍押镖次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(826, 464, 994, 500))
    双倍押镖接取高级镖车按钮: 区域坐标 = Field(default_factory=lambda: 区域坐标(911, 639, 1013, 663))
    双倍押镖接取低级镖车按钮: 区域坐标 = Field(default_factory=lambda: 区域坐标(912,424,1012,450))
    双倍押镖自动押镖按钮: 区域坐标 = Field(default_factory=lambda: 区域坐标(153, 183, 222, 205))
    双倍押镖再次押镖确定按钮: 区域坐标 = Field(default_factory=lambda: 区域坐标(915, 479, 994, 509))
    双倍押镖领取奖励确定按钮: 区域坐标 = Field(default_factory=lambda: 区域坐标(802, 571, 899, 600))
    双倍押镖副本内押镖状态区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(44,70,227,97))


# ==================== 陨圣相关配置 ====================

class 陨圣相关配置(BaseModel):
    """陨圣相关区域"""
    # 陨圣相关区域配置
    陨圣页面祖龙次数区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(697, 586, 756, 614))
    陨圣页面火凤次数区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(695, 612, 756, 635))
    陨圣页面前往挑战按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1003, 629, 1096, 656))
    陨圣战场祖龙剩余次数区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(177, 42, 232, 73))
    陨圣战场祖龙存活次数区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(129, 41, 168, 78))
    陨圣战场火凤剩余次数区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(180, 75, 231, 107))
    陨圣战场火凤存活次数区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(121, 80, 165, 110))
    陨圣战场号角数量区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(160, 136, 188, 165))
    陨圣战场目标名字区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(85, 107, 190, 134))
    陨圣战场目标血量区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(111, 133, 160, 152))
    陨圣战场归属玩家名字区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(41, 148, 238, 170))
    陨圣战场抢归属召唤按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(71, 175, 208, 209))
    陨圣页面太古秘境标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(727, 240, 823, 265))
    太古秘境页面太古层数区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(487, 292, 604, 333))
    太古秘境页面太古体力值区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(678, 651, 767, 677))
    太古刷新标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(649, 369, 755, 400))
    太古刷新标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(949, 368, 1027, 399))
    太古刷新标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(666, 558, 736, 588))
    太古刷新标签4: 区域坐标 = Field(default_factory=lambda: 区域坐标(946, 558, 1030, 587))
    太古前往标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(776, 355, 859, 383))
    太古前往标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(1064, 357, 1148, 385))
    太古前往标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(772, 545, 859, 574))
    太古前往标签4: 区域坐标 = Field(default_factory=lambda: 区域坐标(1062, 547, 1149, 572))
 
    def 获取刷新标签(self, 索引: int) -> Optional[区域坐标]:
        return getattr(self, f"太古刷新标签{索引}", None)
    def 获取前往标签(self, 索引: int) -> Optional[区域坐标]:
        return getattr(self, f"太古前往标签{索引}", None)
# ==================== 日常强化相关配置 ====================

class 日常强化相关配置(BaseModel):
    """日常强化相关区域"""
    打金宝库剩余次数区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1092, 577, 1193, 607))
    打金宝库回收框红点区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(496, 465, 951, 651))
    打金宝库回收不再提示区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(770, 427, 805, 465))
    打金宝库回收不再提示关闭按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(919, 478, 998, 509))
    开服活动内容清单显示区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(496, 233, 576, 671))
    登录领取奖励按钮带红点显示区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(944, 580, 1063, 645))
    每日必买奖励按钮带红点显示区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(639, 592, 763, 646))
    每日必买奖励奖品文字区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(646, 375, 771, 404))
    在线奖励领取奖励按钮带红点区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1055, 339, 1189, 385))
    寻宝终身卡奖励红点范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(916, 281, 1203, 651))
    强星上部分页卡红点范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(473, 224, 734, 280))
    强星按钮带红点范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(897, 624, 1019, 675))
    自动强星按钮带红点范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(986, 625, 1101, 674))
    涅槃升级按钮带红点范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(900, 627, 1035, 673))
    传世升级装备带红点范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(474, 223, 945, 658))
    传世升级按钮带红点范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1000, 626, 1128, 677))
    暗殿提升按钮带红点范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(970, 619, 1111, 662))
    神兵升级按钮带红点范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(966, 597, 1111, 650))
    神兵等级按钮带红点范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(484, 428, 560, 507))
    神兵全天赋按钮带红点范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(497,247,934,653))
    神兵等级升级按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1012, 645, 1103, 672))
    神兵等级升级页面关闭小区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1234,183,1256,220))
    幻装上部分页卡红点范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(468, 225, 1215, 276))
    幻装激活球带红点范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(520, 304, 942, 603))
    幻装激活球激活按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(668, 637, 756, 664))
    幻装累计属性按钮带红点区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(679, 600, 749, 677))
    幻装长安升级按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(790, 611, 881, 639))
    幻装长安升级完成颜色核对区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(793, 570, 881, 646))
    幻装长安升级页关闭区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1067, 285, 1163, 371))
    星辰升级按钮带红点标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1003, 626, 1133, 681))
    星辰升级切换带红点标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(495, 604, 898, 667))
    使用道具小卡道具名称标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1466, 457, 1565, 481))
    使用道具小卡使用按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1484, 489, 1551, 515))
    使用道具小卡关闭按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1595, 356, 1612, 384))
    使用道具小卡使用按钮标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(1384, 479, 1451, 507))


# ==================== 合成相关配置 ====================

class 合成相关配置(BaseModel):
    """合成相关区域"""
    合成左分类卡区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(473, 228, 598, 675))
    合成中分类卡区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(595, 227, 730, 680))
    合成打造含红点区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(905, 611, 1025, 662))
    熔炼页面熔炼按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(799, 362, 877, 388))
    锻造页面打造按钮含红点标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(853, 597, 965, 648))


# ==================== 合成相关配置 ====================

class 炼器宝阁相关配置(BaseModel):
    """ """
    炼器宝阁宝阁信息区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(662,246,1161,672))
    炼器宝阁主页面当前占领对象名称标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(847,238,955,274))
    炼器宝阁主页面占领剩余次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(737,550,798,584))
    炼器宝阁主页面抢夺剩余次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1028,553,1088,580))
    炼器宝阁拖拽区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(647,329,685,592))
    炼器宝阁战斗结果情况标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(676,394,1014,486))
    炼器宝阁被抢夺后进入确定提示区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(908,478,1002,509))
    炼器宝阁被抢夺后冒号进入提示区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(743,386,959,424))
    炼器宝阁占领成功提示区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(807,479,893,507))
    
   


# ==================== 图鉴强化相关配置 ====================

class 图鉴强化相关配置(BaseModel):
    """图鉴强化相关区域"""
    图鉴页面激活按钮带红点区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1040, 618, 1177, 673))
    图鉴页面精英按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(487, 234, 579, 263))
    图鉴页面BOSS按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(604, 234, 699, 263))
    炼妖炉完成提示区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(623, 560, 684, 669))
    炼化丹药右位带红点按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(833, 313, 931, 404))
    炼化丹药左位带红点按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(515, 312, 604, 404))
    炼化丹药放入文字群标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(845, 245, 988, 653))
    炼化丹药关闭按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(961, 202, 1060, 284))

# ==================== 聊天相关配置 ====================

class 聊天相关配置(BaseModel):
    """聊天相关区域"""
    当前频道显示标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(549, 855, 593, 874))
    频道选项卡区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(558, 680, 597, 852))
    发送按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1109, 858, 1142, 870))
    发送坐标区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(523, 747, 556, 855))
    第一行文字区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(551, 826, 1139, 850))
    聊天输入区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(618, 858, 819, 871))

# ==================== 主界面配置（单独定义，避免循环引用） ====================

class 主界面配置(BaseModel):
    """主界面相关区域"""
    小地图敌人显示标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1585, 30, 1696, 124))
    小地图安全危险显示标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1582, 123, 1644, 141))
    小地图地图名显示标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1580, 2, 1698, 23))
    小地图商店文字范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1548, -2, 1586, 72))
    小地图坐标显示标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1645, 115, 1697, 147))
    中间地图内容范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(485, 259, 1063, 650))
    复活按钮范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(906, 207, 1218, 355))
    第一排任务区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1126, 4, 1513, 80))
    第二三排任务区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(814, 84, 1521, 330))
    任务小页面检查区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(891, 206, 1613, 306))
    任务帘带红点区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1514, 0, 1559, 32))
    中间页面名称区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(510, 185, 622, 222))
    行会按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(549, 739, 574, 747))
    合成按钮带红点区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(627, 728, 667, 754))
    光翼按钮带红点区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(705, 728, 750, 755))
    强星按钮带红点区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(783, 730, 825, 754))
    图鉴按钮带红点区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(828, 730, 865, 754))
    下方第三个技能按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(838, 690, 862, 713))
    下方第五个技能按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(951, 682, 981, 712))
    下方技能按钮总区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(696,665,999,732))
    自动战斗区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1308, 606, 1368, 677))
    自动战斗按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1326, 630, 1351, 654))
    自动走位区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1244, 597, 1306, 684))
    自动走位按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1265, 633, 1291, 658))
    摇人按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(374, 393, 480, 536))
    退出按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(280, 182, 321, 221))
    关闭按钮搜寻区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(743, 162, 1642, 354))
    关闭按钮搜寻中区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(831, 306, 1320, 536))
    普通boss召唤按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(547, 441, 680, 501))
    目标信息显示区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(741, 1, 964, 66))
    目标血条下归属区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(752, 41, 942, 63))
    目标血条血量区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(817, 25, 885, 44))
    服务器喇叭文字显示区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(587, 65, 1111, 94))
    保护20秒读秒数字区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(735, 95, 885, 166))
    任务结束确定领取奖励区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(755, 519, 948, 731))
    中间任务结束按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(759,449,935,538))
    传送点立即前往文字区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(37, 118, 178, 159))
    请求协助内容窗口区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1293, 173, 1658, 289))
    请求协助按钮窗口区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1293, 286, 1647, 364))
    右上角关闭不在提示区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1332, 271, 1506, 372))
    中间关闭不在提示区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(745, 471, 828, 539))
    角色状态按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1184, 726, 1203, 745))
    角色名字区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(204, 46, 352, 77))
    角色面板右侧状态标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(472, 218, 492, 249))
    角色状态面板职业文字标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(111, 95, 201, 137))
    角色面板关闭按钮范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(431, 48, 536, 171))
    敌人面板开闭按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1228, 524, 1264, 554))
    敌人面板范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(6, 329, 374, 498))
    玩家血球百分之三十范围标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(426, 812, 462, 816))
    玩家血球自定义血条区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(429,731,437,857))
    沙巴克外城小地图9080点位: 区域坐标 = Field(default_factory=lambda: 区域坐标(724, 403, 731, 408))
    决战沙巴克进入房间点击位置范围: 区域坐标 = Field(default_factory=lambda: 区域坐标(639, 107, 743, 182))
    空闲区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(12, 344, 15, 353))
    小地图中心区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(759, 439, 766, 444))
    小地图中心位置复查点击区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(729,404,814,467))
    提示划动区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1294, 79, 1336, 122))
    左上领取奖励区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(45, 123, 164, 152))
    讨伐页面领取奖励区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(844, 628, 928, 656))    

    #公共区域提示指感叹号等
    公共提示区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(509,570,710,668)) 
    背包按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1232,706,1250,719))
    


    
    # 特殊退出
    魔神禁地退出确认区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(871, 458, 1050, 522))
class 商店购买(BaseModel):
    商店按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1270,773,1290,794))
    商店标题按钮区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(474,231,1209,264))
    商店页面货物名称查询区域标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(479,267,1201,543)) 
    商店页面购买按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1066,637,1160,667))  
    商店页面道具购买MAX按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(916,460,946,476))
    商店页面道具购买购买按钮: 区域坐标 = Field(default_factory=lambda: 区域坐标(792,545,877,574))

class 特殊活动(BaseModel):
    """"""
    开服活动右侧小标签红点检查区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1217,263,1253,614))
    怪物试炼活动倒计时文字区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(950,304,1082,338))
    怪物试炼活动领取奖励按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1069,348,1174,380))
    左上角活动检查区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(341,143,481,198))
    节日福利领取奖励按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1072,348,1171,380))
    节日试炼积分领取按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1126,297,1211,330))    
    节日试炼积分奖励红点搜寻区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(607,236,994,678))
    
    节日试炼五天模式第三天文字区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(825,365,899,390))
    节日试炼五天模式五天标题区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(608,355,1114,397))
    节日试炼五天模式领取每日奖励区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1131,410,1191,675))
    节日试炼五天模式领取每周奖励区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(656,222,1168,321))
    节日犒赏领取区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(873,383,1194,664))


    灵符特惠购买按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(650,605,749,639))
    灵符特惠礼包信息区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(655,464,695,484))
    连充豪礼页面已充值金额区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1030,309,1186,345))
    每日累充页面领取宝箱按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(649,612,789,662))
    连充豪礼页面领取范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1100,352,1198,674))
    连充豪礼页面天数范围区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(850,348,907,669))
    连充豪礼页面金额奖励区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(608,303,1005,343))
    红包使用信息提示区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(744,348,927,388))
    红包数量输入区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(810,396,860,427))
    红包使用按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(908,461,992,490))
    红包取消按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(700,459,780,490))
    红包提示信息搜寻区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(780,400,900,530))
    福利BOSS前往按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(637,621,777,671))
    抢红包界面红包出现范围: 区域坐标 = Field(default_factory=lambda: 区域坐标(796,242,987,669))
    抢红包界面红包出现抢红包按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(903,429,1037,554))
    抢红包界面抢红包返回按钮: 区域坐标 = Field(default_factory=lambda: 区域坐标(936,569,1007,594))


    




class 传奇之路相关(BaseModel):
    """"""
    传奇之路查看队伍按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(968,593,1063,626))
    传奇之路我的队伍按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1087,595,1184,625))
    传奇之路开始挑战按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(802,578,897,607))
    传奇之路通关成功提示文字区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(48,177,170,213))
    传奇之路返回按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(805,573,900,606))
    传奇之路入口层数信息区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(778,262,919,300))


class 至尊联赛相关(BaseModel):
    """"""
    迷阵夺旗进入按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(804,634,899,667))
    迷阵夺旗世界赛程按钮区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(1262,326,1285,363))
    迷阵夺旗死亡问号校正区域: 区域坐标 = Field(default_factory=lambda: 区域坐标(189,29,239,75))
    迷阵夺旗按钮翡翠荣耀旗: 区域坐标 = Field(default_factory=lambda: 区域坐标(59,177,87,188))
    迷阵夺旗按钮金岩霸者旗: 区域坐标 = Field(default_factory=lambda: 区域坐标(118,176,154,190))
    迷阵夺旗按钮赤焰战神旗: 区域坐标 = Field(default_factory=lambda: 区域坐标(186,176,216,190))

class 焚天炎域页面(BaseModel):
    """"""
    焚天炎域刷新时间标签1: 区域坐标 = Field(default_factory=lambda: 区域坐标(983,525,1078,550))
    焚天炎域刷新时间标签2: 区域坐标 = Field(default_factory=lambda: 区域坐标(886, 500, 960, 527))
    焚天炎域刷新时间标签3: 区域坐标 = Field(default_factory=lambda: 区域坐标(1096,500,1170,528))
    焚天炎域前往挑战按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(977, 634, 1078, 666))
    焚天炎域剩余次数按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(994, 595, 1094, 629))
    焚天炎域右侧禁地按钮标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1228, 327, 1248, 368))
    焚天炎域禁地页面禁地次数标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(772, 637, 891, 667))
    焚天炎域禁地页面前往挑战标签: 区域坐标 = Field(default_factory=lambda: 区域坐标(1042,624,1138,653))
    焚天禁地中间地图检索范围: 区域坐标 = Field(default_factory=lambda: 区域坐标(471,226,1072,665))

class 焚天禁地地图位置配置(BaseModel):
    """诸神遗迹BOSS地图位置，喜怒哀乐泰坦"""
    位置1: 区域坐标 = Field(default_factory=lambda: 区域坐标(525,303,578,348))
    位置2: 区域坐标 = Field(default_factory=lambda: 区域坐标(818,254,869,298))
    位置3: 区域坐标 = Field(default_factory=lambda: 区域坐标(506,496,565,546))
    位置4: 区域坐标 = Field(default_factory=lambda: 区域坐标(769,557,834,613))
    位置5: 区域坐标 = Field(default_factory=lambda: 区域坐标(967,408,1026,465))
    
    def 获取(self, 索引: int) -> Optional[区域坐标]:
        return getattr(self, f"位置{索引}", None)
    
class 焚天禁地地图刷新时间区域配置(BaseModel):
    """诸神遗迹BOSS地图位置，喜怒哀乐泰坦"""
    位置1: 区域坐标 = Field(default_factory=lambda: 区域坐标(573,540,658,571))
    位置2: 区域坐标 = Field(default_factory=lambda: 区域坐标(583,340,655,365))
    位置3: 区域坐标 = Field(default_factory=lambda: 区域坐标(890,340,970,369))
    位置4: 区域坐标 = Field(default_factory=lambda: 区域坐标(891,528,975,561))
    位置5: 区域坐标 = Field(default_factory=lambda: 区域坐标(731,433,816,460))
    
    def 获取(self, 索引: int) -> Optional[区域坐标]:
        return getattr(self, f"位置{索引}", None)

class 首领合成入口右侧标签坐标池(BaseModel):
    """页面A的坐标池（5个可能的位置）"""
    位置1: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226, 252, 1249, 300))
    位置2: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226, 325, 1249, 372))
    位置3: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226, 396, 1249, 443))
    位置4: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226, 467, 1249, 517))
    位置5: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226, 539, 1249, 587))
    
    def 获取所有位置(self) -> List[区域坐标]:
        """获取所有位置坐标"""
        return [self.位置1, self.位置2, self.位置3, self.位置4, self.位置5]
class 战场光翼图鉴页面右侧标签坐标池(BaseModel):
    """页面A的坐标池（5个可能的位置）"""
    位置1: 区域坐标 = Field(default_factory=lambda: 区域坐标( 1226,251,1250,301))
    位置2: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226,327,1250,379))
    位置3: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226,406,1250,458))
    位置4: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226, 484, 1250, 535))
    位置5: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226,563,1250,614))
    
    def 获取所有位置(self) -> List[区域坐标]:
        """获取所有位置坐标"""
        return [self.位置1, self.位置2, self.位置3, self.位置4, self.位置5]
    
class 神界战灵坐骑古剑页面右侧标签坐标池(BaseModel):
    """页面A的坐标池（5个可能的位置）"""
    位置1: 区域坐标 = Field(default_factory=lambda: 区域坐标( 1226,251,1250,301))
    位置2: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226,327,1250,379))
    位置3: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226,406,1250,458))
    位置4: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226, 484, 1250, 535))
    
    def 获取所有位置(self) -> List[区域坐标]:
        """获取所有位置坐标"""
        return [self.位置1, self.位置2, self.位置3, self.位置4]
    
class 强星页面右侧标签坐标池(BaseModel):
    """页面A的坐标池（5个可能的位置）"""
    位置1: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226, 252, 1249, 300))
    位置2: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226, 325, 1249, 372))
    位置3: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226, 396, 1249, 443))
    位置4: 区域坐标 = Field(default_factory=lambda: 区域坐标(1226, 467, 1249, 517))    
    
    def 获取所有位置(self) -> List[区域坐标]:
        """获取所有位置坐标"""
        return [self.位置1, self.位置2, self.位置3, self.位置4]
# ==================== 主区域配置 ====================

class 区域配置(BaseModel):
    """
    区域配置 - 完整多级配置
    
    使用方式：
        配置 = 区域配置.创建默认()
        配置.应用全局偏移(8, 30)
        
        # 访问配置
        地图区域 = 配置.主界面.小地图地图名显示标签
        攻击模式 = 配置.攻击模式.当前攻击模式显示区域标签
        神器1 = 配置.神器位置.位置1
    """
    
    # ========== 主界面区域 ==========
    主界面: 主界面配置 = Field(default_factory=lambda: 主界面配置())
    
    # ========== 子配置 ==========
    神器位置: 神器位置配置 = Field(default_factory=神器位置配置)
    攻击模式: 攻击模式配置 = Field(default_factory=攻击模式配置)
    掉线检查: 掉线检查配置 = Field(default_factory=掉线检查配置)
    boss相关: Boss相关配置 = Field(default_factory=Boss相关配置)
    专属BOSS: 专属BOSS配置 = Field(default_factory=专属BOSS配置)
    降魔: 降魔配置 = Field(default_factory=降魔配置)
    天关: 天关配置 = Field(default_factory=天关配置)
    行会: 行会配置 = Field(default_factory=行会配置)
    鱼塘: 鱼塘配置 = Field(default_factory=鱼塘配置)
    兽神: 兽神相关配置 = Field(default_factory=兽神相关配置)
    战场页面: 战场页面相关配置 = Field(default_factory=战场页面相关配置)
    暗殿: 暗殿相关配置 = Field(default_factory=暗殿相关配置)
    巅峰竞技: 巅峰竞技相关配置 = Field(default_factory=巅峰竞技相关配置)
    神兵: 神兵相关配置 = Field(default_factory=神兵相关配置)
    跨服入侵: 跨服入侵相关配置 = Field(default_factory=跨服入侵相关配置)
    跨服入侵旧: 跨服入侵相关旧配置 = Field(default_factory=跨服入侵相关旧配置)
    主宰: 主宰相关配置 = Field(default_factory=主宰相关配置)
    坐骑: 坐骑相关配置 = Field(default_factory=坐骑相关配置)
    古剑: 古剑相关配置 = Field(default_factory=古剑相关配置)
    大千世界入口: 大千世界各任务入口配置 = Field(default_factory=大千世界各任务入口配置)
    神界大陆: 神界大陆相关配置 = Field(default_factory=神界大陆相关配置)
    神界战场: 神界战场相关配置 = Field(default_factory=神界战场相关配置)
    诸神遗迹: 诸神遗迹相关配置 = Field(default_factory=诸神遗迹相关配置)
    诸神遗迹BOSS地图位置: 诸神遗迹BOSS地图位置配置 = Field(default_factory=诸神遗迹BOSS地图位置配置)
    诸神遗迹BOSS地图刷新时间区域: 诸神遗迹BOSS地图刷新时间区域配置 = Field(default_factory=诸神遗迹BOSS地图刷新时间区域配置)    
    # 修罗魔域
    修罗魔域: 修罗魔域相关配置 = Field(default_factory=修罗魔域相关配置)    
    # 圣兽试炼
    圣兽试炼: 圣兽试炼相关配置 = Field(default_factory=圣兽试炼相关配置)    
    # 圣兽宝库
    圣兽宝库: 圣兽宝库相关配置 = Field(default_factory=圣兽宝库相关配置)    
    # 虚空剑界
    虚空剑界: 虚空剑界相关配置 = Field(default_factory=虚空剑界相关配置)    
    # 决战盟重
    决战盟重: 决战盟重相关配置 = Field(default_factory=决战盟重相关配置)    
    # 五行洞天
    五行洞天: 五行洞天相关配置 = Field(default_factory=五行洞天相关配置)    
    # 跨服争霸
    跨服争霸: 跨服争霸相关配置 = Field(default_factory=跨服争霸相关配置)    
    # 群星圣域
    群星圣域: 群星圣域相关配置 = Field(default_factory=群星圣域相关配置)    
    # 魔神禁地
    魔神禁地: 魔神禁地相关配置 = Field(default_factory=魔神禁地相关配置)    
    # 飞升灵境
    飞升灵境: 飞升灵境相关配置 = Field(default_factory=飞升灵境相关配置)    
    # 异界夺宝
    异界夺宝: 异界夺宝相关配置 = Field(default_factory=异界夺宝相关配置)    
    # 双倍押镖
    双倍押镖: 双倍押镖相关配置 = Field(default_factory=双倍押镖相关配置)    
    # 日常强化
    日常强化: 日常强化相关配置 = Field(default_factory=日常强化相关配置)    
    # 合成
    合成: 合成相关配置 = Field(default_factory=合成相关配置)    
    # 图鉴强化
    图鉴强化: 图鉴强化相关配置 = Field(default_factory=图鉴强化相关配置)
    # 聊天
    聊天: 聊天相关配置 = Field(default_factory=聊天相关配置)
    # 陨圣相关
    陨圣: 陨圣相关配置 = Field(default_factory=陨圣相关配置)
    # 焚天炎域
    焚天炎域: 焚天炎域页面 = Field(default_factory=焚天炎域页面)
    # 焚天禁地
    焚天禁地地图位置: 焚天禁地地图位置配置 = Field(default_factory=焚天禁地地图位置配置)
    # 焚天禁地
    焚天禁地地图刷新时间区域: 焚天禁地地图刷新时间区域配置 = Field(default_factory=焚天禁地地图刷新时间区域配置)
    # 炼器宝阁
    炼器宝阁: 炼器宝阁相关配置 = Field(default_factory=炼器宝阁相关配置)
    # 特殊活动
    各种活动: 特殊活动 = Field(default_factory=特殊活动)
    # 至尊联赛
    至尊联赛: 至尊联赛相关 = Field(default_factory=至尊联赛相关)
    # 商店购买
    商店: 商店购买 = Field(default_factory=商店购买)
    # 传奇之路
    传奇之路: 传奇之路相关 = Field(default_factory=传奇之路相关)

    首领合成页面右侧标签坐标池: 首领合成入口右侧标签坐标池 = Field(default_factory=首领合成入口右侧标签坐标池)    
    战场光翼图鉴页面右侧坐标池: 战场光翼图鉴页面右侧标签坐标池 = Field(default_factory=战场光翼图鉴页面右侧标签坐标池)
    神界战灵坐骑古剑页面右侧坐标池: 神界战灵坐骑古剑页面右侧标签坐标池 = Field(default_factory=神界战灵坐骑古剑页面右侧标签坐标池)
    强星页面右侧坐标池: 强星页面右侧标签坐标池 = Field(default_factory=强星页面右侧标签坐标池)
    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def 创建默认(cls) -> '区域配置':
        """创建默认配置"""
        return cls()
    
    # @classmethod
    # def 从字典加载(cls, 数据: dict) -> '区域配置':
    #     """从字典加载配置"""
    #     def 转换区域(值):
    #         if isinstance(值, dict) and all(k in 值 for k in ['左', '上', '右', '下']):
    #             return 区域坐标(值['左'], 值['上'], 值['右'], 值['下'])
    #         elif isinstance(值, dict):
    #             return {k: 转换区域(v) for k, v in 值.items()}
    #         elif isinstance(值, list):
    #             return [转换区域(v) for v in 值]
    #         return 值
        
    #     转换后数据 = {k: 转换区域(v) for k, v in 数据.items()}
    #     return cls(**转换后数据)

    @classmethod
    def 从字典加载(cls, 数据: dict) -> '区域配置':
        def 转换区域(值):
            if isinstance(值, dict) and all(k in 值 for k in ['左', '上', '右', '下']):
                return 区域坐标(值['左'], 值['上'], 值['右'], 值['下'])
            elif isinstance(值, dict):
                return {k: 转换区域(v) for k, v in 值.items()}
            elif isinstance(值, list):
                return [转换区域(v) for v in 值]
            return 值
        
        转换后数据 = {k: 转换区域(v) for k, v in 数据.items()}
        
        # 调试
        if '炼器宝阁' in 转换后数据:
            print(f"炼器宝阁类型: {type(转换后数据['炼器宝阁'])}")
            print(f"炼器宝阁内容: {转换后数据['炼器宝阁']}")
        
        结果 = cls(**转换后数据)
        
        # 调试
        print(f"加载后炼器宝阁类型: {type(结果.炼器宝阁)}")
        
        return 结果
    
    @classmethod
    def 从文件加载(cls, 文件名: str = "region_config.json") -> '区域配置':
        """从JSON文件加载配置"""
        文件路径 = path_mgr.get_config_path(文件名)
        if not Path(文件路径).exists():
            print(f"[区域配置] 文件不存在: {文件路径}，使用默认配置")
            return cls.创建默认()
        
        with open(文件路径, 'r', encoding='utf-8') as f:
            数据 = json.load(f)
        
        print(f"[区域配置] 从文件加载: {文件路径}")
        return cls.从字典加载(数据)
    
    def 保存到文件(self, 文件名: str = "region_config.json"):
        """保存配置到JSON文件"""
        文件路径 = path_mgr.get_config_path(文件名)
               
        def 转换值(值):
            if isinstance(值, 区域坐标):
                return 值.转字典()
            elif isinstance(值, BaseModel):
                return 值.dict()
            elif isinstance(值, dict):
                return {k: 转换值(v) for k, v in 值.items()}
            elif isinstance(值, list):
                return [转换值(v) for v in 值]
            return 值
        
        数据 = {k: 转换值(v) for k, v in self.__dict__.items() if not k.startswith('_')}
        
        with open(文件路径, 'w', encoding='utf-8') as f:
            json.dump(数据, f, ensure_ascii=False, indent=2)
        
        print(f"[区域配置] 保存到文件: {文件路径}")
    
    def 应用全局偏移(self, offset_x: int, offset_y: int):
        """应用全局偏移到所有区域"""
        区域坐标.设置当前线程偏移 (offset_x, offset_y)
        
        def 重新计算(值):
            if isinstance(值, 区域坐标):
                值._重新计算偏移()
            elif isinstance(值, BaseModel):
                for 子值 in 值.__dict__.values():
                    重新计算(子值)
            elif isinstance(值, dict):
                for 子值 in 值.values():
                    重新计算(子值)
            elif isinstance(值, list):
                for 子值 in 值:
                    重新计算(子值)
        
        重新计算(self)
        print(f"[区域配置] 已应用全局偏移: X={offset_x}, Y={offset_y}")
    
    def 打印所有区域(self):
        """打印所有区域配置"""
        print("\n" + "=" * 60)
        print("区域配置列表")
        print("=" * 60)
        
        def 打印(名称, 值, 层级=0):
            缩进 = "  " * 层级
            if isinstance(值, 区域坐标):
                print(f"{缩进}{名称}: {值}")
            elif isinstance(值, BaseModel):
                print(f"{缩进}{名称}:")
                for 子名, 子值 in 值.__dict__.items():
                    if not 子名.startswith('_'):
                        打印(子名, 子值, 层级 + 1)
            elif isinstance(值, dict):
                print(f"{缩进}{名称}:")
                for 子名, 子值 in 值.items():
                    打印(子名, 子值, 层级 + 1)
        
        for 名称, 值 in self.__dict__.items():
            if not 名称.startswith('_'):
                打印(名称, 值)
        
        print("=" * 60)





# 更新区域配置中的主界面类型引用
区域配置.model_rebuild()


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("测试完整多级区域配置")
    print("=" * 60)
    
    # 测试1：创建配置
    print("\n[测试1] 创建默认配置")
    配置 = 区域配置.创建默认()
    
    print(f"  主界面.小地图地图名显示标签: {配置.主界面.小地图地图名显示标签}")
    print(f"  攻击模式.当前攻击模式显示区域标签: {配置.攻击模式.当前攻击模式显示区域标签}")
    print(f"  神器位置.位置1: {配置.神器位置.位置1}")
    print(f"  boss相关.BOSS页面进入第一层位置: {配置.boss相关.BOSS页面进入第一层位置}")
    print(f"  降魔.降魔页面剩余次数区域标签: {配置.降魔.降魔页面剩余次数区域标签}")
    # 配置.天关.天关扫荡页面扫荡按钮标签.元组
    # 测试2：随机点
    print("\n[测试2] 随机点测试")
    随机点 = 配置.主界面.自动战斗按钮标签.随机点(0.8)
    print(f"  自动战斗按钮随机点: {随机点}")
    
    # 测试3：全局偏移
    print("\n[测试3] 应用全局偏移")
    配置.应用全局偏移(8, 30)
    print(f"  偏移后小地图地图名: {配置.主界面.小地图地图名显示标签}")
    print(f"  偏移后自动战斗按钮随机点: {配置.主界面.自动战斗按钮标签.随机点()}")
    
    # 测试4：保存JSON
    print("\n[测试4] 保存配置")
    配置.保存到文件("region_config.json")
    
    # # 测试5：加载JSON
    # print("\n[测试5] 加载配置")
    # 新配置 = 区域配置.从文件加载("region_config.json")
    # print(f"  加载后小地图地图名: {新配置.主界面.小地图地图名显示标签}")
    
    # # 测试6：重置偏移
    # print("\n[测试6] 重置偏移")
    # # 区域坐标.重置全局偏移()
    # 新配置.应用全局偏移(0, 0)
    # print(f"  重置后小地图地图名: {新配置.主界面.小地图地图名显示标签}")
    
    # # 测试7：打印所有区域
    # print("\n[测试7] 打印所有区域（仅显示前10个）")
    # print("  主界面配置项:")
    # for i, (键, 值) in enumerate(配置.主界面.__dict__.items()):
    #     if i >= 10:
    #         print(f"  ... 共 {len(配置.主界面.__dict__.items())} 项")
    #         break
    #     if not 键.startswith('_'):
    #         print(f"    {键}: {值}")
    
    # print("\n[测试完成]")
    # print(f"  主界面.小地图地图名显示标签: {配置.主界面.小地图地图名显示标签}")
    # print(区域坐标.获取当前线程偏移())
    # 配置 = 区域配置.从文件加载("region_config.json")
    # print(f"  加载后小地图地图名: {配置.诸神遗迹BOSS地图位置.位置1.元组}")
    # # print(区域配置.大千世界入口.大千世界页面五行洞天按钮标签.元组)
    # 新配置.应用全局偏移(10, 20)
    # 区域1=区域坐标(1,2,300,400)
    # 区域2=区域坐标(300,400,1000,2000)
    # print(区域1.元组)
    # print(区域2)

    