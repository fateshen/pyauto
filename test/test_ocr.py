

# test/test_ocr_simple.py
"""
简单OCR测试 - 测试文字识别功能

运行方式：
    python -m test.test_ocr_simple
"""
from ctypes.wintypes import PINT
import sys
import os
import time
import cv2
import numpy as np

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.recognition import TextRecognizer,TemplateMatcher
from core.window_manager import capture_window
from models.region_config import 区域配置
from core.action_executor import ActionExecutor
from core.utils import 缩放区域, 解析时间文字, 随机点
from typing import Tuple, Union, List, Optional
import random


"""
图片颜色分析器

功能：
- 分析目标图和噪点图的颜色分布
- 自动生成多组 color_range 候选
- 按目标命中率和噪点排除率评分排序
"""
import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
# from sklearn.cluster import KMeans
from core.debug import 调试器


class 图片颜色分析器:
    """图片颜色分析器"""
    
    def __init__(self, 目标图路径: str, 噪点图路径: str):
        from pathlib import Path
    
        # 尝试查找图片
        self.目标图 = self._读取图片(目标图路径)
        self.噪点图 = self._读取图片(噪点图路径)
        
        if self.目标图 is None:
            raise FileNotFoundError(f"目标图不存在: {目标图路径}")
        if self.噪点图 is None:
            raise FileNotFoundError(f"噪点图不存在: {噪点图路径}")
        
        self.目标颜色列表 = self._提取非黑像素_RGB(self.目标图)
        self.噪点颜色列表 = self._提取非黑像素_RGB(self.噪点图)
        
        print(f"目标图非黑像素数: {len(self.目标颜色列表)}")
        print(f"噪点图非黑像素数: {len(self.噪点颜色列表)}")


    def _读取图片(self, 路径: str):
        """读取图片，支持相对路径和绝对路径"""
        from pathlib import Path
        
        # 直接尝试
        img = cv2.imread(路径)
        if img is not None:
            return img
        
        # 尝试当前工作目录
        cwd_path = Path.cwd() / 路径
        if cwd_path.exists():
            return cv2.imread(str(cwd_path))
        
        # 尝试脚本所在目录
        import sys
        if getattr(sys, 'frozen', False):
            script_dir = Path(sys.executable).parent
        else:
            script_dir = Path(sys.argv[0]).parent if sys.argv[0] else Path.cwd()
        
        script_path = script_dir / 路径
        if script_path.exists():
            return cv2.imread(str(script_path))
        
        # 尝试帝王霸业图库
        from core.path_manager import path_mgr
        图库路径 = path_mgr.image_dir / 路径
        if 图库路径.exists():
            return cv2.imread(str(图库路径))
        
        return None
    
    def _提取非黑像素_RGB(self, img: np.ndarray) -> np.ndarray:
        """提取非黑像素，BGR转RGB"""
        mask = np.any(img > 5, axis=2)  # R,G,B都<=5视为纯黑
        pixels = img[mask]
        if len(pixels) == 0:
            return np.array([])
        # BGR → RGB
        return pixels[:, ::-1]
    
    #完全赛出
    def 生成候选(self, 
             聚类数范围: Tuple[int, int] = (1, 8),
             扩展值列表: List[int] = None,
             模式: str = "A") -> List[Dict]:
        """
        生成多组 color_range 候选
        
        参数:
            模式: "A"=平衡, "B"=排除噪点优先
        """
        if 扩展值列表 is None:
            扩展值列表 = [2, 5, 8, 12, 18, 25]
        
        if len(self.目标颜色列表) == 0:
            return []
        
        所有候选 = []
        
        for 聚类数 in range(聚类数范围[0], 聚类数范围[1] + 1):
            if 聚类数 > len(self.目标颜色列表):
                break
            
            聚类结果 = self._聚类颜色(聚类数)
            
            for 扩展值 in 扩展值列表:
                规则 = self._聚类生成规则(聚类结果, 扩展值)
                评分 = self._评估规则(规则)
                
                所有候选.append({
                    "color_range": 规则,
                    "聚类数": 聚类数,
                    "扩展值": 扩展值,
                    "评分": 评分,
                    "综合分": 评分["目标命中率"] - 评分["噪点误命中率"],
                    "filter_config": {
                        "color_range": 规则,
                        "keep_color": True,
                        "background": "black"
                    }
                })
        
        if 模式 == "B":
            # 方案B：噪点0命中优先，其次目标命中率
            所有候选.sort(key=lambda x: (x["评分"]["噪点误命中率"], -x["评分"]["目标命中率"]))
        else:
            # 方案A：综合分高
            所有候选.sort(key=lambda x: -x["综合分"])
        
        return 所有候选


    # # ========损失原值，折中
    # def 生成候选(self, 
    #          聚类数范围: Tuple[int, int] = (1, 8),
    #          扩展值列表: List[int] = None) -> List[Dict]:
    #     """
    #     生成多组 color_range 候选（方案A：平衡目标命中率和噪点排除率）
    #     """
    #     if 扩展值列表 is None:
    #         扩展值列表 = [2, 5, 8, 12, 18, 25]
        
    #     if len(self.目标颜色列表) == 0:
    #         return []
        
    #     所有候选 = []
        
    #     for 聚类数 in range(聚类数范围[0], 聚类数范围[1] + 1):
    #         if 聚类数 > len(self.目标颜色列表):
    #             break
            
    #         聚类结果 = self._聚类颜色(聚类数)
            
    #         for 扩展值 in 扩展值列表:
    #             规则 = self._聚类生成规则(聚类结果, 扩展值)
    #             评分 = self._评估规则(规则)
                
    #             所有候选.append({
    #                 "color_range": 规则,
    #                 "聚类数": 聚类数,
    #                 "扩展值": 扩展值,
    #                 "评分": 评分,
    #                 "综合分": 评分["目标命中率"] - 评分["噪点误命中率"],
    #                 "filter_config": {
    #                     "color_range": 规则,
    #                     "keep_color": True,
    #                     "background": "black"
    #                 }
    #             })
        
    #     # 方案A：目标命中率高 + 噪点误命中率低 → 综合分高
    #     所有候选.sort(key=lambda x: -x["综合分"])
        
    #     return 所有候选



    #========保留所有原值
    # def 生成候选(self, 
    #              聚类数范围: Tuple[int, int] = (1, 8),
    #              扩展值列表: List[int] = None,
    #              噪点容忍度: float = 0.05) -> List[Dict]:
    #     """
    #     生成多组 color_range 候选
        
    #     参数:
    #         聚类数范围: (最小聚类数, 最大聚类数)，尝试不同聚类数
    #         扩展值列表: RGB范围扩展值列表，如 [3, 5, 8, 12, 20]
    #         噪点容忍度: 允许的最大噪点误命中率
        
    #     返回:
    #         候选列表，按评分降序
    #     """
    #     if 扩展值列表 is None:
    #         扩展值列表 = [2, 5, 8, 12, 18, 25]
        
    #     if len(self.目标颜色列表) == 0:
    #         return []
        
    #     所有候选 = []
        
    #     for 聚类数 in range(聚类数范围[0], 聚类数范围[1] + 1):
    #         if 聚类数 > len(self.目标颜色列表):
    #             break
            
    #         # 聚类
    #         聚类结果 = self._聚类颜色(聚类数)
            
    #         for 扩展值 in 扩展值列表:
    #             # 生成 color_range
    #             规则 = self._聚类生成规则(聚类结果, 扩展值)
                
    #             # 评估
    #             评分 = self._评估规则(规则)
                
    #             if 评分["噪点误命中率"] <= 噪点容忍度 or 噪点容忍度 >= 1.0:
    #                 所有候选.append({
    #                     "color_range": 规则,
    #                     "聚类数": 聚类数,
    #                     "扩展值": 扩展值,
    #                     "评分": 评分,
    #                     "filter_config": {
    #                         "color_range": 规则,
    #                         "keep_color": True,
    #                         "background": "black"
    #                     }
    #                 })
        
    #     # 按评分排序（目标命中率高 + 噪点误命中率低）
    #     所有候选.sort(key=lambda x: (
    #         -x["评分"]["目标命中率"],
    #         x["评分"]["噪点误命中率"]
    #     ))
        
    #     return 所有候选
    
    def _聚类颜色(self, 聚类数: int) -> List[Dict]:
        """用纯numpy实现K-Means聚类颜色"""
        if len(self.目标颜色列表) == 0:
            return []
        
        if len(self.目标颜色列表) <= 聚类数:
            聚类数 = len(self.目标颜色列表)
        
        数据 = self.目标颜色列表.astype(np.float64)
        
        # 随机初始化聚类中心
        np.random.seed(42)
        索引 = np.random.choice(len(数据), 聚类数, replace=False)
        中心 = 数据[索引].copy()
        
        for _ in range(100):  # 最多100次迭代
            # 计算每个点到各中心的距离
            距离 = np.zeros((len(数据), 聚类数))
            for i in range(聚类数):
                距离[:, i] = np.sqrt(np.sum((数据 - 中心[i])**2, axis=1))
            
            # 分配标签
            标签 = np.argmin(距离, axis=1)
            
            # 更新中心
            新中心 = np.zeros_like(中心)
            for i in range(聚类数):
                簇点 = 数据[标签 == i]
                if len(簇点) > 0:
                    新中心[i] = np.mean(簇点, axis=0)
                else:
                    新中心[i] = 中心[i]  # 空簇保持原中心
            
            # 检查收敛
            if np.allclose(中心, 新中心, rtol=1e-4):
                break
            
            中心 = 新中心
        
        # 构建结果
        结果 = []
        for i in range(聚类数):
            簇像素 = 数据[标签 == i]
            if len(簇像素) == 0:
                continue
            
            结果.append({
                "中心": 中心[i],
                "最小": np.min(簇像素, axis=0),
                "最大": np.max(簇像素, axis=0),
                "数量": len(簇像素),
                "占比": len(簇像素) / len(数据)
            })
        
        return 结果
    
    def _聚类生成规则(self, 聚类结果: List[Dict], 扩展值: int) -> str:
        """从聚类结果生成 color_range 字符串"""
        规则列表 = []
        
        for 簇 in 聚类结果:
            最小 = np.maximum(0, 簇["最小"] - 扩展值)
            最大 = np.minimum(255, 簇["最大"] + 扩展值)
            
            规则列表.append(
                f"{int(最小[0])},{int(最大[0])},"
                f"{int(最小[1])},{int(最大[1])},"
                f"{int(最小[2])},{int(最大[2])}"
            )
        
        return "|".join(规则列表)
    
    def _评估规则(self, 规则: str) -> Dict:
        """评估规则的目标命中率和噪点误命中率"""
        # 解析规则
        区间列表 = []
        for 部分 in 规则.split('|'):
            值 = [int(x.strip()) for x in 部分.split(',')]
            if len(值) == 6:
                区间列表.append(((值[0], 值[1]), (值[2], 值[3]), (值[4], 值[5])))
        
        # 统计目标命中
        目标命中 = 0
        for 像素 in self.目标颜色列表:
            if self._像素在区间内(像素, 区间列表):
                目标命中 += 1
        
        # 统计噪点命中
        噪点命中 = 0
        if len(self.噪点颜色列表) > 0:
            for 像素 in self.噪点颜色列表:
                if self._像素在区间内(像素, 区间列表):
                    噪点命中 += 1
        
        return {
            "目标命中率": 目标命中 / len(self.目标颜色列表) if len(self.目标颜色列表) > 0 else 0,
            "目标命中数": 目标命中,
            "目标总数": len(self.目标颜色列表),
            "噪点误命中率": 噪点命中 / len(self.噪点颜色列表) if len(self.噪点颜色列表) > 0 else 0,
            "噪点命中数": 噪点命中,
            "噪点总数": len(self.噪点颜色列表),
        }
    
    def _像素在区间内(self, 像素: np.ndarray, 区间列表: List) -> bool:
        """判断像素是否在任一区间内"""
        r, g, b = int(像素[0]), int(像素[1]), int(像素[2])
        for (r_range, g_range, b_range) in 区间列表:
            if (r_range[0] <= r <= r_range[1] and
                g_range[0] <= g <= g_range[1] and
                b_range[0] <= b <= b_range[1]):
                return True
        return False
    
    def 打印候选(self, 候选列表: List[Dict], 显示数量: int = 10):
        """打印候选结果"""
        print("\n" + "=" * 80)
        print("颜色分析结果（前{}条）".format(min(显示数量, len(候选列表))))
        print("=" * 80)
        
        for i, 候选 in enumerate(候选列表[:显示数量]):
            评分 = 候选["评分"]
            print(f"\n--- 候选 {i+1} (聚类数={候选['聚类数']}, 扩展值={候选['扩展值']}) ---")
            print(f"  目标命中率: {评分['目标命中率']:.1%} ({评分['目标命中数']}/{评分['目标总数']})")
            print(f"  噪点误命中率: {评分['噪点误命中率']:.1%} ({评分['噪点命中数']}/{评分['噪点总数']})")
            print(f"  color_range: \"{候选['color_range']}\"")
            print(f"  filter_config:")
            print(f"    {候选['filter_config']}")




# ==================== 便捷函数 ====================
#完全赛出
def 分析图片生成规则(目标图路径: str, 噪点图路径: str, 
                     聚类数范围: Tuple[int, int] = (1, 8),
                     扩展值列表: List[int] = None,
                     显示数量: int = 10,
                     模式: str = "A") -> List[Dict]:
    """
    便捷函数：分析图片并打印结果
    
    参数:
        模式: "A"=平衡, "B"=排除噪点优先
    """
    分析器 = 图片颜色分析器(目标图路径, 噪点图路径)
    候选 = 分析器.生成候选(聚类数范围, 扩展值列表, 模式=模式)
    分析器.打印候选(候选, 显示数量)
    return 候选
# #折中
# def 分析图片生成规则(目标图路径: str, 噪点图路径: str, 
#                      聚类数范围: Tuple[int, int] = (1, 8),
#                      扩展值列表: List[int] = None,
#                      显示数量: int = 10) -> List[Dict]:
#     """便捷函数：分析图片并打印结果"""
#     分析器 = 图片颜色分析器(目标图路径, 噪点图路径)
#     候选 = 分析器.生成候选(聚类数范围, 扩展值列表)   # ← 去掉噪点容忍度
#     分析器.打印候选(候选, 显示数量)
#     return 候选
#保留原值
# def 分析图片生成规则(目标图路径: str, 噪点图路径: str, 
#                      聚类数范围: Tuple[int, int] = (1, 8),
#                      扩展值列表: List[int] = None,
#                      显示数量: int = 10,
#                      噪点容忍度: float = 1.0) -> List[Dict]:  # ← 默认1.0=显示全部
#     """便捷函数：分析图片并打印结果"""
#     分析器 = 图片颜色分析器(目标图路径, 噪点图路径)
#     候选 = 分析器.生成候选(聚类数范围, 扩展值列表, 噪点容忍度)
    
#     if not 候选:
#         print("⚠️ 没有候选满足噪点容忍度，显示所有候选（未过滤）")
#         候选 = 分析器.生成候选(聚类数范围, 扩展值列表, 噪点容忍度=1.0)
    
#     分析器.打印候选(候选, 显示数量)
#     return 候选

#=================================================================
def 提取等级数字(text: str) -> Union[int, bool]:
    """
    从文字中提取等级数字
    
    参数:
        text: 如 "天之主[5400级]" 或 "雷使[5300级]"
    
    返回:
        等级数字，如 5400，未找到返回 False
    """
    import re
    
    # 匹配 [数字级] 格式
    match = re.search(r'\[(\d+)级\]', text)
    if match:
        return int(match.group(1))
    
    # 匹配 数字级 格式（无括号）
    match = re.search(r'(\d+)级', text)
    if match:
        return int(match.group(1))
    
    return False
def _提取邀请玩家名(文字: str) -> str:
    """
    从邀请文字中提取玩家名
    
    "巢元畅邀请您加入他的战队" → "巢元畅"
    "古剑宝贝多出邀请您加入他的战队" → "古剑宝贝多出"
    """
    if not 文字:
        return ""
    
    # 找到"邀请"的位置，之前的部分就是玩家名
    位置 = 文字.find("邀请")
    if 位置 > 0:
        return 文字[:位置]
    
    return ""

def test_ocr():
    """测试OCR识别"""
    print("\n" + "=" * 60)
    print("OCR识别测试")
    print("=" * 60)
    
    # 窗口句柄
    hwnd = 944048
    # hwnd = 598454
    区域=区域配置.创建默认()
    # 区域.保存到文件("region_config.json")
    # 1. 截图
    print("\n[1] 截图...")
    截图 = capture_window(hwnd, client_only=True)
    
    if 截图 is None:
        print("❌ 截图失败，请检查窗口句柄是否正确")
        print(f"   窗口句柄: {hwnd}")
        return False
    
    print(f"✅ 截图成功，尺寸: {截图.shape}")
    
    # 保存截图用于调试
    cv2.imwrite("debug_screenshot.png", 截图)
    print("   已保存: debug_screenshot.png")
    
    # 2. 创建OCR识别器
    print("\n[2] 初始化OCR...")
    识别器 = TextRecognizer()
    模板匹配=TemplateMatcher()
    鼠标模拟器=ActionExecutor(hwnd)
    print("✅ 匹配开始")
    自检区域=295,223,817,617
    匹配=模板匹配.match_bypicture(截图, "背包仓库图标.bmp",0.5)
    
    if 匹配:

        print(  f"匹配：{匹配}")

    # 图片集合=("1元图标.bmp", "5元图标.bmp", "10元图标.bmp", "50元图标.bmp","100元图标.bmp", 
                       
    #            )
    # time1=time.time()
    # 所有区域=模板匹配.match_multiple_bypictures(截图, 图片集合,0.9,自检区域)
    # print(time.time()-time1)
    # for 图片 in 所有区域:
    #     print(f"   图片：{图片}")
    #     for 匹配1 in 所有区域[图片]:
    #         print(f"   匹配：{匹配1.rect}")
        
    # 鼠标模拟器.click(730,691,button="right")
    # time.sleep(0.01)
    # 鼠标模拟器.click(1149,576)
    # time.sleep(0.05)
    # 鼠标模拟器.set_keyboard_mode("后台")
    # 鼠标模拟器.type_text("11")
    # 鼠标模拟器.set_keyboard_mode("前台")
    
    # 多匹配=模板匹配.match_all_bypicture(截图, "3级异界.bmp",region=区域.异界夺宝.报名标记查找区域标签.元组)
    # print(f"   多匹配：{多匹配}")
    # for 匹配 in 多匹配:
    #     print(  f"匹配x：{匹配.rect}")
    # 文字集合=识别器.recognize_result(截图,区域.合成.合成左分类卡区域标签.元组)
    # 文字区域集合=文字集合.get_all_boxes()
    # 文字集合.print_items()
    # print(f"   文字区域：{文字集合.get_all_texts()}")
    # 图片集合=[匹配1.rect for 匹配1 in 匹配]
    # print(f"   图片区域：{图片集合}")
    # from core.utils import 提取重叠区域
    # 重叠区域=提取重叠区域(文字区域集合,图片集合)
    # print(f"   重叠区域：{重叠区域}")
   
    # 降魔定位区域=匹配.rect
    # 时间区域=降魔定位区域[0] + 52,降魔定位区域[1] + 191,降魔定位区域[0] + 167,降魔定位区域[1] + 226
    # 时间文字=识别器.recognize_text(截图,时间区域)
    # print(f"   时间: {时间文字}")

    x,y =区域.合成.合成左分类卡区域标签.随机点(0.5)
    鼠标模拟器.drag(x,y,x,y+300)
    # time.sleep(1)   
    # for i in range(0):
    #     # 拖拽范围=拖拽区域[0],拖拽区域[3],拖拽区域[2],拖拽区域[1]
    #     鼠标模拟器.drag(x,y,x,y-257)
    #     time.sleep(0.5)
    #     鼠标模拟器.drag(x,y,x,y-257)
    #     print(i+1)
    #     time.sleep(0.5)        
    #     截图 = capture_window(hwnd, client_only=True)
    # 鼠标模拟器.drag(508,346,567,551)
    # # 3. 全图识别
    # print("\n[3] 全图识别...")
    # 结果 = 识别器.recognize_text(截图)
    # print(f"   识别结果: {结果}")
    
    # if 结果:
    #     print(f"   文字长度: {len(结果)}")
    #     print(f"   前100字符: {结果[:100]}...")
    
    # # 4. 识别指定区域（地图名称区域）
    # print("\n[4] 识别地图名称区域...")
    # # 地图名称区域坐标 (左, 上, 右, 下)
    # 地图区域 = (1580, 2, 1698, 23)
    
    # # 裁剪区域并保存
    # 左, 上, 右, 下 = 地图区域
    # 区域截图 = 截图[上:下, 左:右]
    # cv2.imwrite("debug_map_region.png", 区域截图)
    # print(f"   区域保存: debug_map_region.png")
    
    # 地图结果 = 识别器.recognize_text(截图, region=地图区域)
    # print(f"   地图名称识别: '{地图结果}'")
    
    info=区域.主宰.主宰归属玩家检查区域.元组
    # print(info)
   
    # info = 缩放区域(info, 1.2)
    # print(缩放)
    # # 5. 获取详细结果（带坐标）
    # print("\n[5] 获取详细识别结果（带坐标）...")
    filter_config = {
                # "color_range": "110,255,0,24,0,20|0,25,150,255,0,16",  
                # "color_range":"162,178,9,14,9,15|125,130,6,15,2,15|229,233,7,11,7,11|138,165,10,18,10,18|215,219,8,12,8,12|186,205,8,13,8,13|110,120,11,17,11,18",
                "color_diff": "8-80,255,80,255,80,255",
                "keep_color": True,
                "background": "black"
            }
    时间=time.time()
    ocr_result = 识别器.recognize_result(截图,info)
    print(f"识别时间：{time.time()-时间}")
    # tex=ocr_result.get_all_texts()

    print(ocr_result.items)
    # for 文字, 坐标 in ocr_result.items:
    #     玩家名 = _提取邀请玩家名(文字)
    #     if not 玩家名:
    #         continue
    #     print(f"   玩家名: {玩家名}")
    #     print(f"   zuobiao: {坐标}")
    # print(tex)
    # text=ocr_result.get_all_text()
    # print(text)
    # print(解析时间文字(text))
    # print(len(text))
    # text=ocr_result.print_items()
    
    # for i in range(4):
    #         index=i+1
    #         print(f"识别第{index}个区域")
    #         属性名 = f"位置{index}"
    #         print(属性名)
    #         # 区域对象 = getattr(区域.诸神遗迹BOSS地图刷新时间区域, 属性名, None)
    #         区域对象 =区域.陨圣.获取刷新标签(index)
           
    #         if 区域对象 is None:               
    #             continue
    #         识别区域 = 区域对象.元组
    #         ocr_result = 识别器.recognize_text(截图,识别区域,filter_config)
    #         print(ocr_result)
    # print(f"   识别结果: {text}")


    
    # a,b,c=获取倒数第二次刷新信息(ocr_result)
    # print(a,b,c)
    
    # if not a:
    #     print("未找到刷新信息")
    #     x,y=随机点(info, 0.5)
        
    #     鼠标模拟器.drag(x, y, x, y+random.randint(100, 200),random.uniform(0.1, 0.5))
    # 截图 = capture_window(hwnd, client_only=True)
    # ocr_result = 识别器.recognize_result(截图,info)
    # a,b,c=获取倒数第二次刷新信息(ocr_result)
    # print(a,b,c)
    # if ocr_result:
    #     print(f"   识别结果:{ocr_result}")
    #     所有文字 = ocr_result.get_all_texts()
    #     print(f"   识别到 {len(所有文字)} 个文本块")
        
    #     # 打印前10个文本块
    #     for i, text in enumerate(所有文字[:15]):
    #         print(f"     [{i}] {text}")
    #     alltex=ocr_result.get_all_text()
    #     print(f"   识别到 {alltex}")
    # else:
    #     print("   未识别到文字")
    
    # # 6. 测试查找特定文字
    # print("\n[6] 查找特定文字...")
    # if ocr_result:
    #     位置 = ocr_result.find("刷", match_type="contains",return_all= True)
    #     if 位置:
    #         print(f"   找到'刷'位置: {位置}")
    #         print(f"   找到'刷'数量: {len(位置)}")
    #     else:
    #         print("   未找到'刷'")
        
       
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
    
    return True


import subprocess

def 检查UMI运行() -> bool:
    """检查 UMI-OCR 进程是否在运行"""
    try:
        结果 = subprocess.run(
            ['tasklist', '/fi', 'IMAGENAME eq UMI-OCR.exe'],
            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
        )
        return 'Umi-OCR.exe' in 结果.stdout
    except:
        return False
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
if __name__ == "__main__":
    # 运行基础测试
    # if  检查UMI运行():
    #     print("UMI-OCR 运行，请先运行 UMI-OCR.exe")
    #     exit(1)
    test_ocr()

    # 红包列表 = []
    # # 红包列表.append({
    # #                 "金额":1,
    # #                 "数量":1000,
    # #                 "图标区域": (100, 100, 100, 100),
    # #                 "格子序号": 1,
    # #             })
    # # 红包列表.append({
    # #                 "金额":5,
    # #                 "数量":20,
    # #                 "图标区域": (200, 200, 100, 100),
    # #                 "格子序号": 2,
    # #             })
    # # 红包列表.append({
    # #                 "金额":10,
    # #                 "数量":10,
    # #                 "图标区域": (500, 200, 100, 100),
    # #                 "格子序号": 3,
    # #             })
    # 红包列表.append({
    #                 "金额":50,
    #                 "数量":20,
    #                 "图标区域": (500, 200, 100, 100),
    #                 "格子序号": 4,
    #             })
    # 红包列表.append({
    #                 "金额":100,
    #                 "数量":20,
    #                 "图标区域": (500, 200, 100, 100),
    #                 "格子序号": 5,
    #             })
    # 分配结果= 计算红包分配(红包列表, 165)
    # 打印分配结果(分配结果, 165)
    # 可选：运行特定区域测试
    # test_特定区域列表()
    
    # 可选：运行连续识别测试
    # test_连续识别()

    #保留所有原值
    # 候选 = 分析图片生成规则(
    #     "F.PNG",
    #     "Z.PNG",
    #     聚类数范围=(1, 6),
    #     扩展值列表=[3, 5, 8, 12, 18],
    #     显示数量=15,
    #     噪点容忍度=1.0,
    # )

    #损失原值   
    # 候选 = 分析图片生成规则(
    #     "F.PNG",
    #     "Z.PNG",
    #     聚类数范围=(1, 6),
    #     扩展值列表=[3, 5, 8, 12, 18],
    #     显示数量=15,
    # )
    # 分析图片生成规则("F.PNG", "Z.PNG", 模式="B")
    # # 挑选最优的
    # 最优 = 候选[0]
    # print(最优["color_range"])
    # print(最优["filter_config"])