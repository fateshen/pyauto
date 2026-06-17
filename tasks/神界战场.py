# tasks/shenjiezhanchang.py
"""
神界战场任务定义
"""

from tasks.base import 任务定义
from core.task_executors.battle_executor import 战斗任务执行器
from core.page_operations import 页面操作集
from typing import Optional, Tuple, List
from core.utils import 匹配分组关键字, 解析时间文字,提取次数
from core.debug import 调试器
import time
from core.recognition import OCRResult
from pydantic import Field


@任务定义(
    任务ID="shenjiezhanchang",
    任务名称="神界战场",
    调试模式=True,
    任务类型="每日任务",
    优先级=10,
    地图关键字="神界战场|界,战场",
    启用位置复查=True,
    位置复查目标半径=10,
    避让模式使用全局设置=True,
    回城回血使用全局设置=True,
    怪物有无敌=True,
    工作时间开始=10,
    提前进场秒数=15,
    子任务队列="1,2,3,4,5,6",
    次优先级任务队列="2,3",
    每日更新任务数量=3,
    次优先级任务开始时间=22,
    状态_子任务刷新情况=Field(default_factory=dict),
    状态_下次任务队列检查时间=0,
    状态_子任务避让时间=Field(default_factory=dict),
    状态_当前子任务ID="",
    状态_移动开始时间=0,
)
class 神界战场任务(战斗任务执行器):
    """神界战场任务执行器"""

    def __init__(self, 线程, 任务配置, 任务状态):
        super().__init__(线程, 任务配置, 任务状态)
        self.页面 = 页面操作集(线程)
        self.怪物名字关键字 = {
            "1": "钟|东皇|鼎|神农",
            "2": "轩|辕|印|崆峒",
            "3": "昆仑|镜|斧|盘古",
            "4": "女娲|石|炼妖|壶",
            "5": "昊天|塔|葫芦|炽",
            "6": "伏|琴|佛|心圣",
        }
        self.BOSS坐标 = {
            "1": (28, 26),
            "2": (84, 31),
            "3": (52, 47),
            "4": (43, 85),
            "5": (88, 79),
            "6": (24, 54),
        }

    # ==================== 入口逻辑 ====================

    def 执行入口逻辑(self) -> bool:
        """执行神界战场入口逻辑"""
        调试器.info(self.调试分类, "开始执行入口逻辑")

        # 1. 检查剩余次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, f"今日次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
            return False

        if not self.页面.主界面操作.展开右上角任务帘:
            调试器.debug(self.调试分类, "展开右上角任务帘失败")
            return False

        if not self.页面.大千世界.进入大千世界页面():
            调试器.debug(self.调试分类, "进入大千世界页面失败")
            return False

        if not self.页面.大千世界.神界页面.进入神界页面():
            调试器.debug(self.调试分类, "进入神界页面失败")
            return False

        # 等待刷新时间，强制等待服务器时间同步
        time.sleep(max(0.5, self.游戏配置.刷新等待秒))
        self.线程.刷新截图()

        # 3. 更新剩余次数
        调试器.debug(self.调试分类, "步骤2: 读取神界战场次数")
        filter_config = {
            "color_range": "110,255,0,16,0,16|20,50,150,255,0,16",
            "keep_color": False,
            "background": "black",
        }
        if not self.更新区域任务次数(
            self.游戏配置.区域.神界战场.神界战场剩余神元区域标签.元组,
            filter_config,
            "剩|余|神元",
        ):
            调试器.warning(self.调试分类, "读取神界战场次数失败，入口逻辑中断")
            return False
        调试器.debug(self.调试分类, f"剩余次数: {self.任务状态.剩余次数}")

        # 4. 再次检查次数
        if self.任务状态.剩余次数 <= 0:
            调试器.state(self.调试分类, "读取次数后确认为0，次数已用完")
            return False

        # 5. 核查子任务队列
        if len(self.当前子任务队列) == 0:
            调试器.debug(self.调试分类, "当前子任务队列为空，更新子任务队列")
            if len(self.任务配置.子任务队列) == 0:
                调试器.debug(self.调试分类, "子任务队列为空，使用默认子任务队列")
                self.任务配置.子任务队列 = "1,2,3,4,5,6"
            self.当前子任务队列 = [
                int(x.strip()) for x in self.任务配置.子任务队列.split(',') if x.strip()
            ]

        # 6. 检查刷新时间
        self._识别全部刷新时间("神界战场页面刷新时间标签")
        self._合并避让时间到刷新情况()

        需要处理的任务 = self.获取已刷新任务列表()
        调试器.debug(self.调试分类, f"需要处理的任务: {需要处理的任务}")
        if not 需要处理的任务:
            调试器.debug(self.调试分类, "无已刷新任务")
            self.更新下一次刷新时间()
            return False

        # 7. 点击进入秘境
        调试器.debug(self.调试分类, "步骤5: 点击进入神界战场副本")
        if not self.页面.大千世界.神界页面.进入神界战场副本():
            调试器.error(self.调试分类, "点击挑战按钮失败，入口逻辑中断")
            return False

        调试器.state(self.调试分类, "入口逻辑执行成功，已进入神界战场副本")
        return True

    # ==================== 副本内钩子 ====================

    def _副本内检查钩子(self) -> Optional[str]:
        截图 = self.线程.截图
        if 截图 is None:
            截图= self.线程.刷新截图()
        if 截图 is None:
            return None
        filter_config = {               
                "color_diff": "5-80,255,80,255,80,255",
                "keep_color": True,
                "background": "black"
            }
        副本内剩余能量文字=self.线程.文字识别器.recognize_text(截图,self.游戏配置.区域.神界战场.神界战场副本剩余神元区域标签.元组,filter_config)
        if 匹配分组关键字(副本内剩余能量文字, f"/"):
            文字=副本内剩余能量文字.split("/")[0]
            调试器.debug(self.调试分类, f"副本内检查钩子: 读取神界战场副本剩余体力值{文字}")
            if len(文字) == 1:
                次数=提取次数(文字)
                self.任务状态.剩余次数=次数                
                调试器.debug(self.调试分类, f"剩余次数: {次数}")
                if self.任务状态.剩余次数 <= 0:                    
                    调试器.state(self.调试分类, f"剩余次数已用完(剩余{self.任务状态.剩余次数})，跳过执行")
                    self.退出副本()
                    return "任务完成"                    
        return None

    # ==================== 位置复查（覆盖基类） ====================

    def _检查位置复查(self) -> Optional[str]:
        """
        检查并调整角色位置到当前子任务boss坐标

        返回:
            None: 已在范围内，不需要复查
            "移动中": 正在移动或已触发移动
            "无新任务，退出副本": 没有可处理的子任务
        """
        self._合成页面神装确认专属神器()
        if not self.任务配置.启用位置复查:
            return None

        # ========== 1. 确定当前子任务 ==========
        if self.任务状态.当前子任务ID == "":
            需要处理的任务 = self.获取已刷新任务列表()
            if 需要处理的任务:
                self.任务状态.当前子任务ID = str(需要处理的任务[0])
                调试器.debug(self.调试分类, f"设置当前子任务ID: {self.任务状态.当前子任务ID}")
            else:
                调试器.trace(self.调试分类, "位置复查: 无已刷新任务，退出副本")
                self.退出副本()
                return "无新任务，退出副本"

        子任务ID = self.任务状态.当前子任务ID

        # ========== 2. 获取boss坐标 ==========
        boss坐标 = self._获取boss坐标(子任务ID)
        if boss坐标 is None:
            调试器.warning(self.调试分类, f"位置复查: 未找到子任务{子任务ID}的boss坐标")
            return None

        目标x, 目标y = boss坐标

        # ========== 3. 获取当前坐标 ==========
        当前坐标 = self.辅助识别器.获取当前玩家坐标()
        if 当前坐标 is None:
            调试器.debug(self.调试分类, "位置复查: 无法获取当前坐标")
            return None

        当前x, 当前y = 当前坐标
        距离 = ((当前x - 目标x) ** 2 + (当前y - 目标y) ** 2) ** 0.5

        # ========== 4. 判断是否在范围内 ==========
        if 距离 <= self.任务配置.位置复查目标半径:
            调试器.trace(
                self.调试分类,
                f"位置复查: 已在范围内(距离{距离:.0f}≤{self.任务配置.位置复查目标半径})",
            )
            self.任务状态.移动开始时间 = 0.0
            self.任务状态.位置复查次数 = 0
            return None

        # ========== 5. 检查是否多次走位失败 ==========
        if self.任务状态.位置复查次数 >= 3:
            调试器.debug(
                self.调试分类,
                f"boss{子任务ID}位置复查: 已达最大次数3，刷新时间后延，避让",
            )
            self.任务状态.子任务刷新情况[子任务ID] = (
                time.time() + self.任务配置.避让冷却秒数
            )
            return "多次走位不到位避让"

        # ========== 6. 不在范围内，判断是否需要移动 ==========
        静止时长 = self.公共变量.获取静止时长()
        移动已耗时 = (
            time.time() - self.任务状态.移动开始时间
            if self.任务状态.移动开始时间 > 0
            else 0
        )
        需要移动 = False

        # 移动超时保护
        if self.任务状态.移动开始时间 > 0 and 移动已耗时 > 20:
            调试器.warning(
                self.调试分类,
                f"位置复查: 移动超时({移动已耗时:.0f}秒>20秒)，重新移动",
            )
            self.任务状态.移动开始时间 = 0.0
            self.任务状态.位置复查次数 += 1
            需要移动 = True

        # 画面静止 → 卡住了或到达了但识别不准，重新移动
        if 静止时长 > self.静止超时秒数:
            调试器.state(
                self.调试分类,
                f"位置复查: 画面静止{静止时长:.1f}秒，移动到({目标x},{目标y})",
            )
            需要移动 = True

        if 需要移动:
            self._神界战场小地图识别移动检查()

        # 画面还在变化 → 正在移动中
        调试器.trace(
            self.调试分类,
            f"位置复查: 移动中(静止{静止时长:.1f}秒，距离{距离:.0f}，已耗时{移动已耗时:.0f}秒)",
        )

        return "移动中"

    def _获取boss坐标(self, 子任务ID: str) -> Optional[Tuple[int, int]]:
        """获取指定子任务的boss坐标"""
        boss坐标字典 = self.BOSS坐标
        if not boss坐标字典:
            return None

        坐标 = boss坐标字典.get(子任务ID)
        if not 坐标 or len(坐标) < 2:
            return None

        return (坐标[0], 坐标[1])

    def _神界战场小地图识别移动检查(self) -> None:
        """打开大地图，识别刷新时间，点击目标BOSS位置移动"""

        # 1. 打开大地图
        if not self.通用操作.打开大地图():
            调试器.debug(self.调试分类, "未打开中间地图")
            return

        # 2. 识别副本内刷新时间
        self._识别全部刷新时间("神界战场副本刷新时间标签")
        self._合并避让时间到刷新情况()

        需要处理的任务 = self.获取已刷新任务列表()
        调试器.debug(self.调试分类, f"副本内识别刷新时间:需要处理的任务: {需要处理的任务}")
        if not 需要处理的任务:
            调试器.debug(self.调试分类, "副本内识别刷新时间:无已刷新任务")
            self.更新下一次刷新时间()
            self.通用操作.关闭大地图()
            self.退出副本()
            return

        子任务ID = str(需要处理的任务[0])
        self.任务状态.当前子任务ID = 子任务ID

        移动目标区域 = getattr(
            self.游戏配置.区域.神界战场,
            f"神界战场副本地图BOSS位置标签{子任务ID}",
            None,
        )

        if 移动目标区域 is None:
            调试器.warning(self.调试分类, f"位置复查: 未找到子任务{子任务ID}的移动目标区域")
            self.通用操作.关闭大地图()
            return

        # 3. 点击目标坐标
        self.通用操作.点击区域(移动目标区域.元组, 3, 0.08)

        # 4. 记录移动开始时间
        self.任务状态.移动开始时间 = time.time()

        # 5. 关闭地图
        if not self.通用操作.关闭中间可能存在的窗口():
            调试器.debug(self.调试分类, "未关闭中间地图")

    # ==================== 刷新时间识别（公共方法） ====================

    def _识别全部刷新时间(self, 区域前缀: str) -> None:
        """
        循环识别6个BOSS的刷新时间，更新子任务刷新情况

        参数:
            区域前缀: 区域配置的属性名前缀
                      入口逻辑用 "神界战场页面刷新时间标签"
                      副本内用 "神界战场副本刷新时间标签"
        """
        for i in range(6):
            index = i + 1
            属性名 = f"{区域前缀}{index}"
            区域对象 = getattr(self.游戏配置.区域.神界战场, 属性名, None)
            if 区域对象 is None:
                调试器.warning(self.调试分类, f"未找到区域配置: 神界战场.{属性名}")
                continue
            区域坐标 = 区域对象.元组
            秒数 = self.辅助识别器.获取刷新秒数(区域坐标, None, "刷|新")
            if 秒数 is not None and 秒数 >= 0:
                调试器.debug(self.调试分类, f"刷新时间[{index}]: {秒数}秒")
                self.任务状态.子任务刷新情况[str(index)] =time.time() + 秒数

    # ==================== 合成页面 ====================

    def _合成页面神装确认专属神器(self) -> bool:
        """检查合成页面专属神器，更新子任务队列"""

        # 还没到检查时间，跳过
        if time.time() < self.任务状态.下次任务队列检查时间:
            调试器.trace(self.调试分类, "下次任务队列检查时间未到")
            return True

        if not self.页面.主界面操作.进入合成页面("神,装", "神|剑"):
            调试器.error(self.调试分类, "进入合成页面失败")
            return False

        截图 = self.线程.截图
        if 截图 is None:
            return False

        ocr_result = self.线程.文字识别器.recognize_result(
            截图, self.游戏配置.区域.合成.合成中分类卡区域标签.元组
        )
        if not ocr_result:
            return False

        专属神器文字区域 = ocr_result.find("专属|神器")
        if not 专属神器文字区域:
            调试器.debug(self.调试分类, "未识别到专属神器")
            return False

        for i in range(2):
            self.通用操作.点击区域(专属神器文字区域)
            time.sleep(self.游戏配置.战斗.默认等待秒)
            截图 = self.线程.刷新截图()
            if 截图 is None:
                continue

            ocr_result = self.线程.文字识别器.recognize_result(
                截图, self.游戏配置.区域.合成.合成中分类卡区域标签.元组
            )

            识别到的神器列表 = []
            for key, value in self.怪物名字关键字.items():
                if ocr_result.find(value):
                    调试器.debug(self.调试分类, f"已识别到专属神器: {key}")
                    识别到的神器列表.append(key)

            if not 识别到的神器列表:
                continue

            子任务队列字符串 = ",".join(识别到的神器列表)
            调试器.debug(self.调试分类, f"识别到专属神器：{子任务队列字符串}")

            if self.任务配置.子任务队列 != 子任务队列字符串:
                self.任务配置.子任务队列 = 子任务队列字符串
                self.当前子任务队列 = [
                    int(x.strip()) for x in 子任务队列字符串.split(',') if x.strip()
                ]
                # 直接设置当前子任务ID为队列第一个
                if self.当前子任务队列:
                    self.任务状态.当前子任务ID = str(self.当前子任务队列[0])
                调试器.debug(self.调试分类, f"更新子任务队列: {self.当前子任务队列}，当前子任务ID: {self.任务状态.当前子任务ID}")
                try:
                    任务定义.导出配置到JSON(self.线程.窗口名称,线程=self.线程)
                    调试器.info(
                        self.调试分类,
                        f"[保存配置] 任务配置已保存 -> config/{self.线程.窗口名称}/tasks_config.json",
                    )
                except Exception as e:
                    调试器.error(self.调试分类, f"[保存配置] 保存任务配置失败: {e}")

            self.任务状态.下次任务队列检查时间 = time.time() + 1200
            return True

        return False

    # ==================== 避让策略（覆盖基类） ====================

    def _策略_避让高战(self) -> bool:
        策略生效 = super()._策略_避让高战()
        if 策略生效:
            调试器.debug(self.调试分类, "已启用避让高战策略")
            子任务 = self.任务状态.当前子任务ID
            if 子任务 != "":
                调试器.debug(self.调试分类, f"当前子任务高战避让: {子任务}")
                self.任务状态.子任务避让时间[子任务] = self.任务状态.子任务刷新情况[子任务]
        return 策略生效

    def _策略_高频死亡避让(self) -> bool:
        策略生效 = super()._策略_高频死亡避让()
        if 策略生效:
            调试器.debug(self.调试分类, "已启用高频死亡避让策略")
            子任务 = self.任务状态.当前子任务ID
            if 子任务 != "":
                调试器.debug(self.调试分类, f"当前子任务高频死亡避让: {子任务}")
                self.任务状态.子任务避让时间[子任务] = self.任务状态.子任务刷新情况[子任务]
        return 策略生效

    def _合并避让时间到刷新情况(self) -> None:
        """
        将子任务避让时间合并到子任务刷新情况

        规则：
        - 如果避让时间中存在同名key且值更大，则采用避让时间
        """
        刷新情况 = self.任务状态.子任务刷新情况
        避让时间 = self.任务状态.子任务避让时间

        if not 避让时间:
            return

        for 队列号, 避让值 in 避让时间.items():
            if 队列号 in 刷新情况:
                if 避让值 > 刷新情况[队列号]:
                    调试器.trace(
                        self.调试分类,
                        f"子任务{队列号}: 避让时间({避让值}) > 刷新时间({刷新情况[队列号]})，采用避让时间",
                    )
                    刷新情况[队列号] = 避让值