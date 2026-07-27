# tasks/__init__.py
"""
任务模块 - 自动发现并注册所有任务
"""
import os
import importlib
from pathlib import Path
from typing import List, Dict, Any
from core.debug import 调试器

程序任务配置版本 = "1.03"
def 初始化任务系统():
    """手动初始化任务系统（需要在 main.py 中调用）"""
    return 自动发现并注册任务()
# def 自动发现并注册任务():
#     """自动发现并注册所有任务"""
#     调试器.info("任务系统", "开始自动发现任务模块...")
    
#     当前目录 = Path(__file__).parent
#     已注册 = []
#     加载失败列表 = []
    
#     for 文件 in 当前目录.glob("*.py"):
#         if 文件.name in ["__init__.py", "base.py"]:
#             continue
        
#         模块名 = f"tasks.{文件.stem}"
#         try:
#             importlib.import_module(模块名)
#             已注册.append(文件.stem)
#             调试器.info("任务系统", f"✅ 已加载: {文件.stem}")
#         except Exception as e:
#             加载失败列表.append(文件.stem)
#             调试器.error("任务系统", f"❌ 加载失败: {文件.stem} - {e}")
    
#     if 加载失败列表:
#         调试器.warning("任务系统", f"共 {len(加载失败列表)} 个任务加载失败: {加载失败列表}")
    
#     调试器.info("任务系统", f"任务发现完成，成功加载 {len(已注册)} 个任务")
#     return 已注册


def 获取所有任务配置() -> List:
    """获取所有已注册任务的配置实例"""
    from core.task_executors.registry import 任务执行器注册表
    
    配置列表 = []
    for 任务ID in 任务执行器注册表.获取所有已注册任务():
        注册信息 = 任务执行器注册表.获取注册信息(任务ID)
        if 注册信息 and 注册信息.配置类:
            配置列表.append(注册信息.配置类())
    return 配置列表


def 导出任务配置(文件路径: str = "tasks_config.json"):
    """导出所有任务配置到JSON（只导出配置）"""
    from .base import 任务定义
    return 任务定义.导出配置到JSON(文件路径)


def 导入任务配置(文件路径: str = "tasks_config.json") -> bool:
    """从JSON导入任务配置（只导入配置）"""
    from .base import 任务定义
    return 任务定义.导入配置从JSON(文件路径)


def 自动发现并注册任务() -> List[str]:
    from core.path_manager import path_mgr
    
    已注册 = []
    
    # 1. 优先加载外部 tasks 目录（exe 旁边的 tasks/ 文件夹）
    外部目录 = path_mgr.run_dir / "tasks"
    if 外部目录.exists():
        _扫描并加载(外部目录, "tasks", 已注册)
    
    # 2. 再加载内置 tasks（exe 内部的模块）
    内置目录 = Path(__file__).parent
    _扫描并加载(内置目录, "tasks", 已注册)
    
    return 已注册


# import importlib
import sys
# from pathlib import Path


def _扫描并加载(目录, 模块前缀, 已注册列表):
    for 文件 in 目录.glob("*.py"):
        if 文件.name in ["__init__.py", "base.py"]:
            continue
        if 文件.stem in 已注册列表:
            continue
        
        模块名 = f"{模块前缀}.{文件.stem}"
        try:
            # 把文件所在目录加入 sys.path，然后用 importlib 导入
            父目录 = str(文件.parent)
            if 父目录 not in sys.path:
                sys.path.insert(0, 父目录)
            
            importlib.import_module(文件.stem)
            已注册列表.append(文件.stem)
            调试器.info("任务系统", f"✅ 已加载: {文件.stem}")
        except Exception as e:
            调试器.error("任务系统", f"❌ 加载失败: {文件.stem} - {e}")