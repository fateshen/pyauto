"""
全局配置标签页
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QScrollArea,
    QGroupBox, QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit, QComboBox
)


class 全局配置标签页(QWidget):
    """全局配置标签页"""
    
    def __init__(self):
        super().__init__()
        self._初始化界面()
        self._原始分辨率缓存 = {}
        self._当前窗口名称 = None
    def _初始化界面(self):
        标签页 = QScrollArea()
        标签页.setWidgetResizable(True)
        
        内容 = QWidget()
        布局 = QVBoxLayout(内容)
        布局.setSpacing(8)
        
        # 玩家信息
        玩家组 = QGroupBox("玩家信息：（注意改变偏移必须先保存窗口配置，然后点击窗口校正来应用偏移才能正常运行）")
        玩家组.setStyleSheet("QGroupBox::title { color: red; }")
        玩家布局 = QFormLayout(玩家组)
        
        self.全局_窗口名称 = QLineEdit()
        self.全局_窗口名称.setReadOnly(True)
        玩家布局.addRow("窗口名称:", self.全局_窗口名称)
        
        self.全局_游戏标题 = QLineEdit()
        self.全局_游戏标题.setReadOnly(True)
        玩家布局.addRow("游戏标题:", self.全局_游戏标题)
        
        self.全局_分辨率W = QSpinBox()
        self.全局_分辨率W.setRange(800, 3840)
        self.全局_分辨率W.setReadOnly(True)        
        玩家布局.addRow("分辨率宽:", self.全局_分辨率W)
        
        self.全局_分辨率H = QSpinBox()
        self.全局_分辨率H.setRange(600, 2160)
        self.全局_分辨率H.setReadOnly(True)       
        玩家布局.addRow("分辨率高:", self.全局_分辨率H)
        
        self.全局_玩家名称 = QLineEdit()
        self.全局_玩家名称.setReadOnly(True)
        玩家布局.addRow("玩家角色名称:", self.全局_玩家名称)
        
        self.全局_公会名称 = QLineEdit()
        self.全局_公会名称.setReadOnly(True)
        玩家布局.addRow("玩家公会名称:", self.全局_公会名称)
        
        self.全局_偏移X = QSpinBox()
        self.全局_偏移X.setRange(0, 200)
        玩家布局.addRow("窗口偏移X[百度游戏就需要偏移一个百度游戏条的高度x=0]:", self.全局_偏移X)
        self.全局_偏移X.valueChanged.connect(lambda val: self._更新分辨率显示(偏移X=val))

        self.全局_偏移Y = QSpinBox()
        self.全局_偏移Y.setRange(0, 200)
        玩家布局.addRow("窗口偏移Y[百度游戏就需要偏移一个百度游戏条的高度y=46]:", self.全局_偏移Y)
        self.全局_偏移Y.valueChanged.connect(lambda val: self._更新分辨率显示(偏移Y=val))
        布局.addWidget(玩家组)
        
        # 日志配置
        日志组 = QGroupBox("日志配置")
        日志布局 = QFormLayout(日志组)
        self.全局_日志开关 = QCheckBox()
        日志布局.addRow("全局开关:", self.全局_日志开关)
        self.全局_控制台输出 = QCheckBox()
        日志布局.addRow("控制台输出:", self.全局_控制台输出)
        self.全局_文件输出 = QCheckBox()
        日志布局.addRow("文件输出:", self.全局_文件输出)
        self.全局_日志级别 = QComboBox()
        self.全局_日志级别.addItems(["NONE", "ERROR", "WARNING", "INFO", "STATE", "DEBUG", "TRACE", "VERBOSE"])
        日志布局.addRow("全局级别:", self.全局_日志级别)
        self.全局_日志目录 = QLineEdit()
        日志布局.addRow("日志目录:", self.全局_日志目录)
        布局.addWidget(日志组)
        
        # 召唤响应
        召唤组 = QGroupBox("召唤响应")
        召唤布局 = QFormLayout(召唤组)
        self.全局_召唤启用 = QCheckBox()
        召唤布局.addRow("启用召唤响应:", self.全局_召唤启用)
        self.全局_召唤白名单 = QLineEdit()
        self.全局_召唤白名单.setPlaceholderText("空=全响应，逗号分隔")
        召唤布局.addRow("白名单:", self.全局_召唤白名单)
        self.全局_召唤黑名单 = QLineEdit()
        self.全局_召唤黑名单.setPlaceholderText("逗号分隔")
        召唤布局.addRow("黑名单:", self.全局_召唤黑名单)
        布局.addWidget(召唤组)
        
        # 避让
        避让组 = QGroupBox("避让全局设置")
        避让布局 = QFormLayout(避让组)
        self.全局_高战避让 = QCheckBox()
        避让布局.addRow("启用高战避让:", self.全局_高战避让)
        self.全局_避让名单 = QLineEdit()
        self.全局_避让名单.setPlaceholderText("逗号分隔")
        避让布局.addRow("避让杀手名单:", self.全局_避让名单)
        self.全局_避让冷却 = QSpinBox()
        self.全局_避让冷却.setRange(0, 3600)
        self.全局_避让冷却.setSingleStep(10)
        避让布局.addRow("避让冷却秒数:", self.全局_避让冷却)
        self.全局_高频避让 = QCheckBox()
        避让布局.addRow("启用高频死亡避让:", self.全局_高频避让)
        self.全局_高频次数 = QSpinBox()
        self.全局_高频次数.setRange(1, 10)
        避让布局.addRow("高频死亡次数:", self.全局_高频次数)
        self.全局_高频秒数 = QSpinBox()
        self.全局_高频秒数.setRange(10, 300)
        避让布局.addRow("高频死亡间隔秒:", self.全局_高频秒数)
        布局.addWidget(避让组)
        
        # 回城
        回城组 = QGroupBox("回城回血[低血量的时候回城回血]")
        回城布局 = QFormLayout(回城组)
        self.全局_回城启用 = QCheckBox()
        回城布局.addRow("启用回城回血:", self.全局_回城启用)
        self.全局_回城阈值 = QSpinBox()
        self.全局_回城阈值.setRange(1, 100)
        回城布局.addRow("回城血量阈值(%):", self.全局_回城阈值)
        布局.addWidget(回城组)
        
        # 服务器
        服务器组 = QGroupBox("用服务器范围判定公会玩家【此服务器范围内玩家视为友军】")
        服务器布局 = QFormLayout(服务器组)
        self.全局_服务器规则 = QCheckBox()
        服务器布局.addRow("此范围视为队友:", self.全局_服务器规则)
        self.全局_服务器低 = QSpinBox()
        self.全局_服务器低.setRange(0, 9999)
        服务器布局.addRow("服务器范围低:", self.全局_服务器低)
        self.全局_服务器高 = QSpinBox()
        self.全局_服务器高.setRange(0, 9999)
        服务器布局.addRow("服务器范围高:", self.全局_服务器高)
        布局.addWidget(服务器组)
        
        # 攻击模式
        攻击组 = QGroupBox("攻击模式")
        攻击布局 = QFormLayout(攻击组)
        self.全局_攻击模式 = QComboBox()
        self.全局_攻击模式.addItems(["", "全体模式", "和平模式", "行会模式", "队伍模式"])
        攻击布局.addRow("默认攻击模式:", self.全局_攻击模式)
        布局.addWidget(攻击组)
        
        # 通知
        通知组 = QGroupBox("通知消息")
        通知布局 = QFormLayout(通知组)
        self.全局_通知启用 = QCheckBox()
        通知布局.addRow("启用通知消息:", self.全局_通知启用)
        self.全局_太古通知 = QCheckBox()
        通知布局.addRow("太古祖龙刷新通知:", self.全局_太古通知)
        self.全局_聊天通知 = QCheckBox()
        通知布局.addRow("聊天通知:", self.全局_聊天通知)
        self.全局_企业微信Webhook = QLineEdit()
        self.全局_企业微信Webhook.setPlaceholderText(
            "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
        )
        通知布局.addRow(
            "企业微信机器人:",
            self.全局_企业微信Webhook,
        )
        布局.addWidget(通知组)
        
        布局.addStretch()
        标签页.setWidget(内容)
        
        外布局 = QVBoxLayout(self)
        外布局.setContentsMargins(0, 0, 0, 0)
        外布局.addWidget(标签页)
    
    def 加载配置(self, 线程):
        """从线程加载全局配置"""
        if not 线程:
            return
        玩家 = 线程.游戏配置.玩家
        self._填充玩家配置(玩家)
        self._填充日志配置()
        self._填充策略配置(玩家)
    
    def 加载配置_纯配置(self, 配置):
        """从配置对象加载全局配置"""
        if not 配置:
            return
        self._填充玩家配置(配置.玩家)
        self._填充日志配置()
        self._填充策略配置(配置.玩家)
    
    def _填充玩家配置(self, 玩家):
        self.全局_窗口名称.setText(玩家.窗口名称)
        self.全局_游戏标题.setText(玩家.游戏标题)
        self.全局_分辨率W.setValue(玩家.游戏分辨率[0]+玩家.窗口偏移X)
        self.全局_分辨率H.setValue(玩家.游戏分辨率[1]+玩家.窗口偏移Y)
        self.全局_玩家名称.setText(玩家.玩家角色名称)
        self.全局_公会名称.setText(getattr(玩家, '玩家公会名称', ''))
        self.全局_偏移X.setValue(玩家.窗口偏移X)
        self.全局_偏移Y.setValue(玩家.窗口偏移Y)
    
    def _填充只读字段(self, 窗口名称,全局缓存):
        """加载只读的玩家信息字段（不受编辑副本管理），每次切换窗口时调用"""
        from models.game_config import 玩家配置
        玩家 = 玩家配置.从文件加载(窗口名称)
        self._当前窗口名称 = 窗口名称
        # 玩家 = 配置.玩家
        self._原始分辨率缓存[窗口名称] = (玩家.游戏分辨率[0], 玩家.游戏分辨率[1])
        self.全局_窗口名称.setText(玩家.窗口名称)
        self.全局_游戏标题.setText(玩家.游戏标题)
        if 全局缓存:
            self._更新分辨率显示(全局缓存["偏移X"], 全局缓存["偏移Y"])
        else:
           self._更新分辨率显示(玩家.窗口偏移X, 玩家.窗口偏移Y)
        self.全局_玩家名称.setText(玩家.玩家角色名称)
        self.全局_公会名称.setText(getattr(玩家, '玩家公会名称', ''))
    
    def _更新分辨率显示(self, 偏移X=None, 偏移Y=None):
        if not self._当前窗口名称:
            return
        if 偏移X is None:
            偏移X = self.全局_偏移X.value()
        if 偏移Y is None:
            偏移Y = self.全局_偏移Y.value()
        
        原始 = self._原始分辨率缓存.get(self._当前窗口名称, (0, 0))
        self.全局_分辨率W.setValue(原始[0] + 偏移X)
        self.全局_分辨率H.setValue(原始[1] + 偏移Y)
    def _填充日志配置(self):
        """从 debug_config.json 读取日志配置，每次切换窗口时调用"""
        import json
        from pathlib import Path
        
        配置路径 = Path("config/debug_config.json")
        if not 配置路径.exists():
            return
        
        try:
            with open(配置路径, 'r', encoding='utf-8') as f:
                配置 = json.load(f)
            
            self.全局_日志开关.setChecked(配置.get("全局开关", True))
            self.全局_控制台输出.setChecked(配置.get("控制台输出", True))
            self.全局_文件输出.setChecked(配置.get("文件输出", True))
            
            级别映射 = {0: "NONE", 1: "ERROR", 2: "WARNING", 3: "INFO", 4: "STATE", 5: "DEBUG", 6: "TRACE", 7: "VERBOSE"}
            级别 = 配置.get("全局级别", 4)
            self.全局_日志级别.setCurrentText(级别映射.get(级别, "STATE"))
            
            self.全局_日志目录.setText(配置.get("日志目录", "logs"))
        except:
            pass
    
    def _填充策略配置(self, 玩家):
        复活 = 玩家.战斗.复活
        检测 = 玩家.战斗.检测
        
        self.全局_召唤启用.setChecked(玩家.启用召唤响应)
        self.全局_召唤白名单.setText(玩家.召唤响应白名单)
        self.全局_召唤黑名单.setText(玩家.召唤响应黑名单)
        self.全局_高战避让.setChecked(复活.启用高战避让模式)
        self.全局_避让名单.setText(复活.避让杀手名单)
        self.全局_避让冷却.setValue(复活.避让冷却秒数)
        self.全局_高频避让.setChecked(复活.启用高频死亡避让模式)
        self.全局_高频次数.setValue(复活.高频死亡避让次数)
        self.全局_高频秒数.setValue(复活.高频死亡避让秒数)
        self.全局_回城启用.setChecked(检测.启用回城回血)
        self.全局_回城阈值.setValue(检测.回城血量阈值)
        self.全局_服务器规则.setChecked(玩家.服务器规则视为队友)
        self.全局_服务器低.setValue(玩家.服务器范围低)
        self.全局_服务器高.setValue(玩家.服务器范围高)
        self.全局_攻击模式.setCurrentText(玩家.默认攻击模式)
        self.全局_通知启用.setChecked(玩家.启用通知消息)
        self.全局_太古通知.setChecked(玩家.发送太古祖龙刷新通知)
        self.全局_聊天通知.setChecked(玩家.启用聊天通知)
        self.全局_企业微信Webhook.setText(玩家.企业微信机器人Webhook)
    
    # ==================== 编辑副本接口 ====================
    
    def 获取编辑结果(self) -> dict:
        """获取所有可编辑控件的当前值"""
        return {
            "偏移X": self.全局_偏移X.value(),
            "偏移Y": self.全局_偏移Y.value(),
            "召唤启用": self.全局_召唤启用.isChecked(),
            "白名单": self.全局_召唤白名单.text(),
            "黑名单": self.全局_召唤黑名单.text(),
            "高战避让": self.全局_高战避让.isChecked(),
            "避让名单": self.全局_避让名单.text(),
            "避让冷却": self.全局_避让冷却.value(),
            "高频避让": self.全局_高频避让.isChecked(),
            "高频次数": self.全局_高频次数.value(),
            "高频秒数": self.全局_高频秒数.value(),
            "回城启用": self.全局_回城启用.isChecked(),
            "回城阈值": self.全局_回城阈值.value(),
            "服务器规则": self.全局_服务器规则.isChecked(),
            "服务器低": self.全局_服务器低.value(),
            "服务器高": self.全局_服务器高.value(),
            "攻击模式": self.全局_攻击模式.currentText(),
            "通知启用": self.全局_通知启用.isChecked(),
            "太古通知": self.全局_太古通知.isChecked(),
            "聊天通知": self.全局_聊天通知.isChecked(),
            "企业微信Webhook": self.全局_企业微信Webhook.text().strip(),
            "日志开关": self.全局_日志开关.isChecked(),
            "控制台输出": self.全局_控制台输出.isChecked(),
            "文件输出": self.全局_文件输出.isChecked(),
            "日志级别": self.全局_日志级别.currentText(),
            "日志目录": self.全局_日志目录.text(),
        }
    
    def 应用编辑副本(self, 副本: dict):
        """将编辑副本的值恢复到控件（只处理可编辑字段）"""
        if not 副本:
            return
        if "偏移X" in 副本:
            self.全局_偏移X.setValue(副本["偏移X"])
        if "偏移Y" in 副本:
            self.全局_偏移Y.setValue(副本["偏移Y"])
        if "召唤启用" in 副本:
            self.全局_召唤启用.setChecked(副本["召唤启用"])
        if "白名单" in 副本:
            self.全局_召唤白名单.setText(副本["白名单"])
        if "黑名单" in 副本:
            self.全局_召唤黑名单.setText(副本["黑名单"])
        if "高战避让" in 副本:
            self.全局_高战避让.setChecked(副本["高战避让"])
        if "避让名单" in 副本:
            self.全局_避让名单.setText(副本["避让名单"])
        if "避让冷却" in 副本:
            self.全局_避让冷却.setValue(副本["避让冷却"])
        if "高频避让" in 副本:
            self.全局_高频避让.setChecked(副本["高频避让"])
        if "高频次数" in 副本:
            self.全局_高频次数.setValue(副本["高频次数"])
        if "高频秒数" in 副本:
            self.全局_高频秒数.setValue(副本["高频秒数"])
        if "回城启用" in 副本:
            self.全局_回城启用.setChecked(副本["回城启用"])
        if "回城阈值" in 副本:
            self.全局_回城阈值.setValue(副本["回城阈值"])
        if "服务器规则" in 副本:
            self.全局_服务器规则.setChecked(副本["服务器规则"])
        if "服务器低" in 副本:
            self.全局_服务器低.setValue(副本["服务器低"])
        if "服务器高" in 副本:
            self.全局_服务器高.setValue(副本["服务器高"])
        if "攻击模式" in 副本:
            self.全局_攻击模式.setCurrentText(副本["攻击模式"])
        if "通知启用" in 副本:
            self.全局_通知启用.setChecked(副本["通知启用"])
        if "太古通知" in 副本:
            self.全局_太古通知.setChecked(副本["太古通知"])
        if "聊天通知" in 副本:
            self.全局_聊天通知.setChecked(副本["聊天通知"])
        if "企业微信Webhook" in 副本:
            self.全局_企业微信Webhook.setText(副本["企业微信Webhook"])
        if "日志开关" in 副本:
            self.全局_日志开关.setChecked(副本["日志开关"])
        if "控制台输出" in 副本:
            self.全局_控制台输出.setChecked(副本["控制台输出"])
        if "文件输出" in 副本:
            self.全局_文件输出.setChecked(副本["文件输出"])
        if "日志级别" in 副本:
            self.全局_日志级别.setCurrentText(副本["日志级别"])
        if "日志目录" in 副本:
            self.全局_日志目录.setText(副本["日志目录"])
