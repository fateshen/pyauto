# ui/widgets.py
"""
自定义控件
"""
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QCheckBox
)
from PySide6.QtCore import Qt


class 多选子任务控件(QWidget):
    """子任务多选控件（复选框列表）"""
    
    def __init__(self, 选项映射: dict, 默认选中: str = ""):
        super().__init__()
        self.选项映射 = 选项映射
        布局 = QVBoxLayout(self)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(2)
        
        self.复选框列表 = {}
        for 值, 名称 in 选项映射.items():
            复选框 = QCheckBox(f"{值} - {名称}")
            复选框.setChecked(值 in 默认选中.split(","))
            self.复选框列表[值] = 复选框
            布局.addWidget(复选框)
    
    def 获取选中值(self) -> str:
        选中 = [值 for 值, 框 in self.复选框列表.items() if 框.isChecked()]
        return ",".join(选中)
    
    def 设置选中值(self, 值字符串: str):
        选中集合 = set(值字符串.split(",")) if 值字符串 else set()
        for 值, 框 in self.复选框列表.items():
            框.setChecked(值 in 选中集合)


class 子任务双选控件(QWidget):
    """子任务队列 + 次优先级任务队列，左右双栏"""
    
    def __init__(self, 选项映射: dict, 主默认: str = "", 次默认: str = "", 主tip: str = "", 次tip: str = ""):
        super().__init__()
        self.选项映射 = 选项映射
        
        主布局 = QHBoxLayout(self)
        主布局.setContentsMargins(0, 0, 0, 0)
        主布局.setSpacing(6)
        
        # 左：子任务队列
        左布局 = QVBoxLayout()
        self.主标题 = QLabel("子任务队列:")
        if 主tip:
            self.主标题.setToolTip(主tip)
        左布局.addWidget(self.主标题)
        self.主复选框列表 = {}
        主选中 = set(主默认.split(",")) if 主默认 else set()
        for 值, 名称 in 选项映射.items():
            复选框 = QCheckBox(f"{值} - {名称}")
            复选框.setChecked(值 in 主选中)
            if 主tip:
                复选框.setToolTip(主tip)
            self.主复选框列表[值] = 复选框
            左布局.addWidget(复选框)
        主布局.addLayout(左布局)
        
        # 分割线
        分割线 = QWidget()
        分割线.setFixedWidth(1)
        分割线.setStyleSheet("background-color: #ccc;")
        主布局.addWidget(分割线)
        
        # 右：次优先级任务队列
        右布局 = QVBoxLayout()
        self.次标题 = QLabel("次优先级队列:")
        if 次tip:
            self.次标题.setToolTip(次tip)
        右布局.addWidget(self.次标题)
        self.次复选框列表 = {}
        次选中 = set(次默认.split(",")) if 次默认 else set()
        for 值, 名称 in 选项映射.items():
            复选框 = QCheckBox(f"{值} - {名称}")
            复选框.setChecked(值 in 次选中)
            if 次tip:
                复选框.setToolTip(次tip)
            self.次复选框列表[值] = 复选框
            右布局.addWidget(复选框)
        主布局.addLayout(右布局)
    
    def 获取主选中(self) -> str:
        return ",".join([v for v, c in self.主复选框列表.items() if c.isChecked()])
    
    def 获取次选中(self) -> str:
        return ",".join([v for v, c in self.次复选框列表.items() if c.isChecked()])
    
    def 设置主选中(self, 值: str):
        选中 = set(值.split(",")) if 值 else set()
        for v, c in self.主复选框列表.items():
            c.setChecked(v in 选中)
    
    def 设置次选中(self, 值: str):
        选中 = set(值.split(",")) if 值 else set()
        for v, c in self.次复选框列表.items():
            c.setChecked(v in 选中)


class 击杀顺序控件(QWidget):
    """击杀顺序编辑控件：左侧可选列表 + 右侧已选顺序（可拖拽排序）"""
    
    def __init__(self, 选项映射: dict, 默认顺序: str = ""):
        super().__init__()
        self.选项映射 = 选项映射
        
        主布局 = QHBoxLayout(self)
        主布局.setContentsMargins(0, 0, 0, 0)
        主布局.setSpacing(6)
        
        # 左侧：可选BOSS列表
        左侧布局 = QVBoxLayout()
        左侧布局.addWidget(QLabel("可选BOSS:"))
        self.可选列表 = QListWidget()
        self.可选列表.setSelectionMode(QListWidget.SingleSelection)
        for 值, 名称 in 选项映射.items():
            项 = QListWidgetItem(f"{值} - {名称}")
            项.setData(Qt.UserRole, 值)
            self.可选列表.addItem(项)
        左侧布局.addWidget(self.可选列表)
        
        # 中间：移动按钮
        中间布局 = QVBoxLayout()
        中间布局.addStretch()
        self.添加按钮 = QPushButton("→")
        self.添加按钮.clicked.connect(self._添加)
        中间布局.addWidget(self.添加按钮)
        self.移除按钮 = QPushButton("←")
        self.移除按钮.clicked.connect(self._移除)
        中间布局.addWidget(self.移除按钮)
        中间布局.addStretch()
        
        # 右侧：已选顺序
        右侧布局 = QVBoxLayout()
        右侧布局.addWidget(QLabel("击杀顺序:"))
        self.顺序列表控件 = QListWidget()
        self.顺序列表控件.setSelectionMode(QListWidget.SingleSelection)
        右侧布局.addWidget(self.顺序列表控件)
        
        # 排序按钮
        排序按钮布局 = QHBoxLayout()
        self.上移按钮 = QPushButton("↑")
        self.上移按钮.clicked.connect(self._上移)
        排序按钮布局.addWidget(self.上移按钮)
        self.下移按钮 = QPushButton("↓")
        self.下移按钮.clicked.connect(self._下移)
        排序按钮布局.addWidget(self.下移按钮)
        右侧布局.addLayout(排序按钮布局)
        
        主布局.addLayout(左侧布局)
        主布局.addLayout(中间布局)
        主布局.addLayout(右侧布局, stretch=1)
        
        if 默认顺序:
            self.设置顺序值(默认顺序)
    
    def _添加(self):
        当前项 = self.可选列表.currentItem()
        if not 当前项:
            return
        值 = 当前项.data(Qt.UserRole)
        名称 = self.选项映射.get(值, 值)
        
        for i in range(self.顺序列表控件.count()):
            if self.顺序列表控件.item(i).data(Qt.UserRole) == 值:
                return
        
        项 = QListWidgetItem(f"{self.顺序列表控件.count() + 1}. {名称}")
        项.setData(Qt.UserRole, 值)
        self.顺序列表控件.addItem(项)
        self._刷新序号()
    
    def _移除(self):
        当前行 = self.顺序列表控件.currentRow()
        if 当前行 >= 0:
            self.顺序列表控件.takeItem(当前行)
            self._刷新序号()
    
    def _上移(self):
        当前行 = self.顺序列表控件.currentRow()
        if 当前行 > 0:
            项 = self.顺序列表控件.takeItem(当前行)
            self.顺序列表控件.insertItem(当前行 - 1, 项)
            self.顺序列表控件.setCurrentRow(当前行 - 1)
            self._刷新序号()
    
    def _下移(self):
        当前行 = self.顺序列表控件.currentRow()
        if 当前行 < self.顺序列表控件.count() - 1:
            项 = self.顺序列表控件.takeItem(当前行)
            self.顺序列表控件.insertItem(当前行 + 1, 项)
            self.顺序列表控件.setCurrentRow(当前行 + 1)
            self._刷新序号()
    
    def _刷新序号(self):
        for i in range(self.顺序列表控件.count()):
            项 = self.顺序列表控件.item(i)
            值 = 项.data(Qt.UserRole)
            名称 = self.选项映射.get(值, 值)
            项.setText(f"{i + 1}. {名称}")
    
    def 获取顺序值(self) -> str:
        值列表 = []
        for i in range(self.顺序列表控件.count()):
            值列表.append(self.顺序列表控件.item(i).data(Qt.UserRole))
        return ",".join(值列表)
    
    def 设置顺序值(self, 值字符串: str):
        self.顺序列表控件.clear()
        if not 值字符串:
            return
        for 值 in 值字符串.split(","):
            值 = 值.strip()
            if not 值:
                continue
            名称 = self.选项映射.get(值, 值)
            项 = QListWidgetItem(f"{self.顺序列表控件.count() + 1}. {名称}")
            项.setData(Qt.UserRole, 值)
            self.顺序列表控件.addItem(项)