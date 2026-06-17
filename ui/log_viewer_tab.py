# ui/log_viewer_tab.py
"""
日志查看标签页
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QPlainTextEdit
)
from PySide6.QtCore import Qt
from pathlib import Path
from core.debug import 线程日志管理器

class 日志标签页(QWidget):
    """日志查看标签页"""
    
    def __init__(self):
        super().__init__()
        self.当前窗口 = None
        self._初始化界面()
    
    def _初始化界面(self):
        布局 = QVBoxLayout(self)
        布局.setContentsMargins(0, 0, 0, 0)
        
        工具栏 = QHBoxLayout()
        工具栏.addWidget(QLabel("级别:"))
        self.日志级别 = QComboBox()
        self.日志级别.addItems(["全部", "INFO", "STATE", "DEBUG", "TRACE", "WARNING", "ERROR"])
        工具栏.addWidget(self.日志级别)
        工具栏.addStretch()
        self.日志刷新按钮 = QPushButton("刷新")
        工具栏.addWidget(self.日志刷新按钮)
        布局.addLayout(工具栏)
        
        self.未运行提示 = QLabel("窗口未运行")
        self.未运行提示.setAlignment(Qt.AlignCenter)
        self.未运行提示.setStyleSheet("color: #999; font-size: 14px;")
        
        self.日志内容 = QPlainTextEdit()
        self.日志内容.setReadOnly(True)
        self.日志内容.setStyleSheet("""
            QPlainTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
        """)
        
        布局.addWidget(self.未运行提示)
        布局.addWidget(self.日志内容)
    
    def 切换窗口(self, 窗口名称: str):
        """切换到指定窗口的日志"""
        self.当前窗口 = 窗口名称
        日志路径 = self._日志路径(窗口名称)
        
        if not 日志路径.exists():
            self.日志内容.hide()
            self.未运行提示.setText("暂无日志")
            self.未运行提示.show()
            return
        
        self.未运行提示.hide()
        self.日志内容.show()
        self._刷新日志()
    
    def _刷新日志(self):
        if not self.当前窗口:
            return
        
        日志路径 = self._日志路径(self.当前窗口)
        if not 日志路径.exists():
            return
        
        try:
            with open(日志路径, 'r', encoding='utf-8') as f:
                行列表 = f.readlines()
                self.日志内容.setPlainText(''.join(行列表[-500:]))
        except:
            self.日志内容.setPlainText("读取日志失败")

    def _日志路径(self, 窗口名称: str) -> Path:

        return 线程日志管理器._获取日志文件路径(窗口名称, 线程日志管理器._获取当前日期())