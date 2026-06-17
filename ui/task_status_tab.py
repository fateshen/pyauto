# ui/task_status_tab.py
"""
任务状态标签页
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel
)
from PySide6.QtCore import Qt
import time

class 任务状态标签页(QWidget):
    """任务状态标签页：表格显示所有任务的运行状态"""
    
    def __init__(self):
        super().__init__()
        self.当前线程 = None
        self._初始化界面()
    
    def _初始化界面(self):
        布局 = QVBoxLayout(self)
        布局.setContentsMargins(0, 0, 0, 0)
        
        self.未运行提示 = QLabel("窗口未运行")
        self.未运行提示.setAlignment(Qt.AlignCenter)
        self.未运行提示.setStyleSheet("color: #999; font-size: 14px; padding: 50px;")
        布局.addWidget(self.未运行提示)
        
        self.状态表格 = QTableWidget()
        self.状态表格.setColumnCount(5)
        self.状态表格.setHorizontalHeaderLabels(["任务名", "状态", "剩余", "地图", "备注"])
        self.状态表格.horizontalHeader().setStretchLastSection(True)
        self.状态表格.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.状态表格.setEditTriggers(QTableWidget.NoEditTriggers)
        self.状态表格.setSelectionBehavior(QTableWidget.SelectRows)
        self.状态表格.hide()
        布局.addWidget(self.状态表格)
        
        按钮行 = QHBoxLayout()
        self.刷新状态按钮 = QPushButton("刷新状态")
        self.刷新状态按钮.clicked.connect(self._刷新)
        self.刷新状态按钮.hide()
        按钮行.addStretch()
        按钮行.addWidget(self.刷新状态按钮)
        布局.addLayout(按钮行)
    
    def 加载状态(self, 线程):
        self.当前线程 = 线程
        
        if not 线程:
            self.未运行提示.show()
            self.状态表格.hide()
            self.刷新状态按钮.hide()
            return
        
        self.未运行提示.hide()
        self.状态表格.show()
        self.刷新状态按钮.show()
        
        任务列表 = 线程.任务排序列表
        self.状态表格.setRowCount(len(任务列表))
        self.状态表格.setColumnCount(4)
        self.状态表格.setHorizontalHeaderLabels(["任务名", "剩余次数", "下次刷新", "入口失败"])
        
        for i, 任务 in enumerate(任务列表):
            状态 = 线程.任务状态映射.get(任务.任务ID)
            
            self.状态表格.setItem(i, 0, QTableWidgetItem(任务.任务名称))
            
            # 剩余次数
            if 状态:
                try:
                    剩余 = str(状态.剩余次数)
                except:
                    剩余 = str(状态.剩余次数)
            else:
                剩余 = "-"
            self.状态表格.setItem(i, 1, QTableWidgetItem(剩余))
            
            # 下次刷新时间
            if 状态 and getattr(状态, '下次刷新时间', 0) > 0:
                剩余秒 = int(状态.下次刷新时间 - time.time())
                if 剩余秒 > 0:
                    时 = 剩余秒 // 3600
                    分 = (剩余秒 % 3600) // 60
                    秒 = 剩余秒 % 60
                    if 时 > 0:
                        刷新 = f"{时}:{分:02d}:{秒:02d}"
                    else:
                        刷新 = f"{分}:{秒:02d}"
                else:
                    刷新 = "已到"
            else:
                刷新 = "-"
            self.状态表格.setItem(i, 2, QTableWidgetItem(刷新))
            
            # 入口连续失败次数
            if 状态:
                失败次数 = getattr(状态, '入口连续失败次数', 0)
                冷却次数 = getattr(状态, '入口冷却触发次数', 5)
                入口失败 = f"{失败次数}/{冷却次数}" if 失败次数 > 0 else "0"
            else:
                入口失败 = "-"
            self.状态表格.setItem(i, 3, QTableWidgetItem(入口失败))
    
    def _刷新(self):
        if self.当前线程:
            self.加载状态(self.当前线程)