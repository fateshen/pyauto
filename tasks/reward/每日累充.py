# tasks/reward/huodong.py

from core.recognition import OCRResult
from core.utils import 是否为今天, 缩放区域,匹配分组关键字,是否有重叠,提取次数
from typing import List, Tuple,Dict,Optional
from tasks.reward.base import 强化奖励任务基类
from core.debug import 调试器
import time,random
def 计算红包分配(红包列表: List[Dict], 目标金额: int, 最大超出: int = 10) -> Optional[List[Dict]]:
    """
    计算红包分配，优先使用面额种类最少、超出最小的方案。
    """
    if not 红包列表:
        return None
    
    排序列表 = sorted(红包列表, key=lambda x: x["金额"])
    
    最佳方案 = None
    最佳种类数 = float('inf')
    最佳超出 = float('inf')
    
    def 搜索(idx, 当前总额, 已选):
        nonlocal 最佳方案, 最佳种类数, 最佳超出
        
        if 当前总额 >= 目标金额:
            超出 = 当前总额 - 目标金额
            if 超出 > 最大超出:
                return
            种类数 = len(set(i for i, _ in 已选))
            if 种类数 < 最佳种类数 or (种类数 == 最佳种类数 and 超出 < 最佳超出):
                最佳种类数 = 种类数
                最佳超出 = 超出
                最佳方案 = 已选.copy()
            return
        
        if idx >= len(排序列表):
            return
        
        红包 = 排序列表[idx]
        # 最多用多少个（不超过数量，不无限加）
        最大可用 = min(红包["数量"], (目标金额 - 当前总额) // 红包["金额"] + 1)
        
        for cnt in range(最大可用, -1, -1):
            if cnt > 0:
                已选.append((idx, cnt))
            搜索(idx + 1, 当前总额 + cnt * 红包["金额"], 已选)
            if cnt > 0:
                已选.pop()
    
    搜索(0, 0, [])
    
    if 最佳方案 is None:
        return None
    
    结果 = []
    for idx, cnt in 最佳方案:
        if cnt > 0:
            结果.append({
                "金额": 排序列表[idx]["金额"],
                "使用数量": cnt,
                "图标区域": 排序列表[idx]["图标区域"],
                "格子序号": 排序列表[idx]["格子序号"],
                "数量": 排序列表[idx]["数量"],
            })
    
    return 结果
def 打印分配结果(分配列表, 目标金额: int):
    """打印红包分配结果"""
    if not 分配列表:
        print(f"目标 {目标金额} 元 → 无法分配（超出超过限制或无可用红包）")
        return
    
    总额 = sum(项["金额"] * 项["使用数量"] for 项 in 分配列表)
    超出 = 总额 - 目标金额
    
    print(f"目标 {目标金额} 元 → 实际 {总额} 元（超出 {超出} 元）")
    
    # 按金额从大到小排列
    for 项 in sorted(分配列表, key=lambda x: x["金额"], reverse=True):
        print(f"  {项['金额']:>4}元 x {项['使用数量']:>2} = {项['金额'] * 项['使用数量']:>5}元  (格子 {项['格子序号']})")
    
    print(f"  {'─' * 12}")
    print(f"  合计: {总额} 元  (超出 {超出} 元)")

class 每日累充(强化奖励任务基类):
    任务ID = "meirileichong"
    任务名称 = "每日累充"  
    是否启用: bool = True  
    最小间隔秒 = 3000
    最大间隔秒 = 6000
    在盟重省执行: bool = True
    启用每日累充: bool = True
    每日累充金额="168"
    每周充值天数="7"
    今日已充值金额=0
    本周已充值天数=0
    上次充值时间=0
    上次读取每周充值天数时间= 0
    任务类型: str = "每日任务"


    
    def 执行(self) -> bool:
        调试器.debug("强化奖励", "每日累充: 开始检查")               
        if not self.页面.创建_通用点击图片验证文字切换(
            self.配置.区域.主界面.第一排任务区域标签.元组,
            "活动图标.bmp",
             self.配置.区域.主界面.中间页面名称区域标签.元组,
             "开服|活动",
        ).执行():
            return False
        #=========这里面写开服活动相关，暂时空缺待补充
        self._每日累充()
       
        #####奖励领取完成，同时充值满足要求，设置 self.上次确定任务结束时间 = time.time()
        self.通用操作.关闭中间可能存在的窗口()        
        return True
    
    def _每日累充(self):
        if 是否为今天(self.上次确定任务结束时间): 
            调试器.debug("强化奖励", "每日累充: 检查到今日充值已满额度")
            return
        if not self._检查是否要充值(): return
        调试器.debug("强化奖励", "每日累充: 启动")
        左侧菜单=self.辅助识别器.获取区域文字坐标(self.配置.区域.合成.合成左分类卡区域标签.元组)
        if 左侧菜单 is  None:    return
        每日累充按钮区域=左侧菜单.find("每日累|每日,充")
        if 每日累充按钮区域 is not None: 
            self._领取每日累充奖励(每日累充按钮区域)
        连充按钮区域=左侧菜单.find("连充豪")  
        if 连充按钮区域 is  None: return
        if self.页面.创建_通用点击区域验证文字切换(
                连充按钮区域,
                self.配置.区域.各种活动.连充豪礼页面已充值金额区域.元组,
                "今日|累充"
            ) .执行():
            self._读取本周已充值天数()
            self._领取连充奖励()

            if self.本周已充值天数>=int(self.每周充值天数): return
            金额=self.辅助识别器.获取区域次数(self.配置.区域.各种活动.连充豪礼页面已充值金额区域.元组,None,"元")
            if 金额 is None:
                return
            self.今日已充值金额=金额
            每日累充金额=int(self.每日累充金额)
            需要充值金额=每日累充金额-金额
            if 需要充值金额<=0:
                调试器.debug("强化奖励", "每日累充: 今日已充值金额 >= 每日累充金额")
                self.上次确定任务结束时间 = time.time()
                self.管理器.保存配置()
                return
            self.通用操作.关闭中间可能存在的窗口()
            定位坐标=self.通用操作._打开背包()
            if 定位坐标 is None:
                调试器.debug("强化奖励", "每日累充: 打开背包失败")
                return True
            格子坐标集合=self.通用操作._生成背包格子区域(定位坐标)                          
            分页按钮标签=self.通用操作._生成背包翻页标签区域(定位坐标)
            整理按钮区域=定位坐标[0]+324,定位坐标[1]-4,定位坐标[0]+390,定位坐标[1]+14
            self.通用操作.点击区域(整理按钮区域)            
            背包区域=定位坐标[0]+11,定位坐标[1]-400,定位坐标[0]+523,定位坐标[1]-16            
            图片集合=("1元图标.bmp", "5元图标.bmp", "10元图标.bmp", "50元图标.bmp","100元图标.bmp", 
                       
               )
          
            for 分页标签 in 分页按钮标签:
                self.通用操作.点击区域(分页标签,2,缩放比例=0.5)
                time.sleep(self.配置.默认等待秒*3)
                截图=self.页面.线程.刷新截图()
                if 截图 is None:continue
                找寻结果=self.页面.线程.模板匹配器.match_multiple_bypictures(截图, 图片集合,0.7,背包区域)
                if not 找寻结果:                    
                    continue
                红包位置=self.获取红包数据(背包区域,格子坐标集合)                
                if 红包位置: 
                    分配结果= 计算红包分配(红包位置, 需要充值金额)
                    打印分配结果(分配结果, 需要充值金额)
                    if 分配结果:     
                        self._使用红包(分配结果)
                        return

    def _领取每日累充奖励(self,按钮:Tuple[int,int,int,int]) ->Optional[bool]:
        调试器.debug("强化奖励", "每日累充: 领取宝箱")
        if self.页面.创建_通用点击区域验证文字切换(
                按钮,
                self.配置.区域.各种活动.连充豪礼页面已充值金额区域.元组,
                "今日|累充"
            ) .执行():
            for _ in range(5):                
                if not self.页面.创建寻图偏移点击操作(
                    self.配置.区域.各种活动.每日累充页面领取宝箱按钮区域.元组,                    
                    "红点1.bmp",
                    (-70, 5, -10, 25 )
                ).执行():     
                    time.sleep(self.配置.默认等待秒*2)    
                    self.页面.线程.刷新截图()           
                    break


    def _读取本周已充值天数(self) ->Optional[bool]:
        调试器.debug("强化奖励", "检查本周已充值天数")
        self._重置本周已充值天数()        
        time.sleep(self.配置.默认等待秒*2)
        self.页面.线程.刷新截图()
        self.页面.创建点击文字操作(
            self.配置.区域.各种活动.连充豪礼页面金额奖励区域.元组,
            self.每日累充金额,
        ).执行()
        time.sleep(self.配置.默认等待秒)
        self.页面.线程.刷新截图()
        
        领取结果文字 = self.辅助识别器.获取区域文字坐标(
            self.配置.区域.各种活动.连充豪礼页面领取范围区域.元组
        )
        调试器.trace("强化奖励", f"领取区域文字: {领取结果文字.get_all_texts() if 领取结果文字 else 'None'}")
        
        if 领取结果文字 is None:
            调试器.debug("强化奖励", "未识别到领取区域文字")
            return
        
        领取结果 = 领取结果文字.find("领取", return_all=True)
        调试器.trace("强化奖励", f"找到 {len(领取结果) if 领取结果 else 0} 个'领取'")
        
        if not 领取结果:
            调试器.debug("强化奖励", "未找到'领取'按钮")
            return
        
        count = len(领取结果)
        调试器.debug("强化奖励", f"第一页领取数量: {count}")
        
        if count < 4:
            self.本周已充值天数 = count
            self.上次读取每周充值天数时间 = time.time()
            调试器.debug("强化奖励", f"本周已充值天数: {self.本周已充值天数}")            
            return True
        

        if count >= 4:
            调试器.debug("强化奖励", "领取数量>=4，拖拽查看后面天数")
            x, y, x1, y1 = self.配置.区域.各种活动.连充豪礼页面天数范围区域.元组
            self.动作.drag(x1, y1, x, y)
            time.sleep(self.配置.默认等待秒 * 2)
            self.页面.线程.刷新截图()
            
            是否7天 = self.辅助识别器.区域包含文字(
                self.配置.区域.各种活动.连充豪礼页面天数范围区域.元组,
                "7天|第7"
            )
            调试器.trace("强化奖励", f"拖拽后是否包含7天: {是否7天}")
            
            if 是否7天:
                领取结果文字 = self.辅助识别器.获取区域文字坐标(
                    self.配置.区域.各种活动.连充豪礼页面领取范围区域.元组
                )
                调试器.trace("强化奖励", f"拖拽后领取区域文字: {领取结果文字.get_all_texts() if 领取结果文字 else 'None'}")
                
                if 领取结果文字 is None:
                    调试器.debug("强化奖励", "拖拽后未识别到领取区域文字")
                    return
                
                领取结果 = 领取结果文字.find("领取", return_all=True)
                if not 领取结果:
                    调试器.debug("强化奖励", "拖拽后未找到'领取'按钮")
                    return
                
                count2 = len(领取结果)
                self.本周已充值天数 = count2 + 3
                self.上次读取每周充值天数时间 = time.time()
                调试器.debug("强化奖励", f"拖拽后领取数量: {count2}, 本周已充值天数: {self.本周已充值天数}")
                return True
    def _重置本周已充值天数(self):
        """
        每周六开始新一周，每天均可充值并累加天数
        如果 本周已充值天数 > 从周6到现在的天数，重置为0
        """
        import datetime
        
        today = datetime.date.today()
        星期 = today.isoweekday()  # 1=周一 ... 6=周六 7=周日
        
        # 计算本周六的日期
        if 星期 == 6:
            本周六 = today
        elif 星期 == 7:
            本周六 = today - datetime.timedelta(days=1)
        else:
            本周六 = today - datetime.timedelta(days=星期 + 2)
        
        # 从周六到今天的天数（周六=1）
        应充值天数 = (today - 本周六).days + 1
        
        调试器.debug("强化奖励", f"本周六: {本周六}, 今天: {today}, 应充值天数: {应充值天数}, 实际充值天数: {self.本周已充值天数}")
        
        if self.本周已充值天数 > 应充值天数:
            调试器.debug("强化奖励", f"充值天数异常({self.本周已充值天数} > {应充值天数})，重置为0")
            self.本周已充值天数 = 0
    def _领取连充奖励(self) ->Optional[bool]:
        调试器.debug("强化奖励", "领取连充奖励")
        time.sleep(self.配置.默认等待秒)
        self.页面.线程.刷新截图()

        for _ in range(8):
            #点击上部红点
            time.sleep(self.配置.默认等待秒)
            self.页面.线程.刷新截图()
            if not self.页面.创建寻图偏移点击操作(
                self.配置.区域.各种活动.连充豪礼页面金额奖励区域.元组,
                "红点1.bmp",
                (-60,5,-10,25),
            ).执行():
                return
            time.sleep(self.配置.默认等待秒)
            self.页面.线程.刷新截图()
            
            领取结果文字 = self.辅助识别器.获取区域文字坐标(
                self.配置.区域.各种活动.连充豪礼页面领取范围区域.元组
            )        
            if 领取结果文字 is None:
                调试器.debug("强化奖励", "未识别到领取区域文字")
                continue
            
            领取结果 = 领取结果文字.find("领取", return_all=True)
            调试器.trace("强化奖励", f"找到 {len(领取结果) if 领取结果 else 0} 个'领取'")
            
            if not 领取结果:
                调试器.debug("强化奖励", "未找到'领取'按钮")
                continue
            
            count = len(领取结果)
            调试器.debug("强化奖励", f"第一页领取数量: {count}")
            
            if count < 4:
                领取按钮=领取结果文字.find("领取",match_type="exact", return_all=True)
                if 领取按钮:  
                    for 按钮 in 领取按钮:                    
                        self.通用操作.点击区域(按钮)
                        time.sleep(self.配置.默认等待秒)
                continue
            

            if count >= 4:
                调试器.debug("强化奖励", "领取数量>=4，拖拽查看后面天数")
                x, y, x1, y1 = self.配置.区域.各种活动.连充豪礼页面天数范围区域.元组
                self.动作.drag(x1, y1, x, y)
                time.sleep(self.配置.默认等待秒 * 2)
                self.页面.线程.刷新截图()
                
                是否7天 = self.辅助识别器.区域包含文字(
                    self.配置.区域.各种活动.连充豪礼页面天数范围区域.元组,
                    "7天|第7"
                )
                调试器.trace("强化奖励", f"拖拽后是否包含7天: {是否7天}")
                
                if 是否7天:
                    领取结果文字 = self.辅助识别器.获取区域文字坐标(
                        self.配置.区域.各种活动.连充豪礼页面领取范围区域.元组
                    )
                    
                    if 领取结果文字 is None:
                        调试器.debug("强化奖励", "拖拽后未识别到领取区域文字")
                        continue                
                    领取按钮=领取结果文字.find("领取",match_type="exact", return_all=True)
                    if 领取按钮:  
                        for 按钮 in 领取按钮:                    
                            self.通用操作.点击区域(按钮)
                            time.sleep(self.配置.默认等待秒)
                    
    def _使用红包(self, 分配结果: list) -> bool:
        """
        按分配结果依次右键单击红包图标，确认使用。
        分配结果: [{"金额": 100, "使用数量": 2, "图标区域": (...), "格子序号": 0}, ...]
        """
        if not 分配结果:
            return False
        
        # 按格子序号排序，确保从上到下从左到右依次点击
        排序结果 = sorted(分配结果, key=lambda x: x["格子序号"])
        右键有效=True
        for 红包 in 排序结果:            
                图标 = 红包["图标区域"]
                if not 右键有效:                    
                    self.通用操作.点击区域(图标, 2,0.1,缩放比例=0.5)
                else:  
                   self.通用操作.点击区域(图标, 1,button="right",缩放比例=0.5)
                if  红包["数量"]==1:                    
                    continue
                # 确认使用
                time.sleep(self.配置.默认等待秒*2)
                self.页面.线程.刷新截图()
                if not self.辅助识别器.区域包含文字(self.配置.区域.各种活动.红包使用信息提示区域.元组,"请输入|使用道具|的数量"):
                   右键有效=False
                   self.通用操作.点击区域(图标, 2,0.1,缩放比例=0.5)
                   time.sleep(self.配置.默认等待秒*2)
                   self.页面.线程.刷新截图()
                   if not self.辅助识别器.区域包含文字(self.配置.区域.各种活动.红包使用信息提示区域.元组,"请输入|使用道具|的数量"):
                        continue
                self.通用操作.点击区域(self.配置.区域.各种活动.红包数量输入区域.元组, 2,0.1,缩放比例=0.5)
                
                self.动作.set_keyboard_mode("后台")
                调试器.debug("红包", f"使用红包: {红包['使用数量']}")
                self.动作.type_text(str(红包["使用数量"]))
                self.动作.set_keyboard_mode("前台")
                time.sleep(self.配置.默认等待秒)
                self.通用操作.点击区域(self.配置.区域.各种活动.红包使用信息提示区域.元组, 2)
                time.sleep(self.配置.默认等待秒*2)
                self.页面.线程.刷新截图()
                数量=self.辅助识别器.获取区域次数(self.配置.区域.各种活动.红包数量输入区域.元组)
                if 数量 is None or 数量!=红包["使用数量"]:  
                    self.页面.创建_通用点击文字验证文字切换(
                        self.配置.区域.各种活动.红包取消按钮区域.元组,
                        "取|消",
                        self.配置.区域.各种活动.红包取消按钮区域.元组,
                        "取|消",
                        False
                    ).执行()
                                
                    continue
                else:
                    self.页面.创建_通用点击文字验证文字切换(
                            self.配置.区域.各种活动.红包使用按钮区域.元组,
                            "使|用",
                            self.配置.区域.各种活动.红包使用按钮区域.元组,
                            "使|用",
                            False
                        ).执行()
                    for _ in range(5):  
                        time.sleep(1)                      
                        self.页面.线程.刷新截图()
                        if self.页面.创建_通用点击图片验证图片切换(
                            self.配置.区域.各种活动.红包提示信息搜寻区域.元组,
                            "红包收益提示.bmp",
                            self.配置.区域.各种活动.红包提示信息搜寻区域.元组,
                            "红包收益提示.bmp",
                            False
                        ).执行():                        
                            调试器.debug("红包", "使用红包成功")
                            break
                    
        return True


    
    def _检查是否要充值(self):
        if not 是否为今天(self.上次充值时间):
            self.上次充值时间=time.time()
            self.今日已充值金额=0
        每日累充金额=int(self.每日累充金额)
        if self.今日已充值金额>=每日累充金额:
            调试器.debug("强化奖励", "每日累充: 今日已充值")
            return False      
        return True
    def 获取红包数据(self, 背包区域: Tuple[int, int, int, int], 
                 格子坐标集合: List[Tuple[int, int, int, int]]) -> List[Dict]:
        """
        获取所有红包的金额、数量、图标区域、序号
        
        返回:
            [{"金额": 1, "数量": 5, "图标区域": (...), "格子序号": 0}, ...]
        """
        红包配置 = [
            {"金额": 1, "图片": "1元图标.bmp"},
            {"金额": 5, "图片": "5元图标.bmp"},
            {"金额": 10, "图片": "10元图标.bmp"},
            {"金额": 50, "图片": "50元图标.bmp"},
            {"金额": 100, "图片": "100元图标.bmp"},
        ]
        
        红包列表 = []
        filter_config = {
                "color_diff": "10-80,255,80,255,80,255",
                "keep_color": True,
                "background": "black"
            }
        for 配置 in 红包配置:
            调试器.debug("红包图标", f"金额: {配置['金额']}")
            调试器.debug("红包图标",  配置["图片"])
            图标 = self.辅助识别器.查找图片单结果(背包区域, 配置["图片"])
            if 图标 is None: 
                调试器.debug("红包图标", f"红包查找失败")
            if 图标:
                调试器.debug("红包图标", f"格子序号: {图标}")
                格子, 序号 = self.通用操作.查找目标所在格子(图标, 格子坐标集合)
                if 格子 is not None:
                    数量区域 = (格子[0] + 28, 格子[1] + 40, 格子[0] + 60, 格子[1] + 61)
                    数量 = self.辅助识别器.获取区域次数(数量区域, filter_config)
                    if 数量 is None:
                        数量=1
                    调试器.debug("红包数量", f"格子序号: {序号}, 量: {数量}")
                    调试器.debug("红包金额", 配置["金额"])
                    红包列表.append({
                        "金额": 配置["金额"],
                        "数量": 数量,
                        "图标区域": 图标,
                        "格子序号": 序号,
                    })
        
        return 红包列表


            
           

   
           

         

      
