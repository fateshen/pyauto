# core/map_navigator.py
"""
步骤式地图进入器
基于切换操作类实现多步骤导航
"""
from core.page_switcher import 切换操作工厂


class 步骤式地图进入器:
    """步骤式地图进入器"""
    
    def __init__(self, 线程):
        """
        初始化进入器
        
        参数:
            线程: 窗口线程实例（持有全局变量）
        """
        self.线程 = 线程
        self.步骤列表 = []
    
    def 配置步骤(self, 步骤配置列表: list):
        """
        配置进入步骤
        
        步骤配置格式:
        [
            {
                "点击类型": "点击文字",
                "点击配置": {...},
                "验证配置": {...},
                "重试配置": {...}
            },
            ...
        ]
        """
        self.步骤列表 = []
        for 配置 in 步骤配置列表:
            操作 = 切换操作工厂.创建(self.线程, 配置)
            self.步骤列表.append(操作)
    
    def 进入(self) -> bool:
        """
        执行进入流程
        
        返回:
            True: 所有步骤成功
            False: 某步骤失败
        """
        for 步骤 in self.步骤列表:
            成功 = 步骤.执行()
            if not 成功:
                return False
        return True
    
    def 清空步骤(self):
        """清空步骤列表"""
        self.步骤列表 = []