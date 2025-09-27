#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图像处理工具模块
提供图像加载、保存、格式转换等基础功能
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance
from pathlib import Path
from typing import Optional, Tuple, Union
import logging

from ..core.models import ImageInfo, ImageFormat


class ImageProcessor:
    """图像处理器"""
    
    # 支持的图像格式
    SUPPORTED_FORMATS = {
        '.jpg': ImageFormat.JPEG,
        '.jpeg': ImageFormat.JPEG,
        '.png': ImageFormat.PNG,
        '.bmp': ImageFormat.BMP,
        '.tiff': ImageFormat.TIFF,
        '.tif': ImageFormat.TIFF
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_image(self, file_path: Union[str, Path]) -> Tuple[Optional[np.ndarray], Optional[ImageInfo]]:
        """
        加载图像文件
        
        Args:
            file_path: 图像文件路径
        
        Returns:
            Tuple[Optional[np.ndarray], Optional[ImageInfo]]: (图像数组, 图像信息)
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                self.logger.error(f"图像文件不存在: {file_path}")
                return None, None
            
            # 检查文件格式
            file_ext = file_path.suffix.lower()
            if file_ext not in self.SUPPORTED_FORMATS:
                self.logger.error(f"不支持的图像格式: {file_ext}")
                return None, None
            
            # 使用OpenCV加载图像
            image = cv2.imread(str(file_path), cv2.IMREAD_COLOR)
            
            if image is None:
                self.logger.error(f"无法加载图像: {file_path}")
                return None, None
            
            # 获取图像信息
            height, width, channels = image.shape
            file_size = file_path.stat().st_size
            
            image_info = ImageInfo(
                file_path=str(file_path),
                file_name=file_path.name,
                file_size=file_size,
                width=width,
                height=height,
                channels=channels,
                format=self.SUPPORTED_FORMATS[file_ext]
            )
            
            self.logger.info(f"成功加载图像: {file_path} ({width}x{height})")
            return image, image_info
            
        except Exception as e:
            self.logger.error(f"加载图像失败: {e}")
            return None, None
    
    def save_image(self, image: np.ndarray, file_path: Union[str, Path], quality: int = 95) -> bool:
        """
        保存图像文件
        
        Args:
            image: 图像数组
            file_path: 保存路径
            quality: JPEG质量 (1-100)
        
        Returns:
            bool: 保存是否成功
        """
        try:
            file_path = Path(file_path)
            
            # 确保目录存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 检查文件格式
            file_ext = file_path.suffix.lower()
            if file_ext not in self.SUPPORTED_FORMATS:
                self.logger.error(f"不支持的保存格式: {file_ext}")
                return False
            
            # 设置保存参数
            save_params = []
            if file_ext in ['.jpg', '.jpeg']:
                save_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            elif file_ext == '.png':
                save_params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
            
            # 保存图像
            success = cv2.imwrite(str(file_path), image, save_params)
            
            if success:
                self.logger.info(f"图像已保存: {file_path}")
                return True
            else:
                self.logger.error(f"保存图像失败: {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"保存图像时出错: {e}")
            return False
    
    def resize_image(self, image: np.ndarray, target_size: Tuple[int, int], 
                    keep_aspect_ratio: bool = True) -> np.ndarray:
        """
        调整图像大小
        
        Args:
            image: 输入图像
            target_size: 目标尺寸 (width, height)
            keep_aspect_ratio: 是否保持宽高比
        
        Returns:
            np.ndarray: 调整后的图像
        """
        try:
            height, width = image.shape[:2]
            target_width, target_height = target_size
            
            if keep_aspect_ratio:
                # 计算缩放比例
                scale = min(target_width / width, target_height / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                # 调整大小
                resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                
                # 创建目标尺寸的画布
                canvas = np.zeros((target_height, target_width, image.shape[2]), dtype=image.dtype)
                
                # 计算居中位置
                y_offset = (target_height - new_height) // 2
                x_offset = (target_width - new_width) // 2
                
                # 将调整后的图像放置在画布中心
                canvas[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = resized
                
                return canvas
            else:
                # 直接调整到目标尺寸
                return cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)
                
        except Exception as e:
            self.logger.error(f"调整图像大小失败: {e}")
            return image
    
    def convert_to_rgb(self, image: np.ndarray) -> np.ndarray:
        """
        将BGR图像转换为RGB
        
        Args:
            image: BGR图像
        
        Returns:
            np.ndarray: RGB图像
        """
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    def convert_to_bgr(self, image: np.ndarray) -> np.ndarray:
        """
        将RGB图像转换为BGR
        
        Args:
            image: RGB图像
        
        Returns:
            np.ndarray: BGR图像
        """
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    def enhance_image(self, image: np.ndarray, 
                     brightness: float = 1.0,
                     contrast: float = 1.0,
                     saturation: float = 1.0) -> np.ndarray:
        """
        图像增强
        
        Args:
            image: 输入图像
            brightness: 亮度调整 (0.0-2.0)
            contrast: 对比度调整 (0.0-2.0)
            saturation: 饱和度调整 (0.0-2.0)
        
        Returns:
            np.ndarray: 增强后的图像
        """
        try:
            # 转换为PIL图像
            pil_image = Image.fromarray(self.convert_to_rgb(image))
            
            # 亮度调整
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(pil_image)
                pil_image = enhancer.enhance(brightness)
            
            # 对比度调整
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(pil_image)
                pil_image = enhancer.enhance(contrast)
            
            # 饱和度调整
            if saturation != 1.0:
                enhancer = ImageEnhance.Color(pil_image)
                pil_image = enhancer.enhance(saturation)
            
            # 转换回OpenCV格式
            enhanced = np.array(pil_image)
            return self.convert_to_bgr(enhanced)
            
        except Exception as e:
            self.logger.error(f"图像增强失败: {e}")
            return image
    
    def get_image_histogram(self, image: np.ndarray) -> dict:
        """
        计算图像直方图
        
        Args:
            image: 输入图像
        
        Returns:
            dict: 包含各通道直方图的字典
        """
        try:
            histograms = {}
            
            # 计算各通道直方图
            colors = ['blue', 'green', 'red']
            for i, color in enumerate(colors):
                hist = cv2.calcHist([image], [i], None, [256], [0, 256])
                histograms[color] = hist.flatten()
            
            # 计算灰度直方图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            hist_gray = cv2.calcHist([gray], [0], None, [256], [0, 256])
            histograms['gray'] = hist_gray.flatten()
            
            return histograms
            
        except Exception as e:
            self.logger.error(f"计算直方图失败: {e}")
            return {}
    
    def validate_image_size(self, image: np.ndarray, max_size: int = 4096) -> bool:
        """
        验证图像尺寸
        
        Args:
            image: 输入图像
            max_size: 最大尺寸限制
        
        Returns:
            bool: 尺寸是否合法
        """
        height, width = image.shape[:2]
        return width <= max_size and height <= max_size
    
    def get_image_stats(self, image: np.ndarray) -> dict:
        """
        获取图像统计信息
        
        Args:
            image: 输入图像
        
        Returns:
            dict: 图像统计信息
        """
        try:
            stats = {
                'shape': image.shape,
                'dtype': str(image.dtype),
                'min_value': float(np.min(image)),
                'max_value': float(np.max(image)),
                'mean_value': float(np.mean(image)),
                'std_value': float(np.std(image))
            }
            
            # 各通道统计
            if len(image.shape) == 3:
                for i, channel in enumerate(['blue', 'green', 'red']):
                    channel_data = image[:, :, i]
                    stats[f'{channel}_mean'] = float(np.mean(channel_data))
                    stats[f'{channel}_std'] = float(np.std(channel_data))
            
            return stats
            
        except Exception as e:
            self.logger.error(f"计算图像统计信息失败: {e}")
            return {}
    
    def load_image_info(self, file_path: Union[str, Path]) -> Optional[ImageInfo]:
        """加载图像信息（不加载图像数据）
        
        Args:
            file_path: 图像文件路径
        
        Returns:
            Optional[ImageInfo]: 图像信息对象，失败时返回None
        """
        try:
            _, image_info = self.load_image(file_path)
            return image_info
        except Exception as e:
            self.logger.error(f"加载图像信息失败: {e}")
            return None


# 全局图像处理器实例
_image_processor: Optional[ImageProcessor] = None


def get_image_processor() -> ImageProcessor:
    """
    获取全局图像处理器实例
    
    Returns:
        ImageProcessor: 图像处理器实例
    """
    global _image_processor
    if _image_processor is None:
        _image_processor = ImageProcessor()
    return _image_processor


# 便捷函数
def load_image(file_path: Union[str, Path]) -> Tuple[Optional[np.ndarray], Optional[ImageInfo]]:
    """加载图像（便捷函数）"""
    return get_image_processor().load_image(file_path)


def save_image(image: np.ndarray, file_path: Union[str, Path], quality: int = 95) -> bool:
    """保存图像（便捷函数）"""
    return get_image_processor().save_image(image, file_path, quality)


def resize_image(image: np.ndarray, target_size: Tuple[int, int], keep_aspect_ratio: bool = True) -> np.ndarray:
    """调整图像大小（便捷函数）"""
    return get_image_processor().resize_image(image, target_size, keep_aspect_ratio)