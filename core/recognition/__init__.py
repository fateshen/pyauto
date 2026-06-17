# core/recognition/__init__.py
"""
识别模块

提供OCR文字识别、像素分析、模板匹配和结果管理功能
"""

from .ocr import TextRecognizer, OCRResult
from .pixel_detector import PixelAnalyzer
from .template_match import TemplateMatcher, MatchResult, RegionUtils

# 定义包对外暴露的接口
__all__ = ['TextRecognizer', 'OCRResult', 'PixelAnalyzer', 'TemplateMatcher', 'MatchResult', 'RegionUtils']

# 包版本信息
__version__ = '1.0.0'
__author__ = 'vencon'

from typing import List, Tuple, Optional
from core.debug import 调试器


def 分离粘连文字(ocr_result: 'OCRResult', 间隙比例: float = 0.15) -> 'OCRResult':
    """
    将OCR识别结果中的粘连文字按等分法分离
    
    参数:
        ocr_result: 原始OCR结果
        间隙比例: 间隙宽度占总宽度的比例，默认0.15（15%）
    
    返回:
        分离后的OCRResult
    """
    import re
    
    def 提取完整词语(文字: str) -> List[str]:
        """
        提取完整的词语，保留数字和后面的单位
        
        例如：
        "坐骑2层坐骑3层" -> ["坐骑2层", "坐骑3层"]
        "坐骑4层坐骑5层" -> ["坐骑4层", "坐骑5层"]
        """
        if not 文字:
            return []
        
        # 匹配：中文字符 + 数字 + 单位（层/关/级等）
        pattern = r'([\u4e00-\u9fa5]+\d+[层关级章回]?)'
        结果 = re.findall(pattern, 文字)
        
        # 如果匹配结果为空，尝试其他模式
        if not 结果:
            # 匹配：任意非数字 + 数字 + 任意字符（直到遇到下一个非数字+数字）
            pattern2 = r'([^\d]*\d+[^\d]*?)'
            结果 = re.findall(pattern2, 文字)
            # 过滤空字符串
            结果 = [w for w in 结果 if w and re.search(r'\d', w)]
        
        return 结果
    
    def 估算等分区域带间隙(区域: Tuple[int, int, int, int], 
                              数量: int, 
                              间隙比例: float) -> List[Tuple[int, int, int, int]]:
        """
        按等分法估算子区域，每个子项之间有间隙
        
        参数:
            区域: (left, top, right, bottom)
            数量: 需要分成的数量
            间隙比例: 间隙宽度占总宽度的比例
        
        返回:
            子区域列表
        """
        left, top, right, bottom = 区域
        总宽度 = right - left
        
        if 数量 <= 0:
            return []
        
        # 计算每个子项的宽度（总宽度减去间隙后等分）
        总间隙宽度 = int(总宽度 * 间隙比例 * (数量 - 1))
        内容总宽度 = 总宽度 - 总间隙宽度
        每份宽度 = 内容总宽度 // 数量
        剩余宽度 = 内容总宽度 % 数量
        
        结果 = []
        当前左 = left
        
        for i in range(数量):
            子左 = 当前左
            子右 = 当前左 + 每份宽度 + (1 if i < 剩余宽度 else 0)
            结果.append((子左, top, 子右, bottom))
            
            # 添加间隙（最后一个不加）
            if i < 数量 - 1:
                间隙宽度 = int(总宽度 * 间隙比例)
                当前左 = 子右 + 间隙宽度
            else:
                当前左 = 子右
        
        return 结果
    
    新项列表 = []
    
    for 文字, 区域 in ocr_result.items:
        词语列表 = 提取完整词语(文字)
        
        if len(词语列表) <= 1:
            # 无需分离，直接添加
            新项列表.append((文字, 区域))
        else:
            # 需要分离
            数量 = len(词语列表)
            子区域列表 = 估算等分区域带间隙(区域, 数量, 间隙比例)
            
            for i, 词语 in enumerate(词语列表):
                if i < len(子区域列表):
                    新项列表.append((词语, 子区域列表[i]))
                else:
                    新项列表.append((词语, 区域))
    
    # 按左坐标排序
    新项列表.sort(key=lambda x: x[1][0])
    
    return OCRResult(新项列表)