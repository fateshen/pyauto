# core/path_manager.py
"""
路径管理器

- logs 目录：运行时自动创建
- 帝王霸业图库、config 目录：随程序发布，不自动创建
"""
import os
import sys
from pathlib import Path
from typing import Optional
from core.debug import 调试器


class PathManager:
    """路径管理器"""
    
    def __init__(self):
        """初始化，确定运行目录"""
        
        # 确定运行目录（EXE所在目录或脚本所在目录）
        if getattr(sys, 'frozen', False):
            # 打包后：EXE 所在目录
            self.run_dir = Path(sys.executable).parent
        else:
            # 开发环境：当前文件在 core/ 目录下，向上两级到项目根目录
            current_file = Path(__file__).resolve()
            self.run_dir = current_file.parent.parent
        
        # 随程序发布的目录（与 EXE 同级，不自动创建）
        self.image_dir = self.run_dir / "帝王霸业图库"
        self.config_dir = self.run_dir / "config"
        
        # 运行时创建的目录（自动创建）
        self.logs_dir = self.run_dir / "logs"
        self._ensure_logs_dir()
    
    def _ensure_logs_dir(self):
        """确保 logs 目录存在"""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def check_dirs(self) -> dict:
        """检查目录是否存在（用于启动时验证）"""
        return {
            "帝王霸业图库": self.image_dir.exists(),
            "config": self.config_dir.exists(),
        }
    
    def print_status(self):
        """打印目录状态（用于调试）"""
        调试器.info("路径管理", "=" * 50)
        调试器.info("路径管理", "路径管理器状态")
        调试器.info("路径管理", "=" * 50)
        调试器.info("路径管理", f"运行目录: {self.run_dir}")
        调试器.info("路径管理", f"是否打包: {getattr(sys, 'frozen', False)}")
        调试器.info("路径管理", "-" * 50)
        调试器.info("路径管理", "随程序发布的目录:")
        
        for name, exists in self.check_dirs().items():
            status = "✅ 存在" if exists else "❌ 不存在"
            if exists:
                调试器.info("路径管理", f"  {name}: {status}")
            else:
                调试器.warning("路径管理", f"  {name}: {status}")
        
        调试器.info("路径管理", "  logs: ✅ 已创建（运行时）")
        调试器.info("路径管理", "=" * 50)
    
    # ==================== 获取目录 ====================
    
    def get_run_dir(self) -> str:
        """获取运行目录"""
        return str(self.run_dir)
    
    def get_logs_dir(self) -> str:
        """获取日志目录"""
        return str(self.logs_dir)
    
    def get_config_dir(self) -> str:
        """获取配置目录"""
        return str(self.config_dir)
    
    def get_image_dir(self) -> str:
        """获取图库目录"""
        return str(self.image_dir)
    
    # ==================== 获取文件路径 ====================
    
    def get_log_path(self, filename: str) -> str:
        """获取日志文件路径"""
        return str(self.logs_dir / filename)
    
    def get_config_path(self, filename: str) -> str:
        """获取配置文件路径"""
        return str(self.config_dir / filename)
    
    def get_image_path(self, filename: str) -> str:
        """获取图片文件路径"""
        return str(self.image_dir / filename)
    
    # ==================== 智能查找 ====================
    
    def find_image(self, filename: str) -> Optional[str]:
        """
        查找图片文件
        
        查找顺序：
        1. 帝王霸业图库目录
        2. 运行目录
        3. 当前工作目录
        
        返回:
            找到则返回路径，否则返回 None
        """
        # 1. 图库目录
        img_path = self.image_dir / filename
        if img_path.exists():
            return str(img_path)
        
        # 2. 运行目录
        img_path = self.run_dir / filename
        if img_path.exists():
            return str(img_path)
        
        # 3. 当前工作目录
        img_path = Path.cwd() / filename
        if img_path.exists():
            return str(img_path)
        
        return None
    
    def get_config(self, filename: str, default: dict = None) -> dict:
        """
        读取配置文件
        
        参数:
            filename: 配置文件名
            default: 默认配置（文件不存在时返回）
        
        返回:
            配置字典
        """
        import json
        
        config_path = self.get_config_path(filename)
        
        if not os.path.exists(config_path):
            if default is not None:
                return default
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            调试器.error("路径管理", f"读取配置文件失败: {config_path}, 错误: {e}")
            return default or {}
    
    def save_config(self, filename: str, data: dict):
        """保存配置文件"""
        import json
        
        config_path = self.get_config_path(filename)
        
        # 确保目录存在（虽然理论上应该已存在）
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            调试器.error("路径管理", f"保存配置文件失败: {config_path}, 错误: {e}")


# 创建全局实例
path_mgr = PathManager()


# ==================== 便捷函数 ====================

def get_log_path(filename: str) -> str:
    """获取日志文件路径"""
    return path_mgr.get_log_path(filename)

def get_config_path(filename: str) -> str:
    """获取配置文件路径"""
    return path_mgr.get_config_path(filename)

def get_image_path(filename: str) -> str:
    """获取图片文件路径"""
    return path_mgr.get_image_path(filename)

def find_image(filename: str) -> Optional[str]:
    """智能查找图片"""
    return path_mgr.find_image(filename)

def check_environment() -> bool:
    """检查运行环境是否完整"""
    from core.debug import 调试器
    status = path_mgr.check_dirs()
    all_exist = all(status.values())
    
    if not all_exist:
        调试器.warning("路径管理", "⚠️ 缺少必要目录:")
        for name, exists in status.items():
            if not exists:
                调试器.warning("路径管理", f"   - {name}/")
        调试器.warning("路径管理", "请确保这些目录与程序放在同一目录下")
    
    return all_exist

def print_status():
    """打印状态信息"""
    path_mgr.print_status()