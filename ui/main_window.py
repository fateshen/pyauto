"""
游戏助手主窗口
"""
import sys
import time
import json
from ctypes import windll
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QTabWidget, QMessageBox, QStatusBar, QApplication,
    QAbstractSpinBox, QComboBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
import subprocess
from ui.task_config_tab import 任务配置标签页
# from ui.task_config_defs import 任务配置定义
from ui.task_status_tab import 任务状态标签页
from ui.battle_config_tab import 战斗配置标签页
from ui.global_config_tab import 全局配置标签页
from ui.reward_task_tab import 强化奖励标签页
# from ui.reward_task_defs import 强化奖励任务定义
from ui.log_viewer_tab import 日志标签页
from core.debug import 调试器
from ui.reward_task_tab import _加载强化奖励任务定义, 强化奖励任务定义
from ui.task_config_tab import _加载任务配置定义, 任务配置定义

def 检查UMI运行() -> bool:
    """检查 UMI-OCR 进程是否在运行"""
    try:
        结果 = subprocess.run(
            ['tasklist', '/fi', 'IMAGENAME eq UMI-OCR.exe'],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        return 'Umi-OCR.exe' in 结果.stdout
    except:
        return False
    
class 主窗口(QMainWindow):
    """游戏助手主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("游戏助手")
        self.resize(1050, 650)
        
        self.窗口线程列表 = {}
        self.窗口配置字典 = {}
        self.当前选中窗口名称 = None
        self.正在获取句柄 = False
        self.句柄检测定时器 = None
        
        # 编辑副本：{窗口名: {"任务": {任务ID: {字段: 值}}, "战斗": {...}, "全局": {...}, "强化奖励": {...}}}
        self._窗口编辑副本 = {}
        
        # 任务列表缓存：{窗口名: {"任务": [任务对象列表], "强化奖励": [实例列表]}}
        self._窗口任务列表缓存 = {}
        self._窗口句柄缓存 = {} # {窗口名: 句柄字符串}
        self._禁用滚轮()
        self._扫描已有窗口()
        self._初始化界面()
        self._初始化菜单栏()
        self._初始化状态栏()
        self._连接信号()
    
        if self.窗口列表.count() > 0:
            self.窗口列表.setCurrentRow(0)

        # UMI-OCR 监控
        self.umi监控定时器 = QTimer()
        self.umi监控定时器.timeout.connect(self._检查UMI状态)
        self.umi监控定时器.start(3000)
        self._检查UMI状态()
    
     
    def _禁用滚轮(self):
        QAbstractSpinBox.wheelEvent = lambda self, event: event.ignore()
        QComboBox.wheelEvent = lambda self, event: event.ignore()
    
    def _扫描已有窗口(self):
        配置根目录 = Path("config")
        if not 配置根目录.exists():
            return
        for 子目录 in 配置根目录.iterdir():
            if 子目录.is_dir() and (子目录 / "user_config.json").exists():
                self.窗口配置字典[子目录.name] = None
    
    def _初始化界面(self):
        中央控件 = QWidget()
        self.setCentralWidget(中央控件)
        主布局 = QHBoxLayout(中央控件)
        主布局.setContentsMargins(6, 6, 6, 6)
        主布局.setSpacing(6)
        
        主布局.addWidget(self._创建左侧面板())
        主布局.addWidget(self._创建右侧面板(), stretch=2)
    
    def _创建左侧面板(self) -> QWidget:
        面板 = QWidget()
        面板.setFixedWidth(180)
        布局 = QVBoxLayout(面板)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(4)
        
        self.窗口列表 = QListWidget()
        self.窗口列表.setStyleSheet("""
            QListWidget::item {
                padding: 6px 4px;
                min-height: 28px;
            }
            QListWidget::item:selected {
                background-color: #1a73e8;
                color: white;
                font-weight: bold;
            }
            QListWidget::item:!selected {
                color: #333;
            }
            QListWidget::item:hover:!selected {
                background-color: #d2e3fc;
                color: #1a73e8;
            }
            QListWidget:focus {
                outline: none;
            }
            QListWidget::item:selected:!focus {
                background-color: #93c5fd;
                color: #1a73e8;
                font-weight: bold;
            }
        """)
        self.窗口列表.currentItemChanged.connect(self._窗口选中)
        布局.addWidget(self.窗口列表)
        
        self.添加按钮 = QPushButton("+ 添加窗口")
        self.添加按钮.clicked.connect(self._添加窗口)
        布局.addWidget(self.添加按钮)
        
        分隔线 = QWidget()
        分隔线.setFixedHeight(1)
        分隔线.setStyleSheet("background-color: #ccc;")
        布局.addWidget(分隔线)
        
        self.启动按钮 = QPushButton("启动")
        self.启动按钮.clicked.connect(self._启动窗口)
        布局.addWidget(self.启动按钮)
        
        self.暂停按钮 = QPushButton("暂停")
        self.暂停按钮.clicked.connect(self._暂停窗口)
        布局.addWidget(self.暂停按钮)

        self.恢复按钮 = QPushButton("恢复")
        self.恢复按钮.clicked.connect(self._恢复窗口)
        布局.addWidget(self.恢复按钮)

        self.停止按钮 = QPushButton("停止")
        self.停止按钮.clicked.connect(self._停止窗口)
        布局.addWidget(self.停止按钮)
        
        self.全部停止按钮 = QPushButton("全部停止")
        self.全部停止按钮.clicked.connect(self._全部停止)
        布局.addWidget(self.全部停止按钮)
        
        for 窗口名称 in self.窗口配置字典:
            项 = QListWidgetItem(f"{窗口名称}  ⚪")
            项.setData(Qt.UserRole, 窗口名称)
            self.窗口列表.addItem(项)
        
        return 面板
    
    def _创建右侧面板(self) -> QWidget:
        面板 = QWidget()
        布局 = QVBoxLayout(面板)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(4)
        
        布局.addWidget(self._创建顶部信息栏())
        
        self.内容标签页 = QTabWidget()
        self.任务配置标签 = 任务配置标签页()
        self.任务状态标签 = 任务状态标签页()
        self.战斗配置标签 = 战斗配置标签页()
        self.全局配置标签 = 全局配置标签页()
        self.强化奖励标签 = 强化奖励标签页()
        self.日志标签 = 日志标签页()
        
        self.内容标签页.addTab(self.任务配置标签, "任务配置")
        self.内容标签页.addTab(self.任务状态标签, "任务状态")
        self.内容标签页.addTab(self.战斗配置标签, "战斗配置")
        self.内容标签页.addTab(self.全局配置标签, "全局配置")
        self.内容标签页.addTab(self.强化奖励标签, "强化奖励")
        self.内容标签页.addTab(self.日志标签, "日志")
        布局.addWidget(self.内容标签页)
        
        return 面板
    
    def _创建顶部信息栏(self) -> QWidget:
        信息栏 = QWidget()
        布局 = QHBoxLayout(信息栏)
        布局.setContentsMargins(0, 0, 0, 0)
        布局.setSpacing(6)
        
        布局.addWidget(QLabel("窗口名称:"))
        self.窗口名称输入 = QLineEdit()
        self.窗口名称输入.setFixedWidth(120)  # 稍微加宽
        self.窗口名称输入.setPlaceholderText("游戏1")
        self.窗口名称输入.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                font-weight: bold;
                color: #1a73e8;
                background-color: #e8f0fe;
                border: 2px solid #1a73e8;
                border-radius: 4px;
                padding: 2px 6px;
            }
        """)
        布局.addWidget(self.窗口名称输入)
        
        布局.addWidget(QLabel("句柄:"))
        self.句柄输入 = QLineEdit()
        self.句柄输入.setFixedWidth(80)
        self.句柄输入.setReadOnly(True)
        self.句柄输入.setPlaceholderText("未设置")
        布局.addWidget(self.句柄输入)
        
        self.获取句柄按钮 = QPushButton("获取句柄")
        self.获取句柄按钮.setCheckable(True)
        self.获取句柄按钮.clicked.connect(self._获取句柄)
        布局.addWidget(self.获取句柄按钮)
        
        self.窗口校正按钮 = QPushButton("窗口校正")
        self.窗口校正按钮.clicked.connect(self._窗口校正)
        布局.addWidget(self.窗口校正按钮)
        
        self.保存窗口按钮 = QPushButton("保存窗口配置")
        self.保存窗口按钮.setStyleSheet("font-weight: bold;")
        self.保存窗口按钮.clicked.connect(self._保存窗口配置)
        布局.addWidget(self.保存窗口按钮)
        # ========== UMI-OCR 状态和启动 ==========
        self.umi状态标签 = QLabel("● 检测中...")
        self.umi状态标签.setStyleSheet("font-weight: bold; padding: 2px 6px; border-radius: 3px;")
        布局.addWidget(self.umi状态标签)

        self.启动UMI按钮 = QPushButton("启动UMI")
        self.启动UMI按钮.setStyleSheet("padding: 2px 8px;")
        self.启动UMI按钮.clicked.connect(self._启动UMI)
        布局.addWidget(self.启动UMI按钮)

        布局.addStretch()
        return 信息栏
    
    def _初始化菜单栏(self):
        菜单栏 = self.menuBar()
        
        文件菜单 = 菜单栏.addMenu("文件")
        保存所有 = QAction("保存所有配置", self)
        文件菜单.addAction(保存所有)
        文件菜单.addSeparator()
        退出 = QAction("退出", self)
        退出.triggered.connect(self.close)
        文件菜单.addAction(退出)
        
        帮助菜单 = 菜单栏.addMenu("帮助")
        关于 = QAction("关于", self)
        帮助菜单.addAction(关于)
    
    def _初始化状态栏(self):
        self.状态栏 = QStatusBar()
        self.setStatusBar(self.状态栏)
        self.状态栏.showMessage("就绪")
    
    def _连接信号(self):
        self.内容标签页.currentChanged.connect(self._标签页切换)
    
    def _标签页切换(self, index):
        标签名 = self.内容标签页.tabText(index)
        if 标签名 == "日志" and self.当前选中窗口名称:
            self.日志标签.切换窗口(self.当前选中窗口名称)
        elif 标签名 == "任务状态" and self.当前选中窗口名称:
            线程 = self.窗口线程列表.get(self.当前选中窗口名称)
            self.任务状态标签.加载状态(线程)
    
    # ==================== 获取句柄 ====================
    
    def _获取句柄(self):
        if self.正在获取句柄:
            self._取消获取句柄()
            return
        
        self.正在获取句柄 = True
        self.获取句柄按钮.setChecked(True)
        self.获取句柄按钮.setText("请点击目标窗口...")
        self.setCursor(Qt.CrossCursor)
        
        self.句柄检测定时器 = QTimer()
        self.句柄检测定时器.timeout.connect(self._检测鼠标点击)
        self.句柄检测定时器.start(100)
    
    def _检测鼠标点击(self):
        if windll.user32.GetAsyncKeyState(0x01) & 0x8000:
            from win32gui import WindowFromPoint, GetCursorPos
            x, y = GetCursorPos()
            句柄 = WindowFromPoint((x, y))
            self.句柄输入.setText(str(句柄))
            if self.当前选中窗口名称:
                self._窗口句柄缓存[self.当前选中窗口名称] = str(句柄)
            self._取消获取句柄()
    
    def _取消获取句柄(self):
        self.正在获取句柄 = False
        self.获取句柄按钮.setChecked(False)
        self.获取句柄按钮.setText("获取句柄")
        self.setCursor(Qt.ArrowCursor)
        if self.句柄检测定时器:
            self.句柄检测定时器.stop()
            self.句柄检测定时器 = None
    
    # ==================== 窗口校正 ====================
    
    def _获取顶层父窗口(self, 子句柄: int) -> int:
        import win32gui
        当前句柄 = 子句柄
        父句柄 = win32gui.GetParent(当前句柄)
        while 父句柄 != 0:
            当前句柄 = 父句柄
            父句柄 = win32gui.GetParent(当前句柄)
        return 当前句柄
    
    # def _窗口校正(self):
    #     if not self.当前选中窗口名称:
    #         QMessageBox.warning(self, "错误", "请先选择窗口")
    #         return
    #     try:
    #         子句柄 = int(self.句柄输入.text())
    #     except ValueError:
    #         QMessageBox.warning(self, "错误", "请先获取窗口句柄")
    #         return
        
    #     import win32gui
        
    #     顶层句柄 = self._获取顶层父窗口(子句柄)
    #     调试器.debug("UI", f"窗口校正: 子句柄={子句柄}, 顶层句柄={顶层句柄}")
        
    #     子客户区 = win32gui.GetClientRect(子句柄)
    #     当前宽 = 子客户区[2] - 子客户区[0]
    #     当前高 = 子客户区[3] - 子客户区[1]
        
    #     from models.game_config import 游戏全局配置
    #     配置 = 游戏全局配置.从文件加载(self.当前选中窗口名称)
    #     目标宽, 目标高 = 配置.玩家.游戏分辨率
        
    #     if 当前宽 == 目标宽 and 当前高 == 目标高:
    #         QMessageBox.information(self, "提示", "窗口尺寸已匹配，无需校正")
    #         return
        
    #     父窗口区域 = win32gui.GetWindowRect(顶层句柄)
    #     父窗口宽 = 父窗口区域[2] - 父窗口区域[0]
    #     父窗口高 = 父窗口区域[3] - 父窗口区域[1]
        
    #     边框宽 = 父窗口宽 - 当前宽
    #     边框高 = 父窗口高 - 当前高
        
    #     新父窗口宽 = 目标宽 + 边框宽
    #     新父窗口高 = 目标高 + 边框高
        
    #     win32gui.SetWindowPos(
    #         顶层句柄, 0,
    #         父窗口区域[0], 父窗口区域[1],
    #         新父窗口宽, 新父窗口高,
    #         0x0004
    #     )
        
    #     调试器.info("UI", f"窗口校正完成: {父窗口宽}x{父窗口高} → {新父窗口宽}x{新父窗口高}")
    #     QMessageBox.information(self, "提示", f"窗口校正完成\n客户区: {当前宽}x{当前高} → {目标宽}x{目标高}")
    def _窗口校正(self):
        if not self.当前选中窗口名称:
            QMessageBox.warning(self, "错误", "请先选择窗口")
            return
        try:
            子句柄 = int(self.句柄输入.text())
        except ValueError:
            QMessageBox.warning(self, "错误", "请先获取窗口句柄")
            return
        
        import win32gui
        
        顶层句柄 = self._获取顶层父窗口(子句柄)
        调试器.debug("UI", f"窗口校正: 子句柄={子句柄}, 顶层句柄={顶层句柄}")
        
        from models.game_config import 游戏全局配置
        配置 = 游戏全局配置.从文件加载(self.当前选中窗口名称)
        原始宽, 原始高 = 配置.玩家.游戏分辨率
        偏移X = 配置.玩家.窗口偏移X
        偏移Y = 配置.玩家.窗口偏移Y
        目标宽 = 原始宽 + 偏移X
        目标高 = 原始高 + 偏移Y
        
        调试器.debug("UI", f"窗口校正: 原始={原始宽}x{原始高}, 偏移=({偏移X},{偏移Y}), 目标={目标宽}x{目标高}")
        
        def _执行校正():
            子客户区 = win32gui.GetClientRect(子句柄)
            当前宽 = 子客户区[2] - 子客户区[0]
            当前高 = 子客户区[3] - 子客户区[1]
            
            if 当前宽 == 目标宽 and 当前高 == 目标高:
                return True, "已匹配"
            
            父窗口区域 = win32gui.GetWindowRect(顶层句柄)
            边框宽 = (父窗口区域[2] - 父窗口区域[0]) - 当前宽
            边框高 = (父窗口区域[3] - 父窗口区域[1]) - 当前高
            
            新父窗口宽 = 目标宽 + 边框宽
            新父窗口高 = 目标高 + 边框高
            
            win32gui.SetWindowPos(
                顶层句柄, 0,
                父窗口区域[0], 父窗口区域[1],
                新父窗口宽, 新父窗口高,
                0x0004
            )
            return False, None
        
        # 第一次尝试
        已匹配, _ = _执行校正()
        
        if 已匹配:
            QMessageBox.information(self, "提示", "窗口尺寸已匹配，无需校正")
            return
        
        # 复查
        import time
        time.sleep(0.1)
        子客户区 = win32gui.GetClientRect(子句柄)
        当前宽 = 子客户区[2] - 子客户区[0]
        当前高 = 子客户区[3] - 子客户区[1]
        
        if 当前宽 == 目标宽 and 当前高 == 目标高:
            调试器.info("UI", f"窗口校正成功: {目标宽}x{目标高}")
            QMessageBox.information(self, "提示", f"窗口校正完成\n客户区: {目标宽}x{目标高}")
            return
        
        # 失败，再试一次
        调试器.warning("UI", f"窗口校正复查失败({当前宽}x{当前高}≠{目标宽}x{目标高})，再次尝试")
        _执行校正()
        
        time.sleep(0.1)
        子客户区 = win32gui.GetClientRect(子句柄)
        当前宽 = 子客户区[2] - 子客户区[0]
        当前高 = 子客户区[3] - 子客户区[1]
        
        if 当前宽 == 目标宽 and 当前高 == 目标高:
            调试器.info("UI", f"窗口校正重试成功: {目标宽}x{目标高}")
            QMessageBox.information(self, "提示", f"窗口校正完成\n客户区: {目标宽}x{目标高}")
        else:
            调试器.error("UI", f"窗口校正失败: 当前={当前宽}x{当前高}, 目标={目标宽}x{目标高}")
            QMessageBox.warning(self, "警告", f"窗口校正失败\n当前: {当前宽}x{当前高}\n目标: {目标宽}x{目标高}")
    
    # ==================== 窗口选中与切换 ====================
    
    def _窗口选中(self, 当前, 上一个):
        """切换窗口：1. 保存当前窗口控件值到副本  2. 加载目标窗口"""
        if self.当前选中窗口名称:
            # 保存当前窗口的编辑状态到副本
            self._保存当前窗口到副本()
        
        if 当前:
            self.当前选中窗口名称 = 当前.data(Qt.UserRole)
            self._切换到窗口(self.当前选中窗口名称)
    
    def _保存当前窗口到副本(self):
        """将当前窗口所有控件的值保存到编辑副本"""
        窗口名称 = self.当前选中窗口名称
        if not 窗口名称:
            return
        
        任务编辑 = self.任务配置标签.获取所有编辑结果()
        战斗编辑 = self.战斗配置标签.获取编辑结果()
        全局编辑 = self.全局配置标签.获取编辑结果()
        强化奖励编辑 = self.强化奖励标签.获取所有编辑结果()
        
        self._窗口编辑副本[窗口名称] = {
            "任务": 任务编辑,
            "战斗": 战斗编辑,
            "全局": 全局编辑,
            "强化奖励": 强化奖励编辑,
        }
    
    def _切换到窗口(self, 窗口名称):
        """切换到目标窗口：从副本恢复控件值，如果副本不存在则从文件加载并创建副本"""
        线程 = self.窗口线程列表.get(窗口名称)
        
        # ========== 基础信息 ==========
        self.窗口名称输入.setText(窗口名称)
        if 线程:
            self.句柄输入.setText(str(线程.窗口句柄))
        else:
            句柄 = self._窗口句柄缓存.get(窗口名称)
            if 句柄:
                self.句柄输入.setText(句柄)
            else:
                self.句柄输入.setText("未设置")
        
        # ========== 确保窗口的任务列表已缓存 ==========
        self._确保窗口已缓存(窗口名称)
        
        # ========== 切换到缓存的列表 ==========
        缓存 = self._窗口任务列表缓存[窗口名称]
        self.任务配置标签.切换到任务列表(缓存["任务"])
        self.强化奖励标签.切换到任务列表(缓存["强化奖励"])
        
        # ========== 从副本恢复控件值 ==========
        副本 = self._窗口编辑副本.get(窗口名称, {})
        self.任务配置标签.应用编辑副本(副本.get("任务", {}))
        self.强化奖励标签.应用编辑副本(副本.get("强化奖励", {}))
        self.战斗配置标签.应用编辑副本(副本.get("战斗", {}))
        self.全局配置标签.应用编辑副本(副本.get("全局", {}))
        
        # ========== 加载只读字段和日志配置（不依赖编辑副本） ==========
        self.全局配置标签._填充只读字段(窗口名称,副本.get("全局", {}))
        self.全局配置标签._填充日志配置()
        
        # ========== 刷新UI ==========
        self.任务配置标签._刷新列表启用状态_全部()
        self.强化奖励标签._刷新列表启用状态_全部()
        
        # 恢复上次选中的任务
        self.任务配置标签._恢复上次选中任务()
        self.强化奖励标签._恢复上次选中任务()
        
        self._刷新单个窗口状态(窗口名称)
    
    def _确保窗口已缓存(self, 窗口名称):
        """确保指定窗口的任务列表已加载到缓存中。如果缓存中没有，从文件加载并创建完整副本。"""
        if 窗口名称 in self._窗口任务列表缓存:
            return
        
        # 加载任务列表
        from tasks import 初始化任务系统
        初始化任务系统()
        from tasks import 获取所有任务配置
        默认任务列表 = 获取所有任务配置()
        任务列表 = self._加载任务配置从文件(窗口名称, 默认任务列表)
        
        # 加载强化奖励列表
        from core.reward_manager import 强化奖励管理器
        临时管理器 = 强化奖励管理器(窗口名称=窗口名称)
        强化奖励列表 = 临时管理器.任务实例列表
        
        # 加载战斗/全局配置
        from models.game_config import 游戏全局配置
        配置 = 游戏全局配置.从文件加载(窗口名称)
        
        # 缓存列表结构
        self._窗口任务列表缓存[窗口名称] = {
            "任务": 任务列表,
            "强化奖励": 强化奖励列表,
        }
        
        # 如果副本不存在，创建初始副本（从文件/配置对象读取的值）
        if 窗口名称 not in self._窗口编辑副本:
            战斗副本 = {
                "无目标超时": 配置.战斗.超时.无目标超时秒数,
                "静止超时": 配置.战斗.超时.静止超时秒数,
                "开战超时": 配置.战斗.超时.开战超时秒数,
                "循环间隔": 配置.战斗.等待.主循环间隔秒,
                "刷新等待": 配置.战斗.等待.刷新等待秒,
                "默认等待毫秒": 配置.战斗.等待.默认等待毫秒,
                "自动战斗": 配置.战斗.自动战斗.启用自动战斗,
                "自动走位": 配置.战斗.自动战斗.启用自动走位,
            }
            全局副本 = {
                "偏移X": 配置.玩家.窗口偏移X,
                "偏移Y": 配置.玩家.窗口偏移Y,
                "召唤启用": 配置.玩家.启用召唤响应,
                "白名单": 配置.玩家.召唤响应白名单,
                "黑名单": 配置.玩家.召唤响应黑名单,
                "高战避让": 配置.玩家.战斗.复活.启用高战避让模式,
                "避让名单": 配置.玩家.战斗.复活.避让杀手名单,
                "避让冷却": 配置.玩家.战斗.复活.避让冷却秒数,
                "高频避让": 配置.玩家.战斗.复活.启用高频死亡避让模式,
                "高频次数": 配置.玩家.战斗.复活.高频死亡避让次数,
                "高频秒数": 配置.玩家.战斗.复活.高频死亡避让秒数,
                "回城启用": 配置.玩家.战斗.检测.启用回城回血,
                "回城阈值": 配置.玩家.战斗.检测.回城血量阈值,
                "服务器规则": 配置.玩家.服务器规则视为队友,
                "服务器低": 配置.玩家.服务器范围低,
                "服务器高": 配置.玩家.服务器范围高,
                "攻击模式": 配置.玩家.默认攻击模式,
                "通知启用": 配置.玩家.启用通知消息,
                "太古通知": 配置.玩家.发送太古祖龙刷新通知,
            }
            self._窗口编辑副本[窗口名称] = {
                "任务": {},
                "战斗": 战斗副本,
                "全局": 全局副本,
                "强化奖励": {},
            }
    
    # def _加载任务配置从文件(self, 窗口名称, 默认任务列表):
    #     import copy
    #     任务列表 = copy.deepcopy(默认任务列表)
        
    #     配置路径 = Path("config") / 窗口名称 / "tasks_config.json"
    #     if not 配置路径.exists():
    #         return 任务列表
        
    #     try:
    #         with open(配置路径, 'r', encoding='utf-8') as f:
    #             数据 = json.load(f)
            
    #         文件任务列表 = 数据.get("任务列表", [])
    #         文件任务映射 = {t["任务ID"]: t for t in 文件任务列表}
            
    #         for 任务 in 任务列表:
    #             if 任务.任务ID in 文件任务映射:
    #                 for 字段名, 值 in 文件任务映射[任务.任务ID].items():
    #                     if 字段名 != "任务ID" and hasattr(任务, 字段名):
    #                         if 值 is None:
    #                             setattr(任务, 字段名, None)
    #                         else:
    #                             setattr(任务, 字段名, 值)
    #     except Exception:
    #         pass
        
    #     return 任务列表
    

    def _加载任务配置从文件(self, 窗口名称, 默认任务列表):
        import copy
        from tasks import 程序任务配置版本
        任务列表 = copy.deepcopy(默认任务列表)
        
        配置路径 = Path("config") / 窗口名称 / "tasks_config.json"
        if not 配置路径.exists():
            return 任务列表
        
        try:
            with open(配置路径, 'r', encoding='utf-8') as f:
                数据 = json.load(f)
            
            文件版本 = 数据.get("版本", "0")
            文件任务列表 = 数据.get("任务列表", [])
            文件任务映射 = {t["任务ID"]: t for t in 文件任务列表}
            
            if 文件版本 != 程序任务配置版本:
                # 版本更新：只保留 UI 字段
                for 任务 in 任务列表:
                    if 任务.任务ID in 文件任务映射:
                        旧数据 = 文件任务映射[任务.任务ID]
                        ui字段 = set(任务配置定义.get(任务.任务名称, {}).keys())
                        需要保留的字段 = ui字段 | {"当前任务可执行的最高层数", "打不过的敌人", "跨服入侵三首龙任务开启",
                                         "节日BOSS开启时间", "上一次完成时间"}
                        for 字段名 in 需要保留的字段:
                            if 字段名 in 旧数据:
                                setattr(任务, 字段名, 旧数据[字段名])
                # 保存合并后的配置
                所有任务配置 = []
                for 任务 in 任务列表:
                    项 = {"任务ID": 任务.任务ID, "任务名称": 任务.任务名称}
                    for 字段名 in 任务配置定义.get(任务.任务名称, {}):
                        项[字段名] = getattr(任务, 字段名, None)
                    所有任务配置.append(项)
                
                数据 = {
                    "版本": 程序任务配置版本,
                    "窗口名称": 窗口名称,
                    "更新时间": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "任务数量": len(所有任务配置),
                    "任务列表": 所有任务配置,
                }
                
                配置路径.parent.mkdir(parents=True, exist_ok=True)
                with open(配置路径, 'w', encoding='utf-8') as f:
                    json.dump(数据, f, ensure_ascii=False, indent=2)
                
                调试器.info("配置", f"窗口 '{窗口名称}' 任务配置版本更新: v{文件版本} → v{程序任务配置版本}")   
            else:
                # 版本一致：原版逻辑
                for 任务 in 任务列表:
                    if 任务.任务ID in 文件任务映射:
                        for 字段名, 值 in 文件任务映射[任务.任务ID].items():
                            if 字段名 != "任务ID" and hasattr(任务, 字段名):
                                if 值 is None:
                                    setattr(任务, 字段名, None)
                                else:
                                    setattr(任务, 字段名, 值)
        except Exception:
            pass
        
        return 任务列表
    
    def _刷新单个窗口状态(self, 窗口名称):
        for i in range(self.窗口列表.count()):
            项 = self.窗口列表.item(i)
            if 项.data(Qt.UserRole) == 窗口名称:
                线程 = self.窗口线程列表.get(窗口名称)
                if 线程 and 线程.运行中:
                    if 线程.暂停中:
                        项.setText(f"{窗口名称}  🟡")
                    else:
                        项.setText(f"{窗口名称}  🟢")
                else:
                    项.setText(f"{窗口名称}  ⚪")
                break
    
    # ==================== 按钮事件 ====================
    
    def _添加窗口(self):
        from PySide6.QtWidgets import QInputDialog
        名称, ok = QInputDialog.getText(self, "添加窗口", "窗口名称:")
        if not ok or not 名称:
            return
        
        if 名称 in self.窗口配置字典:
            QMessageBox.warning(self, "错误", f"窗口 '{名称}' 已存在")
            return
        
        from models.game_config import 游戏全局配置
        配置 = 游戏全局配置.创建默认(名称)
        配置.保存到文件()
        
        self.窗口配置字典[名称] = 配置
        
        项 = QListWidgetItem(f"{名称}  ⚪")
        项.setData(Qt.UserRole, 名称)
        self.窗口列表.addItem(项)
        self.窗口列表.setCurrentItem(项)
    
    def _启动窗口(self):
        if not self.当前选中窗口名称:
            return
        
        try:
            句柄 = int(self.句柄输入.text())
        except ValueError:
            QMessageBox.warning(self, "错误", "请先获取窗口句柄")
            return
        
        线程 = self.窗口线程列表.get(self.当前选中窗口名称)

        if 线程 and not 线程.运行中:
            try:
                线程.信号.停止信号.disconnect()
                线程.信号.启动信号.disconnect()
            except:
                pass
            线程 = None
        
        if 线程 and 线程.运行中:
            return
        
        self._保存窗口配置()
        
        from core.window_thread import 窗口线程
        线程 = 窗口线程(窗口句柄=句柄, 窗口名称=self.当前选中窗口名称)
        线程.信号.停止信号.connect(self._线程已停止)
        线程.信号.启动信号.connect(lambda name: self._刷新单个窗口状态(name))
        self.窗口线程列表[self.当前选中窗口名称] = 线程
        # 应用窗口偏移
        配置 = 线程.游戏配置
        配置.应用窗口偏移(配置.玩家.窗口偏移X, 配置.玩家.窗口偏移Y)
        线程.start()
        self._刷新单个窗口状态(self.当前选中窗口名称)
        调试器.info("UI", f"窗口 '{self.当前选中窗口名称}' 已启动")
    
    def _线程已停止(self, 窗口名称):
        self._刷新单个窗口状态(窗口名称)
    
    def _暂停窗口(self):
        if not self.当前选中窗口名称:
            return
        线程 = self.窗口线程列表.get(self.当前选中窗口名称)
        if 线程 and 线程.运行中:
            线程.暂停()
            self._刷新单个窗口状态(self.当前选中窗口名称)

    def _恢复窗口(self):
        if not self.当前选中窗口名称:
            return
        线程 = self.窗口线程列表.get(self.当前选中窗口名称)
        if 线程 and 线程.运行中:
            线程.恢复()
            self._刷新单个窗口状态(self.当前选中窗口名称)
    
    def _停止窗口(self):
        if not self.当前选中窗口名称:
            return
        线程 = self.窗口线程列表.get(self.当前选中窗口名称)
        if 线程 and 线程.运行中:
            线程.stop()
            self._刷新单个窗口状态(self.当前选中窗口名称)
    
    def _全部停止(self):
        for 线程 in self.窗口线程列表.values():
            if 线程.运行中:
                线程.stop()
        for i in range(self.窗口列表.count()):
            项 = self.窗口列表.item(i)
            名称 = 项.data(Qt.UserRole)
            self._刷新单个窗口状态(名称)
    
    # ==================== 保存配置 ====================
    
    def _保存窗口配置(self):
        if not self.当前选中窗口名称:
            return
        
        窗口名称 = self.当前选中窗口名称
        线程 = self.窗口线程列表.get(窗口名称)
        
        # 保存前先确保当前控件值已写入副本
        self._保存当前窗口到副本()
        
        副本 = self._窗口编辑副本.get(窗口名称, {})
        
        # ========== 1. 保存任务配置 ==========
        self._保存任务配置到文件(窗口名称, 副本.get("任务", {}))
        
        # ========== 2. 保存战斗配置 ==========
        self._保存战斗配置到文件(窗口名称, 副本.get("战斗", {}))
        
        # ========== 3. 保存全局配置 ==========
        self._保存全局配置到文件(窗口名称, 副本.get("全局", {}))
        
        # ========== 4. 保存强化奖励配置 ==========
        self._保存强化奖励配置到文件(窗口名称, 副本.get("强化奖励", {}))
        
        # ========== 5. 如果有线程，从文件重新加载到线程 ==========
        if 线程:
            from models.game_config import 游戏全局配置
            配置 = 游戏全局配置.从文件加载(窗口名称)
            self._同步配置到线程(线程, 配置)
            
            # 同步任务配置到线程
            for 任务ID, 修改字段 in 副本.get("任务", {}).items():
                for t in 线程.任务排序列表:
                    if t.任务ID == 任务ID:
                        for 字段名, 值 in 修改字段.items():
                            if 值 is not None:
                                setattr(t, 字段名, 值)
                        break
            
            # 同步强化奖励配置到线程
            for 任务ID, 修改字段 in 副本.get("强化奖励", {}).items():
                for 实例 in 线程.强化奖励管理器.任务实例列表:
                    if 实例.任务ID == 任务ID:
                        for 字段名, 值 in 修改字段.items():
                            if hasattr(实例, 字段名):
                                setattr(实例, 字段名, 值)
                        break
            # 应用窗口偏移
            配置 = 线程.游戏配置
            配置.应用窗口偏移(配置.玩家.窗口偏移X, 配置.玩家.窗口偏移Y)
        # ========== 6. 保存日志配置 ==========
        self._保存日志配置到文件()
        return True
    
    def _保存任务配置到文件(self, 窗口名称, 任务编辑副本):
        配置路径 = Path("config") / 窗口名称 / "tasks_config.json"
        版本=None
        # 读取旧配置作为基础
        旧任务映射 = {}
        if 配置路径.exists():
            try:
                with open(配置路径, 'r', encoding='utf-8') as f:
                    旧数据 = json.load(f)
                    版本= 旧数据.get("版本")
                for t in 旧数据.get("任务列表", []):
                    旧任务映射[t["任务ID"]] = t
            except:
                pass
        
        缓存 = self._窗口任务列表缓存.get(窗口名称)
        if not 缓存:
            return
        
        所有任务配置 = []
        for 任务 in 缓存["任务"]:
            if 任务.任务ID in 旧任务映射:
                任务配置数据 = 旧任务映射[任务.任务ID].copy()
            else:
                任务配置数据 = {}
            
            任务配置数据["任务ID"] = 任务.任务ID
            任务配置数据["任务名称"] = 任务.任务名称
            
            配置定义 = 任务配置定义.get(任务.任务名称, {})
            
            for 字段名 in 配置定义:
                if 任务.任务ID in 任务编辑副本 and 字段名 in 任务编辑副本[任务.任务ID]:
                    任务配置数据[字段名] = 任务编辑副本[任务.任务ID][字段名]
                elif 字段名 not in 任务配置数据:
                    值 = getattr(任务, 字段名, None)
                    if 值 is not None:
                        任务配置数据[字段名] = 值
            
            所有任务配置.append(任务配置数据)
        if 版本 is None:
            from tasks import 程序任务配置版本
            版本 = 程序任务配置版本
        数据 = {
            "版本": 版本,
            "窗口名称": 窗口名称,
            "更新时间": time.strftime("%Y-%m-%d %H:%M:%S"),
            "任务数量": len(所有任务配置),
            "任务列表": 所有任务配置,
        }
        
        配置路径.parent.mkdir(parents=True, exist_ok=True)
        with open(配置路径, 'w', encoding='utf-8') as f:
            json.dump(数据, f, ensure_ascii=False, indent=2)
    
    def _保存强化奖励配置到文件(self, 窗口名称, 强化奖励编辑副本):
        奖励配置路径 = Path("config") / 窗口名称 / "reward_tasks_config.json"
        版本=None
        旧奖励映射 = {}
        if 奖励配置路径.exists():
            try:
                with open(奖励配置路径, 'r', encoding='utf-8') as f:
                    旧数据 = json.load(f)
                    版本=旧数据.get("版本")
                for t in 旧数据.get("任务列表", []):
                    旧奖励映射[t["任务ID"]] = t
            except:
                pass
        
        缓存 = self._窗口任务列表缓存.get(窗口名称)
        if not 缓存:
            return
        
        所有奖励配置 = []
        for 实例 in 缓存["强化奖励"]:
            if 实例.任务ID in 旧奖励映射:
                任务数据 = 旧奖励映射[实例.任务ID].copy()
            else:
                任务数据 = {}
            
            任务数据["任务ID"] = 实例.任务ID
            任务数据["任务名称"] = 实例.任务名称
            
            配置定义 = 强化奖励任务定义.get(实例.任务名称, {})
            
            for 字段名 in 配置定义:
                if 实例.任务ID in 强化奖励编辑副本 and 字段名 in 强化奖励编辑副本[实例.任务ID]:
                    任务数据[字段名] = 强化奖励编辑副本[实例.任务ID][字段名]
                elif 字段名 not in 任务数据:
                    值 = getattr(实例, 字段名, None)
                    if 值 is not None:
                        任务数据[字段名] = 值
            
            所有奖励配置.append(任务数据)
        if 版本 is  None:
            from core.reward_manager import 强化奖励配置版本
            版本=强化奖励配置版本
        奖励数据 = {
            "版本": 版本,
            "窗口名称": 窗口名称,
            "更新时间": time.strftime("%Y-%m-%d %H:%M:%S"),
            "任务数量": len(所有奖励配置),
            "任务列表": 所有奖励配置,
        }
        
        奖励配置路径.parent.mkdir(parents=True, exist_ok=True)
        with open(奖励配置路径, 'w', encoding='utf-8') as f:
            json.dump(奖励数据, f, ensure_ascii=False, indent=2)
    
    def _保存战斗配置到文件(self, 窗口名称, 战斗副本):
        from models.game_config import 游戏全局配置
        配置 = 游戏全局配置.从文件加载(窗口名称)
        战斗 = 配置.战斗
        战斗.超时.无目标超时秒数 = 战斗副本.get("无目标超时", 战斗.超时.无目标超时秒数)
        战斗.超时.静止超时秒数 = 战斗副本.get("静止超时", 战斗.超时.静止超时秒数)
        战斗.超时.开战超时秒数 = 战斗副本.get("开战超时", 战斗.超时.开战超时秒数)
        战斗.等待.主循环间隔秒 = 战斗副本.get("循环间隔", 战斗.等待.主循环间隔秒)
        战斗.等待.刷新等待秒 = 战斗副本.get("刷新等待", 战斗.等待.刷新等待秒)
        战斗.等待.默认等待毫秒 = 战斗副本.get("默认等待毫秒", 战斗.等待.默认等待毫秒)
        战斗.自动战斗.启用自动战斗 = 战斗副本.get("自动战斗", 战斗.自动战斗.启用自动战斗)
        战斗.自动战斗.启用自动走位 = 战斗副本.get("自动走位", 战斗.自动战斗.启用自动走位)
        配置.保存到文件()
    
    def _保存全局配置到文件(self, 窗口名称, 全局副本):
        from models.game_config import 游戏全局配置
        配置 = 游戏全局配置.从文件加载(窗口名称)
        玩家 = 配置.玩家
        玩家.窗口偏移X = 全局副本.get("偏移X", 玩家.窗口偏移X)
        玩家.窗口偏移Y = 全局副本.get("偏移Y", 玩家.窗口偏移Y)
        玩家.启用召唤响应 = 全局副本.get("召唤启用", 玩家.启用召唤响应)
        玩家.召唤响应白名单 = 全局副本.get("白名单", 玩家.召唤响应白名单)
        玩家.召唤响应黑名单 = 全局副本.get("黑名单", 玩家.召唤响应黑名单)
        玩家.战斗.复活.启用高战避让模式 = 全局副本.get("高战避让", 玩家.战斗.复活.启用高战避让模式)
        玩家.战斗.复活.避让杀手名单 = 全局副本.get("避让名单", 玩家.战斗.复活.避让杀手名单)
        玩家.战斗.复活.避让冷却秒数 = 全局副本.get("避让冷却", 玩家.战斗.复活.避让冷却秒数)
        玩家.战斗.复活.启用高频死亡避让模式 = 全局副本.get("高频避让", 玩家.战斗.复活.启用高频死亡避让模式)
        玩家.战斗.复活.高频死亡避让次数 = 全局副本.get("高频次数", 玩家.战斗.复活.高频死亡避让次数)
        玩家.战斗.复活.高频死亡避让秒数 = 全局副本.get("高频秒数", 玩家.战斗.复活.高频死亡避让秒数)
        玩家.战斗.检测.启用回城回血 = 全局副本.get("回城启用", 玩家.战斗.检测.启用回城回血)
        玩家.战斗.检测.回城血量阈值 = 全局副本.get("回城阈值", 玩家.战斗.检测.回城血量阈值)
        玩家.服务器规则视为队友 = 全局副本.get("服务器规则", 玩家.服务器规则视为队友)
        玩家.服务器范围低 = 全局副本.get("服务器低", 玩家.服务器范围低)
        玩家.服务器范围高 = 全局副本.get("服务器高", 玩家.服务器范围高)
        玩家.默认攻击模式 = 全局副本.get("攻击模式", 玩家.默认攻击模式)
        玩家.启用通知消息 = 全局副本.get("通知启用", 玩家.启用通知消息)
        玩家.发送太古祖龙刷新通知 = 全局副本.get("太古通知", 玩家.发送太古祖龙刷新通知)
        配置.保存到文件()
    
    def _保存日志配置到文件(self):
        """保存日志配置到 debug_config.json（直接从控件取值）"""
        import json
        from pathlib import Path
        
        配置路径 = Path("config/debug_config.json")
        
        旧配置 = {}
        if 配置路径.exists():
            try:
                with open(配置路径, 'r', encoding='utf-8') as f:
                    旧配置 = json.load(f)
            except:
                pass
        
        级别映射 = {"NONE": 0, "ERROR": 1, "WARNING": 2, "INFO": 3, "STATE": 4, "DEBUG": 5, "TRACE": 6, "VERBOSE": 7}
        
        旧配置["全局开关"] = self.全局配置标签.全局_日志开关.isChecked()
        旧配置["控制台输出"] = self.全局配置标签.全局_控制台输出.isChecked()
        旧配置["文件输出"] = self.全局配置标签.全局_文件输出.isChecked()
        旧配置["全局级别"] = 级别映射.get(self.全局配置标签.全局_日志级别.currentText(), 4)
        旧配置["日志目录"] = self.全局配置标签.全局_日志目录.text()
        
        配置路径.parent.mkdir(parents=True, exist_ok=True)
        with open(配置路径, 'w', encoding='utf-8') as f:
            json.dump(旧配置, f, ensure_ascii=False, indent=2)
    def _同步配置到线程(self, 线程, 配置):
        战斗 = 配置.战斗
        线程.游戏配置.战斗.超时.无目标超时秒数 = 战斗.超时.无目标超时秒数
        线程.游戏配置.战斗.超时.静止超时秒数 = 战斗.超时.静止超时秒数
        线程.游戏配置.战斗.超时.开战超时秒数 = 战斗.超时.开战超时秒数
        线程.游戏配置.战斗.等待.主循环间隔秒 = 战斗.等待.主循环间隔秒
        线程.游戏配置.战斗.等待.刷新等待秒 = 战斗.等待.刷新等待秒
        线程.游戏配置.战斗.等待.默认等待毫秒 = 战斗.等待.默认等待毫秒
        线程.游戏配置.战斗.自动战斗.启用自动战斗 = 战斗.自动战斗.启用自动战斗
        线程.游戏配置.战斗.自动战斗.启用自动走位 = 战斗.自动战斗.启用自动走位
        
        玩家 = 配置.玩家
        线程.游戏配置.玩家.窗口偏移X = 玩家.窗口偏移X
        线程.游戏配置.玩家.窗口偏移Y = 玩家.窗口偏移Y
        线程.游戏配置.玩家.启用召唤响应 = 玩家.启用召唤响应
        线程.游戏配置.玩家.召唤响应白名单 = 玩家.召唤响应白名单
        线程.游戏配置.玩家.召唤响应黑名单 = 玩家.召唤响应黑名单
        线程.游戏配置.玩家.战斗.复活.启用高战避让模式 = 玩家.战斗.复活.启用高战避让模式
        线程.游戏配置.玩家.战斗.复活.避让杀手名单 = 玩家.战斗.复活.避让杀手名单
        线程.游戏配置.玩家.战斗.复活.避让冷却秒数 = 玩家.战斗.复活.避让冷却秒数
        线程.游戏配置.玩家.战斗.复活.启用高频死亡避让模式 = 玩家.战斗.复活.启用高频死亡避让模式
        线程.游戏配置.玩家.战斗.复活.高频死亡避让次数 = 玩家.战斗.复活.高频死亡避让次数
        线程.游戏配置.玩家.战斗.复活.高频死亡避让秒数 = 玩家.战斗.复活.高频死亡避让秒数
        线程.游戏配置.玩家.战斗.检测.启用回城回血 = 玩家.战斗.检测.启用回城回血
        线程.游戏配置.玩家.战斗.检测.回城血量阈值 = 玩家.战斗.检测.回城血量阈值
        线程.游戏配置.玩家.服务器规则视为队友 = 玩家.服务器规则视为队友
        线程.游戏配置.玩家.服务器范围低 = 玩家.服务器范围低
        线程.游戏配置.玩家.服务器范围高 = 玩家.服务器范围高
        线程.游戏配置.玩家.默认攻击模式 = 玩家.默认攻击模式
        线程.游戏配置.玩家.启用通知消息 = 玩家.启用通知消息
        线程.游戏配置.玩家.发送太古祖龙刷新通知 = 玩家.发送太古祖龙刷新通知
    
    # ==================== 公共方法 ====================
    
    def 添加窗口线程(self, 线程):
        self.窗口线程列表[线程.窗口名称] = 线程
        self.窗口配置字典[线程.窗口名称] = None
        for i in range(self.窗口列表.count()):
            if self.窗口列表.item(i).data(Qt.UserRole) == 线程.窗口名称:
                return
        项 = QListWidgetItem(f"{线程.窗口名称}  ⚪")
        项.setData(Qt.UserRole, 线程.窗口名称)
        self.窗口列表.addItem(项)

    def _检查UMI状态(self):
        if 检查UMI运行():
            self.umi状态标签.setText("● UMI-OCR 运行中")
            self.umi状态标签.setStyleSheet("color: #2e7d32; background-color: #e8f5e9; font-weight: bold; padding: 2px 6px; border-radius: 3px;")
            self.启动UMI按钮.setEnabled(False)
        else:
            self.umi状态标签.setText("● UMI-OCR 未启动")
            self.umi状态标签.setStyleSheet("color: #c62828; background-color: #ffebee; font-weight: bold; padding: 2px 6px; border-radius: 3px;")
            self.启动UMI按钮.setEnabled(True)
    # def _启动UMI(self):
    #     """启动 UMI-OCR"""
    #     from pathlib import Path
    #     import subprocess
    #     import os
        
    #     可能路径列表 = [
    #         Path("UMI-OCR/UMI-OCR.exe"),
    #         Path("../UMI-OCR/UMI-OCR.exe"),
    #     ]
        
    #     for 路径 in 可能路径列表:
    #         if 路径.exists():
    #             subprocess.Popen(str(路径.absolute()), cwd=str(路径.parent.absolute()),
    #                         creationflags=subprocess.CREATE_NO_WINDOW)
    #             self.umi状态标签.setText("● UMI-OCR 启动中...")
    #             self.umi状态标签.setStyleSheet("color: #e65100; background-color: #fff3e0; font-weight: bold; padding: 2px 6px; border-radius: 3px;")
    #             return
        
    #     # 没找到，让用户手动选择
    #     from PySide6.QtWidgets import QFileDialog
    #     路径, _ = QFileDialog.getOpenFileName(self, "选择 UMI-OCR.exe", "", "可执行文件 (*.exe)")
    #     if 路径:
    #         subprocess.Popen(路径, creationflags=subprocess.CREATE_NO_WINDOW)
    def _启动UMI(self):
        from pathlib import Path
        import sys
        import subprocess
        
        可能路径列表 = [
            Path("UMI-OCR/UMI-OCR.exe"),
            Path("../UMI-OCR/UMI-OCR.exe"),
        ]
        
        for 路径 in 可能路径列表:
            if 路径.exists():
                # 用 explorer 启动，完全独立进程
                subprocess.Popen(['explorer', str(路径.absolute())])
                self.umi状态标签.setText("● UMI-OCR 启动中...")
                return
        
        QMessageBox.information(self, "提示", "未找到 UMI-OCR.exe")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    from core.debug import 加载配置
    加载配置()
    
    窗口 = 主窗口()
    窗口.show()
    sys.exit(app.exec())