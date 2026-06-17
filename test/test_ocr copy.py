

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

from sympy import im

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
        self.目标图 = cv2.imread(目标图路径)
        self.噪点图 = cv2.imread(噪点图路径)
        
        if self.目标图 is None:
            raise FileNotFoundError(f"目标图不存在: {目标图路径}")
        if self.噪点图 is None:
            raise FileNotFoundError(f"噪点图不存在: {噪点图路径}")
        
        # 提取非黑像素（OpenCV是BGR，转RGB）
        self.目标颜色列表 = self._提取非黑像素_RGB(self.目标图)
        self.噪点颜色列表 = self._提取非黑像素_RGB(self.噪点图)
        
        print(f"目标图非黑像素数: {len(self.目标颜色列表)}")
        print(f"噪点图非黑像素数: {len(self.噪点颜色列表)}")
    
    def _提取非黑像素_RGB(self, img: np.ndarray) -> np.ndarray:
        """提取非黑像素，BGR转RGB"""
        mask = np.any(img > 5, axis=2)  # R,G,B都<=5视为纯黑
        pixels = img[mask]
        if len(pixels) == 0:
            return np.array([])
        # BGR → RGB
        return pixels[:, ::-1]
    
    def 生成候选(self, 
                 聚类数范围: Tuple[int, int] = (1, 8),
                 扩展值列表: List[int] = None,
                 噪点容忍度: float = 0.05) -> List[Dict]:
        """
        生成多组 color_range 候选
        
        参数:
            聚类数范围: (最小聚类数, 最大聚类数)，尝试不同聚类数
            扩展值列表: RGB范围扩展值列表，如 [3, 5, 8, 12, 20]
            噪点容忍度: 允许的最大噪点误命中率
        
        返回:
            候选列表，按评分降序
        """
        if 扩展值列表 is None:
            扩展值列表 = [2, 5, 8, 12, 18, 25]
        
        if len(self.目标颜色列表) == 0:
            return []
        
        所有候选 = []
        
        for 聚类数 in range(聚类数范围[0], 聚类数范围[1] + 1):
            if 聚类数 > len(self.目标颜色列表):
                break
            
            # 聚类
            聚类结果 = self._聚类颜色(聚类数)
            
            for 扩展值 in 扩展值列表:
                # 生成 color_range
                规则 = self._聚类生成规则(聚类结果, 扩展值)
                
                # 评估
                评分 = self._评估规则(规则)
                
                if 评分["噪点误命中率"] <= 噪点容忍度 or 噪点容忍度 >= 1.0:
                    所有候选.append({
                        "color_range": 规则,
                        "聚类数": 聚类数,
                        "扩展值": 扩展值,
                        "评分": 评分,
                        "filter_config": {
                            "color_range": 规则,
                            "keep_color": True,
                            "background": "black"
                        }
                    })
        
        # 按评分排序（目标命中率高 + 噪点误命中率低）
        所有候选.sort(key=lambda x: (
            -x["评分"]["目标命中率"],
            x["评分"]["噪点误命中率"]
        ))
        
        return 所有候选
    
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

def 分析图片生成规则(目标图路径: str, 噪点图路径: str, 
                     聚类数范围: Tuple[int, int] = (1, 8),
                     扩展值列表: List[int] = None,
                     显示数量: int = 10) -> List[Dict]:
    """便捷函数：分析图片并打印结果"""
    分析器 = 图片颜色分析器(目标图路径, 噪点图路径)
    候选 = 分析器.生成候选(聚类数范围, 扩展值列表)
    分析器.打印候选(候选, 显示数量)
    return 候选

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
    hwnd = 270906
    # hwnd = 598454
    区域=区域配置.创建默认()

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
    匹配=模板匹配.match_bypicture(截图, "2级异界.bmp",region=区域.异界夺宝.报名标记查找区域标签.元组)

    if 匹配:
        print(  f"匹配：{匹配.rect}")
    多匹配=模板匹配.match_all_bypicture(截图, "3级异界.bmp",region=区域.异界夺宝.报名标记查找区域标签.元组)
    print(f"   多匹配：{多匹配}")
    for 匹配 in 多匹配:
        print(  f"匹配x：{匹配.rect}")

    # 降魔定位区域=匹配.rect
    # 时间区域=降魔定位区域[0] + 52,降魔定位区域[1] + 191,降魔定位区域[0] + 167,降魔定位区域[1] + 226
    # 时间文字=识别器.recognize_text(截图,时间区域)
    # print(f"   时间: {时间文字}")

    # 拖拽区域 =区域.行会.人员名单拖动区域.元组

    # 拖拽范围=拖拽区域[0],拖拽区域[3],拖拽区域[2],拖拽区域[1]
    # 鼠标模拟器.drag(拖拽区域[0],拖拽区域[3],拖拽区域[2],拖拽区域[3]-280)
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
    
    info=区域.炼器宝阁.炼器宝阁宝阁信息区域.元组
    # print(info)
   
    # info = 缩放区域(info, 1.2)
    # print(缩放)
    # # 5. 获取详细结果（带坐标）
    # print("\n[5] 获取详细识别结果（带坐标）...")
    filter_config = {
                # "color_range": "110,255,0,16,0,16|0,25,150,255,0,16",  
                "color_range": "110,255,0,16,0,16|130,170,18,35,18,35",  
                # "color_diff": "5-80,255,80,255,80,255",
                "keep_color": True,
                "background": "black"
            }
    时间=time.time()
    ocr_result = 识别器.recognize_result(截图,info,filter_config)
    print(f"识别时间：{time.time()-时间}")
    tex=ocr_result.get_all_texts()

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



if __name__ == "__main__":
    # 运行基础测试
    # test_ocr()
    
    # 可选：运行特定区域测试
    # test_特定区域列表()
    
    # 可选：运行连续识别测试
    # test_连续识别()
    候选 = 分析图片生成规则(
        "目标.bmp",
        "噪点.bmp",
        聚类数范围=(1, 6),
        扩展值列表=[3, 5, 8, 12, 18],
        显示数量=15
    )

    # 挑选最优的
    最优 = 候选[0]
    print(最优["color_range"])
    print(最优["filter_config"])