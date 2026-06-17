# PyAuto - 游戏挂机自动化框架

## 介绍

PyAuto 是一个基于 Python 的游戏挂机自动化框架，支持多窗口、多任务并行运行。通过 OCR 文字识别、模板匹配、像素分析等技术实现游戏界面的智能识别与操作。

### 主要特性

- **多窗口支持**：每个窗口独立线程运行，互不干扰
- **插件化任务系统**：装饰器模式自动注册任务，支持外置加载
- **多级日志系统**：线程独立日志，7级调试级别，支持配置文件
- **智能战斗系统**：目标检测、死亡复活、血量估算、抢归属判定
- **召唤响应机制**：支持队友召唤协助
- **防卡死检测**：自动检测卡死并刷新游戏
- **强化奖励任务**：后台静默执行低优先级奖励领取

---

## 软件架构
pyauto/
├── main.py # 主入口
├── core/ # 核心模块
│ ├── window_thread.py # 窗口线程（主循环、调度）
│ ├── task_scheduler.py # 任务调度器
│ ├── action_executor.py # 键鼠操作封装
│ ├── window_manager.py # 窗口截图、后台键鼠
│ ├── assistant.py # 战斗辅助识别器
│ ├── page_operations.py # 页面操作集（多级菜单）
│ ├── page_switcher.py # 页面切换器（点击+验证+重试）
│ ├── common_operations.py # 通用操作集
│ ├── debug.py # 多级日志系统
│ ├── runtime_state.py # 运行时公共变量
│ ├── path_manager.py # 路径管理器
│ ├── chat_manager.py # 聊天管理器
│ ├── reward_manager.py # 强化奖励管理器
│ ├── foreground_lock.py # 前台操作全局锁
│ ├── image_color_analyzer.py # 图片颜色分析器
│ ├── recognition/ # 识别模块
│ │ ├── ocr.py # OCR 文字识别
│ │ ├── template_match.py # 模板匹配
│ │ └── pixel_detector.py # 像素分析
│ └── task_executors/ # 任务执行器
│ ├── base_executor.py # 基类
│ ├── battle_executor.py # 战斗执行器
│ └── registry.py # 任务注册表
├── tasks/ # 任务模块（支持外置）
│ ├── base.py # 任务定义装饰器
│ ├── putong.py # 普通任务
│ ├── zuoqi.py # 坐骑任务
│ └── reward/ # 强化奖励任务
├── models/ # 数据模型
│ ├── game_config.py # 游戏配置
│ ├── task_config.py # 任务配置
│ ├── task_state.py # 任务状态
│ ├── battle_config.py # 战斗配置
│ ├── region_config.py # 区域配置
│ └── dynamic_tags.py # 动态标签
├── config/ # 配置文件
│ ├── region_config.json # 区域坐标配置
│ └── debug_config.json # 调试日志配置
├── ui/ # UI 界面（支持外置）
├── logs/ # 日志文件（运行时生成）
└── 帝王霸业图库/ # 游戏图片资源

text

---

## 安装教程

### 环境要求

- Python 3.12+
- Windows 10/11

### 安装步骤

1. **克隆仓库**
```bash
git clone https://gitee.com/vencons/pyauto.git
cd pyauto
创建虚拟环境

bash
python -m venv .venv
.venv\Scripts\activate
安装依赖

bash
pip install -r requirements.txt
配置 UMI-OCR

下载 UMI-OCR

启动服务：Umi-OCR.exe --http 1224

配置区域坐标

根据你的游戏分辨率修改 config/region_config.json

配置调试日志（可选）

修改 config/debug_config.json 调整日志级别

打包为 EXE
bash
pyinstaller main.spec
使用说明
启动程序
bash
python main.py
命令行参数
参数	说明
--debug	调试模式（DEBUG 级别日志）
--verbose	详细模式（VERBOSE 级别日志）
--quiet	安静模式（仅控制台输出错误）
任务配置
任务通过装饰器定义，示例：

python
@任务定义(
    任务ID="andian_daily",
    任务名称="暗殿任务",
    优先级=2,
    每日次数=3,
    地图关键字="暗殿",
    提前进场秒数=15,
)
class 暗殿任务(战斗任务执行器):
    pass
插件化
支持外置任务加载，将 .py 文件放入 tasks/ 目录即可，无需修改任何代码。

调试日志
日志按窗口名称独立存储，7级日志级别：

text
0=NONE  1=ERROR  2=WARNING  3=INFO  4=STATE  5=DEBUG  6=TRACE  7=VERBOSE
可通过 config/debug_config.json 按模块独立设置级别。