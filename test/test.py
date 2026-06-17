"""
测试页面操作集

运行方式：
    python -m test.test_page_operations

使用步骤：
    1. 确保游戏窗口已打开
    2. 修改下面的 窗口句柄 为实际值
    3. 运行测试
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.assistant import 战斗辅助识别器
from models.game_config import 游戏全局配置
from core.page_operations import 页面操作集
from core.window_thread import 窗口线程
from core.task_executors.registry import 任务执行器注册表
from tasks.base import 任务定义


# ==================== 配置 ====================

# 游戏窗口句柄（测试者直接赋值）
窗口句柄 = 460874

# 窗口名称（用于配置隔离）
窗口名称 = "巢元畅"

# 要测试的任务ID（从注册表中获取）
测试任务ID = "shenbing_mijing"  # 可选: andian_daily, shenbing_mijing

# 窗口偏移量（如果窗口有边框）
窗口偏移X = 0
窗口偏移Y = 0

# 是否加载已保存的任务配置
是否加载任务配置 = True


# ==================== 辅助函数 ====================

def 创建执行器从注册表(线程, 任务ID: str):
    """
    从注册表获取任务信息并创建执行器
    
    参数:
        线程: 窗口线程实例
        任务ID: 任务标识
    
    返回:
        任务执行器实例
    """
    # 从注册表获取注册信息
    注册信息 = 任务执行器注册表.获取注册信息(任务ID)
    if not 注册信息:
        print(f"错误: 任务 '{任务ID}' 未注册")
        print(f"已注册的任务: {任务执行器注册表.获取所有已注册任务()}")
        return None
    
    # 创建配置和状态实例
    配置 = 注册信息.配置类()
    状态 = 注册信息.状态类()
    
    # 创建执行器
    执行器类 = 注册信息.执行器类
    执行器 = 执行器类(线程, 配置, 状态)
    
    print(f"成功创建执行器: {任务ID}")
    print(f"  配置类: {注册信息.配置类.__name__}")
    print(f"  状态类: {注册信息.状态类.__name__}")
    print(f"  执行器类: {注册信息.执行器类.__name__}")
    
    return 执行器


def 打印已注册任务():
    """打印所有已注册的任务"""
    已注册 = 任务执行器注册表.获取所有已注册任务()
    print("\n已注册的任务:")
    for 任务ID in 已注册:
        信息 = 任务执行器注册表.获取注册信息(任务ID)
        print(f"  - {任务ID}: {信息.执行器类.__name__}")


# ==================== 测试函数 ====================

def test_页面操作集(窗口):
    """测试页面操作集"""
    print("\n" + "-" * 40)
    print("测试页面操作集")
    print("-" * 40)
    
    # 创建页面操作集
    操作集 = 页面操作集(窗口)
    
    # 测试预创建的操作
    print("预创建的操作:")
    # 操作列表 = [
    #     ("进入跨服战场页面", 操作集.进入跨服战场页面),
    #     ("进入暗殿页面", 操作集.进入暗殿页面),
    #     ("点击前往挑战", 操作集.点击前往挑战),
    #     ("退出副本", 操作集.退出副本),
    #     ("开启自动战斗", 操作集.开启自动战斗),
    # ]
    
    # for 名称, 操作 in 操作列表:
    #     print(f"  - {名称}: {操作}")
    
    print("\n✅ 页面操作集测试完成")


def test_任务配置加载():
    """测试任务配置加载"""
    print("\n" + "-" * 40)
    print("测试任务配置加载")
    print("-" * 40)
    
    if 是否加载任务配置:
        try:
            # 加载窗口专属任务配置
            任务定义.导入配置从JSON(窗口名称)
            print(f"✅ 已加载窗口 '{窗口名称}' 的任务配置")
        except Exception as e:
            print(f"⚠️ 加载任务配置失败: {e}，使用默认配置")
    else:
        print("跳过加载任务配置，使用默认配置")
    
    # 导出当前配置（用于查看）
    try:
        任务定义.导出配置到JSON(窗口名称)
        print(f"✅ 已导出任务配置到 config/{窗口名称}/tasks_config.json")
    except Exception as e:
        print(f"⚠️ 导出任务配置失败: {e}")


# ==================== 主函数 ====================

def main():
    print("\n" + "=" * 60)
    print("页面操作集与战斗执行器测试")
    print("=" * 60)
    import win32gui
    if not win32gui.IsWindowVisible(窗口句柄): 
         print("错误: 窗口句柄无效！")
         return

    from core.debug import (
    设置日志开关, 设置控制台输出, 设置文件输出,
    set_global_level, set_log_dir)
    # 1. 检查窗口句柄
    if 窗口句柄 == 0:
        print("错误: 请先设置窗口句柄！")
        print("在代码中找到 '窗口句柄 = 0' 并修改为实际值")
        return
    
    # 2. 打印已注册的任务
    打印已注册任务()
    set_log_dir("logs")
        
    # 2. 设置日志总开关（False=完全不输出）
    设置日志开关(True)
    
    # 3. 设置输出目标
    设置控制台输出(True)   # 输出到控制台
    设置文件输出(True)     # 输出到文件
    
    # 4. 设置全局级别（所有线程默认）
    set_global_level(7)    # INFO级别

    # if not self.初始化():
    #     return
    from tasks import 初始化任务系统
    # 初始化任务系统()
    # 3. 创建游戏配置（使用窗口名称）
    print(f"\n[1] 创建游戏配置...")
    游戏配置 = 游戏全局配置.从文件加载(窗口名称)
    
    # # 应用窗口偏移
    # if 窗口偏移X != 0 or 窗口偏移Y != 0:
    #     游戏配置.设置窗口偏移(窗口偏移X, 窗口偏移Y)
    #     print(f"已应用窗口偏移: X={窗口偏移X}, Y={窗口偏移Y}")
    
    # 4. 加载任务配置
    print(f"\n[2] 加载任务配置...")
    # test_任务配置加载()
    
    # 5. 创建窗口线程
    print(f"\n[3] 创建窗口线程...")
    窗口 = 窗口线程(窗口句柄, 窗口名称, 游戏配置)
    窗口.start()
    time.sleep(1)  # 等待线程初始化
    窗口.通用操作.点击回城石()
    # print(f"  窗口名称: {窗口.窗口名称}")
    # print(f"  当前地图: {窗口.当前地图}")
    # 战斗辅助 = 战斗辅助识别器(窗口)
    # 玩家坐标 = 战斗辅助.获取当前玩家坐标()
    # print(f"  玩家坐标: {玩家坐标}")
    # 血量= 战斗辅助.获取玩家血量
    # time.sleep(1)
    # print(f"  玩家血量: {血量}")
    # 血量= 战斗辅助.获取玩家血量
    # time.sleep(1)
    # print(f"  玩家血量: {血量}")
    # 血量= 战斗辅助.获取玩家血量
    # time.sleep(1)
    # print(f"  玩家血量: {血量}")
    # 玩家名称= 战斗辅助.获取玩家角色名称()
    # print(f"  玩家名称: {玩家名称}")
    # # 6. 测试页面操作集
    test_页面操作集(窗口)
    页面操作=窗口.页面
    
    print( 页面操作.主界面操作.进入合成页面("神|装","神|剑"))
    # # 7. 创建执行器并测试
    # print("\n" + "-" * 40)
    # print(f"测试执行器: {测试任务ID}")
    # print("-" * 40)
    
    # # 执行器 = 创建执行器从注册表(窗口, 测试任务ID)
    # if not 执行器:
    #     print("创建执行器失败")
    #     窗口.stop()
    #     return
    
    # # 8. 测试执行器方法
    # print("\n[执行器方法测试]")
    
    # # 测试基础属性
    # print(f"  任务配置: {执行器.任务配置.任务名称}")
    # print(f"  任务状态剩余次数: {执行器.任务状态.剩余次数}")
    
   
    
    # # 9. 测试入口逻辑（可选，不自动执行）
    # print("\n" + "-" * 40)
    # print("提示: 执行器.执行() 方法会真正进入游戏操作")
    # print("如需测试，请取消下面代码的注释")
    # print("-" * 40)
    # 注意：下面代码会真正操作游戏，谨慎使用
    # if input("是否执行入口逻辑？(y/N): ").lower() == 'y':
    #     结果 = 执行器.执行()
    #     print(f"执行结果: {结果}")
    
    # # 10. 保存配置
    # print("\n[4] 保存配置...")
    # try:
    #     游戏配置.保存到文件()
    #     print(f"  玩家配置已保存 -> config/{窗口名称}/user_config.json")
    # except Exception as e:
    #     print(f"  保存玩家配置失败: {e}")
    
    # try:
    #     任务定义.导出配置到JSON(窗口名称)
    #     print(f"  任务配置已保存 -> config/{窗口名称}/tasks_config.json")
    # except Exception as e:
    #     print(f"  保存任务配置失败: {e}")
    time.sleep(15)
    # 11. 清理
    print("\n[5] 停止窗口线程...")
    窗口.stop()
    窗口.join(timeout=3)
    print("测试完成")


if __name__ == "__main__":
    main()