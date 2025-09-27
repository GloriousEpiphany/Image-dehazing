#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型定义
包含图像信息、处理历史、用户设置等数据结构
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import json


class ProcessingStatus(Enum):
    """处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageFormat(Enum):
    """支持的图像格式"""
    JPEG = "jpeg"
    PNG = "png"
    BMP = "bmp"
    TIFF = "tiff"


@dataclass
class ImageInfo:
    """图像信息数据模型"""
    file_path: str
    file_name: str
    file_size: int  # 文件大小（字节）
    width: int
    height: int
    channels: int
    format: ImageFormat
    created_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'width': self.width,
            'height': self.height,
            'channels': self.channels,
            'format': self.format.value,
            'created_time': self.created_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageInfo':
        """从字典创建实例"""
        return cls(
            file_path=data['file_path'],
            file_name=data['file_name'],
            file_size=data['file_size'],
            width=data['width'],
            height=data['height'],
            channels=data['channels'],
            format=ImageFormat(data['format']),
            created_time=datetime.fromisoformat(data['created_time'])
        )


@dataclass
class DehazingParameters:
    """去雾算法参数"""
    # 暗通道先验参数
    dark_channel_size: int = 15  # 暗通道窗口大小
    
    # 大气光值估计参数
    atmosphere_ratio: float = 0.001  # 大气光估计比例
    
    # 透射率估计参数
    omega: float = 0.95  # 去雾强度参数
    min_transmission: float = 0.1  # 最小透射率阈值
    
    # 导向滤波参数
    guided_filter_radius: int = 60  # 导向滤波半径
    guided_filter_eps: float = 0.0001  # 导向滤波正则化参数
    
    # 非均质处理参数
    enable_non_homogeneous: bool = True  # 启用非均质处理
    block_size: int = 32  # 分块大小
    adaptive_strength: float = 1.0  # 自适应强度
    
    # 后处理参数
    enable_post_processing: bool = True  # 启用后处理
    contrast_enhancement: float = 1.0  # 对比度增强参数
    saturation_enhancement: float = 1.0  # 饱和度增强参数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'dark_channel_size': self.dark_channel_size,
            'atmosphere_ratio': self.atmosphere_ratio,
            'omega': self.omega,
            'min_transmission': self.min_transmission,
            'guided_filter_radius': self.guided_filter_radius,
            'guided_filter_eps': self.guided_filter_eps,
            'enable_non_homogeneous': self.enable_non_homogeneous,
            'block_size': self.block_size,
            'adaptive_strength': self.adaptive_strength,
            'enable_post_processing': self.enable_post_processing,
            'contrast_enhancement': self.contrast_enhancement,
            'saturation_enhancement': self.saturation_enhancement
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DehazingParameters':
        """从字典创建实例"""
        return cls(**data)


@dataclass
class ProcessingRecord:
    """处理记录数据模型"""
    id: str
    input_image: ImageInfo
    output_image: Optional[ImageInfo] = None
    parameters: DehazingParameters = field(default_factory=DehazingParameters)
    status: ProcessingStatus = ProcessingStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None  # 处理时间（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'input_image': self.input_image.to_dict(),
            'output_image': self.output_image.to_dict() if self.output_image else None,
            'parameters': self.parameters.to_dict(),
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error_message': self.error_message,
            'processing_time': self.processing_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingRecord':
        """从字典创建实例"""
        return cls(
            id=data['id'],
            input_image=ImageInfo.from_dict(data['input_image']),
            output_image=ImageInfo.from_dict(data['output_image']) if data['output_image'] else None,
            parameters=DehazingParameters.from_dict(data['parameters']),
            status=ProcessingStatus(data['status']),
            start_time=datetime.fromisoformat(data['start_time']) if data['start_time'] else None,
            end_time=datetime.fromisoformat(data['end_time']) if data['end_time'] else None,
            error_message=data['error_message'],
            processing_time=data['processing_time']
        )


@dataclass
class UserSettings:
    """用户设置数据模型"""
    # 界面设置
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    
    # 默认算法参数
    default_parameters: DehazingParameters = field(default_factory=DehazingParameters)
    
    # 当前去雾参数
    dehazing_params: DehazingParameters = field(default_factory=DehazingParameters)
    
    # 文件设置
    last_input_directory: str = ""
    last_output_directory: str = ""
    auto_save_results: bool = True
    
    # 显示设置
    show_processing_details: bool = True
    auto_fit_image: bool = True
    
    # 性能设置
    max_image_size: int = 4096  # 最大处理图像尺寸
    use_gpu_acceleration: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'window_width': self.window_width,
            'window_height': self.window_height,
            'window_maximized': self.window_maximized,
            'default_parameters': self.default_parameters.to_dict(),
            'dehazing_params': self.dehazing_params.to_dict(),
            'last_input_directory': self.last_input_directory,
            'last_output_directory': self.last_output_directory,
            'auto_save_results': self.auto_save_results,
            'show_processing_details': self.show_processing_details,
            'auto_fit_image': self.auto_fit_image,
            'max_image_size': self.max_image_size,
            'use_gpu_acceleration': self.use_gpu_acceleration
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSettings':
        """从字典创建实例"""
        return cls(
            window_width=data.get('window_width', 1200),
            window_height=data.get('window_height', 800),
            window_maximized=data.get('window_maximized', False),
            default_parameters=DehazingParameters.from_dict(data.get('default_parameters', {})),
            dehazing_params=DehazingParameters.from_dict(data.get('dehazing_params', {})),
            last_input_directory=data.get('last_input_directory', ''),
            last_output_directory=data.get('last_output_directory', ''),
            auto_save_results=data.get('auto_save_results', True),
            show_processing_details=data.get('show_processing_details', True),
            auto_fit_image=data.get('auto_fit_image', True),
            max_image_size=data.get('max_image_size', 4096),
            use_gpu_acceleration=data.get('use_gpu_acceleration', False)
        )