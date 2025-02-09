# 检查上传的格式和尺寸是否符合要求，并返回相应的错误信息。

import os
from PIL import Image
import logging

# 配置不同API的文件限制规则
API_RULES = {
    'table_ocr': {  # 通用表格识别的规则
        'max_size': 10 * 1024 * 1024,  # 10MB
        'allowed_extensions': ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.pdf', '.doc', '.docx'],
        'min_dimension': 20,
        'max_dimension': 10000
    },
    'extract_ocr': {  # 智能提取的规则
        'max_size': 50 * 1024 * 1024,  # 50MB
        'allowed_extensions': ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.pdf', '.doc', '.docx'],
        'min_dimension': 20,
        'max_dimension': 10000
    }
    # 可以在这里添加新的API规则
}

# 错误类型枚举
class FileCheckError:
    FILE_NOT_FOUND = "文件不存在"
    FILE_TOO_LARGE = "文件大小超出限制"
    INVALID_FORMAT = "不支持的文件格式"
    INVALID_DIMENSION = "图片尺寸不符合要求"
    UNKNOWN_API = "未知的API类型"
    READ_ERROR = "文件读取错误"

class FileChecker:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def check(self, file_path: str, api_type: str) -> tuple[bool, list[str]]:
        """
        检查文件是否符合指定API的要求
        
        Args:
            file_path: 文件路径
            api_type: API类型 ('table_ocr' 或 'extract_ocr')
            
        Returns:
            tuple: (是否通过检查, [错误信息列表])
        """
        errors = []
        
        # 检查API类型是否存在
        if api_type not in API_RULES:
            return False, [FileCheckError.UNKNOWN_API]

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False, [FileCheckError.FILE_NOT_FOUND]

        try:
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            # 获取文件扩展名
            ext = os.path.splitext(file_path)[1].lower()
            
            rules = API_RULES[api_type]
            
            # 检查文件大小
            if file_size > rules['max_size']:
                errors.append(f"{FileCheckError.FILE_TOO_LARGE}: "
                            f"当前大小 {file_size/1024/1024:.2f}MB, "
                            f"最大限制 {rules['max_size']/1024/1024}MB")

            # 检查文件格式
            if ext not in rules['allowed_extensions']:
                errors.append(f"{FileCheckError.INVALID_FORMAT}: "
                            f"当前格式 {ext}, "
                            f"支持的格式 {', '.join(rules['allowed_extensions'])}")

            # 如果是图片，检查尺寸
            if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
                try:
                    with Image.open(file_path) as img:
                        width, height = img.size
                        if (width < rules['min_dimension'] or 
                            height < rules['min_dimension'] or
                            width > rules['max_dimension'] or 
                            height > rules['max_dimension']):
                            errors.append(f"{FileCheckError.INVALID_DIMENSION}: "
                                        f"当前尺寸 {width}x{height}, "
                                        f"要求范围 {rules['min_dimension']}-{rules['max_dimension']}")
                except Exception as e:
                    self.logger.error(f"图片尺寸检查错误: {str(e)}")
                    errors.append(f"{FileCheckError.READ_ERROR}: {str(e)}")

        except Exception as e:
            self.logger.error(f"文件检查错误: {str(e)}")
            errors.append(f"{FileCheckError.READ_ERROR}: {str(e)}")

        return len(errors) == 0, errors

    def add_api_rule(self, api_type: str, rule: dict) -> bool:
        """
        添加新的API规则
        
        Args:
            api_type: API类型标识符
            rule: 规则字典，包含 max_size, allowed_formats, min_dimension, max_dimension
            
        Returns:
            bool: 是否添加成功
        """
        try:
            required_keys = ['max_size', 'allowed_formats', 'min_dimension', 'max_dimension']
            if not all(key in rule for key in required_keys):
                self.logger.error("规则格式不完整")
                return False
                
            API_RULES[api_type] = rule
            return True
        except Exception as e:
            self.logger.error(f"添加规则失败: {str(e)}")
            return False

    @staticmethod
    def get_supported_apis() -> list[str]:
        """获取支持的API类型列表"""
        return list(API_RULES.keys())
    