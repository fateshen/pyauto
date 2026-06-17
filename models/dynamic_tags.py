# models/dynamic_tags.py
"""
动态标签 - 自动从坐标池中匹配

使用方式：
    # 在窗口线程中创建（传入线程的区域配置）
    self.动态标签 = 动态标签(self, self.游戏配置.区域)
    
    # 然后直接使用
    坐标 = self.线程.动态标签.页面A.页面进入标签.元组
"""
import time
from typing import Optional, List, Tuple, Dict, Any
from pydantic import BaseModel, Field
from models.region_config import 区域坐标, 区域配置
from core.debug import 调试器


class 待匹配标签:
    """待匹配标签 - 需要从坐标池中匹配的标签"""
    
    def __init__(self, 名称: str, 期望文字: str):
        self.名称 = 名称
        self.期望文字 = 期望文字
        self._坐标: Optional[区域坐标] = 区域坐标(-1, -1, -1, -1)
        self._已匹配 = False
        self._父页面 = None
    
    def _触发匹配(self):
        """触发匹配（由父页面调用）"""
        if self._已匹配:
            return True
        if self._父页面:
            return self._父页面._匹配所有标签()
        return False
    
    @property
    def 坐标(self) -> 区域坐标:
        if not self._已匹配:
            self._触发匹配()
        return self._坐标
    
    @坐标.setter
    def 坐标(self, 值: 区域坐标):
        self._坐标 = 值
        self._已匹配 = True
    
    @property
    def 是否有效(self) -> bool:
        return self._坐标.是否有效 if self._坐标 else False
    
    @property
    def 元组(self) -> Tuple[int, int, int, int]:
        return self.坐标.元组
    
    @property
    def 中心点(self) -> Tuple[int, int]:
        return self.坐标.中心点
    
    @property
    def 左(self) -> int:
        return self.坐标.左
    
    @property
    def 右(self) -> int:
        return self.坐标.右
    
    @property
    def 上(self) -> int:
        return self.坐标.上
    
    @property
    def 下(self) -> int:
        return self.坐标.下
    
    def __repr__(self) -> str:
        if self._已匹配:
            return f"待匹配标签({self.名称}, 已匹配={self._坐标})"
        return f"待匹配标签({self.名称}, 未匹配)"

from core.utils import 匹配分组关键字, 随机点
class 页面动态标签:
    """页面动态标签 - 管理一个页面的所有标签"""
    
    def __init__(self, 线程, 坐标池: List[区域坐标]):
        """
        初始化页面动态标签
        
        参数:
            页面名称: 页面名称
            线程: 窗口线程
            坐标池: 该页面的坐标池列表
        """
        self.页面名称 = self.__class__.__name__ 
        self._线程 = 线程
        self._坐标池 = 坐标池  # 直接传入坐标池，不再动态获取
        self._已匹配 = False
        self._匹配结果: Dict[str, 区域坐标] = {}
        
        # 调用子类实现的创建标签方法
        self._创建标签()
        
        # 设置父页面引用
        for 标签 in self.获取所有标签():
            标签._父页面 = self
    
    def _创建标签(self):
        """子类重写：创建具体标签"""
        raise NotImplementedError
    
    def 获取所有标签(self) -> List[待匹配标签]:
        """子类重写：返回所有标签列表"""
        raise NotImplementedError
    
    def _匹配所有标签(self) -> bool:
        """批量匹配所有标签"""
        
        if self._已匹配:
            return True
        
        调试器.info("动态标签", f"开始匹配页面: {self.页面名称}")
        
        if not self._坐标池:
            调试器.warning("动态标签", f"页面 '{self.页面名称}' 坐标池为空")
            return False
        
        # 刷新截图
        截图 = self._线程.刷新截图()
        if 截图 is None:
            调试器.error("动态标签", f"页面 '{self.页面名称}' 截图失败")
            return False     
        
        # 对每个坐标池位置进行文字识别
        识别结果 = []
        for i, 坐标 in enumerate(self._坐标池):
            if 坐标.是否有效:
                文字 = self._线程.文字识别器.recognize_text(截图, 坐标.元组,{
                                                            "color_range": "73,253,68,235,60,208|50,135,35,120,30,100",
                                                            "keep_color": True,
                                                            "background": "black"
                                                        }                                                   
                                                   )
                识别结果.append({
                    "索引": i,
                    "坐标": 坐标,
                    "文字": 文字,
                    "元组": 坐标.元组  
                })
                调试器.trace("动态标签", f"  坐标{i+1}: {坐标.元组} -> '{文字}'")
        
         # 将识别结果匹配到标签（使用元组去重）
        已分配元组 = set()  
        未分配元组 = set(结果项["元组"] for 结果项 in 识别结果)
        for 标签 in self.获取所有标签():
            for 结果项 in 识别结果:
                if 结果项["元组"] in 已分配元组: 
                    continue
                if 匹配分组关键字(结果项["文字"], 标签.期望文字):
                    标签.坐标 = 结果项["坐标"]
                    已分配元组.add(结果项["元组"])  
                    未分配元组.discard(结果项["元组"])
                    self._匹配结果[标签.名称] = 结果项["坐标"]
                    调试器.debug("动态标签", f"  匹配成功: {标签.名称} -> {结果项['坐标'].元组}")
                    break
        
        # 二次匹配：处理未分配的坐标
        if 未分配元组:
            调试器.debug("动态标签", f"二次匹配: 处理未分配的坐标 {未分配元组}")
            
            # 重新识别未分配的坐标（使用更宽松的识别参数或不同的识别方式）
            for 元组坐标 in 未分配元组:
                # 找到对应的坐标对象
                对应坐标 = None
                for 结果项 in 识别结果:
                    if 结果项["元组"] == 元组坐标:
                        对应坐标 = 结果项["坐标"]
                        break
                
                if not 对应坐标:
                    continue
                x,y=随机点(对应坐标.元组,0.5)
                self._线程.动作执行器.click(x,y)
                time.sleep(self._线程.游戏配置.战斗.等待.默认等待秒*2)
                截图 = self._线程.刷新截图()
                # 重新识别该坐标（可以尝试不同的识别参数）
                文字 = self._线程.文字识别器.recognize_text(截图, 对应坐标.元组)
                if len(文字) == 0:  
                    文字 = self._线程.文字识别器.recognize_text(截图, self._线程.游戏配置.区域.主界面.中间页面名称区域标签.元组)
                调试器.trace("动态标签", f"  二次识别坐标 {元组坐标}: '{文字}'")
                
                # 尝试匹配尚未匹配的标签
                for 标签 in self.获取所有标签():
                    if 标签._已匹配:  # 跳过已匹配的标签
                        continue
                    if 匹配分组关键字(文字, 标签.期望文字):
                        标签.坐标 = 对应坐标
                        已分配元组.add(元组坐标)
                        self._匹配结果[标签.名称] = 对应坐标
                        调试器.state("动态标签", f"  二次匹配成功: {标签.名称} -> {对应坐标.元组}")
                        break

        self._已匹配 = True
        
        调试器.info("动态标签", f"页面 {self.页面名称} 匹配完成")
        # 循环结束后，打印未匹配的坐标
        if 未分配元组:
            调试器.warning("动态标签", f"  未匹配的坐标: {未分配元组} ({len(未分配元组)}个)")
        else:
            调试器.debug("动态标签", "  所有坐标均已匹配")
        return True
    
    def 重置(self):
        """重置匹配状态"""
        self._已匹配 = False
        self._匹配结果.clear()
        for 标签 in self.获取所有标签():
            标签._坐标 = 区域坐标(-1, -1, -1, -1)
            标签._已匹配 = False
        调试器.debug("动态标签", f"页面 {self.页面名称} 已重置")

class 首领页面右侧标签(页面动态标签):
    """首领页面右侧标签"""
    
    def _创建标签(self):
        """创建所有标签属性"""
        self.首领 = 待匹配标签("首领", "首|领")
        self.专属 = 待匹配标签("专属", "专|属")
        self.兽神 = 待匹配标签("兽神", "兽|神")
        self.降魔 = 待匹配标签("降魔", "降|魔|隆")
        self.天关 = 待匹配标签("天关", "天|关")
    
    def 获取所有标签(self) -> List[待匹配标签]:
        """返回所有标签列表"""
        return [
            self.首领,
            self.专属,
            self.兽神,
            self.降魔,
            self.天关,
        ]
class 合成页面右侧标签(页面动态标签):
    """首领页面右侧标签"""
    
    def _创建标签(self):
        """创建所有标签属性"""
        self.合成 = 待匹配标签("合成", "成")
        self.分解 = 待匹配标签("分解", "分|解")
        self.锻造 = 待匹配标签("锻造", "锻|造")
        self.熔炼 = 待匹配标签("熔炼", "熔|炼")
        self.融合 = 待匹配标签("融合", "融")
    
    def 获取所有标签(self) -> List[待匹配标签]:
        """返回所有标签列表"""
        return [
            self.合成,
            self.分解,
            self.锻造,
            self.熔炼,
            self.融合,
        ]

class 图鉴页面右侧标签(页面动态标签):
    """图鉴页面右侧标签"""
    
    def _创建标签(self):
        """创建所有标签属性"""
        self.图鉴 = 待匹配标签("图鉴", "图|鉴")
        self.兵魂 = 待匹配标签("兵魂", "兵|魂")
        self.铭文 = 待匹配标签("铭文", "铭|文")
        self.投保 = 待匹配标签("投保", "投|保")
        self.炼化 = 待匹配标签("炼化", "炼|化")
    
    def 获取所有标签(self) -> List[待匹配标签]:
        """返回所有标签列表"""
        return [
            self.图鉴,
            self.兵魂,
            self.铭文,
            self.投保,
            self.炼化,
        ]
class 跨服战场页面右侧标签(页面动态标签):
    """跨服战场页面右侧标签"""
    
    def _创建标签(self):
        """创建所有标签属性"""
        self.战场 = 待匹配标签("战场", "战|场")
        self.组队 = 待匹配标签("组队", "组|队")
        self.坐骑 = 待匹配标签("坐骑", "坐|骑")
        self.古剑 = 待匹配标签("古剑", "古|剑|克")
        self.陨圣 = 待匹配标签("陨圣", "陨|圣")
    
    def 获取所有标签(self) -> List[待匹配标签]:
        """返回所有标签列表"""
        return [
            self.战场,
            self.组队,
            self.坐骑,
            self.古剑,
            self.陨圣,
        ]
    
class 神界页面右侧标签(页面动态标签):
    """跨服战场页面右侧标签"""
    
    def _创建标签(self):
        """创建所有标签属性"""
        self.神界 = 待匹配标签("神界", "神|界")
        self.专属 = 待匹配标签("专属", "专|属")
        self.秘境 = 待匹配标签("秘境", "秘|境")
        self.百宝 = 待匹配标签("百宝", "百|宝")
        
    
    def 获取所有标签(self) -> List[待匹配标签]:
        """返回所有标签列表"""
        return [
            self.神界,
            self.专属,
            self.秘境,
            self.百宝
        ]
    
class 强星页面右侧标签(页面动态标签):
    """跨服战场页面右侧标签"""
    
    def _创建标签(self):
        """创建所有标签属性"""
        self.强星 = 待匹配标签("强星", "强|星")
        self.涅槃 = 待匹配标签("涅槃", "涅|繁|槃")
        self.传世 = 待匹配标签("传世", "传|世")
        self.暗殿 = 待匹配标签("暗殿", "暗|殿")
        
    
    def 获取所有标签(self) -> List[待匹配标签]:
        """返回所有标签列表"""
        return [
            self.强星,
            self.涅槃,
            self.传世,
            self.暗殿
        ]
    

class 光翼页面右侧标签(页面动态标签):
    """光翼页面右侧标签"""
    
    def _创建标签(self):
        """创建所有标签属性"""
        self.光翼 = 待匹配标签("光翼", "光|翼")
        self.神兵 = 待匹配标签("神兵", "神|兵")
        self.幻装 = 待匹配标签("幻装", "幻|装")
        self.觉醒 = 待匹配标签("觉醒", "觉|醒")
        self.星辰 = 待匹配标签("星辰", "星|辰")
    
    def 获取所有标签(self) -> List[待匹配标签]:
        """返回所有标签列表"""
        return [
            self.光翼,
            self.神兵,
            self.幻装,
            self.觉醒,
            self.星辰,
            ]
        
class 动态标签:
    """
    动态标签根类 - 管理所有页面
    
    使用方式：
        # 在窗口线程中创建（传入线程和区域配置）
        self.动态标签 = 动态标签(self, self.游戏配置.区域)
        
        # 然后直接使用
        坐标 = self.线程.动态标签.页面A.页面进入标签.元组
    """
    
    def __init__(self, 线程, 区域配置: 区域配置):
        """
        初始化动态标签
        
        参数:
            线程: 窗口线程实例
            区域配置: 线程持有的区域配置实例（单例）
        """
        self._线程 =线程
        self._区域配置 = 区域配置  # ✅ 保存线程的区域配置引用
        
        # 创建各页面动态标签（直接传入坐标池）
        self.首领页面右侧标签 = 首领页面右侧标签(            
           线程, 
            self._区域配置.首领合成页面右侧标签坐标池.获取所有位置()
        )
        self.合成页面右侧标签 = 合成页面右侧标签(            
           线程, 
            self._区域配置.首领合成页面右侧标签坐标池.获取所有位置()
        )
        self.跨服战场页面右侧标签 = 跨服战场页面右侧标签(            
           线程, 
            self._区域配置.战场光翼图鉴页面右侧坐标池.获取所有位置()
        )

        self.神界页面右侧标签 = 神界页面右侧标签(            
           线程, 
            self._区域配置.神界战灵坐骑古剑页面右侧坐标池.获取所有位置()
        )
        self.图鉴页面右侧标签 = 图鉴页面右侧标签(            
           线程, 
            self._区域配置.战场光翼图鉴页面右侧坐标池.获取所有位置()
        )
        self.强星页面右侧标签 = 强星页面右侧标签(            
           线程, 
            self._区域配置.强星页面右侧坐标池.获取所有位置()
        )
        self.光翼页面右侧标签 = 光翼页面右侧标签(            
           线程, 
            self._区域配置.战场光翼图鉴页面右侧坐标池.获取所有位置()
        )
       
    def 重置页面(self, 页面名称: str):
        """重置指定页面的匹配状态"""
        页面 = getattr(self, 页面名称, None)
        if 页面:
            页面.重置()
    
    def 重置所有(self):
        """重置所有页面"""
        self.首领页面右侧标签.重置()
        self.跨服战场页面右侧标签.重置()