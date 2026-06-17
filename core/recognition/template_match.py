# core/recognition/template_match.py
"""
模板匹配模块

功能：
1. 单模板匹配、多模板匹配
2. 区域工具（IoU、交集计算）
3. 调试工具（可视化匹配结果）
"""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Union
from pathlib import Path
from core.debug import 调试器
from core.utils import 读取图片

# ==================== 数据结构 ====================

@dataclass
class MatchResult:
    """匹配结果"""
    left: int
    top: int
    right: int
    bottom: int
    confidence: float
    
    @property
    def width(self) -> int:
        return self.right - self.left
    
    @property
    def height(self) -> int:
        return self.bottom - self.top
    
    @property
    def center(self) -> Tuple[int, int]:
        return ((self.left + self.right) // 2, 
                (self.top + self.bottom) // 2)
    
    @property
    def rect(self) -> Tuple[int, int, int, int]:
        return (self.left, self.top, self.right, self.bottom)
    
    def to_xywh(self) -> Tuple[int, int, int, int]:
        return (self.left, self.top, self.width, self.height)
    
    def __repr__(self) -> str:
        return f"MatchResult(left={self.left}, top={self.top}, right={self.right}, bottom={self.bottom}, conf={self.confidence:.3f})"


# ==================== 区域工具 ====================

class RegionUtils:
    """区域工具"""
    
    @staticmethod
    def is_overlap(rect1: Tuple[int, int, int, int], 
                   rect2: Tuple[int, int, int, int]) -> bool:
        l1, t1, r1, b1 = rect1
        l2, t2, r2, b2 = rect2
        return not (r1 <= l2 or r2 <= l1 or b1 <= t2 or b2 <= t1)
    
    @staticmethod
    def intersection(rect1: Tuple[int, int, int, int], 
                     rect2: Tuple[int, int, int, int]) -> Optional[Tuple[int, int, int, int]]:
        l1, t1, r1, b1 = rect1
        l2, t2, r2, b2 = rect2
        
        left = max(l1, l2)
        top = max(t1, t2)
        right = min(r1, r2)
        bottom = min(b1, b2)
        
        if left < right and top < bottom:
            return (left, top, right, bottom)
        return None
    
    @staticmethod
    def area(rect: Tuple[int, int, int, int]) -> int:
        left, top, right, bottom = rect
        return (right - left) * (bottom - top)
    
    @staticmethod
    def iou(rect1: Tuple[int, int, int, int], 
            rect2: Tuple[int, int, int, int]) -> float:
        """计算 IoU（交并比）"""
        inter = RegionUtils.intersection(rect1, rect2)
        if not inter:
            return 0.0
        
        inter_area = RegionUtils.area(inter)
        area1 = RegionUtils.area(rect1)
        area2 = RegionUtils.area(rect2)
        
        return inter_area / (area1 + area2 - inter_area)


# ==================== 模板匹配器 ====================

class TemplateMatcher:
    """模板匹配器"""
    
    METHODS = {
        'sqdiff': cv2.TM_SQDIFF,
        'sqdiff_normed': cv2.TM_SQDIFF_NORMED,
        'ccorr': cv2.TM_CCORR,
        'ccorr_normed': cv2.TM_CCORR_NORMED,
        'ccoeff': cv2.TM_CCOEFF,
        'ccoeff_normed': cv2.TM_CCOEFF_NORMED,
    }
    
    def __init__(self, method: Union[str, int] = 'ccoeff_normed'):
        if isinstance(method, str):
            if method not in self.METHODS:
                raise ValueError(f"不支持的匹配方法: {method}")
            self.method = self.METHODS[method]
        else:
            self.method = method
        
        self._is_sqdiff = self.method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]
    
    def _crop_region(self, img: np.ndarray, 
                     region: Optional[Tuple[int, int, int, int]]) -> Tuple[np.ndarray, int, int]:
        if region is None:
            return img, 0, 0
        
        left, top, right, bottom = region
        h, w = img.shape[:2]
        
        left = max(0, min(left, w))
        right = max(left, min(right, w))
        top = max(0, min(top, h))
        bottom = max(top, min(bottom, h))
        
        return img[top:bottom, left:right], left, top
    
    def _normalize_confidence(self, value: float) -> float:
        if self._is_sqdiff:
            return max(0.0, min(1.0, 1.0 / (1.0 + value)))
        else:
            return max(0.0, min(1.0, value))
    
    def _get_local_maxima(self, result: np.ndarray, threshold: float, 
                          min_distance: int) -> List[Tuple[int, int, float]]:
        """
        获取局部最大值点（非极大值抑制）
        
        参数:
            result: 匹配结果矩阵
            threshold: 置信度阈值
            min_distance: 最小距离（像素）
        
        返回:
            [(x, y, confidence), ...]
        """
        h, w = result.shape
        
        # 创建掩码，标记满足阈值的点
        if self._is_sqdiff:
            mask = result <= threshold
        else:
            mask = result >= threshold
        
        if not np.any(mask):
            return []
        
        # 使用膨胀操作找到局部最大值
        if self._is_sqdiff:
            # SQDIFF: 值越小越好，找局部最小值
            neg_result = -result
            kernel_size = min_distance * 2 + 1
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            dilated = cv2.dilate(neg_result, kernel)
            local_max = (neg_result == dilated) & mask
        else:
            # 其他方法: 值越大越好，找局部最大值
            kernel_size = min_distance * 2 + 1
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            dilated = cv2.dilate(result, kernel)
            local_max = (result == dilated) & mask
        
        # 提取局部最大值点
        ys, xs = np.where(local_max)
        
        candidates = []
        for x, y in zip(xs, ys):
            val = result[y, x]
            confidence = self._normalize_confidence(val)
            candidates.append((x, y, confidence))
        
        # 按置信度降序排序
        candidates.sort(key=lambda c: c[2], reverse=True)
        
        return candidates
    
    def match_bypicture(self, img: np.ndarray, path: str,
              threshold: float = 0.8,
              region: Optional[Tuple[int, int, int, int]] = None) -> Optional[MatchResult]:
        """单模板匹配，返回最佳匹配"""
       
        template=读取图片(path)
        if template is None:
            return None
        return self.match(img, template, threshold, region) 

    def match(self, img: np.ndarray, template: np.ndarray,
              threshold: float = 0.8,
              region: Optional[Tuple[int, int, int, int]] = None) -> Optional[MatchResult]:
        """单模板匹配，返回最佳匹配"""
        if img is None or template is None:
            return None
        
        h_img, w_img = img.shape[:2]
        h_tpl, w_tpl = template.shape[:2]
        
        if h_tpl > h_img or w_tpl > w_img:
            return None
        
        search_img, offset_x, offset_y = self._crop_region(img, region)
        
        h_search, w_search = search_img.shape[:2]
        if h_tpl > h_search or w_tpl > w_search:
            return None
        
        # 执行模板匹配
        result = cv2.matchTemplate(search_img, template, self.method)
        
        # 找到最佳匹配位置
        if self._is_sqdiff:
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            best_val = min_val
            best_loc = min_loc
        else:
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            best_val = max_val
            best_loc = max_loc
        
        confidence = self._normalize_confidence(best_val)
        
        if confidence < threshold:
            return None
        
        left = best_loc[0] + offset_x
        top = best_loc[1] + offset_y
        right = left + w_tpl
        bottom = top + h_tpl
        
        return MatchResult(left, top, right, bottom, confidence)
    

    def match_all_bypicture(self, img: np.ndarray, path: str,
                  threshold: float = 0.8,
                  region: Optional[Tuple[int, int, int, int]] = None,
                  max_results: int = 10,
                  min_distance: int = 10) -> List[MatchResult]:
        """
        返回所有匹配结果
        
        参数:
            img: 大图
            template: 模板
            threshold: 置信度阈值
            region: 限定搜索区域
            max_results: 最大返回结果数
            min_distance: 两个匹配之间的最小距离（像素）
        
        返回:
            按 (left, top) 排序的 MatchResult 列表
        """
        template=读取图片(path)
        if template is None:
            return []
        return self.match_all(img, template, threshold, region,max_results,min_distance)
    def match_all(self, img: np.ndarray, template: np.ndarray,
                  threshold: float = 0.8,
                  region: Optional[Tuple[int, int, int, int]] = None,
                  max_results: int = 10,
                  min_distance: int = 10) -> List[MatchResult]:
        """
        返回所有匹配结果
        
        参数:
            img: 大图
            template: 模板
            threshold: 置信度阈值
            region: 限定搜索区域
            max_results: 最大返回结果数
            min_distance: 两个匹配之间的最小距离（像素）
        
        返回:
            按 (left, top) 排序的 MatchResult 列表
        """
        if img is None or template is None:
            return []
        
        h_img, w_img = img.shape[:2]
        h_tpl, w_tpl = template.shape[:2]
        
        if h_tpl > h_img or w_tpl > w_img:
            return []
        
        search_img, offset_x, offset_y = self._crop_region(img, region)
        
        h_search, w_search = search_img.shape[:2]
        if h_tpl > h_search or w_tpl > w_search:
            return []
        
        # 执行模板匹配
        result = cv2.matchTemplate(search_img, template, self.method)
        
        # 获取局部最大值点
        candidates = self._get_local_maxima(result, threshold, min_distance)
        
        if not candidates:
            return []
        
        # 转换为 MatchResult
        matches = []
        for x, y, conf in candidates:
            matches.append(MatchResult(
                left=x + offset_x,
                top=y + offset_y,
                right=x + offset_x + w_tpl,
                bottom=y + offset_y + h_tpl,
                confidence=conf
            ))
        
        # 按置信度降序排序，取前 max_results
        matches.sort(key=lambda m: m.confidence, reverse=True)
        matches = matches[:max_results]
        
        # # 按 (left, top) 排序（从左到右，从上到下）
        # matches.sort(key=lambda m: (m.left, m.top))
        
        # return matches
         # 去重：重叠的保留置信度最高的
         
        print(f"去重前: {len(matches)}个")  
        去重后 = []
        for m in matches:
            重叠 = False
            for k in 去重后:
                if abs(m.center[0] - k.center[0]) < min_distance and \
                abs(m.center[1] - k.center[1]) < min_distance:
                    重叠 = True
                    break
            if not 重叠:
                去重后.append(m)
        
        去重后.sort(key=lambda m: (m.left, m.top))
        return 去重后
    
    def match_multiple(self, img: np.ndarray, 
                       templates: Dict[str, np.ndarray],
                       threshold: float = 0.8,
                       region: Optional[Tuple[int, int, int, int]] = None,
                       max_results_per_template: int = 5,
                       min_distance: int = 10) -> Dict[str, List[MatchResult]]:
        """多模板匹配"""
        results = {}
        
        for name, template in templates.items():
            matches = self.match_all(
                img, template, threshold, region,
                max_results_per_template, min_distance
            )
            if matches:
                results[name] = matches
        
        return results
    def match_multiple_flat(self, img: np.ndarray, 
                        templates: Dict[str, np.ndarray],
                        threshold: float = 0.8,
                        region: Optional[Tuple[int, int, int, int]] = None,
                        max_results_per_template: int = 5,
                        min_distance: int = 10) -> List[MatchResult]:
        """
        多模板匹配，返回按坐标排序的扁平列表
        
        返回:
            按坐标排序的 MatchResult 列表（不包含模板名称）
        """
        grouped = self.match_multiple(
            img, templates, threshold, region,
            max_results_per_template, min_distance
        )
        
        all_matches = []
        for matches in grouped.values():
            all_matches.extend(matches)
        
        all_matches.sort(key=lambda m: (m.left, m.top))
        return all_matches
    
    def match_multiple_bypictures(self, img: np.ndarray, 
                   template_paths: Tuple[str, ...],
                   threshold: float = 0.8,
                   region: Optional[Tuple[int, int, int, int]] = None,
                   max_results_per_template: int = 5,
                   min_distance: int = 10) -> Dict[str, List[MatchResult]]:
        """多模板匹配"""
        from core.utils import 读取图片
        
        results = {}
        
        for path in template_paths:
            template = 读取图片(path)
            if template is None:
                continue
            
            matches = self.match_all(
                img, template, threshold, region,
                max_results_per_template, min_distance
            )
            if matches:
                results[path] = matches
        
        return results


    def match_multiple_flat_bypictures(self, img: np.ndarray, 
                            template_paths: Tuple[str, ...],
                            threshold: float = 0.8,
                            region: Optional[Tuple[int, int, int, int]] = None,
                            max_results_per_template: int = 5,
                            min_distance: int = 10) -> List[MatchResult]:
        """多模板匹配，返回按坐标排序的扁平列表"""
        grouped = self.match_multiple_bypictures(
            img, template_paths, threshold, region,
            max_results_per_template, min_distance
        )
        
        all_matches = []
        for matches in grouped.values():
            all_matches.extend(matches)
        all_matches=self._去重匹配结果(all_matches, min_distance)
        all_matches.sort(key=lambda m: (m.left, m.top))
        return all_matches

    def _去重匹配结果(self, matches: List[MatchResult], 最小距离: int = 10) -> List[MatchResult]:
        """去掉重叠的匹配结果，保留置信度最高的"""
        if not matches:
            return []
        
        # 按置信度降序
        matches = sorted(matches, key=lambda m: m.confidence, reverse=True)
        
        保留 = []
        for m in matches:
            重叠 = False
            for k in 保留:
                # 计算中心距离
                cx1, cy1 = m.center
                cx2, cy2 = k.center
                if abs(cx1 - cx2) < 最小距离 and abs(cy1 - cy2) < 最小距离:
                    重叠 = True
                    break
            if not 重叠:
                保留.append(m)
        
        # 按坐标排序
        保留.sort(key=lambda m: (m.left, m.top))
        return 保留
# ==================== 调试工具 ====================

class DebugUtils:
    """调试工具（保留 print 用于调试图像保存）"""
    
    @staticmethod
    def draw_matches(img: np.ndarray, matches: List[MatchResult],
                     color: Tuple[int, int, int] = (0, 255, 0),
                     thickness: int = 2,
                     show_center: bool = True,
                     show_confidence: bool = True) -> np.ndarray:
        result = img.copy()
        
        for match in matches:
            cv2.rectangle(result, 
                         (match.left, match.top), 
                         (match.right, match.bottom), 
                         color, thickness)
            
            if show_center:
                cx, cy = match.center
                cv2.circle(result, (cx, cy), 3, color, -1)
            
            if show_confidence:
                text = f"{match.confidence:.2f}"
                cv2.putText(result, text, (match.left, match.top - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return result
    
    @staticmethod
    def save_debug_image(img: np.ndarray, path: str,
                         matches: Optional[List[MatchResult]] = None,
                         color: Tuple[int, int, int] = (0, 255, 0)) -> bool:
        try:
            if matches:
                img = DebugUtils.draw_matches(img, matches, color)
            cv2.imwrite(path, img)
            return True
        except Exception as e:
            print(f"保存调试图像失败: {e}")
            return False