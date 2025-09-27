#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非均质有雾图像去雾应用程序
主程序入口文件

作者: 开发团队
版本: 1.0.0
创建时间: 2025
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.main_window import MainWindow
from src.core.config import ConfigManager
from src.utils.logger import get_logger


def main():
    """
    应用程序主入口函数
    """
    # 设置日志
    logger = get_logger()
    logger.info("启动非均质有雾图像去雾应用程序")
    
    # 创建QApplication实例
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("非均质有雾图像去雾工具")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("图像处理实验室")
    
    # PyQt6 默认支持高DPI
    
    try:
        # 创建主窗口
        main_window = MainWindow()
        
        # 显示主窗口
        main_window.show()
        
        logger.info("应用程序界面已启动")
        
        # 运行应用程序事件循环
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()