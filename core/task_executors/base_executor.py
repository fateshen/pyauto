# core/task_executors/base_executor.py
"""
任务执行器基类

所有任务执行器的基类，定义执行接口
"""
from abc import ABC, abstractmethod
import time
from typing import  TYPE_CHECKING, Optional, Tuple
from core.utils import 提取次数,解析坐标范围,解析中心坐标,匹配分组关键字
from core.debug import 调试器


# 解决循环导入，同时提供类型提示
if TYPE_CHECKING:    
    from models.game_config import 游戏全局配置
    from models.task_config import 任务配置基类
    from models.task_state import 任务状态基类
    from core.runtime_state import 运行时公共变量
    from core.page_operations import 页面操作集
    from models.dynamic_tags import 动态标签
    from core.window_thread import 窗口线程
    from core.common_operations import 通用操作集
    from core.assistant import 战斗辅助识别器

class 任务执行器基类(ABC):
    """
    任务执行器基类
    
    所有任务执行器必须继承此类并实现 执行 方法
    """
    
    def __init__(self, 线程, 任务配置, 任务状态):
        """
        初始化任务执行器
        
        参数:
            线程: 窗口线程实例
            任务配置: 任务配置对象
            任务状态: 任务状态对象
        """
        self.线程:'窗口线程' = 线程
        self.页面:'页面操作集' = 线程.页面
        self.游戏配置:'游戏全局配置' =  线程.游戏配置
        self.任务配置:'任务配置基类' = 任务配置
        self.任务状态:'任务状态基类' = 任务状态
        self.公共变量: '运行时公共变量' = 线程.公共变量
        self.动态标签:'动态标签'=线程.动态标签
        self.辅助识别器:'战斗辅助识别器' = 线程.辅助识别器
        self.通用操作: '通用操作集' = 线程.通用操作
    @abstractmethod
    def 执行(self) -> str:
        """
        执行任务
        
        返回:
            "完成": 任务完成
            "进行中": 任务执行中
            "等待": 等待条件
            "失败": 任务失败
        """
        pass
    @property
    def 调试分类(self) -> str:
        """获取调试分类名"""
        return getattr(self.任务配置, '调试分类', '') or self.任务配置.任务名称
    @property
    def 启用自动走位(self) -> bool:
        """获取自动走位状态，没有任务配置时使用全局配置"""
        return self.任务配置.启用自动走位 if self.任务配置.启用自动走位 is not None else self.游戏配置.玩家.战斗.自动战斗.启用自动走位
    
    @property
    def 启用自动战斗(self) -> bool:
        """获取自动战斗状态，没有任务配置时使用全局配置"""
        return self.任务配置.启用自动战斗 if self.任务配置.启用自动战斗 is not None else self.游戏配置.玩家.战斗.自动战斗.启用自动战斗

    def 应用窗口偏移(self, 坐标: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        """
        将坐标应用当前线程的窗口偏移
        
        参数:
            坐标: (左, 上, 右, 下)
        
        返回:
            偏移后的坐标
        """
        偏移X = self.游戏配置.玩家.窗口偏移X
        偏移Y = self.游戏配置.玩家.窗口偏移Y
        
        if 偏移X == 0 and 偏移Y == 0:
            return 坐标
        
        return (
            坐标[0] + 偏移X,
            坐标[1] + 偏移Y,
            坐标[2] + 偏移X,
            坐标[3] + 偏移Y,
        )
    def 是否在副本中(self) -> bool:
        """判断是否在副本中（子类可重写）"""
        return getattr(self.任务状态, '是否在副本中', False)
    
    def 检查前置条件(self) -> bool:
        """检查任务前置条件（子类可重写）"""
        if hasattr(self.任务状态, '剩余次数') and self.任务状态.剩余次数 <= 0:
            return False
        
        if hasattr(self.任务状态, '下次刷新时间') and self.任务状态.下次刷新时间 > 0:
            提前秒数 = getattr(self.任务配置, '提前进场秒数', 0)
            
            if self.任务状态.下次刷新时间 - 提前秒数 > time.time():
                return False        
        return True
    def 更新区域任务次数(self,区域: Tuple[int, int, int, int],filter_config:Optional[dict] = None,规则:Optional[str]=None) -> int:
        """
        获取区域中的剩余次数
        
        参数:
            区域: 识别区域
            规则: 匹配规则，满足规则才是有效次数            

        返回:
            True: 识别成功，已更新剩余次数
            False: 识别失败
        """
        截图 = self.线程.截图
        if 截图 is None:
            截图= self.线程.刷新截图()
        if 截图 is None:
            调试器.debug(self.调试分类, "更新区域任务次数时截图失败")
            return False
        
        调试器.trace(self.调试分类, f"识别区域: {区域}")
        if filter_config:
            结果 = self.线程.文字识别器.recognize_text(
                截图, 区域,filter_config
            )
        else:
            结果 = self.线程.文字识别器.recognize_text(
                截图, 区域
            )
        
        if 结果:
            if 规则 is not None and not 匹配分组关键字(结果,规则):
                调试器.debug(self.调试分类, f"未匹配规则，规则: '{规则}',结果: '{结果}'")
                return False
            数字 = 提取次数(结果)
            if 数字>=0:
                self.任务状态.剩余次数 = 数字
                调试器.debug(self.调试分类, f"剩余次数: {self.任务状态.剩余次数},原始结果: '{结果}")
                return True
        
        调试器.trace(self.调试分类, f"未能识别次数，原始结果: '{结果}'")
        return False    
   
    # ==================== 自动战斗状态检测 ====================



    def 检查调整自动战斗状态(self, 启用自动战斗:Optional[bool]=None) -> bool:
        """
        调整自动战斗状态
        
        参数:
            启用自动战斗: True 开启 / False 停止
            不设参数则使用任务配置或全局配置
        
        返回:
            True: 成功切换或已为目标状态， False: 切换失败
        """
        if 启用自动战斗 is None:
            启用自动战斗 = self.启用自动战斗

        当前状态 = self.辅助识别器.获取自动战斗状态()
        
        if 当前状态 == -1:
            调试器.debug("自动战斗", "无法检测当前状态，跳过调整")
            return False
        
        # 判断是否需要切换
        需要开启 = (启用自动战斗  and 当前状态 == 0)
        需要停止 = (not 启用自动战斗  and 当前状态 == 1)
        
        if not 需要开启 and not 需要停止:
            调试器.trace("自动战斗", f"已是目标状态 ({'自动战斗中' if 当前状态 == 1 else '未开启'})，无需切换")
            return True
        
        # 点击自动战斗按钮
        按钮区域 = self.游戏配置.自动战斗按钮区域
        if not 按钮区域:
            调试器.warning("自动战斗", "未配置按钮区域")
            return False
        
        调试器.debug("自动战斗", f"{'开启' if 需要开启 else '关闭'}自动战斗")
        点击坐标 = 按钮区域.随机点(0.6)
        self.线程.动作执行器.click(点击坐标[0], 点击坐标[1])
        return True 
    # ==================== 自动走位状态检测 ====================

    def 检查调整自动走位状态(self, 启用自动走位: Optional[bool]=None) -> bool:
        """
        调整自动走位状态
        
        参数:
            启用自动走位: True 开启 / False 停止
            不设参数则使用任务配置或全局配置
        
        返回:
            True: 成功切换或已为目标状态， False: 切换失败
        """
        if 启用自动走位 is None:
            启用自动走位 = self.启用自动走位
               
        当前状态 = self.辅助识别器.获取自动走位状态()
        
        if 当前状态 == -1:
            调试器.debug("自动走位", "无法检测当前状态，跳过调整")
            return False
        
        # 判断是否需要切换
        需要开启 = (启用自动走位  and 当前状态 == 0)
        需要停止 = (not 启用自动走位  and 当前状态 == 1)
        
        if not 需要开启 and not 需要停止:
            调试器.trace("自动走位", f"已是目标状态 ({'自动走位中' if 当前状态 == 1 else '未开启'})，无需切换")
            return True
        
        # 点击自动走位按钮
        按钮区域 = self.游戏配置.区域.主界面.自动走位按钮标签
        if not 按钮区域:
            调试器.warning("自动走位", "未配置按钮区域")
            return False
        
        调试器.debug("自动走位", f"{'开启' if 需要开启 else '关闭'}自动走位")
        点击坐标 = 按钮区域.随机点(0.6)
        self.线程.动作执行器.click(点击坐标[0], 点击坐标[1])
            
        return True
    
    def _检查位置复查(self) -> Optional[str]:
        """
        提前进本时检查并调整位置
        
        触发条件：
        - 启用位置复查
        - 离BOSS刷新时间 > 触发提前秒数
        - 离上次复查 >= 间隔秒数
        - 复查次数 < 最大次数
        
        执行：
        - 获取当前坐标
        - 判断是否在目标范围内
        - 不在则移动到目标区域中心
        """
        if not self.任务配置.启用位置复查:
            return
        
        # 检查离刷新还有多少秒
        剩余等待秒数 = self.任务状态.下次刷新时间 - time.time()
        if 剩余等待秒数 <= self.任务配置.位置复查触发秒数:
            调试器.trace(self.调试分类, f"位置复查: 离刷新仅{剩余等待秒数:.1f}秒，停止复查")
            return
        
        # 检查复查间隔
        距上次复查秒数 = time.time() - self.任务状态.上次位置复查时间
        if 距上次复查秒数 < 5:
            调试器.trace(self.调试分类, f"位置复查: 距上次复查仅{距上次复查秒数:.1f}秒，跳过")
            return
        
        # 记录本次复查
        self.任务状态.上次位置复查时间 = time.time()
        self.任务状态.位置复查次数 += 1
        
        # 检查次数上限
        if self.任务状态.位置复查次数 >= 3:
            调试器.debug(self.调试分类, f"位置复查: 已达最大次数{3}，停止")
            return
        
        # 解析目标中心
        中心坐标 = 解析中心坐标(self.任务配置.位置复查目标中心)
        if not 中心坐标:
            调试器.warning(self.调试分类, "位置复查: 未配置目标中心或格式错误")
            return
        
        # 获取当前坐标
        当前坐标 = self.辅助识别器.获取当前玩家坐标()
        if 当前坐标 is None:
            调试器.debug(self.调试分类, "位置复查: 无法获取当前坐标")
            return
        
       
        当前x, 当前y = 当前坐标
        目标x, 目标y = 中心坐标
        距离 = ((当前x - 目标x)**2 + (当前y - 目标y)**2) ** 0.5
        # 判断是否在范围内
        if 距离 <= self.任务配置.位置复查目标半径:
            调试器.trace(self.调试分类, f"位置复查: 已在范围内(距离{距离:.0f}≤半径{self.任务配置.位置复查目标半径})")
            return
        
        # 移动到目标区域
        目标区域 = None
        if self.任务配置.位置复查移动区域:
            目标区域 =解析坐标范围( self.任务配置.位置复查移动区域 ) 
            if 目标区域 is not None:
                目标区域=self.应用窗口偏移(目标区域)
        if 目标区域 is None:
            目标区域= self.游戏配置.区域.主界面.小地图中心位置复查点击区域.元组        
        if 目标区域 is None:
            调试器.warning(self.调试分类, "位置复查: 未配置移动区域或格式错误")
            return    
        调试器.state(self.调试分类, f"位置复查({self.任务状态.位置复查次数}/{3}): ({当前x},{当前y})→({目标x},{目标y})")
        self.通用操作.打开地图移动到(目标区域)

    
        # ==================== 攻击模式检查与切换 ====================

    def 检查攻击模式(self) -> None:
        """
        检查并切换攻击模式
        
        流程：
        1. 判断是否已检查过（本次核验时间 > 任务切换时间）
        2. 判断是否在任务中（当前地图匹配当前任务）
        3. 获取设定模式
        4. 识别当前模式，不一致则切换
        """
        # 任务切换后已检查过，跳过
        if self.公共变量.本次攻击模式核验时间 > self.公共变量.任务切换时间:
            调试器.trace(self.调试分类, "攻击模式: 任务切换后已核验，跳过")
            return
        
        # 不在任务中（当前地图不匹配），跳过
        if not self.任务配置.匹配地图(self.线程.当前地图):
            调试器.trace(self.调试分类, "攻击模式: 当前地图不匹配任务，跳过")
            return
        
        # 获取设定模式
        设定模式 = self._获取攻击模式设定()
        if not 设定模式:
            调试器.trace(self.调试分类, "攻击模式: 未配置默认攻击模式，跳过")
            return
        
        调试器.debug(self.调试分类, f"攻击模式: 设定模式='{设定模式}'")
        
        # 识别当前模式
        当前模式 = self.辅助识别器.获取当前攻击模式()
        调试器.debug(self.调试分类, f"攻击模式: 当前模式='{当前模式}'")
        
        if 当前模式 == 设定模式:
            self.公共变量.本次攻击模式核验时间 = time.time()
            调试器.debug(self.调试分类, "攻击模式: 已是目标模式，无需切换")
            return
        
        # 需要切换
        self._切换攻击模式(设定模式)


    def _获取攻击模式设定(self) -> str:
        """获取攻击模式设定（任务配置优先，否则用全局配置）"""
        模式 = getattr(self.任务配置, '默认攻击模式', '')
        if not 模式:
            模式 = getattr(self.游戏配置.玩家, '默认攻击模式', '')
        return 模式


    def _切换攻击模式(self, 目标模式: str) -> None:
        """
        切换攻击模式
        
        步骤：
        1. 点击当前模式显示区域，展开模式选项卡
        2. 点击目标模式按钮
        3. 验证切换结果
        """
        调试器.state(self.调试分类, f"攻击模式: 切换 '{目标模式}'")
        
        # 获取模式对应的按钮配置
        按钮区域 = self._获取模式按钮区域(目标模式)
        if not 按钮区域:
            调试器.warning(self.调试分类, f"攻击模式: 未找到模式'{目标模式}'的按钮区域")
            return
        
        # 获取当前模式显示区域
        当前模式区域 = self.游戏配置.区域.攻击模式.当前攻击模式显示区域标签
        if not 当前模式区域:
            调试器.warning(self.调试分类, "攻击模式: 未配置当前模式显示区域")
            return
        
        # 获取展开后的选项卡区域
        展开区域 = self.游戏配置.区域.攻击模式.攻击模式展开显示区域标签
        if not 展开区域:
            调试器.warning(self.调试分类, "攻击模式: 未配置展开显示区域")
            return
        
        # 步骤1: 如果当前不是目标模式，打开选项卡
        # 验证文字"式"是否存在，存在说明选项卡区域已展开
        if not self.页面.创建_通用点击区域验证文字切换(
            当前模式区域.元组,
            展开区域.元组,
            "式",
            True,   # 切换后文字存在
            False   # 不先验证
        ).执行():
            调试器.warning(self.调试分类, "攻击模式: 展开选项卡失败")
            return
        
        # 步骤2: 点击目标模式按钮，验证选项卡关闭
        if not self.页面.创建_通用点击区域验证文字切换(
            按钮区域.元组,
            展开区域.元组,
            "式",
            False,  # 切换后文字消失（选项卡关闭）
            False   # 不先验证
        ).执行():
            调试器.warning(self.调试分类, f"攻击模式: 点击'{目标模式}'按钮失败")
            return
        
        # 验证最终结果
        当前模式 = self.辅助识别器.获取当前攻击模式()
        if 当前模式 == 目标模式:
            self.公共变量.本次攻击模式核验时间 = time.time()
            调试器.state(self.调试分类, f"攻击模式: 切换成功 '{目标模式}'")
        else:
            调试器.warning(self.调试分类, f"攻击模式: 切换后验证失败，当前='{当前模式}'，目标='{目标模式}'")


    def _获取模式按钮区域(self, 模式名: str):
        """根据模式名获取对应的按钮区域标签"""
        模式映射 = {
            "全体模式": "攻击模式全体模式按钮标签",
            "和平模式": "攻击模式和平模式按钮标签",
            "善恶模式": "攻击模式善恶模式按钮标签",
            "盟友模式": "攻击模式盟友模式按钮标签",
            "编组模式": "攻击模式编组模式按钮标签",
            "行会模式": "攻击模式行会模式按钮标签",
        }
        
        属性名 = 模式映射.get(模式名, '')
        if not 属性名:
            return None
        
        return getattr(self.游戏配置.区域.攻击模式, 属性名, None)

    
    