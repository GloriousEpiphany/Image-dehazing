# -*- coding: utf-8 -*-
"""
设置对话框模块
提供算法参数调整和应用设置功能
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
    QLabel, QSpinBox, QDoubleSpinBox, QSlider, QCheckBox, QComboBox,
    QPushButton, QGroupBox, QFrame, QMessageBox, QFileDialog,
    QLineEdit, QTextEdit, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette

from ..core.models import DehazingParameters, UserSettings
from ..core.config import ConfigManager
from ..utils.logger import get_logger


class ParameterWidget(QWidget):
    """参数调整组件基类"""
    
    value_changed = pyqtSignal()
    
    def __init__(self, name: str, description: str = "", parent=None):
        super().__init__(parent)
        self.name = name
        self.description = description
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 参数名称
        name_label = QLabel(self.name)
        name_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout.addWidget(name_label)
        
        # 参数描述
        if self.description:
            desc_label = QLabel(self.description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #666; font-size: 9px;")
            layout.addWidget(desc_label)
        
        # 子类实现具体控件
        self.create_control(layout)
    
    def create_control(self, layout):
        """创建控件（子类实现）"""
        pass
    
    def get_value(self):
        """获取参数值（子类实现）"""
        pass
    
    def set_value(self, value):
        """设置参数值（子类实现）"""
        pass


class SliderParameterWidget(ParameterWidget):
    """滑块参数组件"""
    
    def __init__(self, name: str, min_val: float, max_val: float, 
                 step: float = 0.1, decimals: int = 2, 
                 description: str = "", parent=None):
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.decimals = decimals
        super().__init__(name, description, parent)
    
    def create_control(self, layout):
        control_layout = QHBoxLayout()
        
        # 滑块
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(int(self.min_val / self.step))
        self.slider.setMaximum(int(self.max_val / self.step))
        self.slider.valueChanged.connect(self.on_slider_changed)
        
        # 数值输入框
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setMinimum(self.min_val)
        self.spinbox.setMaximum(self.max_val)
        self.spinbox.setSingleStep(self.step)
        self.spinbox.setDecimals(self.decimals)
        self.spinbox.setFixedWidth(80)
        self.spinbox.valueChanged.connect(self.on_spinbox_changed)
        
        control_layout.addWidget(self.slider)
        control_layout.addWidget(self.spinbox)
        layout.addLayout(control_layout)
    
    def on_slider_changed(self, value):
        real_value = value * self.step
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(real_value)
        self.spinbox.blockSignals(False)
        self.value_changed.emit()
    
    def on_spinbox_changed(self, value):
        slider_value = int(value / self.step)
        self.slider.blockSignals(True)
        self.slider.setValue(slider_value)
        self.slider.blockSignals(False)
        self.value_changed.emit()
    
    def get_value(self):
        return self.spinbox.value()
    
    def set_value(self, value):
        self.spinbox.setValue(value)
        self.slider.setValue(int(value / self.step))


class IntParameterWidget(ParameterWidget):
    """整数参数组件"""
    
    def __init__(self, name: str, min_val: int, max_val: int, 
                 description: str = "", parent=None):
        self.min_val = min_val
        self.max_val = max_val
        super().__init__(name, description, parent)
    
    def create_control(self, layout):
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(self.min_val)
        self.spinbox.setMaximum(self.max_val)
        self.spinbox.valueChanged.connect(self.value_changed.emit)
        layout.addWidget(self.spinbox)
    
    def get_value(self):
        return self.spinbox.value()
    
    def set_value(self, value):
        self.spinbox.setValue(value)


class BoolParameterWidget(ParameterWidget):
    """布尔参数组件"""
    
    def create_control(self, layout):
        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self.value_changed.emit)
        layout.addWidget(self.checkbox)
    
    def get_value(self):
        return self.checkbox.isChecked()
    
    def set_value(self, value):
        self.checkbox.setChecked(value)


class ComboParameterWidget(ParameterWidget):
    """下拉选择参数组件"""
    
    def __init__(self, name: str, options: list, 
                 description: str = "", parent=None):
        self.options = options
        super().__init__(name, description, parent)
    
    def create_control(self, layout):
        self.combobox = QComboBox()
        self.combobox.addItems([str(option) for option in self.options])
        self.combobox.currentTextChanged.connect(self.value_changed.emit)
        layout.addWidget(self.combobox)
    
    def get_value(self):
        return self.combobox.currentText()
    
    def set_value(self, value):
        index = self.combobox.findText(str(value))
        if index >= 0:
            self.combobox.setCurrentIndex(index)


class DehazingParametersTab(QWidget):
    """去雾参数标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.parameter_widgets = {}
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 暗通道参数组
        dark_channel_group = QGroupBox("暗通道先验参数")
        dark_channel_layout = QGridLayout(dark_channel_group)
        
        # 暗通道窗口大小
        self.parameter_widgets['dark_channel_size'] = IntParameterWidget(
            "暗通道窗口大小",
            min_val=3,
            max_val=21,
            description="计算暗通道时使用的窗口大小，通常为奇数"
        )
        dark_channel_layout.addWidget(self.parameter_widgets['dark_channel_size'], 0, 0)
        
        # 大气光估计参数
        self.parameter_widgets['atmosphere_ratio'] = SliderParameterWidget(
            "大气光比例",
            min_val=0.001,
            max_val=0.01,
            step=0.001,
            decimals=3,
            description="用于大气光估计的最亮像素比例"
        )
        dark_channel_layout.addWidget(self.parameter_widgets['atmosphere_ratio'], 0, 1)
        
        scroll_layout.addWidget(dark_channel_group)
        
        # 透射率参数组
        transmission_group = QGroupBox("透射率估计参数")
        transmission_layout = QGridLayout(transmission_group)
        
        # 最小透射率
        self.parameter_widgets['min_transmission'] = SliderParameterWidget(
            "最小透射率",
            min_val=0.1,
            max_val=0.5,
            step=0.01,
            decimals=2,
            description="透射率的最小值，防止过度去雾"
        )
        transmission_layout.addWidget(self.parameter_widgets['min_transmission'], 0, 0)
        
        # omega参数
        self.parameter_widgets['omega'] = SliderParameterWidget(
            "Omega参数",
            min_val=0.8,
            max_val=1.0,
            step=0.01,
            decimals=2,
            description="保留少量雾气的参数，使图像更自然"
        )
        transmission_layout.addWidget(self.parameter_widgets['omega'], 0, 1)
        
        scroll_layout.addWidget(transmission_group)
        
        # 引导滤波参数组
        guided_filter_group = QGroupBox("引导滤波参数")
        guided_filter_layout = QGridLayout(guided_filter_group)
        
        # 滤波半径
        self.parameter_widgets['guided_filter_radius'] = IntParameterWidget(
            "滤波半径",
            min_val=1,
            max_val=100,
            description="引导滤波的半径，影响边缘保持效果"
        )
        guided_filter_layout.addWidget(self.parameter_widgets['guided_filter_radius'], 0, 0)
        
        # 正则化参数
        self.parameter_widgets['guided_filter_eps'] = SliderParameterWidget(
            "正则化参数",
            min_val=0.001,
            max_val=0.1,
            step=0.001,
            decimals=3,
            description="引导滤波的正则化参数，控制平滑程度"
        )
        guided_filter_layout.addWidget(self.parameter_widgets['guided_filter_eps'], 0, 1)
        
        scroll_layout.addWidget(guided_filter_group)
        
        # 非均质调整参数组
        non_homo_group = QGroupBox("非均质调整参数")
        non_homo_layout = QGridLayout(non_homo_group)
        
        # 启用非均质调整
        self.parameter_widgets['enable_non_homogeneous'] = BoolParameterWidget(
            "启用非均质调整",
            description="是否启用非均质雾密度调整"
        )
        non_homo_layout.addWidget(self.parameter_widgets['enable_non_homogeneous'], 0, 0)
        
        # 分块大小
        self.parameter_widgets['block_size'] = IntParameterWidget(
            "分块大小",
            min_val=16,
            max_val=128,
            description="非均质处理时的图像分块大小"
        )
        non_homo_layout.addWidget(self.parameter_widgets['block_size'], 0, 1)
        
        # 自适应强度
        self.parameter_widgets['adaptive_strength'] = SliderParameterWidget(
            "自适应强度",
            min_val=0.1,
            max_val=2.0,
            step=0.1,
            decimals=1,
            description="非均质调整的强度"
        )
        non_homo_layout.addWidget(self.parameter_widgets['adaptive_strength'], 1, 0)
        
        scroll_layout.addWidget(non_homo_group)
        
        # 后处理参数组
        post_process_group = QGroupBox("后处理参数")
        post_process_layout = QGridLayout(post_process_group)
        
        # 启用后处理
        self.parameter_widgets['enable_post_processing'] = BoolParameterWidget(
            "启用后处理",
            description="是否启用图像后处理增强"
        )
        post_process_layout.addWidget(self.parameter_widgets['enable_post_processing'], 0, 0)
        
        # 对比度增强
        self.parameter_widgets['contrast_enhancement'] = SliderParameterWidget(
            "对比度增强",
            min_val=0.8,
            max_val=1.5,
            step=0.1,
            decimals=1,
            description="对比度增强系数"
        )
        post_process_layout.addWidget(self.parameter_widgets['contrast_enhancement'], 0, 1)
        
        # 饱和度增强
        self.parameter_widgets['saturation_enhancement'] = SliderParameterWidget(
            "饱和度增强",
            min_val=0.8,
            max_val=1.5,
            step=0.1,
            decimals=1,
            description="饱和度增强系数"
        )
        post_process_layout.addWidget(self.parameter_widgets['saturation_enhancement'], 1, 0)
        
        scroll_layout.addWidget(post_process_group)
        
        # 添加弹性空间
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # 预设参数按钮
        preset_layout = QHBoxLayout()
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["默认参数", "轻度去雾", "中度去雾", "重度去雾", "自定义"])
        self.preset_combo.currentTextChanged.connect(self.load_preset)
        preset_layout.addWidget(QLabel("预设参数:"))
        preset_layout.addWidget(self.preset_combo)
        
        preset_layout.addStretch()
        
        reset_btn = QPushButton("重置为默认")
        reset_btn.clicked.connect(self.reset_to_default)
        preset_layout.addWidget(reset_btn)
        
        layout.addLayout(preset_layout)
    
    def get_parameters(self) -> DehazingParameters:
        """获取当前参数"""
        try:
            return DehazingParameters(
                dark_channel_size=self.parameter_widgets['dark_channel_size'].get_value(),
                atmosphere_ratio=self.parameter_widgets['atmosphere_ratio'].get_value(),
                min_transmission=self.parameter_widgets['min_transmission'].get_value(),
                omega=self.parameter_widgets['omega'].get_value(),
                guided_filter_radius=self.parameter_widgets['guided_filter_radius'].get_value(),
                guided_filter_eps=self.parameter_widgets['guided_filter_eps'].get_value(),
                enable_non_homogeneous=self.parameter_widgets['enable_non_homogeneous'].get_value(),
                block_size=self.parameter_widgets['block_size'].get_value(),
                adaptive_strength=self.parameter_widgets['adaptive_strength'].get_value(),
                enable_post_processing=self.parameter_widgets['enable_post_processing'].get_value(),
                contrast_enhancement=self.parameter_widgets['contrast_enhancement'].get_value(),
                saturation_enhancement=self.parameter_widgets['saturation_enhancement'].get_value()
            )
        except Exception as e:
            self.logger.error(f"获取参数失败: {str(e)}")
            return DehazingParameters()  # 返回默认参数
    
    def set_parameters(self, parameters: DehazingParameters):
        """设置参数"""
        try:
            self.parameter_widgets['dark_channel_size'].set_value(parameters.dark_channel_size)
            self.parameter_widgets['atmosphere_ratio'].set_value(parameters.atmosphere_ratio)
            self.parameter_widgets['min_transmission'].set_value(parameters.min_transmission)
            self.parameter_widgets['omega'].set_value(parameters.omega)
            self.parameter_widgets['guided_filter_radius'].set_value(parameters.guided_filter_radius)
            self.parameter_widgets['guided_filter_eps'].set_value(parameters.guided_filter_eps)
            self.parameter_widgets['enable_non_homogeneous'].set_value(parameters.enable_non_homogeneous)
            self.parameter_widgets['block_size'].set_value(parameters.block_size)
            self.parameter_widgets['adaptive_strength'].set_value(parameters.adaptive_strength)
            self.parameter_widgets['enable_post_processing'].set_value(parameters.enable_post_processing)
            self.parameter_widgets['contrast_enhancement'].set_value(parameters.contrast_enhancement)
            self.parameter_widgets['saturation_enhancement'].set_value(parameters.saturation_enhancement)
        except Exception as e:
            self.logger.error(f"设置参数失败: {str(e)}")
    
    def load_preset(self, preset_name: str):
        """加载预设参数"""
        presets = {
            "默认参数": DehazingParameters(),
            "轻度去雾": DehazingParameters(
                min_transmission=0.3,
                omega=0.95,
                adaptive_strength=0.5,
                contrast_enhancement=1.0,
                saturation_enhancement=1.0
            ),
            "中度去雾": DehazingParameters(
                min_transmission=0.2,
                omega=0.9,
                adaptive_strength=1.0,
                contrast_enhancement=1.1,
                saturation_enhancement=1.1
            ),
            "重度去雾": DehazingParameters(
                min_transmission=0.1,
                omega=0.85,
                adaptive_strength=1.5,
                contrast_enhancement=1.2,
                saturation_enhancement=1.2
            )
        }
        
        if preset_name in presets:
            self.set_parameters(presets[preset_name])
    
    def reset_to_default(self):
        """重置为默认参数"""
        self.set_parameters(DehazingParameters())
        self.preset_combo.setCurrentText("默认参数")


class GeneralSettingsTab(QWidget):
    """通用设置标签页"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 输出设置组
        output_group = QGroupBox("输出设置")
        output_layout = QGridLayout(output_group)
        
        # 默认输出目录
        output_layout.addWidget(QLabel("默认输出目录:"), 0, 0)
        self.output_dir_edit = QLineEdit()
        output_layout.addWidget(self.output_dir_edit, 0, 1)
        
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(browse_btn, 0, 2)
        
        # 输出文件名格式
        output_layout.addWidget(QLabel("文件名后缀:"), 1, 0)
        self.filename_suffix_edit = QLineEdit("_dehazed")
        output_layout.addWidget(self.filename_suffix_edit, 1, 1, 1, 2)
        
        # 自动保存
        self.auto_save_checkbox = QCheckBox("处理完成后自动保存")
        output_layout.addWidget(self.auto_save_checkbox, 2, 0, 1, 3)
        
        layout.addWidget(output_group)
        
        # 性能设置组
        performance_group = QGroupBox("性能设置")
        performance_layout = QGridLayout(performance_group)
        
        # 最大图像尺寸
        performance_layout.addWidget(QLabel("最大处理尺寸:"), 0, 0)
        self.max_size_spinbox = QSpinBox()
        self.max_size_spinbox.setRange(512, 4096)
        self.max_size_spinbox.setSuffix(" px")
        self.max_size_spinbox.setValue(2048)
        performance_layout.addWidget(self.max_size_spinbox, 0, 1)
        
        # 内存优化
        self.memory_optimize_checkbox = QCheckBox("启用内存优化（处理大图像时）")
        self.memory_optimize_checkbox.setChecked(True)
        performance_layout.addWidget(self.memory_optimize_checkbox, 1, 0, 1, 2)
        
        layout.addWidget(performance_group)
        
        # 界面设置组
        ui_group = QGroupBox("界面设置")
        ui_layout = QGridLayout(ui_group)
        
        # 语言设置
        ui_layout.addWidget(QLabel("语言:"), 0, 0)
        self.language_combo = QComboBox()
        self.language_combo.addItems(["中文", "English"])
        ui_layout.addWidget(self.language_combo, 0, 1)
        
        # 主题设置
        ui_layout.addWidget(QLabel("主题:"), 1, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["默认", "深色", "浅色"])
        ui_layout.addWidget(self.theme_combo, 1, 1)
        
        # 显示处理时间
        self.show_time_checkbox = QCheckBox("显示处理时间")
        self.show_time_checkbox.setChecked(True)
        ui_layout.addWidget(self.show_time_checkbox, 2, 0, 1, 2)
        
        layout.addWidget(ui_group)
        
        layout.addStretch()
    
    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if dir_path:
            self.output_dir_edit.setText(dir_path)


class SettingsDialog(QDialog):
    """设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager()
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("参数设置")
        self.setMinimumSize(800, 600)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 去雾参数标签页
        self.dehazing_tab = DehazingParametersTab()
        self.tab_widget.addTab(self.dehazing_tab, "去雾参数")
        
        # 通用设置标签页
        self.general_tab = GeneralSettingsTab()
        self.tab_widget.addTab(self.general_tab, "通用设置")
        
        layout.addWidget(self.tab_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 导入/导出按钮
        import_btn = QPushButton("导入配置")
        import_btn.clicked.connect(self.import_config)
        button_layout.addWidget(import_btn)
        
        export_btn = QPushButton("导出配置")
        export_btn.clicked.connect(self.export_config)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        # 确定/取消按钮
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        apply_btn = QPushButton("应用")
        apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_btn)
        
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
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                border-bottom: 1px solid #ffffff;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
    
    def load_settings(self):
        """加载当前设置"""
        try:
            settings = self.config_manager.get_user_settings()
            
            # 加载去雾参数
            self.dehazing_tab.set_parameters(settings.dehazing_params)
            
            # 加载通用设置
            if hasattr(settings, 'output_directory'):
                self.general_tab.output_dir_edit.setText(settings.output_directory)
            if hasattr(settings, 'filename_suffix'):
                self.general_tab.filename_suffix_edit.setText(settings.filename_suffix)
            if hasattr(settings, 'auto_save'):
                self.general_tab.auto_save_checkbox.setChecked(settings.auto_save)
            
        except Exception as e:
            self.logger.error(f"加载设置失败: {str(e)}")
    
    def apply_settings(self):
        """应用设置"""
        try:
            # 获取当前设置
            settings = self.config_manager.get_user_settings()
            
            # 更新去雾参数
            settings.dehazing_params = self.dehazing_tab.get_parameters()
            
            # 更新通用设置
            settings.output_directory = self.general_tab.output_dir_edit.text()
            settings.filename_suffix = self.general_tab.filename_suffix_edit.text()
            settings.auto_save = self.general_tab.auto_save_checkbox.isChecked()
            
            # 保存设置
            self.config_manager.update_user_settings(settings)
            self.config_manager.save_config()
            
            self.logger.info("设置已保存")
            
        except Exception as e:
            self.logger.error(f"保存设置失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")
    
    def accept(self):
        """确定按钮"""
        self.apply_settings()
        super().accept()
    
    def import_config(self):
        """导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入配置文件",
            "",
            "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 解析配置数据
                if 'dehazing_params' in config_data:
                    params = DehazingParameters.from_dict(config_data['dehazing_params'])
                    self.dehazing_tab.set_parameters(params)
                
                QMessageBox.information(self, "成功", "配置导入成功")
                
            except Exception as e:
                self.logger.error(f"导入配置失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"导入配置失败: {str(e)}")
    
    def export_config(self):
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出配置文件",
            "dehazing_config.json",
            "JSON文件 (*.json);;所有文件 (*)"
        )
        
        if file_path:
            try:
                import json
                
                config_data = {
                    'dehazing_params': self.dehazing_tab.get_parameters().to_dict(),
                    'export_time': str(datetime.now()),
                    'version': '1.0'
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "成功", f"配置已导出到: {file_path}")
                
            except Exception as e:
                self.logger.error(f"导出配置失败: {str(e)}")
                QMessageBox.critical(self, "错误", f"导出配置失败: {str(e)}")


if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = SettingsDialog()
    dialog.show()
    sys.exit(app.exec())