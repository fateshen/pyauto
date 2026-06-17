# core/assistant.py
"""
战斗辅助识别器

功能：
1. 血量识别
2. 目标状态识别
3. 无敌倒计时识别

使用方式：
    # 在战斗执行器中初始化
    self.战斗助手 = 战斗辅助识别器(self.线程)
    
    # 获取血量
    目标血量 = self.战斗助手.获取目标血量
    
    # 获取无敌倒计时
    倒计时 = self.战斗助手.获取无敌倒计时()
"""

from pickletools import OpcodeInfo

import numpy as np
import re
from typing import Optional, Tuple, TYPE_CHECKING,List
import random

from rich.repr import T
from core.debug import 调试器
from core.recognition.ocr import OCRResult
from core.utils import 归属情况,匹配分组关键字, 提取次数, 是否为今天, 解析时间文字,读取图片, 重试,解析玩家全名
import time

if TYPE_CHECKING:    
    from models.game_config import 游戏全局配置
    from core.runtime_state import 运行时公共变量
    from core.page_operations import 页面操作集
    from core.action_executor import ActionExecutor
    from core.window_thread import 窗口线程


class 战斗辅助识别器:
    """
    战斗辅助识别器
    
    封装各种战斗相关的识别逻辑，供战斗执行器调用
    不主动导入模块，只依赖传入的参数，避免循环导入
    """
    
    def __init__(self, 线程):
        """
        初始化战斗辅助识别器
        
        参数:
            线程: 窗口线程实例
        """
        self.线程: '窗口线程' = 线程
        self.游戏配置: '游戏全局配置' = 线程.游戏配置
        self.页面: '页面操作集' = 线程.页面
        self.公共变量: '运行时公共变量' = 线程.公共变量
        self.动作执行器:"ActionExecutor"=线程.动作执行器
    
    # ==================== 血量识别 ====================
    
    @property
    def 获取目标血量(self) -> Optional[int]:
        """
        获取当前怪物血量百分比
        
        返回:
            血量百分比（0-100），识别失败返回 None
        """
        截图 = self.线程.截图
        if 截图 is None:
            return None
        
        区域 = self.游戏配置.区域.主界面.目标血条血量区域标签.元组
        if 区域 is None:
            调试器.warning("战斗助手", "血量区域配置为空")
            return None
        
        try:
            结果 = self.线程.文字识别器.recognize_text(截图, 区域)
            if 结果:
                # 提取数字，如 "75%" -> 75
                数字 = re.findall(r'\d+', 结果)
                if 数字:
                    血量 = int(数字[0])
                    血量 = max(0, min(100, 血量))
                    调试器.trace("战斗助手", f"目标血量: {血量}%")
                    return 血量
        except Exception as e:
            调试器.warning("战斗助手", f"血量识别异常: {e}")
        
        return None
    @property
    def 获取玩家血量(self) -> Optional[int]:
        截图 = self.线程.截图
        if 截图 is None:
            return None
        
        区域 = self.游戏配置.区域.主界面.目标血条血量区域标签.元组
        if 区域 is None:
            调试器.warning("战斗助手", "血量区域配置为空")
            return None
        结果=self.线程.像素分析器.count_colors_by_range(截图,self.游戏配置.区域.主界面.玩家血球自定义血条区域标签.元组,"70,255,0,40,0,40|115,140,95,113,95,113")
        if 结果:
            if 结果[0]==0 and 结果[1]==0 :
                调试器.warning("战斗助手", "血量校正像素为0，不能保证结果")
                return None
            return int (结果[0]/839*100)  #像素数量839为估算设置
        return None
    
    def 获取目标类型(self)->str:
       
        目标信息=self.获取区域文字(self.游戏配置.区域.主界面.目标血条下归属区域标签.元组)
        if 匹配分组关键字(目标信息,"归|属"):
            return "怪物"
        return ""
    
    def 古剑类副本归属判定(self):
        """
        判定BOSS归属
        
        返回:
            归属情况.未知 (0)
            归属情况.归属自己 (1)
            归属情况.归属公会 (2)
            归属情况.归属外人 (-1)
        """       
        
        # 1. 确保有玩家名字
        
        玩家名字 = self.获取玩家角色名称()
        if not 玩家名字:
            return 归属情况.未知
    
        # 2. 检查"抢归属"按钮
        抢归属文字 = self.获取区域文字(
            self.游戏配置.区域.古剑.古剑副本抢归属按钮标签.元组
        )
        if not 抢归属文字 or "抢" not in 抢归属文字:
            return 归属情况.未知
        
        # 3. 识别归属文字
        filter_config = {
            "color_range": "20,50,150,255,0,16",
            "keep_color": True,
            "background": "black"
        }
        归属文字 = self.线程.文字识别器.recognize_text(
            self.线程.截图,
            self.游戏配置.区域.古剑.古剑副本归属区域标签.元组,
            filter_config
        )
        if not 归属文字:
            if "抢" in 抢归属文字:
                self.线程.公共变量.任务可能结束时间=time.time()
            return 归属情况.未知
        
        归属信息 = 解析玩家全名(归属文字)
        归属名字 = 归属信息["名字"]
        归属服务器 = 归属信息["服务器号"]
        
        if not 归属名字:
            return 归属情况.未知
        
        调试器.debug("战斗助手", f"归属判定: '{归属文字}' → 名字='{归属名字}' 服务器='{归属服务器}'")
        调试器.debug("战斗助手", f"玩家名字: '{玩家名字}'")

        self.线程.公共变量.任务可能结束时间=0
        # 4. 归属是自己
        if 归属名字 == 玩家名字:
            return 归属情况.归属自己
        
        # 5. 归属是公会成员
        if 归属名字 in self.游戏配置.玩家.公会成员列表:
            return 归属情况.归属公会
        
        # 6. 服务器号在允许范围内 → 视为公会成员（待你实现）
        if self._是否允许的服务器(归属服务器):
            return 归属情况.归属公会
        
        # 7. 外人
        return 归属情况.归属外人
    def _是否允许的服务器(self,归属服务器)->bool:
        if not self.游戏配置.玩家.服务器规则视为队友:
            return False
        if self.游戏配置.玩家.服务器范围低<=0 or self.游戏配置.玩家.服务器范围高<=0:
             return False
        if int( 归属服务器)>=self.游戏配置.玩家.服务器范围低 and  int( 归属服务器)<=self.游戏配置.玩家.服务器范围高:
            return True
        return False
        
    # ==================== 目标状态识别 ====================
    
    def 是否有目标(self, 区域: Tuple[int, int, int, int] = None, 
                    像素规则: str = None,
                    阈值: int = None) -> bool:
        """
        判断当前是否有目标
        
        参数:
            区域: 目标检测区域
            像素规则: 像素匹配规则
            阈值: 像素数量阈值
        
        返回:
            True: 有目标， False: 无目标
        """
        截图 = self.线程.截图
        if 截图 is None:
            return False
        
        if 区域 is None:
            区域 = self.游戏配置.区域.主界面.目标信息显示区域标签.元组            
        
        if 像素规则 is None:
            像素规则 = self.游戏配置.战斗.目标存在像素规则
        
        if 阈值 is None:
            阈值 = self.游戏配置.战斗.检测.目标检测阈值
        
        try:
            结果 = self.线程.像素分析器.count_colors(截图, 区域, 像素规则)
            if len(结果) >= 2:
                有目标 = 结果[0] > 阈值 and 结果[1] > 阈值
            elif len(结果) == 1:
                有目标 = 结果[0] > 阈值
            else:
                有目标 = False
            
            调试器.trace("战斗助手", f"目标检测: 像素结果={结果}, 阈值={阈值}, 有目标={有目标}")
            return 有目标
        except Exception as e:
            调试器.warning("战斗助手", f"目标检测异常: {e}")
        
        return False
    
    # ==================== 无敌倒计时识别 ====================
    
    def 获取无敌倒计时(self, 区域: Tuple[int, int, int, int] = None) -> Optional[int]:
        """
        获取无敌倒计时秒数
        
        参数:
            区域: 无敌文字区域，默认从配置获取
        
        返回:
            倒计时秒数，None表示未识别到
        """
        截图 = self.线程.截图
        if 截图 is None:
            return None
        
        if 区域 is None:
            区域 = self.游戏配置.区域.主界面.保护20秒读秒数字区域标签.元组           
        
        try:
            结果 = self.线程.文字识别器.recognize_text(截图, 区域)
            if 结果:
                # 匹配无敌倒计时格式，如 "无敌 20秒"、"剩余 15s"、"15秒"
                数字 = re.findall(r'\d+', 结果)
                if 数字:
                    倒计时 = int(数字[0])
                    调试器.trace("战斗助手", f"无敌倒计时: {倒计时}秒")
                    return 倒计时
        except Exception as e:
            调试器.warning("战斗助手", f"无敌倒计时识别异常: {e}")
        
        return None
    
    def 获取刷新秒数(self,区域:Tuple[int,int,int,int],filter_config: Optional[dict] = None,刷新关键字规则:Optional[str]=None) ->Optional[int] :
        """获取刷新时间，单位秒"""
        截图 = self.线程.截图
        if 截图 is None:
            截图=self.线程.刷新截图()
        if 截图 is None:
            return None
        if filter_config:             
            结果 = self.线程.文字识别器.recognize_text(
                截图, 区域,filter_config
            )
            # 调试器.trace("战斗助手", "获取刷新秒数: 有像素解析")
        else:             
            结果 = self.线程.文字识别器.recognize_text(
                截图, 区域
            )
            # 调试器.trace("战斗助手", "获取刷新秒数: 无像素解析")
        if not 结果:
            调试器.trace("战斗助手", "获取刷新秒数: 未识别到时间文字")
            return None
        
        # 解析时间数字
        if 刷新关键字规则 is not None and 匹配分组关键字(结果,刷新关键字规则):
            秒数=0
        else:
            秒数 = 解析时间文字(结果)
        调试器.trace("战斗助手", f"获取刷新秒数: 原始='{结果}' -> {秒数}秒")
        return 秒数

    def 获取当前玩家坐标(self) -> Optional[Tuple[int, int]]:
        """
        通过OCR识别小地图获取当前坐标
        
        返回:
            (x, y) 或 None
        """
        截图 = self.线程.截图
        if 截图 is None:
            return None
        
        # 获取小地图坐标显示区域
        坐标区域对象 =self.游戏配置.区域.主界面.小地图坐标显示标签
        if not 坐标区域对象:
            调试器.warning("战斗助手", "位置复查: 未配置小地图坐标显示区域")
            return None
        
        filter_config = {
            "color_diff": "6-180,245,180,245,180,245",
            "keep_color": True,
            "background": "black"
        }
        结果 = self.线程.文字识别器.recognize_text(截图, 坐标区域对象.元组,filter_config)

        调试器.verbose("战斗助手", f"位置复查文字识别内容: {结果}")

        if not 结果:
            return None
        
        # 解析坐标格式如 "123,456" 或 "123, 456" 或 "(123,456)"
        数字 = re.findall(r'\d+', 结果)
        if len(数字) >= 2:
            return (int(数字[0]), int(数字[1]))
        
        return None
    
    
    def 获取自动战斗状态(self) -> int:
        """
        检测当前自动战斗状态
        
        返回:
            0: 自动战斗未开启
            1: 自动战斗中
            -1: 检测失败或按钮不存在
        """
        区域 = self.游戏配置.区域.主界面.自动战斗区域标签
        像素规则 = self.游戏配置.战斗.检测.自动战斗像素规则
        
        if not 区域 or not 像素规则:
            调试器.warning("战斗助手", "未配置状态检测区域或像素规则")
            return -1
        
        截图 = self.线程.截图
        if 截图 is None:
            调试器.debug("战斗助手", "截图为空，无法检测")
            return -1
        
        # 获取三个颜色的像素数量
        结果 = self.线程.像素分析器.count_colors(
            截图, 
            区域.元组, 
            像素规则
        )
        
        if len(结果) < 3:
            调试器.debug("战斗助手", f"像素统计结果不足: {结果}")
            return -1
        
        # c1(0) = 颜色1(F3FFFF)数量
        # c1(1) = 颜色2(E8FFFF)数量  
        # c1(2) = 颜色3(D0D5DA)数量
        颜色1数量 = 结果[0]
        颜色2数量 = 结果[1]
        颜色3数量 = 结果[2]
        
        调试器.trace("战斗助手", f"像素: 开启特征1={颜色1数量}, 开启特征2={颜色2数量}, 按钮标识={颜色3数量}")
        
        # 如果第三个像素数量>0，说明按钮区域有效
        if 颜色3数量 > 0:
            战斗特征和 = 颜色1数量 + 颜色2数量
            if 战斗特征和 > 0:
                调试器.debug("自动战斗", "当前状态: 自动战斗中")
                return 1
            else:
                调试器.debug("自动战斗", "当前状态: 未开启自动战斗")
                return 0
        else:
            调试器.debug("自动战斗", "按钮区域未找到")
            return -1
    def 获取自动走位状态(self) -> int:
        """
        检测当前自动走位状态
        
        返回:
            0: 自动走位未开启
            1: 自动走位中
            -1: 检测失败或按钮不存在
        """
        区域 = self.游戏配置.区域.主界面.自动走位区域标签
        像素规则 = self.游戏配置.战斗.检测.自动走位像素规则
        
        if not 区域 or not 像素规则:
            调试器.warning("战斗助手", "未配置状态检测区域或像素规则")
            return -1
        
        截图 = self.线程.截图
        if 截图 is None:
            调试器.debug("战斗助手", "截图为空，无法检测")
            return -1
        
        # 获取四个颜色的像素数量
        结果 = self.线程.像素分析器.count_colors(
            截图, 
            区域.元组, 
            像素规则
        )
        
        if len(结果) < 4:
            调试器.debug("战斗助手", f"像素统计结果不足: {结果}")
            return -1
        
        颜色1数量 = 结果[0]  # F3FFFF
        颜色2数量 = 结果[1]  # E8FFFF
        颜色3数量 = 结果[2]  # 4C95B6
        颜色4数量 = 结果[3]  # 3F87A9
        
        开启特征和 = 颜色1数量 + 颜色2数量
        按钮特征和 = 颜色3数量 + 颜色4数量
        
        调试器.trace("战斗助手", f"开启特征={开启特征和}, 按钮特征={按钮特征和}")
        
        # 如果特征和 > 0，说明按钮区域有效
        if 按钮特征和 > 0:
            if 开启特征和 > 0:
                调试器.debug("战斗助手", "当前状态: 自动走位中")
                return 1
            else:
                调试器.debug("战斗助手", "当前状态: 未开启自动走位")
                return 0
        else:
            调试器.debug("战斗助手", "按钮区域未找到")
            return -1
    
    def _解析杀手名字(self, 文字: str) -> str:
        """
        从文字中解析杀手名字
        
        格式：
        - "【张三】将你击杀" → "张三"
        - "你被【李四】击杀" → "李四"
        """
        import re
        
        if not 文字:
            return ""
        
        # 匹配【】中的内容
        匹配 = re.search(r'【(.+?)】', 文字)
        if 匹配:
            return 匹配.group(1)
        
        return ""
    def 获取复活面板杀手名字(self) -> str:
        """
        从复活面板提取击杀者名字
        
        返回:
            击杀者名字，提取失败返回空字符串
        """
        复活区域 = self.游戏配置.区域.主界面.复活按钮范围标签
        if not 复活区域:
            return ""        
        截图 = self.线程.截图
        if 截图 is None:
            return ""        
        # 识别复活区域文字
        区域 = 复活区域.元组
        结果 = self.线程.文字识别器.recognize_text(截图, 区域)

        if not 结果:
            return ""
        
        # 提取【】中的名字
        杀手名 = self._解析杀手名字(结果)
        调试器.trace("战斗助手", f"复活面板杀手名: '{杀手名}' (原始文字: '{结果}')")
        return 杀手名
    
    def 获取复活按钮区域(self,safe:bool=True) -> Optional[Tuple[int,int,int,int]]:
        """
        查找复活按钮
        
        返回:
            图片所在区域            
        """
        复活区域 = self.游戏配置.区域.主界面.复活按钮范围标签
        if not 复活区域:
            return None        
        截图 = self.线程.截图
        if 截图 is None:
            return None
        
        # 尝试找图
        复活图片路径 = "安全复活.bmp" if safe else "原地复活.bmp"
        
        模板 = 读取图片(复活图片路径)
        if 模板 is not None:
            区域 = 复活区域.元组
            结果 = self.线程.模板匹配器.match(截图, 模板, threshold=0.8, region=区域)
            if 结果:
                return 结果.rect
                  
        return None
    
    @重试(2,200,True)
    def _识别玩家名字(self) -> str|bool:
        
        截图=self.线程.截图
        if 截图 is None:
            return False
        name1=self.线程.文字识别器.recognize_text(截图,self.游戏配置.区域.主界面.角色名字区域标签.元组)
        time.sleep(0.05)
        截图=self.线程.刷新截图()
        if 截图 is None:
            return False
        name2=self.线程.文字识别器.recognize_text(截图,self.游戏配置.区域.主界面.角色名字区域标签.元组)
        if name1==name2 :
            return name2
        调试器.state("战斗助手","玩家角色名识别出错，名字识别失败")
        return False
    def 获取玩家角色名称(self) -> str:
        """
        获取玩家自身角色名称（从游戏界面OCR识别）
        优先使用缓存在配置中的名称
        
        返回:
            玩家角色名，失败返回空字符串
        """
        # 优先使用缓存
        if self.游戏配置.玩家.玩家角色名称 and 是否为今天(self.游戏配置.玩家.玩家角色名称更新时间):
            return self.游戏配置.玩家.玩家角色名称
        
        截图 = self.线程.截图
        if 截图 is None:
            调试器.info("战斗助手","玩家角色名识别出错，截图为空")
            return ""
        
        if not self.页面.创建_通用点击区域验证图片切换(
                self.游戏配置.区域.主界面.角色状态按钮标签.元组,
                self.游戏配置.区域.主界面.角色面板关闭按钮范围标签.元组,
                "关闭按钮.bmp"
            ).执行():
            调试器.info("战斗助手","玩家角色名识别出错，不能打开角色面板")
            return ""
        if not self.页面.创建_通用点击区域验证文字切换(
                self.游戏配置.区域.主界面.角色面板右侧状态标签.元组,
                self.游戏配置.区域.主界面.角色状态面板职业文字标签.元组,
                "职|业"
            ).执行():
            调试器.info("战斗助手","玩家角色名识别出错，不能切换到职业面板")
            return ""
        name= self._识别玩家名字()
        #注意补上关闭页面操作
        if not self.页面.创建_通用点击图片验证图片切换(
            self.游戏配置.区域.主界面.角色面板关闭按钮范围标签.元组,
            "关闭按钮.bmp",
            self.游戏配置.区域.主界面.角色面板关闭按钮范围标签.元组,
            "关闭按钮.bmp",
            False
             ).执行():
            调试器.info("战斗助手","玩家角色名识别出错，未能正确关闭页面")
        if name and type(name)==str:   
            self.游戏配置.玩家.玩家角色名称 = name
            self.游戏配置.玩家.玩家角色名称更新时间=time.time()
            self.游戏配置.保存到文件()
            return name
        
        调试器.info("战斗助手","玩家角色名识别出错，识别失败")
        return ""
    
     #==================== 查询操作 ====================
    def 查找图片单结果(self, 查询区域:Tuple[int,int,int,int],目标图标路径:str) -> Optional[Tuple[int, int,int, int]]:
        截图 = self.线程.截图
        if 截图 is None: 
            截图= self.线程.刷新截图()
        if 截图 is None: 
            return None
        模板匹配器 = self.线程.模板匹配器
        匹配结果 = 模板匹配器.match_bypicture(
            截图,
            目标图标路径,
            0.8,
            查询区域,
        )
        if 匹配结果: return 匹配结果.rect

        return None
    def 查找图片多结果(self, 搜索区域:Tuple[int,int,int,int],目标图标路径:str) -> List[Tuple[int, int,int, int]]:
        截图 = self.线程.截图
        if 截图 is None: 
            截图= self.线程.刷新截图()
        if 截图 is None: 
            return []
        返回结果=[]
        模板匹配器 = self.线程.模板匹配器
        匹配结果 = 模板匹配器.match_all_bypicture(
            截图,
            目标图标路径,
            0.8,
            搜索区域,
        )
        for 匹配 in 匹配结果: 
            返回结果.append(匹配.rect)
        return 返回结果
    
    #===================获取召唤信息=================
 
    def 获取召唤信息(self) -> Optional[dict]:
        """
        识别召唤窗口，提取召唤玩家名、副本名、层数
        
        返回:
            {"玩家名": "xxx", "副本名": "xxx", "层数": 8, "类型": "协助"}  或 None
        """
        import re
        
        截图 = self.线程.截图
        if 截图 is None:
            return None
        
        召唤区域 = self.游戏配置.区域.主界面.请求协助内容窗口区域
        if not 召唤区域:
            return None
        
        result = self.线程.文字识别器.recognize_result(截图, 召唤区域.元组)
        if not result:
            return None
        
        # 删除空格后合并
        所有文字列表 = result.get_all_texts()
        完整文字 = ''.join(t.replace(' ', '') for t in 所有文字列表)
        调试器.trace("战斗助手", f"召唤窗口文字: '{完整文字}'")
        
        # 筛选：必须包含"协助"或"集结令"
        if '协助' not in 完整文字 and '激活' not in 完整文字 and '集结令' not in 完整文字:
            return None
        
        # 提取玩家名
        玩家名 = ""
        匹配 = re.search(r'请求协助者[：:](.+?)(?:在|发起|集结令)', 完整文字)
        if 匹配:
            玩家名 = 匹配.group(1)
        
        # if not 玩家名:
        #     return None
        
        # 集结令：副本名=当前地图
        if '集结令' in 完整文字:
            return {
                "玩家名": 玩家名,
                "副本名": self.线程.当前地图,
                "层数": None,
                "类型": "集结令"
            }
        
        # 协助：提取副本名（"在"之后"遇见"之前）
        副本名 = ""
        匹配 = re.search(r'在(.+?)遇见', 完整文字)
        if not 匹配:  
            匹配 = re.search(r'(.+?)\s*已激活', 完整文字)
        if 匹配:
            副本名 = 匹配.group(1)

        if not 副本名:            
            return None
        
        # 提取层数
        层数 = None
        层数匹配 = re.search(r'(\d+)层', 副本名)
        if 层数匹配:
            层数 = int(层数匹配.group(1))
        
        调试器.debug("战斗助手", f"召唤信息: 玩家='{玩家名}', 副本='{副本名}', 层数={层数}")
        return {"玩家名": 玩家名, "副本名": 副本名, "层数": 层数, "类型": "协助"}
    
    def 获取当前攻击模式(self) -> str:
        """
        识别当前攻击模式
        
        返回:
            "全体模式" | "和平模式" | "善恶模式" | "盟友模式" | "编组模式" | "行会模式" | ""
        """
        截图 = self.线程.截图
        if 截图 is None:
            return ""
        
        区域 = self.游戏配置.区域.攻击模式.当前攻击模式显示区域标签
        if not 区域:
            return ""
        
        结果 = self.线程.文字识别器.recognize_text(截图, 区域.元组)
        调试器.trace("战斗助手", f"当前攻击模式识别: '{结果}'")
        
        if not 结果:
            return ""
        
        # 匹配模式文字
        模式映射 = {
            "全": "全体模式",
            "平": "和平模式",
            "恶": "善恶模式",
            "友": "盟友模式",
            "组": "编组模式",
            "会": "行会模式",
        }
        
        for 关键字, 模式名 in 模式映射.items():
            if 关键字 in 结果:
                return 模式名
        
        return ""
    
    #======================文字识别辅助==================
    def 区域包含文字(self,文字区域:Tuple[int,int,int,int],文字规则:str,filter_config:Optional[dict]=None) ->bool:
        截图 = self.线程.截图
        if 截图 is None:
            截图=self.线程.刷新截图()
        if 截图 is None:
            return False
        if not 文字区域 or not 文字规则:
            return False
        if filter_config:           
            识别文字=self.线程.文字识别器.recognize_text(截图,文字区域,filter_config)
        else:
            识别文字=self.线程.文字识别器.recognize_text(截图,文字区域)
        
        return  匹配分组关键字(识别文字,文字规则)
    
    def 获取区域文字(self,文字区域:Tuple[int,int,int,int],filter_config:Optional[dict]=None) ->str:
        截图 = self.线程.截图
        if 截图 is None:
            截图=self.线程.刷新截图()
        if 截图 is None:
            return ""
      
        if filter_config:           
            识别文字=self.线程.文字识别器.recognize_text(截图,文字区域,filter_config)
        else:
            识别文字=self.线程.文字识别器.recognize_text(截图,文字区域)
        
        return  识别文字
    def 获取区域文字坐标(self,文字区域:Tuple[int,int,int,int],filter_config:Optional[dict]=None) ->OCRResult|None:
        截图 = self.线程.截图
        if 截图 is None:
            截图=self.线程.刷新截图()
        if 截图 is None:
            return None
      
        if filter_config:           
            识别文字=self.线程.文字识别器.recognize_result(截图,文字区域,filter_config)
        else:
            识别文字=self.线程.文字识别器.recognize_result(截图,文字区域)
        
        return  识别文字
    
    def 区域像素统计(self,区域:Tuple[int,int,int,int],规则:str):
        """
        颜色匹配计数 - 统计区域内符合颜色规则的像素数量
        
        参数:            
            区域: 区域 (left, top, right, bottom)
            规则: 规则字符串，如 "0000ff,0.9|00ff00,0.8"
        
        返回:
            每个规则对应的像素数量列表
        """
        截图 = self.线程.截图
        if 截图 is None:
            截图=self.线程.刷新截图()
        if 截图 is None:
            return []
        return self.线程.像素分析器.count_colors(截图,区域,规则)
        
    def 获取区域次数(self,文字区域:Tuple[int,int,int,int],filter_config:Optional[dict]=None,规则:Optional[str]=None) ->Optional[int]:
        """
        获取区域中的剩余次数
        
        参数:
            区域: 识别区域
            规则: 匹配规则，满足规则才是有效次数            

        返回:
            大于=0的数字: 识别成功，已更新剩余次数
            小于0，识别失败
            None: 识别失败
        """
        文字=self.获取区域文字(文字区域,filter_config)
        if not 文字:
            return None
        if 规则 is not None and not 匹配分组关键字(文字,规则):
            调试器.debug("战斗助手", f"未匹配规则，规则: '{规则}',结果: '{文字}'")
            return None
        数字 = 提取次数(文字)
        if 数字>=0:
            调试器.debug("战斗助手", f"获取次数为0: ,文字: '{文字}'")
            return 数字
        return None
            


    def 更新公会成员列表(self, 是否强制刷新: bool = False) -> bool:
        
        调试器.info("战斗助手", "开始更新公会成员列表")
        
        # 打开公会页面
        if not self.页面.主界面操作.进入行会页面.执行():
            调试器.warning("战斗助手", "无法打开公会页面")
            return False
        
        # 读取公会名称
        公会名称 = self.获取区域文字(
            self.游戏配置.区域.行会.行会页面行会名称区域标签.元组
        )
        if 公会名称:
            self.游戏配置.玩家.玩家公会名称 = 公会名称
        
        # 读取成员数量
        数量文字 = self.获取区域文字(
            self.游戏配置.区域.行会.行会成员数量区域标签.元组
        )
        行会成员数量 = 提取次数(数量文字) if 数量文字 else 0
        
        # 进入成员页面
        if not self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.行会.行会页面右侧成员按钮标签.元组,
            self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
            "成员"
        ).执行():
            # 检查是否没有公会
            if 匹配分组关键字(
                self.获取区域文字(
                    self.游戏配置.区域.行会.行会页面创建行会按钮区域标签.元组
                ), "创|建"
            ):
                self.游戏配置.玩家.公会名单更新时间 = time.time()
                self.游戏配置.保存到文件()
                return True
            return False
        
        所有名字 = []
        连续无新增 = 0
        最大页数 = 50
        
        for 页码 in range(最大页数):
            截图 = self.线程.刷新截图()
            if 截图 is None:
                break
            
            本页成员 = self._识别本页公会成员(截图)
            
            添加前数量 = len(所有名字)
            for 全名 in 本页成员:
                if 全名 not in 所有名字:
                    所有名字.append(全名)
            
            if len(所有名字) == 添加前数量:
                连续无新增 += 1
                if 连续无新增 >= 2:  # 连续2次无新增才停止
                    break
            else:
                连续无新增 = 0
            
            # 拖拽翻页
            拖拽区域 = self.游戏配置.区域.行会.人员名单拖动区域.元组
            self.线程.动作执行器.drag(
                拖拽区域[0], 拖拽区域[3],      # 底部
                拖拽区域[2], 拖拽区域[3] - 280  # 向上拖
            )
            time.sleep(self.游戏配置.默认等待秒)
        
        # 校验数量
        if 行会成员数量 <= 0 or len(所有名字) >= 行会成员数量 * 0.9:
            self.游戏配置.玩家.公会成员列表 = 所有名字
            self.游戏配置.玩家.公会名单更新时间 = time.time()
            self.游戏配置.保存到文件()
            调试器.info("战斗助手", f"公会成员更新完成，共 {len(所有名字)} 人")
            return True
        
        调试器.warning("战斗助手", f"公会成员数量不足: {len(所有名字)}/{行会成员数量}")
        return False
    def _识别本页公会成员(self, 截图) -> List[str]:
        """识别当前页面的公会成员名字"""
        区域 = self.游戏配置.区域.行会.成员页面成员名单区域标签
        if not 区域:
            return []
        
        结果 = self.线程.文字识别器.recognize_result(截图, 区域.元组)
        if not 结果:
            return []
        
        成员列表 = []
        for 文字, _ in 结果.items:
            文字 = 文字.strip()
            # 过滤无效短文本（数字、符号等）
            if len(文字) >= 1 :
                名称信息=解析玩家全名(文字)
                if 名称信息["名字"]:
                  成员列表.append(名称信息["名字"])
        
        调试器.trace("战斗助手", f"本页识别到 {len(成员列表)} 个成员")
        return 成员列表


    def 检查并更新敌人面板(self) -> bool:
        
        当前时间 = time.time()
        
        # 面板已就绪且未到检查时间
        if self.游戏配置.玩家.敌人面板坐标 and self.游戏配置.玩家.敌人面板上次检查时间 > 当前时间:
            return True
        
        # 重置检查时间（10~20分钟后）
        self.游戏配置.玩家.敌人面板上次检查时间 = 当前时间 + random.randint(600, 1200)
        
        调试器.debug("战斗助手", "检查敌人信息面板")
        
        for 尝试次数 in range(3):
            截图 = self.线程.截图
            if 截图 is None:
                continue
            
            面板范围 = self.游戏配置.区域.主界面.敌人面板范围标签
            if not 面板范围:
                break
            
            ocr结果 = self.线程.文字识别器.recognize_result(截图, 面板范围.元组)
            人字坐标 = ocr结果.find("人") if ocr结果 else None
            
            if 人字坐标:
                self.游戏配置.玩家.敌人面板坐标 = (
                    人字坐标[0] + 15,
                    人字坐标[1] + 25,
                    人字坐标[0] + 155,
                    人字坐标[1] + 195,
                )
                调试器.info("战斗助手", f"敌人面板就绪: {self.游戏配置.玩家.敌人面板坐标}")
                return True
            
            # 最后一次不点击
            if 尝试次数 >= 2:
                break
            
            开闭按钮 = self.游戏配置.区域.主界面.敌人面板开闭按钮标签
            if 开闭按钮:
                self.线程.动作执行器.click(开闭按钮.中心点[0], 开闭按钮.中心点[1])
                time.sleep(self.游戏配置.默认等待秒)
                self.线程.刷新截图()
        
        调试器.warning("战斗助手", "敌人面板检查失败")
        self.游戏配置.玩家.敌人面板坐标 = None
        return False
    
    def 敌人面板敌人情况(self)->Optional[OCRResult]:
        面板坐标=self.游戏配置.玩家.敌人面板坐标
        if 面板坐标 is None:
            return None
        return self.获取区域文字坐标(面板坐标)
    
    # def 敌人面板有敌人(self)->Optional[bool]:
    #     敌人文字坐标=self.敌人面板敌人情况()
        
    #     if 敌人文字坐标 is None:
    #         return None
        
    #     if 敌人文字坐标.find("无可攻|击目标"):
    #        if len(敌人文字坐标) ==1:
    #            return False          
    #     return True
    def 敌人面板有敌人(self)->Optional[bool]:
        面板坐标=self.游戏配置.玩家.敌人面板坐标
        if 面板坐标 is None:
            return None
        if self.区域像素统计(面板坐标, "0000FF,0.95"):
            return True
        return False
    
    