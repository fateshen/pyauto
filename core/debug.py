"""
调试日志系统 - 支持多线程独立日志文件，每天自动切换
"""
import os
import sys
import time
import threading
from typing import Optional, Dict
from enum import IntEnum
from pathlib import Path
from datetime import datetime


class DebugLevel(IntEnum):
    """调试级别（扩展版）"""
    NONE = 0      # 不输出
    ERROR = 1     # 只输出错误（导致功能中断）
    WARNING = 2   # 输出警告和错误（可恢复异常）
    INFO = 3      # 输出关键里程碑（任务开始/完成、线程启停、配置加载）
    STATE = 4     # 输出状态变更（进入副本、退出副本、次数耗尽、地图切换）
    DEBUG = 5     # 输出流程追踪（步骤尝试/成功、分支选择）
    TRACE = 6     # 输出数据细节（识别结果、像素数值、坐标耗时）
    VERBOSE = 7   # 输出所有细节（高频循环状态）


class 线程日志管理器:
    """
    线程日志管理器 - 支持每天自动切换日志文件
    
    每个线程维护独立的日志文件和调试配置
    """
    
    # 线程本地存储
    _线程本地 = threading.local()
    
    # 全局开关（影响所有线程）
    _全局启用: bool = True          # 总开关（False时完全不输出）
    _控制台启用: bool = True        # 控制台输出开关
    _文件启用: bool = True          # 文件输出开关
    
    # 默认配置
    _默认全局级别: DebugLevel = DebugLevel.STATE
    _默认分类级别: Dict[str, DebugLevel] = {}
    _默认显示时间戳: bool = True
    _默认启用颜色: bool = False
    _日志目录: str = "logs"
    
    @classmethod
    def _获取线程配置(cls):
        """获取当前线程的配置（懒加载）"""
        if not hasattr(cls._线程本地, '窗口名称'):
            cls._线程本地.窗口名称 = None
            cls._线程本地.全局级别 = cls._默认全局级别
            cls._线程本地.分类级别 = cls._默认分类级别.copy()
            cls._线程本地.显示时间戳 = cls._默认显示时间戳
            cls._线程本地.日志文件 = None      # 文件句柄
            cls._线程本地.当前日志日期 = None  # 当前日志文件的日期（用于检测跨天）
            cls._线程本地.最后输出分类 = None
        return cls._线程本地
    
    # ==================== 全局开关管理 ====================
    
    @classmethod
    def 设置启用(cls, 启用: bool):
        """
        设置日志总开关
        
        参数:
            启用: True=启用日志，False=完全不输出任何日志
        """
        cls._全局启用 = 启用
        status = "启用" if 启用 else "禁用"
        print(f"[日志开关] 日志系统已{status}")
    
    @classmethod
    def 设置控制台输出(cls, 启用: bool):
        """设置控制台输出开关"""
        cls._控制台启用 = 启用
        status = "启用" if 启用 else "禁用"
        print(f"[日志开关] 控制台输出已{status}")
    
    @classmethod
    def 设置文件输出(cls, 启用: bool):
        """设置文件输出开关"""
        cls._文件启用 = 启用
        status = "启用" if 启用 else "禁用"
        print(f"[日志开关] 文件输出已{status}")
    
    @classmethod
    def 是否启用(cls) -> bool:
        """检查日志系统是否启用"""
        return cls._全局启用
    
    # ==================== 文件管理（核心：跨天自动切换）====================
    
    @classmethod
    def _获取当前日期(cls) -> str:
        """获取当前日期字符串（线程安全）"""
        return datetime.now().strftime('%Y%m%d')
    
    @classmethod
    def _确保日志目录(cls):
        """确保日志目录存在"""
        if cls._文件启用:
            Path(cls._日志目录).mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def _获取日志文件路径(cls, 窗口名称: str, 日期: str) -> Path:
        """根据窗口名称和日期获取日志文件路径"""
        return Path(cls._日志目录) / f"{窗口名称}_{日期}.log"
    
    @classmethod
    def _打开日志文件(cls, 窗口名称: str, 日期: str):
        """打开日志文件（追加模式）"""
        cls._确保日志目录()
        日志路径 = cls._获取日志文件路径(窗口名称, 日期)
        return open(日志路径, 'a', encoding='utf-8')
    
    @classmethod
    def _写入文件(cls, 文件句柄, 消息: str):
        """写入文件并刷新"""
        if 文件句柄:
            try:
                文件句柄.write(消息 + "\n")
                文件句柄.flush()
            except Exception:
                pass  # 忽略写入错误，避免影响主逻辑
    
    @classmethod
    def _切换日志文件(cls):
        """
        检查并切换日志文件（跨天时自动切换）
        返回: 是否需要重新获取文件句柄
        """
        if not cls._文件启用:
            return False
        
        配置 = cls._获取线程配置()
        current_date = cls._获取当前日期()
        
        # 检查是否需要切换
        if 配置.日志文件 is None:
            return True  # 需要打开新文件
        if 配置.当前日志日期 != current_date:
            return True  # 日期变化，需要切换
        
        return False  # 无需切换
    
    @classmethod
    def _执行文件切换(cls):
        """执行实际的日志文件切换"""
        配置 = cls._获取线程配置()
        current_date = cls._获取当前日期()
        
        # 关闭旧文件
        if 配置.日志文件:
            try:
                # 写入切换标记
                cls._写入文件(配置.日志文件, "=" * 60)
                cls._写入文件(配置.日志文件, f"日志文件切换 - 日期变更")
                cls._写入文件(配置.日志文件, f"旧日期: {配置.当前日志日期}")
                cls._写入文件(配置.日志文件, f"新日期: {current_date}")
                cls._写入文件(配置.日志文件, "=" * 60)
                配置.日志文件.close()
            except Exception:
                pass
        
        # 打开新文件
        新路径 = cls._获取日志文件路径(配置.窗口名称, current_date)
        try:
            配置.日志文件 = open(新路径, 'a', encoding='utf-8')
            配置.当前日志日期 = current_date
            
            # 写入新文件开始标记
            cls._写入文件(配置.日志文件, "=" * 60)
            cls._写入文件(配置.日志文件, f"线程日志: {配置.窗口名称}")
            cls._写入文件(配置.日志文件, f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            cls._写入文件(配置.日志文件, f"日志文件: {新路径}")
            cls._写入文件(配置.日志文件, "=" * 60)
            
            if cls._控制台启用:
                print(f"[日志] 线程 '{配置.窗口名称}' 日志已切换到: {新路径}")
        except Exception as e:
            if cls._控制台启用:
                print(f"[日志错误] 无法创建日志文件 {新路径}: {e}")
            配置.日志文件 = None
            配置.当前日志日期 = None
    
    @classmethod
    def _确保日志文件(cls):
        """确保当前线程的日志文件已打开且日期正确"""
        if not cls._文件启用:
            return
        
        配置 = cls._获取线程配置()
        
        # 如果窗口名称未设置，无法创建日志文件
        if not 配置.窗口名称:
            return
        
        # 检查是否需要切换
        if cls._切换日志文件():
            cls._执行文件切换()
    
    @classmethod
    def 初始化线程(cls, 窗口名称: str):
        """
        初始化当前线程的日志（窗口线程启动时调用）
        
        参数:
            窗口名称: 窗口标识，用于区分不同线程的日志文件
        """
        if not cls._全局启用:
            return
        
        配置 = cls._获取线程配置()
        配置.窗口名称 = 窗口名称
        cls._确保日志目录()
        
        if cls._文件启用:
            current_date = cls._获取当前日期()
            try:
                日志路径 = cls._获取日志文件路径(窗口名称, current_date)
                配置.日志文件 = open(日志路径, 'a', encoding='utf-8')
                配置.当前日志日期 = current_date
                
                # 写入启动标记
                cls._写入文件(配置.日志文件, "=" * 60)
                cls._写入文件(配置.日志文件, f"线程启动: {窗口名称}")
                cls._写入文件(配置.日志文件, f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                cls._写入文件(配置.日志文件, "=" * 60)
                
                if cls._控制台启用:
                    print(f"[日志] 线程 '{窗口名称}' 日志文件: {日志路径}")
            except Exception as e:
                if cls._控制台启用:
                    print(f"[日志错误] 线程 '{窗口名称}' 初始化失败: {e}")
                配置.日志文件 = None
        elif cls._控制台启用:
            print(f"[日志] 线程 '{窗口名称}' 日志（仅控制台）")
    
    @classmethod
    def 关闭线程(cls):
        """关闭当前线程的日志（窗口线程停止时调用）"""
        if not cls._全局启用:
            return
        
        配置 = cls._获取线程配置()
        if 配置.日志文件:
            try:
                cls._写入文件(配置.日志文件, "=" * 60)
                cls._写入文件(配置.日志文件, f"线程停止: {配置.窗口名称}")
                cls._写入文件(配置.日志文件, f"停止时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                cls._写入文件(配置.日志文件, "=" * 60)
                配置.日志文件.close()
            except Exception:
                pass
            配置.日志文件 = None
            配置.当前日志日期 = None
    
    # ==================== 级别管理 ====================
    
    @classmethod
    def 获取当前全局级别(cls) -> DebugLevel:
        """获取当前线程的全局调试级别"""
        配置 = cls._获取线程配置()
        return 配置.全局级别
    
    @classmethod
    def 设置全局级别(cls, 级别: DebugLevel):
        """设置当前线程的全局调试级别"""
        if not cls._全局启用:
            return
        配置 = cls._获取线程配置()
        配置.全局级别 = 级别
    
    @classmethod
    def 设置分类级别(cls, 分类: str, 级别: DebugLevel):
        """设置当前线程的分类调试级别"""
        if not cls._全局启用:
            return
        配置 = cls._获取线程配置()
        配置.分类级别[分类] = 级别
    
    @classmethod
    def 获取有效级别(cls, 分类: str) -> DebugLevel:
        """获取分类的有效级别"""
        配置 = cls._获取线程配置()
        return 配置.分类级别.get(分类, 配置.全局级别)
    
    @classmethod
    def 设置显示时间戳(cls, 启用: bool):
        """设置是否显示时间戳"""
        配置 = cls._获取线程配置()
        配置.显示时间戳 = 启用
    
    # ==================== 日志输出 ====================
    
    @classmethod
    def _格式化消息(cls, 分类: str, 级别: DebugLevel, 消息: str) -> str:
        """格式化日志消息"""
        if not cls._全局启用:
            return ""
        
        配置 = cls._获取线程配置()
        前缀 = ""
        
        if 配置.显示时间戳:
            时间 = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            前缀 = f"[{时间}]"
        
        级别名 = 级别.name
        return f"{前缀}[{分类}][{级别名}] {消息}"
    
    @classmethod
    def _输出到控制台(cls, 消息: str):
        """输出到控制台"""
        if cls._控制台启用:
            try:
                print(消息)
            except UnicodeEncodeError:
                编码 = getattr(sys.stdout, "encoding", None) or "utf-8"
                安全消息 = 消息.encode(编码, errors="backslashreplace").decode(
                    编码
                )
                print(安全消息)
    
    @classmethod
    def _输出到文件(cls, 消息: str):
        """输出到文件（会自动确保文件可用）"""
        if not cls._文件启用:
            return
        
        cls._确保日志文件()
        配置 = cls._获取线程配置()
        if 配置.日志文件:
            cls._写入文件(配置.日志文件, 消息)
    
    @classmethod
    def 日志(cls, 分类: str, 级别: DebugLevel, 消息: str):
        """
        输出日志（根据开关决定输出位置）
        每次调用时会自动检查并切换日志文件
        """
        if not cls._全局启用:
            return
        
        有效级别 = cls.获取有效级别(分类)
        if 级别.value <= 有效级别.value:
            格式化消息 = cls._格式化消息(分类, 级别, 消息)
            if 格式化消息:
                # 控制台输出
                cls._输出到控制台(格式化消息)
                
                # 文件输出（会自动处理跨天切换）
                cls._输出到文件(格式化消息)
    
    # ==================== 便捷方法 ====================
    
    @classmethod
    def error(cls, 分类: str, 消息: str):
        """错误日志：导致功能中断"""
        cls.日志(分类, DebugLevel.ERROR, 消息)
    
    @classmethod
    def warning(cls, 分类: str, 消息: str):
        """警告日志：可恢复异常"""
        cls.日志(分类, DebugLevel.WARNING, 消息)
    
    @classmethod
    def info(cls, 分类: str, 消息: str):
        """信息日志：关键里程碑"""
        cls.日志(分类, DebugLevel.INFO, 消息)
    
    @classmethod
    def state(cls, 分类: str, 消息: str):
        """状态日志：状态变更"""
        cls.日志(分类, DebugLevel.STATE, 消息)
    
    @classmethod
    def debug(cls, 分类: str, 消息: str):
        """调试日志：流程追踪"""
        cls.日志(分类, DebugLevel.DEBUG, 消息)
    
    @classmethod
    def trace(cls, 分类: str, 消息: str):
        """追踪日志：数据细节"""
        cls.日志(分类, DebugLevel.TRACE, 消息)
    
    @classmethod
    def verbose(cls, 分类: str, 消息: str):
        """详细日志：高频循环"""
        cls.日志(分类, DebugLevel.VERBOSE, 消息)
    
    @classmethod
    def 设置日志目录(cls, 目录: str):
        """设置日志目录"""
        cls._日志目录 = 目录
        if cls._文件启用:
            cls._确保日志目录()


# 创建全局实例
调试器 = 线程日志管理器()


# ==================== 便捷函数 ====================

def 初始化线程日志(窗口名称: str):
    """初始化当前线程的日志（窗口线程启动时调用）"""
    调试器.初始化线程(窗口名称)


def 关闭线程日志():
    """关闭当前线程的日志（窗口线程停止时调用）"""
    调试器.关闭线程()


def 设置日志开关(启用: bool):
    """设置日志总开关"""
    调试器.设置启用(启用)


def 设置控制台输出(启用: bool):
    """设置控制台输出开关"""
    调试器.设置控制台输出(启用)


def 设置文件输出(启用: bool):
    """设置文件输出开关"""
    调试器.设置文件输出(启用)


def set_global_level(级别: int):
    """设置当前线程的全局调试级别"""
    级别映射 = {
        0: DebugLevel.NONE,
        1: DebugLevel.ERROR,
        2: DebugLevel.WARNING,
        3: DebugLevel.INFO,
        4: DebugLevel.STATE,
        5: DebugLevel.DEBUG,
        6: DebugLevel.TRACE,
        7: DebugLevel.VERBOSE,
    }
    调试器.设置全局级别(级别映射.get(级别, DebugLevel.STATE))


def set_category_level(分类: str, 级别: int):
    """设置当前线程的分类调试级别"""
    级别映射 = {
        0: DebugLevel.NONE,
        1: DebugLevel.ERROR,
        2: DebugLevel.WARNING,
        3: DebugLevel.INFO,
        4: DebugLevel.STATE,
        5: DebugLevel.DEBUG,
        6: DebugLevel.TRACE,
        7: DebugLevel.VERBOSE,
    }
    调试器.设置分类级别(分类, 级别映射.get(级别, DebugLevel.STATE))


def set_log_dir(目录: str):
    """设置日志目录"""
    调试器.设置日志目录(目录)


def get_debugger():
    """获取调试器实例"""
    return 调试器


def get_current_level() -> int:
    """获取当前线程的全局调试级别（返回整数值）"""
    return 调试器.获取当前全局级别().value


# ==================== 配置加载 ====================

def 加载配置(配置文件路径: str = "config/debug_config.json"):
    """从配置文件加载调试设置"""
    import json
    
    路径 = Path(配置文件路径)
    if not 路径.exists():
        调试器.warning("日志", f"配置文件不存在: {配置文件路径}，使用默认配置")
        return
    
    try:
        with open(路径, 'r', encoding='utf-8') as f:
            配置 = json.load(f)
        
        # 总开关
        设置日志开关(配置.get("全局开关", True))
        
        # 输出目标
        设置控制台输出(配置.get("控制台输出", True))
        设置文件输出(配置.get("文件输出", True))
        
        # 日志目录
        set_log_dir(配置.get("日志目录", "logs"))
        
        # 全局级别
        全局级别 = 配置.get("全局级别", 4)
        set_global_level(全局级别)
        
        # 分类级别
        for 分类, 级别 in 配置.get("分类级别", {}).items():
            set_category_level(分类, 级别)
        
        # 显示时间戳
        调试器.设置显示时间戳(配置.get("显示时间戳", True))
        
        调试器.info("日志", f"日志配置加载完成，全局级别: {DebugLevel(全局级别).name}")
        
    except Exception as e:
        调试器.error("日志", f"加载配置文件失败: {e}")
