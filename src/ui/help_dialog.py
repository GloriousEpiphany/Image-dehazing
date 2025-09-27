# -*- coding: utf-8 -*-
"""
帮助对话框模块
提供用户手册、算法说明和关于信息
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QTextEdit, QScrollArea,
    QWidget, QFrame, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QPixmap, QDesktopServices

from ..utils.logger import get_logger


class UserManualTab(QWidget):
    """用户手册标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 快速开始
        quick_start_group = QGroupBox("快速开始")
        quick_start_layout = QVBoxLayout(quick_start_group)
        
        quick_start_text = QTextEdit()
        quick_start_text.setReadOnly(True)
        quick_start_text.setMaximumHeight(200)
        quick_start_text.setHtml("""
        <h3>欢迎使用非均质有雾图像去雾系统！</h3>
        <p><b>1. 打开图像：</b>点击"打开图像"按钮或直接拖拽图像文件到预览区域</p>
        <p><b>2. 调整参数：</b>通过"设置"菜单调整去雾算法参数</p>
        <p><b>3. 开始处理：</b>点击"开始去雾"按钮进行图像处理</p>
        <p><b>4. 保存结果：</b>处理完成后点击"保存图像"保存去雾结果</p>
        """)
        quick_start_layout.addWidget(quick_start_text)
        scroll_layout.addWidget(quick_start_group)
        
        # 功能说明
        features_group = QGroupBox("主要功能")
        features_layout = QVBoxLayout(features_group)
        
        features_text = QTextEdit()
        features_text.setReadOnly(True)
        features_text.setMaximumHeight(300)
        features_text.setHtml("""
        <h3>核心功能</h3>
        <ul>
            <li><b>智能去雾：</b>基于改进的暗通道先验算法，针对非均质雾霾进行优化</li>
            <li><b>实时预览：</b>支持原图与去雾结果的实时对比预览</li>
            <li><b>参数调节：</b>提供丰富的算法参数供用户精细调节</li>
            <li><b>批量处理：</b>支持多张图像的批量去雾处理</li>
            <li><b>格式支持：</b>支持JPG、PNG、BMP、TIFF等常见图像格式</li>
        </ul>
        
        <h3>界面操作</h3>
        <ul>
            <li><b>拖拽操作：</b>直接拖拽图像文件到预览区域即可打开</li>
            <li><b>缩放查看：</b>使用鼠标滚轮或缩放按钮调整图像显示大小</li>
            <li><b>进度显示：</b>处理过程中显示实时进度和状态信息</li>
            <li><b>历史记录：</b>自动保存处理历史，方便回顾和管理</li>
        </ul>
        """)
        features_layout.addWidget(features_text)
        scroll_layout.addWidget(features_group)
        
        # 使用技巧
        tips_group = QGroupBox("使用技巧")
        tips_layout = QVBoxLayout(tips_group)
        
        tips_text = QTextEdit()
        tips_text.setReadOnly(True)
        tips_text.setMaximumHeight(250)
        tips_text.setHtml("""
        <h3>获得最佳效果的建议</h3>
        <ul>
            <li><b>参数选择：</b>对于轻度雾霾，建议使用"轻度去雾"预设；重度雾霾使用"重度去雾"预设</li>
            <li><b>图像质量：</b>输入图像分辨率建议在512x512到2048x2048之间，过小或过大都可能影响效果</li>
            <li><b>处理时间：</b>启用"非均质调整"会增加处理时间，但能获得更好的去雾效果</li>
            <li><b>内存使用：</b>处理大尺寸图像时建议启用"内存优化"选项</li>
            <li><b>结果对比：</b>使用分屏预览功能对比原图和去雾结果，便于评估效果</li>
        </ul>
        """)
        tips_layout.addWidget(tips_text)
        scroll_layout.addWidget(tips_group)
        
        # 常见问题
        faq_group = QGroupBox("常见问题")
        faq_layout = QVBoxLayout(faq_group)
        
        faq_text = QTextEdit()
        faq_text.setReadOnly(True)
        faq_text.setMaximumHeight(300)
        faq_text.setHtml("""
        <h3>常见问题解答</h3>
        
        <p><b>Q: 为什么处理后的图像看起来不自然？</b></p>
        <p>A: 可能是去雾强度过大，建议调整"最小透射率"参数，增大该值可以保留更多雾气，使图像看起来更自然。</p>
        
        <p><b>Q: 处理速度很慢怎么办？</b></p>
        <p>A: 1) 关闭"非均质调整"功能；2) 启用"内存优化"；3) 减小"引导滤波半径"参数。</p>
        
        <p><b>Q: 支持哪些图像格式？</b></p>
        <p>A: 支持JPG、JPEG、PNG、BMP、TIFF格式的图像文件。</p>
        
        <p><b>Q: 如何批量处理多张图像？</b></p>
        <p>A: 目前版本暂不支持批量处理，请逐张处理图像。</p>
        
        <p><b>Q: 处理过程中出现错误怎么办？</b></p>
        <p>A: 请检查图像文件是否损坏，确保有足够的内存空间，必要时重启应用程序。</p>
        """)
        faq_layout.addWidget(faq_text)
        scroll_layout.addWidget(faq_group)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)


class AlgorithmTab(QWidget):
    """算法说明标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 算法概述
        overview_group = QGroupBox("算法概述")
        overview_layout = QVBoxLayout(overview_group)
        
        overview_text = QTextEdit()
        overview_text.setReadOnly(True)
        overview_text.setMaximumHeight(200)
        overview_text.setHtml("""
        <h3>非均质有雾图像去雾算法</h3>
        <p>本系统采用基于<b>改进暗通道先验</b>的去雾算法，专门针对<b>非均质雾霾分布</b>进行优化。
        算法能够自适应地处理不同区域的雾霾密度差异，有效恢复图像的清晰度和对比度。</p>
        
        <p><b>核心创新点：</b></p>
        <ul>
            <li>非均质雾密度自适应调整</li>
            <li>改进的大气光估计方法</li>
            <li>边缘保持的透射率优化</li>
            <li>智能后处理增强</li>
        </ul>
        """)
        overview_layout.addWidget(overview_text)
        scroll_layout.addWidget(overview_group)
        
        # 算法流程
        process_group = QGroupBox("算法流程")
        process_layout = QVBoxLayout(process_group)
        
        process_text = QTextEdit()
        process_text.setReadOnly(True)
        process_text.setMaximumHeight(350)
        process_text.setHtml("""
        <h3>处理流程</h3>
        
        <p><b>1. 暗通道计算</b></p>
        <p>计算输入图像的暗通道图，用于估计雾霾的分布情况。暗通道反映了图像中最暗像素的分布。</p>
        
        <p><b>2. 大气光估计</b></p>
        <p>基于暗通道图中最亮的像素区域估计大气光值，这代表了无穷远处的天空亮度。</p>
        
        <p><b>3. 透射率估计</b></p>
        <p>利用暗通道先验和大气光值计算初始透射率图，表示光线穿过雾霾到达相机的比例。</p>
        
        <p><b>4. 引导滤波优化</b></p>
        <p>使用引导滤波对透射率图进行优化，保持边缘信息的同时平滑噪声。</p>
        
        <p><b>5. 非均质调整</b></p>
        <p>根据图像不同区域的雾霾密度差异，自适应调整透射率，实现非均质去雾。</p>
        
        <p><b>6. 场景辐射恢复</b></p>
        <p>基于大气散射模型恢复无雾的场景辐射，得到去雾结果。</p>
        
        <p><b>7. 后处理增强</b></p>
        <p>对去雾结果进行对比度和饱和度增强，提升视觉效果。</p>
        """)
        process_layout.addWidget(process_text)
        scroll_layout.addWidget(process_group)
        
        # 参数说明
        params_group = QGroupBox("关键参数说明")
        params_layout = QVBoxLayout(params_group)
        
        params_text = QTextEdit()
        params_text.setReadOnly(True)
        params_text.setMaximumHeight(400)
        params_text.setHtml("""
        <h3>重要参数详解</h3>
        
        <p><b>暗通道窗口大小：</b>计算暗通道时的邻域窗口大小，影响雾霾检测的精度。较大的窗口能更好地检测大面积雾霾。</p>
        
        <p><b>最小透射率：</b>透射率的下限值，防止过度去雾导致图像失真。较大的值会保留更多雾气。</p>
        
        <p><b>Omega参数：</b>控制雾气保留程度的参数，接近1时去雾更彻底，接近0.8时保留更多自然雾气。</p>
        
        <p><b>引导滤波半径：</b>影响透射率图的平滑程度，较大的半径能更好地保持边缘，但计算量增加。</p>
        
        <p><b>正则化参数：</b>控制引导滤波的平滑强度，较小的值保持更多细节，较大的值平滑效果更强。</p>
        
        <p><b>分块大小：</b>非均质处理时的图像分块大小，影响局部自适应的精度。</p>
        
        <p><b>自适应强度：</b>非均质调整的强度系数，控制不同区域透射率调整的幅度。</p>
        
        <p><b>对比度/饱和度增强：</b>后处理阶段的图像增强系数，提升去雾结果的视觉效果。</p>
        """)
        params_layout.addWidget(params_text)
        scroll_layout.addWidget(params_group)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)


class AboutTab(QWidget):
    """关于标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # 应用信息
        app_info_frame = QFrame()
        app_info_frame.setFrameStyle(QFrame.Shape.Box)
        app_info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        
        app_info_layout = QVBoxLayout(app_info_frame)
        
        # 应用标题
        title_label = QLabel("非均质有雾图像去雾系统")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        app_info_layout.addWidget(title_label)
        
        # 版本信息
        version_label = QLabel("版本 1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setFont(QFont("Arial", 12))
        version_label.setStyleSheet("color: #6c757d; margin-bottom: 15px;")
        app_info_layout.addWidget(version_label)
        
        # 描述信息
        desc_text = QTextEdit()
        desc_text.setReadOnly(True)
        desc_text.setMaximumHeight(150)
        desc_text.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: transparent;
                font-size: 11px;
            }
        """)
        desc_text.setHtml("""
        <p style="text-align: center; line-height: 1.6;">
        <b>专业的图像去雾处理工具</b><br>
        基于改进的暗通道先验算法，专门针对非均质雾霾分布进行优化。<br>
        提供直观的用户界面和丰富的参数调节功能，<br>
        帮助用户获得高质量的去雾效果。
        </p>
        """)
        app_info_layout.addWidget(desc_text)
        
        layout.addWidget(app_info_frame)
        
        # 开发信息
        dev_info_group = QGroupBox("开发信息")
        dev_info_layout = QGridLayout(dev_info_group)
        
        dev_info_layout.addWidget(QLabel("开发者:"), 0, 0)
        dev_info_layout.addWidget(QLabel("图像处理研究团队"), 0, 1)
        
        dev_info_layout.addWidget(QLabel("开发语言:"), 1, 0)
        dev_info_layout.addWidget(QLabel("Python 3.9+"), 1, 1)
        
        dev_info_layout.addWidget(QLabel("界面框架:"), 2, 0)
        dev_info_layout.addWidget(QLabel("PyQt6"), 2, 1)
        
        dev_info_layout.addWidget(QLabel("图像处理:"), 3, 0)
        dev_info_layout.addWidget(QLabel("OpenCV, NumPy, SciPy"), 3, 1)
        
        dev_info_layout.addWidget(QLabel("开发时间:"), 4, 0)
        dev_info_layout.addWidget(QLabel("2025年"), 4, 1)
        
        layout.addWidget(dev_info_group)
        
        # 技术特性
        features_group = QGroupBox("技术特性")
        features_layout = QVBoxLayout(features_group)
        
        features_text = QTextEdit()
        features_text.setReadOnly(True)
        features_text.setMaximumHeight(120)
        features_text.setHtml("""
        <ul style="line-height: 1.5;">
            <li><b>先进算法：</b>基于改进暗通道先验的非均质去雾算法</li>
            <li><b>高效处理：</b>优化的图像处理流程，支持大尺寸图像</li>
            <li><b>用户友好：</b>直观的图形界面，支持拖拽操作</li>
            <li><b>参数丰富：</b>提供多种预设和自定义参数调节</li>
            <li><b>格式支持：</b>支持主流图像格式的读取和保存</li>
        </ul>
        """)
        features_layout.addWidget(features_text)
        
        layout.addWidget(features_group)
        
        # 联系信息
        contact_group = QGroupBox("联系方式")
        contact_layout = QVBoxLayout(contact_group)
        
        contact_text = QTextEdit()
        contact_text.setReadOnly(True)
        contact_text.setMaximumHeight(80)
        contact_text.setHtml("""
        <p style="line-height: 1.5;">
        <b>技术支持：</b>support@dehazing.com<br>
        <b>项目主页：</b><a href="https://github.com/dehazing/non-homogeneous">GitHub Repository</a><br>
        <b>文档中心：</b><a href="https://docs.dehazing.com">在线文档</a>
        </p>
        """)
        contact_layout.addWidget(contact_text)
        
        layout.addWidget(contact_group)
        
        layout.addStretch()


class HelpDialog(QDialog):
    """帮助对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("帮助")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 用户手册标签页
        self.manual_tab = UserManualTab()
        self.tab_widget.addTab(self.manual_tab, "用户手册")
        
        # 算法说明标签页
        self.algorithm_tab = AlgorithmTab()
        self.tab_widget.addTab(self.algorithm_tab, "算法说明")
        
        # 关于标签页
        self.about_tab = AboutTab()
        self.tab_widget.addTab(self.about_tab, "关于")
        
        layout.addWidget(self.tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 在线帮助按钮
        online_help_btn = QPushButton("在线帮助")
        online_help_btn.clicked.connect(self.open_online_help)
        button_layout.addWidget(online_help_btn)
        
        # 反馈建议按钮
        feedback_btn = QPushButton("反馈建议")
        feedback_btn.clicked.connect(self.open_feedback)
        button_layout.addWidget(feedback_btn)
        
        button_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # 应用样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 1px solid #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #e9ecef;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                background-color: #ffffff;
            }
        """)
    
    def open_online_help(self):
        """打开在线帮助"""
        try:
            url = QUrl("https://docs.dehazing.com")
            QDesktopServices.openUrl(url)
        except Exception as e:
            self.logger.error(f"打开在线帮助失败: {str(e)}")
    
    def open_feedback(self):
        """打开反馈页面"""
        try:
            url = QUrl("https://github.com/dehazing/non-homogeneous/issues")
            QDesktopServices.openUrl(url)
        except Exception as e:
            self.logger.error(f"打开反馈页面失败: {str(e)}")


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = HelpDialog()
    dialog.show()
    sys.exit(app.exec())