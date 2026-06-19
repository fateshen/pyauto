# # main.py
# """
# 游戏挂机自动化 - 主入口

# 功能：
# 1. 窗口选择
# 2. 配置加载
# 3. 任务配置
# 4. 启动窗口线程

# 使用方式：
#     python main.py
# """
# import sys
# import os
# import time
# import signal
# from typing import Optional, List

# from core.utils import 匹配分组关键字

# # 添加项目根目录到路径
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# import win32gui
# import win32con
# from tasks import 获取所有任务配置
# from tasks.base import 任务定义
# from models.game_config import 游戏全局配置
# from core.window_thread import 窗口线程
# from core.path_manager import path_mgr, check_environment, print_status
# from core.debug import (
#     设置日志开关, 设置控制台输出, 设置文件输出,
#     set_global_level, set_log_dir
# )


# # ==================== 窗口管理 ====================

# # 固定窗口名称
# 窗口名称 = "巢元畅"


# def 获取游戏窗口(标题关键词: str = "传奇") -> Optional[int]:
#     """
#     获取游戏窗口句柄
    
#     参数:
#         标题关键词: 窗口标题包含的关键词
    
#     返回:
#         窗口句柄，未找到返回None
#     """
#     结果 = []
    
#     def 枚举回调(句柄, _):
#         if win32gui.IsWindowVisible(句柄):
#             标题 = win32gui.GetWindowText(句柄)
#             if 标题关键词 in 标题 and 标题:
#                 结果.append((句柄, 标题))
#         return True
    
#     win32gui.EnumWindows(枚举回调, None)
    
#     if not 结果:
#         print(f"未找到包含 '{标题关键词}' 的窗口")
#         return None
    
#     print("\n找到以下窗口:")
#     for i, (句柄, 标题) in enumerate(结果):
#         print(f"  {i}. {标题} (句柄: {句柄})")
    
#     while True:
#         try:
#             选择 = input("\n请选择窗口序号: ").strip()
#             if 选择.isdigit():
#                 索引 = int(选择)
#                 if 0 <=索引< len(结果):
#                     return 结果[索引][0]
#             print("输入无效，请重新输入")
#         except KeyboardInterrupt:
#             print("\n已取消")
#             return None
#         except Exception:
#             print("输入无效，请重新输入")


# def 获取所有游戏窗口(标题关键词: str = "传奇") -> List[tuple]:
#     """
#     获取所有游戏窗口（用于多开）
    
#     参数:
#         标题关键词: 窗口标题包含的关键词
    
#     返回:
#         [(句柄, 标题), ...]
#     """
#     结果 = []
    
#     def 枚举回调(句柄, _):
#         if win32gui.IsWindowVisible(句柄):
#             标题 = win32gui.GetWindowText(句柄)
#             if 匹配分组关键字(标题, 标题关键词):
#                 结果.append((句柄, 标题))
#         return True
    
#     win32gui.EnumWindows(枚举回调, None)
#     return 结果


# def find_child_by_class_recursive(hwnd_parent, target_class):
#     """递归查找所有后代窗口中第一个匹配指定类名的窗口"""
#     hwnd_target = win32gui.FindWindowEx(hwnd_parent, 0, target_class, None)
#     if hwnd_target != 0:
#         return hwnd_target
    
#     # 枚举所有直接子窗口
#     hwnd_child = win32gui.GetWindow(hwnd_parent, win32con.GW_CHILD)
#     while hwnd_child:
#         # 递归查找
#         found = find_child_by_class_recursive(hwnd_child, target_class)
#         if found:
#             return found
#         hwnd_child = win32gui.GetWindow(hwnd_child, win32con.GW_HWNDNEXT)
#     return 0


# # ==================== 配置管理 ====================
# def 创建默认配置() -> 游戏全局配置:
#     """创建默认配置"""
#     配置 = 游戏全局配置.创建默认(窗口名称)
    
#     # 设置游戏标题
#     配置.玩家.游戏标题 = "上古"
    
#     return 配置


# def 加载配置文件() -> 游戏全局配置:
#     """加载配置文件（使用固定窗口名称）"""
#     return 游戏全局配置.从文件加载(窗口名称)


# def 保存玩家配置(配置: 游戏全局配置):
#     """保存玩家配置到文件"""
#     try:
#         配置.玩家.保存到文件()
#         print(f"[保存配置] 玩家配置已保存 -> config/{窗口名称}/user_config.json")
#     except Exception as e:
#         print(f"[保存配置] 保存玩家配置失败: {e}")


# def 保存任务配置():
#     """保存当前任务配置到文件（使用固定窗口名称）"""
#     try:
#         任务定义.导出配置到JSON(窗口名称)
#         print(f"[保存配置] 任务配置已保存 -> config/{窗口名称}/tasks_config.json")
#     except Exception as e:
#         print(f"[保存配置] 保存任务配置失败: {e}")


# def 保存所有配置(配置: 游戏全局配置):
#     """保存所有配置（玩家配置 + 任务配置）"""
#     print("\n[保存配置] 开始保存所有配置...")
#     保存玩家配置(配置)
#     保存任务配置()
#     print("[保存配置] 所有配置保存完成")


# def 加载任务配置(窗口名称: str):
#     """加载任务配置（使用固定窗口名称）"""
#     try:
#         任务定义.导入配置从JSON(窗口名称)
#         print(f"[任务系统] 已加载窗口专属任务配置 -> config/{窗口名称}/tasks_config.json")
#     except Exception as e:
#         print(f"[任务系统] 加载任务配置失败: {e}，使用默认配置")


# # main.py

# class 自动化应用:
    
#     def __init__(self):
#         self.线程列表: List[窗口线程] = []
#         self.运行中 = False
#         self.配置: Optional[游戏全局配置] = None
#         self.任务列表: List = []
#         self.窗口名称: str = "巢元畅"  # 固定或可配置
    
#     def 初始化(self):
#         """初始化应用"""
#         print("\n" + "=" * 60)
#         print("游戏挂机自动化系统")
#         print("=" * 60)
#         from tasks import 初始化任务系统
#         初始化任务系统()
#         # 1. 检查环境
#         print("\n[1] 检查运行环境...")
#         if not check_environment():
#             print("环境检查失败，请确保必要目录存在")
#             return False
#         print_status()
        
#         # 2. 获取窗口句柄（在配置加载之前）
#         print("\n[2] 获取游戏窗口...")
#         self.窗口句柄 = 获取游戏窗口("上古")
#         if not self.窗口句柄:
#             print("未选择窗口，退出")
#             return False
        
#         # 3. 初始化全局配置
#         print("\n[3] 加载配置...")
#         self.配置 = self._加载全局配置()
        
#         # 4. 创建任务列表（从内存获取）
#         print("\n[4] 创建任务列表...")
#         self.任务列表 = self._创建任务列表()
        
#         return True
    
#     def _加载全局配置(self) -> 游戏全局配置:
#         """加载全局配置（region + user基础 + tasks）"""
#         # 加载游戏全局配置（区域配置 + 玩家基础配置）
#         config = 游戏全局配置.从文件加载(self.窗口名称)
#         print(f"  从窗口 '{self.窗口名称}' 加载游戏配置")
        
#         # 加载任务配置到内存
#         加载任务配置(self.窗口名称)
#         print(f"  加载窗口 '{self.窗口名称}' 任务配置")
        
#         return config
    
#     def _创建任务列表(self) -> List:
#         """创建任务配置列表（只从已加载的内存中获取）"""
#         return 获取所有任务配置()
    
#     def 运行自动化(self):
#         """运行自动化"""
#         # 5. 创建窗口线程
#         print("\n[5] 启动自动化...")
        
#         线程 = 窗口线程(
#             窗口句柄=self.窗口句柄,
#             窗口名称=self.窗口名称,
#             游戏配置=self.配置,      # 传入已加载的配置
#             任务配置列表=self.任务列表  # 传入已创建的任务列表
#         )
#         线程.start()
#         self.线程列表.append(线程)
        
#         print(f"\n已启动自动化线程: {self.窗口名称}")
#         print("按 Ctrl+C 停止\n")
        
#         # 6. 等待停止
#         self._等待停止()
    
#     def 运行多窗口(self):
#         """多窗口模式"""
#         print("\n[2] 获取所有窗口...")
#         窗口列表 = 获取所有游戏窗口("帝王|上古")
        
#         if not 窗口列表:
#             print("未找到任何游戏窗口")
#             return
        
#         print("\n找到以下窗口:")
#         for i, (句柄, 标题) in enumerate(窗口列表):
#             print(f"  {i}. {标题}")
        
#         选择字符串 = input("\n请输入要启动的窗口序号（多个用逗号分隔）: ").strip()
#         if not 选择字符串:
#             return
        
#         try:
#             索引列表 = [int(x.strip()) for x in 选择字符串.split(',')]
#         except ValueError:
#             print("输入格式错误")
#             return
        
#         # 3. 加载全局配置（只加载一次）
#         print("\n[3] 加载配置...")
#         self.配置 = self._加载全局配置()
#         self.任务列表 = self._创建任务列表()
        
#         # 4. 创建多个线程
#         print("\n[4] 启动自动化...")
#         for 索引 in 索引列表:
#             if 0 <= 索引 < len(窗口列表):
#                 句柄, 标题 = 窗口列表[索引]
#                 print(f"  启动窗口: {标题}")
                
#                 # 查找子窗口句柄
#                 子句柄 = find_child_by_class_recursive(句柄, "Chrome_RenderWidgetHostHWND")
#                 if 子句柄 == 0:
#                     子句柄 = 句柄
                
#                 线程 = 窗口线程(
#                     窗口句柄=子句柄,
#                     窗口名称=self.窗口名称,  # 注意：多个窗口可能共用同一名称空间
#                     游戏配置=self.配置,
#                     任务配置列表=self.任务列表
#                 )
#                 try:
#                     # 线程.游戏配置.玩家.保存到文件()
#                     线程.游戏配置.保存到文件()
#                     保存任务配置()
#                     线程.start()
#                     self.线程列表.append(线程)
#                 except Exception as e:
#                     print(f"线程启动失败: {e}")
#                     import traceback
#                     traceback.print_exc()
        
#         print(f"\n已启动 {len(self.线程列表)} 个自动化线程")
#         self._等待停止()
#     def _创建窗口配置(self, 窗口索引: int) -> 游戏全局配置:
#         """为窗口创建配置（可针对不同窗口调整偏移）"""
#         # 从窗口专属配置加载
#         config = 游戏全局配置.从文件加载(窗口名称)
        
#         # 可以根据窗口索引设置不同的偏移
#         # 例如: 窗口0偏移(8,30)，窗口1偏移(0,0)
#         # if 窗口索引 == 0:
#         #     config.设置窗口偏移(8, 30)
#         # else:
#         #     config.设置窗口偏移(0, 0)
        
#         return config
    
#     def _等待停止(self):
#         """等待停止信号"""
#         self.运行中 = True
        
#         def 信号处理函数(signum, frame):
#             print("\n\n收到停止信号，正在停止...")
#             self.停止()
        
#         # 注册信号处理
#         signal.signal(signal.SIGINT, 信号处理函数)
        
#         try:
#             while self.运行中:
#                 # 检查线程状态
#                 for 线程 in self.线程列表[:]:  # 使用切片遍历避免修改问题
#                     if not 线程.运行中:
#                         print(f"线程 {线程.窗口名称} ({线程.窗口句柄}) 已停止")
#                         self.线程列表.remove(线程)
                
#                 if not self.线程列表:
#                     print("所有线程已停止")
#                     break
                
#                 time.sleep(1)
#         except KeyboardInterrupt:
#             self.停止()
    
#     def 停止(self):
#         """停止所有线程"""
#         print("\n正在停止所有线程...")
#         self.运行中 = False
        
#         for 线程 in self.线程列表:
#             线程.stop()
        
#         for 线程 in self.线程列表:
#             线程.join(timeout=5)
        
#         print("所有线程已停止")
    
#     def 运行(self):
#         """运行应用"""
#          # 1. 设置日志目录
#         set_log_dir("logs")
        
#         # 2. 设置日志总开关（False=完全不输出）
#         设置日志开关(True)
        
#         # 3. 设置输出目标
#         设置控制台输出(True)   # 输出到控制台
#         设置文件输出(True)     # 输出到文件
        
#         # 4. 设置全局级别（所有线程默认）
#         set_global_level(3)    # INFO级别

#         # if not self.初始化():
#         #     return
#         from tasks import 初始化任务系统
#         初始化任务系统()
#         # 显示配置管理菜单
#         # self._显示配置菜单()
        
#         # 启动自动化
#         self.运行多窗口()
        
#         # 退出前保存配置
#         # self._保存配置()
    
#     def _显示配置菜单(self):
#         """显示配置管理菜单"""
#         print("\n" + "-" * 40)
#         print("配置管理")
#         print("-" * 40)
#         print("  1. 查看当前配置")
#         print("  2. 保存配置")
#         print("  3. 加载配置")
#         print("  0. 直接启动")
        
#         try:
#             选择 = input("\n请选择: ").strip()
            
#             if 选择 == "1":
#                 self.配置.打印配置()
#                 input("按回车键继续...")
#             elif 选择 == "2":
#                 self._保存配置()
#                 input("按回车键继续...")
#             elif 选择 == "3":
#                 self._加载配置()
#                 print("配置已重新加载")
#                 input("按回车键继续...")
#             elif 选择 == "0":
#                 pass
#             else:
#                 print("输入无效，直接启动")
#         except KeyboardInterrupt:
#             print("\n直接启动")
    
#     def _保存配置(self):
#         """保存所有配置"""
#         保存所有配置(self.配置)



# # ==================== 入口 ====================

# def main():
#     """主入口"""
#     应用 = 自动化应用()
#     应用.运行()


# if __name__ == "__main__":
#     main()




# """
# 程序入口
# """
# import sys
# import win32event
# import win32api
# import winerror

# # 全局互斥体，防止多开
# 互斥体 = win32event.CreateMutex(None, False, "GameAssistant_SingleInstance_Mutex")
# if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
#     from PySide6.QtWidgets import QMessageBox
#     QMessageBox.warning(None, "提示", "程序已在运行中")
#     sys.exit(0)

# # 原有 import 和启动代码...


# import os
# from pathlib import Path

# # 确保运行目录正确（exe 和开发环境兼容）
# if getattr(sys, 'frozen', False):
#     os.chdir(Path(sys.executable).parent)

# from PySide6.QtWidgets import QApplication
# from core.debug import 加载配置
# from ui.main_window import 主窗口

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     app.setStyle("Fusion")
    
#     加载配置()
    
#     窗口 = 主窗口()
#     窗口.show()
#     sys.exit(app.exec())



#===============================================================

import sys
import win32event
import win32api
import winerror



from PySide6.QtWidgets import (
    QApplication, QSplashScreen, QProgressBar, QLabel, QVBoxLayout, QWidget
)
from PySide6.QtGui import QFont, QColor, QPalette, QLinearGradient, QBrush
from PySide6.QtCore import Qt, QTimer

# 全局互斥体，防止多开
互斥体 = win32event.CreateMutex(None, False, "GameAssistant_SingleInstance_Mutex")
if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
    from PySide6.QtWidgets import QMessageBox
    app = QApplication(sys.argv)          # 先创建
    QMessageBox.warning(None, "提示", "程序已在运行中")
    app.quit()                            # 清理
    sys.exit(0)


app = QApplication(sys.argv)
app.setStyle("Fusion")

# ========== 自定义闪屏 ==========
class 闪屏窗口(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setFixedSize(360, 150)
        
        self.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #1a1a2e, stop:0.4 #16213e, stop:1 #0f3460);
            border-radius: 12px;
        """)
        
        布局 = QVBoxLayout(self)
        布局.setContentsMargins(30, 20, 30, 20)
        布局.setSpacing(10)
        
        标题 = QLabel("游戏助手")
        标题.setFont(QFont("Microsoft YaHei", 20, QFont.Bold))
        标题.setStyleSheet("color: #e0e0e0; background: transparent;")
        标题.setAlignment(Qt.AlignCenter)
        布局.addWidget(标题)
        
        self.副标题 = QLabel("正在载入...")                    # ← 改为 self.
        self.副标题.setFont(QFont("Microsoft YaHei", 10))
        self.副标题.setStyleSheet("color: #a0a0c0; background: transparent;")
        self.副标题.setAlignment(Qt.AlignCenter)
        布局.addWidget(self.副标题)
        
        self.进度条 = QProgressBar()
        self.进度条.setRange(0, 100)
        self.进度条.setValue(0)
        self.进度条.setTextVisible(False)
        self.进度条.setFixedHeight(6)
        self.进度条.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255,255,255,0.1);
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00b4d8, stop:0.5 #0077b6, stop:1 #00b4d8);
                border-radius: 3px;
            }
        """)
        布局.addWidget(self.进度条)
        
        版本 = QLabel("v1.0.0")
        版本.setFont(QFont("Microsoft YaHei", 8))
        版本.setStyleSheet("color: #606080; background: transparent;")
        版本.setAlignment(Qt.AlignCenter)
        布局.addWidget(版本)
    
    def 设置进度(self, value, 文字=None):
        self.进度条.setValue(value)
        if 文字:
            self.副标题.setText(文字)

闪屏 = 闪屏窗口()
闪屏.show()
app.processEvents()

# ========== 模拟载入流程 ==========
def 载入流程():
    步骤列表 = [
        (20, "加载配置..."),
        (40, "初始化任务系统..."),
        (60, "扫描已有窗口..."),
        (80, "构建界面..."),
        (100, "启动完成"),
    ]
    
    for i, (进度, 文字) in enumerate(步骤列表):
        闪屏.设置进度(进度, 文字)
        app.processEvents()
        
        if i == 0:
            from core.debug import 加载配置
            加载配置()
        elif i == 3:
            from ui.main_window import 主窗口
            global 窗口
            窗口 = 主窗口()

    # 载入完成后关闭闪屏，显示主窗口
    闪屏.close()
    窗口.show()

QTimer.singleShot(100, 载入流程)

# ========== 主循环 ==========
sys.exit(app.exec())