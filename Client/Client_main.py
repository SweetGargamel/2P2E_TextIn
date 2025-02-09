from Get_Table import CommonTableOcr
from Get_Extract import IntellectExtractOcr
from File_Check import FileChecker
import os
import configparser
import sys

def load_config():
    try:
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.conf')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
        config.read(config_path)
        
        if not config.has_section('API'):
            raise configparser.Error("配置文件中缺少 [API] 部分")
            
        app_id = config['API']['x_ti_app_id']
        secret_code = config['API']['x_ti_secret_code']
        
        if not app_id or not secret_code:
            raise ValueError("API 凭证不能为空")
            
        return {
            'x_ti_app_id': app_id,
            'x_ti_secret_code': secret_code
        }
    except Exception as e:
        print(f"配置文件读取错误 - 行号 {sys.exc_info()[2].tb_lineno}")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        sys.exit(1)

def get_all_file_paths(directory):#得到所有文件的路径
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_paths.append(os.path.join(root, file))
    return file_paths

def check_files_for_api(file_paths: list, api_type: str) -> list:
    """
    检查文件是否符合API要求，返回符合要求的文件路径列表
    
    Args:
        file_paths: 文件路径列表
        api_type: API类型 ('table_ocr' 或 'extract_ocr')
        
    Returns:
        list: 符合要求的文件路径列表
    """
    checker = FileChecker()
    valid_files = []
    
    for file_path in file_paths:
        abs_path = os.path.abspath(file_path)
        is_valid, errors = checker.check(file_path, api_type)
        
        if is_valid:
            valid_files.append(file_path)
        else:
            print(f"\n文件不符合要求: {abs_path}")
            for error in errors:
                print(f"- {error}")
    
    if len(valid_files) == 0:
        print("\n警告: 没有符合要求的文件可以处理")
    else:
        print(f"\n共发现 {len(valid_files)}/{len(file_paths)} 个有效文件")
    
    return valid_files

def process_with_common_table_ocr():
    try:
        test_table_dir = './Test_table'
        # output_dir = './Output'
        # if not os.path.exists(output_dir):
        #     os.makedirs(output_dir)
        file_paths = get_all_file_paths(test_table_dir)
        valid_files = check_files_for_api(file_paths, 'table_ocr')
        urls = []

        if valid_files:  # 只在有有效文件时继续处理
            config = load_config()
            ocr = CommonTableOcr(config['x_ti_app_id'], config['x_ti_secret_code'])
            ocr.recognize(valid_files, urls)
    except Exception as e:
        print(f"通用表格识别错误 - 行号 {sys.exc_info()[2].tb_lineno}")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")

def process_with_intellect_extract_ocr():
    try:
        test_table_dir = './Test_Extract'
        output_dir = './Output_Extract'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        file_paths = get_all_file_paths(test_table_dir)
        valid_files = check_files_for_api(file_paths, 'extract_ocr')
        urls = []
        fields_key = []
        #table_key = ["排名","国家定位","校名","学校档次","一级硕士点数量","A+数","A数","A-数","A+及A数","A类总数","总量积分"]
        table_key =["省份","类别","文科分数线","理科分数线","其他分数线"]
        if valid_files:  # 只在有有效文件时继续处理
            config = load_config()
            ocr = IntellectExtractOcr(config['x_ti_app_id'], config['x_ti_secret_code'])
            ocr.recognize(valid_files, urls, table_key=table_key, output_dir=output_dir, output_filename='combined.xlsx')
    except Exception as e:
        print(f"智能提取识别错误 - 行号 {sys.exc_info()[2].tb_lineno}")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")

if __name__ == "__main__":
    # Uncomment the function you want to use
    #process_with_common_table_ocr()
    process_with_intellect_extract_ocr()
