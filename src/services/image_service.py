# -*- coding: utf-8 -*-
"""
图像处理服务模块
提供图像处理相关的业务逻辑服务
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List, Callable
from datetime import datetime

from ..core.models import ImageInfo, DehazingParameters, ProcessingRecord, ProcessingStatus
from ..core.config import ConfigManager
from ..utils.logger import get_logger
from ..utils.image_utils import ImageProcessor
from ..algorithms.dehazing import NonHomogeneousDehazingAlgorithm


class ImageProcessingService:
    """图像处理服务类"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager()
        self.image_processor = ImageProcessor()
        self.dehazing_algorithm = NonHomogeneousDehazingAlgorithm()
        
        # 处理状态
        self.is_processing = False
        self.current_progress = 0
        self.current_status = "就绪"
    
    def validate_input_image(self, image_path: str) -> Optional[ImageInfo]:
        """验证输入图像
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            ImageInfo对象，如果验证失败返回None
        """
        try:
            if not os.path.exists(image_path):
                self.logger.error(f"图像文件不存在: {image_path}")
                return None
            
            # 检查文件大小
            file_size = os.path.getsize(image_path)
            if file_size == 0:
                self.logger.error(f"图像文件为空: {image_path}")
                return None
            
            if file_size > 100 * 1024 * 1024:  # 100MB限制
                self.logger.warning(f"图像文件过大: {file_size / 1024 / 1024:.1f}MB")
            
            # 加载图像信息
            image_info = self.image_processor.load_image_info(image_path)
            if not image_info:
                self.logger.error(f"无法加载图像信息: {image_path}")
                return None
            
            # 检查图像尺寸
            if image_info.width < 100 or image_info.height < 100:
                self.logger.warning(f"图像尺寸过小: {image_info.width}x{image_info.height}")
            
            if image_info.width > 4000 or image_info.height > 4000:
                self.logger.warning(f"图像尺寸较大: {image_info.width}x{image_info.height}，处理可能较慢")
            
            self.logger.info(f"图像验证成功: {image_path}")
            return image_info
            
        except Exception as e:
            self.logger.error(f"图像验证异常: {str(e)}")
            return None
    
    def generate_output_path(self, input_path: str, suffix: str = "_dehazed") -> str:
        """生成输出文件路径
        
        Args:
            input_path: 输入文件路径
            suffix: 文件名后缀
            
        Returns:
            输出文件路径
        """
        input_path_obj = Path(input_path)
        output_dir = input_path_obj.parent
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一的输出文件名
        base_name = input_path_obj.stem
        extension = input_path_obj.suffix
        
        output_path = output_dir / f"{base_name}{suffix}{extension}"
        
        # 如果文件已存在，添加数字后缀
        counter = 1
        while output_path.exists():
            output_path = output_dir / f"{base_name}{suffix}_{counter}{extension}"
            counter += 1
        
        return str(output_path)
    
    def process_image_async(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        parameters: Optional[DehazingParameters] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> bool:
        """异步处理图像
        
        Args:
            input_path: 输入图像路径
            output_path: 输出图像路径，如果为None则自动生成
            parameters: 处理参数，如果为None则使用默认参数
            progress_callback: 进度回调函数
            
        Returns:
            处理是否成功
        """
        if self.is_processing:
            self.logger.warning("已有处理任务在进行中")
            return False
        
        try:
            self.is_processing = True
            self.current_progress = 0
            self.current_status = "开始处理"
            
            # 验证输入图像
            if progress_callback:
                progress_callback(5, "验证输入图像...")
            
            image_info = self.validate_input_image(input_path)
            if not image_info:
                raise ValueError("输入图像验证失败")
            
            # 生成输出路径
            if not output_path:
                output_path = self.generate_output_path(input_path)
            
            # 获取处理参数
            if not parameters:
                parameters = self.config_manager.get_user_settings().dehazing_params
            
            if progress_callback:
                progress_callback(10, "准备处理算法...")
            
            # 执行去雾处理
            def internal_progress_callback(progress: int, status: str = ""):
                # 将算法进度映射到总进度的10-90%
                total_progress = 10 + int(progress * 0.8)
                self.current_progress = total_progress
                if status:
                    self.current_status = status
                if progress_callback:
                    progress_callback(total_progress, status)
            
            success = self.dehazing_algorithm.process_image(
                input_path,
                output_path,
                parameters,
                internal_progress_callback
            )
            
            if success:
                if progress_callback:
                    progress_callback(95, "验证输出结果...")
                
                # 验证输出结果
                if not os.path.exists(output_path):
                    raise RuntimeError("输出文件未生成")
                
                output_info = self.image_processor.load_image_info(output_path)
                if not output_info:
                    raise RuntimeError("输出文件无效")
                
                if progress_callback:
                    progress_callback(100, "处理完成")
                
                # 记录处理历史
                self.record_processing_history(input_path, output_path, parameters)
                
                self.current_progress = 100
                self.current_status = "处理完成"
                self.logger.info(f"图像处理成功: {input_path} -> {output_path}")
                
                return True
            else:
                raise RuntimeError("去雾算法处理失败")
                
        except Exception as e:
            self.logger.error(f"图像处理失败: {str(e)}")
            self.current_status = f"处理失败: {str(e)}"
            if progress_callback:
                progress_callback(self.current_progress, self.current_status)
            return False
        
        finally:
            self.is_processing = False
    
    def record_processing_history(
        self,
        input_path: str,
        output_path: str,
        parameters: DehazingParameters
    ):
        """记录处理历史
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            parameters: 处理参数
        """
        try:
            self.config_manager.add_processing_record(
                input_path,
                output_path,
                parameters
            )
            self.logger.info("处理历史记录成功")
        except Exception as e:
            self.logger.warning(f"记录处理历史失败: {str(e)}")
    
    def get_processing_history(self, limit: int = 10) -> List[ProcessingRecord]:
        """获取处理历史
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            处理记录列表
        """
        try:
            history = self.config_manager.get_processing_history()
            # 按时间倒序排列
            history.sort(key=lambda x: x.timestamp, reverse=True)
            return history[:limit]
        except Exception as e:
            self.logger.error(f"获取处理历史失败: {str(e)}")
            return []
    
    def clear_processing_history(self):
        """清空处理历史"""
        try:
            self.config_manager.clear_processing_history()
            self.logger.info("处理历史已清空")
        except Exception as e:
            self.logger.error(f"清空处理历史失败: {str(e)}")
    
    def get_processing_status(self) -> tuple[bool, int, str]:
        """获取当前处理状态
        
        Returns:
            (是否正在处理, 当前进度, 当前状态描述)
        """
        return self.is_processing, self.current_progress, self.current_status
    
    def cancel_processing(self):
        """取消当前处理"""
        if self.is_processing:
            # 这里可以添加取消处理的逻辑
            # 由于当前实现是同步的，实际取消需要在算法层面支持
            self.logger.info("请求取消处理")
            self.current_status = "用户取消"


class FileManagementService:
    """文件管理服务类"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    def is_supported_image(self, file_path: str) -> bool:
        """检查是否为支持的图像格式
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持
        """
        return Path(file_path).suffix.lower() in self.supported_formats
    
    def get_image_files_in_directory(self, directory: str) -> List[str]:
        """获取目录中的所有图像文件
        
        Args:
            directory: 目录路径
            
        Returns:
            图像文件路径列表
        """
        try:
            directory_path = Path(directory)
            if not directory_path.exists() or not directory_path.is_dir():
                return []
            
            image_files = []
            for file_path in directory_path.iterdir():
                if file_path.is_file() and self.is_supported_image(str(file_path)):
                    image_files.append(str(file_path))
            
            # 按文件名排序
            image_files.sort()
            return image_files
            
        except Exception as e:
            self.logger.error(f"获取目录图像文件失败: {str(e)}")
            return []
    
    def copy_file(self, source: str, destination: str) -> bool:
        """复制文件
        
        Args:
            source: 源文件路径
            destination: 目标文件路径
            
        Returns:
            是否成功
        """
        try:
            # 确保目标目录存在
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            shutil.copy2(source, destination)
            self.logger.info(f"文件复制成功: {source} -> {destination}")
            return True
            
        except Exception as e:
            self.logger.error(f"文件复制失败: {str(e)}")
            return False
    
    def move_file(self, source: str, destination: str) -> bool:
        """移动文件
        
        Args:
            source: 源文件路径
            destination: 目标文件路径
            
        Returns:
            是否成功
        """
        try:
            # 确保目标目录存在
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 移动文件
            shutil.move(source, destination)
            self.logger.info(f"文件移动成功: {source} -> {destination}")
            return True
            
        except Exception as e:
            self.logger.error(f"文件移动失败: {str(e)}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self.logger.info(f"文件删除成功: {file_path}")
                return True
            else:
                self.logger.warning(f"文件不存在: {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"文件删除失败: {str(e)}")
            return False
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            return {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'is_image': self.is_supported_image(file_path)
            }
            
        except Exception as e:
            self.logger.error(f"获取文件信息失败: {str(e)}")
            return None
    
    def create_backup(self, file_path: str, backup_dir: Optional[str] = None) -> Optional[str]:
        """创建文件备份
        
        Args:
            file_path: 原文件路径
            backup_dir: 备份目录，如果为None则在原文件目录创建
            
        Returns:
            备份文件路径，失败返回None
        """
        try:
            if not os.path.exists(file_path):
                return None
            
            file_path_obj = Path(file_path)
            
            if backup_dir:
                backup_dir_path = Path(backup_dir)
                backup_dir_path.mkdir(parents=True, exist_ok=True)
            else:
                backup_dir_path = file_path_obj.parent
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path_obj.stem}_backup_{timestamp}{file_path_obj.suffix}"
            backup_path = backup_dir_path / backup_name
            
            # 复制文件
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"备份创建成功: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"创建备份失败: {str(e)}")
            return None