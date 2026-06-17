# tasks/base.py
"""
任务定义基类 - 简化任务创建
"""
from typing import Type, Dict, Any, Optional,List
from pydantic import BaseModel
from core.task_executors.registry import 任务执行器注册表, 任务注册信息
from models.task_config import 任务配置基类
from models.task_state import 任务状态基类
from core.path_manager import path_mgr
from core.debug import 调试器
import time

class 任务定义:
    """
    任务定义装饰器
    """
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    
    def __call__(self, cls):
        任务ID = self.kwargs.get("任务ID")
        if not 任务ID:
            raise ValueError("任务定义必须包含 任务ID")
        
        # 分离配置参数和状态参数
        配置参数 = {}
        状态参数 = {}
        
        for k, v in self.kwargs.items():
            if k.startswith("状态_"):
                新键 = k[3:]
                状态参数[新键] = v
            else:
                配置参数[k] = v
        
        # 动态创建配置类和状态类
        配置类 = self._创建配置类(任务ID, 配置参数)
        状态类 = self._创建状态类(任务ID, 状态参数)
        
        # 创建配置实例，获取完整配置（包含默认值）
        配置实例 = 配置类()
        完整配置参数 = {}
        for key, value in 配置实例.__dict__.items():
            if not key.startswith('_'):  # 排除私有属性
                # 用户显式声明的配置覆盖默认值
                if key in 配置参数 and 配置参数[key] is not None:
                    完整配置参数[key] = 配置参数[key]
                else:
                    完整配置参数[key] = value
        
        # 保存完整配置参数到注册表（作为默认配置）
        任务执行器注册表.设置默认配置参数(任务ID, 完整配置参数)

        # 注册到执行器注册表
        任务执行器注册表.注册(
            任务ID=任务ID,
            配置类=配置类,
            状态类=状态类,
            执行器类=cls
        )
        
        # 将配置类和状态类附加到执行器类上
        cls.配置类 = 配置类
        cls.状态类 = 状态类
        
        调试器.info("配置", f"注册任务: {任务ID} '{配置参数.get('任务名称', '')}' 优先级={配置参数.get('优先级', 5)} 每日{配置参数.get('每日次数', 1)}次")
        return cls
    
    @staticmethod
    def _创建配置类( 任务ID: str, 配置参数: dict) -> Type[任务配置基类]:
        """动态创建配置类"""
        class_dict = {
            "__annotations__": {}
        }
        
        # 设置基类属性值
        class_dict["任务ID"] = 配置参数.get("任务ID", "")
        class_dict["任务名称"] = 配置参数.get("任务名称", "")
        class_dict["任务类型"] = 配置参数.get("任务类型", "")
        class_dict["优先级"] = 配置参数.get("优先级", 5)
        class_dict["是否启用"] = 配置参数.get("是否启用", True)
        class_dict["工作时间开始"] = 配置参数.get("工作时间开始", 0)
        class_dict["工作时间结束"] = 配置参数.get("工作时间结束", 24)
        class_dict["地图关键字"] = 配置参数.get("地图关键字", "")
        class_dict["提前进场秒数"] = 配置参数.get("提前进场秒数", 0)  
        class_dict["避让模式使用全局设置"] = 配置参数.get("避让模式使用全局设置", False)
        class_dict["启用高战避让模式"] = 配置参数.get("启用高战避让模式", False)
        class_dict["避让杀手名单"] = 配置参数.get("避让杀手名单", "")
        class_dict["启用高频死亡避让模式"] = 配置参数.get("启用高频死亡避让模式", False)
        class_dict["高频死亡避让秒数"] = 配置参数.get("高频死亡避让秒数", 60)
        class_dict["高频死亡避让次数"] = 配置参数.get("高频死亡避让次数", 3)
        class_dict["避让冷却秒数"] = 配置参数.get("避让冷却秒数", 180)
        class_dict["回城回血使用全局设置"] = 配置参数.get("回城回血使用全局设置", False)
        class_dict["启用回城回血"] = 配置参数.get("启用回城回血", False)
        class_dict["回城血量阈值"] = 配置参数.get("回城血量阈值", 30)
        class_dict["启用抢怪模式"] = 配置参数.get("启用抢怪模式", False)
        class_dict["死亡前多少秒抢归属"] = 配置参数.get("死亡前多少秒抢归属",15)   
        class_dict["启用响应召唤"] = 配置参数.get("启用响应召唤", False)
        class_dict["召唤响应优先级模式"] = 配置参数.get("召唤响应优先级模式", "仅普通任务")
        class_dict["召唤启用任务完成状况动态管理"] = 配置参数.get("召唤启用任务完成状况动态管理", False)
        class_dict["召唤_任务完成后响应所有层级"] = 配置参数.get("召唤_任务完成后响应所有层级", False)
        class_dict["召唤_未完成任务响应当前层级"] = 配置参数.get("召唤_未完成任务响应当前层级", False)
        
        # 开发配置
        class_dict["当前任务可执行的最高层数"] = 配置参数.get("当前任务可执行的最高层数",0)
        class_dict["调试分类"] = 配置参数.get("调试分类", "")
        class_dict["调试模式"] = 配置参数.get("调试模式", False)
        class_dict["启用位置复查"] = 配置参数.get("启用位置复查", False)
        class_dict["怪物有无敌"] = 配置参数.get("怪物有无敌", False)
        class_dict["无敌触发血量阈值"] = 配置参数.get("无敌触发血量阈值", 20)
        class_dict["无敌持续时间"] = 配置参数.get("无敌持续时间", 20)
        class_dict["位置复查目标中心"] = 配置参数.get("位置复查目标中心", "")
        class_dict["位置复查目标半径"] = 配置参数.get("位置复查目标半径",10)
        class_dict["位置复查触发秒数"] = 配置参数.get("位置复查触发秒数", 5)
        class_dict["位置复查移动区域"] = 配置参数.get("位置复查移动区域", "")
        class_dict["工作时间段列表"]= 配置参数.get("工作时间段列表", "")
        class_dict["执行日期规则"]= 配置参数.get("执行日期规则", "")
        class_dict["次数刷新间隔小时"]= 配置参数.get("次数刷新间隔小时", 0)
        class_dict["次数刷新区间列表"]= 配置参数.get("次数刷新区间列表", "")
        class_dict["次数刷新区间条件"]= 配置参数.get("次数刷新区间条件", "")
        class_dict["默认攻击模式"]= 配置参数.get("默认攻击模式", "")
        class_dict["地图关键字组列表"] = []
        
        # 任务特有配置属性
        for k, v in 配置参数.items():
            if k not in ["任务ID", "任务名称", "任务类型", "优先级", "是否启用",
                        "工作时间开始", "工作时间结束", "地图关键字", 
                        "提前进场秒数","调试分类", "调试模式", "启用位置复查","位置复查目标半径",
                        "避让模式使用全局设置", "启用高战避让模式", "避让杀手名单",
                        "启用高频死亡避让模式", "高频死亡避让秒数", "高频死亡避让次数",
                        "避让冷却秒数", "回城回血使用全局设置", "启用回城回血",
                        "回城血量阈值", "启用抢怪模式", "死亡前多少秒抢归属",
                        "怪物有无敌", "无敌触发血量阈值", "无敌持续时间","默认攻击模式",
                        "启用响应召唤","召唤响应优先级模式","当前任务可执行的最高层数",
                        "召唤启用任务完成状况动态管理","召唤_任务完成后响应所有层级","召唤_未完成任务响应当前层级",
                        "工作时间段列表","执行日期规则","次数刷新间隔小时","次数刷新区间列表","次数刷新区间条件",
                        "位置复查目标中心","位置复查触发秒数","位置复查移动区域","地图关键字组列表"]:
                class_dict[k] = v
                class_dict["__annotations__"][k] = type(v)
        
        # 设置类型注解
        class_dict["__annotations__"].update({
            "任务ID": str,
            "任务名称": str,
            "任务类型": str,
            "优先级": int,
            "是否启用": bool,
            "工作时间开始": int,
            "工作时间结束": int,
            "地图关键字": str,            
            "提前进场秒数": int,
            "地图关键字组列表": list,
            "调试分类": str,
            "调试模式": bool,
            "启用位置复查": bool,
            "位置复查目标半径": int,
            "位置复查目标中心": str,
            "位置复查触发秒数": int,
            "位置复查移动区域": str,
            "避让模式使用全局设置": bool,
            "启用高战避让模式": bool,
            "避让杀手名单": str,
            "启用高频死亡避让模式": bool,
            "高频死亡避让秒数": int,
            "高频死亡避让次数": int,
            "避让冷却秒数": int,
            "回城回血使用全局设置": bool,
            "启用回城回血": bool,
            "回城血量阈值": int,
            "启用抢怪模式": bool,
            "死亡前多少秒抢归属": int,
            "怪物有无敌": bool,
            "无敌触发血量阈值": int,
            "无敌持续时间": int,
            "工作时间段列表": str,
            "执行日期规则": str,
            "次数刷新间隔小时": float,
            "次数刷新区间列表": str,
            "次数刷新区间条件": str,
            "启用响应召唤": bool,
            "召唤响应优先级模式": str,
            "召唤启用任务完成状况动态管理": bool,
            "召唤_任务完成后响应所有层级": bool,
            "召唤_未完成任务响应当前层级": bool,
            "默认攻击模式": str,
            "当前任务可执行的最高层数":int,
        })
        
        类名 = f"{任务ID}_配置"
        return type(类名, (任务配置基类,), class_dict)
    
    @staticmethod
    def _创建状态类(任务ID: str, 状态参数: dict) -> Type[任务状态基类]:
        """动态创建状态类"""
        class_dict = {
            "剩余次数": 20,
            "下次刷新时间": 0.0,
            "是否在副本中": False,
            "今日已完成次数": 0,
            "入口连续失败次数": 0,
            "入口冷却触发次数": 5,
            "入口冷却基础秒数": 180,
            "上次位置复查时间": 0.0,
            "上次次数刷新时间": time.time(),
            "位置复查次数": 0,            
            "__annotations__": {
                "剩余次数": int,
                "下次刷新时间": float,
                "是否在副本中": bool,
                "今日已完成次数": int,
                "入口连续失败次数": int,
                "入口冷却触发次数": int,
                "入口冷却基础秒数": int,    
                "上次位置复查时间": float,
                "上次次数刷新时间": float,
                "位置复查次数": int,
            }
        }
        
        for k, v in 状态参数.items():
            class_dict[k] = v
            class_dict["__annotations__"][k] = type(v)
        
        类名 = f"{任务ID}_状态"
        return type(类名, (任务状态基类,), class_dict)
    
    # ==================== 配置导入导出（支持多窗口） ====================
    
    @classmethod
    def 获取配置文件路径(cls, 窗口名称: str, 文件名: str = "tasks_config.json") -> str:
        """获取指定窗口的任务配置文件路径"""
        return path_mgr.get_config_path(f"{窗口名称}/{文件名}")
    
    @classmethod
    def 导入配置从JSON(cls, 窗口名称: str = None, 文件名: str = "tasks_config.json") -> bool:
        """
        从JSON文件导入配置并更新注册表
        
        参数:
            窗口名称: 窗口名称，None表示使用当前线程的窗口
            文件名: 配置文件名
        """
        import json
        from pathlib import Path
        
        if 窗口名称 is None:
            窗口名称 = 任务执行器注册表.获取当前窗口()
        
        文件路径 = cls.获取配置文件路径(窗口名称, 文件名)
        
        if not Path(文件路径).exists():
            调试器.warning("配置", f"配置文件不存在: {文件路径}，将使用默认配置")
            return False
        
        try:
            with open(文件路径, 'r', encoding='utf-8') as f:
                数据 = json.load(f)
        except Exception as e:
            调试器.error("配置", f"读取配置文件失败: {文件路径}, 错误: {e}")
            return False
        
        任务列表 = 数据.get("任务列表", [])
        if not 任务列表:
            调试器.warning("配置", f"配置文件 '{文件路径}' 中没有任务配置")
            return False
        
        更新计数 = 0
        for 任务配置 in 任务列表:
            任务ID = 任务配置.get("任务ID")
            if not 任务ID:
                continue
            
            # 获取当前配置（先取当前窗口的，再更新）
            当前配置 = 任务执行器注册表.获取配置参数(任务ID, 窗口名称)
            
            for key, value in 任务配置.items():
                if key != "任务ID":
                    当前配置[key] = value
            
            # 保存到注册表（按窗口隔离）
            任务执行器注册表.设置配置参数(任务ID, 当前配置, 窗口名称)
            调试器.trace("配置", f"更新 '{窗口名称}' 任务 '{任务ID}' 的配置项: {list(任务配置.keys())}")
            
            # 重新创建配置类并更新注册表
            cls._更新配置类(任务ID, 窗口名称)
            更新计数 += 1
        
        调试器.info("配置", f"窗口 '{窗口名称}' 从 '{文件路径}' 导入 {更新计数} 个任务配置")
        return True
    
    @classmethod
    def _更新配置类(cls, 任务ID: str, 窗口名称: str = None):
        """重新创建配置类并更新注册表"""
        # 获取指定窗口的配置参数
        配置参数 = 任务执行器注册表.获取配置参数(任务ID, 窗口名称)
        if not 配置参数:
            调试器.warning("配置", f"未找到任务 '{任务ID}' 的配置参数，无法更新配置类")
            return
        
        # 获取旧的注册信息
        旧注册信息 = 任务执行器注册表.获取注册信息(任务ID)
        if not 旧注册信息:
            调试器.warning("配置", f"未找到任务 '{任务ID}' 的注册信息，无法更新配置类")
            return
        
        # 创建新的配置类        
        新配置类 = cls._创建配置类(任务ID, 配置参数)
                
        # 更新注册表
        任务执行器注册表._注册表[任务ID] = 任务注册信息(
            配置类=新配置类,
            状态类=旧注册信息.状态类,
            执行器类=旧注册信息.执行器类
        )
        
        # 更新执行器类的配置类引用
        旧注册信息.执行器类.配置类 = 新配置类
        
        调试器.state("配置", f"任务 '{任务ID}' 配置类已更新 (窗口='{窗口名称}')")
    
    # @classmethod
    # def 导出配置到JSON(cls, 窗口名称: str = None, 文件名: str = "tasks_config.json") -> dict:
    #     """
    #     导出指定窗口的任务配置到JSON文件
        
    #     参数:
    #         窗口名称: 窗口名称，None表示使用当前线程的窗口
    #         文件名: 配置文件名
    #     """
    #     import json
    #     from pathlib import Path
        
    #     if 窗口名称 is None:
    #         窗口名称 = 任务执行器注册表.获取当前窗口()
        
    #     # 获取指定窗口的所有配置参数
    #     所有配置参数 = 任务执行器注册表.获取所有配置参数(窗口名称)
        
    #     所有配置 = []
    #     for 任务ID, 配置参数 in 所有配置参数.items():
    #         # 排除运行时属性
    #         导出配置 = {}
    #         for key, value in 配置参数.items():
    #             if key not in ["地图关键字组列表","调试模式","调试分类","启用位置复查","位置复查目标半径",
    #                     "怪物有无敌", "无敌触发血量阈值", "无敌持续时间","次数刷新时刻条件",
    #                     "工作时间段列表","执行日期规则","次数刷新间隔小时","次数刷新区间列表","次数刷新区间条件",
    #                     "位置复查目标中心","位置复查触发秒数","位置复查移动区域"]:
    #                 导出配置[key] = value
            
    #         if "任务ID" not in 导出配置:
    #             导出配置["任务ID"] = 任务ID
    #         所有配置.append(导出配置)
        
    #     数据 = {
    #         "版本": "1.0",
    #         "窗口名称": 窗口名称,
    #         "更新时间": cls._获取当前时间(),
    #         "任务数量": len(所有配置),
    #         "任务列表": 所有配置
    #     }
        
    #     文件路径 = cls.获取配置文件路径(窗口名称, 文件名)
    #     Path(文件路径).parent.mkdir(parents=True, exist_ok=True)
        
    #     try:
    #         with open(文件路径, 'w', encoding='utf-8') as f:
    #             json.dump(数据, f, ensure_ascii=False, indent=2)
    #         调试器.info("配置", f"窗口 '{窗口名称}' 导出 {len(所有配置)} 个任务配置到: {文件路径}")
    #     except Exception as e:
    #         调试器.error("配置", f"导出配置失败: {文件路径}, 错误: {e}")
    #         return {}
        
    #     return 数据
    @classmethod
    def 导出配置到JSON(cls, 窗口名称: str = None, 文件名: str = "tasks_config.json", 线程=None) -> dict:
        """
        导出指定窗口的任务配置到JSON文件
        
        参数:
            窗口名称: 窗口名称，None表示使用当前线程的窗口
            文件名: 配置文件名
            线程: 可选，传入线程对象则直接从任务实例读取最新值
        """
        import json
        from pathlib import Path
        
        if 窗口名称 is None:
            窗口名称 = 任务执行器注册表.获取当前窗口()
        
        if 线程:
            # 从线程任务实例直接读取最新值
            所有配置 = []
            for 任务 in 线程.任务排序列表:
                导出配置 = {}
                for key in dir(任务):
                    if key.startswith('_'):
                        continue
                    if key.startswith('model_'):
                        continue
                    value = getattr(任务, key)
                    if callable(value):
                        continue
                    if key in ["地图关键字组列表","调试模式","调试分类","启用位置复查","位置复查目标半径",
                            "怪物有无敌", "无敌触发血量阈值", "无敌持续时间","次数刷新时刻条件",
                            "工作时间段列表","执行日期规则","次数刷新间隔小时","次数刷新区间列表","次数刷新区间条件",
                            "位置复查目标中心","位置复查触发秒数","位置复查移动区域"]:
                        continue
                    导出配置[key] = value
                
                if "任务ID" not in 导出配置:
                    导出配置["任务ID"] = 任务.任务ID
                所有配置.append(导出配置)
        else:
            # 原方案：从缓存读取
            所有配置参数 = 任务执行器注册表.获取所有配置参数(窗口名称)
            
            所有配置 = []
            for 任务ID, 配置参数 in 所有配置参数.items():
                导出配置 = {}
                for key, value in 配置参数.items():
                    if key not in ["地图关键字组列表","调试模式","调试分类","启用位置复查","位置复查目标半径",
                            "怪物有无敌", "无敌触发血量阈值", "无敌持续时间","次数刷新时刻条件",
                            "工作时间段列表","执行日期规则","次数刷新间隔小时","次数刷新区间列表","次数刷新区间条件",
                            "位置复查目标中心","位置复查触发秒数","位置复查移动区域"]:
                        导出配置[key] = value
                
                if "任务ID" not in 导出配置:
                    导出配置["任务ID"] = 任务ID
                所有配置.append(导出配置)
        
        数据 = {
            "版本": "1.0",
            "窗口名称": 窗口名称,
            "更新时间": cls._获取当前时间(),
            "任务数量": len(所有配置),
            "任务列表": 所有配置
        }
        
        文件路径 = cls.获取配置文件路径(窗口名称, 文件名)
        Path(文件路径).parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(文件路径, 'w', encoding='utf-8') as f:
                json.dump(数据, f, ensure_ascii=False, indent=2)
            调试器.info("配置", f"窗口 '{窗口名称}' 导出 {len(所有配置)} 个任务配置到: {文件路径}")
        except Exception as e:
            调试器.error("配置", f"导出配置失败: {文件路径}, 错误: {e}")
            return {}
        
        return 数据
    
    @classmethod
    def 导出所有窗口配置(cls, 窗口名称列表: List[str] = None, 文件名: str = "tasks_config.json") -> dict:
        """导出所有窗口的任务配置"""
        if 窗口名称列表 is None:
            窗口名称列表 = 任务执行器注册表.获取所有窗口名称()
        
        结果 = {}
        for 窗口名称 in 窗口名称列表:
            结果[窗口名称] = cls.导出配置到JSON(窗口名称, 文件名)
        
        return 结果
    
    @classmethod
    def 获取当前窗口配置(cls) -> Dict[str, dict]:
        """获取当前窗口的所有任务配置"""
        窗口名称 = 任务执行器注册表.获取当前窗口()
        return 任务执行器注册表.获取所有配置参数(窗口名称)
    
    @classmethod
    def _获取当前时间(cls) -> str:
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    @classmethod
    def 获取配置参数(cls, 任务ID: str, 窗口名称: str = None) -> dict:
        """获取任务的配置参数"""
        return 任务执行器注册表.获取配置参数(任务ID, 窗口名称)


# 便捷别名
任务 = 任务定义