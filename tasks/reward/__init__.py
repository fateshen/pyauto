
# tasks/reward/__init__.py
"""
强化奖励任务模块 - 自动发现
"""
import importlib
from pathlib import Path
from typing import List, Type
from core.debug import 调试器
from core.path_manager import path_mgr

# def 获取所有强化奖励任务类() -> List[Type]:
#     """自动发现并返回所有强化奖励任务类"""
#     任务类列表 = []
#     当前目录 = Path(__file__).parent
    
#     for 文件 in 当前目录.glob("*.py"):
#         if 文件.name in ["__init__.py", "base.py"]:
#             continue
        
#         模块名 = f"tasks.reward.{文件.stem}"
#         try:
#             模块 = importlib.import_module(模块名)
#             for attr_name in dir(模块):
#                 attr = getattr(模块, attr_name)
#                 if (isinstance(attr, type) and 
#                     attr.__module__ == 模块名 and
#                     hasattr(attr, '任务ID') and 
#                     attr.任务ID):
#                     任务类列表.append(attr)
#                     调试器.info("强化奖励", f"发现任务: {attr.任务ID}")
#         except Exception as e:
#             调试器.warning("强化奖励", f"加载失败: {文件.stem} - {e}")
    
#     return 任务类列表

def 获取所有强化奖励任务类() -> List[Type]:
    调试器.info("强化奖励", "开始加载奖励任务模块...")
    
    任务类列表 = []
    已加载模块 = set()
    
    # 1. 优先加载外部 reward 目录
    外部目录 = path_mgr.run_dir / "tasks" / "reward"
    if 外部目录.exists():
        _扫描奖励模块(外部目录, "tasks.reward", 任务类列表, 已加载模块)
    
    # 2. 再加载内置 reward
    内置目录 = Path(__file__).parent
    _扫描奖励模块(内置目录, "tasks.reward", 任务类列表, 已加载模块)
    
    return 任务类列表
def _扫描奖励模块(目录, 模块前缀, 任务类列表, 已加载模块):
    import sys
    import types
    
    # 确保父包存在（构造 tasks 和 tasks.reward 命名空间）
    if 'tasks' not in sys.modules:
        sys.modules['tasks'] = types.ModuleType('tasks')
    if 'tasks.reward' not in sys.modules:
        sys.modules['tasks.reward'] = types.ModuleType('tasks.reward')
    
    for 文件 in 目录.glob("*.py"):
        if 文件.name in ["__init__.py", "base.py"]:
            continue
        if 文件.stem in 已加载模块:
            continue
        
        模块名 = f"{模块前缀}.{文件.stem}"
        try:
            父目录 = str(文件.parent)
            if 父目录 not in sys.path:
                sys.path.insert(0, 父目录)
            
            模块 = importlib.import_module(文件.stem)
            # 修正模块的 __name__ 和 __package__
            模块.__name__ = 模块名
            模块.__package__ = 模块前缀
            sys.modules[模块名] = 模块
            
            已加载模块.add(文件.stem)
            
            for attr_name in dir(模块):
                attr = getattr(模块, attr_name)
                if (isinstance(attr, type) and
                    hasattr(attr, '任务ID') and
                    attr.任务ID):
                    任务类列表.append(attr)
                    调试器.info("强化奖励", f"发现任务: {attr.任务ID}")
        except Exception as e:
            调试器.warning("强化奖励", f"加载失败: {文件.stem} - {e}")