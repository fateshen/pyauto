# core/common_operations.py
"""
通用操作集

职责：
- 全局通用的基础操作，不验证页面切换
- 任何游戏页面下都可以执行
- 操作简单直接（1-3步），返回 bool

与页面操作集的区别：
- 页面操作集：点击 + 验证切换 + 重试，依赖页面层级
- 通用操作集：只管执行，不管结果验证
"""
import time
import random
from typing import List,Tuple, Optional,TYPE_CHECKING
from core.debug import 调试器
from core.task_executors.registry import 任务执行器注册表
from core.utils import 随机点,匹配分组关键字
if TYPE_CHECKING:    
    from models.game_config import 游戏全局配置
    from core.page_operations import 页面操作集
    from core.action_executor import ActionExecutor
    from core.window_thread import 窗口线程

class 通用操作集:
    """
    全局通用操作集合
    
    使用方式：
        # 在窗口线程中初始化
        self.通用操作 = 通用操作集(self)
        
        # 在任务执行器中调用
        self.线程.通用操作.回城()
        self.线程.通用操作.打开地图移动到((400, 300))
    """
    
    def __init__(self, 线程):
        """
        初始化通用操作集
        
        参数:
            线程: 窗口线程实例
        """
        self.线程:'窗口线程' = 线程
        self.动作执行器 : 'ActionExecutor' = 线程.动作执行器
        self.页面: '页面操作集' = 线程.页面
        self.游戏配置: '游戏全局配置' = 线程.游戏配置       
    
    # ==================== 地图移动 ====================
    
    def 打开大地图(self) -> bool:
        """
        打开大地图        
        
        """
        调试器.trace("通用操作", "打开大地图")
        if self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.主界面.小地图敌人显示标签.元组,
            self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
            "小地|地图"
        ).执行():
            调试器.state("战斗助手", "打开中间地图成功")
            return True
        
        调试器.debug("战斗助手", "未打开中间地图")
        return False
    
    def 关闭大地图(self) -> bool:
        """
        关闭大地图
        """
        调试器.trace("通用操作", "关闭大地图")
        if self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.主界面.小地图敌人显示标签.元组,
            self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
            "小地|地图",
            False,
            True
        ).执行():
            调试器.state("战斗助手", "关闭中间地图成功")
            return True
        
        调试器.debug("战斗助手", "未关闭中间地图")
        return False   
    
    def 打开地图移动到(self, 目标区域: Tuple[int,int,int, int], 关闭地图: bool = True) -> bool:
        """
        完整的"打开地图 → 点击 → 关闭地图"流程
        
        参数:
            目标坐标: (x, y)
            关闭地图: 移动后是否关闭地图
        
        返回:
            True: 操作完成
        """
        调试器.debug("通用操作", f"打开地图移动到 ({目标区域})")
        
        # 1. 打开大地图
        if not self.打开大地图() :
            调试器.debug("战斗助手", "未打开中间地图")
            return False      
        
        time.sleep(self.游戏配置.战斗.等待.默认等待秒)
        # 2. 点击目标坐标
        self.点击区域(目标区域,2,0.1)    
        self.点击区域(目标区域,2,0.1)
        self.点击区域(目标区域,2,0.1)        
        
        # 3. 关闭地图
        if 关闭地图:
           if not self.关闭大地图(): 
               调试器.debug("战斗助手", "未关闭中间地图")          
        
        return True
    
    # ==================== 点击回城退出等 ====================
    def 点击退出按钮(self) -> bool:
        截图=self.线程.截图
        if 截图 is None: return False 
        退出按钮区域=self.游戏配置.退出按钮区域.元组
        关键色点数量=self.线程.像素分析器.count_colors(截图,退出按钮区域,"B4F2F9,0.98")
        if 关键色点数量 and  关键色点数量[0]>3:
            调试器.state("战斗助手", "点击退出按钮")
            x,y=self.游戏配置.退出按钮区域.随机点(0.6)
            self.线程.动作执行器.click(x,y)
            return True
        调试器.debug("战斗助手", "未找到退出按钮")
        return False
    def 点击回城石(self) -> bool:
        回城石区域=self.线程.辅助识别器.查找图片单结果(self.游戏配置.区域.主界面.下方技能按钮总区域标签.元组,"回城石.bmp")
        if not 回城石区域: 
            调试器.debug("战斗助手", "未找到回城石")
            return False               
        if self.页面.创建_通用点击区域验证文字切换(
            回城石区域,
            self.游戏配置.区域.主界面.小地图地图名显示标签.元组,
            "盟重省",            
            按键="right"
        ).执行():
            调试器.state("战斗助手", "点击回城石")
            return True
        self.点击区域(回城石区域,2,0.1)        
        调试器.debug("战斗助手", "双击回城石点")
        return True
        
    def 按副本类型退出(self) -> bool:
        if 匹配分组关键字(self.线程.当前地图,"魔神禁|群星试|会试"): 
            time.sleep(0.3)
            if not self.页面.创建点击文字操作(
                self.游戏配置.区域.主界面.魔神禁地退出确认区域标签.元组,
                "确",
                False,
                0.5
            ).执行():
                调试器.state("战斗助手", "按副本类型退出，未查询到退出确认按钮")
                return False
            调试器.state("战斗助手", "按副本类型退出，点击退出确认按钮")
            return True
        return False
        
    # ==================== 鼠标操作 ====================
    #     
    def 覆盖鼠标提示到边缘(self):
        
        随机整数 = random.randint(1, 2)
        if 随机整数==1:
            x,y=self.游戏配置.区域.主界面.角色状态按钮标签.随机点(0.8) 
        else :  
            x,y=self.游戏配置.区域.攻击模式.当前攻击模式显示区域标签.随机点(0.8)        
        self.动作执行器.move(x,y)
        调试器.debug("战斗助手", f"鼠标提示: 移动到X={x}, 移动到Y={y}")
    
    def 点击坐标(self, 坐标: Tuple[int, int], 次数: int = 1, 间隙: float = 0.05,button:str="left") -> bool:
        """
        点击指定坐标
        
        参数:
            坐标: (x, y)
            次数: 连续点击次数，>2时实际次数为2到次数之间的随机值
            间隙: 每次点击间隔秒数
        """
        import random
        
        if 次数 > 2:
            实际次数 = random.randint(2, 次数)
            调试器.trace("通用操作", f"点击 ({坐标[0]}, {坐标[1]}) ×{实际次数}(随机{2}-{次数})")
        else:
            实际次数 = 次数
            调试器.trace("通用操作", f"点击 ({坐标[0]}, {坐标[1]}) ×{实际次数}")
        
        for _ in range(实际次数):
            self.动作执行器.click(坐标[0], 坐标[1],button)
            if 实际次数 > 1 and 间隙 > 0:
                time.sleep(间隙)
        return True

    def 点击区域(self, 区域: Tuple[int,int,int,int], 次数: int = 1, 间隙: float = 0.05,button:str="left",缩放比例:float=1) -> bool:
        调试器.trace("通用操作", f"点击区域 {区域}")
        坐标=随机点(区域,缩放比例)
        return self.点击坐标(坐标, 次数, 间隙,button) 
       
    # ===================== 领取奖励退出操作 =====================
    def 领取奖励退出操作(self) -> bool:
        """
        任务完成时，界面有领取奖励等标识时，领取奖励并退出
        
        返回:
            True: 领取成功
            False: 无需领取或领取失败
        """
        截图 = self.线程.截图
        if 截图 is None:
            截图= self.线程.刷新截图()
        if 截图 is None:
            return False
        结果 = self.线程.文字识别器.recognize_result(
            截图, self.游戏配置.区域.主界面.任务结束确定领取奖励区域标签.元组
        ) .find("领取|退出|确","group")
        if 结果:    
            self.页面.创建点击区域操作(结果,0.5).执行()
            调试器.state("通用操作", "领取奖励退出操作完成")
            self.线程.刷新截图()
            return True
        return False
    
    
    def 关闭中间可能存在的窗口(self):
        """
        清理中间可能存在的窗口（如任务失败时）
        
        操作：
        1. 领取奖励退出（关闭可能的奖励弹窗）
        2. 按 ESC 多次关闭可能的弹窗
        3. 刷新截图
        4. 移动鼠标到不遮蔽区域
        """
        调试器.debug("通用操作", "执行中间窗口清理")
        截图=self.线程.截图
        if 截图 is None: 
            截图= self.线程.刷新截图()
        if 截图 is None: return

        for i in range(6):  
            关闭按钮集合=self.线程.模板匹配器.match_all_bypicture(
                截图,
                "关闭按钮.bmp",
                0.8,            
                self.游戏配置.区域.主界面.关闭按钮搜寻区域标签.元组,           
            )
            if not 关闭按钮集合:
                调试器.verbose("通用操作", "未找到关闭按钮")  
                return
            for 关闭按钮 in 关闭按钮集合:
                point=随机点(关闭按钮.rect)
                self.点击坐标(point, 1, 0.05)
                time.sleep(self.线程.游戏配置.战斗.等待.默认等待秒)
            截图=self.线程.刷新截图()
            if 截图 is None: return
        

    def 清理页面状态(self):
        """
        清理页面状态（入口失败半程时调用）
        
        操作：
        1. 领取奖励退出（关闭可能的奖励弹窗）
        2. 按 ESC 多次关闭可能的弹窗
        3. 刷新截图
        4. 移动鼠标到不遮蔽区域
        """
        调试器.debug("通用操作", "执行页面清理")
        self.领取奖励退出操作()
        self.关闭中间可能存在的窗口()
        
        调试器.debug("通用操作", "页面清理完成")

    def 随机等待(self, 最小秒数: float, 最大秒数: float) -> None:
        """
        随机等待
        
        参数:
            最小秒数: 最小等待秒数
            最大秒数: 最大等待秒数
        """
        等待秒数 = random.uniform(最小秒数, 最大秒数)        
        调试器.debug("通用操作", f"随机等待 {等待秒数:.2f} 秒")
        time.sleep(等待秒数)
    #======================= 背包操作 ======================
    def _打开背包(self,打开仓库:bool=False)->Optional[Tuple[int, int, int, int]]:
        """
        打开背包
        
        参数:
            打开仓库: 是否打开仓库
        返回:
            成功: 仓库图标区域
            失败: None
        """
        仓库图标 = None
        for _ in range(2):
            self.线程.通用操作.点击区域(self.游戏配置.区域.主界面.背包按钮区域标签.元组)
            time.sleep(self.游戏配置.默认等待秒)
            截图 = self.线程.刷新截图()
            if 截图 is None: continue
            仓库图标 = self.线程.模板匹配器.match_bypicture(
                截图, "背包仓库图标.bmp", threshold=0.8
            )
            if 仓库图标:
                break
        仓库图标区域=()
        # 2. 调整位置
        for i in range(3):
            if not 仓库图标:
                break            
            x, y = 仓库图标.left, 仓库图标.top            
            if x < 936 or y > 559:
                仓库图标区域=仓库图标.rect
                break   
            if i >= 2:                
                break         
            self.线程.通用操作.点击区域(仓库图标.rect, 2)
            time.sleep(self.游戏配置.默认等待秒)
            截图 = self.线程.刷新截图()
            if 截图 is None: continue
            仓库图标 = self.线程.模板匹配器.match_bypicture(
                截图, "背包仓库图标.bmp", threshold=0.8
            )
        if not 仓库图标区域:  
            return
        if not 打开仓库:
            self._关闭仓库(仓库图标区域)
        return 仓库图标区域
    
    def _关闭仓库(self,仓库图标区域:Tuple[int, int, int, int]):
        """
        关闭仓库
        """
        仓库关闭按钮区域=仓库图标区域[0]-125,166,仓库图标区域[0],410

        if self.页面.创建点击图片操作(
            仓库关闭按钮区域,
            "关闭按钮.bmp",           
        ).执行():
            return True
        return False
     
    def _生成背包格子区域(self,仓库图标区域: Tuple[int, int, int, int]) -> List[Tuple[int, int, int, int]]:
        """
        根据仓库图标位置生成48个背包格子区域
        
        参数:
            仓库图标区域: (左, 上, 右, 下)
        
        返回:
            48个格子区域列表 [(左, 上, 右, 下), ...]
        """
        图标X = (仓库图标区域[0] + 仓库图标区域[2]) // 2
        图标Y = (仓库图标区域[1] + 仓库图标区域[3]) // 2
        
        # 第一个格子的左上角（图标左移11, 上移415）
        基准X = 图标X -7
        基准Y = 图标Y - 415
        
        格子大小 = 64
        格子列表 = []
        
        for 行 in range(6):
            for 列 in range(8):
                左 = 基准X + 列 * 格子大小
                上 = 基准Y + 行 * 格子大小
                格子列表.append((左, 上, 左 + 格子大小, 上 + 格子大小))
        
        return 格子列表
    
    def _生成背包翻页标签区域(self,仓库图标区域: Tuple[int, int, int, int]) -> List[Tuple[int, int, int, int]]:
        """
        根据仓库图标位置生成7个翻页标签区域
        
        参数:
            仓库图标区域: (左, 上, 右, 下)
        
        返回:
            7个翻页标签区域列表 [(左, 上, 右, 下), ...]
        """
        基准X = 仓库图标区域[0] + 530
        基准Y = 仓库图标区域[1] - 364
        
        标签宽 = 26   # 1420 - 1394
        标签高 = 35   # 298 - 263
        Y偏移 = 52
        
        标签列表 = []
        
        for i in range(7):
            左 = 基准X
            上 = 基准Y + i * Y偏移
            标签列表.append((左, 上, 左 + 标签宽, 上 + 标签高))
        
        return 标签列表

    def 查找目标所在格子(self, 目标区域: Tuple[int, int, int, int], 
                      背包格子列表: list) -> Tuple[Optional[Tuple[int, int, int, int]], Optional[int]]:
        """
        查找目标区域所在的背包格子
        
        返回:
            (格子rect, 格子序号)，未找到返回 (None, None)
        """
        目标左, 目标上, 目标右, 目标下 = 目标区域
        
        for i, 格子 in enumerate(背包格子列表):
            格左, 格上, 格右, 格下 = 格子
            if 格左 <= 目标左 and 格上 <= 目标上 and 目标右 <= 格右 and 目标下 <= 格下:
                return 格子, i

        # 目标左, 目标上, 目标右, 目标下 = 目标区域
        # count=len(背包格子列表)
        # for i in range(count):
        #     格左, 格上, 格右, 格下 = 背包格子列表[i]
        #     if 格左 <= 目标左 and 格上 <= 目标上 and 目标右 <= 格右 and 目标下 <= 格下:
        #         return 背包格子列表[i],i
        
        # # return None,None
        return None, None
   