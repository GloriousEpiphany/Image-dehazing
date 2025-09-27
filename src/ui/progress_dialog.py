# -*- coding: utf-8 -*-
"""
进度显示对话框模块
提供处理进度显示和取消功能
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QMovie

import time
from typing import Optional

from ..utils.logger import get_logger


class ProgressDialog(QDialog):
    """进度显示对话框"""
    
    # 信号定义
    cancel_requested = pyqtSignal()  # 取消请求信号
    
    def __init__(self, title: str = "处理中", parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.start_time = None
        self.is_cancelled = False
        self.can_cancel = True
        
        self.init_ui(title)
        self.setup_timer()
    
    def init_ui(self, title: str):
        """初始化UI"""
        self.setWindowTitle(title)
        self.setMinimumSize(400, 300)
        self.setMaximumSize(500, 400)
        self.setModal(True)
        
        # 禁用关闭按钮
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.CustomizeWindowHint | 
            Qt.WindowType.WindowTitleHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 标题标签
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(self.title_label)
        
        # 当前操作标签
        self.operation_label = QLabel("准备开始...")
        self.operation_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.operation_label.setFont(QFont("Arial", 10))
        self.operation_label.setStyleSheet("color: #34495e; margin-bottom: 5px;")
        layout.addWidget(self.operation_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 详细信息区域
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.Box)
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        
        # 时间信息
        time_layout = QHBoxLayout()
        
        self.elapsed_label = QLabel("已用时间: 00:00")
        self.elapsed_label.setFont(QFont("Arial", 9))
        time_layout.addWidget(self.elapsed_label)
        
        time_layout.addStretch()
        
        self.remaining_label = QLabel("预计剩余: --:--")
        self.remaining_label.setFont(QFont("Arial", 9))
        time_layout.addWidget(self.remaining_label)
        
        info_layout.addLayout(time_layout)
        
        # 详细日志
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(100)
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 8))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #ced4da;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        info_layout.addWidget(self.log_text)
        
        layout.addWidget(info_frame)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setMinimumWidth(80)
        self.cancel_button.clicked.connect(self.cancel_operation)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def setup_timer(self):
        """设置定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_info)
        self.timer.start(1000)  # 每秒更新一次
    
    def start_progress(self):
        """开始进度显示"""
        self.start_time = time.time()
        self.is_cancelled = False
        self.progress_bar.setValue(0)
        self.operation_label.setText("开始处理...")
        self.add_log("开始处理任务")
    
    def update_progress(self, value: int, operation: str = ""):
        """更新进度
        
        Args:
            value: 进度值 (0-100)
            operation: 当前操作描述
        """
        if self.is_cancelled:
            return
        
        self.progress_bar.setValue(max(0, min(100, value)))
        
        if operation:
            self.operation_label.setText(operation)
            self.add_log(f"[{value}%] {operation}")
    
    def add_log(self, message: str):
        """添加日志信息"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        self.log_text.append(log_entry)
        
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def update_time_info(self):
        """更新时间信息"""
        if not self.start_time:
            return
        
        elapsed = time.time() - self.start_time
        elapsed_str = self.format_time(elapsed)
        self.elapsed_label.setText(f"已用时间: {elapsed_str}")
        
        # 计算预计剩余时间
        progress = self.progress_bar.value()
        if progress > 0 and progress < 100:
            total_estimated = elapsed * 100 / progress
            remaining = total_estimated - elapsed
            remaining_str = self.format_time(remaining)
            self.remaining_label.setText(f"预计剩余: {remaining_str}")
        elif progress >= 100:
            self.remaining_label.setText("预计剩余: 00:00")
    
    def format_time(self, seconds: float) -> str:
        """格式化时间显示"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    def cancel_operation(self):
        """取消操作"""
        if not self.can_cancel:
            return
        
        self.is_cancelled = True
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("取消中...")
        self.operation_label.setText("正在取消操作...")
        self.add_log("用户请求取消操作")
        
        # 发送取消信号
        self.cancel_requested.emit()
    
    def set_cancellable(self, cancellable: bool):
        """设置是否可以取消"""
        self.can_cancel = cancellable
        self.cancel_button.setEnabled(cancellable and not self.is_cancelled)
    
    def finish_progress(self, success: bool = True, message: str = ""):
        """完成进度显示"""
        self.timer.stop()
        
        if success:
            self.progress_bar.setValue(100)
            self.operation_label.setText(message or "处理完成")
            self.add_log("任务完成")
            
            # 更改取消按钮为关闭按钮
            self.cancel_button.setText("关闭")
            self.cancel_button.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            self.cancel_button.clicked.disconnect()
            self.cancel_button.clicked.connect(self.accept)
            self.cancel_button.setEnabled(True)
        else:
            self.operation_label.setText(message or "处理失败")
            self.add_log(f"任务失败: {message}")
            
            # 更改取消按钮为关闭按钮
            self.cancel_button.setText("关闭")
            self.cancel_button.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
            """)
            self.cancel_button.clicked.disconnect()
            self.cancel_button.clicked.connect(self.accept)
            self.cancel_button.setEnabled(True)
    
    def is_canceled(self) -> bool:
        """检查是否已取消"""
        return self.is_cancelled
    
    def closeEvent(self, event):
        """关闭事件处理"""
        if self.can_cancel and not self.is_cancelled:
            self.cancel_operation()
        event.accept()


class SimpleProgressDialog(QDialog):
    """简单进度对话框（无取消功能）"""
    
    def __init__(self, title: str = "处理中", message: str = "请稍候...", parent=None):
        super().__init__(parent)
        self.init_ui(title, message)
    
    def init_ui(self, title: str, message: str):
        """初始化UI"""
        self.setWindowTitle(title)
        self.setFixedSize(300, 120)
        self.setModal(True)
        
        # 禁用关闭按钮
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.CustomizeWindowHint | 
            Qt.WindowType.WindowTitleHint
        )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 消息标签
        message_label = QLabel(message)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_label.setFont(QFont("Arial", 10))
        layout.addWidget(message_label)
        
        # 不确定进度条
        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(0)  # 不确定进度
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        layout.addWidget(progress_bar)
    
    def update_message(self, message: str):
        """更新消息"""
        if hasattr(self, 'message_label'):
            self.message_label.setText(message)


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QThread
    
    class TestThread(QThread):
        def __init__(self, dialog):
            super().__init__()
            self.dialog = dialog
        
        def run(self):
            for i in range(101):
                if self.dialog.is_canceled():
                    break
                
                self.dialog.update_progress(i, f"处理步骤 {i}")
                self.msleep(50)
            
            if not self.dialog.is_canceled():
                self.dialog.finish_progress(True, "处理完成")
    
    app = QApplication(sys.argv)
    
    dialog = ProgressDialog("测试进度")
    thread = TestThread(dialog)
    
    dialog.start_progress()
    thread.start()
    
    dialog.exec()
    sys.exit(app.exec())