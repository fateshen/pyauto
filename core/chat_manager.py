# core/chat_manager.py
"""
聊天管理器

功能：
1. 管理待发送聊天队列（10秒间隔控制）
2. 频道识别与切换
3. 文字输入与发送验证

使用方式：
    # 在窗口线程中初始化
    self.聊天管理器 = 聊天管理器(self)
    
    # 在主循环中调用
    self.聊天管理器.处理发送队列()
    
    # 在任务执行器中添加发送任务
    self.线程.聊天管理器.添加发送任务("行会", "BOSS刷新了")
"""
import time
from typing import Optional, List, Self, Tuple,TYPE_CHECKING
from core.debug import 调试器
from core.utils import 匹配分组关键字, 随机点
if TYPE_CHECKING:    
    from models.game_config import 游戏全局配置
    from models.task_config import 任务配置基类
    from models.task_state import 任务状态基类
    from core.runtime_state import 运行时公共变量
    from core.page_operations import 页面操作集
    from models.dynamic_tags import 动态标签
    from core.window_thread import 窗口线程
    from core.common_operations import 通用操作集
    from core.assistant import 战斗辅助识别器
    from core.action_executor import ActionExecutor
    from core.recognition.ocr import TextRecognizer
    



class 聊天管理器:
    """聊天管理器"""
    
    def __init__(self, 线程):
        """
        初始化聊天管理器
        
        参数:
            线程: 窗口线程实例
        """
        self.线程:'窗口线程' = 线程
        self.动作: 'ActionExecutor' = 线程.动作执行器
        self.文字识别器 : 'TextRecognizer' = 线程.文字识别器
        self.像素分析器 = 线程.像素分析器
        self.公共变量: '运行时公共变量' = 线程.公共变量
        self.游戏配置: '游戏全局配置' = 线程.游戏配置
    
    # ==================== 主入口 ====================
    
    def 处理发送队列(self) -> None:
        """处理待发送聊天队列（主循环中调用）"""
        队列 = self.公共变量.待发送聊天队列
        
        if not 队列:
            return
        
        # 10秒间隔控制
        当前时间 = time.time()
        if 当前时间 - self.公共变量.上次聊天发送时间 < 10:
            return
        
        # 取队首
        待发送 = 队列[0]
        频道 = 待发送.get("频道", "行会")
        内容 = 待发送.get("内容", "")
        
        调试器.debug("聊天", f"处理发送: 频道='{频道}', 内容='{内容[:20]}{'...' if len(内容)>20 else ''}'")
        
        # 1. 确保频道正确
        if not self._切换到频道(频道):
            调试器.warning("聊天", f"切换频道失败: '{频道}'，跳过本次发送")
            return
        
        # 2. 输入并发送
        if self._输入并发送(内容):
            调试器.info("聊天", f"发送成功: '{内容}'")
            self.公共变量.待发送聊天队列.pop(0)
            self.公共变量.上次聊天发送时间 = time.time()
        else:
            调试器.warning("聊天", "发送失败，保留在队列中下次重试")
    
    # ==================== 频道切换 ====================
    
    def _切换到频道(self, 目标频道: str) -> bool:
        """
        切换到目标聊天频道
        
        流程：
        1. 检查当前频道是否已匹配
        2. 点击当前频道按钮展开选项卡
        3. OCR识别选项卡内容
        4. 用匹配规则查找目标频道坐标
        5. 点击目标频道
        6. 复查当前频道文字
        
        返回:
            True: 已在目标频道或切换成功
        """
        # 生成匹配规则：每个字之间插入"|"
        匹配规则 = self._生成频道匹配规则(目标频道)
        备用规则 = "行|会"
        
        调试器.debug("聊天", f"切换频道: 目标='{目标频道}', 规则='{匹配规则}', 备用='{备用规则}'")
        
        # 步骤1: 检查当前频道
        当前频道文字 = self._获取当前频道文字()
        if self._匹配频道(当前频道文字, 匹配规则):
            调试器.debug("聊天", "已在目标频道，无需切换")
            return True
        
        # 步骤2: 点击当前频道按钮展开选项卡
        当前频道区域 = self.游戏配置.区域.聊天.当前频道显示标签
        if not 当前频道区域:
            调试器.warning("聊天", "未配置当前频道显示区域")
            return False
        
        调试器.trace("聊天", "点击当前频道按钮展开选项卡")
        x,y= 当前频道区域.随机点(0.6)
        self.动作.click(x,y)
        time.sleep(self.游戏配置.战斗.默认等待秒)
        
        # 步骤3: 识别频道选项卡
        选项卡区域 = self.游戏配置.区域.聊天.频道选项卡区域标签
        if not 选项卡区域:
            调试器.warning("聊天", "未配置频道选项卡区域")
            return False
        
        截图 = self.线程.刷新截图()
        if 截图 is None:
            调试器.warning("聊天", "截图失败，无法识别频道选项卡")
            return False
        
        ocr_result = self.文字识别器.recognize_result(截图, 选项卡区域.元组)
        if not ocr_result:
            调试器.warning("聊天", "未识别到频道选项卡内容")
            return False
        
        调试器.trace("聊天", f"频道选项卡识别内容: {ocr_result.get_all_text()}")
        
        # 步骤4: 先尝试主规则匹配
        目标坐标 = ocr_result.find(匹配规则, match_type="group")
        
        # 主规则失败，尝试备用规则
        if not 目标坐标:
            调试器.debug("聊天", f"主规则'{匹配规则}'未匹配，尝试备用规则'{备用规则}'")
            目标坐标 = ocr_result.find(备用规则, match_type="group")
            匹配规则 = 备用规则
            if 匹配分组关键字(当前频道文字,备用规则):
                self.线程.页面.创建_通用点击区域验证文字切换(
                    当前频道区域.元组, 
                    选项卡区域.元组,
                    "会|队", 
                    False
                ).执行()
                return True
        
        if not 目标坐标:
            调试器.warning("聊天", f"频道选项卡中未找到'{目标频道}'或备用频道")
            # 点击关闭选项卡
            self.线程.页面.创建_通用点击区域验证文字切换(
                    当前频道区域.元组, 
                    选项卡区域.元组,
                    "会|队", 
                    False
                ).执行()
            return False
        
        # 步骤5: 点击目标频道
        if  self.线程.页面.创建_通用点击区域验证文字切换(
                目标坐标, 
                选项卡区域.元组,
                "会|队", 
                False
            ).执行():
            return True
        
        调试器.warning("聊天", f"切换后复查失败，当前频道文字='{当前频道文字}'")
        return False
    
    def _生成频道匹配规则(self, 频道名: str) -> str:
        """
        生成频道匹配规则：每个字之间插入'|'
        
        示例:
            "行会" → "行|会"
            "世界" → "世|界"
        """
        if not 频道名:
            return ""
        return '|'.join(list(频道名))
    
    def _匹配频道(self, 当前文字: str, 规则: str) -> bool:
        """检查当前频道文字是否匹配规则"""
        if not 当前文字 or not 规则:
            return False
        return 匹配分组关键字(当前文字, 规则)
    
    def _获取当前频道文字(self) -> str:
        """OCR识别当前频道显示文字"""
        截图 = self.线程.截图
        if 截图 is None:
            截图 = self.线程.刷新截图()
        if 截图 is None:
            return ""
        
        区域 = self.游戏配置.区域.聊天.当前频道显示标签
        if not 区域:
            return ""
        
        结果 = self.文字识别器.recognize_text(截图, 区域.元组)
        调试器.trace("聊天", f"当前频道识别: '{结果}'")
        return (结果 or "").strip()
    
    # ==================== 输入与发送 ====================
    
    def _输入并发送(self, 内容: str) -> bool:
        """
        输入文字并发送
        
        流程：
        1. 点击输入区域获取焦点
        2. type_text 输入文字
        3. 验证输入区有文字（3次重试）
        4. 点击发送按钮
        5. 验证输入区文字消失（3次重试）
        
        返回:
            True: 发送成功
        """
        输入区域 = self.游戏配置.区域.聊天.聊天输入区域标签
        发送按钮 = self.游戏配置.区域.聊天.发送按钮标签
        
        if not 输入区域:
            调试器.warning("聊天", "未配置聊天输入区域")
            return False
        if not 发送按钮:
            调试器.warning("聊天", "未配置发送按钮区域")
            return False
        
        # 1. 点击输入区域获取焦点
        调试器.trace("聊天", "点击输入区域获取焦点")
        self.线程.通用操作.点击区域(输入区域.元组,2,0.1)
        
        
        # 2. 输入文字（尝试3次）
        输入成功 = False
        for i in range(3):
            调试器.trace("聊天", f"输入文字 第{i+1}次: '{内容[:30]}{'...' if len(内容)>30 else ''}'")

            self.动作.set_keyboard_mode("后台")
            self.动作.type_text(内容)
            self.动作.set_keyboard_mode("前台")
            time.sleep(0.2)
            
            if self._输入区有文字():
                输入成功 = True
                break
            
            调试器.debug("聊天", f"输入验证失败，重试 {i+1}/3")
            # 重试前清理输入区
            self.线程.通用操作.点击区域(输入区域.元组,2,0.1)
            time.sleep(0.1)
        
        if not 输入成功:
            调试器.warning("聊天", "文字输入失败（3次重试已耗尽）")
            return False
        
        # 3. 点击发送（尝试3次）
        for i in range(3):
            调试器.trace("聊天", f"点击发送按钮 第{i+1}次")
            self.线程.通用操作.点击区域(发送按钮.元组,2,0.1)
            time.sleep(0.3)
            
            # 验证输入区文字消失
            if not self._输入区有文字():
                调试器.debug("聊天", "发送成功，输入区已清空")
                return True
            
            调试器.debug("聊天", f"发送验证失败（输入区仍有文字），重试 {i+1}/3")
        
        调试器.warning("聊天", "发送失败（3次重试已耗尽）")
        return False
    
    def _输入区有文字(self) -> bool:
        """
        检查输入区域是否有文字
        
        通过像素分析判断：纯黑像素占比 < 70% 认为有文字
        
        返回:
            True: 有文字
        """
        截图 = self.线程.刷新截图()
        if 截图 is None:
            return False
        
        区域 = self.游戏配置.区域.聊天.聊天输入区域标签
        if not 区域:
            return False
        
        # 通过像素分析判断输入区是否有文字
        # 有文字时输入区不是纯黑
        结果 = self.文字识别器.recognize_text(截图, 区域.元组)
        
        if 结果 and len(结果) > 0:
            if 匹配分组关键字(结果, "点击输入内容|点击,内容") and len(结果) < 7:
                调试器.debug("聊天", "输入区有文字，但文字内容过短，可能为点击输入内容，忽略")
                return False
            return True
        
        return False
    
    # ==================== 便捷方法 ====================
    
    def 添加发送任务(self, 频道: str, 内容: str):
        """
        添加一条发送任务到队列
        
        参数:
            频道: 目标频道名（如 "行会"、"世界"、"队伍"）
            内容: 要发送的文字内容
        """
        self.公共变量.待发送聊天队列.append({
            "频道": 频道,
            "内容": 内容,
            "添加时间": time.time()
        })
        调试器.debug("聊天", f"添加发送任务: 频道='{频道}', 队列长度={len(self.公共变量.待发送聊天队列)}")
    
    def 清空队列(self):
        """清空待发送队列"""
        self.公共变量.待发送聊天队列.clear()
        调试器.debug("聊天", "清空发送队列")
    
    def 获取队列长度(self) -> int:
        """获取当前队列长度"""
        return len(self.公共变量.待发送聊天队列)