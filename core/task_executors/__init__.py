# core/task_executors/__init__.py
"""
任务执行器模块

导出：
- 任务执行器注册表
- 任务执行器基类
- 通用战斗执行器
- 便捷函数
"""
from .registry import 任务执行器注册表, 创建执行器
from .base_executor import 任务执行器基类
from .battle_executor import 战斗任务执行器

__all__ = [
    '任务执行器注册表',
    '创建执行器',
    '任务执行器基类',
    '战斗任务执行器'
]