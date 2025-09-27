#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责应用程序配置的加载、保存和管理
"""

import json
import os
from pathlib import Path
from typing import Optional
import logging

from .models import UserSettings, ProcessingRecord


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为用户主目录下的.dehazing文件夹
        """
        if config_dir is None:
            self.config_dir = Path.home() / ".dehazing"
        else:
            self.config_dir = Path(config_dir)
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置文件路径
        self.settings_file = self.config_dir / "settings.json"
        self.history_file = self.config_dir / "history.json"
        
        # 日志配置
        self.logger = logging.getLogger(__name__)
        
        # 当前设置
        self._settings: Optional[UserSettings] = None
    
    def load_settings(self) -> UserSettings:
        """
        加载用户设置
        
        Returns:
            UserSettings: 用户设置对象
        """
        if self._settings is not None:
            return self._settings
        
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._settings = UserSettings.from_dict(data)
                self.logger.info(f"已加载用户设置: {self.settings_file}")
            else:
                self._settings = UserSettings()
                self.logger.info("使用默认用户设置")
        except Exception as e:
            self.logger.error(f"加载用户设置失败: {e}")
            self._settings = UserSettings()
        
        return self._settings
    
    def save_settings(self, settings: Optional[UserSettings] = None) -> bool:
        """
        保存用户设置
        
        Args:
            settings: 要保存的设置对象，如果为None则保存当前设置
        
        Returns:
            bool: 保存是否成功
        """
        if settings is None:
            settings = self._settings
        
        if settings is None:
            self.logger.warning("没有设置对象可保存")
            return False
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings.to_dict(), f, indent=2, ensure_ascii=False)
            
            self._settings = settings
            self.logger.info(f"用户设置已保存: {self.settings_file}")
            return True
        except Exception as e:
            self.logger.error(f"保存用户设置失败: {e}")
            return False
    
    def get_settings(self) -> UserSettings:
        """
        获取当前用户设置
        
        Returns:
            UserSettings: 当前用户设置
        """
        if self._settings is None:
            return self.load_settings()
        return self._settings
    
    def update_settings(self, **kwargs) -> bool:
        """
        更新用户设置
        
        Args:
            **kwargs: 要更新的设置项
        
        Returns:
            bool: 更新是否成功
        """
        settings = self.get_settings()
        
        try:
            for key, value in kwargs.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
                else:
                    self.logger.warning(f"未知的设置项: {key}")
            
            return self.save_settings(settings)
        except Exception as e:
            self.logger.error(f"更新用户设置失败: {e}")
            return False
    
    def load_processing_history(self) -> list[ProcessingRecord]:
        """
        加载处理历史记录
        
        Returns:
            list[ProcessingRecord]: 处理历史记录列表
        """
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                history = []
                for record_data in data:
                    try:
                        record = ProcessingRecord.from_dict(record_data)
                        history.append(record)
                    except Exception as e:
                        self.logger.warning(f"跳过无效的历史记录: {e}")
                
                self.logger.info(f"已加载 {len(history)} 条处理历史记录")
                return history
            else:
                self.logger.info("没有找到历史记录文件")
                return []
        except Exception as e:
            self.logger.error(f"加载处理历史失败: {e}")
            return []
    
    def save_processing_history(self, history: list[ProcessingRecord]) -> bool:
        """
        保存处理历史记录
        
        Args:
            history: 处理历史记录列表
        
        Returns:
            bool: 保存是否成功
        """
        try:
            data = [record.to_dict() for record in history]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"已保存 {len(history)} 条处理历史记录")
            return True
        except Exception as e:
            self.logger.error(f"保存处理历史失败: {e}")
            return False
    
    def add_processing_record(self, record: ProcessingRecord) -> bool:
        """
        添加处理记录到历史
        
        Args:
            record: 处理记录
        
        Returns:
            bool: 添加是否成功
        """
        try:
            history = self.load_processing_history()
            history.append(record)
            
            # 限制历史记录数量（保留最近100条）
            if len(history) > 100:
                history = history[-100:]
            
            return self.save_processing_history(history)
        except Exception as e:
            self.logger.error(f"添加处理记录失败: {e}")
            return False
    
    def clear_processing_history(self) -> bool:
        """
        清空处理历史记录
        
        Returns:
            bool: 清空是否成功
        """
        try:
            if self.history_file.exists():
                self.history_file.unlink()
            self.logger.info("处理历史记录已清空")
            return True
        except Exception as e:
            self.logger.error(f"清空处理历史失败: {e}")
            return False
    
    def get_user_settings(self) -> UserSettings:
        """
        获取用户设置（兼容方法）
        
        Returns:
            UserSettings: 用户设置对象
        """
        return self.get_settings()
    
    def save_config(self, settings: Optional[UserSettings] = None) -> bool:
        """
        保存配置（兼容方法）
        
        Args:
            settings: 要保存的设置对象，如果为None则保存当前设置
        
        Returns:
            bool: 保存是否成功
        """
        return self.save_settings(settings)
    
    def load_config(self) -> UserSettings:
        """
        加载配置（兼容方法）
        
        Returns:
            UserSettings: 用户设置对象
        """
        return self.load_settings()
    
    def update_user_settings(self, settings: UserSettings) -> bool:
        """
        更新用户设置
        
        Args:
            settings: 新的用户设置对象
        
        Returns:
            bool: 更新是否成功
        """
        try:
            self._settings = settings
            return self.save_settings(settings)
        except Exception as e:
            self.logger.error(f"更新用户设置失败: {e}")
            return False
    
    def get_config_info(self) -> dict:
        """
        获取配置信息
        
        Returns:
            dict: 配置信息字典
        """
        return {
            'config_dir': str(self.config_dir),
            'settings_file': str(self.settings_file),
            'history_file': str(self.history_file),
            'settings_exists': self.settings_file.exists(),
            'history_exists': self.history_file.exists()
        }


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """
    获取全局配置管理器实例
    
    Returns:
        ConfigManager: 配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def init_config_manager(config_dir: Optional[str] = None) -> ConfigManager:
    """
    初始化全局配置管理器
    
    Args:
        config_dir: 配置文件目录
    
    Returns:
        ConfigManager: 配置管理器实例
    """
    global _config_manager
    _config_manager = ConfigManager(config_dir)
    return _config_manager