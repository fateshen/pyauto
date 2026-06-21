# core/reward_manager.py
"""
强化奖励管理器
"""
import time
import json
from pathlib import Path
from typing import List, Optional
from core.debug import 调试器

强化奖励配置版本 = "1.1"

class 强化奖励管理器:
    """强化奖励任务管理器"""
    
    def __init__(self, 窗口名称: str, 游戏配置=None, 动作执行器=None, 页面=None, 通用操作=None, 辅助识别器=None):
        self.窗口名称 = 窗口名称
        self.游戏配置 = 游戏配置
        self.动作执行器 = 动作执行器
        self.页面 = 页面
        self.通用操作 = 通用操作
        self.辅助识别器 = 辅助识别器
        
        self.任务实例列表 = []
        self.上次检查时间 = time.time()+180
        self.检查间隔 = 30
        
        self._加载任务实例()
        self._加载配置()
        self._初始化首次执行时间()

    def _初始化首次执行时间(self):
        import random
        for 实例 in self.任务实例列表:
            if 实例.下次执行时间 == 0:
                实例.下次执行时间 = time.time() + random.randint(180, 600)
    def _加载任务实例(self):
        from tasks.reward import 获取所有强化奖励任务类
        
        for 任务类 in 获取所有强化奖励任务类():
            # 创建一个简单的上下文对象传给任务实例
            实例 = 任务类(self)
            self.任务实例列表.append(实例)
    
    # def _加载配置(self):
    #     """从配置文件读取参数覆盖默认值"""
    #     配置路径 = Path("config") / self.窗口名称 / "reward_tasks_config.json"
    #     if not 配置路径.exists():
    #         self.保存配置()
    #         return
        
    #     try:
    #         with open(配置路径, 'r', encoding='utf-8') as f:
    #             数据 = json.load(f)
            
    #         配置映射 = {t["任务ID"]: t for t in 数据.get("任务列表", [])}
            
    #         for 实例 in self.任务实例列表:
    #             if 实例.任务ID in 配置映射:
    #                 配置 = 配置映射[实例.任务ID]
    #                 for 字段名, 值 in 配置.items():
    #                     if hasattr(实例, 字段名) and 字段名 != "任务ID":
    #                         # 类型转换
    #                         当前值 = getattr(实例, 字段名)
    #                         if isinstance(当前值, bool):
    #                             setattr(实例, 字段名, bool(值))
    #                         elif isinstance(当前值, int):
    #                             setattr(实例, 字段名, int(值))
    #                         elif isinstance(当前值, float):
    #                             setattr(实例, 字段名, float(值))
    #                         else:
    #                             setattr(实例, 字段名, 值)
    #     except Exception as e:
    #         调试器.warning("强化奖励", f"加载配置失败: {e}")

    def _加载配置(self):
        配置路径 = Path("config") / self.窗口名称 / "reward_tasks_config.json"
        if not 配置路径.exists():
            self.保存配置(版本=强化奖励配置版本)
            return
        
        try:
            with open(配置路径, 'r', encoding='utf-8') as f:
                数据 = json.load(f)
            
            文件版本 = 数据.get("版本", "0")
            配置映射 = {t["任务ID"]: t for t in 数据.get("任务列表", [])}
            
            if 文件版本 != 强化奖励配置版本:
                # 版本更新：只保留 UI 字段
                from ui.reward_task_defs import 强化奖励任务定义
                for 实例 in self.任务实例列表:
                    if 实例.任务ID in 配置映射:
                        旧数据 = 配置映射[实例.任务ID]
                        ui字段 = set(强化奖励任务定义.get(实例.任务名称, {}).keys())
                        需要保留的字段 = ui字段 | {"上次确定任务结束时间", "下次执行时间", "在线奖励完成时间",
                                          "本周已充值天数"}
                        for 字段名 in 需要保留的字段:
                            if 字段名 in 旧数据:
                                self._设置属性(实例, 字段名, 旧数据[字段名])
                
                调试器.info("强化奖励", f"窗口 '{self.窗口名称}' 配置版本更新: v{文件版本} → v{强化奖励配置版本}")
                self.保存配置(版本=强化奖励配置版本)
            else:
                for 实例 in self.任务实例列表:
                    if 实例.任务ID in 配置映射:
                        配置 = 配置映射[实例.任务ID]
                        for 字段名, 值 in 配置.items():
                            if hasattr(实例, 字段名) and 字段名 != "任务ID":
                                self._设置属性(实例, 字段名, 值)
        except Exception as e:
            调试器.warning("强化奖励", f"加载配置失败: {e}")
    def _设置属性(self, 实例, 字段名, 值):
        """类型转换后设置属性"""
        当前值 = getattr(实例, 字段名)
        if isinstance(当前值, bool):
            setattr(实例, 字段名, bool(值))
        elif isinstance(当前值, int):
            setattr(实例, 字段名, int(值))
        elif isinstance(当前值, float):
            setattr(实例, 字段名, float(值))
        else:
            setattr(实例, 字段名, 值)
    def 保存配置(self,版本:Optional[str] = None):
        """保存配置到文件"""
        配置路径 = Path("config") / self.窗口名称 / "reward_tasks_config.json"
        配置路径.parent.mkdir(parents=True, exist_ok=True)
        
        if 版本 is None: 
            版本 = 强化奖励配置版本
        数据 = {
            "版本": 版本,
            "任务列表": []
        }
        # 不需要保存的开发属性
        排除字段 = {"管理器", "动作", "配置", "页面", "通用操作", "辅助识别器", "线程"}
        for 实例 in self.任务实例列表:
            任务配置 = {}
            # 遍历所有公开属性
            for 属性名 in dir(实例):
                if 属性名.startswith('_') :
                    continue
                if 属性名 in 排除字段:
                    continue
                值 = getattr(实例, 属性名, None)
                if 值 is not None and not callable(值):
                    任务配置[属性名] = 值
            
            数据["任务列表"].append(任务配置)
        
        try:
            with open(配置路径, 'w', encoding='utf-8') as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
            调试器.debug("强化奖励", "配置已保存")
        except Exception as e:
            调试器.error("强化奖励", f"保存配置失败: {e}")
    
    def 检查并执行(self,在盟重省: bool = False):
        """检查并执行所有可执行的任务"""
        
        当前时间 = time.time()
        if 当前时间 - self.上次检查时间 < self.检查间隔:
            return
        self.上次检查时间 = 当前时间
        
        可执行 = [t for t in self.任务实例列表 if t.是否可以执行()]
        # 可执行.sort(key=lambda t: t.优先级, reverse=True)
        
        if not 可执行:
            return
        
        调试器.trace("强化奖励", f"可执行任务: {[t.任务名称 for t in 可执行]}")
        
        for 任务 in 可执行:            
            try:
                if  任务.在盟重省执行 and not 在盟重省: 
                    continue
                if not 任务.在盟重省执行 and  在盟重省: 
                    continue
                if 任务.执行():
                    任务.标记已执行()
                    self.通用操作.清理页面状态() 
                    调试器.debug("强化奖励", f"{任务.任务名称} 执行成功")
            except Exception as e:
                调试器.warning("强化奖励", f"{任务.任务名称} 执行异常: {e}")