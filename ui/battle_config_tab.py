"""
战斗配置标签页
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QScrollArea,
    QGroupBox, QDoubleSpinBox, QCheckBox
)


class 战斗配置标签页(QWidget):
    """战斗配置标签页"""
    
    def __init__(self):
        super().__init__()
        self._初始化界面()
    
    def _初始化界面(self):
        标签页 = QScrollArea()
        标签页.setWidgetResizable(True)
        
        内容 = QWidget()
        布局 = QVBoxLayout(内容)
        布局.setSpacing(8)
        
        # 检测配置
        检测组 = QGroupBox("检测配置")
        检测布局 = QFormLayout(检测组)
        self.战斗_无目标超时 = QDoubleSpinBox()
        self.战斗_无目标超时.setRange(1, 30)
        检测布局.addRow("无目标超时(秒):", self.战斗_无目标超时)
        self.战斗_静止超时 = QDoubleSpinBox()
        self.战斗_静止超时.setRange(1, 30)
        检测布局.addRow("静止超时(秒):", self.战斗_静止超时)
        self.战斗_开战超时 = QDoubleSpinBox()
        self.战斗_开战超时.setRange(1, 30)
        检测布局.addRow("开战超时(秒):", self.战斗_开战超时)
        布局.addWidget(检测组)
        
        # 等待配置
        等待组 = QGroupBox("等待配置")
        等待布局 = QFormLayout(等待组)
        self.战斗_循环间隔 = QDoubleSpinBox()
        self.战斗_循环间隔.setRange(0.1, 5)
        self.战斗_循环间隔.setSingleStep(0.1)
        等待布局.addRow("主循环间隔(秒):", self.战斗_循环间隔)
        self.战斗_刷新等待 = QDoubleSpinBox()
        self.战斗_刷新等待.setRange(0.1, 5)
        self.战斗_刷新等待.setSingleStep(0.1)
        等待布局.addRow("刷新等待(秒):", self.战斗_刷新等待)
        布局.addWidget(等待组)
        
        # 自动战斗配置
        自动组 = QGroupBox("自动战斗")
        自动布局 = QFormLayout(自动组)
        self.战斗_自动战斗 = QCheckBox()
        自动布局.addRow("启用自动战斗:", self.战斗_自动战斗)
        self.战斗_自动走位 = QCheckBox()
        自动布局.addRow("启用自动走位:", self.战斗_自动走位)
        布局.addWidget(自动组)
        
        布局.addStretch()
        标签页.setWidget(内容)
        
        外布局 = QVBoxLayout(self)
        外布局.setContentsMargins(0, 0, 0, 0)
        外布局.addWidget(标签页)
    
    def 加载配置(self, 线程):
        """从线程加载战斗配置"""
        if not 线程:
            return
        战斗 = 线程.游戏配置.战斗
        self._填充配置(战斗)
    
    def 加载配置_纯配置(self, 配置):
        """从配置对象加载战斗配置"""
        if not 配置:
            return
        self._填充配置(配置.战斗)
    
    def _填充配置(self, 战斗):
        self.战斗_无目标超时.setValue(战斗.超时.无目标超时秒数)
        self.战斗_静止超时.setValue(战斗.超时.静止超时秒数)
        self.战斗_开战超时.setValue(战斗.超时.开战超时秒数)
        self.战斗_循环间隔.setValue(战斗.等待.主循环间隔秒)
        self.战斗_刷新等待.setValue(战斗.等待.刷新等待秒)
        self.战斗_自动战斗.setChecked(战斗.自动战斗.启用自动战斗)
        self.战斗_自动走位.setChecked(战斗.自动战斗.启用自动走位)
    
    # ==================== 编辑副本接口 ====================
    
    def 获取编辑结果(self) -> dict:
        """获取所有控件的当前值"""
        return {
            "无目标超时": self.战斗_无目标超时.value(),
            "静止超时": self.战斗_静止超时.value(),
            "开战超时": self.战斗_开战超时.value(),
            "循环间隔": self.战斗_循环间隔.value(),
            "刷新等待": self.战斗_刷新等待.value(),
            "自动战斗": self.战斗_自动战斗.isChecked(),
            "自动走位": self.战斗_自动走位.isChecked(),
        }
    
    def 应用编辑副本(self, 副本: dict):
        """将编辑副本的值恢复到控件"""
        if not 副本:
            return
        if "无目标超时" in 副本:
            self.战斗_无目标超时.setValue(副本["无目标超时"])
        if "静止超时" in 副本:
            self.战斗_静止超时.setValue(副本["静止超时"])
        if "开战超时" in 副本:
            self.战斗_开战超时.setValue(副本["开战超时"])
        if "循环间隔" in 副本:
            self.战斗_循环间隔.setValue(副本["循环间隔"])
        if "刷新等待" in 副本:
            self.战斗_刷新等待.setValue(副本["刷新等待"])
        if "自动战斗" in 副本:
            self.战斗_自动战斗.setChecked(副本["自动战斗"])
        if "自动走位" in 副本:
            self.战斗_自动走位.setChecked(副本["自动走位"])