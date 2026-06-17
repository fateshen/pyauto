"""
强化奖励标签页 — 基于 reward_task_defs.py 动态生成控件
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QScrollArea, QGroupBox, QSpinBox, QCheckBox, QComboBox,
    QLabel, QMessageBox
)
from PySide6.QtCore import Qt

# from ui.reward_task_defs import 强化奖励任务定义

import sys
from pathlib import Path
from core.path_manager import path_mgr
def _加载强化奖励任务定义():
    外部文件 = path_mgr.run_dir / "ui" / "reward_task_defs.py"
    if 外部文件.exists():
        import importlib
        父目录 = str(外部文件.parent)
        if 父目录 not in sys.path:
            sys.path.insert(0, 父目录)
        模块 = importlib.import_module("reward_task_defs")
        return getattr(模块, "强化奖励任务定义", {})
    
    from ui.reward_task_defs import 强化奖励任务定义
    return 强化奖励任务定义

强化奖励任务定义 = _加载强化奖励任务定义()

class 强化奖励标签页(QWidget):
    """强化奖励标签页：左侧任务列表 + 右侧动态配置"""
    
    def __init__(self):
        super().__init__()
        self.当前任务实例列表 = []
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
    
    def 切换到任务列表(self, 任务实例列表):
        """切换窗口时，替换当前任务列表并刷新左侧列表显示（不触发编辑）"""
        之前选中ID = self.当前编辑任务ID
        self.当前任务实例列表 = 任务实例列表 or []
        self.当前编辑任务ID = None
        
        self.任务配置列表.blockSignals(True)
        self.任务配置列表.clear()
        for 实例 in self.当前任务实例列表:
            启用标记 = "☑" if 实例.是否启用 else "☐"
            项 = QListWidgetItem(f"{启用标记} {实例.任务名称}")
            项.setData(Qt.UserRole, 实例.任务ID)
            self.任务配置列表.addItem(项)
        self.任务配置列表.blockSignals(False)
        
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
    
    def 加载任务列表(self, 任务实例列表, 保留编辑副本=False):
        self.当前任务实例列表 = 任务实例列表 or []
        if not 保留编辑副本:
            self.编辑副本 = {}
        self.任务配置列表.clear()
        
        for 实例 in self.当前任务实例列表:
            启用标记 = "☑" if 实例.是否启用 else "☐"
            项 = QListWidgetItem(f"{启用标记} {实例.任务名称}")
            项.setData(Qt.UserRole, 实例.任务ID)
            self.任务配置列表.addItem(项)
    
    def _查找实例(self, 任务ID):
        for t in self.当前任务实例列表:
            if t.任务ID == 任务ID:
                return t
        return None
    
    def _任务选中(self, 当前, 上一个):
        if self.当前编辑任务ID:
            self._保存UI到副本()
        
        if 当前:
            self.当前编辑任务ID = 当前.data(Qt.UserRole)
            self._动态生成配置UI()
            self._从副本加载到UI()
    
    def _动态生成配置UI(self):
        实例 = self._查找实例(self.当前编辑任务ID)
        if not 实例:
            return
        
        配置定义 = 强化奖励任务定义.get(实例.任务名称, {})
        if not 配置定义:
            return
        
        while self.配置布局.count() > 1:
            item = self.配置布局.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.控件映射 = {}
        
        组 = QGroupBox(实例.任务名称)
        布局 = QFormLayout(组)
        
        for 字段名, 定义 in 配置定义.items():
            if 字段名 not in 配置定义:
                continue
            
            控件类型 = 定义[0]
            默认值 = 定义[1]
            额外参数 = 定义[2] if len(定义) > 2 else None
            tip = 定义[3] if len(定义) > 3 else None
            
            if 控件类型 == "check":
                控件 = QCheckBox()
                布局.addRow(字段名 + ":", 控件)
                if 字段名 == "是否启用":
                    控件.toggled.connect(lambda checked: self._刷新列表启用状态(checked))
            elif 控件类型 == "spin":
                控件 = QSpinBox()
                控件.setRange(0, 99999)
                布局.addRow(字段名 + ":", 控件)
            elif 控件类型 == "text":
                控件 = QLineEdit()
                布局.addRow(字段名 + ":", 控件)
            elif 控件类型 == "combo":
                控件 = QComboBox()
                if 额外参数:
                    控件.addItems(额外参数)
                布局.addRow(字段名 + ":", 控件)
            else:
                continue
            
            if tip:
                控件.setToolTip(tip)
            
            self.控件映射[字段名] = (控件类型, 控件)
        
        self.配置布局.insertWidget(self.配置布局.count() - 1, 组)
    
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
                副本[字段名] = 控件.currentText()
        
        self.编辑副本[self.当前编辑任务ID] = 副本
    
    def _从副本加载到UI(self):
        if not self.当前编辑任务ID or not self.控件映射:
            return
        
        实例 = self._查找实例(self.当前编辑任务ID)
        if not 实例:
            return
        
        副本 = self.编辑副本.get(self.当前编辑任务ID, {})
        
        for 字段名, (控件类型, 控件) in self.控件映射.items():
            if 字段名 in 副本:
                值 = 副本[字段名]
            else:
                值 = getattr(实例, 字段名, None)
            
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
                控件.setCurrentText(str(值) if 值 else "")
    
    def _刷新列表启用状态(self, 启用: bool):
        if not self.当前编辑任务ID:
            return
        for i in range(self.任务配置列表.count()):
            项 = self.任务配置列表.item(i)
            if 项.data(Qt.UserRole) == self.当前编辑任务ID:
                实例 = self._查找实例(self.当前编辑任务ID)
                if 实例:
                    项.setText(f"{'☑' if 启用 else '☐'} {实例.任务名称}")
                break
    
    def _刷新列表启用状态_全部(self):
        for i in range(self.任务配置列表.count()):
            项 = self.任务配置列表.item(i)
            任务ID = 项.data(Qt.UserRole)
            实例 = self._查找实例(任务ID)
            if not 实例:
                continue
            
            if 任务ID in self.编辑副本 and "是否启用" in self.编辑副本[任务ID]:
                启用 = self.编辑副本[任务ID]["是否启用"]
            else:
                启用 = 实例.是否启用
            
            项.setText(f"{'☑' if 启用 else '☐'} {实例.任务名称}")
    
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