# core/recognition/ocr.py
"""
OCR 文字识别模块

功能：
1. UmiOCR HTTP 客户端封装
2. OCRResult 结果管理器（支持文字查找、区域筛选）
3. TextRecognizer 业务识别器（支持像素过滤）
4. PixelFilter 像素过滤器
"""
import cv2
import numpy as np
import base64
import requests
import time
from typing import List, Tuple, Union, Optional, Dict

from rich.repr import T
from core.utils import 匹配分组关键字
from core.debug import 调试器


# ==================== ROI 裁剪工具 ====================

def crop_roi(img: np.ndarray, region: Tuple[int, int, int, int], 
             format_type: str = "ltrb") -> Tuple[np.ndarray, int, int]:
    """
    裁剪 ROI 区域
    
    参数:
        img: 输入图像 (BGR)
        region: 4个整数
        format_type: "xywh" = (x, y, width, height)
                    "ltrb" = (left, top, right, bottom)
    
    返回:
        (裁剪后的图像, offset_x, offset_y)
    """
    if len(region) != 4:
        raise ValueError(f"region 必须是4个整数，当前长度: {len(region)}")
    
    h_img, w_img = img.shape[:2]
    
    if format_type == "xywh":
        x, y, w, h = region
        x1, y1 = x, y
        x2, y2 = x + w, y + h
    elif format_type == "ltrb":
        x1, y1, x2, y2 = region
    else:
        raise ValueError(f"不支持的格式类型: {format_type}，请使用 'xywh' 或 'ltrb'")
    
    # 边界检查
    x1 = max(0, min(x1, w_img))
    y1 = max(0, min(y1, h_img))
    x2 = max(x1, min(x2, w_img))
    y2 = max(y1, min(y2, h_img))
    
    if x2 <= x1 or y2 <= y1:
        raise ValueError(f"无效的裁剪区域: ({x1}, {y1}, {x2}, {y2})")
    
    return img[y1:y2, x1:x2], x1, y1


# ==================== 图像工具函数 ====================

def image_to_base64(img: np.ndarray) -> str:
    """
    将 OpenCV 图像转为 base64 字符串
    
    参数:
        img: OpenCV 图像 (BGR 格式)
    
    返回:
        base64 编码的 PNG 图片
    """
    # 将 BGR 转为 RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    # 编码为 PNG
    _, buffer = cv2.imencode('.png', img_rgb)
    # 转为 base64
    return base64.b64encode(buffer).decode('utf-8')


# ==================== UmiOCR 底层客户端 ====================

class UmiOCR:
    """UMI-OCR HTTP 客户端 - 只负责通信，返回原始 JSON"""
    
    def __init__(self, url: str = "http://127.0.0.1:1224/api/ocr", 
                 timeout: int = 30,
                 default_options: Optional[dict] = None):
        """
        初始化 UMI-OCR 客户端
        
        参数:
            url: OCR 服务地址
            timeout: 请求超时时间（秒）
            default_options: 默认 OCR 选项，如 {"data.format": "dict"}
        """
        self.url = url
        self.timeout = timeout
        self.default_options = default_options or {"data.format": "dict"}
    
    def recognize_raw(self, image_base64: str, options: Optional[dict] = None) -> dict:
        """
        识别 base64 图片，返回原始 JSON 结果
        
        参数:
            image_base64: base64 编码的图片
            options: OCR 选项，会与默认选项合并
        
        返回:
            原始 JSON 字典
        """
        # 合并选项
        merge_options = self.default_options.copy()
        if options:
            merge_options.update(options)
        
        data = {
            "base64": image_base64,
            "options": merge_options
        }
        
        try:
            start = time.perf_counter()
            response = requests.post(self.url, json=data, timeout=self.timeout)
            elapsed = (time.perf_counter() - start) * 1000
            
            if response.status_code != 200:
                return {
                    "code": response.status_code, 
                    "data": f"HTTP 错误: {response.status_code}",
                    "time": elapsed / 1000
                }
            
            result = response.json()
            # 添加耗时信息
            if "time" not in result:
                result["time"] = elapsed / 1000
            调试器.trace("OCR", f"UMI-OCR 耗时: {elapsed:.1f}ms")
            return result
            
        except requests.exceptions.ConnectionError:
            调试器.error("OCR", "无法连接到 UMI-OCR 服务，请先启动服务: Umi-OCR.exe --http 1224")
            return {
                "code": -1, 
                "data": "无法连接到 UMI-OCR 服务",
                "time": 0
            }
        except requests.exceptions.Timeout:
            调试器.error("OCR", f"OCR请求超时 ({self.timeout}s)")
            return {
                "code": -1, 
                "data": f"请求超时 ({self.timeout}s)",
                "time": self.timeout
            }
        except Exception as e:
            调试器.error("OCR", f"OCR请求异常: {e}")
            return {
                "code": -1, 
                "data": str(e),
                "time": 0
            }
    
    def recognize_image_raw(self, image: np.ndarray, options: Optional[dict] = None) -> dict:
        """
        识别 OpenCV 图像，返回原始 JSON 结果
        
        参数:
            image: OpenCV 图像 (BGR)
            options: OCR 选项
        
        返回:
            原始 JSON 字典
        """
        img_base64 = image_to_base64(image)
        return self.recognize_raw(img_base64, options)
    
    def recognize_file_raw(self, image_path: str, options: Optional[dict] = None) -> dict:
        """
        识别图片文件，返回原始 JSON 结果
        
        参数:
            image_path: 图片文件路径
            options: OCR 选项
        
        返回:
            原始 JSON 字典
        """
        with open(image_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')
        return self.recognize_raw(img_base64, options)

    def ping(self) -> bool:
        """检查 OCR 服务是否可用"""
        try:
            response = requests.get(self.url.replace('/api/ocr', '/'), timeout=2)
            return response.status_code == 200
        except:
            return False

# ==================== OCRResult 结果管理器 ====================

class OCRResult:
    """OCR 结果管理器，支持文本查找（有序列表版本）"""
    
    def __init__(self, items: List[Tuple[str, Tuple[int, int, int, int]]] = None):
        """
        初始化
        
        参数:
            items: 文本和坐标的列表，格式 [(text, (left, top, right, bottom)), ...]
                   保持识别顺序
        """
        self.items = items if items is not None else []
        
        # 为了快速查找，同时维护一个字典索引（可选）
        self._index: Dict[str, List[int]] = {}
        self._rebuild_index()
    
    def _rebuild_index(self):
        """重建索引（用于快速查找）"""
        self._index.clear()
        for i, (text, box) in enumerate(self.items):
            if text not in self._index:
                self._index[text] = []
            self._index[text].append(i)
    
    @classmethod
    def from_umi_result(cls, result: dict) -> 'OCRResult':
        """
        从 UMI-OCR 原始 JSON 结果创建
        
        参数:
            result: UMI-OCR API 返回的 JSON 字典
        
        返回:
            OCRResult 实例
        """
        code = result.get("code", 0)
        if code != 100:
            return cls()
        
        data = result.get("data", [])
        if not isinstance(data, list):
            return cls()
        
        items = []
        for item in data:
            text = item.get("text", "")
            if not text:
                continue
            
            # 获取坐标
            box = item.get("box", [])
            if len(box) == 4:
                xs = [p[0] for p in box]
                ys = [p[1] for p in box]
                bbox = (min(xs), min(ys), max(xs), max(ys))
            else:
                continue
            
            items.append((text, bbox))
        
        return cls(items)
    
    def find(self, 
             keywords: Union[str, List[str]], 
             match_type: str = "group",
             return_all: bool = False) -> Union[Optional[Tuple[int, int, int, int]], List[Tuple[int, int, int, int]]]:
        """
        查找文字对应的坐标（按出现顺序返回）
        
        参数:
            keywords: 要查找的关键字，可以是字符串或字符串列表
            match_type: 匹配方式
                       - "exact": 完全匹配
                       - "contains": 包含关键字
                       - "group": 匹配关键字组规则（默认，兼容contains）
                       - "startswith": 以关键字开头
                       - "endswith": 以关键字结尾
                       - "regex": 正则表达式匹配
            return_all: True=返回所有匹配坐标列表，False=返回第一个匹配坐标
        
        返回:
            当 return_all=False: 返回第一个匹配的坐标 (left, top, right, bottom)，找不到返回 None
            当 return_all=True: 返回所有匹配的坐标列表，找不到返回空列表
        """
        if isinstance(keywords, str):
            keywords = [keywords]
        
        matched_boxes = []
        
        for text, box in self.items:
            for keyword in keywords:
                matched = False
                if match_type == "exact":
                    matched = (text == keyword)
                elif match_type == "contains":
                    matched = (keyword in text)
                elif match_type == "startswith":
                    matched = text.startswith(keyword)
                elif match_type == "endswith":
                    matched = text.endswith(keyword)
                elif match_type == "regex":
                    try:
                        import re
                        matched = bool(re.search(keyword, text))
                    except re.error:
                        调试器.warning("OCR", f"无效的正则表达式: {keyword}")
                        matched = False
                elif match_type == "group":
                    matched = 匹配分组关键字(text, keyword)          
                else:
                    raise ValueError(f"不支持的匹配方式: {match_type}")
                
                if matched:
                    matched_boxes.append(box)
                    break  # 匹配到一个关键字即可，跳出关键字循环
        
        # 去重（保留顺序）
        seen = set()
        unique_boxes = []
        for box in matched_boxes:
            if box not in seen:
                seen.add(box)
                unique_boxes.append(box)
        
        if return_all:
            return unique_boxes
        else:
            return unique_boxes[0] if unique_boxes else None
    
    def find_with_text(self, 
                       keywords: Union[str, List[str]], 
                       match_type: str = "contains",
                       return_all: bool = False) -> Union[Optional[Tuple[str, Tuple[int, int, int, int]]], 
                                                           List[Tuple[str, Tuple[int, int, int, int]]]]:
        """
        查找文字对应的坐标，同时返回匹配的文本（按出现顺序返回）
        
        参数:
            keywords: 要查找的关键字
            match_type: 匹配方式
            return_all: 是否返回所有结果
        
        返回:
            当 return_all=False: (匹配文本, 坐标) 或 None
            当 return_all=True: [(匹配文本, 坐标), ...] 列表
        """
        if isinstance(keywords, str):
            keywords = [keywords]
        
        matched = []
        
        for text, box in self.items:
            for keyword in keywords:
                matched_flag = False
                if match_type == "exact":
                    matched_flag = (text == keyword)
                elif match_type == "contains":
                    matched_flag = (keyword in text)
                elif match_type == "startswith":
                    matched_flag = text.startswith(keyword)
                elif match_type == "endswith":
                    matched_flag = text.endswith(keyword)
                elif match_type == "regex":
                    try:
                        import re
                        matched_flag = bool(re.search(keyword, text))
                    except re.error:
                        continue
                elif match_type == "group":
                    matched_flag = 匹配分组关键字(text, keyword) 
                if matched_flag:
                    matched.append((text, box))
                    break  # 匹配到一个关键字即可
        
        # 去重（保留顺序）
        seen = set()
        unique_matched = []
        for item in matched:
            key = (item[0], item[1])
            if key not in seen:
                seen.add(key)
                unique_matched.append(item)
        
        if return_all:
            return unique_matched
        else:
            return unique_matched[0] if unique_matched else None
    
    def find_all_by_text(self, text: str) -> List[Tuple[int, int, int, int]]:
        """
        查找指定文本的所有出现位置（按出现顺序）
        
        参数:
            text: 要查找的文本
        
        返回:
            坐标列表，按出现顺序
        """
        boxes = []
        for t, box in self.items:
            if t == text:
                boxes.append(box)
        return boxes
    
    def get_all_texts(self) -> List[str]:
        """获取所有识别的文本（按出现顺序）"""
        return [text for text, _ in self.items]
    
    def get_all_text(self, separator: str = "") -> str:
        """获取所有文本的合并结果（按出现顺序）"""
        return separator.join(self.get_all_texts())
    
    def get_all_boxes(self) -> List[Tuple[int, int, int, int]]:
        """获取所有坐标（按出现顺序）"""
        return [box for _, box in self.items]
    
    def get_all_items(self) -> List[Tuple[str, Tuple[int, int, int, int]]]:
        """获取所有识别项（按出现顺序）"""
        return self.items.copy()
    
    def get_text_by_box(self, box: Tuple[int, int, int, int]) -> Optional[str]:
        """
        根据坐标查找对应的文本
        
        参数:
            box: 坐标 (left, top, right, bottom)
        
        返回:
            匹配的文本，找不到返回 None
        """
        for text, b in self.items:
            if b == box:
                return text
        return None
    
    def get_position(self, index: int) -> Optional[Tuple[str, Tuple[int, int, int, int]]]:
        """
        根据索引获取识别项
        
        参数:
            index: 索引（从0开始）
        
        返回:
            (文本, 坐标) 或 None
        """
        if 0 <= index < len(self.items):
            return self.items[index]
        return None
    
    def filter_by_region(self, region: Tuple[int, int, int, int]) -> 'OCRResult':
        """
        按区域筛选识别结果
        
        参数:
            region: (left, top, right, bottom)
        
        返回:
            新的 OCRResult 实例，只包含区域内或与区域相交的识别项
        """
        l, t, r, b = region
        filtered = []
        for text, box in self.items:
            bl, bt, br, bd = box
            # 检查是否有交集
            if not (br <= l or bl >= r or bd <= t or bt >= b):
                filtered.append((text, box))
        return OCRResult(filtered)
    
    def __len__(self) -> int:
        """返回识别的文本数量"""
        return len(self.items)
    
    def __bool__(self) -> bool:
        """判断是否有识别结果"""
        return len(self.items) > 0
    
    def __getitem__(self, index: int) -> Tuple[str, Tuple[int, int, int, int]]:
        """支持索引访问"""
        return self.items[index]
    
    def __iter__(self):
        """支持迭代"""
        return iter(self.items)
    
    def __repr__(self) -> str:
        return f"OCRResult({len(self.items)} 个文本项)"
    
    def print_items(self, max_items: int = 20):
        """打印识别项（调试用）"""
        print(f"\nOCR识别结果（共 {len(self.items)} 项）:")
        print("-" * 60)
        for i, (text, box) in enumerate(self.items[:max_items]):
            print(f"  [{i}] '{text}' -> {box}")
        if len(self.items) > max_items:
            print(f"  ... 还有 {len(self.items) - max_items} 项")
        print("-" * 60)


# ==================== 像素过滤器 ====================

class PixelFilter:
    """高级像素过滤器（向量化版本）"""
    
    def __init__(self):
        self.debug_mode = False
    
    def is_full_range(self, range_str: str) -> bool:
        """判断单个区间是否为全范围"""
        if range_str == "0,255,0,255,0,255":
            return True
        try:
            values = [int(x.strip()) for x in range_str.split(',')]
            if len(values) == 6:
                return (values[0] == 0 and values[1] == 255 and
                        values[2] == 0 and values[3] == 255 and
                        values[4] == 0 and values[5] == 255)
        except:
            pass
        return False
    
    def parse_color_range(self, range_str: str) -> List[Tuple[Tuple[int, int], ...]]:
        """
        解析颜色区间参数
        格式: "r_low,r_high,g_low,g_high,b_low,b_high|..."
        返回: 有效区间列表，全范围区间会被过滤掉
        """
        ranges = []
        
        for part in range_str.split('|'):
            # 跳过全范围区间
            if self.is_full_range(part):
                continue
            
            values = [int(x.strip()) for x in part.split(',')]
            
            if len(values) != 6:
                raise ValueError(f"颜色区间参数必须包含6个数值，当前: {len(values)}")
            
            r_low, r_high, g_low, g_high, b_low, b_high = values
            
            # 验证数值范围
            for val in values:
                if not 0 <= val <= 255:
                    raise ValueError(f"RGB值必须在0-255之间，当前: {val}")
            
            # 确保低值小于高值
            r_low, r_high = min(r_low, r_high), max(r_low, r_high)
            g_low, g_high = min(g_low, g_high), max(g_low, g_high)
            b_low, b_high = min(b_low, b_high), max(b_low, b_high)
            
            ranges.append((
                (r_low, r_high),
                (g_low, g_high),
                (b_low, b_high)
            ))
        
        return ranges
    
    def parse_color_diff(self, diff_str: str) -> Optional[Tuple[int, Optional[List], Optional[str]]]:
        """
        解析颜色差参数
        格式: "阈值-RGB区间参数"
        返回: (阈值, diff_ranges, 错误信息) 或 None
        """
        if not diff_str:
            return None
        
        if '-' not in diff_str:
            return None
        
        threshold_part, range_part = diff_str.split('-', 1)
        
        try:
            threshold = int(threshold_part.strip())
        except ValueError:
            return None  # 解析失败，跳过 diff 筛选
        
        # 解析 diff 区间，如果解析失败则 diff_ranges 为空（表示全域差值判断）
        try:
            diff_ranges = self.parse_color_range(range_part)
        except Exception:
            diff_ranges = []  # 解析失败，使用全域差值判断
        
        return (threshold, diff_ranges, range_part)
    
    def filter_pixels(self, img: np.ndarray, 
                      color_range_str: str = "0,255,0,255,0,255",
                      color_diff_str: Optional[str] = None,
                      keep_color: bool = True,
                      background_color: Union[str, Tuple[int, int, int]] = 'black') -> np.ndarray:
        """
        向量化像素过滤函数
        
        筛选逻辑: 保留满足 color_range 或 color_diff 条件的像素（并集）
        """
        result = img.copy()
        
        # 解析颜色区间参数（空集表示无有效区间）
        ranges = self.parse_color_range(color_range_str)
        has_range_filter = len(ranges) > 0

        # 解析颜色差参数
        diff_threshold = None
        diff_ranges = None
        has_diff_filter = False
        
        if color_diff_str:
            parsed = self.parse_color_diff(color_diff_str)
            if parsed:
                diff_threshold, diff_ranges, _ = parsed
                has_diff_filter = True
        
        # 如果两个筛选都没有，直接返回原图
        if not has_range_filter and not has_diff_filter:
            return img.copy()
        
        # 分离RGB通道（注意OpenCV是BGR）
        b, g, r = cv2.split(img)
        
        # 条件1: 颜色区间筛选（仅在有效区间存在时计算）
        condition_range = np.zeros(img.shape[:2], dtype=bool)
        if has_range_filter:
            for r_range, g_range, b_range in ranges:
                r_low, r_high = r_range
                g_low, g_high = g_range
                b_low, b_high = b_range
                
                range_condition = (
                    (r >= r_low) & (r <= r_high) &
                    (g >= g_low) & (g <= g_high) &
                    (b >= b_low) & (b <= b_high)
                )
                condition_range = condition_range | range_condition
        
        # 条件2: 颜色差筛选
        condition_diff = np.zeros(img.shape[:2], dtype=bool)
        if has_diff_filter:
            # 计算RGB最大差值
            rgb_max = np.maximum(np.maximum(r, g), b)
            rgb_min = np.minimum(np.minimum(r, g), b)
            rgb_diff = rgb_max - rgb_min
            diff_check = (rgb_diff <= diff_threshold)
            
            # 如果有 diff_ranges，则需要限制在指定区间内
            if diff_ranges and len(diff_ranges) > 0:
                in_diff_range = np.zeros(img.shape[:2], dtype=bool)
                for r_range, g_range, b_range in diff_ranges:
                    r_low, r_high = r_range
                    g_low, g_high = g_range
                    b_low, b_high = b_range
                    
                    range_condition = (
                        (r >= r_low) & (r <= r_high) &
                        (g >= g_low) & (g <= g_high) &
                        (b >= b_low) & (b <= b_high)
                    )
                    in_diff_range = in_diff_range | range_condition
                
                condition_diff = in_diff_range & diff_check
            else:
                # diff_ranges 为空：在全域下进行差值判断
                condition_diff = diff_check
        
        # 最终条件 = 条件1 或 条件2（并集）
        if has_range_filter and has_diff_filter:
            condition = condition_range | condition_diff
        elif has_range_filter:
            condition = condition_range
        else:
            condition = condition_diff
        
        # 获取背景色
        bg_color = self._get_background_color(background_color)
        
        # 应用掩码
        if keep_color:
            result[~condition] = bg_color
        else:
            white = np.array([255, 255, 255], dtype=np.uint8)
            result[condition] = white
            result[~condition] = bg_color
        
        if self.debug_mode:
            mask = condition.astype(np.uint8) * 255
            cv2.imwrite("debug_mask.png", mask)
            if has_range_filter:
                cv2.imwrite("debug_mask_range.png", condition_range.astype(np.uint8) * 255)
            if has_diff_filter:
                cv2.imwrite("debug_mask_diff.png", condition_diff.astype(np.uint8) * 255)
            cv2.imwrite("debug_result.png", result)
            
            total_pixels = condition.size
            range_pixels = np.sum(condition_range) if has_range_filter else 0
            diff_pixels = np.sum(condition_diff) if has_diff_filter else 0
            union_pixels = np.sum(condition)
            
            调试器.debug("像素过滤", f"像素统计: 总={total_pixels}")
            if has_range_filter:
                调试器.debug("像素过滤", f"  颜色区间: {range_pixels} ({range_pixels/total_pixels*100:.2f}%)")
            if has_diff_filter:
                调试器.debug("像素过滤", f"  颜色差: {diff_pixels} ({diff_pixels/total_pixels*100:.2f}%)")
            调试器.debug("像素过滤", f"  并集保留: {union_pixels} ({union_pixels/total_pixels*100:.2f}%)")
        
        return result
    
    def _get_background_color(self, background: Union[str, Tuple[int, int, int]]) -> Tuple[int, int, int]:
        """获取背景色"""
        if background == 'black':
            return (0, 0, 0)
        elif background == 'white':
            return (255, 255, 255)
        elif isinstance(background, tuple) and len(background) == 3:
            return background
        else:
            return (0, 0, 0)

# ==================== TextRecognizer 业务层 ====================

class TextRecognizer:
    """文字识别器，支持像素过滤和结果解析"""
    
    def __init__(self, 
                 ocr_url: str = "http://127.0.0.1:1224/api/ocr", 
                 ocr_timeout: int = 30,
                 ocr_options: Optional[dict] = None):
        """
        初始化文字识别器
        
        参数:
            ocr_url: UMI-OCR 服务地址
            ocr_timeout: OCR 请求超时时间（秒）
            ocr_options: 默认 OCR 选项，如 {"data.format": "dict"}
        """
        self.ocr = UmiOCR(url=ocr_url, timeout=ocr_timeout, default_options=ocr_options)
        self.filter = PixelFilter()
    def _transform_box_coords(self, result: dict, offset_x: int, offset_y: int) -> dict:
        """
        将 JSON 结果中的 box 坐标转换为绝对坐标
        
        参数:
            result: UMI-OCR 原始 JSON
            offset_x, offset_y: 偏移量
        
        返回:
            转换后的 JSON
        """
        if not result:
            return result
        
        code = result.get("code", 0)
        if code != 100:
            return result
        
        data = result.get("data", [])
        if not isinstance(data, list):
            return result
        
        # 转换每个 box 坐标
        new_data = []
        for item in data:
            box = item.get("box", [])
            if len(box) == 4:
                # box 格式: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                new_box = []
                for point in box:
                    new_box.append([point[0] + offset_x, point[1] + offset_y])
                item = item.copy()
                item["box"] = new_box
            new_data.append(item)
        
        result = result.copy()
        result["data"] = new_data
        return result
    def recognize_text(self, 
                       image: np.ndarray,
                       region: Optional[Tuple[int, int, int, int]] = None,                       
                       filter_config: Optional[dict] = None,
                       region_format: str = "ltrb", 放大倍数=1) -> str:
        """
        识别图像中的文字，返回文本
        
        参数:
            image: 输入图像 (BGR格式)
            region: 识别区域，4个整数，None 表示全图
            region_format: 区域格式，"xywh" 或 "ltrb"
            filter_config: 像素过滤配置，可选
        
        返回:
            识别出的文本
        """
        # 1. 裁剪 ROI
        if region is not None:
            roi, _, _ = crop_roi(image, region, region_format)
        else:
            roi = image
        if 放大倍数 > 1:
            h, w = roi.shape[:2]
            roi = cv2.resize(roi, (w * 放大倍数, h * 放大倍数), interpolation=cv2.INTER_CUBIC)
        # 2. 像素过滤（如果配置了）
        if filter_config:
            roi = self._apply_filter(roi, filter_config)
        
        # 3. OCR 识别，获取原始 JSON
        options = {"data.format": "text"}
        result = self.ocr.recognize_image_raw(roi, options)       
        
        # 4. 解析为简单文本
        data = result.get("data")
        
        if result.get("code") != 100:
            return ""
        
        if isinstance(data, str):
            return data
        elif isinstance(data, list):
            # 如果是 dict 格式，合并所有文本
            texts = [item.get("text", "") for item in data if item.get("text")]
            return "".join(texts)
        
        return ""
    
    def recognize_result(self, 
                         image: np.ndarray,
                         region: Optional[Tuple[int, int, int, int]] = None,
                         filter_config: Optional[dict] = None,
                         region_format: str = "ltrb") -> 'OCRResult':
        """
        识别图像中的文字，返回 OCRResult 对象，支持文本查找
        
        参数:
            image: 输入图像 (BGR格式)
            region: 识别区域，4个整数，None 表示全图
            region_format: 区域格式，"xywh" 或 "ltrb"
            filter_config: 像素过滤配置，可选
        
        返回:
            OCRResult 实例
        """
        result = self.recognize_raw(image, region, filter_config, region_format)
        
        return OCRResult.from_umi_result(result)
    
    def recognize_raw(self,
                      image: np.ndarray,
                      region: Optional[Tuple[int, int, int, int]] = None,
                      filter_config: Optional[dict] = None,
                      region_format: str = "ltrb") -> dict:
        """
        识别图像中的文字，返回带坐标的原始 JSON 结果
        
        参数:
            image: 输入图像 (BGR格式)
            region: 识别区域，4个整数，None 表示全图
            region_format: 区域格式，"xywh" 或 "ltrb"
            filter_config: 像素过滤配置，可选
        
        返回:
            UMI-OCR 原始 JSON 字典
        """
        # 1. 裁剪 ROI
        if region is not None:
            roi, offset_x, offset_y = crop_roi(image, region, region_format)
        else:
            roi = image
            offset_x, offset_y = 0, 0
        # 2. 像素过滤（如果配置了）
        if filter_config:
            roi = self._apply_filter(roi, filter_config)
        
        # 3. OCR 识别，返回原始 JSON
        options = {"data.format": "dict"}
        result = self.ocr.recognize_image_raw(roi, options)
        if offset_x != 0 or offset_y != 0:
            result = self._transform_box_coords(result, offset_x, offset_y)        
        return result
    
    def _apply_filter(self, image: np.ndarray, filter_config: dict) -> np.ndarray:
        """应用像素过滤"""
        color_range = filter_config.get("color_range", "0,255,0,255,0,255")
        color_diff = filter_config.get("color_diff")
        keep_color = filter_config.get("keep_color", True)
        background = filter_config.get("background", "black")
        
        return self.filter.filter_pixels(
            image,
            color_range_str=color_range,
            color_diff_str=color_diff,
            keep_color=keep_color,
            background_color=background
        )


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 测试代码保留 print
    img = cv2.imread("debug_screenshot.png")
    
    if img is None:
        print("请确保 debug_screenshot.png 文件存在")
    else:
        recognizer = TextRecognizer()
        
        print("=== 示例1: 获取文本列表 ===")
        texts = recognizer.recognize_text(img, region=(50, 100, 300, 300))
        print(f"文本列表: {texts}")
        
        print("\n=== 示例2: 获取 OCRResult 对象 ===")
        result = recognizer.recognize_result(img, region=(50, 100, 300, 300))
        print(f"识别到 {len(result)} 个文本项")        
        box = result.find("日", return_all=True)
        if box:
            print(f"找到包含'百'的文字，坐标: {box}")
        print(result.get_all_text())
        boxes = result.find("每日可领取100元红包", match_type="exact", return_all=True)
        print(boxes)
        if boxes:
            print(f"找到 {len(boxes)} 个'每日可领取100元红包'按钮")
        
        print("\n=== 示例3: 获取原始 JSON ===")
        raw = recognizer.recognize_raw(img, region=(50, 100, 300, 300))
        print(raw)
        print(f"状态码: {raw.get('code')}")
        print(f"耗时: {raw.get('time')} 秒")
        
        print("\n=== 示例4: 带像素过滤 ===")
        filter_config = {
            "color_range": "200,255,200,255,200,255",
            "keep_color": False,
            "background": "black"
        }
        texts_filtered = recognizer.recognize_text(img, filter_config=filter_config)
        print(f"过滤后文本: {texts_filtered}")