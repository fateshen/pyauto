"""
任务配置标签页 — 基于 task_config_defs.py 动态生成控件
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QScrollArea, QGroupBox, QSpinBox, QCheckBox, QComboBox,
    QLabel, QMessageBox
)
from PySide6.QtCore import Qt

# from ui.task_config_defs import 任务配置定义
from ui.widgets import 多选子任务控件, 击杀顺序控件, 子任务双选控件

import sys
from pathlib import Path
from core.path_manager import path_mgr

def _加载任务配置定义():
    """优先加载外部 task_config_defs.py，否则用内置"""
    # 1. 尝试外部
    外部文件 = path_mgr.run_dir / "ui" / "task_config_defs.py"
    if 外部文件.exists():
        import importlib
        父目录 = str(外部文件.parent)
        if 父目录 not in sys.path:
            sys.path.insert(0, 父目录)
        模块 = importlib.import_module("task_config_defs")
        return getattr(模块, "任务配置定义", {})
    
    # 2. 回退到内置
    from ui.task_config_defs import 任务配置定义
    return 任务配置定义

任务配置定义 = _加载任务配置定义()


class 任务配置标签页(QWidget):
    """任务配置标签页：左侧任务列表 + 右侧动态配置"""
    
    def __init__(self):
        super().__init__()
        self.当前任务配置列表 = []
        self.当前任务状态映射 = {}
        self.编辑副本 = {}
        self.当前编辑任务ID = None
        self.控件映射 = {}
        self._待恢复选中ID = None
        self._初始化界面()
    
    def _初始化界面(self):
        布局 = QHBoxLayout(self)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(6)
        
        # 左侧：任务列表
        左侧 = QWidget()
        左侧.setFixedWidth(180)
        左侧布局 = QVBoxLayout(左侧)
        左侧布局.setContentsMargins(0, 0, 0, 0)
        左侧布局.setSpacing(4)
        
        self.任务搜索框 = QLineEdit()
        self.任务搜索框.setPlaceholderText("搜索任务...")
        self.任务搜索框.textChanged.connect(self._搜索过滤)
        左侧布局.addWidget(self.任务搜索框)
        
        self.任务配置列表 = QListWidget()
        self.任务配置列表.setStyleSheet("""
            QListWidget::item {
                padding: 3px 4px;
                min-height: 22px;
            }
            QListWidget::item:selected {
                background-color: #1a73e8;
                color: white;
            }
            QListWidget::item:selected:!focus {
                background-color: #a8c8f0;
                color: #1a73e8;
            }
            QListWidget::item:hover:!selected {
                background-color: #e8f0fe;
            }
            QListWidget:focus {
                outline: none;
            }
        """)
        self.任务配置列表.currentItemChanged.connect(self._任务选中)
        左侧布局.addWidget(self.任务配置列表)
        
        按钮行 = QHBoxLayout()
        self.全启用按钮 = QPushButton("全启用")
        self.全禁用按钮 = QPushButton("全禁用")
        self.全启用按钮.clicked.connect(lambda: self._批量启用(True))
        self.全禁用按钮.clicked.connect(lambda: self._批量启用(False))
        按钮行.addWidget(self.全启用按钮)
        按钮行.addWidget(self.全禁用按钮)
        左侧布局.addLayout(按钮行)
        
        self.恢复默认按钮 = QPushButton("恢复默认")
        self.恢复默认按钮.clicked.connect(self._恢复默认配置)
        左侧布局.addWidget(self.恢复默认按钮)
        
        布局.addWidget(左侧)
        
        # 右侧：配置区域
        右侧 = QScrollArea()
        右侧.setWidgetResizable(True)
        
        self.配置内容 = QWidget()
        self.配置布局 = QVBoxLayout(self.配置内容)
        self.配置布局.setSpacing(8)
        self.配置布局.addStretch()
        右侧.setWidget(self.配置内容)
        
        布局.addWidget(右侧, stretch=2)
    
    # ==================== 窗口切换接口 ====================
    
    def 切换到任务列表(self, 任务配置列表):
        """切换窗口时，替换当前任务列表并刷新左侧列表显示（不触发编辑）"""
        之前选中ID = self.当前编辑任务ID
        self.当前任务配置列表 = 任务配置列表 or []
        self.当前编辑任务ID = None  # 先清空，避免 _任务选中 触发
        
        # 重建列表（阻断信号避免触发 _任务选中）
        self.任务配置列表.blockSignals(True)
        self.任务配置列表.clear()
        排序后列表 = sorted(self.当前任务配置列表, key=lambda t: getattr(t, '任务名称', ''))
        for 任务 in 排序后列表:
            启用标记 = "☑" if getattr(任务, '是否启用', True) else "☐"
            项 = QListWidgetItem(f"{启用标记} {任务.任务名称}")
            项.setData(Qt.UserRole, 任务.任务ID)
            self.任务配置列表.addItem(项)
        self.任务配置列表.blockSignals(False)
        
        # 记住之前选中的任务ID，供 _恢复上次选中任务 使用
        self._待恢复选中ID = 之前选中ID
    
    def _恢复上次选中任务(self):
        """切换窗口后，恢复上次选中的任务"""
        目标任务ID = self._待恢复选中ID
        if 目标任务ID:
            for i in range(self.任务配置列表.count()):
                项 = self.任务配置列表.item(i)
                if 项.data(Qt.UserRole) == 目标任务ID:
                    self.任务配置列表.setCurrentItem(项)
                    return
        if self.任务配置列表.count() > 0:
            self.任务配置列表.setCurrentItem(self.任务配置列表.item(0))
        self._待恢复选中ID = None
    
    # ==================== 编辑副本接口 ====================
    
    def 应用编辑副本(self, 副本: dict):
        """应用编辑副本（由主窗口调用）"""
        self.编辑副本 = 副本
    
    def 获取所有编辑结果(self) -> dict:
        if self.当前编辑任务ID:
            self._保存UI到副本()
        return self.编辑副本
    
    def 清除编辑副本(self):
        self.编辑副本 = {}
    
    # ==================== 数据加载 ====================
    
    def 加载任务列表(self, 任务配置列表, 任务状态映射=None, 保留编辑副本=False):
        self.当前任务配置列表 = 任务配置列表 or []
        self.当前任务状态映射 = 任务状态映射 or {}
        if not 保留编辑副本:
            self.编辑副本 = {}
        self.任务配置列表.clear()
        
        排序后列表 = sorted(self.当前任务配置列表, key=lambda t: getattr(t, '任务名称', ''))
        
        for 任务 in 排序后列表:
            启用标记 = "☑" if getattr(任务, '是否启用', True) else "☐"
            项 = QListWidgetItem(f"{启用标记} {任务.任务名称}")
            项.setData(Qt.UserRole, 任务.任务ID)
            self.任务配置列表.addItem(项)
    
    def _查找任务(self, 任务ID):
        for t in self.当前任务配置列表:
            if t.任务ID == 任务ID:
                return t
        return None
    
    # ==================== 动态生成控件 ====================
    
    def _任务选中(self, 当前, 上一个):
        if self.当前编辑任务ID:
            self._保存UI到副本()
        
        if 当前:
            self.当前编辑任务ID = 当前.data(Qt.UserRole)
            self._动态生成配置UI()
            self._从副本加载到UI()
    
    def _动态生成配置UI(self):
        任务 = self._查找任务(self.当前编辑任务ID)
        if not 任务:
            return
        
        配置定义 = 任务配置定义.get(任务.任务名称, {})
        if not 配置定义:
            return
        
        while self.配置布局.count() > 1:
            item = self.配置布局.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.控件映射 = {}
        
        通用字段 = ["优先级", "是否启用", "工作时间开始", "工作时间结束", "提前进场秒数"]
        冷却字段 = ["入口冷却触发次数", "入口冷却基础秒数"]
        战斗字段 = ["启用自动战斗", "启用自动走位"]
        抢怪字段 = ["启用抢怪模式", "低于此血量抢怪", "死亡前多少秒抢归属"]
        避让字段 = ["避让模式使用全局设置", "启用高战避让模式", "启用高频死亡避让模式", "避让杀手名单",
                    "高频死亡避让秒数", "高频死亡避让次数", "避让冷却秒数", "开战后归属是队友且无敌人避让"]
        回城字段 = ["回城回血使用全局设置", "启用回城回血", "回城血量阈值"]
        召唤字段 = ["启用摇人按钮","启用响应召唤", "召唤响应优先级模式", "召唤启用任务完成状况动态管理",
                    "召唤_任务完成后响应所有层级", "召唤_未完成任务响应当前层级"]
        专属字段 = ["普通任务模式", "异界作为队长", "异界队友名单", "异界等级范围","启用购买次数",
                    "开始几分钟以后未排队使用强制匹配", "开始几分钟以后队长使用匹配",
                    "击杀顺序", "接取高级镖车", "跨服入侵默认BOSS", "不使用多倍奖励", "默认攻击模式"]
        
        通用组 = self._创建配置组("通用配置", 通用字段, 配置定义)
        if 通用组:
            self.配置布局.insertWidget(self.配置布局.count() - 1, 通用组)
        
        子任务组 = self._创建子任务双选组(配置定义)
        if 子任务组:
            self.配置布局.insertWidget(self.配置布局.count() - 1, 子任务组)
        
        冷却组 = self._创建配置组("入口冷却", 冷却字段, 配置定义, 默认值映射={"入口冷却触发次数": 5, "入口冷却基础秒数": 60})
        if 冷却组:
            self.配置布局.insertWidget(self.配置布局.count() - 1, 冷却组)
        
        策略组 = QGroupBox("策略配置")
        策略布局 = QFormLayout(策略组)
        if self._添加字段到布局(策略布局, 战斗字段, 配置定义):
            self._添加分隔线到布局(策略布局)
        if self._添加字段到布局(策略布局, 抢怪字段, 配置定义):
            self._添加分隔线到布局(策略布局)
        if self._添加字段到布局(策略布局, 避让字段, 配置定义):
            self._添加分隔线到布局(策略布局)
        if self._添加字段到布局(策略布局, 回城字段, 配置定义):
            self._添加分隔线到布局(策略布局)
        if self._添加字段到布局(策略布局, 召唤字段, 配置定义):
            self._添加分隔线到布局(策略布局)
        self._添加字段到布局(策略布局, 专属字段, 配置定义)
        self.配置布局.insertWidget(self.配置布局.count() - 1, 策略组)
    
        # ========== 收集所有已被分组的字段 ==========
        已分组字段 = set()
        已分组字段.update(通用字段)
        已分组字段.update(冷却字段)
        已分组字段.update(战斗字段)
        已分组字段.update(抢怪字段)
        已分组字段.update(避让字段)
        已分组字段.update(回城字段)
        已分组字段.update(召唤字段)
        已分组字段.update(专属字段)
        # 子任务双选相关字段
        if "子任务队列" in 配置定义:
            已分组字段.add("子任务队列")
        if "次优先级任务队列" in 配置定义:
            已分组字段.add("次优先级任务队列")
        if "每日更新任务数量" in 配置定义:
            已分组字段.add("每日更新任务数量")
        if "次优先级任务开始时间" in 配置定义:
            已分组字段.add("次优先级任务开始时间")
        
        # ========== 找出未分组的字段 ==========
        未分组字段 = [f for f in 配置定义 if f not in 已分组字段]
        
        # ========== 渲染未分组字段 ==========
        if 未分组字段:
            其他组 = self._创建配置组("其他配置", 未分组字段, 配置定义)
            if 其他组:
                self.配置布局.insertWidget(self.配置布局.count() - 1, 其他组)

    def _添加分隔线到布局(self, 布局):
        from PySide6.QtWidgets import QFrame
        线 = QFrame()
        线.setFrameShape(QFrame.HLine)
        线.setFrameShadow(QFrame.Sunken)
        线.setStyleSheet("color: #c0c0c0;")
        布局.addRow(线)   
    def _创建子任务双选组(self, 配置定义):
        if "子任务队列" not in 配置定义 and "次优先级任务队列" not in 配置定义:
            return None
        
        主定义 = 配置定义.get("子任务队列")
        次定义 = 配置定义.get("次优先级任务队列")
        
        if 主定义 and len(主定义) > 2:
            映射 = 主定义[2]
        elif 次定义 and len(次定义) > 2:
            映射 = 次定义[2]
        else:
            映射 = {}
        
        主默认 = 主定义[1] if 主定义 else ""
        次默认 = 次定义[1] if 次定义 else ""
        
        主tip = 主定义[3] if 主定义 and len(主定义) > 3 else ""
        次tip = 次定义[3] if 次定义 and len(次定义) > 3 else ""

        控件 = 子任务双选控件(映射, str(主默认), str(次默认), 主tip, 次tip)
        
        组 = QGroupBox("子任务配置")
        布局 = QVBoxLayout(组)
        布局.addWidget(控件)
        
        额外布局 = QFormLayout()
        if "每日更新任务数量" in 配置定义:
            spin = QSpinBox()
            spin.setRange(0, 20)
            spin.setValue(配置定义["每日更新任务数量"][1])
            额外布局.addRow("每日更新任务数量:", spin)
            self.控件映射["每日更新任务数量"] = ("spin", spin)
            数量tip = 配置定义["每日更新任务数量"][3] if len(配置定义["每日更新任务数量"]) > 3 else None
            if 数量tip:
                spin.setToolTip(数量tip)

        if "次优先级任务开始时间" in 配置定义:
            spin = QSpinBox()
            spin.setRange(0, 24)
            spin.setValue(配置定义["次优先级任务开始时间"][1])
            额外布局.addRow("次优先级任务开始时间:", spin)
            self.控件映射["次优先级任务开始时间"] = ("spin", spin)
            时间tip = 配置定义["次优先级任务开始时间"][3] if len(配置定义["次优先级任务开始时间"]) > 3 else None
            if 时间tip:
                spin.setToolTip(时间tip)

        布局.addLayout(额外布局)
        
        self.控件映射["_子任务双选"] = ("dual_select", 控件)
       
        return 组
    
    def _创建配置组(self, 标题, 字段列表, 配置定义, 默认值映射=None):
        布局 = QFormLayout()
        有字段 = self._添加字段到布局(布局, 字段列表, 配置定义, 默认值映射)
        
        if not 有字段:
            return None
        
        组 = QGroupBox(标题)
        组.setLayout(布局)
        return 组
    
    def _添加字段到布局(self, 布局, 字段列表, 配置定义, 默认值映射=None):
        有字段 = False
        for 字段名 in 字段列表:
            if 字段名 not in 配置定义:
                continue
            有字段 = True
            
            定义 = 配置定义[字段名]
            控件类型 = 定义[0]
            默认值 = 定义[1]
            额外参数 = 定义[2] if len(定义) > 2 else None
            tip = 定义[3] if len(定义) > 3 else None
            
            if 默认值映射 and 字段名 in 默认值映射:
                默认值 = 默认值映射[字段名]
            
            if 控件类型 == "check":
                控件 = QCheckBox()
                布局.addRow(字段名 + ":", 控件)
                if 字段名 == "是否启用":
                    控件.toggled.connect(lambda checked: self._刷新列表启用状态(checked))
            elif 控件类型 == "spin":
                控件 = QSpinBox()
                控件.setRange(0, 9999)
                布局.addRow(字段名 + ":", 控件)
            elif 控件类型 == "text":
                控件 = QLineEdit()
                布局.addRow(字段名 + ":", 控件)
            elif 控件类型 == "combo":
                控件 = QComboBox()
                if 额外参数:
                    控件.addItems(额外参数)
                布局.addRow(字段名 + ":", 控件)
            elif 控件类型 == "multiselect":
                控件 = 多选子任务控件(额外参数 or {}, str(默认值))
                布局.addRow(字段名 + ":", 控件)
            elif 控件类型 == "kill_order":
                控件 = 击杀顺序控件(额外参数 or {}, str(默认值))
                布局.addRow(字段名 + ":", 控件)
            else:
                continue
            
            if tip:
                控件.setToolTip(tip)
            
            self.控件映射[字段名] = (控件类型, 控件)
        
        return 有字段
    
    # ==================== 副本读写 ====================
    
    def _保存UI到副本(self):
        if not self.控件映射:
            return
        
        副本 = {}
        for 字段名, (控件类型, 控件) in self.控件映射.items():
            if 控件类型 == "check":
                副本[字段名] = 控件.isChecked()
            elif 控件类型 == "spin":
                副本[字段名] = 控件.value()
            elif 控件类型 == "text":
                副本[字段名] = 控件.text()
            elif 控件类型 == "combo":
                当前文本 = 控件.currentText()                
                if 当前文本 == "默认":
                    副本[字段名] = None
                elif 当前文本 == "是":
                    副本[字段名] = True
                elif 当前文本 == "否":
                    副本[字段名] = False
                else:
                    副本[字段名] = 当前文本
            elif 控件类型 == "multiselect":
                副本[字段名] = 控件.获取选中值()
            elif 控件类型 == "kill_order":
                副本[字段名] = 控件.获取顺序值()
            elif 控件类型 == "dual_select":
                副本["子任务队列"] = 控件.获取主选中()
                副本["次优先级任务队列"] = 控件.获取次选中()
        
        self.编辑副本[self.当前编辑任务ID] = 副本
    
    def _从副本加载到UI(self):
        if not self.当前编辑任务ID or not self.控件映射:
            return

        任务 = self._查找任务(self.当前编辑任务ID)
        if not 任务:
            return
        副本 = self.编辑副本.get(self.当前编辑任务ID, {})
        
        for 字段名, (控件类型, 控件) in self.控件映射.items():
            if 字段名 in 副本:
                值 = 副本[字段名]
            else:
                值 = getattr(任务, 字段名, None)
                if 值 is None and 字段名 in 任务配置定义.get(任务.任务名称, {}):
                    值 = 任务配置定义[任务.任务名称][字段名][1]
            
            if 控件类型 == "check":
                控件.setChecked(bool(值))
            elif 控件类型 == "spin":
                try:
                    控件.setValue(int(值) if 值 is not None else 0)
                except (ValueError, TypeError):
                    控件.setValue(0)
            elif 控件类型 == "text":
                控件.setText(str(值) if 值 is not None else "")
            elif 控件类型 == "combo":
                if 值 is None:
                    控件.setCurrentIndex(0)
                elif isinstance(值, bool):
                    控件.setCurrentIndex(1 if 值 else 2)
                else:
                    控件.setCurrentText(str(值))
            elif 控件类型 == "multiselect":
                控件.设置选中值(str(值) if 值 else "")
            elif 控件类型 == "kill_order":
                控件.设置顺序值(str(值) if 值 else "")
            elif 控件类型 == "dual_select":
                if "子任务队列" in 副本:
                    控件.设置主选中(str(副本["子任务队列"]))
                else:
                    控件.设置主选中(str(getattr(任务, "子任务队列", "")))
                if "次优先级任务队列" in 副本:
                    控件.设置次选中(str(副本["次优先级任务队列"]))
                else:
                    控件.设置次选中(str(getattr(任务, "次优先级任务队列", "")))
    
    # ==================== 列表同步 ====================
    
    def _刷新列表启用状态(self, 启用: bool):
        if not self.当前编辑任务ID:
            return
        for i in range(self.任务配置列表.count()):
            项 = self.任务配置列表.item(i)
            if 项.data(Qt.UserRole) == self.当前编辑任务ID:
                任务 = self._查找任务(self.当前编辑任务ID)
                if 任务:
                    项.setText(f"{'☑' if 启用 else '☐'} {任务.任务名称}")
                break
    
    def _刷新列表启用状态_全部(self):
        """根据编辑副本和任务配置，刷新所有列表项的启用标记"""
        for i in range(self.任务配置列表.count()):
            项 = self.任务配置列表.item(i)
            任务ID = 项.data(Qt.UserRole)
            任务 = self._查找任务(任务ID)
            if not 任务:
                continue
            
            if 任务ID in self.编辑副本 and "是否启用" in self.编辑副本[任务ID]:
                启用 = self.编辑副本[任务ID]["是否启用"]
            else:
                启用 = getattr(任务, '是否启用', True)
            
            项.setText(f"{'☑' if 启用 else '☐'} {任务.任务名称}")
    
    def _批量启用(self, 启用: bool):
        for i in range(self.任务配置列表.count()):
            项 = self.任务配置列表.item(i)
            任务ID = 项.data(Qt.UserRole)
            任务 = self._查找任务(任务ID)
            if 任务:
                任务.是否启用 = 启用
                项.setText(f"{'☑' if 启用 else '☐'} {任务.任务名称}")
            if 任务ID not in self.编辑副本:
                self.编辑副本[任务ID] = {}
            self.编辑副本[任务ID]["是否启用"] = 启用
        
        if self.当前编辑任务ID:
            self._从副本加载到UI()
    
    def _恢复默认配置(self):
        if not self.当前编辑任务ID:
            return
        
        回复 = QMessageBox.question(
            self, "确认恢复",
            "将当前任务配置恢复为默认值？",
            QMessageBox.Yes | QMessageBox.No
        )
        if 回复 != QMessageBox.Yes:
            return
        
        if self.当前编辑任务ID in self.编辑副本:
            del self.编辑副本[self.当前编辑任务ID]
        
        self._从副本加载到UI()
    
    def _搜索过滤(self, 搜索文字):
        for i in range(self.任务配置列表.count()):
            项 = self.任务配置列表.item(i)
            任务ID = 项.data(Qt.UserRole)
            任务 = self._查找任务(任务ID)
            if not 搜索文字 or (任务 and 搜索文字.lower() in 任务.任务名称.lower()):
                项.setHidden(False)
            else:
                项.setHidden(True)