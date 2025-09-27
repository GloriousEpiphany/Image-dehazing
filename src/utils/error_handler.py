# -*- coding: utf-8 -*-
"""
错误处理和异常管理模块
提供统一的错误处理、异常捕获和用户友好的错误提示
"""

import sys
import traceback
from typing import Optional, Callable, Any, Dict
from functools import wraps
from enum import Enum

from PyQt6.QtWidgets import QMessageBox, QWidget
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QIcon

from .logger import get_logger


class ErrorLevel(Enum):
    """错误级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCode(Enum):
    """错误代码枚举"""
    # 文件相关错误
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_ACCESS_DENIED = "FILE_ACCESS_DENIED"
    FILE_FORMAT_UNSUPPORTED = "FILE_FORMAT_UNSUPPORTED"
    FILE_CORRUPTED = "FILE_CORRUPTED"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    
    # 图像处理错误
    IMAGE_LOAD_FAILED = "IMAGE_LOAD_FAILED"
    IMAGE_SAVE_FAILED = "IMAGE_SAVE_FAILED"
    IMAGE_PROCESS_FAILED = "IMAGE_PROCESS_FAILED"
    IMAGE_FORMAT_ERROR = "IMAGE_FORMAT_ERROR"
    IMAGE_SIZE_ERROR = "IMAGE_SIZE_ERROR"
    
    # 算法相关错误
    ALGORITHM_INIT_FAILED = "ALGORITHM_INIT_FAILED"
    ALGORITHM_PROCESS_FAILED = "ALGORITHM_PROCESS_FAILED"
    PARAMETER_INVALID = "PARAMETER_INVALID"
    
    # 系统相关错误
    MEMORY_ERROR = "MEMORY_ERROR"
    DISK_SPACE_ERROR = "DISK_SPACE_ERROR"
    PERMISSION_ERROR = "PERMISSION_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    
    # 配置相关错误
    CONFIG_LOAD_FAILED = "CONFIG_LOAD_FAILED"
    CONFIG_SAVE_FAILED = "CONFIG_SAVE_FAILED"
    CONFIG_INVALID = "CONFIG_INVALID"
    
    # 未知错误
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class DehazingError(Exception):
    """去雾应用自定义异常基类"""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR, 
                 details: Optional[str] = None, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details
        self.original_exception = original_exception
    
    def __str__(self):
        return f"[{self.error_code.value}] {self.message}"


class FileError(DehazingError):
    """文件相关错误"""
    pass


class ImageError(DehazingError):
    """图像处理相关错误"""
    pass


class AlgorithmError(DehazingError):
    """算法相关错误"""
    pass


class ConfigError(DehazingError):
    """配置相关错误"""
    pass


class ErrorHandler(QObject):
    """错误处理器"""
    
    # 错误信号
    error_occurred = pyqtSignal(str, str, str)  # message, level, details
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        self.error_messages = self._init_error_messages()
        self.parent_widget = None
    
    def set_parent_widget(self, parent: QWidget):
        """设置父窗口"""
        self.parent_widget = parent
    
    def _init_error_messages(self) -> Dict[ErrorCode, str]:
        """初始化错误消息映射"""
        return {
            # 文件相关错误
            ErrorCode.FILE_NOT_FOUND: "找不到指定的文件",
            ErrorCode.FILE_ACCESS_DENIED: "文件访问被拒绝，请检查文件权限",
            ErrorCode.FILE_FORMAT_UNSUPPORTED: "不支持的文件格式",
            ErrorCode.FILE_CORRUPTED: "文件已损坏或格式错误",
            ErrorCode.FILE_TOO_LARGE: "文件过大，无法处理",
            
            # 图像处理错误
            ErrorCode.IMAGE_LOAD_FAILED: "图像加载失败",
            ErrorCode.IMAGE_SAVE_FAILED: "图像保存失败",
            ErrorCode.IMAGE_PROCESS_FAILED: "图像处理失败",
            ErrorCode.IMAGE_FORMAT_ERROR: "图像格式错误",
            ErrorCode.IMAGE_SIZE_ERROR: "图像尺寸不符合要求",
            
            # 算法相关错误
            ErrorCode.ALGORITHM_INIT_FAILED: "算法初始化失败",
            ErrorCode.ALGORITHM_PROCESS_FAILED: "算法处理失败",
            ErrorCode.PARAMETER_INVALID: "参数设置无效",
            
            # 系统相关错误
            ErrorCode.MEMORY_ERROR: "内存不足，请关闭其他程序后重试",
            ErrorCode.DISK_SPACE_ERROR: "磁盘空间不足",
            ErrorCode.PERMISSION_ERROR: "权限不足，请以管理员身份运行",
            ErrorCode.NETWORK_ERROR: "网络连接错误",
            
            # 配置相关错误
            ErrorCode.CONFIG_LOAD_FAILED: "配置文件加载失败",
            ErrorCode.CONFIG_SAVE_FAILED: "配置文件保存失败",
            ErrorCode.CONFIG_INVALID: "配置文件格式错误",
            
            # 未知错误
            ErrorCode.UNKNOWN_ERROR: "发生未知错误"
        }
    
    def handle_exception(self, exception: Exception, show_dialog: bool = True) -> str:
        """处理异常
        
        Args:
            exception: 异常对象
            show_dialog: 是否显示错误对话框
            
        Returns:
            错误消息
        """
        if isinstance(exception, DehazingError):
            return self._handle_dehazing_error(exception, show_dialog)
        else:
            return self._handle_system_error(exception, show_dialog)
    
    def _handle_dehazing_error(self, error: DehazingError, show_dialog: bool) -> str:
        """处理自定义错误"""
        message = self.error_messages.get(error.error_code, error.message)
        details = error.details or str(error.original_exception) if error.original_exception else ""
        
        # 记录日志
        self.logger.error(f"DehazingError: {error}")
        if details:
            self.logger.error(f"Details: {details}")
        if error.original_exception:
            self.logger.error(f"Original exception: {error.original_exception}")
            self.logger.error(traceback.format_exc())
        
        # 发送信号
        level = self._get_error_level(error.error_code)
        self.error_occurred.emit(message, level.value, details)
        
        # 显示对话框
        if show_dialog:
            self._show_error_dialog(message, level, details)
        
        return message
    
    def _handle_system_error(self, exception: Exception, show_dialog: bool) -> str:
        """处理系统异常"""
        error_code = self._classify_system_error(exception)
        message = self.error_messages.get(error_code, str(exception))
        details = traceback.format_exc()
        
        # 记录日志
        self.logger.error(f"System error: {exception}")
        self.logger.error(details)
        
        # 发送信号
        level = self._get_error_level(error_code)
        self.error_occurred.emit(message, level.value, details)
        
        # 显示对话框
        if show_dialog:
            self._show_error_dialog(message, level, details)
        
        return message
    
    def _classify_system_error(self, exception: Exception) -> ErrorCode:
        """分类系统异常"""
        if isinstance(exception, FileNotFoundError):
            return ErrorCode.FILE_NOT_FOUND
        elif isinstance(exception, PermissionError):
            return ErrorCode.FILE_ACCESS_DENIED
        elif isinstance(exception, MemoryError):
            return ErrorCode.MEMORY_ERROR
        elif isinstance(exception, OSError):
            if "No space left on device" in str(exception):
                return ErrorCode.DISK_SPACE_ERROR
            else:
                return ErrorCode.PERMISSION_ERROR
        else:
            return ErrorCode.UNKNOWN_ERROR
    
    def _get_error_level(self, error_code: ErrorCode) -> ErrorLevel:
        """获取错误级别"""
        critical_errors = {
            ErrorCode.MEMORY_ERROR,
            ErrorCode.DISK_SPACE_ERROR,
            ErrorCode.PERMISSION_ERROR
        }
        
        warning_errors = {
            ErrorCode.FILE_TOO_LARGE,
            ErrorCode.IMAGE_SIZE_ERROR,
            ErrorCode.PARAMETER_INVALID
        }
        
        if error_code in critical_errors:
            return ErrorLevel.CRITICAL
        elif error_code in warning_errors:
            return ErrorLevel.WARNING
        else:
            return ErrorLevel.ERROR
    
    def _show_error_dialog(self, message: str, level: ErrorLevel, details: str = ""):
        """显示错误对话框"""
        if level == ErrorLevel.INFO:
            icon = QMessageBox.Icon.Information
            title = "信息"
        elif level == ErrorLevel.WARNING:
            icon = QMessageBox.Icon.Warning
            title = "警告"
        elif level == ErrorLevel.ERROR:
            icon = QMessageBox.Icon.Critical
            title = "错误"
        else:  # CRITICAL
            icon = QMessageBox.Icon.Critical
            title = "严重错误"
        
        msg_box = QMessageBox(self.parent_widget)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if details:
            msg_box.setDetailedText(details)
        
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    def show_info(self, message: str, title: str = "信息"):
        """显示信息对话框"""
        QMessageBox.information(self.parent_widget, title, message)
    
    def show_warning(self, message: str, title: str = "警告"):
        """显示警告对话框"""
        QMessageBox.warning(self.parent_widget, title, message)
    
    def show_error(self, message: str, title: str = "错误"):
        """显示错误对话框"""
        QMessageBox.critical(self.parent_widget, title, message)
    
    def ask_question(self, message: str, title: str = "确认") -> bool:
        """显示确认对话框
        
        Returns:
            True if user clicked Yes, False otherwise
        """
        reply = QMessageBox.question(
            self.parent_widget, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes


# 全局错误处理器实例
_global_error_handler = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def handle_exceptions(show_dialog: bool = True):
    """异常处理装饰器
    
    Args:
        show_dialog: 是否显示错误对话框
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = get_error_handler()
                error_handler.handle_exception(e, show_dialog)
                return None
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, show_dialog: bool = True, **kwargs) -> Optional[Any]:
    """安全执行函数
    
    Args:
        func: 要执行的函数
        *args: 函数参数
        show_dialog: 是否显示错误对话框
        **kwargs: 函数关键字参数
        
    Returns:
        函数执行结果，如果出错则返回None
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler = get_error_handler()
        error_handler.handle_exception(e, show_dialog)
        return None


def setup_global_exception_handler():
    """设置全局异常处理器"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger = get_logger("GlobalExceptionHandler")
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        error_handler = get_error_handler()
        error_handler.handle_exception(exc_value, show_dialog=True)
    
    sys.excepthook = handle_exception


if __name__ == '__main__':
    # 测试错误处理
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.error_handler = get_error_handler()
            self.error_handler.set_parent_widget(self)
            
            self.init_ui()
        
        def init_ui(self):
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QVBoxLayout(central_widget)
            
            # 测试按钮
            btn1 = QPushButton("测试文件错误")
            btn1.clicked.connect(self.test_file_error)
            layout.addWidget(btn1)
            
            btn2 = QPushButton("测试图像错误")
            btn2.clicked.connect(self.test_image_error)
            layout.addWidget(btn2)
            
            btn3 = QPushButton("测试系统错误")
            btn3.clicked.connect(self.test_system_error)
            layout.addWidget(btn3)
        
        @handle_exceptions()
        def test_file_error(self):
            raise FileError("测试文件错误", ErrorCode.FILE_NOT_FOUND, "文件路径: /test/path")
        
        @handle_exceptions()
        def test_image_error(self):
            raise ImageError("测试图像错误", ErrorCode.IMAGE_LOAD_FAILED)
        
        @handle_exceptions()
        def test_system_error(self):
            raise ValueError("测试系统错误")
    
    app = QApplication(sys.argv)
    setup_global_exception_handler()
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec())