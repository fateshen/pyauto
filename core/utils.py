# core/utils.py
"""
公共工具函数 - 纯函数，无状态，线程安全

这些函数不依赖任何全局状态，多个线程可以安全调用
"""
import re
import random
import time
from typing import Optional, Tuple, List, Callable
from functools import wraps
import numpy as np
from core.path_manager import find_image
from core.debug import 调试器
import cv2

from enum import IntEnum

class 归属情况(IntEnum):
    未知 = 0      # 没有抢归属按钮
    归属自己 = 1      # 归属是自己
    归属公会 = 2      # 归属是公会成员（含同服务器）
    归属外人 = -1     # 归属是外人（需要抢）
# ==================== 图片处理 ====================
def 读取图片(filename: str):
    """
    读取图片（自动从图库目录查找）
    
    参数:
        filename: 图片文件名（如 "首领图标.bmp"）
    
    返回:
        OpenCV 图像，失败返回 None
    """
    img_path = find_image(filename)
    
    if img_path is None:
        调试器.warning("工具", f"找不到图片: {filename}")
        return None
    
    try:
        with open(img_path, 'rb') as f:
            data = np.frombuffer(f.read(), dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        调试器.error("工具", f"读取图片失败: {filename}, 错误: {e}")
        return None



# ==================== 随机点计算 ====================
def 随机点(区域: Tuple[int, int, int, int], 缩放比例: float = 1.0) -> Tuple[int, int]:
    """
    获取区域内一个随机点
    
    参数:
        区域: (左, 上, 右, 下)
        缩放比例: 缩放比例，1.0=全区域，<1.0=缩小区域，>1.0=扩展区域（受原区域限制）
    
    返回:
        (x, y) 随机点坐标
    """
    左, 上, 右, 下 = 区域
    
    # 计算中心点和尺寸
    中心点_x = (左 + 右) // 2
    中心点_y = (上 + 下) // 2
    宽 = 右 - 左
    高 = 下 - 上
    
    # 根据缩放比例计算实际范围
    if 缩放比例 != 1.0:
        半宽 = int(宽 * 缩放比例 / 2)
        半高 = int(高 * 缩放比例 / 2)
        
        # 计算新边界（限制在原区域范围内）
        左 = max(左, 中心点_x - 半宽)
        右 = min(右, 中心点_x + 半宽)
        上 = max(上, 中心点_y - 半高)
        下 = min(下, 中心点_y + 半高)
    
    # 边界有效性检查
    if 左 >= 右 or 上 >= 下:
        return (中心点_x, 中心点_y)
    
    return (random.randint(左, 右), random.randint(上, 下))

def 缩放区域(区域: Tuple[int, int, int, int], 缩放比例: float = 1.0) -> Tuple[int, int, int, int]:
    """
    缩放区域
    
    参数:
        区域: (左, 上, 右, 下)
        缩放比例: 缩放比例，1.0=全区域，<1.0=缩小区域，>1.0=扩展区域（受原区域限制）    
        返回:
        (左, 上, 右, 下) 新区域
    """
    左, 上, 右, 下 = 区域
    
    # 计算中心点和尺寸
    中心点_x = (左 + 右) // 2
    中心点_y = (上 + 下) // 2
    宽 = 右 - 左
    高 = 下 - 上
    
    # 根据缩放比例计算实际范围
    if 缩放比例 != 1.0:
        半宽 = int(宽 * 缩放比例 / 2)
        半高 = int(高 * 缩放比例 / 2)
        
        # 计算新边界（）
        左 = 中心点_x - 半宽
        右 = 中心点_x + 半宽
        上 =  中心点_y - 半高
        下 =  中心点_y + 半高

    return (左, 上, 右, 下)


# ==================== 时间解析 ====================

def 解析时间文字(文字: str) -> Optional[int]:
    """
    解析时间文字为秒数
    
    支持格式：
    - "已刷新" → 0
    - "01:23:45" → 1小时23分45秒
    - "03:45" → 3分45秒
    - "120" → 120秒
    - "剩余 2分30秒" → 150秒
    
    参数:
        文字: OCR识别到的时间文字
    
    返回:
        秒数，None表示解析失败
    """
    if not 文字:
        return None
    
    if 匹配分组关键字(文字, "已刷|已复"):
        return 0
    
    
    # 提取所有数字
    所有数字 = re.findall(r'\d+', 文字)
    if not 所有数字:
        return None
    
    # 格式1: 时:分:秒 (3个数字)
    if len(所有数字) >= 3:
        try:
            时 = int(所有数字[-3])
            分 = int(所有数字[-2])
            秒 = int(所有数字[-1])
            return 时 * 3600 + 分 * 60 + 秒
        except:
            pass
    
    # 格式2: 分:秒 (2个数字，第一个小于60)
    if len(所有数字) >= 2:
        第一数 = int(所有数字[-2])
        第二数 = int(所有数字[-1])
        if 第一数 <= 60:
            return 第一数 * 60 + 第二数
    
    # 格式3: 纯秒数
    if len(所有数字) >= 1:
        return int(所有数字[0])
    
    return None

# ==================== 数字提取 ====================

def 提取次数(文字: str, 第几个数字: int = 1) -> int:
    """
    从文字中提取数字作为次数
    
    参数:
        文字: OCR识别到的文字
        第几个数字: 取第几个数字，默认为1（第一个）
    
    返回:
        提取到的数字，如果未找到数字返回 -1
        特殊处理：如果数字以0开头（如"05"），返回0
    
    示例:
        提取次数("剩余次数 3") -> 3
        提取次数("05次", 1) -> 0
        提取次数("第3页，共5页", 2) -> 5
        提取次数("无数字") -> -1
    """
    if not 文字:
        return -1
    
    # 提取所有连续数字
    所有数字 = re.findall(r'\d+', 文字)
    
    if not 所有数字:
        return -1
    
    # 检查索引是否有效
    索引 = 第几个数字 - 1
    if 索引 >= len(所有数字):
        return -1
    
    数字字符串 = 所有数字[索引]
    
    # 检查是否以0开头（且长度大于1）
    if len(数字字符串) > 1 and 数字字符串[0] == '0':
        return 0
    
    try:
        return int(数字字符串)
    except ValueError:
        return -1


def 提取所有数字(文字: str) -> List[int]:
    """
    从文字中提取所有数字
    
    参数:
        文字: OCR识别到的文字
    
    返回:
        数字列表，按出现顺序
    
    示例:
        提取所有数字("第3页，共5页") -> [3, 5]
        提取所有数字("剩余3次，已打2次") -> [3, 2]
        提取所有数字("无数字") -> []
    """
    if not 文字:
        return []
    
    所有数字 = re.findall(r'\d+', 文字)
    结果 = []
    
    for 数字字符串 in 所有数字:
        try:
            结果.append(int(数字字符串))
        except ValueError:
            continue
    
    return 结果

# ==================== 文字处理 ====================
def 解析分组关键字( 关键字字符串: str) -> List[List[str]]:
        """ 
         解析分组关键字 
         格式: "key1a,key2a|key1b,key2b,key3b|key1c|....."
         返回:
            [[key1a, key2a], [key1b, key2b, key3b], [key1c], ...]

        """  
        if not 关键字字符串:
            return []
        
        组列表 = []
        for 组 in 关键字字符串.split('|'):
            组 = 组.strip()
            if 组:
                关键字列表 = [k.strip() for k in 组.split(',') if k.strip()]
                if 关键字列表:
                    组列表.append(关键字列表)
        
        return 组列表
def 匹配分组关键字( 字符串: str,规则:str,完整匹配:bool=False) -> bool:
        """
        检查规则是否匹配该字符串
        
        规则：至少有一组关键字满足匹配条件
        - 组内用逗号分隔：需要同时包含所有关键字（AND关系）
        - 组间用竖线分隔：任意一组匹配即可（OR关系）
        
        匹配规则：
        - 完整匹配=False（默认）：字符串包含关键字即可
        - 完整匹配=True 且 子分组只有1个关键字：字符串必须完全等于该关键字
        - 完整匹配=True 且 子分组有多个关键字：字符串必须同时包含所有关键字（AND关系）
        
        示例：
            "暗殿"                    -> 字符串包含"暗殿"即可
            "跨服战场,战场"           -> 字符串必须同时包含"跨服战场"和"战场"
            "暗殿|跨服战场,战场"       -> 包含"暗殿" 或 同时包含"跨服战场"和"战场"
            
            # 完整匹配模式
            "暗殿"                    -> 字符串必须完全等于"暗殿"
            "暗殿,战场"               -> 字符串必须同时包含"暗殿"和"战场"
        """
        if not 字符串:
            return False
        
        关键字组列表 = 解析分组关键字(规则)
        if not 关键字组列表:
            return False
        
        for 关键字组 in 关键字组列表:
            if 完整匹配 and len(关键字组) == 1:
                # 单关键字完整匹配：字符串必须完全等于该关键字
                if 字符串 == 关键字组[0]:
                    return True
            elif 完整匹配 and len(关键字组) > 1:
                # 多关键字完整匹配：必须同时包含所有关键字
                if all(关键字 in 字符串 for 关键字 in 关键字组):
                    return True
            else:
                # 默认模式：包含即可
                if all(关键字 in 字符串 for 关键字 in 关键字组):
                    return True
        
        return False


# ==================== 颜色处理 ====================

def 颜色相似度(颜色1: Tuple[int, int, int], 颜色2: Tuple[int, int, int]) -> float:
    """
    计算两个颜色的相似度（基于欧氏距离）
    
    参数:
        颜色1, 颜色2: (B, G, R) 元组
    
    返回:
        0-1之间的相似度，1表示完全相同
    """
    import math
    b1, g1, r1 = 颜色1
    b2, g2, r2 = 颜色2
    
    距离 = math.sqrt((b1 - b2)**2 + (g1 - g2)**2 + (r1 - r2)**2)
    最大距离 = math.sqrt(255**2 + 255**2 + 255**2)  # ≈ 441.67
    
    return 1 - (距离 / 最大距离)


def 十六进制转BGR(十六进制: str) -> Tuple[int, int, int]:
    """
    将十六进制颜色字符串转换为BGR元组
    
    参数:
        十六进制: 6位十六进制字符串，如 "74B7D1"
    
    返回:
        (B, G, R) 元组
    """
    if len(十六进制) != 6:
        raise ValueError(f"颜色值必须是6位十六进制，当前: {十六进制}")
    
    r = int(十六进制[0:2], 16)
    g = int(十六进制[2:4], 16)
    b = int(十六进制[4:6], 16)
    return (b, g, r)  # OpenCV是BGR格式
# ==================== 纯色检测 ====================

def _快速采样检测(截图: np.ndarray, 采样点数量: int = 9) -> bool:
    """
    快速采样检测（默认9个点）
    
    参数:
        截图: OpenCV图像 (BGR格式)
        采样点数量: 采样点数量，可选 5 或 9
    
    返回:
        True: 疑似纯色， False: 非纯色
    """
    if 截图 is None:
        return True
    
    h, w = 截图.shape[:2]
    
    if 采样点数量 == 5:
        # 5个采样点：四角 + 中心
        采样点 = [
            (20, 20),           # 左上
            (w-20, 20),         # 右上
            (20, h-20),         # 左下
            (w-20, h-20),       # 右下
            (w//2, h//2),     # 中心
        ]
    else:
        # 9个采样点：四角 + 中心 + 四边中点
        采样点 = [
            (20, 20),           # 左上
            (w-20, 20),         # 右上
            (20, h-20),         # 左下
            (w-20, h-20),       # 右下
            (w//2, h//2),     # 中心
            (w//2, 20),        # 上边中点
            (w//2, h-20),      # 下边中点
            (20, h//2),        # 左边中点
            (w-20, h//2),      # 右边中点
        ]
    
    基准颜色 = tuple(截图[采样点[0][1], 采样点[0][0]])
    
    for x, y in 采样点[1:]:
        if tuple(截图[y, x]) != 基准颜色:
            return False
    
    return True


def _标准差检测(截图: np.ndarray, 阈值: float = 5.0) -> bool:
    """
    标准差检测
    
    参数:
        截图: OpenCV图像 (BGR格式)
        阈值: 标准差阈值，小于此值认为是纯色
    
    返回:
        True: 是纯色， False: 非纯色
    """
    if 截图 is None:
        return True
    
    # 计算三个通道的标准差
    std = np.std(截图, axis=(0, 1))
    
    # 如果所有通道的标准差都小于阈值，认为是纯色
    return bool(np.all(std < 阈值))


def 是否是纯色截图(截图: np.ndarray, 
                   使用双层检测: bool = True,
                   标准差阈值: float = 5.0) -> bool:
    """
    双层纯色检测
    
    第一层：快速采样（5个点）- 过滤绝大多数正常截图
    第二层：标准差检测 - 确认疑似纯色的截图
    
    参数:
        截图: OpenCV图像 (BGR格式)
        使用双层检测: 是否使用双层检测（True=双层，False=仅采样）
        标准差阈值: 标准差阈值（仅双层检测时有效）
    
    返回:
        True: 是纯色截图， False: 正常截图
    """
    if 截图 is None:
        return True
    
    # 第一层：快速采样检测
    if not _快速采样检测(截图):
        return False
    
    # 如果不需要双层检测，采样检测为真即认为是纯色
    if not 使用双层检测:
        return True
    
    # 第二层：标准差检测
    return _标准差检测(截图, 标准差阈值)


def 解析坐标范围(坐标字符串: str) -> Optional[Tuple[int, int, int, int]]:
        """解析坐标范围字符串 "x1,y1,x2,y2" """
        if not 坐标字符串:
            return None
        try:
            parts = [int(x.strip()) for x in 坐标字符串.split(',')]
            if len(parts) == 4:
                return (parts[0], parts[1], parts[2], parts[3])
        except:
            pass
        return None

def 解析中心坐标(坐标字符串: str) -> Optional[Tuple[int, int]]:
    """解析中心坐标字符串 "x,y" """
    if not 坐标字符串:
        return None
    try:
        parts = [int(x.strip()) for x in 坐标字符串.split(',')]
        if len(parts) == 2:
            return (parts[0], parts[1])
    except:
        pass
    return None
# 放在 core/utils.py 中，建议放在 解析坐标范围 函数附近

def 坐标在目标半径内(坐标: Tuple[int, int], 目标坐标: Tuple[int, int], 半径: float = 10) -> bool:
    """
    判断坐标是否在目标坐标的半径范围内
    
    参数:
        坐标: (x, y) 当前坐标
        目标坐标: (x, y) 目标中心坐标
        半径: 像素半径，默认10
    
    返回:
        True: 在半径内
    """
    if not 坐标 or not 目标坐标:
        return False
    
    x1, y1 = 坐标
    x2, y2 = 目标坐标
    距离 = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    return 距离 <= 半径


def 坐标在目标区域内(坐标: Tuple[int, int], 目标区域: Tuple[int, int, int, int]) -> bool:
    """
    判断坐标是否在目标矩形区域内
    
    参数:
        坐标: (x, y) 当前坐标
        目标区域: (x1, y1, x2, y2) 左上角和右下角
    
    返回:
        True: 在区域内
    """
    if not 坐标 or not 目标区域:
        return False
    
    x, y = 坐标
    x1, y1, x2, y2 = 目标区域
    return x1 <= x <= x2 and y1 <= y <= y2

# ==================== 聊天文字相似度比较 ====================

def _提取时间戳(文字: str) -> Optional[int]:
    """
    提取"时间HHMMSS"格式中的时间并转为秒数
    
    参数:
        文字: 如 "时间200005玩家张三在..."
    
    返回:
        秒数（如 72005 表示 20:00:05），失败返回 None
    """
    if not 文字:
        return None
    匹配 = re.search(r'时间(\d{1,2})(\d{2})(\d{2})', 文字)
    if 匹配:
        时 = int(匹配.group(1))
        分 = int(匹配.group(2))
        秒 = int(匹配.group(3))
        return 时 * 3600 + 分 * 60 + 秒
    return None


def _提取正文(文字: str) -> str:
    """
    去掉"时间HHMMSS"前缀，返回正文部分
    
    参数:
        文字: 如 "时间200005玩家张三在上古剑冢"
    
    返回:
        "玩家张三在上古剑冢"
    """
    if not 文字:
        return ""
    return re.sub(r'^时间\d+', '', 文字)


def _最长公共子序列长度(s1: str, s2: str) -> int:
    """计算两个字符串的最长公共子序列长度"""
    m, n = len(s1), len(s2)
    if m == 0 or n == 0:
        return 0
    
    prev = [0] * (n + 1)
    curr = [0] * (n + 1)
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                curr[j] = prev[j-1] + 1
            else:
                curr[j] = max(prev[j], curr[j-1])
        prev, curr = curr, prev
    
    return prev[n]


def _文字相似度(文字1: str, 文字2: str) -> float:
    """
    计算两个字符串的相似度（基于最长公共子序列比例）
    
    返回:
        0.0 ~ 1.0，1.0 表示完全相同
    """
    if 文字1 == 文字2:
        return 1.0
    if not 文字1 or not 文字2:
        return 0.0
    
    lcs_len = _最长公共子序列长度(文字1, 文字2)
    max_len = max(len(文字1), len(文字2))
    return lcs_len / max_len


def 是否重复聊天内容(新内容: str, 旧内容: str, 时间差阈值: int = 3, 相似度阈值: float = 0.9) -> bool:
    """
    判断两条聊天内容是否重复
    
    规则：
    1. 提取"时间HHMMSS"前缀，时间差距 > 时间差阈值秒 → 不重复
    2. 提取正文部分（去掉时间前缀）
    3. 正文相似度 >= 相似度阈值 → 重复
    
    参数:
        新内容: 去符号后的新内容
        旧内容: 去符号后的队列最后一项
        时间差阈值: 时间差距超过此秒数直接判定不重复
        相似度阈值: 正文相似度达到此值判定为重复
    
    返回:
        True: 重复，应跳过
    
    示例:
        新: "时间200005玩家张三在上古剑冢召唤太古祖龙"
        旧: "时间200004玩家张三在上古剑冢召唤太古祖笼"
        → 时间差1秒, 相似度0.93 > 0.85 → True
        
        新: "时间200005玩家张三在上古1剑冢召唤太古祖龙"
        旧: "时间200004玩家张三在上古剑冢召唤太古祖笼"
        → 时间差1秒, 相似度0.87 > 0.85 → True
    """
    if not 旧内容:
        return False
    
    # 1. 提取时间比较
    新时间 = _提取时间戳(新内容)
    旧时间 = _提取时间戳(旧内容)
    
    if 新时间 is not None and 旧时间 is not None:
        if abs(新时间 - 旧时间) > 时间差阈值:
            return False
    
    # 2. 提取正文比较
    新正文 = _提取正文(新内容)
    旧正文 = _提取正文(旧内容)
    
    if not 新正文 or not 旧正文:
        return 新内容 == 旧内容
    
    # 3. 相似度比较
    相识度= _文字相似度(新正文, 旧正文)
    print(相识度)
    return 相识度 >= 相似度阈值
#==================== 玩家名字 ====================
#     return {"服务器号": 0, "名字": 全名}
def 解析玩家全名(全名: str) -> dict:
    """
    返回: {"服务器号": int, "名字": str}
          无服务器时 服务器号=0
    """
    import re
    
    if not 全名:
        return {"服务器号": 0, "名字": ""}
    
    全名 = 全名.strip()
    
    # 先清理多余符号（保留字母、数字、汉字、英文句点）
    清理后 = re.sub(r'[。．、，,]', '', 全名)  
    清理后 = re.sub(r'[^\w\u4e00-\u9fa5.]', '', 清理后)  # 去掉其他符号
    
    # 匹配: s22.孤影剑的跟班 或 22.孤影剑的跟班
    匹配 = re.search(r'[a-zA-Z]*(\d+)\.*([\u4e00-\u9fa5].+)$', 清理后)
    if 匹配:
        return {"服务器号": int(匹配.group(1)), "名字": 匹配.group(2)}
    
    return {"服务器号": 0, "名字": 清理后}
# ==================== 等待函数 ====================
def 是否为今天(时间戳: float) -> bool:
    """
    判断时间戳是否为今天
    
    参数:
        时间戳: Unix 时间戳（秒）
    
    返回:
        True: 是今天
        False: 不是今天 或 时间戳无效
    """
    import time
    if 时间戳 <= 0:
        return False
    
    当前 = time.localtime()
    目标 = time.localtime(时间戳)
    
    return (当前.tm_year == 目标.tm_year and 
            当前.tm_mon == 目标.tm_mon and 
            当前.tm_mday == 目标.tm_mday)
#==================== 区域计算函数 ====================
def 提取重叠区域(区域集1: List[Tuple[int, int, int, int]], 区域集2: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
    """
    从区域集1中提取满足条件的区域：
    区域集2中任一区域的第2或第4个参数，在区域集1当前区域的第2~第4范围内。
    
    参数说明：
    - 区域集1: 候选区域列表，每个区域 (left, top, right, bottom)
    - 区域集2: 条件区域列表
    - 条件: 区域集2的 top 或 bottom 落在 区域集1的 top~bottom 之间
    """
    结果 = []
    
    for 区域1 in 区域集1:
        top1, bottom1 = 区域1[1], 区域1[3]
        
        匹配 = False
        for 区域2 in 区域集2:
            # 区域集2的 top(索引1) 或 bottom(索引3) 在 区域1的 top~bottom 范围内
            if (top1 <= 区域2[1] <= bottom1) or (top1 <= 区域2[3] <= bottom1):
                匹配 = True
                break
        
        if 匹配:
            结果.append(区域1)
    
    return 结果

def 是否有重叠(目标区域: Tuple[int, int, int, int], 匹配结果列表: list[Tuple[int, int, int, int]]) -> bool:
    """检查是否有重叠，安全跳过无 rect 属性的元素"""
    目标_top, 目标_bottom = 目标区域[1], 目标区域[3]
    
    for r in 匹配结果列表:       
        if r:
            if (目标_top <= r[1] <= 目标_bottom) or (目标_top <= r[3] <= 目标_bottom):
                 return True
    return False

# ==================== 等待函数 ====================
def 等待毫秒(毫秒: int):
    """等待指定毫秒"""
    time.sleep(毫秒 / 1000)


def 等待秒(秒: float):
    """等待指定秒"""
    time.sleep(秒)


def 短等待():
    """短等待（100ms）"""
    time.sleep(0.1)


def 长等待():
    """长等待（1000ms）"""
    time.sleep(1)


def 超时等待(秒数: float, 检测函数: Callable[[], bool], 间隔秒: float = 0.5) -> bool:
    """
    等待直到条件满足或超时
    
    参数:
        秒数: 超时时间
        检测函数: 返回True表示条件满足
        间隔秒: 检测间隔
    
    返回:
        True: 条件满足， False: 超时
    """
    开始时间 = time.time()
    while time.time() - 开始时间 < 秒数:
        if 检测函数():
            return True
        time.sleep(间隔秒)
    return False


# ==================== 重试装饰器 ====================

def 重试(最大次数: int = 3, 延迟毫秒: int = 300, 重试假值: bool = False):
    """
    重试装饰器
     使用方式:
        @重试(最大次数=3, 延迟毫秒=500)
        def 可能会失败或返回False的操作():
    参数:
        最大次数: 最大重试次数
        延迟毫秒: 基础延迟（毫秒）
        重试假值: 是否在返回 False 时重试
    """
    def 装饰器(func):
        @wraps(func)
        def 包装器(*args, **kwargs):
            for 尝试次数 in range(最大次数):
                try:
                    结果 = func(*args, **kwargs)
                    if 重试假值 and 结果 is False and 尝试次数 < 最大次数 - 1:
                        调试器.debug("重试", f"{func.__name__} 返回 False，第 {尝试次数 + 1} 次重试")
                        等待毫秒(延迟毫秒 * (尝试次数 + 1))
                        continue
                    return 结果
                except Exception as e:
                    if 尝试次数 == 最大次数 - 1:
                        raise
                    调试器.debug("重试", f"{func.__name__} 失败，第 {尝试次数 + 1} 次重试，错误: {e}")
                    等待毫秒(延迟毫秒 * (尝试次数 + 1))
            return None
        return 包装器
    return 装饰器



# ==================== 调试工具 ====================

def 打印分隔线(标题: str = "", 长度: int = 60):
    """打印分隔线（保留用于测试）"""
    if 标题:
        剩余 = 长度 - len(标题) - 2
        if 剩余 > 0:
            print("=" * (剩余 // 2) + f" {标题} " + "=" * (剩余 - 剩余 // 2))
        else:
            print(f"= {标题} =")
    else:
        print("=" * 长度)


def 打印字典(数据: dict, 标题: str = ""):
    """打印字典内容（保留用于测试）"""
    if 标题:
        打印分隔线(标题)
    for 键, 值 in 数据.items():
        print(f"  {键}: {值}")
    if 标题:
        打印分隔线()


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("测试公共工具函数")
    print("=" * 60)
    
    # 测试1：随机点
    print("\n[测试1] 随机点")
    区域 = (100, 100, 200, 200)
    print(f"  区域: {区域}")
    print(f"  全区域随机点: {随机点(区域, 1.0)}")
    print(f"  缩放0.5随机点: {随机点(区域, 0.5)}")
    
    # 测试2：时间解析
    print("\n[测试2] 时间解析")
    测试用例 = [
        ("已刷新", 0),
        ("01:23:45", 5025),
        ("03:45", 225),
        ("120", 120),
        ("剩余 2分30秒", 150),
        ("", None),
    ]
    for 输入, 期望 in 测试用例:
        结果 = 解析时间文字(输入)
        print(f"  '{输入}' -> {结果} (期望: {期望})")
        assert 结果 == 期望
    
    # 测试3：颜色相似度
    print("\n[测试3] 颜色相似度")
    颜色1 = (255, 0, 0)   # 纯红
    颜色2 = (255, 0, 0)   # 纯红
    颜色3 = (0, 255, 0)   # 纯绿
    print(f"  相同颜色: {颜色相似度(颜色1, 颜色2):.3f}")
    print(f"  不同颜色: {颜色相似度(颜色1, 颜色3):.3f}")
    
    # 测试4：十六进制转换
    print("\n[测试4] 十六进制转BGR")
    print(f"  #74B7D1 -> BGR: {十六进制转BGR('74B7D1')}")
    
    # 测试5：等待函数（不实际等待太久）
    print("\n[测试5] 等待函数")
    print("  测试短等待...")
    短等待()
    print("  ✅ 短等待完成")
    
    # 测试6：重试装饰器
    print("\n[测试6] 重试装饰器")
    
    尝试计数 = 0
    
    @重试(最大次数=3, 延迟毫秒=100)
    def 测试函数():
        global  尝试计数
        尝试计数 += 1
        print(f"    第 {尝试计数} 次执行")
        if 尝试计数 < 2:
            raise ValueError("模拟失败")
        return "成功"
    
    结果 = 测试函数()
    print(f"  执行结果: {结果}")
    
    # 测试7：打印分隔线
    print("\n[测试7] 打印分隔线")
    打印分隔线("测试标题")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过!")
    print("=" * 60)