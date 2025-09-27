#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非均质有雾图像去雾算法核心模块
基于改进的暗通道先验和导向滤波的自研去雾算法
"""

import numpy as np
import cv2
from typing import Tuple, Optional, Callable
import logging
from scipy import ndimage
from skimage import filters, morphology

from ..core.models import DehazingParameters


class NonHomogeneousDehazingAlgorithm:
    """
    非均质有雾图像去雾算法
    
    该算法针对非均匀雾霾分布的图像进行优化，结合了：
    1. 改进的暗通道先验算法
    2. 自适应大气光估计
    3. 导向滤波优化透射率
    4. 非均质雾霾密度分析
    5. 后处理增强
    """
    
    def __init__(self, parameters: Optional[DehazingParameters] = None):
        """
        初始化去雾算法
        
        Args:
            parameters: 算法参数，如果为None则使用默认参数
        """
        self.params = parameters or DehazingParameters()
        self.logger = logging.getLogger(__name__)
        
        # 算法状态
        self._atmosphere_light = None
        self._transmission_map = None
        self._dark_channel = None
        
    def dehaze_image(self, 
                    image: np.ndarray, 
                    progress_callback: Optional[Callable[[int, str], None]] = None) -> Tuple[np.ndarray, dict]:
        """
        对图像进行去雾处理
        
        Args:
            image: 输入的有雾图像 (H, W, 3) BGR格式
            progress_callback: 进度回调函数 (progress: int, message: str)
        
        Returns:
            Tuple[np.ndarray, dict]: (去雾后的图像, 处理信息)
        """
        try:
            self.logger.info("开始图像去雾处理")
            
            # 输入验证
            if image is None or image.size == 0:
                raise ValueError("输入图像为空")
            
            if len(image.shape) != 3 or image.shape[2] != 3:
                raise ValueError("输入图像必须是3通道彩色图像")
            
            # 转换为浮点数格式 [0, 1]
            img_float = image.astype(np.float64) / 255.0
            
            processing_info = {
                'input_shape': image.shape,
                'parameters': self.params.to_dict()
            }
            
            # 步骤1: 计算暗通道
            if progress_callback:
                progress_callback(10, "计算暗通道...")
            
            dark_channel = self._compute_dark_channel(img_float)
            self._dark_channel = dark_channel
            processing_info['dark_channel_computed'] = True
            
            # 步骤2: 估计大气光值
            if progress_callback:
                progress_callback(25, "估计大气光值...")
            
            atmosphere_light = self._estimate_atmosphere_light(img_float, dark_channel)
            self._atmosphere_light = atmosphere_light
            processing_info['atmosphere_light'] = atmosphere_light.tolist()
            
            # 步骤3: 估计透射率
            if progress_callback:
                progress_callback(40, "估计透射率...")
            
            transmission_raw = self._estimate_transmission(img_float, atmosphere_light)
            processing_info['transmission_estimated'] = True
            
            # 步骤4: 优化透射率（导向滤波）
            if progress_callback:
                progress_callback(60, "优化透射率...")
            
            transmission_refined = self._refine_transmission(img_float, transmission_raw)
            self._transmission_map = transmission_refined
            processing_info['transmission_refined'] = True
            
            # 步骤5: 非均质雾霾密度分析和调整
            if progress_callback:
                progress_callback(75, "分析雾霾分布...")
            
            transmission_adjusted = self._adjust_non_homogeneous_transmission(transmission_refined, dark_channel)
            processing_info['non_homogeneous_adjusted'] = True
            
            # 步骤6: 恢复场景辐射
            if progress_callback:
                progress_callback(85, "恢复场景辐射...")
            
            dehazed = self._recover_scene_radiance(img_float, atmosphere_light, transmission_adjusted)
            processing_info['scene_radiance_recovered'] = True
            
            # 步骤7: 后处理增强
            if progress_callback:
                progress_callback(95, "后处理增强...")
            
            enhanced = self._post_process_enhancement(dehazed)
            processing_info['post_processed'] = True
            
            # 转换回uint8格式
            result = np.clip(enhanced * 255, 0, 255).astype(np.uint8)
            
            if progress_callback:
                progress_callback(100, "去雾处理完成")
            
            self.logger.info("图像去雾处理完成")
            return result, processing_info
            
        except Exception as e:
            self.logger.error(f"图像去雾处理失败: {e}")
            raise
    
    def _compute_dark_channel(self, image: np.ndarray) -> np.ndarray:
        """
        计算暗通道
        
        Args:
            image: 输入图像 [0, 1]
        
        Returns:
            np.ndarray: 暗通道图像
        """
        # 取每个像素RGB三个通道的最小值
        min_channel = np.min(image, axis=2)
        
        # 在局部窗口内取最小值
        patch_size = self.params.dark_channel_size
        kernel = np.ones((patch_size, patch_size))
        
        # 使用形态学腐蚀操作计算局部最小值
        dark_channel = cv2.erode(min_channel, kernel)
        
        return dark_channel
    
    def _estimate_atmosphere_light(self, image: np.ndarray, dark_channel: np.ndarray) -> np.ndarray:
        """
        估计大气光值
        
        Args:
            image: 输入图像 [0, 1]
            dark_channel: 暗通道图像
        
        Returns:
            np.ndarray: 大气光值 (3,)
        """
        # 获取暗通道中最亮的像素位置
        h, w = dark_channel.shape
        num_pixels = int(h * w * self.params.atmosphere_ratio)
        
        # 找到暗通道中最亮的像素
        dark_flat = dark_channel.flatten()
        indices = np.argpartition(dark_flat, -num_pixels)[-num_pixels:]
        
        # 在原图像中找到对应位置的像素值
        y_coords, x_coords = np.unravel_index(indices, dark_channel.shape)
        
        # 计算这些像素在原图像中的亮度
        candidate_pixels = image[y_coords, x_coords]  # (num_pixels, 3)
        intensities = np.sum(candidate_pixels, axis=1)
        
        # 选择亮度最高的像素作为大气光
        max_intensity_idx = np.argmax(intensities)
        atmosphere_light = candidate_pixels[max_intensity_idx]
        
        # 确保大气光值不会太小
        atmosphere_light = np.maximum(atmosphere_light, 0.1)
        
        return atmosphere_light
    
    def _estimate_transmission(self, image: np.ndarray, atmosphere_light: np.ndarray) -> np.ndarray:
        """
        估计透射率
        
        Args:
            image: 输入图像 [0, 1]
            atmosphere_light: 大气光值
        
        Returns:
            np.ndarray: 透射率图像
        """
        # 归一化图像
        normalized_image = image / atmosphere_light
        
        # 计算归一化图像的暗通道
        dark_channel_norm = self._compute_dark_channel(normalized_image)
        
        # 估计透射率
        transmission = 1 - self.params.omega * dark_channel_norm
        
        return transmission
    
    def _refine_transmission(self, image: np.ndarray, transmission: np.ndarray) -> np.ndarray:
        """
        使用双边滤波优化透射率（替代导向滤波）
        
        Args:
            image: 输入图像 [0, 1]
            transmission: 原始透射率
        
        Returns:
            np.ndarray: 优化后的透射率
        """
        # 使用双边滤波平滑透射率
        transmission_uint8 = (transmission * 255).astype(np.uint8)
        
        # 双边滤波参数
        d = self.params.guided_filter_radius
        sigma_color = 80
        sigma_space = 80
        
        refined = cv2.bilateralFilter(
            transmission_uint8,
            d,
            sigma_color,
            sigma_space
        )
        
        return refined.astype(np.float64) / 255.0
    
    def _adjust_non_homogeneous_transmission(self, transmission: np.ndarray, dark_channel: np.ndarray) -> np.ndarray:
        """
        针对非均质雾霾分布调整透射率
        
        Args:
            transmission: 透射率图像
            dark_channel: 暗通道图像
        
        Returns:
            np.ndarray: 调整后的透射率
        """
        # 分析雾霾密度分布
        fog_density = 1 - transmission
        
        # 计算局部雾霾密度变化
        fog_gradient = np.gradient(fog_density)
        fog_variation = np.sqrt(fog_gradient[0]**2 + fog_gradient[1]**2)
        
        # 对高变化区域进行自适应调整
        variation_threshold = np.percentile(fog_variation, 75)
        high_variation_mask = fog_variation > variation_threshold
        
        # 在高变化区域增强透射率
        adjusted_transmission = transmission.copy()
        adjusted_transmission[high_variation_mask] = np.minimum(
            adjusted_transmission[high_variation_mask] * 1.2,
            0.9
        )
        
        # 确保透射率不低于最小值
        adjusted_transmission = np.maximum(adjusted_transmission, self.params.min_transmission)
        
        return adjusted_transmission
    
    def _recover_scene_radiance(self, image: np.ndarray, atmosphere_light: np.ndarray, transmission: np.ndarray) -> np.ndarray:
        """
        恢复场景辐射
        
        Args:
            image: 输入图像 [0, 1]
            atmosphere_light: 大气光值
            transmission: 透射率
        
        Returns:
            np.ndarray: 恢复的场景辐射
        """
        # 确保透射率不会太小，避免除零错误
        transmission_safe = np.maximum(transmission, self.params.min_transmission)
        
        # 扩展透射率维度以匹配图像
        transmission_3d = np.repeat(transmission_safe[:, :, np.newaxis], 3, axis=2)
        
        # 恢复场景辐射：J(x) = (I(x) - A) / t(x) + A
        recovered = (image - atmosphere_light) / transmission_3d + atmosphere_light
        
        return recovered
    
    def _post_process_enhancement(self, image: np.ndarray) -> np.ndarray:
        """
        后处理增强
        
        Args:
            image: 去雾后的图像 [0, 1]
        
        Returns:
            np.ndarray: 增强后的图像
        """
        enhanced = image.copy()
        
        # 对比度增强
        if self.params.contrast_enhancement != 1.0:
            # 计算图像均值
            mean_val = np.mean(enhanced)
            enhanced = (enhanced - mean_val) * self.params.contrast_enhancement + mean_val
        
        # 饱和度增强（在HSV空间中进行）
        if self.params.saturation_enhancement != 1.0:
            # 转换到HSV空间
            enhanced_uint8 = (enhanced * 255).astype(np.uint8)
            hsv = cv2.cvtColor(enhanced_uint8, cv2.COLOR_BGR2HSV)
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * self.params.saturation_enhancement, 0, 255)
            enhanced_uint8 = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            enhanced = enhanced_uint8.astype(np.float64) / 255.0
        
        # 限制像素值范围
        enhanced = np.clip(enhanced, 0, 1)
        
        return enhanced
    
    def get_intermediate_results(self) -> dict:
        """
        获取中间处理结果
        
        Returns:
            dict: 包含中间结果的字典
        """
        results = {}
        
        if self._dark_channel is not None:
            results['dark_channel'] = (self._dark_channel * 255).astype(np.uint8)
        
        if self._transmission_map is not None:
            results['transmission_map'] = (self._transmission_map * 255).astype(np.uint8)
        
        if self._atmosphere_light is not None:
            results['atmosphere_light'] = self._atmosphere_light
        
        return results
    
    def update_parameters(self, parameters: DehazingParameters):
        """
        更新算法参数
        
        Args:
            parameters: 新的算法参数
        """
        self.params = parameters
        self.logger.info("算法参数已更新")
    
    def reset_state(self):
        """
        重置算法状态
        """
        self._atmosphere_light = None
        self._transmission_map = None
        self._dark_channel = None
        self.logger.info("算法状态已重置")


def create_dehazing_algorithm(parameters: Optional[DehazingParameters] = None) -> NonHomogeneousDehazingAlgorithm:
    """
    创建去雾算法实例
    
    Args:
        parameters: 算法参数
    
    Returns:
        NonHomogeneousDehazingAlgorithm: 去雾算法实例
    """
    return NonHomogeneousDehazingAlgorithm(parameters)