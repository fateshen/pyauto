"""
帝王霸业游戏助手 - 主程序
"""
import datetime
import sys
import os
import time
import re
# from rich.panel import p
from sympy import im

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.path_manager import check_environment, print_status, get_log_path
from core.recognition.template_match import  TemplateMatcher
from core.utils import 读取图片,解析玩家全名


# # def main():
#     """主函数"""
#     # 1. 打印环境信息
#     print_status()
    
#     # 2. 检查必要目录
#     if not check_environment():
#         input("按 Enter 退出...")
#         return
    
#     # 3. 初始化日志
#     import logging
#     logging.basicConfig(
#         filename=get_log_path("app.log"),
#         level=logging.INFO,
#         format='%(asctime)s - %(levelname)s - %(message)s'
#     )
    
#     logging.info("程序启动")
    
#     # 4. 测试读取图片
#     print("\n测试读取图片...")
#     img = 读取图片("首领图标.bmp")
#     if img is not None:
#         print("✅ 图片读取成功")
#     else:
#         print("❌ 图片读取失败")
    
#     print("\n程序运行中...")
#     # 这里添加你的主逻辑
def _去除所有符号(文字: str) -> str:
        """
        去除所有符号，只保留中文、英文、数字
        
        用于去重比较，避免OCR识别误差导致的重复
        """
        import re
        if not 文字:
            return ""
        # 只保留中文字符、英文字母、数字
        return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', 文字)
def main():
     print("\n" + "=" * 60)

if __name__ == "__main__":
#     import time
#     print (time.time())
#     str1="2023-05-05 09:09:09  "
#     print(str1.find("2"))
#     import random

#     # # 方法1：随机浮点数（1.0 到 2.0 之间）
#     # 随机浮点数 = random.uniform(1, 2)
#     # print(随机浮点数)  # 例如: 1.473829

#     # 方法2：随机整数（1 或 2）
#     随机整数 = random.randint(1, 2)
#     print(随机整数)  # 1 或 2
 
#     txt1="2023/09"
#     print(txt1.split("/"))
#     # 方法3：随机2位小数
    # 随机数 = round(random.uniform(1, 2), 2)
    # print(随机数)  # 例如: 1.58
     
    #  print(datetime.datetime.now().minute)
    # 分钟数=datetime.datetime.now().minute
    # print(分钟数)
    # 层数 = None
    # 层数匹配 = re.search(r'(\d+)层', "坐骑战场7层")
    # if 层数匹配:
    #     层数 = int(层数匹配.group(1))
    #     print(层数)
    # import random
    # 当前子任务队列 = [1, 2, 3, 4]
    # random.shuffle(当前子任务队列)
    # print(当前子任务队列)
    name1="129甲"
    xinx=解析玩家全名(name1)
    print(xinx)
    