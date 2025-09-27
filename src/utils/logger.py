#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具模块
提供统一的日志管理功能
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',    # 青色
        'INFO': '\033[32m',     # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',    # 红色
        'CRITICAL': '\033[35m', # 紫色
        'RESET': '\033[0m'      # 重置
    }
    
    def format(self, record):
        # 获取原始格式化结果
        log_message = super().format(record)
        
        # 添加颜色
        if record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS['RESET']
            log_message = f"{color}{log_message}{reset}"
        
        return log_message


class LoggerManager:
    """日志管理器"""
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        初始化日志管理器
        
        Args:
            log_dir: 日志文件目录，默认为当前目录下的logs文件夹
        """
        if log_dir is None:
            self.log_dir = Path("logs")
        else:
            self.log_dir = Path(log_dir)
        
        # 确保日志目录存在
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志文件路径
        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"dehazing_{today}.log"
        
        # 是否已初始化
        self._initialized = False
    
    def setup_logger(self, 
                    name: str = "dehazing",
                    level: int = logging.INFO,
                    console_output: bool = True,
                    file_output: bool = True,
                    colored_console: bool = True) -> logging.Logger:
        """
        设置日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别
            console_output: 是否输出到控制台
            file_output: 是否输出到文件
            colored_console: 控制台是否使用彩色输出
        
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        # 获取或创建日志记录器
        logger = logging.getLogger(name)
        
        # 避免重复初始化
        if self._initialized and logger.handlers:
            return logger
        
        # 设置日志级别
        logger.setLevel(level)
        
        # 清除现有处理器
        logger.handlers.clear()
        
        # 日志格式
        detailed_format = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        simple_format = "%(asctime)s - %(levelname)s - %(message)s"
        
        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            
            if colored_console:
                console_formatter = ColoredFormatter(simple_format)
            else:
                console_formatter = logging.Formatter(simple_format)
            
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        # 文件处理器
        if file_output:
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别的日志
            
            file_formatter = logging.Formatter(detailed_format)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        # 防止日志传播到根记录器
        logger.propagate = False
        
        self._initialized = True
        
        # 记录初始化信息
        logger.info(f"日志系统已初始化 - 级别: {logging.getLevelName(level)}")
        if file_output:
            logger.info(f"日志文件: {self.log_file}")
        
        return logger
    
    def get_logger(self, name: str = "dehazing") -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
        
        Returns:
            logging.Logger: 日志记录器
        """
        logger = logging.getLogger(name)
        
        # 如果还没有初始化，使用默认配置
        if not logger.handlers:
            return self.setup_logger(name)
        
        return logger
    
    def set_level(self, level: int, logger_name: str = "dehazing"):
        """
        设置日志级别
        
        Args:
            level: 日志级别
            logger_name: 日志记录器名称
        """
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        
        # 同时设置所有处理器的级别
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                handler.setLevel(level)
    
    def cleanup_old_logs(self, days_to_keep: int = 7):
        """
        清理旧的日志文件
        
        Args:
            days_to_keep: 保留的天数
        """
        try:
            current_time = datetime.now()
            
            for log_file in self.log_dir.glob("dehazing_*.log"):
                # 从文件名提取日期
                try:
                    date_str = log_file.stem.split("_")[1]
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # 计算文件年龄
                    age_days = (current_time - file_date).days
                    
                    if age_days > days_to_keep:
                        log_file.unlink()
                        print(f"已删除旧日志文件: {log_file}")
                
                except (ValueError, IndexError):
                    # 跳过无法解析日期的文件
                    continue
        
        except Exception as e:
            print(f"清理日志文件时出错: {e}")
    
    def get_log_info(self) -> dict:
        """
        获取日志信息
        
        Returns:
            dict: 日志信息字典
        """
        return {
            'log_dir': str(self.log_dir),
            'current_log_file': str(self.log_file),
            'log_file_exists': self.log_file.exists(),
            'log_file_size': self.log_file.stat().st_size if self.log_file.exists() else 0,
            'initialized': self._initialized
        }


# 全局日志管理器实例
_logger_manager: Optional[LoggerManager] = None


def get_logger_manager() -> LoggerManager:
    """
    获取全局日志管理器实例
    
    Returns:
        LoggerManager: 日志管理器实例
    """
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    return _logger_manager


def get_logger(name: str = "dehazing") -> logging.Logger:
    """
    获取日志记录器（便捷函数）
    
    Args:
        name: 日志记录器名称
    
    Returns:
        logging.Logger: 日志记录器
    """
    return get_logger_manager().get_logger(name)


def setup_logging(level: int = logging.INFO, 
                 console_output: bool = True,
                 file_output: bool = True,
                 colored_console: bool = True) -> logging.Logger:
    """
    设置应用程序日志（便捷函数）
    
    Args:
        level: 日志级别
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
        colored_console: 控制台是否使用彩色输出
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    return get_logger_manager().setup_logger(
        level=level,
        console_output=console_output,
        file_output=file_output,
        colored_console=colored_console
    )