# -*- coding: utf-8 -*-
"""
主窗口界面模块
实现非均质有雾图像去雾应用的主界面
"""

import os
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QScrollArea, QPushButton, QProgressBar, QStatusBar,
    QMenuBar, QMenu, QFileDialog, QMessageBox, QSplitter,
    QGroupBox, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QAction, QIcon, QPalette, QFont

from ..core.models import ImageInfo, DehazingParameters, ProcessingStatus
from ..core.config import ConfigManager
from ..utils.logger import get_logger
from ..utils.image_utils import ImageProcessor
from ..utils.error_handler import get_error_handler, handle_exceptions, FileError, ImageError, ErrorCode
from .progress_dialog import ProgressDialog
from .settings_dialog import SettingsDialog
from .help_dialog import HelpDialog


class ImageDisplayWidget(QLabel):
    """图像显示组件"""
    
    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.image_path = None
        self.original_pixmap = None
        
        self.setMinimumSize(300, 200)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #cccccc;
                border-radius: 8px;
                background-color: #f8f9fa;
                color: #6c757d;
                font-size: 14px;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(f"点击选择{title}图像\n支持格式: JPG, PNG, BMP, TIFF")
        
        # 启用拖放
        self.setAcceptDrops(True)
    
    def set_image(self, image_path: str):
        """设置显示的图像"""
        try:
            self.image_path = image_path
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self.original_pixmap = pixmap
                self.update_display()
                return True
            else:
                self.setText(f"无法加载图像: {os.path.basename(image_path)}")
                return False
        except Exception as e:
            self.setText(f"加载图像失败: {str(e)}")
            return False
    
    def update_display(self):
        """更新图像显示"""
        if self.original_pixmap:
            # 按比例缩放图像以适应控件大小
            scaled_pixmap = self.original_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_pixmap)
    
    def resizeEvent(self, event):
        """窗口大小改变时重新缩放图像"""
        super().resizeEvent(event)
        if self.original_pixmap:
            self.update_display()
    
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """拖拽放下事件"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if self.is_image_file(file_path):
                self.set_image(file_path)
                # 发送信号通知主窗口
                if hasattr(self.parent(), 'on_image_dropped'):
                    self.parent().on_image_dropped(file_path)
    
    def is_image_file(self, file_path: str) -> bool:
        """检查是否为支持的图像文件"""
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        return Path(file_path).suffix.lower() in supported_formats
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 发送信号通知主窗口打开文件对话框
            if hasattr(self.parent(), 'on_image_widget_clicked'):
                self.parent().on_image_widget_clicked(self)


class ProcessingThread(QThread):
    """图像处理线程"""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    processing_finished = pyqtSignal(str, bool)  # 结果路径, 是否成功
    error_occurred = pyqtSignal(str)  # 错误信息
    
    def __init__(self, input_path: str, output_path: str, parameters: DehazingParameters):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.parameters = parameters
        self.logger = get_logger(__name__)
        self.error_handler = get_error_handler()
        self.is_cancelled = False
    
    def cancel(self):
        """取消处理"""
        self.is_cancelled = True
    
    def run(self):
        """执行图像处理"""
        try:
            from ..algorithms.dehazing import NonHomogeneousDehazingAlgorithm
            
            if self.is_cancelled:
                return
            
            self.status_updated.emit("初始化去雾算法...")
            self.progress_updated.emit(10)
            
            # 创建去雾算法实例
            try:
                dehazer = NonHomogeneousDehazingAlgorithm()
            except Exception as e:
                raise ImageError("算法初始化失败", ErrorCode.ALGORITHM_INIT_FAILED, str(e), e)
            
            if self.is_cancelled:
                return
            
            self.status_updated.emit("加载输入图像...")
            self.progress_updated.emit(20)
            
            # 处理图像
            try:
                # 读取输入图像
                import cv2
                input_image = cv2.imread(self.input_path)
                if input_image is None:
                    raise ImageError("无法读取输入图像", ErrorCode.IMAGE_LOAD_FAILED)
                
                # 执行去雾处理
                result_image, processing_info = dehazer.dehaze_image(
                    input_image,
                    progress_callback=self.update_progress
                )
                
                # 保存结果图像
                success = cv2.imwrite(self.output_path, result_image)
                if not success:
                    raise ImageError("保存结果图像失败", ErrorCode.IMAGE_SAVE_FAILED)
            except Exception as e:
                if isinstance(e, ImageError):
                    raise
                else:
                    raise ImageError("去雾处理失败", ErrorCode.ALGORITHM_PROCESS_FAILED, str(e), e)
            
            if self.is_cancelled:
                return
            
            self.status_updated.emit("处理完成")
            self.progress_updated.emit(100)
            self.processing_finished.emit(self.output_path, True)
                
        except Exception as e:
            self.logger.error(f"图像处理异常: {str(e)}")
            error_msg = self.error_handler.handle_exception(e, show_dialog=False)
            self.error_occurred.emit(error_msg)
            self.processing_finished.emit("", False)
    
    def update_progress(self, progress: int, status: str = ""):
        """更新进度"""
        if not self.is_cancelled:
            self.progress_updated.emit(progress)
            if status:
                self.status_updated.emit(status)


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)
        
        # 初始化错误处理器
        self.error_handler = get_error_handler()
        self.error_handler.set_parent_widget(self)
        
        self.config_manager = ConfigManager()
        self.image_processor = ImageProcessor()
        
        # 当前处理的图像信息
        self.current_input_image = None
        self.current_output_image = None
        self.processing_thread = None
        self.progress_dialog = None
        
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("非均质有雾图像去雾系统 v1.0")
        self.setMinimumSize(1200, 800)
        
        # 设置应用图标（如果有的话）
        # self.setWindowIcon(QIcon('icon.png'))
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏区域
        self.create_toolbar_area(main_layout)
        
        # 创建图像显示区域
        self.create_image_area(main_layout)
        
        # 创建进度和状态区域
        self.create_progress_area(main_layout)
        
        # 创建状态栏
        self.create_status_bar()
        
        # 应用样式
        self.apply_styles()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        open_action = QAction('打开图像(&O)', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_image)
        file_menu.addAction(open_action)
        
        save_action = QAction('保存结果(&S)', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(lambda: self.save_result())
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出(&X)', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 处理菜单
        process_menu = menubar.addMenu('处理(&P)')
        
        start_action = QAction('开始去雾(&S)', self)
        start_action.setShortcut('F5')
        start_action.triggered.connect(self.start_processing)
        process_menu.addAction(start_action)
        
        settings_action = QAction('参数设置(&T)', self)
        settings_action.triggered.connect(self.show_settings)
        process_menu.addAction(settings_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        about_action = QAction('关于(&A)', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar_area(self, parent_layout):
        """创建工具栏区域"""
        toolbar_layout = QHBoxLayout()
        
        # 打开图像按钮
        self.open_btn = QPushButton("打开图像")
        self.open_btn.setMinimumHeight(40)
        self.open_btn.clicked.connect(self.open_image)
        toolbar_layout.addWidget(self.open_btn)
        
        # 开始处理按钮
        self.process_btn = QPushButton("开始去雾")
        self.process_btn.setMinimumHeight(40)
        self.process_btn.setEnabled(False)
        self.process_btn.clicked.connect(self.start_processing)
        toolbar_layout.addWidget(self.process_btn)
        
        # 保存结果按钮
        self.save_btn = QPushButton("保存结果")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(lambda: self.save_result())
        toolbar_layout.addWidget(self.save_btn)
        
        # 参数设置按钮
        self.settings_btn = QPushButton("参数设置")
        self.settings_btn.setMinimumHeight(40)
        self.settings_btn.clicked.connect(self.show_settings)
        toolbar_layout.addWidget(self.settings_btn)
        
        toolbar_layout.addStretch()
        parent_layout.addLayout(toolbar_layout)
    
    def create_image_area(self, parent_layout):
        """创建图像显示区域"""
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 输入图像组
        input_group = QGroupBox("输入图像")
        input_layout = QVBoxLayout(input_group)
        
        self.input_image_widget = ImageDisplayWidget("输入", self)
        input_layout.addWidget(self.input_image_widget)
        
        splitter.addWidget(input_group)
        
        # 输出图像组
        output_group = QGroupBox("处理结果")
        output_layout = QVBoxLayout(output_group)
        
        self.output_image_widget = ImageDisplayWidget("输出", self)
        output_layout.addWidget(self.output_image_widget)
        
        splitter.addWidget(output_group)
        
        # 设置分割器比例
        splitter.setSizes([600, 600])
        
        parent_layout.addWidget(splitter)
    
    def create_progress_area(self, parent_layout):
        """创建进度显示区域"""
        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout(progress_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        progress_layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")
        progress_layout.addWidget(self.status_label)
        
        parent_layout.addWidget(progress_group)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def apply_styles(self):
        """应用界面样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
            QProgressBar {
                border: 2px solid #e9ecef;
                border-radius: 6px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 4px;
            }
        """)
    
    def load_settings(self):
        """加载设置"""
        try:
            settings = self.config_manager.get_user_settings()
            # 恢复窗口大小和位置
            if hasattr(settings, 'window_geometry'):
                # 这里可以添加窗口几何信息的恢复
                pass
        except Exception as e:
            self.logger.warning(f"加载设置失败: {str(e)}")
    
    def on_image_widget_clicked(self, widget):
        """图像控件点击事件"""
        if widget == self.input_image_widget:
            self.open_image()
    
    def on_image_dropped(self, file_path: str):
        """图像拖放事件"""
        self.load_input_image(file_path)
    
    @handle_exceptions()
    def open_image(self, checked=False):
        """打开图像文件"""
        # checked参数用于兼容PyQt6信号连接，实际不使用
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "选择输入图像",
                "",
                "图像文件 (*.jpg *.jpeg *.png *.bmp *.tiff *.tif);;所有文件 (*)"
            )
            
            if file_path:
                self.load_input_image(file_path)
        except Exception as e:
            self.error_handler.handle_exception(e)
    
    @handle_exceptions()
    def load_input_image(self, file_path: str):
        """加载输入图像"""
        try:
            # 验证文件
            if not Path(file_path).exists():
                raise FileError("文件不存在", ErrorCode.FILE_NOT_FOUND, f"路径: {file_path}")
            
            # 验证图像文件
            image_info = self.image_processor.load_image_info(file_path)
            if not image_info:
                raise ImageError("无法加载图像文件", ErrorCode.IMAGE_LOAD_FAILED, f"路径: {file_path}")
            
            # 显示图像
            if self.input_image_widget.set_image(file_path):
                self.current_input_image = image_info
                self.process_btn.setEnabled(True)
                self.status_bar.showMessage(f"已加载: {os.path.basename(file_path)}")
                self.logger.info(f"加载输入图像: {file_path}")
            else:
                raise ImageError("图像格式不支持或文件损坏", ErrorCode.IMAGE_LOAD_FAILED, f"路径: {file_path}")
                
        except Exception as e:
            self.error_handler.handle_exception(e)
    
    @handle_exceptions()
    def start_processing(self, checked=False):
        """开始图像处理"""
        # checked参数用于兼容PyQt6信号连接，实际不使用
        if not self.current_input_image:
            self.error_handler.show_warning("请先选择输入图像")
            return
        
        if self.processing_thread and self.processing_thread.isRunning():
            self.error_handler.show_info("正在处理中，请等待...")
            return
        
        try:
            # 生成输出文件路径
            input_path = Path(self.current_input_image.file_path)
            output_path = input_path.parent / f"{input_path.stem}_dehazed{input_path.suffix}"
            
            # 获取处理参数
            parameters = self.config_manager.get_user_settings().dehazing_params
            
            # 创建进度对话框
            self.progress_dialog = ProgressDialog("图像去雾处理", self)
            self.progress_dialog.cancel_requested.connect(self.cancel_processing)
            
            # 创建处理线程
            self.processing_thread = ProcessingThread(
                str(input_path),
                str(output_path),
                parameters
            )
            
            # 连接信号
            self.processing_thread.progress_updated.connect(self.update_progress)
            self.processing_thread.status_updated.connect(self.update_status)
            self.processing_thread.processing_finished.connect(self.on_processing_finished)
            self.processing_thread.error_occurred.connect(self.handle_processing_error)
            
            # 更新UI状态
            self.process_btn.setEnabled(False)
            self.open_btn.setEnabled(False)
            self.progress_bar.setValue(0)
            
            # 启动处理
            self.progress_dialog.start_progress()
            self.processing_thread.start()
            self.progress_dialog.show()
            
            self.logger.info("开始图像去雾处理")
            
        except Exception as e:
            self.error_handler.handle_exception(e)
    
    def update_progress(self, value: int):
        """更新进度条"""
        self.progress_bar.setValue(value)
        
        # 更新进度对话框
        if self.progress_dialog:
            self.progress_dialog.update_progress(value, "")
    
    def update_status(self, status: str):
        """更新状态信息"""
        self.status_label.setText(status)
        self.status_bar.showMessage(status)
        
        # 更新进度对话框
        if self.progress_dialog:
            self.progress_dialog.update_progress(self.progress_bar.value(), status)
    
    def on_processing_finished(self, output_path: str, success: bool):
        """处理完成回调"""
        # 恢复UI状态
        self.process_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
        
        # 完成进度对话框
        if self.progress_dialog:
            message = "处理完成" if success else "处理失败"
            self.progress_dialog.finish_progress(success, message)
            if success:
                # 成功时自动关闭对话框
                QTimer.singleShot(1500, self.progress_dialog.accept)
        
        if success and output_path and os.path.exists(output_path):
            # 显示处理结果
            if self.output_image_widget.set_image(output_path):
                self.current_output_image = self.image_processor.load_image_info(output_path)
                self.save_btn.setEnabled(True)
                self.update_status("处理完成")
                self.logger.info(f"处理完成: {output_path}")
                
                # 记录处理历史
                from src.core.models import ProcessingRecord, ProcessingStatus
                from datetime import datetime
                import uuid
                
                record = ProcessingRecord(
                    id=str(uuid.uuid4()),
                    input_image=self.current_input_image,
                    output_image=self.current_output_image,
                    parameters=self.config_manager.get_user_settings().dehazing_params,
                    status=ProcessingStatus.COMPLETED,
                    start_time=datetime.now(),
                    end_time=datetime.now()
                )
                self.config_manager.add_processing_record(record)
            else:
                self.error_handler.show_warning("无法显示处理结果")
        else:
            self.update_status("处理失败")
            self.logger.error("图像处理失败")
    
    @handle_exceptions()
    def save_result(self):
        """保存处理结果"""
        if not self.current_output_image:
            self.error_handler.show_warning("没有可保存的结果")
            return
        
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存处理结果",
                f"dehazed_{os.path.basename(self.current_input_image.file_path)}",
                "图像文件 (*.jpg *.jpeg *.png *.bmp *.tiff);;所有文件 (*)"
            )
            
            if file_path:
                # 复制结果文件
                import shutil
                shutil.copy2(self.current_output_image.file_path, file_path)
                self.error_handler.show_info(f"结果已保存到: {file_path}")
                self.logger.info(f"保存结果: {file_path}")
                
        except Exception as e:
            self.error_handler.handle_exception(e)
    
    def cancel_processing(self):
        """取消处理"""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.cancel()
            self.processing_thread.wait(3000)  # 等待最多3秒
            if self.processing_thread.isRunning():
                self.processing_thread.terminate()
            
            self.update_status("处理已取消")
            self.process_btn.setEnabled(True)
            self.open_btn.setEnabled(True)
            
            self.logger.info("Processing cancelled by user")
    
    def handle_processing_error(self, error_message: str):
        """处理处理过程中的错误"""
        self.update_status(f"处理错误: {error_message}")
        self.process_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
    
    @handle_exceptions()
    def show_settings(self, checked=False):
        """显示设置对话框"""
        # checked参数用于兼容PyQt6信号连接，实际不使用
        try:
            dialog = SettingsDialog(self)
            if dialog.exec() == dialog.DialogCode.Accepted:
                # 重新加载配置
                self.config_manager.load_config()
                self.logger.info("Settings updated")
        except Exception as e:
            self.error_handler.handle_exception(e)
    
    @handle_exceptions()
    def show_help(self):
        """显示帮助对话框"""
        try:
            dialog = HelpDialog(self)
            dialog.exec()
        except Exception as e:
            self.error_handler.handle_exception(e)
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "非均质有雾图像去雾系统 v1.0\n\n"
            "基于改进的暗通道先验和引导滤波的\n"
            "非均质有雾图像去雾算法\n\n"
            "开发者: GloriousEpiphany\n"
            "技术栈: Python + PyQt6 + OpenCV"
        )
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止正在运行的处理线程
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "确认退出",
                "正在处理图像，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.processing_thread.terminate()
                self.processing_thread.wait()
                event.accept()
            else:
                event.ignore()
                return
        
        # 保存设置
        try:
            self.config_manager.save_config()
        except Exception as e:
            self.logger.warning(f"保存配置失败: {str(e)}")
        
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())