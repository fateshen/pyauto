# tasks/putong.py
"""
普通任务定义
"""


from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from core.debug import 调试器
import time,random,re
from typing import Optional, Any,List,Tuple


@任务定义(
    任务ID="putongrenwu",
    调试模式=True,
    任务名称="普通任务",
    任务类型="普通任务",    
    优先级=1,
    地图关键字="",
    提前进场秒数=0,
    普通任务模式="挂元宝",
    状态_当前阶=0,
    状态_普通本当前层=0,
    状态_普通任务上次换层时间=time.time(),


)
class 普通任务(战斗任务执行器):
    """普通任务执行器"""
    
    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)   
        self.下一次使用道具时间=time.time() +600  


    def 是否在副本中(self) -> bool:
        if self.线程.当前地图 == "盟重省":
            调试器.trace("普通任务", "当前在盟重省，判定不在副本中")
            return False
        
        截图 = self.线程.截图
        if 截图 is None:
            调试器.trace("普通任务", "截图为空，默认判定在副本中(安全策略)")
            return True
        
        区域 = self.游戏配置.区域.主界面.小地图安全危险显示标签
        像素规则 = self.游戏配置.战斗.检测.小地图安全区检查像素规则
        if not 区域 or not 像素规则:
            调试器.warning("普通任务", "安全区检测配置缺失，默认判定在副本中(安全策略)")
            return True
        
        结果 = self.线程.像素分析器.count_colors(
            截图, 
            区域.元组, 
            像素规则
        )
        
        if len(结果) < 2:
            调试器.warning("普通任务", f"安全区像素统计结果异常(期望2种颜色，实际{len(结果)}种)，默认判定在副本中")
            return True
        
        颜色1数量 = 结果[0]
        颜色2数量 = 结果[1]
        调试器.trace("普通任务", f"安全区像素检测: 安全色={颜色1数量}个 危险色={颜色2数量}个")
        
        if 颜色1数量 > 0:
            调试器.debug("普通任务", f"检测到安全区标识(安全色像素={颜色1数量})，判定在安全区")
            return False
        
        if self.线程.获取当前地图任务() is not None:
            调试器.debug("普通任务", f"检测到地图专有任务，判定不在普通副本")
            return False

        调试器.debug("普通任务", f"未检测到安全区标识，判定在副本中")
        return True
    
    
    # ==================== 主执行流程 ====================

    def 不带子任务执行(self) -> str:
        
        return self.执行()
    def 执行(self) -> str:
        """
        执行任务（模板方法）
        
        子类不应重写此方法，而是重写：
        - 是否在副本中()
        - 执行入口逻辑()
        """
        调试器.info("普通任务", f"开始执行: {self.任务配置.任务名称}({self.任务配置.任务ID})")
        调试器.debug("普通任务", f"当前地图: '{self.线程.当前地图}' 剩余次数: {self.任务状态.剩余次数}")

        # 0. 检查召唤响应（副本内外均可）
        if self._检查召唤响应():            
            return "完成"
        
        # 1. 判断是否在副本中
        是否副本 = self.是否在副本中()
        if 是否副本:
            调试器.debug("普通任务", "判定在副本中 → 执行战斗逻辑")
            return self.执行副本战斗逻辑()
        
        # 2. 执行入口逻辑
        调试器.debug("普通任务", "判定不在副本中 → 执行入口逻辑")
        if not self.执行入口逻辑():
            调试器.debug("普通任务", "入口逻辑返回失败")
            return "失败"
        
        
        调试器.state("普通任务", "已进入副本，开始战斗")
        return "进行中"
    
    # ==================== 副本战斗逻辑 ====================
    
    def 执行副本战斗逻辑(self,mode:str="") -> str:
        """执行副本战斗逻辑"""
        调试器.debug("普通任务", "执行战斗逻辑")
        
        截图=self.线程.截图
        
        # 1.1. 检查死亡复活
        if self.检查并处理复活():
            调试器.state("普通任务", "死亡复活处理完成")
            return "进行中"
        
        # 2. 更新战斗状态
        self.更新目标状态()
        self.更新静止状态(截图)
        
        # 3. 打印战斗状态
        self._打印战斗状态()
        self._使用道具()

        # from tasks.reward.合成系列 import 合成系列强化
        # 每日=合成系列强化(self.线程.强化奖励管理器)
        # 每日.执行()

        # self.通用操作._打开背包()
        # time.sleep(0.5)
        # self.通用操作.关闭中间可能存在的窗口()


        # self.领取奖励退出操作()
        
        # # 4. 检查退出条件
        # if self.检查退出条件():
        #     调试器.state("普通任务", "满足退出条件")
        #     self.退出副本()
        #     # self.战斗结束回调()
        #     # self.状态.完成一次()
        #     调试器.info("普通任务", f"任务完成，剩余次数: {self.任务状态.剩余次数}")
        #     return "完成"
        
        # 5. 检查自动战斗
        self.检查调整自动战斗状态()
        self.检查调整自动走位状态()
        self.线程.强化奖励管理器.检查并执行()
        return "进行中"
     
    
    def 执行入口逻辑(self) -> bool:
        """普通任务入口逻辑"""
        调试器.info(self.调试分类, "开始执行普通任务入口逻辑")
        
        # name=self.辅助识别器.获取玩家角色名称()
        # 调试器.info(self.调试分类, f"玩家名称: {name}")
        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            return False
        
        # 2. 根据模式执行
        模式 = self.任务配置.普通任务模式
        
        if 模式 == "精英图鉴":
            return self._精英图鉴入口()
        elif 模式 == "BOSS图鉴":
            return self._BOSS图鉴入口()
        elif 模式 == "挂元宝":
            return self._挂元宝入口()
        
        return False
    def _精英图鉴入口(self) -> bool:
        """精英图鉴入口流程"""
        调试器.info(self.调试分类, "精英图鉴入口")
        
        # 1. 打开图鉴页面（含红点收取）
        if not self._打开图鉴页面():
            return False
        
        # 2. 点击精英按钮
        if not self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.图鉴强化.图鉴页面精英按钮标签.元组,
            self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
            "精英|图鉴"
        ).执行():
            调试器.debug(self.调试分类, "进入精英图鉴页面失败")
            return False
        
        # 3. 点击前往获取 → 进入地图传送页面
        if not self.页面.创建_通用点击文字验证文字切换(
            self.游戏配置.区域.图鉴强化.图鉴页面激活按钮带红点区域标签.元组,
            "前|往",
            self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
            "地图"
        ).执行():
            调试器.debug(self.调试分类, "点击前往获取失败")
            return False
        
        # 4. 地图传送选层进入
        return self._精英图鉴地图传送进入副本()
    def _BOSS图鉴入口(self) -> bool:
        """BOSS图鉴入口流程"""
        调试器.info(self.调试分类, "BOSS图鉴入口")
        
        # 1. 打开图鉴页面（含红点收取）
        if not self._打开图鉴页面():
            return False
        
        # 2. 点击BOSS按钮
        if not self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.图鉴强化.图鉴页面BOSS按钮标签.元组,
            self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
            "BOSS|图鉴"
        ).执行():
            调试器.debug(self.调试分类, "进入BOSS图鉴页面失败")
            return False
        
        # 3. 点击前往获取 → 进入首领页面
        if not self.页面.创建_通用点击文字验证文字切换(
            self.游戏配置.区域.图鉴强化.图鉴页面激活按钮带红点区域标签.元组,
            "前|往",
            self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
            "首领"
        ).执行():
            调试器.debug(self.调试分类, "点击前往获取失败")
            return False
        time.sleep(max(0.5, self.游戏配置.刷新等待秒))
        self.线程.刷新截图()
        # 4. 首领页面选层进入
        return self._BOSS图鉴选层进入()

    def _挂元宝入口(self) -> bool:
        """挂元宝入口流程"""
        调试器.info(self.调试分类, "挂元宝入口")
        
        # 1. 进入首领页面
        if not self.页面.主界面操作.进入首领页面():
            调试器.debug(self.调试分类, "进入首领页面失败")
            return False
        time.sleep(max(0.5, self.游戏配置.刷新等待秒))
        self.线程.刷新截图()
        # 2. 首领页面选层进入
        return self._挂元宝选层进入()
    def _打开图鉴页面(self) -> bool:
        """打开图鉴页面并收取红点收益"""
        # 点击图鉴按钮
        if not self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.主界面.图鉴按钮带红点区域标签.元组,
            self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
            "图"
        ).执行():
            return False
        
        # 收取红点收益
        self._收取图鉴红点收益()
        
        return True


    def _收取图鉴红点收益(self) -> None:
        """依次点击所有红点收益"""
        红点区域 = self.游戏配置.区域.图鉴强化.图鉴页面激活按钮带红点区域标签
        if not 红点区域:
            return
        
        for _ in range(10):  # 最多收10个
            截图 = self.线程.截图
            if 截图 is None:
                break
       
            # 检测红点
            结果 = self.线程.模板匹配器.match_bypicture(
                截图, "红点1.bmp", threshold=0.8, region=红点区域.元组
            )
            if not 结果:
                break
            
            # 点击红点
            self.通用操作.点击区域(结果.rect,缩放比例=0.3)
            time.sleep(self.游戏配置.战斗.默认等待秒)
            self.线程.刷新截图()
            调试器.trace(self.调试分类, "收取一个红点收益")  
    def _挂元宝选层进入(self) -> bool:
        """挂元宝：按阶选择，优先选BOSS>=3的层"""
        调试器.debug(self.调试分类, "挂元宝选层")
        
        截图 = self.线程.刷新截图()
        if 截图 is None:
            return False
        
        # 1. 读取阶数信息
        阶列表 = self._解析首领页面阶数信息(截图)
        if not 阶列表:
            调试器.warning(self.调试分类, "未识别到阶数信息")
            return False
        
        调试器.trace(self.调试分类, f"阶数列表: {[j[0] for j in 阶列表]}")
        
        # 2. 按阶数从小到大尝试，找到>=3只的就进入
        for 阶数, 阶坐标 in 阶列表:
            调试器.trace(self.调试分类, f"尝试第{阶数}阶")
            self.通用操作.点击区域(阶坐标)
            time.sleep(0.3)
            
            截图 = self.线程.刷新截图()
            if 截图 is None:
                continue
            
            层列表 = self._解析首领页面各层信息(截图)
            if not 层列表:
                continue
            
            最大层 = max(层列表, key=lambda x: x[1])
            _层数, 最大只数, _坐标 = 最大层
            
            调试器.trace(self.调试分类, f"第{阶数}阶: 最大{最大只数}只")
            
            if 最大只数 >= 3:
                return self._进入选定层(最大层, 阶数)
        
        # 3. 所有阶都没有>=3只 → 降级处理
        调试器.debug(self.调试分类, "无>=3只的阶，降级处理")
        
        if not 阶列表:
            return False
        
        第一阶数 = 阶列表[0][0]
        
        # 跳过当前阶（与上次相同则选第二阶）
        if self.任务状态.当前阶 == 第一阶数 and len(阶列表) >= 2:
            _阶数, 阶坐标 = 阶列表[1]
            调试器.debug(self.调试分类, f"跳过第{第一阶数}阶，选第{_阶数}阶")
        else:
            _阶数, 阶坐标 = 阶列表[0]
            调试器.debug(self.调试分类, f"选第{_阶数}阶")
        
        # 点击阶
        self.通用操作.点击区域(阶坐标)
        time.sleep(0.3)
        
        截图 = self.线程.刷新截图()
        if 截图 is None:
            return False
        
        层列表 = self._解析首领页面各层信息(截图)
        if not 层列表:
            return False
        
        # 选层
        最大层 = max(层列表, key=lambda x: x[1])
        _层数, 最大只数, 坐标 = 最大层
        
        if 最大只数 > 0:
            调试器.debug(self.调试分类, f"降级选层: 第{_层数}层({最大只数}只)")
            return self._进入选定层(最大层, _阶数)
        else:
            
            随机层 = random.choice(层列表)
            调试器.debug(self.调试分类, f"降级随机选层: 第{随机层[0]}层")
            return self._进入选定层(随机层, _阶数)


    def _BOSS图鉴选层进入(self) -> bool:
        """BOSS图鉴：读取各层信息，选BOSS最多的层进入"""
        调试器.debug(self.调试分类, "BOSS图鉴选层")
        
        截图 = self.线程.刷新截图()
        if 截图 is None:
            return False
        
        层列表 = self._解析首领页面各层信息(截图)
        if not 层列表:
            调试器.warning(self.调试分类, "未识别到层信息")
            return False
        
        # 选最大只数的层
        最大层 = max(层列表, key=lambda x: x[1])
        _层数, 最大只数, 坐标 = 最大层
        
        if 最大只数 > 0:
            调试器.debug(self.调试分类, f"选第{_层数}层({最大只数}只)")
            return self._进入选定层(最大层, 阶数=0)
        else:            
            随机层 = random.choice(层列表)
            调试器.debug(self.调试分类, f"随机选第{随机层[0]}层")
            return self._进入选定层(随机层, 阶数=0)


    def _进入选定层(self, 层信息: Tuple, 阶数: int) -> bool:
        """点击层坐标进入地图传送页面并记录状态"""
        _层数, _只数, 坐标 = 层信息
        
        if not self._点击层坐标并验证进入地图传送(坐标):
            return False
        if not self.点击进入普通副本():  # 进入普通副本
            return False
        self.任务状态.普通本当前层 = _层数
        self.任务状态.当前阶 = 阶数
        调试器.state(self.调试分类, f"进入地图传送: 第{阶数}阶第{_层数}层")
        return True
    
    def _解析首领页面各层信息(self, 截图) -> List[Tuple[int, int, Tuple[int, int, int, int]]]:
        """
        解析首领页面各层信息
        
        输入: [('寒霜长廊1层(1只)', (724, 513, 831, 533)), ...]
        输出: [(层数, 只数, 坐标), ...]
        """
        区域 = self.游戏配置.区域.boss相关.首领页面各层信息显示标签
        if not 区域:
            return []
        
        ocr结果 = self.线程.文字识别器.recognize_result(截图, 区域.元组)
        if not ocr结果:
            return []
        
        层列表 = []
        for 文字, 坐标 in ocr结果.items:
            # 匹配 "X层(Y只)"
            匹配 = re.match(r'.*?(\d+)层\((\d+)只\)', 文字)
            if 匹配:
                层数 = int(匹配.group(1))
                只数 = int(匹配.group(2))
                层列表.append((层数, 只数, 坐标))
        
        return 层列表

    def _解析首领页面阶数信息(self, 截图) -> List[Tuple[int, Tuple[int, int, int, int]]]:
        """
        解析首领页面阶数信息
        
        输入: [('192阶洪荒巨兽', (565, 307, 678, 323)), ...]
        输出: [(阶数, 坐标), ...]  按阶数从小到大排序
        """
        区域 = self.游戏配置.区域.boss相关.首领页面阶数显示标签
        if not 区域:
            return []
        
        ocr结果 = self.线程.文字识别器.recognize_result(截图, 区域.元组)
        if not ocr结果:
            return []
        
        阶列表 = []
        for 文字, 坐标 in ocr结果.items:
            匹配 = re.match(r'(\d+)阶', 文字)
            if 匹配:
                阶数 = int(匹配.group(1))
                阶列表.append((阶数, 坐标))
        
        # 按阶数从小到大排序
        阶列表.sort(key=lambda x: x[0])
        return 阶列表

    def _点击层坐标并验证进入地图传送(self, 坐标: Tuple[int, int, int, int]) -> bool:
        """点击层坐标，验证是否进入地图传送页面"""
        return self.页面.创建_通用点击区域验证文字切换(
            坐标,
            self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
            "地图传"
        ).执行()   
    #=========================================================
    def _精英图鉴地图传送进入副本(self) -> bool:
        """
        精英图鉴：在地图传送页面选层并进入副本
        
        层数在1~3循环，每层停留不超过15分钟
        """
        调试器.debug(self.调试分类, "精英图鉴地图传送选层")
        
        # 1. 确定目标层
        目标层 = self._计算精英图鉴目标层()
        调试器.debug(self.调试分类, f"目标层: {目标层}")
        
        # 2. 读取可选层信息
        截图 = self.线程.刷新截图()
        if 截图 is None:
            return False
        
        层文字结果 = self.线程.文字识别器.recognize_result(
            截图,
            self.游戏配置.区域.boss相关.地图传送选层位置.元组
        )
        if not 层文字结果:
            调试器.warning(self.调试分类, "未识别到地图传送选层信息")
            return False
        
        # 分离粘连文字
        from core.recognition import 分离粘连文字
        层文字结果 = 分离粘连文字(层文字结果)
        
        # 3. 找到目标层坐标
        目标层坐标 = 层文字结果.find(str(目标层), match_type="contains")
        if not 目标层坐标:
            调试器.warning(self.调试分类, f"未找到第{目标层}层")
            return False
        
        # 4. 点击选层 → 点击进入地图
        for _ in range(3):
            self.通用操作.点击区域(目标层坐标)
            time.sleep(0.1)
            
            if self.点击进入普通副本():
                if not self.任务状态.普通本当前层 == 目标层:
                    self.任务状态.普通本当前层 = 目标层
                    self.任务状态.普通任务上次换层时间 = time.time()
                调试器.state(self.调试分类, f"成功进入第{目标层}层")
                return True
        
        return False


    def _计算精英图鉴目标层(self) -> int:
        """
        计算精英图鉴目标层（1~3循环，每层15分钟）
        """
        当前层 = self.任务状态.普通本当前层
        上次换层 = self.任务状态.普通任务上次换层时间
        
        # 首次进入
        if 当前层 <= 0:
            return 1
        
        # 超过15分钟 → 换层
        if time.time() - 上次换层 > 900:
            下一层 = 当前层 + 1
            return 下一层 if 下一层 <= 3 else 1
        
        # 未超时 → 保持当前层
        return 当前层


    def 点击进入普通副本(self) -> bool:
        """点击进入地图按钮并验证"""
        return self.页面.创建_通用点击区域验证文字切换(
            self.游戏配置.区域.boss相关.地图传送进入地图按钮标签.元组,
            self.游戏配置.区域.主界面.中间页面名称区域标签.元组,
            "地图传",
            False,
        ).执行()
    
    def _使用道具(self):
        调试器.debug(self.调试分类, "使用道具")
        if self.下一次使用道具时间 < time.time():
            self.下一次使用道具时间 = time.time()+random.uniform(1800, 6000)
            for _  in range(5):
                if self.辅助识别器.区域包含文字(self.游戏配置.区域.日常强化.使用道具小卡使用按钮标签1.元组,"使|用"):
                    self.通用操作.点击区域(self.游戏配置.区域.日常强化.使用道具小卡使用按钮标签1.元组,缩放比例=0.5)
                    time.sleep(self.游戏配置.默认等待秒)
                    self.线程.刷新截图()
                else:
                    break
            for _  in range(5):
                文字信息=self.辅助识别器.获取区域文字(self.游戏配置.区域.日常强化.使用道具小卡道具名称标签.元组)
                if 文字信息=="":
                    break
                else:
                    if "元" in 文字信息:
                        self.通用操作.点击区域(self.游戏配置.区域.日常强化.使用道具小卡关闭按钮标签.元组)
                        time.sleep(self.游戏配置.默认等待秒)
                        self.线程.刷新截图()
                    else:
                        self.通用操作.点击区域(self.游戏配置.区域.日常强化.使用道具小卡使用按钮标签.元组,缩放比例=0.5)
                        time.sleep(self.游戏配置.默认等待秒)
                        self.线程.刷新截图()
