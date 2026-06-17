# core/recognition/pixel_detector.py
"""
像素分析模块

功能：
1. 颜色转换工具（HEX ↔ BGR）
2. 纯色检测
3. 颜色匹配计数
4. 单点取色
"""
import cv2
import numpy as np
import math
from typing import List, Tuple, Optional, Union
from core.debug import 调试器


class PixelAnalyzer:
    """像素分析模块"""
    
    # 最大颜色距离（RGB 空间欧氏距离最大值）
    MAX_COLOR_DISTANCE = math.sqrt(255**2 + 255**2 + 255**2)  # ≈ 441.67
    
    def __init__(self):
        pass
    
    # ==================== 颜色转换工具 ====================
    
    def _hex_to_bgr(self, hex_color: str) -> Tuple[int, int, int]:
        """
        将 BGR 16位值转换为 BGR 元组
        
        参数:
            hex_color: 6位十六进制字符串，如 "0000ff" 表示红色
        
        返回:
            (b, g, r) 元组，每个值 0-255
        """
        if len(hex_color) != 6:
            raise ValueError(f"颜色值必须是6位十六进制，当前: {hex_color}")
        
        b = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        r = int(hex_color[4:6], 16)
        return (b, g, r)
    
    def _bgr_to_hex(self, bgr: Tuple[int, int, int]) -> str:
        """
        将 BGR 元组转换为 BGR 16位值
        
        参数:
            bgr: (b, g, r) 元组
        
        返回:
            6位十六进制字符串，如 "0000ff" 表示红色
        """
        b, g, r = bgr
        return f"{b:02x}{g:02x}{r:02x}"
    
    def _color_distance(self, bgr1: Tuple[int, int, int], 
                        bgr2: Tuple[int, int, int]) -> float:
        """
        计算两个颜色的欧氏距离
        
        参数:
            bgr1, bgr2: (b, g, r) 元组
        
        返回:
            欧氏距离 (0 ~ 441.67)
        """
        b1, g1, r1 = bgr1
        b2, g2, r2 = bgr2
        return math.sqrt((b1 - b2)**2 + (g1 - g2)**2 + (r1 - r2)**2)
    
    def _color_similarity(self, bgr1: Tuple[int, int, int], 
                          bgr2: Tuple[int, int, int]) -> float:
        """
        计算两个颜色的相似度 (0-1)
        
        1 = 完全相同
        0 = 完全不同
        """
        distance = self._color_distance(bgr1, bgr2)
        similarity = 1 - (distance / self.MAX_COLOR_DISTANCE)
        return max(0.0, min(1.0, similarity))
    
    def _parse_rules(self, rules: str) -> List[Tuple[Tuple[int, int, int], float]]:
        """
        解析颜色匹配规则
        
        格式: "目标颜色,相似度|目标颜色,相似度|..."
        
        参数:
            rules: 规则字符串，如 "0000ff,0.9|00ff00,0.8"
        
        返回:
            [(目标颜色BGR元组, 相似度阈值), ...]
        """
        if not rules:
            return []
        
        parsed = []
        for part in rules.split('|'):
            part = part.strip()
            if not part:
                continue
            
            if ',' not in part:
                raise ValueError(f"规则格式错误，缺少逗号: {part}")
            
            color_str, threshold_str = part.split(',', 1)
            color_str = color_str.strip()
            threshold_str = threshold_str.strip()
            
            if len(color_str) != 6:
                raise ValueError(f"颜色值必须是6位十六进制，当前: {color_str}")
            
            try:
                threshold = float(threshold_str)
            except ValueError:
                raise ValueError(f"相似度阈值必须是数字，当前: {threshold_str}")
            
            if not (0 <= threshold <= 1):
                raise ValueError(f"相似度阈值必须在0-1之间，当前: {threshold}")
            
            bgr = self._hex_to_bgr(color_str)
            parsed.append((bgr, threshold))
        
        return parsed
    
    def _parse_points(self, points: str) -> List[Tuple[int, int]]:
        """
        解析点坐标
        
        格式: "x,y|x,y|..."
        
        参数:
            points: 点坐标字符串，如 "100,100|200,150|300,200"
        
        返回:
            [(x, y), ...]
        """
        if not points:
            return []
        
        parsed = []
        for part in points.split('|'):
            part = part.strip()
            if not part:
                continue
            
            if ',' not in part:
                raise ValueError(f"点坐标格式错误，缺少逗号: {part}")
            
            x_str, y_str = part.split(',', 1)
            
            try:
                x = int(x_str.strip())
                y = int(y_str.strip())
            except ValueError:
                raise ValueError(f"坐标必须是整数，当前: {part}")
            
            parsed.append((x, y))
        
        return parsed
    
    # ==================== 核心功能 ====================
    
    def is_solid(self, img: np.ndarray, 
                 region: Tuple[int, int, int, int]) -> Tuple[bool, Optional[str]]:
        """
        纯色检测 - 判断区域内所有像素是否完全相同
        
        参数:
            img: 输入图像 (BGR)
            region: 区域 (left, top, right, bottom)
        
        返回:
            (是否纯色, 颜色值如"0000ff" 或 None)
        """
        if img is None:
            return (False, None)
        
        left, top, right, bottom = region
        h, w = img.shape[:2]
        
        # 边界检查
        left = max(0, min(left, w))
        right = max(left, min(right, w))
        top = max(0, min(top, h))
        bottom = max(top, min(bottom, h))
        
        if left >= right or top >= bottom:
            return (False, None)
        
        # 提取区域
        roi = img[top:bottom, left:right]
        
        if roi.size == 0:
            return (False, None)
        
        # 取第一个像素的颜色
        first_pixel = roi[0, 0]
        
        # 检查所有像素是否相同
        if np.all(roi == first_pixel):
            color_hex = self._bgr_to_hex(tuple(first_pixel))
            return (True, color_hex)
        
        return (False, None)
    
    def count_colors(self, img: np.ndarray,
                     region: Tuple[int, int, int, int],
                     rules: str) -> List[int]:
        """
        颜色匹配计数 - 统计区域内符合颜色规则的像素数量
        
        参数:
            img: 输入图像 (BGR)
            region: 区域 (left, top, right, bottom)
            rules: 规则字符串，如 "0000ff,0.9|00ff00,0.8"
        
        返回:
            每个规则对应的像素数量列表
        """
        if img is None or not rules:
            return []
        
        left, top, right, bottom = region
        h, w = img.shape[:2]
        
        # 边界检查
        left = max(0, min(left, w))
        right = max(left, min(right, w))
        top = max(0, min(top, h))
        bottom = max(top, min(bottom, h))
        
        if left >= right or top >= bottom:
            return [0] * len(rules.split('|')) if rules else []
        
        # 提取区域
        roi = img[top:bottom, left:right]
        
        if roi.size == 0:
            return [0] * len(rules.split('|')) if rules else []
        
        # 解析规则
        parsed_rules = self._parse_rules(rules)
        
        if not parsed_rules:
            return []
        
        # 对每个规则进行统计
        results = []
        
        for target_bgr, threshold in parsed_rules:
            # 计算每个像素与目标颜色的相似度（向量化计算）
            
            # 分离通道
            b = roi[:, :, 0].astype(np.float32)
            g = roi[:, :, 1].astype(np.float32)
            r = roi[:, :, 2].astype(np.float32)
            
            # 计算欧氏距离
            db = b - target_bgr[0]
            dg = g - target_bgr[1]
            dr = r - target_bgr[2]
            
            distances = np.sqrt(db*db + dg*dg + dr*dr)
            
            # 计算相似度
            similarities = 1 - (distances / self.MAX_COLOR_DISTANCE)
            similarities = np.clip(similarities, 0, 1)
            
            # 统计满足阈值的像素数
            count = np.sum(similarities >= threshold)
            results.append(int(count))
        
        return results
    
    def count_colors_by_range(self, img: np.ndarray,
                          region: Tuple[int, int, int, int],
                          rules: str) -> List[int]:
        """
        颜色区间匹配计数
        
        参数:
            img: 输入图像 (BGR)
            region: 区域 (left, top, right, bottom)
            rules: 规则字符串
                格式: "r_low,r_high,g_low,g_high,b_low,b_high|..."
                示例: "0,255,0,255,0,255|200,255,0,50,0,50"
        
        返回:
            每个区间规则对应的像素数量列表
        """
        if img is None or not rules:
            return []
        
        left, top, right, bottom = region
        h, w = img.shape[:2]
        
        left = max(0, min(left, w))
        right = max(left, min(right, w))
        top = max(0, min(top, h))
        bottom = max(top, min(bottom, h))
        
        if left >= right or top >= bottom:
            return []
        
        roi = img[top:bottom, left:right]
        if roi.size == 0:
            return []
        
        # 分离通道（注意 OpenCV BGR）
        b = roi[:, :, 0]
        g = roi[:, :, 1]
        r = roi[:, :, 2]
        
        results = []
        for part in rules.split('|'):
            part = part.strip()
            if not part:
                continue
            
            values = [x.strip() for x in part.split(',')]
            if len(values) != 6:
                results.append(0)
                continue
            
            try:
                nums = [int(v) for v in values]
            except ValueError:
                results.append(0)
                continue
            
            r_low, r_high = min(nums[0], nums[1]), max(nums[0], nums[1])
            g_low, g_high = min(nums[2], nums[3]), max(nums[2], nums[3])
            b_low, b_high = min(nums[4], nums[5]), max(nums[4], nums[5])
            
            condition = (
                (r >= r_low) & (r <= r_high) &
                (g >= g_low) & (g <= g_high) &
                (b >= b_low) & (b <= b_high)
            )
            results.append(int(np.sum(condition)))
        
        return results
    
    def get_colors(self, img: np.ndarray,
                   points: str) -> List[str]:
        """
        单点取色 - 获取指定坐标点的颜色值
        
        参数:
            img: 输入图像 (BGR)
            points: 点坐标字符串，如 "100,100|200,150|300,200"
        
        返回:
            颜色值列表，如 ["0000ff", "00ff00", "ffffff"]
        """
        if img is None or not points:
            return []
        
        h, w = img.shape[:2]
        
        # 解析点坐标
        parsed_points = self._parse_points(points)
        
        if not parsed_points:
            return []
        
        # 获取每个点的颜色
        results = []
        for x, y in parsed_points:
            # 边界检查
            if 0 <= x < w and 0 <= y < h:
                bgr = tuple(img[y, x])
                color_hex = self._bgr_to_hex(bgr)
                results.append(color_hex)
            else:
                # 超出边界
                调试器.warning("像素分析", f"点 ({x}, {y}) 超出图像范围 ({w}x{h})")
                results.append(None)
        
        return results


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("像素分析模块测试")
    print("=" * 50)
    
    # 创建测试图像
    test_img = np.zeros((200, 200, 3), dtype=np.uint8)
    
    # 绘制红色方块 (B=0, G=0, R=255)
    test_img[50:100, 50:100] = (0, 0, 255)
    
    # 绘制绿色方块 (B=0, G=255, R=0)
    test_img[50:100, 120:170] = (0, 255, 0)
    
    # 绘制白色区域 (B=255, G=255, R=255)
    test_img[120:170, 50:100] = (255, 255, 255)
    
    # 绘制混合区域
    test_img[120:170, 120:170] = (100, 150, 200)
    
    analyzer = PixelAnalyzer()
    
    # 测试1: 纯色检测
    print("\n测试1: 纯色检测")
    
    is_solid, color = analyzer.is_solid(test_img, (50, 50, 100, 100))
    print(f"  红色区域: 纯色={is_solid}, 颜色={color}")
    
    is_solid, color = analyzer.is_solid(test_img, (120, 120, 170, 170))
    print(f"  混合区域: 纯色={is_solid}, 颜色={color}")
    
    # 测试2: 颜色匹配计数
    print("\n测试2: 颜色匹配计数")
    
    counts = analyzer.count_colors(test_img, (0, 0, 200, 200), "0000ff,0.9")
    print(f"  红色像素: {counts[0]}")
    
    counts = analyzer.count_colors(test_img, (0, 0, 200, 200), "00ff00,0.9")
    print(f"  绿色像素: {counts[0]}")
    
    counts = analyzer.count_colors(test_img, (0, 0, 200, 200), "ffffff,0.9")
    print(f"  白色像素: {counts[0]}")
    
    counts = analyzer.count_colors(test_img, (0, 0, 200, 200), "0000ff,0.9|00ff00,0.9|ffffff,0.9")
    print(f"  多规则结果: {counts}")
    
    # 测试3: 单点取色
    print("\n测试3: 单点取色")
    
    colors = analyzer.get_colors(test_img, "75,75|75,145|145,75|145,145")
    print(f"  各点颜色: {colors}")
    
    # 测试4: 相似度计算验证
    print("\n测试4: 相似度计算")
    
    sim = analyzer._color_similarity((0, 0, 255), (0, 0, 255))
    print(f"  完全相同: {sim:.4f}")
    
    sim = analyzer._color_similarity((0, 0, 255), (0, 255, 0))
    print(f"  红色 vs 绿色: {sim:.4f}")
    
    sim = analyzer._color_similarity((0, 0, 255), (0, 0, 200))
    print(f"  红色 vs 暗红色: {sim:.4f}")
    
    # 测试5: 边界情况
    print("\n测试5: 边界情况")
    
    counts = analyzer.count_colors(test_img, (0, 0, 0, 0), "0000ff,0.9")
    print(f"  空区域计数: {counts}")
    
    try:
        counts = analyzer.count_colors(test_img, (0, 0, 200, 200), "invalid")
    except Exception as e:
        print(f"  无效规则捕获: {e}")
    
    colors = analyzer.get_colors(test_img, "1000,1000")
    print(f"  超出边界点: {colors}")
    
    print("\n测试完成")